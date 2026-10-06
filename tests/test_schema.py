"""Structured-data tests.

The offer catalogue puts prices into Google's hands, so a drift between it and
business.json means search results quoting a price the booking form refuses to
honour. That is worse than having no markup at all, hence these.

Run:  python3 -m unittest discover -s tests
"""
import json, os, re, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "business.json"), encoding="utf-8"))
HOME = os.path.join(ROOT, "web", "index.html")


def _home_schema():
    with open(HOME, encoding="utf-8") as fh:
        html = fh.read()
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert blocks, "no JSON-LD on the home page"
    return json.loads(blocks[0])


@unittest.skipUnless(os.path.exists(HOME), "web/index.html not built")
class HomeSchema(unittest.TestCase):
    def setUp(self):
        self.d = _home_schema()

    def test_it_is_a_cleaning_business_with_the_real_phone(self):
        self.assertEqual(self.d["@type"], "HouseCleaningService")
        self.assertEqual(self.d["telephone"], CFG["phone"])

    def test_no_invented_ratings(self):
        # There are no reviews yet. Marking up a rating we do not have is both
        # against Google's policy and a false claim.
        self.assertNotIn("aggregateRating", self.d)
        self.assertNotIn("review", self.d)

    def test_offer_catalog_prices_match_business_json(self):
        offers = self.d["hasOfferCatalog"]["itemListElement"]
        got = {o["itemOffered"]["name"]: (o["priceSpecification"]["minPrice"],
                                          o["priceSpecification"]["maxPrice"])
               for o in offers}
        tiers = [t for t in CFG["home_tiers"] if t.get("prices")]
        want = {
            "Recurring House Cleaning": (min(t["prices"]["biweekly"] for t in tiers),
                                         max(t["prices"]["monthly"] for t in tiers)),
            "Deep Cleaning": (min(t["prices"]["once"] for t in tiers),
                              max(t["prices"]["once"] for t in tiers)),
        }
        for sid, label in (("move", "Move-In / Move-Out Cleaning"),
                           ("str", "Vacation Rental Turnover"),
                           ("construction", "Post-Construction Cleaning")):
            s = next((x for x in CFG["services"] if x["id"] == sid), None)
            if s and s.get("price_min"):
                want[label] = (s["price_min"], s["price_max"])
        for name, (lo, hi) in want.items():
            self.assertIn(name, got, "missing offer: %s" % name)
            self.assertEqual(got[name], ("%.2f" % (lo / 100.0), "%.2f" % (hi / 100.0)), name)

    def test_every_offer_uses_the_configured_currency(self):
        for o in self.d["hasOfferCatalog"]["itemListElement"]:
            self.assertEqual(o["priceSpecification"]["priceCurrency"],
                             CFG["pricing"]["currency"])

    def test_geo_is_inside_the_tampa_bay_area(self):
        g = self.d.get("geo")
        self.assertIsNotNone(g, "no geo coordinates")
        self.assertTrue(26.5 < g["latitude"] < 28.6, g)
        self.assertTrue(-83.2 < g["longitude"] < -82.0, g)


if __name__ == "__main__":
    unittest.main()
