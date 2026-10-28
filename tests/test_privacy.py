"""The privacy policy exists, is linked from every page, and says what Meta and
Twilio need it to say. Meta won't run ads with the Pixel without one, and the
A2P 10DLC review reads the text-message section."""
import glob, os, re, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
STAFF = ("admin", "app", "owner", "google")   # not built from the public shell


class PrivacyPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import json
        from privacy_page import privacy_page
        cfg = json.load(open(os.path.join(ROOT, "business.json"), encoding="utf-8"))
        cls.cfg = cfg
        cls.html = privacy_page(cfg)
        cls.text = re.sub(r"<[^>]+>", " ", cls.html)

    def test_it_builds_to_the_published_page(self):
        path = os.path.join(WEB, "privacy.html")
        self.assertTrue(os.path.exists(path), "run tools/build_site2.py")
        built = open(path, encoding="utf-8").read()
        self.assertIn('rel="canonical" href="https://tampamaidscleaning.com/privacy"', built)
        self.assertIn("Effective October 27, 2026", built)

    def test_it_covers_what_meta_and_twilio_look_for(self):
        for must in ("do not sell", "Reply STOP", "HELP", "Message and data rates may apply",
                     "Meta Pixel", "Conversions API", "Google Analytics", "Stripe",
                     "children under 13", self.cfg["email"], self.cfg["phone"]):
            self.assertIn(must, self.text, must)

    def test_it_makes_no_claims_we_cannot_back(self):
        low = self.text.lower()
        for banned in ("insured", "bonded", "bank-level", "we never share",
                       "background-check", "employee"):
            self.assertNotIn(banned, low, banned)

    def test_every_public_page_links_to_it(self):
        pages = [p for p in glob.glob(os.path.join(WEB, "**", "*.html"), recursive=True)
                 if not os.path.relpath(p, WEB).startswith(STAFF)]
        self.assertGreater(len(pages), 40)
        missing = [os.path.relpath(p, WEB) for p in pages
                   if 'href="/privacy"' not in open(p, encoding="utf-8").read()]
        self.assertEqual(missing, [], "footer link missing on: %s" % missing)

    def test_the_booking_form_links_to_it(self):
        book = open(os.path.join(WEB, "book.html"), encoding="utf-8").read()
        agree = book[book.index('id="agreeBox"'):book.index("</label>", book.index('id="agreeBox"'))]
        self.assertIn('href="/privacy"', agree)

    def test_it_is_in_the_sitemap(self):
        self.assertIn("/privacy</loc>", open(os.path.join(WEB, "sitemap.xml")).read())


if __name__ == "__main__":
    unittest.main()
