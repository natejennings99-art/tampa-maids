import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import outreach_mail as om  # noqa: E402

ADDR = "100 Example St, Tampa, FL 33600"  # placeholder; the real one lives in state.json only
QUEUE = os.path.exists(om.OUTREACH) and os.path.exists(om.STATE)


def _real_addr():
    import json
    return (json.load(open(om.STATE, encoding="utf-8")).get("addr") or "").strip()


class OutreachMailTests(unittest.TestCase):
    def test_split_subject(self):
        s, b = om.split_subject("Subject: Hello there\n\nBody line")
        self.assertEqual(s, "Hello there"); self.assertEqual(b, "Body line")
        self.assertEqual(om.split_subject("no subject")[0], None)

    def test_footer_fills_placeholder_and_optout(self):
        body = om.finish_body("Hi\n\nNate Jennings\n[MAILING ADDRESS]\nReply \"no thanks\" and I won't email again.", ADDR)
        self.assertIn(ADDR, body); self.assertNotIn("[MAILING ADDRESS]", body)
        self.assertEqual(body.count("no thanks"), 1)

    def test_footer_added_when_missing(self):
        body = om.finish_body("Hi\n\nNate Jennings · Tampa Maids Cleaning · (571) 317-3211 · x@y.com", ADDR)
        self.assertIn(ADDR, body); self.assertIn("no thanks", body)

    def test_duplicate_signoff_dropped(self):
        body = om.finish_body("Hi\n\nNate Jennings\nJennings Media | jennings-media.com | (571) 317-3211\n[MAILING ADDRESS]\nReply \"no thanks\" and I won't email again.\n\nNate Jennings · Jennings Media · (571) 317-3211 · x@y.com · jennings-media.com", ADDR)
        self.assertEqual(body.count("(571) 317-3211"), 1)

    @unittest.skipUnless(QUEUE, "private outreach queue not present")
    def test_sendable_excludes_sent_expired_and_twins(self):
        ready, skipped = om.sendable(today=datetime.date.today().isoformat())
        ids = {r["id"] for r in ready}; why = dict(skipped)
        self.assertTrue(ready)
        for r in ready:
            self.assertRegex(r["to"], r"@"); self.assertTrue(r["subject"]); self.assertIn(_real_addr(), r["body"])
        for t in om.HOLD_TWINS:
            self.assertNotIn(t, ids); self.assertIn(t, why)
        cutoff = (datetime.date.today() - datetime.timedelta(days=om.GRACE_DAYS)).isoformat()
        self.assertTrue(all(not (r["exp"] and r["exp"] < cutoff) for r in ready))


    @unittest.skipUnless(QUEUE, "private outreach queue not present")
    def test_domain_cap(self):
        import collections
        ready, _ = om.sendable()
        c = collections.Counter(r["to"].split("@")[1].lower() for r in ready)
        for dom, n in c.items():
            if dom not in om.FREE_MAIL:
                self.assertLessEqual(n, om.DOMAIN_CAP, dom)


if __name__ == "__main__":
    unittest.main()
