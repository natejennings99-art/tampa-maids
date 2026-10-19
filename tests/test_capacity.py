"""Booking capacity must not exceed what the crew can actually clean.

This is the expensive kind of bug: the site happily takes the money and the
slot, and the failure only shows up as a phone call cancelling on someone who
has never used us before. With no reviews yet, a cancelled first visit costs
much more than a declined one, so the caps are deliberately conservative and
the owner can always add a job by hand in the admin.
"""
import datetime, json, math, os, sys, tempfile, threading, unittest
import urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_TMP = tempfile.mkdtemp(prefix="tm-capacity-")
os.environ["DATA_DIR"] = _TMP
sys.path.insert(0, os.path.join(ROOT, "server"))
import app, db  # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402

CFG = json.load(open(os.path.join(ROOT, "business.json"), encoding="utf-8"))


class ConfigSanityTest(unittest.TestCase):
    """No server needed: these catch the config drifting away from reality."""

    def test_bookable_day_fits_the_crew(self):
        bk = CFG["booking"]
        crew = CFG["staffing"]["crew_size"]
        per_cleaner = CFG["economics"]["jobs_per_cleaner_per_day"]
        physical = crew * per_cleaner
        bookable = min(
            bk["max_jobs_per_day"],
            len(bk["time_slots"]) * bk["max_jobs_per_slot"],
        )
        self.assertLessEqual(
            bookable, math.ceil(physical),
            "the site accepts %s jobs a day but %d cleaner(s) can do %s — "
            "raise crew_size before raising the caps" % (bookable, crew, physical),
        )

    def test_one_cleaner_means_one_job_per_slot(self):
        """Two jobs in the same slot cannot both be attended by one person."""
        self.assertLessEqual(
            CFG["booking"]["max_jobs_per_slot"], CFG["staffing"]["crew_size"]
        )

    def test_caps_are_present_and_positive(self):
        bk = CFG["booking"]
        for key in ("max_jobs_per_slot", "max_jobs_per_day"):
            self.assertIn(key, bk)
            self.assertGreaterEqual(bk[key], 1)


class LiveCapacityTest(unittest.TestCase):
    """Books against a throwaway database until the day closes."""

    @classmethod
    def setUpClass(cls):
        db.init()
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def call(self, method, path, body=None):
        req = urllib.request.Request(
            self.base + path,
            data=json.dumps(body).encode() if body is not None else None,
            method=method, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def open_day(self, skip=0):
        """An untouched open day. Each test takes its own, because filling a
        day is the whole point here and tests must not inherit each other's
        bookings — the first version of this test failed for exactly that."""
        found = []
        for off in (0, 40):
            month = (datetime.date.today().replace(day=1)
                     + datetime.timedelta(days=off)).strftime("%Y-%m")
            _, a = self.call("GET", "/api/availability?month=" + month)
            for d in a["days"]:
                if d.get("open") and d.get("slots"):
                    found.append((d["date"], d["slots"]))
                    if len(found) > skip:
                        return found[skip]
        raise AssertionError("no open day available to test with")

    def book(self, date, slot, who):
        return self.call("POST", "/api/bookings", {
            "name": who, "email": "%s@example.com" % who.lower(),
            "phone": "8135550100", "address": "1 Bayshore Blvd",
            "city": "Tampa", "zip": "33606", "date": date, "slot": slot,
            "tier_id": "t3", "frequency": "biweekly", "accept_terms": True,
        })

    def test_a_slot_cannot_be_double_booked(self):
        date, slots = self.open_day()
        slot = slots[0]
        status, first = self.book(date, slot, "Alpha")
        self.assertEqual(status, 200, first)

        status, second = self.call("GET", "/api/availability?date=" + date)
        self.assertNotIn(slot, second.get("slots") or [],
                         "a filled slot is still being offered")

        status, refused = self.book(date, slot, "Bravo")
        self.assertEqual(status, 400,
                         "the same slot was sold twice: %s" % refused)
        self.assertIn("filled up", (refused.get("error") or "").lower())

    def test_the_day_closes_once_the_daily_cap_is_reached(self):
        date, slots = self.open_day(skip=1)
        cap = CFG["booking"]["max_jobs_per_day"]
        for i in range(cap):
            status, r = self.book(date, slots[i] if i < len(slots) else slots[-1],
                                  "Day%d" % i)
            if status != 200:
                _, fresh = self.call("GET", "/api/availability?date=" + date)
                self.fail("booking %d of %d was refused early (%s); day=%s"
                          % (i + 1, cap, r, fresh))

        _, day = self.call("GET", "/api/availability?date=" + date)
        self.assertFalse(day.get("open"),
                         "day stayed open past the daily cap of %d" % cap)
        self.assertEqual(day.get("reason"), "Fully booked")


if __name__ == "__main__":
    unittest.main()
