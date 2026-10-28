"""Server-side conversion events: Meta Conversions API and GA4 Measurement
Protocol.

Most money arrives with no customer browser open (the saved card is charged
when the crew marks the job done), so the browser Pixel/gtag never see the
sale. This sends the Purchase from the server instead. It uses the same ids
as the browser events (Meta event_id "purchase-<ref>", GA transaction_id
<ref>), so a sale both sides report is counted once.

  META_PIXEL_ID + META_CAPI_TOKEN        Meta Events Manager -> Settings -> Conversions API token
  GOOGLE_TAG_ID (G-...) + GA_API_SECRET  GA4 Admin -> Data streams -> Measurement Protocol API secrets

Off unless configured. Sends run on a background thread and never raise:
reporting a sale must never slow down or break taking the money.
"""
import hashlib, json, os, re, threading, time, urllib.request

META_API = os.environ.get("META_API_BASE", "https://graph.facebook.com/v21.0")
GA_API = os.environ.get("GA_API_BASE", "https://www.google-analytics.com")


def _env(k):
    return os.environ.get(k, "").strip()


def meta_on():
    return bool(re.match(r"^\d{6,20}$", _env("META_PIXEL_ID")) and _env("META_CAPI_TOKEN"))


def ga_on():
    return bool(re.match(r"^G-[A-Z0-9]{4,20}$", _env("GOOGLE_TAG_ID")) and _env("GA_API_SECRET"))


def capture(cookies, ua=None):
    """Ad identifiers worth keeping from the booking request's cookies."""
    out = {}
    ga = cookies.get("_ga") or ""
    m = re.match(r"^GA\d\.\d\.(\d+\.\d+)$", ga)
    if m:
        out["ga_cid"] = m.group(1)
    for k in ("_fbp", "_fbc"):
        if re.match(r"^fb\.\d\.\d+\.[A-Za-z0-9_\-.]+$", cookies.get(k) or ""):
            out[k[1:]] = cookies[k]
    if ua:
        out["ua"] = ua[:300]
    return out


def _sha(v):
    return hashlib.sha256(v.encode()).hexdigest() if v else None


def norm_phone(p):
    d = re.sub(r"\D", "", p or "")
    return "1" + d if len(d) == 10 else d


def meta_payload(ref, cents, email, phone, ids, now=None):
    user = {k: v for k, v in {
        "em": [_sha((email or "").strip().lower())] if email else None,
        "ph": [_sha(norm_phone(phone))] if norm_phone(phone) else None,
        "fbp": ids.get("fbp"), "fbc": ids.get("fbc"),
        "client_user_agent": ids.get("ua"),
    }.items() if v}
    return {"data": [{
        "event_name": "Purchase", "event_time": int(now or time.time()),
        "event_id": "purchase-%s" % ref, "action_source": "website",
        "event_source_url": "https://tampamaidscleaning.com/track",
        "user_data": user,
        "custom_data": {"currency": "USD", "value": round(cents / 100.0, 2), "order_id": ref},
    }]}


def ga_payload(ref, cents, ids):
    # Without the visitor's GA client id the sale still counts, it just can't
    # be tied to the ad click; a stable per-booking id keeps it consistent.
    return {"client_id": ids.get("ga_cid") or "srv.%s" % ref,
            "events": [{"name": "purchase", "params": {
                "currency": "USD", "value": round(cents / 100.0, 2),
                "transaction_id": ref}}]}


def _post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return r.status


def _send_purchase(ref, cents, email, phone, ids):
    if meta_on():
        try:
            _post("%s/%s/events?access_token=%s" % (META_API, _env("META_PIXEL_ID"),
                                                    _env("META_CAPI_TOKEN")),
                  meta_payload(ref, cents, email, phone, ids))
            print("  [capi] Purchase %s sent to Meta" % ref, flush=True)
        except Exception as e:                               # noqa: BLE001
            print("  [capi] Meta Purchase %s failed: %s" % (ref, e), flush=True)
    if ga_on():
        try:
            _post("%s/mp/collect?measurement_id=%s&api_secret=%s" % (
                GA_API, _env("GOOGLE_TAG_ID"), _env("GA_API_SECRET")),
                ga_payload(ref, cents, ids))
            print("  [ga-mp] purchase %s sent" % ref, flush=True)
        except Exception as e:                               # noqa: BLE001
            print("  [ga-mp] purchase %s failed: %s" % (ref, e), flush=True)


def purchase(ref, cents, email, phone, ids, wait=False):
    """Report a sale. Returns the thread (tests join it), or None when off."""
    if cents <= 0 or not (meta_on() or ga_on()):
        return None
    t = threading.Thread(target=_send_purchase, args=(ref, cents, email, phone, ids or {}),
                         daemon=True)
    t.start()
    if wait:
        t.join(15)
    return t
