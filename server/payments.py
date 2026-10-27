"""Card payments through Stripe, stdlib only (urllib + hmac, no SDK).

The site promises "payment is due on the day of service, nothing is taken
when you book", so the flow is:

  1. Booking: the customer is offered Stripe Checkout in *setup* mode. That
     saves a card against a Stripe customer and charges nothing.
  2. Job completed: the saved card is charged off-session for the booking
     total. If there is no saved card, or the bank wants the customer to
     approve it (3-D Secure), a Checkout *pay link* is made instead and
     emailed/texted to them.
  3. Stripe tells us what happened, either through the webhook
     (/api/stripe/webhook, needs STRIPE_WEBHOOK_SECRET) or when the customer
     lands back on the site (/api/payments/return), which needs no webhook
     at all. Both are idempotent.

Environment (set by the owner in Render, never committed):

  STRIPE_SECRET_KEY       sk_test_... while testing, sk_live_... when real
  STRIPE_WEBHOOK_SECRET   whsec_...   optional, makes payment updates instant
  STRIPE_API_BASE         tests only: points the client at a fake Stripe

A test key only ever talks to Stripe's test mode, which refuses real cards,
so the public booking page offers card saving only with a live key, or when
the page was opened with ?testpay=1.
"""
import os, json, hmac, hashlib, time, base64
import urllib.request, urllib.parse, urllib.error

API_BASE = os.environ.get("STRIPE_API_BASE", "https://api.stripe.com").rstrip("/")


def _key():
    # Read on every call so tests (and a Render env change) take effect
    # without re-importing the module.
    return os.environ.get("STRIPE_SECRET_KEY", "").strip()


def mode():
    """'live', 'test' or 'off'."""
    k = _key()
    if k.startswith(("sk_live_", "rk_live_")):
        return "live"
    if k.startswith(("sk_test_", "rk_test_")):
        return "test"
    return "off"


def configured():
    return mode() != "off"


class StripeError(Exception):
    def __init__(self, message, code=None, decline_code=None, payment_intent=None):
        super().__init__(message)
        self.code = code
        self.decline_code = decline_code
        self.payment_intent = payment_intent


def _flatten(params, prefix=""):
    """Stripe wants nested form fields: metadata[ref]=..., line_items[0][price]=..."""
    out = []
    items = params.items() if isinstance(params, dict) else enumerate(params)
    for k, v in items:
        key = "%s[%s]" % (prefix, k) if prefix else str(k)
        if isinstance(v, (dict, list, tuple)):
            out.extend(_flatten(v, key))
        elif v is None:
            continue
        elif isinstance(v, bool):
            out.append((key, "true" if v else "false"))
        else:
            out.append((key, str(v)))
    return out


def _call(method, path, params=None, idempotency_key=None):
    if not configured():
        raise StripeError("Card payments are not set up yet (no STRIPE_SECRET_KEY).")
    url = API_BASE + path
    data = None
    if params and method == "GET":
        url += "?" + urllib.parse.urlencode(_flatten(params))
    elif params:
        data = urllib.parse.urlencode(_flatten(params)).encode()
    auth = base64.b64encode((_key() + ":").encode()).decode()
    headers = {"Authorization": "Basic " + auth,
               "Content-Type": "application/x-www-form-urlencoded",
               "Stripe-Version": "2024-06-20"}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode()).get("error") or {}
        except Exception:                                    # noqa: BLE001
            err = {}
        raise StripeError(err.get("message") or "Stripe error %s" % e.code,
                          err.get("code"), err.get("decline_code"),
                          err.get("payment_intent"))
    except urllib.error.URLError as e:
        raise StripeError("Couldn't reach Stripe: %s" % e.reason)


# ---------------------------------------------------------------- flows

def ensure_customer(existing_id, name, email, phone):
    if existing_id:
        return existing_id
    c = _call("POST", "/v1/customers",
              {"name": name, "email": email, "phone": phone or None})
    return c["id"]


