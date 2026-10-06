"""Pricing tests. The price table in business.json is the contract with the
customer, so these assert the engine agrees with it rather than re-deriving it.

Run:  python3 -m unittest discover -s tests
"""
import json, os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "server"))
import pricing  # noqa: E402

CFG = json.load(open(os.path.join(ROOT, "business.json"), encoding="utf-8"))


class TierSelection(unittest.TestCase):
    def test_every_tier_and_frequency_matches_the_published_table(self):
        for t in CFG["home_tiers"]:
            if t.get("custom_quote"):
                continue
            for freq, cents in t["prices"].items():
                q = pricing.quote(CFG, {"service": "residential",
                                        "tier_id": t["id"], "frequency": freq})
                got = (q["lines"][0]["amount"] if freq == "once"
                       else q["recurring_total"])
                self.assertEqual(got, cents,
                                 "%s/%s: table %d, quote %d" % (t["id"], freq, cents, got))

    def test_bedroom_count_picks_the_matching_tier(self):
        for beds, want in [(0, "t1"), (1, "t1"), (2, "t2"), (3, "t3"), (4, "t4")]:
            tier = pricing.find_tier(CFG, bedrooms=beds)
            self.assertEqual(tier["id"], want, "%d BR -> %s" % (beds, tier["id"]))

    def test_more_bedrooms_than_the_table_covers_is_a_custom_quote(self):
        for beds in (5, 6, 12):
            self.assertTrue(pricing.find_tier(CFG, bedrooms=beds).get("custom_quote"))

    def test_unknown_tier_id_is_an_error_not_a_cheap_quote(self):
        # Regression: this used to fall through to tiers[1], the 2 BR tier, so a
        # stale cached app would undercharge silently with nothing in the
        # response to reveal it.
        with self.assertRaises(ValueError):
            pricing.find_tier(CFG, tier_id="no-such-tier")
        self.assertIn("error", pricing.quote(
            CFG, {"service": "residential", "tier_id": "no-such-tier"}))

    def test_square_feet_maps_within_the_published_bands(self):
        for sqft, want in [(400, "t1"), (899, "t1"), (1200, "t2"),
                           (2000, "t3"), (2900, "t4"), (6000, "t5")]:
            self.assertEqual(pricing.find_tier(CFG, sqft=sqft)["id"], want,
                             "%d sqft" % sqft)

    def test_a_size_exactly_on_a_boundary_takes_the_lower_price(self):
        # The published bands share endpoints: 1,500 sq ft reads as both the top
        # of the 2 BR row and the bottom of the 3 BR row. The pricing page now
        # promises "exactly on the line between two sizes? You pay the lower
        # price", so the engine has to actually do that.
        for t in CFG["home_tiers"]:
            edge = t.get("sqft_max")
            if not edge:
                continue
            self.assertEqual(pricing.find_tier(CFG, sqft=edge)["id"], t["id"],
                             "%d sq ft should price as %s" % (edge, t["id"]))
            above = pricing.find_tier(CFG, sqft=edge + 1)
            self.assertNotEqual(above["id"], t["id"],
                                "%d sq ft should move up a tier" % (edge + 1))

    def test_nothing_specified_still_quotes_a_price(self):
        q = pricing.quote(CFG, {"service": "residential", "frequency": "biweekly"})
        self.assertNotIn("error", q)
        self.assertGreater(q["recurring_total"], 0)


class QuoteShape(unittest.TestCase):
    def test_first_visit_is_dearer_than_the_recurring_rate(self):
        q = pricing.quote(CFG, {"service": "residential", "tier_id": "t3",
                                "frequency": "biweekly"})
        self.assertTrue(q["is_first_clean"])
        self.assertGreater(q["total"], 0)
        self.assertEqual(q["recurring_total"], 18500)

    def test_lines_sum_to_the_total(self):
        for tier in ("t1", "t2", "t3", "t4"):
            q = pricing.quote(CFG, {"service": "residential", "tier_id": tier,
                                    "frequency": "biweekly", "city": "Tampa"})
            self.assertEqual(sum(l["amount"] for l in q["lines"]) + q["surcharge"]
                             + q["tax"], q["total"], tier)

    def test_outlying_cities_carry_their_published_surcharge(self):
        for city, cents in (CFG["surcharge_zones"]["cities"]).items():
            q = pricing.quote(CFG, {"service": "residential", "tier_id": "t3",
                                    "frequency": "biweekly", "city": city})
            self.assertEqual(q["surcharge"], cents, city)

    def test_home_market_cities_carry_no_surcharge(self):
        for city in ("Tampa", "St. Petersburg", "Clearwater", "tampa", "  Tampa "):
            q = pricing.quote(CFG, {"service": "residential", "tier_id": "t3",
                                    "frequency": "biweekly", "city": city})
            self.assertEqual(q["surcharge"], 0, city)

    def test_surcharge_matches_what_the_outreach_drafts_quote(self):
        # marketing/outreach-ready-to-send.md promises $15 for Apollo Beach and
        # $35 for Sarasota. If the table moves, the drafts become wrong.
        cities = CFG["surcharge_zones"]["cities"]
        self.assertEqual(cities["Apollo Beach"], 1500)
        self.assertEqual(cities["Sarasota"], 3500)

    def test_unknown_service_is_rejected(self):
        self.assertIn("error", pricing.quote(CFG, {"service": "spaceship-detailing"}))


if __name__ == "__main__":
    unittest.main()
