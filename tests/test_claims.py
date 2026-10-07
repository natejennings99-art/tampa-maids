"""Claims tests: the site must not say things that are not true yet.

Tampa Maids has no bound insurance policy, no screening vendor, no employees and
no reviews. Each of those has already appeared on the live site at some point,
and the insurance one survived several rounds of flagging because it was worded
as a forward promise rather than a flat claim. These tests make the wording a
build failure instead of a thing someone has to keep noticing.

Run:  python3 -m unittest discover -s tests
"""
import json, os, re, sys, unittest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"))
import notify  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
with open(os.path.join(ROOT, "business.json"), encoding="utf-8") as fh:
    CFG = json.load(fh)


def _page_text():
    """Rendered text of every built page, keyed by filename."""
    out = {}
    for root, _, files in os.walk(WEB):
        for f in files:
            if not f.endswith(".html"):
                continue
            with open(os.path.join(root, f), encoding="utf-8") as fh:
                out[os.path.relpath(os.path.join(root, f), WEB)] = re.sub(r"<[^>]+>", " ", fh.read())
    return out


@unittest.skipUnless(os.path.isdir(WEB), "site not built")
class NoUnearnedClaims(unittest.TestCase):
    def setUp(self):
        self.pages = _page_text()
        self.assertTrue(self.pages, "no built pages found")

    def _offenders(self, pattern):
        rx = re.compile(pattern, re.I)
        return {name: " ".join(rx.search(t).group(0).split())
                for name, t in self.pages.items() if rx.search(t)}

    def test_no_insurance_claim_while_the_policy_is_unbound(self):
        if CFG["insurance"]["bound"]:
            self.skipTest("policy is bound; the claim is allowed")
        # "fully insured before your first clean" was the previous wording. It is
        # a forward promise, so it is not literally false -- but it answered the
        # FAQ "Are you insured?" and sat on every page as a badge, so a customer
        # read it as yes. Net impression is what matters, so it is barred too.
        bad = self._offenders(r"(fully insured|we are insured|we're insured|bonded)")
        self.assertEqual(bad, {}, "unearned insurance claim: %s" % bad)

    def test_no_background_check_claim(self):
        # There is no screening vendor.
        bad = self._offenders(r"background[- ]check")
        self.assertEqual(bad, {}, "unearned screening claim: %s" % bad)

    def test_no_employee_claim(self):
        # Cleaners are 1099 independent contractors, not employees. Saying
        # otherwise is both untrue and a worker-classification problem.
        # The negated form is correct and must not trip this: the service
        # agreement says the work is done by contractors "not by our employees".
        bad = {n: m for n, m in self._offenders(
                   r"\bW-2\b|(?<!not by )(?<!not )our employees|employee team").items()
               if "not by our employees" not in " ".join(self.pages[n].split())}
        self.assertEqual(bad, {}, "unearned employment claim: %s" % bad)

    def test_no_testimonials_without_the_verified_flag(self):
        for t in CFG.get("testimonials") or []:
            self.assertTrue(t.get("verified"),
                            "unverified testimonial would render: %r" % t.get("name"))

    def test_the_insurance_switch_drives_every_insurance_string(self):
        ins = CFG["insurance"]
        expect = ins["claim_when_bound"] if ins["bound"] else ins["claim_when_unbound"]
        self.assertEqual(CFG["license"], expect,
                         "license line is out of step with insurance.bound")
        faq = next((f for f in CFG["faq"] if "insured" in f["q"].lower()), None)
        self.assertIsNotNone(faq, "the 'Are you insured?' FAQ went missing")
        self.assertEqual(faq["a"], ins["faq_when_bound"] if ins["bound"] else ins["faq_when_unbound"])


if __name__ == "__main__":
    unittest.main()


class ReviewRequest(unittest.TestCase):
    """The review ask is the gate on the Google local pack, so it has to exist
    and it has to be compliant. Asking only satisfied customers, or routing
    unhappy ones somewhere private, is review gating: it breaks Google's
    policies and the FTC's endorsement rules."""

    def setUp(self):
        self.subject, self.text, self.html = notify.review_request(
            CFG, {"ref": "TM-TEST"}, {"name": "Dana Reyes", "email": "d@example.invalid"})

    def test_it_links_to_the_real_review_url(self):
        self.assertTrue(CFG.get("review_url"), "no review_url configured")
        self.assertIn(CFG["review_url"], self.text)
        self.assertIn(CFG["review_url"], self.html)

    def test_it_does_not_gate_on_sentiment(self):
        blob = (self.text + " " + self.html).lower()
        for phrase in ("if you were happy", "if you enjoyed", "were you satisfied",
                       "if you had a good", "only if you"):
            self.assertNotIn(phrase, blob, "review gating phrase: %r" % phrase)
        # It must invite the unhappy ones too, not just the pleased ones.
        self.assertIn("wasn't right", self.text)

    def test_it_offers_no_incentive(self):
        blob = (self.text + " " + self.html).lower()
        for word in ("discount", "voucher", "gift card", "free clean", "% off",
                     "in exchange", "reward"):
            self.assertNotIn(word, blob, "incentivised review: %r" % word)

    def test_it_is_addressed_to_the_customer(self):
        self.assertIn("Dana", self.text)
        self.assertTrue(self.subject.strip())
