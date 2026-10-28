"""Customer texts need a ticked box (TCPA, Twilio A2P 10DLC). The box is
optional, it is recorded with time and IP, and nothing texts a customer who
didn't tick it -- even with CUSTOMER_SMS=1."""
import datetime, os, sys, tempfile, unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="tm-sms-"))
os.environ["DAILY_TEXT"] = "0"
sys.path.insert(0, os.path.join(ROOT, "server"))
import app, db, notify  # noqa: E402


class SmsConsentTest(unittest.TestCase):
    def setUp(self):
        db.init()
        self.con = db.connect()
        self.addCleanup(self.con.close)

    def book(self, email, consent):
        day = datetime.date.today() + datetime.timedelta(days=3)
        while True:
            a = app.api_availability({"query": {"date": [day.isoformat()],
                                                "service": ["residential"]}, "con": self.con})
            if a.get("open") and a.get("slots"):
                break
            day += datetime.timedelta(days=1)
        body = {"name": "Pat Lee", "email": email, "phone": "8135550111",
                "address": "1 Main St", "city": "Tampa", "zip": "33602",
                "date": day.isoformat(), "slot": a["slots"][0], "accept_terms": True,
                "service": "residential", "tier_id": "t2", "frequency": "once",
                "sms_consent": consent}
        ctx = {"body": body, "con": self.con, "ip": "203.0.113.9",
               "cookies": {}, "headers": {}}
        with mock.patch.object(notify, "send_sms", return_value=True) as sms, \
             mock.patch.dict(os.environ, {"CUSTOMER_SMS": "1"}):
            app.api_create_booking(ctx)
        cust = db.one(self.con.execute("SELECT * FROM customers WHERE email=?", (email,)))
        to_customer = [c for c in sms.call_args_list if c.args[0] == "8135550111"]
        return cust, to_customer

    def test_a_ticked_box_is_recorded_and_the_first_text_says_stop(self):
        cust, texts = self.book("yes@example.invalid", True)
        self.assertTrue(cust["sms_consent_at"])
        self.assertEqual(cust["sms_consent_ip"], "203.0.113.9")
        self.assertEqual(len(texts), 1)
        self.assertIn("Reply STOP", texts[0].args[1])

    def test_no_box_no_texts(self):
        cust, texts = self.book("no@example.invalid", False)
        self.assertIsNone(cust["sms_consent_at"])
        self.assertEqual(texts, [])

    def test_the_box_is_optional_on_the_form(self):
        html = open(os.path.join(ROOT, "web", "book.html"), encoding="utf-8").read()
        box = html[html.index('id="smsBox"'):html.index("</label>", html.index('id="smsBox"'))]
        self.assertIn('id="f-sms"', box)
        self.assertNotIn("checked", box.split('id="f-sms"')[1].split(">")[0])
        for must in ("STOP", "HELP", "Msg &amp; data rates may apply", "Not required"):
            self.assertIn(must, box)


if __name__ == "__main__":
    unittest.main()