def card_setup_session(customer_id, ref, site_url):
    """Checkout in setup mode: saves a card, charges nothing."""
    s = _call("POST", "/v1/checkout/sessions", {
        "mode": "setup",
        "customer": customer_id,
        "payment_method_types": ["card"],
        "client_reference_id": ref,
        "metadata": {"ref": ref, "purpose": "save_card"},
        "setup_intent_data": {"metadata": {"ref": ref}},
        "success_url": "%s/track?ref=%s&card=saved&session_id={CHECKOUT_SESSION_ID}"
                       % (site_url, urllib.parse.quote(ref)),
        "cancel_url": "%s/track?ref=%s&card=skipped" % (site_url, urllib.parse.quote(ref)),
    }, idempotency_key="setup-%s-%d" % (ref, int(time.time() // 600)))
    return s


def pay_link_session(customer_id, ref, amount_cents, description, site_url):
    """Checkout in payment mode: a link the customer opens to pay the visit."""
    s = _call("POST", "/v1/checkout/sessions", {
        "mode": "payment",
        "customer": customer_id or None,
        "payment_method_types": ["card"],
        "client_reference_id": ref,
        "metadata": {"ref": ref, "purpose": "pay_visit"},
        "payment_intent_data": {"metadata": {"ref": ref},
                                "setup_future_usage": "off_session"},
        "line_items": [{
            "quantity": 1,
            "price_data": {"currency": "usd", "unit_amount": int(amount_cents),
                           "product_data": {"name": description}},
        }],
        "success_url": "%s/track?ref=%s&paid=1&session_id={CHECKOUT_SESSION_ID}"
                       % (site_url, urllib.parse.quote(ref)),
        "cancel_url": "%s/track?ref=%s" % (site_url, urllib.parse.quote(ref)),
    }, idempotency_key="pay-%s-%d-%d" % (ref, amount_cents, int(time.time() // 3600)))
    return s


def charge_saved_card(customer_id, payment_method, amount_cents, ref, description):
    """Off-session charge. Returns the PaymentIntent; raises StripeError on a
    decline or when the bank needs the customer present."""
    return _call("POST", "/v1/payment_intents", {
        "amount": int(amount_cents),
        "currency": "usd",
        "customer": customer_id,
        "payment_method": payment_method,
        "off_session": True,
        "confirm": True,
        "description": description,
        "metadata": {"ref": ref},
    }, idempotency_key="charge-%s-%d" % (ref, amount_cents))


def get_session(session_id):
    return _call("GET", "/v1/checkout/sessions/%s" % urllib.parse.quote(session_id),
                 {"expand": ["setup_intent", "payment_intent"]})


def session_outcome(s):
    """Reduce a Checkout Session to what the booking needs to record.

    Returns a dict with ref, kind ('card_saved' | 'paid' | None), and the
    Stripe ids worth keeping.
    """
    ref = (s.get("metadata") or {}).get("ref") or s.get("client_reference_id")
    out = {"ref": ref, "kind": None, "customer": s.get("customer"),
           "payment_method": None, "payment_intent": None, "amount": None}
    if s.get("mode") == "setup" and s.get("status") == "complete":
        si = s.get("setup_intent") or {}
        if isinstance(si, str):
            si = _call("GET", "/v1/setup_intents/%s" % si)
        if si.get("status") == "succeeded":
            out["kind"] = "card_saved"
            out["payment_method"] = si.get("payment_method")
    elif s.get("mode") == "payment" and s.get("payment_status") == "paid":
        pi = s.get("payment_intent") or {}
        out["kind"] = "paid"
        out["amount"] = s.get("amount_total")
        if isinstance(pi, dict):
            out["payment_intent"] = pi.get("id")
            out["payment_method"] = pi.get("payment_method")
        else:
            out["payment_intent"] = pi
    return out


# ---------------------------------------------------------------- webhook

def verify_webhook(payload_bytes, sig_header, secret=None, tolerance=300, now=None):
    """Check a Stripe-Signature header. Returns the parsed event or raises
    ValueError. Implements Stripe's documented v1 scheme: HMAC-SHA256 of
    "<timestamp>.<raw body>" with the endpoint secret."""
    secret = secret if secret is not None else os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise ValueError("STRIPE_WEBHOOK_SECRET is not set")
    parts = {}
    for item in (sig_header or "").split(","):
        k, _, v = item.strip().partition("=")
        parts.setdefault(k, []).append(v)
    try:
        ts = int(parts.get("t", ["0"])[0])
    except ValueError:
        raise ValueError("bad timestamp")
    expected = hmac.new(secret.encode(), b"%d." % ts + payload_bytes,
                        hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, s) for s in parts.get("v1", [])):
        raise ValueError("signature mismatch")
    if abs((now or time.time()) - ts) > tolerance:
        raise ValueError("timestamp outside tolerance")
    return json.loads(payload_bytes.decode())


def card_fee_cents(amount_cents, cfg):
    """What Stripe keeps, from business.json economics.card_processing."""
    cp = (cfg.get("economics") or {}).get("card_processing") or {}
    return int(round(amount_cents * float(cp.get("percent", 0.029)))) + int(cp.get("fixed_cents", 30))
