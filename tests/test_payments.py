"""Card payments and contractor payouts.

Pay math is pure and tested directly. The Stripe flow runs end to end against
a fake Stripe on localhost, so no real key, card or network is ever involved:
book -> save card -> job completed -> card charged -> payout line written ->
Friday summary -> Nate marks the cleaner paid -> 1099 totals.
"""
import datetime, hashlib, hmac, http.cookiejar, json, os, sys, tempfile, threading
import time, unittest, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="tm-payments-"))
os.environ["DAILY_TEXT"] = "0"
sys.path.insert(0, os.path.join(ROOT, "server"))
import app, db, payments, payouts  # noqa: E402


class PayMathTest(unittest.TestCase):

    def test_schedule_a_is_half_the_job(self):
        self.assertEqual(payouts.compute_pay("split_a", 15000), (7500, []))

    def test_schedule_b_caps_at_65_percent(self):
        pay, flags = payouts.compute_pay("split_b", 15000, company_rate_cents=11000)
        self.assertEqual(pay, 9750)
        self.assertIn("capped", flags)

    def test_schedule_b_pays_their_rate_under_the_cap(self):
        self.assertEqual(payouts.compute_pay("split_b", 30000, company_rate_cents=15000),
                         (15000, []))

    def test_schedule_b_always_leaves_45_dollars(self):
        # 65% of $115 is $74.75, which would leave $40.25. The $45 floor wins.
        pay, flags = payouts.compute_pay("split_b", 11500, company_rate_cents=9000)
        self.assertEqual(pay, 7000)
        self.assertEqual(11500 - pay, payouts.MIN_MARGIN_CENTS)

    def test_hourly_is_rate_times_hours(self):
        pay, flags = payouts.compute_pay("hourly", 18500, hours=3.5, hourly_rate_cents=2000)
        self.assertEqual(pay, 7000)
        self.assertIn("hourly", flags)
        self.assertNotIn("low_margin", flags)

    def test_hourly_flags_a_thin_margin_instead_of_cutting_pay(self):
        pay, flags = payouts.compute_pay("hourly", 11500, hours=4, hourly_rate_cents=2000)
        self.assertEqual(pay, 8000)
        self.assertIn("low_margin", flags)

    def test_hourly_needs_hours(self):
        with self.assertRaises(ValueError):
            payouts.compute_pay("hourly", 15000, hours=None, hourly_rate_cents=2000)

    def test_pay_is_never_negative(self):
        self.assertEqual(payouts.compute_pay("split_b", 3000, company_rate_cents=5000)[0], 0)

    def test_weeks_run_saturday_to_friday(self):
        f = payouts.week_ending_friday
        self.assertEqual(f("2026-10-30"), datetime.date(2026, 10, 30))   # Friday
        self.assertEqual(f("2026-10-26"), datetime.date(2026, 10, 30))   # Monday
        self.assertEqual(f("2026-10-31"), datetime.date(2026, 11, 6))    # Saturday

    def test_implausible_durations_are_ignored(self):
        self.assertEqual(payouts.hours_between("2026-10-27 09:00:00", "2026-10-27 12:30:00"), 3.5)
        self.assertIsNone(payouts.hours_between("2026-10-27 09:00:00", "2026-10-28 12:30:00"))

    def test_hourly_summary_carries_the_1099_warning(self):
        s = {"through": "2026-10-30", "total_cents": 7000, "warning": payouts.HOURLY_1099_WARNING,
             "cleaners": [{"name": "Ana", "method": "Zelle", "handle": "8135550100",
                           "amount_cents": 7000, "jobs": [{}], "needs_attention": False}]}
        text = payouts.text_summary(s, app.notify._money)
        self.assertIn("Ana $70.00 (1 job) -> Zelle 8135550100", text)
        self.assertIn("attorney", text)


