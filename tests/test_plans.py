"""One-time clients can switch to a plan themselves, and the owner page
shows plans whose next visit never got booked."""
import datetime, json, os, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="tm-plans-"))
os.environ["DAILY_TEXT"] = "0"
sys.path.insert(0, os.path.join(ROOT, "server"))
import app, db, pricing  # noqa: E402


class PlansTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db.init()

    def setUp(self):
        self.con = db.connect()
        self._stripe = os.environ.pop("STRIPE_SECRET_KEY", None)
        self.sent = []
        self._ping, app.notify.ping_owner = app.notify.ping_owner, \
            lambda cfg, t, s=None: self.sent.append(t)

    def tearDown(self):
        app.notify.ping_owner = self._ping
        self.con.close()
        if self._stripe is not None:
            os.environ["STRIPE_SECRET_KEY"] = self._stripe

    def book(self, who, frequency="once", start=4):
        for off in range(start, 80):
            d = (datetime.date.today() + datetime.timedelta(days=off)).isoformat()
            st = app.api_availability({"con": self.con, "query": {"date": [d]}})
            if st.get("open") and st.get("slots"):
                email = "%s@example.com" % who.lower()
                return app.api_create_booking({"con": self.con, "query": {}, "cookies": {},
                                               "headers": {}, "ip": "t", "body": {
                    "name": who, "email": email, "phone": "8135550100", "address": "1 Main St",
                    "city": "Tampa", "date": d, "slot": st["slots"][0], "tier_id": "t2",
                    "frequency": frequency, "accept_terms": True}}), email
        raise AssertionError("no open day")

    def call(self, fn, **body):
        return fn({"con": self.con, "query": {}, "cookies": {}, "headers": {}, "ip": "t", "body": body})

    def row(self, bid):
        return dict(self.con.execute("SELECT * FROM bookings WHERE id=?", (bid,)).fetchone())

    def test_switch_once_to_biweekly_reprices_at_the_plan_price(self):
        r, email = self.book("Switcher")
        self.assertTrue(app.booking_public(self.con, self.row(r["id"]))["can_go_recurring"])
        prev = self.call(app.api_make_recurring, ref=r["ref"], email=email,
                         frequency="biweekly", preview=True)
        self.assertEqual(self.row(r["id"])["frequency"], "once", "preview must not save")
        want = pricing.quote(app.CFG, {"service": "residential", "tier_id": "t2", "frequency": "biweekly",
                                       "city": "Tampa", "is_first_clean": True})["total"]
        self.assertEqual(prev["total"], want)
        out = self.call(app.api_make_recurring, ref=r["ref"], email=email, frequency="biweekly")
        row = self.row(r["id"])
        self.assertEqual((row["frequency"], row["total_cents"], row["series_visit"]),
                         ("biweekly", want, 1))
        self.assertIn("NEW PLAN", self.sent[-1])
        self.assertNotIn("insured", out["message"].lower())
        # Now it's a plan: completing it books the next visit.
        self.con.execute("UPDATE bookings SET status='completed' WHERE id=?", (r["id"],))
        self.con.commit()
        app.on_job_completed(self.con, r["id"])
        self.assertIsNotNone(self.con.execute("SELECT id FROM bookings WHERE recurring_from=?",
                                              (r["id"],)).fetchone())
        with self.assertRaises(app.ApiError):     # already a plan
            self.call(app.api_make_recurring, ref=r["ref"], email=email, frequency="weekly")

    def test_referral_credit_survives_the_switch(self):
        r, email = self.book("Credited")
        q = json.loads(self.row(r["id"])["quote"])
        q["lines"].append({"label": "Your referral credit", "detail": "x", "amount": -2500})
        self.con.execute("UPDATE bookings SET quote=? WHERE id=?", (json.dumps(q), r["id"]))
        self.con.commit()
        plain = self.call(app.api_make_recurring, ref=r["ref"], email=email, preview=True)
        want = pricing.quote(app.CFG, {"service": "residential", "tier_id": "t2", "frequency": "biweekly",
                                       "city": "Tampa", "is_first_clean": True})["total"]
        self.assertEqual(plain["total"], want - 2500)

    def test_bad_frequency_and_non_house_jobs_are_refused(self):
        r, email = self.book("Picky")
        with self.assertRaises(app.ApiError):
            self.call(app.api_make_recurring, ref=r["ref"], email=email, frequency="hourly")
        self.con.execute("UPDATE bookings SET service_id='move' WHERE id=?", (r["id"],))
        self.con.commit()
        with self.assertRaises(app.ApiError):
            self.call(app.api_make_recurring, ref=r["ref"], email=email, frequency="biweekly")

    def test_owner_sees_and_rebooks_a_stalled_plan(self):
        r, email = self.book("Stalled", frequency="biweekly", start=20)
        # Done long ago and the auto-book never happened.
        past = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        self.con.execute("UPDATE bookings SET status='completed', date=? WHERE id=?", (past, r["id"]))
        self.con.commit()
        plans = app._plans(self.con, datetime.date.today().isoformat())
        self.assertIn(r["id"], [p["id"] for p in plans["stalled"]])
        from unittest import mock
        with mock.patch.object(app, "need_staff", return_value={"role": "owner"}):
            out = app.api_owner_book_next({"con": self.con, "query": {}, "body": {},
                                           "headers": {}, "cookies": {}}, str(r["id"]))
        self.assertGreaterEqual(out["date"], datetime.date.today().isoformat())
        plans = app._plans(self.con, datetime.date.today().isoformat())
        self.assertNotIn(r["id"], [p["id"] for p in plans["stalled"]])
        self.assertGreaterEqual(plans["active"], 1)
        self.assertGreater(plans["monthly_cents"], 0)

    def test_ended_plans_are_listed_for_a_call(self):
        r, email = self.book("Ender", frequency="weekly", start=10)
        self.call(app.api_cancel, ref=r["ref"], email=email)
        ended = app._plans(self.con, datetime.date.today().isoformat())["ended"]
        self.assertIn(r["ref"], [p["ref"] for p in ended])

    def test_pages_wire_the_features(self):
        js = open(os.path.join(ROOT, "web", "js", "track.js"), encoding="utf-8").read()
        self.assertIn("/api/bookings/make-recurring", js)
        owner = open(os.path.join(ROOT, "web", "owner.html"), encoding="utf-8").read()
        self.assertIn("data-next", owner)
        self.assertIn("d.plans.stalled", owner)


if __name__ == "__main__":
    unittest.main()
