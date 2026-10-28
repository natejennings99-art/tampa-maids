"""Lead capture (/api/leads): the contact form and the "send me this quote" box on /book.

A lead is only worth something if Nate hears about it fast, and the endpoint is
public, so bots must not be able to fill the inbox or run up texts.
"""
import os, sys, tempfile, unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="tm-leads-"))
os.environ["DAILY_TEXT"] = "0"
sys.path.insert(0, os.path.join(ROOT, "server"))
import app, db, notify  # noqa: E402


class LeadTest(unittest.TestCase):
    def setUp(self):
        db.init()
        self.con = db.connect()
        self.addCleanup(self.con.close)
        self.before = self.count()

    def count(self):
        return self.con.execute("SELECT COUNT(*) FROM leads").fetchone()[0]

    def post(self, **body):
        return app.api_lead({"body": body, "con": self.con})

    def test_a_saved_quote_is_stored_and_texts_nate(self):
        with mock.patch.object(notify, "ping_owner") as ping:
            r = self.post(name="Dana Reyes", email="dana@example.invalid", phone="8135550100",
                          kind="saved_quote", message="Total: $172.00", website="")
        self.assertTrue(r["ok"])
        self.assertEqual(self.count(), self.before + 1)
        text = ping.call_args[0][1]
        self.assertIn("saved quote", text)
        self.assertIn("Dana Reyes", text)
        self.assertIn("8135550100", text)

    def test_the_hidden_field_traps_bots_without_telling_them(self):
        with mock.patch.object(notify, "ping_owner") as ping:
            r = self.post(name="Bot", email="bot@example.invalid", website="http://spam.example")
        self.assertTrue(r["ok"], "a bot should see the normal reply")
        self.assertEqual(self.count(), self.before)
        ping.assert_not_called()

    def test_a_text_outage_does_not_lose_the_lead(self):
        with mock.patch.object(notify, "ping_owner", side_effect=RuntimeError("down")):
            r = self.post(name="Sam Ortiz", email="sam@example.invalid")
        self.assertTrue(r["ok"])
        self.assertEqual(self.count(), self.before + 1)


if __name__ == "__main__":
    unittest.main()