class StripeHelpersTest(unittest.TestCase):

    def test_nested_params_flatten_the_way_stripe_wants(self):
        flat = payments._flatten({"metadata": {"ref": "TM-1"},
                                  "line_items": [{"quantity": 1}], "off_session": True})
        self.assertIn(("metadata[ref]", "TM-1"), flat)
        self.assertIn(("line_items[0][quantity]", "1"), flat)
        self.assertIn(("off_session", "true"), flat)

    def test_mode_follows_the_key(self):
        old = os.environ.get("STRIPE_SECRET_KEY")
        try:
            os.environ["STRIPE_SECRET_KEY"] = "sk_test_x"
            self.assertEqual(payments.mode(), "test")
            os.environ["STRIPE_SECRET_KEY"] = "sk_live_x"
            self.assertEqual(payments.mode(), "live")
            os.environ["STRIPE_SECRET_KEY"] = ""
            self.assertEqual(payments.mode(), "off")
        finally:
            os.environ["STRIPE_SECRET_KEY"] = old or ""

    def _sign(self, body, secret, ts):
        return "t=%d,v1=%s" % (ts, hmac.new(secret.encode(), b"%d." % ts + body,
                                            hashlib.sha256).hexdigest())

    def test_webhook_signature_is_checked(self):
        body = b'{"type":"x"}'
        ts = int(time.time())
        self.assertEqual(payments.verify_webhook(body, self._sign(body, "whsec_a", ts),
                                                 "whsec_a")["type"], "x")
        with self.assertRaises(ValueError):
            payments.verify_webhook(body, self._sign(body, "whsec_b", ts), "whsec_a")
        with self.assertRaises(ValueError):
            payments.verify_webhook(body, self._sign(body, "whsec_a", ts - 3600), "whsec_a")

    def test_card_fee_matches_the_economics_config(self):
        self.assertEqual(payments.card_fee_cents(15000, app.CFG), 465)


# ------------------------------------------------------------------ fake Stripe

