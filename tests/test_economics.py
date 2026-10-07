"""Unit-economics tests.

The model answers "how many clients is a living?", so it has to stay tied to
the real price table and the real contractor split. A model that quietly drifts
from the prices actually charged is worse than not having one.

Run:  python3 -m unittest discover -s tests
"""
import json, os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
with open(os.path.join(ROOT, "business.json"), encoding="utf-8") as fh:
    CFG = json.load(fh)
import unit_economics as ue  # noqa: E402


class Contribution(unittest.TestCase):
    def test_the_split_matches_the_contractor_agreement(self):
        # The agreement says 50% of the cleaning price. If that changes, the
        # job offers and the ads have to change with it, so fail loudly.
        self.assertEqual(CFG["economics"]["contractor_share"], 0.50)

    def test_a_job_splits_evenly_at_a_fifty_percent_share(self):
        for price in (11500, 15000, 31000, 120000):
            keep, pay, card = ue.contribution(price)
            self.assertEqual(pay, price // 2, price)
            self.assertEqual(keep + pay + card, price, "money vanished at %d" % price)

    def test_card_fees_are_only_counted_when_card_payments_exist(self):
        # No Stripe is built, so counting processing fees would understate the
        # margin and flatter nothing.
        self.assertFalse(CFG["economics"]["card_payments_live"])
        _, _, card = ue.contribution(15000)
        self.assertEqual(card, 0)

    def test_every_tier_leaves_a_positive_contribution(self):
        for t in CFG["home_tiers"]:
            if not t.get("prices"):
                continue
            for freq, price in t["prices"].items():
                keep, _, _ = ue.contribution(price)
                self.assertGreater(keep, 0, "%s/%s" % (t["id"], freq))

    def test_fixed_costs_are_small_enough_that_overheads_are_not_the_risk(self):
        fixed = sum(CFG["economics"]["fixed_monthly_cents"].values())
        anchor = next(t for t in CFG["home_tiers"] if t["id"] == "t2")
        keep, _, _ = ue.contribution(anchor["prices"]["biweekly"])
        # Break-even should be a couple of jobs a month, not a business plan.
        self.assertLess(fixed / float(keep), 5.0,
                        "break-even is %.1f jobs/month -- overheads have grown"
                        % (fixed / float(keep)))

    def test_the_insurance_figure_matches_the_quote_on_file(self):
        # $938/yr from Insureon, still unbound. If it is bound at a different
        # premium this must be updated or the model lies.
        self.assertEqual(CFG["economics"]["fixed_monthly_cents"]["insurance_bop"],
                         round(93800 / 12))


if __name__ == "__main__":
    unittest.main()
