"""Customers can skip a recurring visit (plan continues) or reschedule
themselves, free, up to 48 hours out. Inside 48 hours they must call."""
import datetime, os, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="tm-self-"))
os.environ["DAILY_TEXT"] = "0"
sys.path.insert(0, os.path.join(ROOT, "server"))
import app, db  # noqa: E402


class SelfServeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db.init()

    def setUp(self):
        self.con = db.connect()
        self._stripe = os.environ.pop("STRIPE_SECRET_KEY", None)

    def tearDown(self):
        self.con.close()
        if self._stripe is not None:
            os.environ["STRIPE_SECRET_KEY"] = self._stripe

    def open_days(self, start=4):
        for off in range(start, 80):
            d = datetime.date.today() + datetime.timedelta(days=off)
            st = app.api_availability({"con": self.con, "query": {"date": [d.isoformat()]}})
            if st.get("open") and st.get("slots"):
                yield d.isoformat(), st["slots"]

    def book(self, who, frequency="biweekly"):
        d, slots = next(self.open_days())
        email = "%s@example.com" % who.lower()
        r = app.api_create_booking({"con": self.con, "query": {}, "cookies": {}, "headers": {},
                                    "ip": "t", "body": {
            "name": who, "email": email, "phone": "8135550100", "address": "1 Main St",
            "city": "Tampa", "date": d, "slot": slots[0], "tier_id": "t2",
            "frequency": frequency, "accept_terms": True}})
        return r, email

    def call(self, fn, **body):
        return fn({"con": self.con, "query": {}, "cookies": {}, "headers": {}, "ip": "t",
                   "body": body})

    def row(self, bid):
        return dict(self.con.execute("SELECT * FROM bookings WHERE id=?", (bid,)).fetchone())

    def test_skip_keeps_the_plan_and_the_intro_count(self):
        r, email = self.book("Skipper")
        out = self.call(app.api_skip, ref=r["ref"], email=email)
        self.assertEqual(self.row(r["id"])["status"], "cancelled")
        nxt = dict(self.con.execute("SELECT * FROM bookings WHERE recurring_from=?",
                                    (r["id"],)).fetchone())
        self.assertEqual(out["next"]["ref"], nxt["ref"])
        gap = (datetime.date.fromisoformat(nxt["date"]) - datetime.date.fromisoformat(r["date"])).days
        self.assertTrue(11 <= gap <= 17, gap)
        # The skipped visit never happened, so the next one is still visit 1.
        self.assertEqual((nxt["series_visit"], nxt["is_first_clean"], nxt["status"]),
                         (1, 1, "confirmed"))
        # Skipping twice is refused (the first is already cancelled).
        with self.assertRaises(app.ApiError):
            self.call(app.api_skip, ref=r["ref"], email=email)

    def test_one_time_bookings_cannot_skip(self):
        r, email = self.book("Oncer", frequency="once")
        with self.assertRaises(app.ApiError):
            self.call(app.api_skip, ref=r["ref"], email=email)
        pub = app.booking_public(self.con, self.row(r["id"]))
        self.assertFalse(pub["can_skip"])
        self.assertTrue(pub["can_change"])

    def test_reschedule_moves_to_a_free_slot_only(self):
        r, email = self.book("Mover")
        days = list(self.open_days(start=6))
        target = next((d, s) for d, s in days if d != r["date"])
        out = self.call(app.api_reschedule, ref=r["ref"], email=email,
                        date=target[0], slot=target[1][0])
        self.assertTrue(out["ok"])
        self.assertEqual((self.row(r["id"])["date"], self.row(r["id"])["slot"]),
                         (target[0], target[1][0]))
        with self.assertRaises(app.ApiError):     # wrong email
            self.call(app.api_reschedule, ref=r["ref"], email="x@example.com",
                      date=r["date"], slot="8:00 AM")
        with self.assertRaises(app.ApiError):     # a slot that isn't offered
            self.call(app.api_reschedule, ref=r["ref"], email=email,
                      date=target[0], slot="3:17 AM")

    def test_reschedule_cannot_overfill_a_day(self):
        cap = app.CFG["booking"]["max_jobs_per_day"]
        d, _ = next(self.open_days(start=30))
        fillers = []
        for i in range(cap):
            r, _e = self.book("Filler%d" % i)
            fillers.append(r)
            st = app.api_availability({"con": self.con, "query": {"date": [d]}})
            self.con.execute("UPDATE bookings SET date=?, slot=? WHERE id=?",
                             (d, st["slots"][0], r["id"]))
            self.con.commit()
        r, email = self.book("Latecomer")
        for slot in app.CFG["booking"]["time_slots"]:
            with self.assertRaises(app.ApiError):
                self.call(app.api_reschedule, ref=r["ref"], email=email, date=d, slot=slot)

    def test_inside_48_hours_must_call(self):
        r, email = self.book("Lastminute")
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        self.con.execute("UPDATE bookings SET date=? WHERE id=?", (tomorrow, r["id"]))
        self.con.commit()
        self.assertFalse(app.booking_public(self.con, self.row(r["id"]))["can_change"])
        for fn in (app.api_skip, app.api_reschedule):
            with self.assertRaises(app.ApiError):
                self.call(fn, ref=r["ref"], email=email, date="2030-01-02", slot="8:00 AM")
        self.assertNotEqual(self.row(r["id"])["status"], "cancelled")

    def test_track_page_offers_skip_and_reschedule(self):
        js = open(os.path.join(ROOT, "web", "js", "track.js"), encoding="utf-8").read()
        self.assertIn("/api/bookings/skip", js)
        self.assertIn("/api/bookings/reschedule", js)
        self.assertNotIn('href="/contact" style="margin-left:8px">Reschedule', js)


if __name__ == "__main__":
    unittest.main()