class FakeStripe(BaseHTTPRequestHandler):
    sessions, intents, decline = {}, [], False

    def log_message(self, *a):
        pass

    def _out(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        sid = urllib.parse.urlparse(self.path).path.rsplit("/", 1)[1]
        self._out(200, FakeStripe.sessions[sid])

    def do_POST(self):
        assert self.headers["Authorization"].startswith("Basic ")
        n = int(self.headers.get("Content-Length") or 0)
        f = dict(urllib.parse.parse_qsl(self.rfile.read(n).decode()))
        p = self.path
        if p == "/v1/customers":
            return self._out(200, {"id": "cus_test1"})
        if p == "/v1/checkout/sessions":
            sid = "cs_test_%d" % (len(FakeStripe.sessions) + 1)
            s = {"id": sid, "mode": f["mode"], "status": "open", "customer": f.get("customer"),
                 "client_reference_id": f["client_reference_id"],
                 "metadata": {"ref": f["metadata[ref]"]},
                 "url": "https://checkout.stripe.test/%s" % sid,
                 "amount_total": int(f.get("line_items[0][price_data][unit_amount]") or 0)}
            FakeStripe.sessions[sid] = s
            return self._out(200, s)
        if p == "/v1/payment_intents":
            FakeStripe.intents.append(f)
            if FakeStripe.decline:
                return self._out(402, {"error": {"message": "Your card was declined.",
                                                 "code": "card_declined"}})
            return self._out(200, {"id": "pi_test_%d" % len(FakeStripe.intents),
                                   "status": "succeeded",
                                   "amount_received": int(f["amount"])})
        self._out(404, {"error": {"message": "no route " + p}})


class PaymentFlowTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db.init()
        cls.stripe = ThreadingHTTPServer(("127.0.0.1", 0), FakeStripe)
        threading.Thread(target=cls.stripe.serve_forever, daemon=True).start()
        payments.API_BASE = "http://127.0.0.1:%d" % cls.stripe.server_address[1]
        os.environ["STRIPE_SECRET_KEY"] = "sk_test_fake"
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

        con = db.connect()
        for email, role in (("owner-pay@example.com", "owner"), ("ana-pay@example.com", "cleaner")):
            if not con.execute("SELECT 1 FROM staff WHERE email=?", (email,)).fetchone():
                h, s = db.hash_password("testpass123")
                con.execute("INSERT INTO staff (name,email,role,pw_hash,pw_salt,created_at) "
                            "VALUES (?,?,?,?,?,?)", ("Ana Test" if role == "cleaner" else "Nate",
                                                     email, role, h, s, db.now()))
        con.commit()
        cls.cleaner_id = con.execute("SELECT id FROM staff WHERE email='ana-pay@example.com'"
                                     ).fetchone()[0]
        con.close()
        cls.jar = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        st, _ = cls.call("POST", "/api/auth/login",
                         {"email": "owner-pay@example.com", "password": "testpass123"})
        assert st == 200

    @classmethod
    def tearDownClass(cls):
        os.environ["STRIPE_SECRET_KEY"] = ""
        for s in (cls.srv, cls.stripe):
            s.shutdown()
            s.server_close()

    @classmethod
    def call(cls, method, path, body=None):
        req = urllib.request.Request(
            cls.base + path, data=json.dumps(body).encode() if body is not None else None,
            method=method, headers={"Content-Type": "application/json"})
        try:
            with cls.jar.open(req, timeout=10) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def _book(self, who, test_payments=True):
        for off in (0, 40):
            month = (datetime.date.today().replace(day=1)
                     + datetime.timedelta(days=off)).strftime("%Y-%m")
            _, a = self.call("GET", "/api/availability?month=" + month)
            for d in a["days"]:
                if d.get("open") and d.get("slots"):
                    st, r = self.call("POST", "/api/bookings", {
                        "name": who, "email": "%s@example.com" % who.lower(),
                        "phone": "8135550100", "address": "1 Bayshore Blvd", "city": "Tampa",
                        "zip": "33606", "date": d["date"], "slot": d["slots"][-1],
                        "tier_id": "t2", "frequency": "biweekly", "accept_terms": True,
                        "test_payments": test_payments})
                    if st == 200:
                        return r
        raise AssertionError("no open slot to book")

    def _complete(self, bid, hours=None):
        self.call("POST", "/api/admin/bookings/%d" % bid, {"assigned_to": self.cleaner_id})
        if hours:
            con = db.connect()
            start = datetime.datetime.now() - datetime.timedelta(hours=hours)
            con.execute("UPDATE bookings SET started_at=? WHERE id=?",
                        (start.replace(microsecond=0).isoformat(sep=" "), bid))
            con.commit(); con.close()
        return self.call("POST", "/api/admin/bookings/%d" % bid, {"status": "completed"})

    def _row(self, bid):
        con = db.connect()
        r = dict(con.execute("SELECT * FROM bookings WHERE id=?", (bid,)).fetchone())
        con.close()
        return r

    def test_public_booking_hides_card_step_in_test_mode(self):
        r = self._book("Plainvisitor", test_payments=False)
        self.assertIsNone(r["card_url"])

    def test_save_card_then_charge_on_completion(self):
        r = self._book("Cardholder")
        self.assertTrue(r["card_url"].startswith("https://checkout.stripe.test/"))
        self.assertEqual(r["card_mode"], "test")

        sid = r["card_url"].rsplit("/", 1)[1]
        FakeStripe.sessions[sid].update(status="complete", setup_intent={
            "id": "seti_1", "status": "succeeded", "payment_method": "pm_card_visa"})
        st, back = self.call("GET", "/api/payments/return?session_id=" + sid)
        self.assertEqual((st, back["result"]), (200, "card_saved"))
        self.assertEqual(self._row(r["id"])["payment_status"], "card_saved")

        st, _ = self._complete(r["id"], hours=3)
        self.assertEqual(st, 200)
        row = self._row(r["id"])
        self.assertEqual(row["payment_status"], "paid")
        self.assertEqual(row["paid_cents"], r["quote"]["total"])
        self.assertEqual(FakeStripe.intents[-1]["payment_method"], "pm_card_visa")
        self.assertEqual(FakeStripe.intents[-1]["off_session"], "true")

        # The return page firing again must not double-record.
        self.assertFalse(app.mark_paid(db.connect(), r["id"], 100, "card"))

        st, summ = self.call("GET", "/api/owner/summary")
        self.assertEqual(st, 200)
        self.assertNotIn(r["id"], [u["id"] for u in summ["unpaid"]])
        ana = [c for c in summ["payouts_due"]["cleaners"] if c["staff_id"] == self.cleaner_id]
        if payouts.week_ending_friday(r["date"]) <= payouts.week_ending_friday(app.local_today()):
            self.assertTrue(ana)

        con = db.connect()
        line = dict(con.execute("SELECT * FROM payouts WHERE booking_id=?", (r["id"],)).fetchone())
        con.close()
        self.assertEqual(line["pay_basis"], "split_a")
        self.assertEqual(line["pay_cents"], round(r["quote"]["total"] * 0.5))
        self.assertAlmostEqual(line["hours"], 3, places=1)

    def test_no_card_means_a_pay_link_and_it_settles(self):
        r = self._book("Nocard", test_payments=False)
        self._complete(r["id"])
        row = self._row(r["id"])
        self.assertEqual(row["payment_status"], "link_sent")
        sid = row["pay_link_url"].rsplit("/", 1)[1]
        self.assertEqual(FakeStripe.sessions[sid]["amount_total"], r["quote"]["total"])

        FakeStripe.sessions[sid].update(status="complete", payment_status="paid",
                                        payment_intent={"id": "pi_link", "payment_method": "pm_x"})
        st, back = self.call("GET", "/api/payments/return?session_id=" + sid)
        self.assertEqual(back["result"], "paid")
        self.assertEqual(self._row(r["id"])["paid_method"], "card")

    def test_a_decline_falls_back_to_a_pay_link(self):
        r = self._book("Decliner")
        sid = r["card_url"].rsplit("/", 1)[1]
        FakeStripe.sessions[sid].update(status="complete", setup_intent={
            "id": "seti_2", "status": "succeeded", "payment_method": "pm_card_declined"})
        self.call("GET", "/api/payments/return?session_id=" + sid)
        FakeStripe.decline = True
        try:
            self._complete(r["id"])
        finally:
            FakeStripe.decline = False
        row = self._row(r["id"])
        self.assertEqual(row["payment_status"], "link_sent")
        self.assertIn("declined", row["payment_error"])

    def test_hourly_cleaner_and_marking_paid_feeds_the_1099_total(self):
        st, res = self.call("POST", "/api/owner/staff/%d/pay" % self.cleaner_id, {
            "pay_basis": "hourly", "hourly_rate": "20", "payout_method": "Zelle",
            "payout_handle": "8135550100"})
        self.assertEqual(st, 200)
        self.assertIn("attorney", res["warning"])
        try:
            r = self._book("Hourlyclient", test_payments=False)
            self._complete(r["id"], hours=3)
            con = db.connect()
            line = dict(con.execute("SELECT * FROM payouts WHERE booking_id=?",
                                    (r["id"],)).fetchone())
            con.close()
            self.assertEqual(line["pay_basis"], "hourly")
            self.assertAlmostEqual(line["pay_cents"], 6000, delta=20)

            st, fixed = self.call("POST", "/api/owner/payouts/%d/hours" % line["id"], {"hours": 2.5})
            self.assertEqual((st, fixed["pay_cents"]), (200, 5000))

            # Pay everything up to this job's Friday, then check the year total.
            con = db.connect()
            con.execute("UPDATE payouts SET week_ending=? WHERE id=?",
                        (payouts.week_ending_friday(app.local_today()).isoformat(), line["id"]))
            con.commit(); con.close()
            st, paid = self.call("POST", "/api/owner/payouts/pay-cleaner",
                                 {"staff_id": self.cleaner_id, "method": "zelle",
                                  "payout_ids": [line["id"]]})
            self.assertEqual((st, paid["paid_cents"]), (200, 5000))
            _, summ = self.call("GET", "/api/owner/summary")
            ana = [c for c in summ["totals_1099"]["cleaners"] if c["staff_id"] == self.cleaner_id]
            self.assertGreaterEqual(ana[0]["paid_cents"], 5000)
            # A paid line is final.
            st, _ = self.call("POST", "/api/owner/payouts/%d/hours" % line["id"], {"hours": 9})
            self.assertEqual(st, 400)
        finally:
            self.call("POST", "/api/owner/staff/%d/pay" % self.cleaner_id, {"pay_basis": "split_a"})

    def test_owner_endpoints_need_the_owner(self):
        anon = urllib.request.Request(self.base + "/api/owner/summary")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(anon, timeout=5)
        self.assertEqual(cm.exception.code, 401)

    def test_daily_text_lists_the_day(self):
        st, r = self.call("POST", "/api/owner/daily-text", {})
        self.assertEqual(st, 200)
        self.assertIn("/owner", r["text"])

    def test_signed_webhook_records_a_payment(self):
        r = self._book("Webhooker", test_payments=False)
        self._complete(r["id"])
        sid = self._row(r["id"])["pay_link_url"].rsplit("/", 1)[1]
        FakeStripe.sessions[sid].update(status="complete", payment_status="paid",
                                        payment_intent="pi_hook")
        body = json.dumps({"type": "checkout.session.completed",
                           "data": {"object": {"id": sid}}}).encode()
        ts = int(time.time())
        sig = "t=%d,v1=%s" % (ts, hmac.new(b"whsec_t", b"%d." % ts + body,
                                           hashlib.sha256).hexdigest())
        os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_t"
        try:
            req = urllib.request.Request(self.base + "/api/stripe/webhook", data=body,
                                         method="POST", headers={"Stripe-Signature": sig,
                                                                 "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
            bad = urllib.request.Request(self.base + "/api/stripe/webhook", data=body,
                                         method="POST", headers={"Stripe-Signature": "t=1,v1=00"})
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(bad, timeout=5)
        finally:
            os.environ["STRIPE_WEBHOOK_SECRET"] = ""
        row = self._row(r["id"])
        self.assertEqual((row["payment_status"], row["stripe_payment_intent"]), ("paid", "pi_hook"))


if __name__ == "__main__":
    unittest.main()
