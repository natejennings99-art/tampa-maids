"""Referral tests.

Cleaning is a referral trade, so this loop is the cheapest growth the business
has. It is also money leaving the till, which makes correctness matter more
than usual: a code that can be reused, self-applied or pushed below zero is a
discount with no floor.
"""
import json, os, re, sqlite3, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "server"))
with open(os.path.join(ROOT, "business.json"), encoding="utf-8") as fh:
    CFG = json.load(fh)
import db as dbmod  # noqa: E402
import notify  # noqa: E402


class Codes(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.con.row_factory = sqlite3.Row
        self.con.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, referral_code TEXT)")

    def test_codes_avoid_characters_people_misread(self):
        # These get read down the phone and written on fridges.
        for _ in range(60):
            code = dbmod.new_referral_code(self.con)
            self.assertEqual(len(code), 6)
            self.assertFalse(set(code) & set("OI01"), "ambiguous character in %s" % code)
            self.assertTrue(re.fullmatch(r"[A-Z2-9]{6}", code), code)

    def test_codes_do_not_collide_with_existing_ones(self):
        seen = set()
        for _ in range(40):
            code = dbmod.new_referral_code(self.con)
            self.assertNotIn(code, seen)
            seen.add(code)
            self.con.execute("INSERT INTO customers (referral_code) VALUES (?)", (code,))


class InviteEmail(unittest.TestCase):
    def setUp(self):
        self.subject, self.text, self.html = notify.referral_invite(
            CFG, {"name": "Dana Reyes", "email": "d@example.invalid"}, "HXJ4YP")

    def test_it_shows_the_code_and_the_configured_credit(self):
        credit = CFG["pricing"]["referral_credit"]
        self.assertIn("HXJ4YP", self.text)
        self.assertIn("HXJ4YP", self.html)
        amount = "$%d" % round(credit / 100)
        self.assertIn(amount, self.text, "credit %s missing from the email" % amount)

    def test_it_is_two_sided(self):
        # A one-sided offer asks someone to do unpaid marketing. Both halves
        # have to be stated or the customer has nothing to actually say.
        low = self.text.lower()
        self.assertIn("they get", low)
        self.assertIn("you get", low)

    def test_the_credit_is_configured_and_positive(self):
        self.assertGreater(CFG["pricing"]["referral_credit"], 0)


if __name__ == "__main__":
    unittest.main()
