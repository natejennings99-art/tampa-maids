"""Recurring plans book their own next visit, and reminders go out once."""
import datetime, json, os, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="tm-recur-"))
os.environ["DAILY_TEXT"] = "0"
sys.path.insert(0, os.path.join(ROOT, "server"))
import app, db, pricing  # noqa: E402


class RecurringTest(unittest.TestCase):

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

    def book(self, who, frequency="biweekly", skip=0):
        found = 0
        for off in range(1, 50):
            d = datetime.date.today() + datetime.timedelta(days=off)
            st = app.api_availability({"con": self.con, "query": {"date": [d.isoformat()]}})
            if st.get("open") and st.get("slots"):
                if found < skip:
                    found += 1
                    continue
                ctx = {"con": self.con, "query": {}, "cookies": {}, "headers": {}, "ip": "t",
                       "body": {"name": who, "email": "%s@example.com" % who.lower(),
                                "phone": "8135550100", "address": "1 Main St", "city": "Tampa",
                                "date": d.isoformat(), "slot": st["slots"][0], "tier_id": "t2",
                                "frequency": frequency, "accept_terms": True}}
                return app.api_create_booking(ctx)
        raise AssertionError("no open day")

    def complete(self, bid):
        self.con.execute("UPDATE bookings SET status='completed', completed_at=? WHERE id=?",
                         (db.now(), bid))
        self.con.commit()
        app.on_job_completed(self.con, bid)

    def child(self, bid):
        r = self.con.execute("SELECT * FROM bookings WHERE recurring_from=?", (bid,)).fetchone()
        return dict(r) if r else None

    def test_biweekly_books_the_next_visit_two_weeks_out_at_the_intro_price(self):
        r = self.book("Biweekly")
        self.complete(r["id"])
        nxt = self.child(r["id"])
        self.assertIsNotNone(nxt)
        gap = (datetime.date.fromisoformat(nxt["date"]) - datetime.date.fromisoformat(r["date"])).days
        self.assertTrue(11 <= gap <= 17, gap)
        self.assertEqual((nxt["status"], nxt["is_first_clean"], nxt["series_visit"]),
                         ("confirmed", 0, 2))
        plain = pricing.quote(app.CFG, {"service": "residential", "tier_id": "t2",
                                        "frequency": "biweekly", "city": "Tampa",
                                        "is_first_clean": False})
        self.assertLess(nxt["total_cents"], plain["total"], "visit 2 must keep the 15% intro")
        self.assertGreater(self.con.execute("SELECT COUNT(*) FROM tasks WHERE booking_id=?",
                                            (nxt["id"],)).fetchone()[0], 0)

        # Completing it again (or twice) never double-books.
        app.schedule_next_visit(self.con, r["id"])
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM bookings WHERE recurring_from=?",
                                          (r["id"],)).fetchone()[0], 1)

    def test_the_fourth_visit_is_full_price(self):
        r = self.book("Fourth", skip=1)
        self.con.execute("UPDATE bookings SET series_visit=3 WHERE id=?", (r["id"],))
        self.complete(r["id"])
        plain = pricing.quote(app.CFG, {"service": "residential", "tier_id": "t2",
                                        "frequency": "biweekly", "city": "Tampa",
                                        "is_first_clean": False})
        self.assertEqual(self.child(r["id"])["total_cents"], plain["total"])

    def test_one_time_jobs_do_not_repeat(self):
        r = self.book("Oneoff", frequency="once", skip=2)
        self.complete(r["id"])
        self.assertIsNone(self.child(r["id"]))

    def test_a_full_week_never_overbooks(self):
        r = self.book("Crowded", skip=3)
        target = datetime.date.fromisoformat(r["date"]) + datetime.timedelta(days=14)
        days = [(target + datetime.timedelta(days=x)).isoformat() for x in range(-3, 4)]
        for d in days:
            self.con.execute("INSERT OR REPLACE INTO blackouts (date, reason) VALUES (?, 'test')", (d,))
        self.con.commit()
        try:
            self.complete(r["id"])
            self.assertIsNone(self.child(r["id"]))
        finally:
            self.con.executemany("DELETE FROM blackouts WHERE date=?", [(d,) for d in days])
            self.con.commit()

    def test_reminders_go_once(self):
        r = self.book("Remindme", frequency="once", skip=4)
        day = datetime.date.fromisoformat(r["date"])
        self.assertGreaterEqual(app.send_reminders(self.con, day), 1)
        self.assertEqual(app.send_reminders(self.con, day), 0)


if __name__ == "__main__":
    unittest.main()
