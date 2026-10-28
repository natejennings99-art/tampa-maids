#!/usr/bin/env python3
"""Tampa Maids Cleaning — website, booking API, admin and crew backend.

Stdlib only. No pip install, no virtualenv, no build step.

    python3 server/app.py            # http://localhost:8000
    python3 server/app.py --port 9000 --host 0.0.0.0
"""
import os, sys, json, re, io, time, argparse, datetime, mimetypes, secrets, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db, pricing, checklists, backup, notify, payments, payouts, tags, conversions

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
CONFIG_PATH = os.path.join(ROOT, "business.json")

SESSION_DAYS = 14

# Set these in production (see README "Going live").
TRUST_PROXY = os.environ.get("TRUST_PROXY", "").lower() in ("1", "true", "yes")
FORCE_HTTPS = os.environ.get("FORCE_HTTPS", "").lower() in ("1", "true", "yes")
mimetypes.add_type("application/manifest+json", ".webmanifest")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("font/woff2", ".woff2")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


CFG = load_config()


# --------------------------------------------------------------------------
# tiny router
# --------------------------------------------------------------------------
ROUTES = []


def route(method, pattern):
    rx = re.compile("^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", pattern) + "$")
    def deco(fn):
        ROUTES.append((method, rx, fn))
        return fn
    return deco


# Guessable short URLs -> the real page. Keys are lowercased and have any
# trailing slash stripped before lookup.
ALIASES = {
    "/prices": "/pricing",
    "/price": "/pricing",
    "/rates": "/pricing",
    "/cost": "/pricing",
    "/quote": "/book",
    "/booking": "/book",
    "/schedule": "/book",
    "/tampa": "/cleaning/tampa",
    "/clearwater": "/cleaning/clearwater",
    "/sarasota": "/cleaning/sarasota",
    "/st-petersburg": "/cleaning/st-petersburg",
    "/stpetersburg": "/cleaning/st-petersburg",
    "/st-pete": "/cleaning/st-petersburg",
    "/stpete": "/cleaning/st-petersburg",
}

class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def require(data, *fields):
    missing = [f for f in fields if not str(data.get(f) or "").strip()]
    if missing:
        raise ApiError("Missing required field(s): %s" % ", ".join(missing))
    return [str(data[f]).strip() for f in fields]


EMAIL_RX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def valid_email(e):
    return bool(EMAIL_RX.match((e or "").strip()))


def parse_date(s):
    try:
        return datetime.date.fromisoformat(s)
    except (ValueError, TypeError):
        raise ApiError("Invalid date: %r (expected YYYY-MM-DD)" % s)


def log(con, booking_id, actor, event, detail=None):
    con.execute(
        "INSERT INTO activity (booking_id, actor, event, detail, created_at) VALUES (?,?,?,?,?)",
        (booking_id, actor, event, detail, db.now()))


def current_staff(ctx):
    tok = ctx["cookies"].get("gc_session")
    if not tok:
        return None
    con = ctx["con"]
    row = db.one(con.execute(
        "SELECT s.* , sess.expires_at FROM sessions sess "
        "JOIN staff s ON s.id = sess.staff_id "
        "WHERE sess.token = ? AND sess.expires_at > ? AND s.active = 1",
        (tok, db.now())))
    return row


def need_staff(ctx, roles=None):
    s = current_staff(ctx)
    if not s:
        raise ApiError("Please sign in.", 401)
    if roles and s["role"] not in roles:
        raise ApiError("Your account doesn't have access to that.", 403)
    return s


def public_staff(s):
    return {"id": s["id"], "name": s["name"], "email": s["email"],
            "role": s["role"], "phone": s.get("phone")}


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

@route("GET", "/api/config")
def api_config(ctx):
    """Everything the website and phone app need to render, in one call."""
    c = dict(CFG)
    c.pop("_comment", None)
    c.pop("_TODO_contact", None)
    c.pop("payouts", None)          # contractor pay terms are not public
    # "live" | "test" | "off". The booking page only offers to save a card
    # when this is live, or when a tester opened /book?testpay=1.
    c["card_payments"] = payments.mode()
    return c


@route("POST", "/api/quote")
def api_quote(ctx):
    q = pricing.quote(CFG, ctx["body"])
    if q.get("error"):
        raise ApiError(q["error"])
    return q


@route("GET", "/api/availability")
def api_availability(ctx):
    """Open slots for a single date, or a whole month's day-by-day capacity."""
    con = ctx["con"]
    bk = CFG["booking"]
    today = datetime.date.today()
    earliest = today + datetime.timedelta(days=bk["lead_time_days"])
    latest = today + datetime.timedelta(days=bk["booking_window_days"])
    service = ctx["query"].get("service", ["residential"])[0]
    slots = bk["commercial_slots"] if service == "commercial" else bk["time_slots"]

    blocked = {r["date"]: r["reason"] for r in db.rows(
        con.execute("SELECT date, reason FROM blackouts"))}

    def day_status(d):
        iso = d.isoformat()
        if d < earliest:
            return {"date": iso, "open": False, "reason": "Too soon"}
        if d > latest:
            return {"date": iso, "open": False, "reason": "Outside booking window"}
        if d.weekday() in bk["closed_weekdays"]:
            return {"date": iso, "open": False, "reason": "Closed"}
        if iso in blocked:
            return {"date": iso, "open": False, "reason": blocked[iso] or "Unavailable"}
        taken = {}
        for r in db.rows(con.execute(
                "SELECT slot, COUNT(*) n FROM bookings "
                "WHERE date = ? AND status NOT IN ('cancelled') GROUP BY slot", (iso,))):
            taken[r["slot"]] = r["n"]

        # A per-slot cap alone is not enough. The slots are two hours apart but a
        # 3 BR deep clean runs four to five hours for one cleaner, so a day that
        # is open in every slot still oversells the day. Cap the day as well.
        per_day = bk.get("max_jobs_per_day")
        if per_day is not None and sum(taken.values()) >= per_day:
            return {"date": iso, "open": False, "slots": [],
                    "reason": "Fully booked"}

        free = [s for s in slots if taken.get(s, 0) < bk["max_jobs_per_slot"]]
        return {"date": iso, "open": bool(free), "slots": free,
                "reason": None if free else "Fully booked"}

    if "date" in ctx["query"]:
        return day_status(parse_date(ctx["query"]["date"][0]))

    # Default to the month containing the first bookable date, not today's month:
    # on the last day of a month, today's month has no open days left.
    month = ctx["query"].get("month", [earliest.strftime("%Y-%m")])[0]
    try:
        y, m = [int(x) for x in month.split("-")]
        start = datetime.date(y, m, 1)
    except (ValueError, TypeError):
        raise ApiError("Invalid month: %r (expected YYYY-MM)" % month)
    days = []
    d = start
    while d.month == m:
        days.append(day_status(d))
        d += datetime.timedelta(days=1)
    return {"month": month, "days": days, "slots": slots}


@route("POST", "/api/bookings")
def api_create_booking(ctx):
    b = ctx["body"]
    con = ctx["con"]
    name, email, phone, address, city, date_s, slot = require(
        b, "name", "email", "phone", "address", "city", "date", "slot")
    if not valid_email(email):
        raise ApiError("That email address doesn't look right.")

    # A booking is where the client service agreement is formed. Refuse to create
    # one without recorded acceptance -- the record is the evidence that terms
    # applied to this job.
    if not b.get("accept_terms"):
        raise ApiError("Please accept the service agreement to confirm your booking.")
    terms_version = (CFG.get("service_agreement") or {}).get("version") or "unversioned"

    d = parse_date(date_s)
    avail = api_availability({**ctx, "query": {"date": [date_s],
                                               "service": [b.get("service", "residential")]}})
    if not avail.get("open") or slot not in (avail.get("slots") or []):
        # api_availability already knows WHY the day is closed. Saying "just
        # filled up" for a Sunday, a past date or a holiday is simply untrue,
        # and it reads like a broken site rather than a date to change.
        reason = avail.get("reason") or ""
        pretty = notify.nice_date(date_s)
        if reason == "Too soon":
            lead = CFG["booking"]["lead_time_days"]
            msg = ("We need at least %d day%s notice, so %s is too soon. "
                   "Please pick a later date — or call us and we'll see what "
                   "we can do." % (lead, "" if lead == 1 else "s", pretty))
        elif reason == "Closed":
            msg = ("We're closed on %ss. Please pick another day." %
                   pretty.split(",")[0])
        elif reason == "Outside booking window":
            msg = ("%s is further out than we schedule right now. Please pick "
                   "a date within the next %d days." %
                   (pretty, CFG["booking"]["booking_window_days"]))
        elif not avail.get("open") and reason not in ("", "Fully booked"):
            msg = "We're not available on %s (%s). Please pick another day." % (
                pretty, reason.lower())
        else:
            msg = ("%s at %s just filled up. Please pick another time." %
                   (pretty, slot))
        raise ApiError(msg)

    q = pricing.quote(CFG, b)
    if q.get("error"):
        raise ApiError(q["error"])
    if q.get("custom_quote"):
        raise ApiError("That job needs a custom quote. Please use the quote request form.")

    cust = db.one(con.execute(
        "SELECT * FROM customers WHERE lower(email) = lower(?)", (email,)))
    if cust:
        cid = cust["id"]
        con.execute("UPDATE customers SET name=?, phone=?, address=?, city=?, zip=? WHERE id=?",
                    (name, phone, address, city, b.get("zip"), cid))
    else:
        cur = con.execute(
            "INSERT INTO customers (name,email,phone,address,city,zip,notes,created_at)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (name, email, phone, address, city, b.get("zip"), b.get("notes"), db.now()))
        cid = cur.lastrowid
    # Only a ticked box counts as consent, and an unticked one on a later
    # booking doesn't withdraw it -- STOP does. Consent is never required.
    sms_consent = bool(b.get("sms_consent"))
    if sms_consent:
        con.execute("UPDATE customers SET sms_consent_at=?, sms_consent_ip=? WHERE id=?",
                    (db.now(), ctx.get("ip"), cid))

    # ---------- referrals ----------
    # Cleaning is a referral trade: people ask a neighbour, not a search engine.
    # The credit was configured from the start and never built, so the column
    # sat at zero. Both sides get it -- a one-sided offer asks someone to do
    # unpaid marketing, a two-sided one gives them something to actually say.
    credit = int((CFG.get("pricing") or {}).get("referral_credit") or 0)
    applied = 0
    referrer = None
    code = (b.get("referral_code") or "").strip().upper()
    if code and credit:
        referrer = db.one(con.execute(
            "SELECT * FROM customers WHERE upper(referral_code) = ?", (code,)))
        if referrer and referrer["id"] != cid:
            applied += credit
            q["lines"].append({
                "label": "Referral credit",
                "detail": "Code %s, applied to this visit" % code,
                "amount": -credit})

    # A credit the customer has already earned by referring someone else.
    banked = int((cust["referral_credit_cents"] if cust else 0) or 0)
    if banked > 0:
        use = min(banked, max(0, q["total"] - applied))
        if use:
            applied += use
            q["lines"].append({
                "label": "Your referral credit",
                "detail": "Earned by referring a friend",
                "amount": -use})
            con.execute("UPDATE customers SET referral_credit_cents = referral_credit_cents - ? "
                        "WHERE id = ?", (use, cid))

    if applied:
        # Never let credits push a job below zero; the discount caps at the total.
        applied = min(applied, q["total"])
        q["discount"] = q.get("discount", 0) + applied
        q["total"] = max(0, q["total"] - applied)

    if referrer and referrer["id"] != cid:
        # Pay the referrer only once this booking exists, and record who sent whom.
        con.execute("UPDATE customers SET referral_credit_cents = referral_credit_cents + ? "
                    "WHERE id = ?", (credit, referrer["id"]))
        con.execute("UPDATE customers SET referred_by = ? WHERE id = ? AND referred_by IS NULL",
                    (code, cid))

    ref = db.new_ref(CFG["booking"].get("ref_prefix", "TM"))
    while db.one(con.execute("SELECT id FROM bookings WHERE ref=?", (ref,))):
        ref = db.new_ref(CFG["booking"].get("ref_prefix", "TM"))

    cur = con.execute(
        "INSERT INTO bookings (ref,customer_id,service_id,tier_id,frequency,sqft,addons,"
        "date,slot,status,is_first_clean,quote,total_cents,access_notes,notes,created_at,"
        "terms_version,terms_accepted_at,terms_accepted_ip)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (ref, cid, b.get("service", "residential"), b.get("tier_id"),
         b.get("frequency", "once"), b.get("sqft") or None,
         json.dumps(b.get("addons") or []), date_s, slot, "requested",
         1 if b.get("is_first_clean", True) else 0,
         json.dumps(q), q["total"], b.get("access_notes"), b.get("notes"), db.now(),
         terms_version, db.now(), ctx.get("ip")))
    bid = cur.lastrowid
    ad_ids = conversions.capture(ctx["cookies"], ctx["headers"].get("User-Agent"))
    if ad_ids:
        con.execute("UPDATE bookings SET ad_ids=? WHERE id=?", (json.dumps(ad_ids), bid))

    for i, (area, label) in enumerate(checklists.for_service(b.get("service", "residential"))):
        con.execute("INSERT INTO tasks (booking_id,area,label,sort) VALUES (?,?,?,?)",
                    (bid, area, label, i))

    log(con, bid, name, "created", "Booked online for %s at %s" % (date_s, slot))
    log(con, bid, name, "terms_accepted",
        "Service agreement %s accepted from %s" % (terms_version, ctx.get("ip") or "unknown IP"))
    if sms_consent:
        log(con, bid, name, "sms_consent", "Agreed to booking texts at %s from %s" % (
            phone, ctx.get("ip") or "unknown IP"))
    con.commit()

    # Email is best-effort and must never cost a booking: notify.send swallows
    # provider failures, and this whole block is belt-and-braces on top.
    emailed = False
    try:
        bk = {"ref": ref, "date": date_s, "slot": slot, "total_cents": q["total"],
              "access_notes": b.get("access_notes"), "notes": b.get("notes")}
        cust = {"name": name, "email": email, "phone": phone,
                "address": address, "city": city}
        subj, text, html = notify.booking_confirmation(CFG, bk, cust, q)
        emailed = notify.send(email, subj, text, html)
        if notify.OWNER_NOTIFY:
            osubj, otext, ohtml = notify.owner_alert(CFG, bk, cust, q)
            notify.send(notify.OWNER_NOTIFY, osubj, otext, ohtml)
    except Exception as e:                                   # noqa: BLE001
        print("  [notify] skipped for %s: %s" % (ref, e))

    if not emailed:
        # Nothing reached the customer or the owner. Say so where it will
        # actually be seen -- the Render log -- rather than failing quietly.
        # flush: stdout is block-buffered when Render captures it, and an alert
        # that shows up an hour late is not an alert.
        print("  *** BOOKING %s NEEDS A HUMAN: %s, %s at %s, %s. No email went "
              "out (mail provider: %s). Call them." %
              (ref, name, date_s, slot, phone or email, notify.provider()),
              flush=True)

    # Card on file. Nothing is charged now (the site promises payment on the
    # day of service); Checkout in setup mode only saves the card. A failure
    # here must never cost the booking, so it degrades to "we'll arrange it".
    card_url = None
    if payments.mode() == "live" or (payments.mode() == "test" and b.get("test_payments")):
        try:
            card_url = start_card_setup(con, bid)
        except Exception as e:                               # noqa: BLE001
            print("  [stripe] card setup skipped for %s: %s" % (ref, e), flush=True)

    try:
        notify.send_sms(notify.owner_phone(CFG), notify.booking_text(
            CFG, {"ref": ref, "date": date_s, "slot": slot, "total_cents": q["total"]},
            {"name": name, "phone": phone, "city": city}), owner=True)
    except Exception as e:                                   # noqa: BLE001
        print("  [sms] skipped for %s: %s" % (ref, e))
    if sms_consent and customer_sms_on():
        notify.send_sms(phone, notify.customer_booking_text(CFG, {
            "ref": ref, "date": date_s, "slot": slot, "total_cents": q["total"]}))

    # The confirmation panel already has "You're booked." as its heading, so
    # repeating it here reads as a stutter at the moment the customer is paying
    # most attention.
    msg = ("A confirmation is on its way to %s." % email) if emailed else \
          ("Save your reference %s — we'll be in touch to confirm." % ref)
    return {"ok": True, "ref": ref, "id": bid, "quote": q,
            "date": date_s, "slot": slot, "emailed": emailed,
            "card_url": card_url, "card_mode": payments.mode() if card_url else None,
            "message": msg}


def booking_public(con, row):
    cust = db.one(con.execute("SELECT * FROM customers WHERE id=?", (row["customer_id"],)))
    svc = next((s for s in CFG["services"] if s["id"] == row["service_id"]), None)
    tasks = db.rows(con.execute(
        "SELECT id,area,label,done FROM tasks WHERE booking_id=? ORDER BY sort", (row["id"],)))
    assigned = None
    if row.get("assigned_to"):
        a = db.one(con.execute("SELECT name FROM staff WHERE id=?", (row["assigned_to"],)))
        assigned = a["name"] if a else None
    return {
        "id": row["id"], "ref": row["ref"], "status": row["status"],
        "service_id": row["service_id"],
        "service": svc["name"] if svc else row["service_id"],
        "frequency": row["frequency"], "date": row["date"], "slot": row["slot"],
        "total": row["total_cents"], "quote": json.loads(row["quote"] or "{}"),
        "addons": json.loads(row["addons"] or "[]"),
        "notes": row["notes"], "access_notes": row["access_notes"],
        "is_first_clean": bool(row["is_first_clean"]),
        "created_at": row["created_at"], "completed_at": row["completed_at"],
        "terms_version": row.get("terms_version"),
        "terms_accepted_at": row.get("terms_accepted_at"),
        "assigned_to": row.get("assigned_to"), "assigned_name": assigned,
        "customer": {"name": cust["name"], "email": cust["email"], "phone": cust["phone"],
                     "address": cust["address"], "city": cust["city"], "zip": cust["zip"]},
        "payment_status": row.get("payment_status"),
        "paid_cents": row.get("paid_cents"), "paid_at": row.get("paid_at"),
        "paid_method": row.get("paid_method"),
        "pay_link_url": row.get("pay_link_url") if row.get("payment_status") == "link_sent" else None,
        # Self-serve skip/reschedule is free up to 48 hours out (cancellation_policy).
        "can_change": row["status"] in ("requested", "confirmed") and _hours_until(row["date"]) >= 48,
        "can_skip": row["status"] in ("requested", "confirmed") and _hours_until(row["date"]) >= 48
                    and row["frequency"] in RECUR_DAYS and row["service_id"] == "residential",
        "tasks": tasks,
        "tasks_done": sum(1 for t in tasks if t["done"]),
        "tasks_total": len(tasks),
    }


@route("GET", "/api/bookings/track")
def api_track(ctx):
    ref = (ctx["query"].get("ref", [""])[0]).strip().upper()
    email = (ctx["query"].get("email", [""])[0]).strip()
    if not ref or not email:
        raise ApiError("Enter both your booking reference and your email address.")
    con = ctx["con"]
    row = db.one(con.execute(
        "SELECT b.* FROM bookings b JOIN customers c ON c.id=b.customer_id "
        "WHERE upper(b.ref)=? AND lower(c.email)=lower(?)", (ref, email)))
    if not row:
        raise ApiError("We couldn't find a booking with that reference and email.", 404)
    return booking_public(con, row)


@route("GET", "/api/bookings/mine")
def api_mine(ctx):
    """All bookings for one email address — the phone app's 'My cleans' tab."""
    email = (ctx["query"].get("email", [""])[0]).strip()
    if not valid_email(email):
        raise ApiError("Enter the email address you booked with.")
    con = ctx["con"]
    rows = db.rows(con.execute(
        "SELECT b.* FROM bookings b JOIN customers c ON c.id=b.customer_id "
        "WHERE lower(c.email)=lower(?) ORDER BY b.date DESC, b.slot", (email,)))
    return {"bookings": [booking_public(con, r) for r in rows]}


def _hours_until(date_s):
    when = datetime.datetime.fromisoformat(date_s + "T00:00:00")
    return (when - datetime.datetime.now()).total_seconds() / 3600.0


def _customer_booking(ctx):
    """The booking named by ref + email, for the customer's own changes."""
    ref, email = require(ctx["body"], "ref", "email")
    row = db.one(ctx["con"].execute(
        "SELECT b.* FROM bookings b JOIN customers c ON c.id=b.customer_id "
        "WHERE upper(b.ref)=? AND lower(c.email)=lower(?)", (ref.upper(), email)))
    if not row:
        raise ApiError("We couldn't find that booking.", 404)
    if row["status"] in ("cancelled", "completed"):
        raise ApiError("That booking is already %s." % row["status"])
    return row, email


def _require_free_change(row):
    if row["status"] not in ("requested", "confirmed"):
        raise ApiError("This visit can't be changed online now. Call us at %s." % CFG.get("phone", ""))
    if _hours_until(row["date"]) < 48:
        raise ApiError("Your visit is less than 48 hours away, so it can't be changed online. "
                       "Call or text us at %s." % CFG.get("phone", ""))


@route("POST", "/api/bookings/skip")
def api_skip(ctx):
    """Skip one recurring visit and keep the plan: this visit is cancelled
    and the next one is booked one interval later."""
    con = ctx["con"]
    row, email = _customer_booking(ctx)
    if row["frequency"] not in RECUR_DAYS or row["service_id"] != "residential":
        raise ApiError("Only recurring plans can skip a visit. You can reschedule instead.")
    _require_free_change(row)
    con.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (row["id"],))
    log(con, row["id"], email, "skipped", "Customer skipped this visit; plan continues")
    con.commit()
    nid = schedule_next_visit(con, row["id"], skipped=True)
    nxt = db.one(con.execute("SELECT ref, date, slot, total_cents FROM bookings WHERE id=?",
                             (nid,))) if nid else None
    if not nxt:
        notify.ping_owner(CFG, "SKIPPED %s: %s skipped %s %s; no slot found for the next visit, "
                          "book it by hand. %s/owner" % (row["ref"], email,
                                                        notify.nice_date(row["date"]), row["slot"],
                                                        _site_url()),
                          "Skipped: %s" % row["ref"])
    return {"ok": True, "next": nxt,
            "message": ("Skipped. Your plan continues: next cleaning %s at %s (reference %s)." % (
                notify.nice_date(nxt["date"]), nxt["slot"], nxt["ref"])) if nxt else
                       "Skipped. Your plan continues; we'll be in touch to confirm your next date."}


@route("POST", "/api/bookings/reschedule")
def api_reschedule(ctx):
    con = ctx["con"]
    row, email = _customer_booking(ctx)
    _require_free_change(row)
    date_s, slot = require(ctx["body"], "date", "slot")
    parse_date(date_s)
    if (date_s, slot) == (row["date"], row["slot"]):
        raise ApiError("That's already your booked time.")
    avail = api_availability({**ctx, "query": {"date": [date_s], "service": [row["service_id"]]}})
    if not avail.get("open") or slot not in (avail.get("slots") or []):
        raise ApiError("Sorry, %s at %s isn't available. Pick another time." % (date_s, slot), 409)
    old = "%s %s" % (row["date"], row["slot"])
    con.execute("UPDATE bookings SET date=?, slot=?, reminder_sent_at=NULL WHERE id=?",
                (date_s, slot, row["id"]))
    log(con, row["id"], email, "rescheduled", "%s -> %s %s (by customer)" % (old, date_s, slot))
    con.commit()
    notify.ping_owner(CFG, "MOVED %s: %s %s -> %s %s. %s/owner" % (
        row["ref"], notify.nice_date(row["date"]), row["slot"], notify.nice_date(date_s), slot,
        _site_url()), "Rescheduled: %s" % row["ref"])
    return {"ok": True, "date": date_s, "slot": slot,
            "message": "Moved to %s at %s. Nothing else changes." % (notify.nice_date(date_s), slot)}


@route("POST", "/api/bookings/cancel")
def api_cancel(ctx):
    con = ctx["con"]
    row, email = _customer_booking(ctx)
    fee = _hours_until(row["date"]) < 48
    con.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (row["id"],))
    log(con, row["id"], email, "cancelled",
        "Inside 48 hours — fee applies" if fee else "Free cancellation")
    con.commit()
    notify.ping_owner(CFG, "CANCELLED %s: %s %s%s. %s/owner" % (
        row["ref"], notify.nice_date(row["date"]), row["slot"],
        " (inside 48h, fee applies)" if fee else "", CFG.get("url", "")),
        "Cancelled: %s" % row["ref"])
    return {"ok": True, "fee_applies": fee,
            "message": ("Cancelled. Because this is inside 48 hours of your visit, our "
                        "cancellation fee applies — we'll be in touch.") if fee else
                       "Cancelled, free of charge. We hope to see you again soon."}


@route("POST", "/api/leads")
def api_lead(ctx):
    b = ctx["body"]
    name, email = require(b, "name", "email")
    if not valid_email(email):
        raise ApiError("That email address doesn't look right.")
    # Hidden "website" field: people never see it, form-filling bots do. Answer as
    # if it worked so they learn nothing, but store nothing and text no one.
    if (b.get("website") or "").strip():
        return {"ok": True, "message": "Thanks %s — we'll be back to you within one "
                "business day." % name.split()[0]}
    con = ctx["con"]
    con.execute(
        "INSERT INTO leads (name,email,phone,kind,message,payload,created_at) VALUES (?,?,?,?,?,?,?)",
        (name, email, b.get("phone"), b.get("kind", "contact"), b.get("message"),
         json.dumps(b), db.now()))
    con.commit()

    # The reply above promises one business day. Nothing was telling anyone an
    # enquiry had arrived, so that promise was being kept by luck. Fail-safe:
    # a mail outage must not break the form, but it must be visible.
    sent = False
    try:
        if notify.OWNER_NOTIFY:
            subj, text, html = notify.lead_alert(CFG, {
                "name": name, "email": email, "phone": b.get("phone"),
                "kind": b.get("kind", "contact"), "message": b.get("message")})
            sent = notify.send(notify.OWNER_NOTIFY, subj, text, html)
    except Exception as e:                                   # noqa: BLE001
        print("  [notify] lead alert skipped for %s: %s" % (email, e))
    # Speed to lead decides who gets the job: text Nate as well as emailing him.
    try:
        notify.ping_owner(CFG, "New %s lead: %s, %s, %s. Reply within 1 business day. %s/admin"
                          % (b.get("kind", "contact").replace("_", " "), name,
                             b.get("phone") or "no phone", email, CFG.get("url", "")))
    except Exception as e:                                   # noqa: BLE001
        print("  [notify] lead text skipped for %s: %s" % (email, e))
    if not sent:
        print("  *** ENQUIRY NEEDS A HUMAN: %s, %s, %s. Promised a reply within one "
              "business day. No email went out (mail provider: %s)."
              % (name, email, b.get("phone") or "no phone", notify.provider()),
              flush=True)

    return {"ok": True, "message": "Thanks %s — we'll be back to you within one business day."
            % name.split()[0]}


# --------------------------------------------------------------------------
# auth
# --------------------------------------------------------------------------

# Failed-login tracking, per client IP. In-memory is fine: a restart clearing it
# is not a meaningful weakening, and it costs nothing. Without this the staff
# login is an unthrottled password oracle on a public domain.
_FAILED = {}
MAX_FAILS = 8
LOCKOUT_SECONDS = 900


def _throttle_check(ip):
    hits = [t for t in _FAILED.get(ip, [])
            if time.time() - t < LOCKOUT_SECONDS]
    _FAILED[ip] = hits
    if len(hits) >= MAX_FAILS:
        wait = int((LOCKOUT_SECONDS - (time.time() - hits[0])) / 60) + 1
        raise ApiError("Too many failed sign-in attempts. Try again in about "
                       "%d minutes." % wait, 429)


def _throttle_fail(ip):
    _FAILED.setdefault(ip, []).append(time.time())
    if len(_FAILED) > 5000:                      # bound the dict
        cutoff = time.time() - LOCKOUT_SECONDS
        for k in [k for k, v in _FAILED.items() if not any(t > cutoff for t in v)]:
            _FAILED.pop(k, None)


@route("POST", "/api/auth/login")
def api_login(ctx):
    ip = ctx.get("ip") or "?"
    _throttle_check(ip)
    email, password = require(ctx["body"], "email", "password")
    con = ctx["con"]
    s = db.one(con.execute("SELECT * FROM staff WHERE lower(email)=lower(?) AND active=1", (email,)))
    if not s or not db.verify_password(password, s["pw_hash"], s["pw_salt"]):
        _throttle_fail(ip)
        raise ApiError("Email or password is incorrect.", 401)
    _FAILED.pop(ip, None)
    tok = secrets.token_urlsafe(32)
    exp = (datetime.datetime.now() + datetime.timedelta(days=SESSION_DAYS)
           ).replace(microsecond=0).isoformat(sep=" ")
    con.execute("INSERT INTO sessions (token,staff_id,created_at,expires_at) VALUES (?,?,?,?)",
                (tok, s["id"], db.now(), exp))
    con.execute("DELETE FROM sessions WHERE expires_at < ?", (db.now(),))
    con.commit()
    ctx["set_cookie"] = ("gc_session", tok, SESSION_DAYS * 86400)
    return {"ok": True, "staff": public_staff(s)}


@route("POST", "/api/auth/logout")
def api_logout(ctx):
    tok = ctx["cookies"].get("gc_session")
    if tok:
        ctx["con"].execute("DELETE FROM sessions WHERE token=?", (tok,))
        ctx["con"].commit()
    ctx["set_cookie"] = ("gc_session", "", 0)
    return {"ok": True}


@route("GET", "/api/auth/me")
def api_me(ctx):
    s = current_staff(ctx)
    return {"staff": public_staff(s) if s else None}


# --------------------------------------------------------------------------
# owner / admin
# --------------------------------------------------------------------------

def _job_times(con):
    """Measured minutes per job, grouped by home size.

    Only counts jobs with both timestamps and a sane duration: a crew that
    forgets to tap "finished" until the next morning would otherwise drag the
    average into nonsense, and a wrong number here is worse than none because
    it would be used to decide how many jobs a cleaner can carry.
    """
    rows = db.rows(con.execute(
        "SELECT tier_id, service_id, started_at, completed_at FROM bookings "
        "WHERE started_at IS NOT NULL AND completed_at IS NOT NULL "
        "AND status = 'completed'"))
    buckets = {}
    for r in rows:
        try:
            a = datetime.datetime.fromisoformat(r["started_at"])
            b = datetime.datetime.fromisoformat(r["completed_at"])
        except (TypeError, ValueError):
            continue
        mins = (b - a).total_seconds() / 60.0
        if not (20 <= mins <= 600):          # implausible: ignore rather than skew
            continue
        key = r["tier_id"] or r["service_id"] or "other"
        buckets.setdefault(key, []).append(mins)
    out = []
    for key, vals in sorted(buckets.items()):
        vals.sort()
        out.append({"key": key, "jobs": len(vals),
                    "avg_minutes": int(round(sum(vals) / len(vals))),
                    "median_minutes": int(round(vals[len(vals) // 2]))})
    measured = sum(b["jobs"] for b in out)
    return {"buckets": out, "measured": measured,
            # The figure the capacity model currently assumes, so the dashboard
            # can show the assumption next to the reality.
            "assumed_jobs_per_day": (CFG.get("economics") or {}).get("jobs_per_cleaner_per_day")}


@route("GET", "/api/admin/overview")
def api_overview(ctx):
    need_staff(ctx, ["owner", "lead"])
    con = ctx["con"]
    today = datetime.date.today().isoformat()
    month = datetime.date.today().strftime("%Y-%m")

    def scalar(sql, args=()):
        r = con.execute(sql, args).fetchone()
        return r[0] or 0

    booked_month = scalar(
        "SELECT SUM(total_cents) FROM bookings WHERE date LIKE ? AND status != 'cancelled'",
        (month + "%",))
    completed_month = scalar(
        "SELECT SUM(total_cents) FROM bookings WHERE date LIKE ? AND status = 'completed'",
        (month + "%",))
    return {
        "today": today,
        "jobs_today": scalar("SELECT COUNT(*) FROM bookings WHERE date=? AND status!='cancelled'", (today,)),
        "jobs_upcoming": scalar("SELECT COUNT(*) FROM bookings WHERE date>? AND status!='cancelled'", (today,)),
        "requested": scalar("SELECT COUNT(*) FROM bookings WHERE status='requested'"),
        "unassigned": scalar("SELECT COUNT(*) FROM bookings WHERE assigned_to IS NULL AND status IN ('requested','confirmed')"),
        "new_leads": scalar("SELECT COUNT(*) FROM leads WHERE handled=0"),
        "customers": scalar("SELECT COUNT(*) FROM customers"),
        "recurring_clients": scalar(
            "SELECT COUNT(DISTINCT customer_id) FROM bookings WHERE frequency != 'once' AND status != 'cancelled'"),
        "booked_month_cents": booked_month,
        "completed_month_cents": completed_month,
        "revenue_by_service": db.rows(con.execute(
            "SELECT service_id, COUNT(*) n, SUM(total_cents) cents FROM bookings "
            "WHERE status != 'cancelled' GROUP BY service_id ORDER BY cents DESC")),
        # Without a mail provider the owner alert never sends, so a booking can
        # sit here unseen. A business with no customers yet cannot afford to
        # miss its first one, so the dashboard is told rather than left to
        # look healthy while nothing is reaching anybody.
        # Actual job durations. started_at and completed_at have always been
        # recorded and never used, while the whole capacity model rests on an
        # assumed 2.5 jobs per cleaner per day that nobody has checked. Ten
        # finished jobs settles it, so surface it as soon as there is anything.
        "job_times": _job_times(con),
        "mail_configured": notify.configured(),
        "mail_provider": notify.provider(),
        "owner_notify": bool(notify.OWNER_NOTIFY),
        "unseen_bookings": scalar(
            "SELECT COUNT(*) FROM bookings WHERE status='requested'"),
        "next_7_days": db.rows(con.execute(
            "SELECT date, COUNT(*) n, SUM(total_cents) cents FROM bookings "
            "WHERE date >= ? AND date <= ? AND status != 'cancelled' GROUP BY date ORDER BY date",
            (today, (datetime.date.today() + datetime.timedelta(days=7)).isoformat()))),
    }


@route("GET", "/api/admin/bookings")
def api_admin_bookings(ctx):
    need_staff(ctx, ["owner", "lead"])
    con = ctx["con"]
    q = ctx["query"]
    sql = ("SELECT b.* FROM bookings b JOIN customers c ON c.id=b.customer_id WHERE 1=1")
    args = []
    if q.get("status") and q["status"][0] != "all":
        sql += " AND b.status = ?"; args.append(q["status"][0])
    if q.get("from"):
        sql += " AND b.date >= ?"; args.append(q["from"][0])
    if q.get("to"):
        sql += " AND b.date <= ?"; args.append(q["to"][0])
    if q.get("search"):
        s = "%" + q["search"][0] + "%"
        sql += " AND (c.name LIKE ? OR c.email LIKE ? OR b.ref LIKE ? OR c.address LIKE ?)"
        args += [s, s, s, s]
    sql += " ORDER BY b.date DESC, b.slot LIMIT 300"
    return {"bookings": [booking_public(con, r) for r in db.rows(con.execute(sql, args))]}


@route("POST", "/api/admin/bookings/{bid}")
def api_admin_update_booking(ctx, bid):
    s = need_staff(ctx, ["owner", "lead"])
    con = ctx["con"]
    b = ctx["body"]
    row = db.one(con.execute("SELECT * FROM bookings WHERE id=?", (bid,)))
    if not row:
        raise ApiError("Booking not found.", 404)

    if "status" in b:
        valid = ("requested", "confirmed", "in_progress", "completed", "cancelled")
        if b["status"] not in valid:
            raise ApiError("Invalid status.")
        con.execute("UPDATE bookings SET status=? WHERE id=?", (b["status"], bid))
        if b["status"] == "completed":
            con.execute("UPDATE bookings SET completed_at=? WHERE id=?", (db.now(), bid))
        log(con, bid, s["name"], "status", b["status"])
        if b["status"] == "completed" and row["status"] != "completed":
            con.commit()
            on_job_completed(con, bid)
    if "assigned_to" in b:
        val = b["assigned_to"] or None
        con.execute("UPDATE bookings SET assigned_to=? WHERE id=?", (val, bid))
        log(con, bid, s["name"], "assigned", str(val))
    if "date" in b and "slot" in b:
        con.execute("UPDATE bookings SET date=?, slot=? WHERE id=?", (b["date"], b["slot"], bid))
        log(con, bid, s["name"], "rescheduled", "%s %s" % (b["date"], b["slot"]))
    if "notes" in b:
        con.execute("UPDATE bookings SET notes=? WHERE id=?", (b["notes"], bid))
    con.commit()
    return booking_public(con, db.one(con.execute("SELECT * FROM bookings WHERE id=?", (bid,))))


@route("GET", "/api/admin/leads")
def api_admin_leads(ctx):
    need_staff(ctx, ["owner", "lead"])
    return {"leads": db.rows(ctx["con"].execute(
        "SELECT * FROM leads ORDER BY handled, created_at DESC LIMIT 200"))}


@route("POST", "/api/admin/leads/{lid}")
def api_admin_lead_update(ctx, lid):
    need_staff(ctx, ["owner", "lead"])
    ctx["con"].execute("UPDATE leads SET handled=? WHERE id=?",
                       (1 if ctx["body"].get("handled") else 0, lid))
    ctx["con"].commit()
    return {"ok": True}


@route("GET", "/api/admin/staff")
def api_admin_staff(ctx):
    need_staff(ctx, ["owner", "lead"])
    return {"staff": [public_staff(r) for r in db.rows(ctx["con"].execute(
        "SELECT * FROM staff WHERE active=1 ORDER BY role, name"))]}


@route("POST", "/api/admin/staff")
def api_admin_staff_create(ctx):
    need_staff(ctx, ["owner"])
    name, email, password, role = require(ctx["body"], "name", "email", "password", "role")
    if role not in ("owner", "lead", "cleaner"):
        raise ApiError("Invalid role.")
    if len(password) < 8:
        raise ApiError("Password must be at least 8 characters.")
    con = ctx["con"]
    if db.one(con.execute("SELECT id FROM staff WHERE lower(email)=lower(?)", (email,))):
        raise ApiError("A team member with that email already exists.")
    h, salt = db.hash_password(password)
    con.execute("INSERT INTO staff (name,email,phone,role,pw_hash,pw_salt,created_at)"
                " VALUES (?,?,?,?,?,?,?)",
                (name, email, ctx["body"].get("phone"), role, h, salt, db.now()))
    con.commit()
    return {"ok": True}


@route("GET", "/api/admin/blackouts")
def api_blackouts(ctx):
    need_staff(ctx, ["owner", "lead"])
    return {"blackouts": db.rows(ctx["con"].execute(
        "SELECT * FROM blackouts ORDER BY date"))}


@route("POST", "/api/admin/blackouts")
def api_blackout_add(ctx):
    need_staff(ctx, ["owner", "lead"])
    d, = require(ctx["body"], "date")
    parse_date(d)
    con = ctx["con"]
    con.execute("INSERT OR REPLACE INTO blackouts (date,reason) VALUES (?,?)",
                (d, ctx["body"].get("reason")))
    con.commit()
    return {"ok": True}


@route("POST", "/api/admin/blackouts/delete")
def api_blackout_del(ctx):
    need_staff(ctx, ["owner", "lead"])
    d, = require(ctx["body"], "date")
    ctx["con"].execute("DELETE FROM blackouts WHERE date=?", (d,))
    ctx["con"].commit()
    return {"ok": True}


# --------------------------------------------------------------------------
# crew
# --------------------------------------------------------------------------

@route("GET", "/api/crew/jobs")
def api_crew_jobs(ctx):
    s = need_staff(ctx)
    con = ctx["con"]
    today = datetime.date.today().isoformat()
    if s["role"] == "owner":
        rows = db.rows(con.execute(
            "SELECT * FROM bookings WHERE date >= ? AND status != 'cancelled' "
            "ORDER BY date, slot LIMIT 100", (today,)))
    else:
        rows = db.rows(con.execute(
            "SELECT * FROM bookings WHERE assigned_to = ? AND date >= ? AND status != 'cancelled' "
            "ORDER BY date, slot LIMIT 100", (s["id"], today)))
    jobs = [booking_public(con, r) for r in rows]
    return {"today": today, "jobs": jobs,
            "jobs_today": [j for j in jobs if j["date"] == today]}


@route("POST", "/api/crew/jobs/{bid}/status")
def api_crew_status(ctx, bid):
    s = need_staff(ctx)
    con = ctx["con"]
    row = db.one(con.execute("SELECT * FROM bookings WHERE id=?", (bid,)))
    if not row:
        raise ApiError("Job not found.", 404)
    if s["role"] not in ("owner", "lead") and row["assigned_to"] != s["id"]:
        raise ApiError("That job isn't assigned to you.", 403)
    status = ctx["body"].get("status")
    if status not in ("in_progress", "completed", "confirmed"):
        raise ApiError("Invalid status.")
    if status == "completed":
        left = con.execute("SELECT COUNT(*) FROM tasks WHERE booking_id=? AND done=0",
                           (bid,)).fetchone()[0]
        if left and not ctx["body"].get("force"):
            raise ApiError("%d checklist item(s) still open. Finish them, or confirm to "
                           "complete anyway." % left)
        con.execute("UPDATE bookings SET completed_at=? WHERE id=?", (db.now(), bid))
    if status == "in_progress":
        con.execute("UPDATE bookings SET started_at=? WHERE id=?", (db.now(), bid))
    con.execute("UPDATE bookings SET status=? WHERE id=?", (status, bid))
    log(con, bid, s["name"], "status", status)
    con.commit()
    if status == "completed" and row["status"] != "completed":
        on_job_completed(con, bid)

    # Marking a job done is the only moment we reliably know a customer has a
    # finished clean to judge, so it is where the review gets asked for. Reviews
    # are the gate on the Google local pack and nobody will remember to ask by
    # hand. Fail-safe, like every other send: a mail outage must never stop a
    # crew closing out a job. Sent once -- review_requested_at is the guard.
    if status == "completed" and not row["review_requested_at"]:
        try:
            cust = db.one(con.execute("SELECT * FROM customers WHERE id=?",
                                      (row["customer_id"],)))
            if cust and cust["email"]:
                subj, text, html = notify.review_request(
                    CFG, {"ref": row["ref"]}, dict(cust))
                if notify.send(cust["email"], subj, text, html):
                    con.execute("UPDATE bookings SET review_requested_at=? WHERE id=?",
                                (db.now(), bid))
                    log(con, bid, "system", "review", "requested")
                    con.commit()
                # Same moment, second job: hand them a referral code. They have
                # just had a clean, which is the only time the ask means anything.
                if not cust["referral_code"]:
                    rcode = db.new_referral_code(con)
                    con.execute("UPDATE customers SET referral_code=? WHERE id=?",
                                (rcode, cust["id"]))
                    con.commit()
                    rsubj, rtext, rhtml = notify.referral_invite(
                        CFG, dict(cust), rcode)
                    notify.send(cust["email"], rsubj, rtext, rhtml)
        except Exception as e:                               # noqa: BLE001
            print("  [notify] review request skipped for %s: %s" % (row["ref"], e))

    return booking_public(con, db.one(con.execute("SELECT * FROM bookings WHERE id=?", (bid,))))


@route("POST", "/api/crew/tasks/{tid}")
def api_crew_task(ctx, tid):
    s = need_staff(ctx)
    con = ctx["con"]
    t = db.one(con.execute("SELECT * FROM tasks WHERE id=?", (tid,)))
    if not t:
        raise ApiError("Task not found.", 404)
    row = db.one(con.execute("SELECT * FROM bookings WHERE id=?", (t["booking_id"],)))
    if s["role"] not in ("owner", "lead") and row["assigned_to"] != s["id"]:
        raise ApiError("That job isn't assigned to you.", 403)
    con.execute("UPDATE tasks SET done=? WHERE id=?",
                (1 if ctx["body"].get("done") else 0, tid))
    con.commit()
    done = con.execute("SELECT COUNT(*) FROM tasks WHERE booking_id=? AND done=1",
                       (t["booking_id"],)).fetchone()[0]
    total = con.execute("SELECT COUNT(*) FROM tasks WHERE booking_id=?",
                        (t["booking_id"],)).fetchone()[0]
    return {"ok": True, "tasks_done": done, "tasks_total": total}


# --------------------------------------------------------------------------
# payments (Stripe, see payments.py)
# --------------------------------------------------------------------------

def _site_url():
    return (os.environ.get("SITE_URL") or CFG.get("url") or "").rstrip("/")


def _booking_and_customer(con, bid):
    row = db.one(con.execute("SELECT * FROM bookings WHERE id=?", (bid,)))
    if not row:
        raise ApiError("Booking not found.", 404)
    cust = db.one(con.execute("SELECT * FROM customers WHERE id=?", (row["customer_id"],)))
    return row, cust


def _stripe_customer(con, cust):
    cid = payments.ensure_customer(cust.get("stripe_customer"), cust["name"],
                                   cust["email"], cust.get("phone"))
    if cid != cust.get("stripe_customer"):
        con.execute("UPDATE customers SET stripe_customer=? WHERE id=?", (cid, cust["id"]))
        con.commit()
    return cid


def start_card_setup(con, bid):
    row, cust = _booking_and_customer(con, bid)
    s = payments.card_setup_session(_stripe_customer(con, cust), row["ref"], _site_url())
    log(con, bid, "system", "card_setup", "Checkout session %s" % s.get("id"))
    con.commit()
    return s.get("url")


def mark_paid(con, bid, cents, method, intent=None, actor="system"):
    """Record money in. Idempotent: a second call for a paid booking is a no-op
    and returns False, so the webhook and the return page can both fire."""
    row = db.one(con.execute("SELECT * FROM bookings WHERE id=?", (bid,)))
    if not row or row.get("payment_status") == "paid":
        return False
    con.execute("UPDATE bookings SET payment_status='paid', paid_cents=?, paid_at=?, "
                "paid_method=?, stripe_payment_intent=COALESCE(?, stripe_payment_intent), "
                "payment_error=NULL WHERE id=?",
                (int(cents), db.now(), method, intent, bid))
    log(con, bid, actor, "paid", "%s %s" % (method, notify._money(int(cents))))
    con.commit()
    notify.ping_owner(CFG, "PAID %s: %s by %s." % (row["ref"], notify._money(int(cents)), method),
                      "Paid: %s %s" % (row["ref"], notify._money(int(cents))))
    # Tell the ad platforms about the sale. Every method counts (a Zelle
    # payment is as much a customer as a card one); ids match the browser's.
    cust = db.one(con.execute("SELECT email, phone FROM customers WHERE id=?",
                              (row["customer_id"],))) or {}
    try:
        ids = json.loads(row.get("ad_ids") or "{}")
    except ValueError:
        ids = {}
    conversions.purchase(row["ref"], int(cents), cust.get("email"), cust.get("phone"), ids)
    return True


def apply_checkout_session(con, s):
    """Record what a finished Checkout Session means for its booking."""
    out = payments.session_outcome(s)
    row = db.one(con.execute("SELECT * FROM bookings WHERE upper(ref)=upper(?)",
                             (out["ref"] or "",)))
    if not row or not out["kind"]:
        return None
    if out["customer"]:
        con.execute("UPDATE customers SET stripe_customer=COALESCE(stripe_customer, ?) "
                    "WHERE id=?", (out["customer"], row["customer_id"]))
    if out["kind"] == "card_saved":
        if row.get("payment_status") not in ("paid",):
            con.execute("UPDATE bookings SET payment_status='card_saved', "
                        "stripe_payment_method=? WHERE id=?", (out["payment_method"], row["id"]))
            log(con, row["id"], "customer", "card_saved", "Card saved via Stripe")
            con.commit()
            # A card saved after the clean was already done: charge it now.
            if row["status"] == "completed":
                charge_booking(con, row["id"])
    elif out["kind"] == "paid":
        if out["payment_method"]:
            con.execute("UPDATE bookings SET stripe_payment_method=? WHERE id=?",
                        (out["payment_method"], row["id"]))
        mark_paid(con, row["id"], out["amount"] or row["total_cents"], "card",
                  out["payment_intent"])
    con.commit()
    return out["kind"]


def send_pay_link(con, bid, reason=None):
    """Make a Checkout pay link for the visit, email it, and return the url."""
    row, cust = _booking_and_customer(con, bid)
    svc = next((x for x in CFG["services"] if x["id"] == row["service_id"]), {})
    s = payments.pay_link_session(_stripe_customer(con, cust), row["ref"], row["total_cents"],
                                  "%s, %s (%s)" % (svc.get("name", "Cleaning"),
                                                   notify.nice_date(row["date"]), row["ref"]),
                                  _site_url())
    url = s.get("url")
    con.execute("UPDATE bookings SET payment_status='link_sent', pay_link_url=?, "
                "payment_error=? WHERE id=?", (url, reason, bid))
    log(con, bid, "system", "pay_link", reason or "Pay link sent")
    con.commit()
    subj, text, html = notify.pay_link_email(CFG, dict(cust), dict(row), url)
    notify.send(cust["email"], subj, text, html)
    return url


def charge_booking(con, bid):
    """Charge the saved card, or fall back to a pay link. Never raises for a
    card problem: returns {"status": "paid"|"link_sent"|"failed"|..., ...}."""
    row, cust = _booking_and_customer(con, bid)
    if row.get("payment_status") == "paid":
        return {"status": "paid", "already": True}
    if row["total_cents"] <= 0:
        mark_paid(con, bid, 0, "credit")
        return {"status": "paid"}
    if not payments.configured():
        return {"status": "off", "message": "Card payments are not set up (STRIPE_SECRET_KEY)."}
    if row.get("stripe_payment_method") and cust.get("stripe_customer"):
        try:
            pi = payments.charge_saved_card(
                cust["stripe_customer"], row["stripe_payment_method"], row["total_cents"],
                row["ref"], "%s cleaning %s" % (CFG["name"], row["ref"]))
            if pi.get("status") == "succeeded":
                mark_paid(con, bid, pi.get("amount_received") or row["total_cents"],
                          "card", pi.get("id"))
                return {"status": "paid"}
            reason = "Card needs the customer to approve (%s)" % pi.get("status")
        except payments.StripeError as e:
            reason = "Card charge failed: %s" % e
        con.execute("UPDATE bookings SET payment_status='failed', payment_error=? WHERE id=?",
                    (reason, bid))
        con.commit()
        notify.ping_owner(CFG, "PAYMENT FAILED %s: %s. Sending them a pay link." %
                          (row["ref"], reason), "Payment failed: %s" % row["ref"])
    else:
        reason = None
    try:
        url = send_pay_link(con, bid, reason)
        return {"status": "link_sent", "url": url, "reason": reason}
    except payments.StripeError as e:
        con.execute("UPDATE bookings SET payment_status='failed', payment_error=? WHERE id=?",
                    (str(e), bid))
        con.commit()
        return {"status": "failed", "message": str(e)}


def on_job_completed(con, bid):
    """The clean is done: write the cleaner's payout line, then collect.
    Both are best-effort; closing out a job must never fail on them."""
    try:
        row = db.one(con.execute("SELECT * FROM bookings WHERE id=?", (bid,)))
        payouts.record_for_booking(con, row, db.now())
        con.commit()
    except Exception as e:                                   # noqa: BLE001
        print("  [payouts] skipped for booking %s: %s" % (bid, e), flush=True)
    if (CFG.get("payments") or {}).get("auto_charge_on_complete", True) and payments.configured():
        try:
            charge_booking(con, bid)
        except Exception as e:                               # noqa: BLE001
            print("  [stripe] charge skipped for booking %s: %s" % (bid, e), flush=True)
    try:
        schedule_next_visit(con, bid)
    except Exception as e:                                   # noqa: BLE001
        print("  [recurring] next visit skipped for booking %s: %s" % (bid, e), flush=True)


@route("GET", "/api/payments/return")
def api_payment_return(ctx):
    """The customer's browser lands here from Stripe. We ask Stripe ourselves
    rather than trusting the URL, so this works with no webhook configured."""
    sid = (ctx["query"].get("session_id", [""])[0]).strip()
    if not sid.startswith("cs_"):
        raise ApiError("Missing checkout session.")
    try:
        s = payments.get_session(sid)
        kind = apply_checkout_session(ctx["con"], s)
    except payments.StripeError as e:
        raise ApiError(str(e), 502)
    # Value and ref let the page fire one de-duplicated Purchase event.
    return {"ok": True, "result": kind, "ref": payments.session_outcome(s)["ref"],
            "amount_cents": s.get("amount_total") if kind == "paid" else None}


@route("POST", "/api/stripe/webhook")
def api_stripe_webhook(ctx):
    try:
        ev = payments.verify_webhook(ctx["raw"].encode(), ctx["headers"].get("Stripe-Signature"))
    except ValueError as e:
        raise ApiError("Webhook rejected: %s" % e, 400)
    obj = (ev.get("data") or {}).get("object") or {}
    con = ctx["con"]
    if ev.get("type") in ("checkout.session.completed",
                          "checkout.session.async_payment_succeeded"):
        apply_checkout_session(con, payments.get_session(obj["id"]))
    elif ev.get("type") == "payment_intent.payment_failed":
        ref = (obj.get("metadata") or {}).get("ref")
        row = db.one(con.execute("SELECT * FROM bookings WHERE ref=?", (ref or "",)))
        if row and row.get("payment_status") != "paid":
            msg = ((obj.get("last_payment_error") or {}).get("message")) or "declined"
            con.execute("UPDATE bookings SET payment_status='failed', payment_error=? "
                        "WHERE id=?", (msg, row["id"]))
            con.commit()
    return {"received": True}


# --------------------------------------------------------------------------
# recurring visits
# --------------------------------------------------------------------------

RECUR_DAYS = {"weekly": 7, "biweekly": 14, "monthly": 28}


def _find_slot(con, target, preferred):
    """Same weekday and slot if free; otherwise another slot that day, then
    the nearest day either side (up to 3). Respects every capacity cap,
    because it asks the same availability check the booking page uses."""
    for delta in (0, 1, -1, 2, -2, 3, -3):
        d = target + datetime.timedelta(days=delta)
        st = api_availability({"con": con, "query": {"date": [d.isoformat()],
                                                     "service": ["residential"]}})
        free = st.get("slots") or []
        if st.get("open") and free:
            return d.isoformat(), (preferred if preferred in free else free[0])
    return None, None


def schedule_next_visit(con, bid, skipped=False):
    """After a recurring visit is done (or skipped), book the next one.
    Returns the new booking id, or None (one-time job, already scheduled, or
    no room). A skipped visit doesn't count toward the intro discount."""
    row, cust = _booking_and_customer(con, bid)
    days = RECUR_DAYS.get(row["frequency"])
    if not days or row["service_id"] != "residential":
        return None
    if db.one(con.execute("SELECT id FROM bookings WHERE recurring_from=?", (bid,))):
        return None
    visit = (row.get("series_visit") or 1) + (0 if skipped else 1)
    first = bool(skipped and row["is_first_clean"])
    target = datetime.date.fromisoformat(row["date"]) + datetime.timedelta(days=days)
    date_s, slot = _find_slot(con, target, row["slot"])
    if not date_s:
        notify.ping_owner(CFG, "Couldn't auto-book %s's next %s visit around %s: no free slot. "
                          "Book it by hand. %s/admin" % (cust["name"], row["frequency"],
                                                         notify.nice_date(target.isoformat()),
                                                         _site_url()),
                          "Next visit needs booking: %s" % cust["name"])
        log(con, bid, "system", "recurring", "No free slot near %s" % target.isoformat())
        con.commit()
        return None

    intro = (CFG["pricing"].get("intro_offer") or {})
    q = pricing.quote(CFG, {"service": "residential", "tier_id": row["tier_id"],
                            "sqft": row["sqft"], "frequency": row["frequency"],
                            "addons": [], "city": cust.get("city"), "is_first_clean": first,
                            "intro_visit": visit <= 3 and row["frequency"] == intro.get("requires")})
    if q.get("error") or q.get("custom_quote"):
        log(con, bid, "system", "recurring", "Could not price next visit: %s" % q.get("error"))
        con.commit()
        return None

    ref = db.new_ref(CFG["booking"].get("ref_prefix", "TM"))
    while db.one(con.execute("SELECT id FROM bookings WHERE ref=?", (ref,))):
        ref = db.new_ref(CFG["booking"].get("ref_prefix", "TM"))
    has_card = bool(row.get("stripe_payment_method"))
    cur = con.execute(
        "INSERT INTO bookings (ref,customer_id,service_id,tier_id,frequency,sqft,addons,date,slot,"
        "status,is_first_clean,quote,total_cents,access_notes,notes,assigned_to,created_at,"
        "terms_version,terms_accepted_at,terms_accepted_ip,recurring_from,series_visit,"
        "stripe_payment_method,payment_status)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (ref, row["customer_id"], "residential", row["tier_id"], row["frequency"], row["sqft"],
         "[]", date_s, slot, "confirmed", int(first), json.dumps(q), q["total"], row["access_notes"],
         row["notes"], row["assigned_to"], db.now(), row["terms_version"],
         row["terms_accepted_at"], row["terms_accepted_ip"], bid, visit,
         row.get("stripe_payment_method") if has_card else None,
         "card_saved" if has_card else None))
    nid = cur.lastrowid
    for i, (area, label) in enumerate(checklists.for_service("residential")):
        con.execute("INSERT INTO tasks (booking_id,area,label,sort) VALUES (?,?,?,?)",
                    (nid, area, label, i))
    log(con, nid, "system", "created", "Auto-booked %s visit #%d after %s%s" %
        (row["frequency"], visit, row["ref"], " (skipped)" if skipped else ""))
    con.commit()

    nb = {"ref": ref, "date": date_s, "slot": slot, "total_cents": q["total"]}
    try:
        subj, text, html = notify.next_visit_email(CFG, dict(cust), nb, _site_url(), skipped=skipped)
        notify.send(cust["email"], subj, text, html)
    except Exception as e:                                   # noqa: BLE001
        print("  [notify] next-visit email skipped for %s: %s" % (ref, e))
    moved = "" if (date_s, slot) == (target.isoformat(), row["slot"]) else \
        " (moved from %s %s, that slot was taken)" % (target.isoformat(), row["slot"])
    notify.send_sms(notify.owner_phone(CFG), "%s %s's next visit: %s %s, %s%s." % (
        "Skipped one; auto-booked" if skipped else "Auto-booked", cust["name"], notify.nice_date(date_s), slot, notify._money(q["total"]), moved),
        owner=True)
    return nid


def customer_sms_on():
    return os.environ.get("CUSTOMER_SMS") == "1"


def send_reminders(con, day):
    """Day-before reminders: email (and text, with Twilio) each customer, and
    text each cleaner their list. Once per booking, guarded on the row."""
    rows = db.rows(con.execute(
        "SELECT * FROM bookings WHERE date=? AND status IN ('requested','confirmed') "
        "AND reminder_sent_at IS NULL", (day.isoformat(),)))
    per_cleaner = {}
    for row in rows:
        cust = db.one(con.execute("SELECT * FROM customers WHERE id=?", (row["customer_id"],)))
        subj, text, html = notify.reminder_email(CFG, cust, row, _site_url())
        notify.send(cust["email"], subj, text, html)
        # Texting customers needs their opt-in (TCPA, Twilio A2P rules): the
        # ticked box on /book, and CUSTOMER_SMS=1 once Twilio is registered.
        if cust.get("phone") and cust.get("sms_consent_at") and customer_sms_on():
            notify.send_sms(cust["phone"], "%s: reminder, your cleaning is tomorrow at %s. "
                            "Reply or call %s with any questions." % (
                                CFG["name"], row["slot"], CFG.get("phone", "")))
        con.execute("UPDATE bookings SET reminder_sent_at=? WHERE id=?", (db.now(), row["id"]))
        if row["assigned_to"]:
            per_cleaner.setdefault(row["assigned_to"], []).append((row, cust))
    con.commit()
    for sid, jobs in per_cleaner.items():
        st = db.one(con.execute("SELECT name, phone FROM staff WHERE id=?", (sid,)))
        if st and st.get("phone"):
            lines = ["Tomorrow (%s):" % notify.nice_date(day.isoformat())] + [
                "%s %s, %s %s" % (r["slot"], c["name"], c.get("address") or "", c.get("city") or "")
                for r, c in sorted(jobs, key=lambda rc: _slot_key(rc[0]["slot"]))]
            notify.send_sms(st["phone"], "\n".join(lines) + "\nDetails: %s/app" % _site_url())
    return len(rows)


# --------------------------------------------------------------------------
# owner phone page (/owner)
# --------------------------------------------------------------------------

THRESHOLD_1099_CENTS = 200000


def _threshold_1099():
    return int(((CFG.get("payouts") or {}).get("form_1099_threshold_cents"))
               or THRESHOLD_1099_CENTS)


def _unpaid_invoices(con):
    return db.rows(con.execute(
        "SELECT b.id, b.ref, b.date, b.slot, b.total_cents, b.payment_status, "
        "b.payment_error, b.pay_link_url, c.name, c.phone, c.email "
        "FROM bookings b JOIN customers c ON c.id=b.customer_id "
        "WHERE b.status='completed' AND b.total_cents > 0 "
        "AND COALESCE(b.payment_status,'') != 'paid' ORDER BY b.date"))


def _jobs_on(con, day):
    return sorted(db.rows(con.execute(
        "SELECT b.id, b.ref, b.date, b.slot, b.status, b.total_cents, b.service_id, "
        "b.access_notes, b.notes, b.payment_status, b.assigned_to, "
        "c.name, c.phone, c.address, c.city, s.name cleaner "
        "FROM bookings b JOIN customers c ON c.id=b.customer_id "
        "LEFT JOIN staff s ON s.id=b.assigned_to "
        "WHERE b.date=? AND b.status!='cancelled'", (day,))),
        key=lambda j: _slot_key(j["slot"]))


def _slot_key(slot):
    """'8:00 AM' sorts before '12:00 PM'. As text it would not."""
    try:
        return datetime.datetime.strptime(slot.strip(), "%I:%M %p").time()
    except (ValueError, AttributeError):
        return datetime.time(23, 59)


def local_today():
    return local_now().date()


def local_now():
    """Tampa time. Render runs in UTC, and a 7 AM text sent at 3 AM is no use."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/New_York")).replace(tzinfo=None)
    except Exception:                                        # noqa: BLE001
        # No tz database in the image: US Eastern DST rule by hand.
        utc = datetime.datetime.utcnow()
        y = utc.year
        mar = datetime.datetime(y, 3, 8 + (6 - datetime.date(y, 3, 8).weekday()) % 7, 7)
        nov = datetime.datetime(y, 11, 1 + (6 - datetime.date(y, 11, 1).weekday()) % 7, 6)
        return utc - datetime.timedelta(hours=4 if mar <= utc < nov else 5)


@route("GET", "/api/owner/summary")
def api_owner_summary(ctx):
    need_staff(ctx, ["owner"])
    con = ctx["con"]
    today = local_today()
    friday = payouts.week_ending_friday(today)
    due = payouts.friday_summary(con, friday)
    return {
        "today": today.isoformat(),
        "jobs_today": _jobs_on(con, today.isoformat()),
        "jobs_tomorrow": _jobs_on(con, (today + datetime.timedelta(days=1)).isoformat()),
        "unpaid": _unpaid_invoices(con),
        "payouts_due": due,
        "payout_text": payouts.text_summary(due, notify._money),
        "totals_1099": payouts.totals_1099(con, today.year, _threshold_1099()),
        "cleaners": db.rows(con.execute(
            "SELECT id, name, phone, role, pay_basis, hourly_rate_cents, company_rate_cents, "
            "payout_method, payout_handle FROM staff WHERE active=1 AND role != 'owner' "
            "ORDER BY name")),
        "status": {
            "card_payments": payments.mode(),
            "webhook": bool(os.environ.get("STRIPE_WEBHOOK_SECRET")),
            "email": notify.provider(),
            "sms": notify.sms_provider(),
            "owner_phone": notify.owner_phone(CFG),
        },
        "hourly_warning": payouts.HOURLY_1099_WARNING,
    }


@route("POST", "/api/owner/bookings/{bid}/charge")
def api_owner_charge(ctx, bid):
    need_staff(ctx, ["owner"])
    return charge_booking(ctx["con"], int(bid))


@route("POST", "/api/owner/bookings/{bid}/pay-link")
def api_owner_pay_link(ctx, bid):
    need_staff(ctx, ["owner"])
    try:
        return {"status": "link_sent", "url": send_pay_link(ctx["con"], int(bid))}
    except payments.StripeError as e:
        raise ApiError(str(e), 502)


@route("POST", "/api/owner/bookings/{bid}/mark-paid")
def api_owner_mark_paid(ctx, bid):
    s = need_staff(ctx, ["owner"])
    method = (ctx["body"].get("method") or "").strip()
    if method not in ("cash", "check", "zelle", "venmo", "card", "other"):
        raise ApiError("Pick how they paid: cash, check, zelle, venmo, card or other.")
    con = ctx["con"]
    row, _ = _booking_and_customer(con, int(bid))
    cents = int(ctx["body"].get("cents") or row["total_cents"])
    mark_paid(con, int(bid), cents, method, actor=s["name"])
    return {"ok": True}


@route("POST", "/api/owner/staff/{sid}/pay")
def api_owner_staff_pay(ctx, sid):
    """Set how a cleaner is paid and where to send it."""
    need_staff(ctx, ["owner"])
    b = ctx["body"]
    basis = b.get("pay_basis") or "split_a"
    if basis not in payouts.BASES:
        raise ApiError("Pay basis must be split_a, split_b or hourly.")

    def cents(k):
        v = b.get(k)
        if v in (None, ""):
            return None
        try:
            return int(round(float(v) * 100))
        except (TypeError, ValueError):
            raise ApiError("%s must be a dollar amount." % k)
    rate = cents("hourly_rate")
    if basis == "hourly" and not rate:
        raise ApiError("Enter the hourly rate.")
    con = ctx["con"]
    con.execute("UPDATE staff SET pay_basis=?, hourly_rate_cents=?, company_rate_cents=?, "
                "payout_method=?, payout_handle=? WHERE id=?",
                (basis, rate, cents("company_rate"), (b.get("payout_method") or "").strip(),
                 (b.get("payout_handle") or "").strip(), int(sid)))
    con.commit()
    return {"ok": True, "warning": payouts.HOURLY_1099_WARNING if basis == "hourly" else None}


@route("POST", "/api/owner/payouts/{pid}/hours")
def api_owner_payout_update(ctx, pid):
    """Correct the hours on an unpaid line (recomputes pay)."""
    need_staff(ctx, ["owner"])
    con = ctx["con"]
    p = db.one(con.execute("SELECT * FROM payouts WHERE id=?", (int(pid),)))
    if not p:
        raise ApiError("Payout line not found.", 404)
    if p["paid_at"]:
        raise ApiError("That line is already paid.")
    try:
        hours = float(ctx["body"].get("hours"))
    except (TypeError, ValueError):
        raise ApiError("Enter the hours as a number, e.g. 3.5")
    if not 0 < hours <= 14:
        raise ApiError("Hours must be between 0 and 14.")
    con.execute("UPDATE payouts SET hours=?, hours_override=1 WHERE id=?", (hours, int(pid)))
    row = db.one(con.execute("SELECT * FROM bookings WHERE id=?", (p["booking_id"],)))
    payouts.record_for_booking(con, row, db.now())
    con.commit()
    return db.one(con.execute("SELECT * FROM payouts WHERE id=?", (int(pid),)))


@route("POST", "/api/owner/payouts/pay-cleaner")
def api_owner_pay_cleaner(ctx):
    """Nate paid someone (Zelle/Venmo/etc): close every due line for them."""
    need_staff(ctx, ["owner"])
    b = ctx["body"]
    sid = int(b.get("staff_id") or 0)
    method = (b.get("method") or "").strip() or "zelle"
    con = ctx["con"]
    through = payouts.week_ending_friday(local_today()).isoformat()
    ids = [int(i) for i in (b.get("payout_ids") or [])]
    q = ("SELECT id, pay_cents, flags FROM payouts WHERE staff_id=? AND paid_at IS NULL "
         "AND week_ending <= ?")
    lines = db.rows(con.execute(q, (sid, through)))
    if ids:
        lines = [l for l in lines if l["id"] in ids]
    if any("needs_" in (l["flags"] or "") for l in lines):
        raise ApiError("Fill in the missing hours or hourly rate first.")
    for l in lines:
        con.execute("UPDATE payouts SET paid_at=?, paid_method=? WHERE id=?",
                    (db.now(), method, l["id"]))
    con.commit()
    return {"ok": True, "paid_lines": len(lines),
            "paid_cents": sum(l["pay_cents"] for l in lines)}


def daily_text(con, day=None):
    day = day or local_today()
    jobs = _jobs_on(con, day.isoformat())
    return notify.daily_schedule_text(CFG, day.isoformat(), jobs, len(_unpaid_invoices(con)))


@route("POST", "/api/owner/daily-text")
def api_owner_daily_text(ctx):
    need_staff(ctx, ["owner"])
    text = daily_text(ctx["con"])
    if ctx["body"].get("payouts"):
        text += "\n\n" + payouts.text_summary(payouts.friday_summary(ctx["con"]), notify._money)
    sent = notify.ping_owner(CFG, text, "Today's schedule") if ctx["body"].get("send") \
        else {"sms": False, "email": False}
    return {"text": text, "sent": sent}


def _daily_text_loop():
    """Once a day at DAILY_TEXT_HOUR (Tampa time, default 7), text Nate the
    day's jobs, and on Fridays the payouts due. Guarded in the database so a
    restart or a second worker never sends twice."""
    try:
        hour = int(os.environ.get("DAILY_TEXT_HOUR", "7"))
    except ValueError:
        hour = 7
    while True:
        try:
            now = local_now()
            # A three-hour window: a deploy at 10 PM must not send "today's"
            # schedule after the day is over.
            if hour <= now.hour < hour + 3:
                key = "daily_text:%s" % now.date().isoformat()
                con = db.connect()
                try:
                    cur = con.execute("INSERT OR IGNORE INTO kv (k, v) VALUES (?, ?)",
                                      (key, db.now()))
                    con.commit()
                    if cur.rowcount:
                        text = daily_text(con, now.date())
                        if now.weekday() == 4:
                            text += "\n\n" + payouts.text_summary(
                                payouts.friday_summary(con, now.date()), notify._money)
                        notify.ping_owner(CFG, text, "Today's schedule")
                        send_reminders(con, now.date() + datetime.timedelta(days=1))
                finally:
                    con.close()
        except Exception as e:                               # noqa: BLE001
            print("  [daily text] %s" % e, flush=True)
        time.sleep(300)


# --------------------------------------------------------------------------
# HTTP plumbing
# --------------------------------------------------------------------------
SAFE = re.compile(r"^[A-Za-z0-9_\-./]*$")


class Handler(BaseHTTPRequestHandler):
    server_version = "TampaMaids/1.0"
    sys_version = ""          # don't advertise the exact Python version publicly
    protocol_version = "HTTP/1.1"

    # The health check is the only request that repeats on a timer, so it is the
    # only one worth hiding: left in, it accounts for ~17,000 log lines a day and
    # makes the owner alerts impossible to find in Render's log view.
    QUIET_PATHS = ("/healthz",)

    def log_message(self, fmt, *args):
        if self.path in self.QUIET_PATHS:
            return
        sys.stderr.write("  %s  %s\n" % (self.log_date_time_string(), fmt % args))

    # ---- output helpers ----
    def _send(self, status, body, ctype, extra=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status, obj, extra=None):
        self._send(status, json.dumps(obj, default=str), "application/json; charset=utf-8", extra)

    def _client_ip(self):
        """Real client IP. Only trusts X-Forwarded-For when TRUST_PROXY is set,
        because otherwise anyone could spoof the header to dodge the throttle."""
        if TRUST_PROXY:
            fwd = self.headers.get("X-Forwarded-For", "")
            if fwd:
                return fwd.split(",")[0].strip()
        return self.client_address[0] if self.client_address else "?"

    def _is_https(self):
        if self.headers.get("X-Forwarded-Proto", "").lower() == "https":
            return True
        return FORCE_HTTPS

    def _cookies(self):
        raw = self.headers.get("Cookie", "")
        out = {}
        for part in raw.split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                out[k.strip()] = urllib.parse.unquote(v.strip())
        return out

    # ---- dispatch ----
    def _handle(self, method):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        if path.startswith("/api/"):
            return self._api(method, path, parsed)
        if method in ("GET", "HEAD"):
            return self._static(path)
        self._json(405, {"error": "Method not allowed"})

    def _api(self, method, path, parsed):
        con = db.connect()
        try:
            body = {}
            raw = ""
            if method == "POST":
                n = int(self.headers.get("Content-Length") or 0)
                if n > 2_000_000:
                    return self._json(413, {"error": "Request too large"})
                raw = self.rfile.read(n).decode("utf-8") if n else ""
                if raw:
                    try:
                        body = json.loads(raw)
                    except ValueError:
                        return self._json(400, {"error": "Malformed JSON body"})
                    if not isinstance(body, dict):
                        return self._json(400, {"error": "JSON body must be an object"})

            ctx = {"con": con, "body": body,
                   "query": urllib.parse.parse_qs(parsed.query),
                   "cookies": self._cookies(), "set_cookie": None,
                   "ip": self._client_ip(), "https": self._is_https(),
                   "raw": raw, "headers": self.headers}

            # Backup downloads return files, not JSON, so they are handled
            # before the JSON router rather than bending every response helper.
            if method == "GET" and path.startswith("/api/admin/backup"):
                try:
                    need_staff(ctx, ["owner"])
                except ApiError as e:
                    return self._json(e.status, {"error": e.message})
                stamp = datetime.datetime.now().strftime("%Y-%m-%d")
                if path.endswith("/bookings.csv"):
                    return self._send(200, backup.bookings_csv(), "text/csv; charset=utf-8",
                        {"Content-Disposition": 'attachment; filename="bookings-%s.csv"' % stamp,
                         "Cache-Control": "no-store"})
                if path.endswith("/customers.csv"):
                    return self._send(200, backup.customers_csv(), "text/csv; charset=utf-8",
                        {"Content-Disposition": 'attachment; filename="customers-%s.csv"' % stamp,
                         "Cache-Control": "no-store"})
                if path.endswith("/database.db"):
                    return self._send(200, backup.snapshot_bytes(), "application/octet-stream",
                        {"Content-Disposition": 'attachment; filename="tampamaids-%s.db"' % stamp,
                         "Cache-Control": "no-store"})
                return self._json(404, {"error": "Unknown backup file"})

            for m, rx, fn in ROUTES:
                if m != method:
                    continue
                match = rx.match(path)
                if match:
                    try:
                        result = fn(ctx, **match.groupdict())
                    except ApiError as e:
                        return self._json(e.status, {"error": e.message})
                    extra = {"Cache-Control": "no-store"}
                    if ctx["set_cookie"]:
                        k, v, age = ctx["set_cookie"]
                        # Mark the session cookie Secure whenever the request
                        # reached us over HTTPS, so it can never be replayed
                        # over a plaintext connection.
                        secure = "; Secure" if ctx.get("https") else ""
                        extra["Set-Cookie"] = (
                            "%s=%s; Path=/; HttpOnly; SameSite=Lax%s; Max-Age=%d"
                            % (k, urllib.parse.quote(v), secure, age))
                    return self._json(200, result, extra)
            self._json(404, {"error": "No such endpoint: %s %s" % (method, path)})
        except Exception as e:
            import traceback; traceback.print_exc()
            self._json(500, {"error": "Server error: %s" % e})
        finally:
            con.close()

    def _manifest(self):
        """Generated from business.json so the installed app name can never
        drift from the rest of the site."""
        m = {
            "name": CFG["name"],
            "short_name": CFG["short_name"],
            "description": CFG.get("description", ""),
            "start_url": "/app/",
            "scope": "/app/",
            "display": "standalone",
            "orientation": "portrait",
            "background_color": CFG["brand"]["primary"],
            "theme_color": CFG["brand"]["primary"],
            "categories": ["business", "lifestyle", "productivity"],
            "icons": [
                {"src": "/icons/icon-192.png", "sizes": "192x192",
                 "type": "image/png", "purpose": "any"},
                {"src": "/icons/icon-512.png", "sizes": "512x512",
                 "type": "image/png", "purpose": "any"},
                {"src": "/icons/icon-512-maskable.png", "sizes": "512x512",
                 "type": "image/png", "purpose": "maskable"},
            ],
            "shortcuts": [
                {"name": "Book a cleaning", "url": "/app/?tab=book",
                 "icons": [{"src": "/icons/icon-192.png", "sizes": "192x192"}]},
                {"name": "My cleanings", "url": "/app/?tab=jobs",
                 "icons": [{"src": "/icons/icon-192.png", "sizes": "192x192"}]},
            ],
        }
        self._send(200, json.dumps(m, indent=2),
                   "application/manifest+json; charset=utf-8",
                   {"Cache-Control": "no-cache"})

    def _static(self, path):
        # Render pings the health check every few seconds, forever. Answer it
        # here, before anything touches config or the database, and keep it out
        # of the access log (see log_message) so that a real booking alert is
        # not buried under thousands of health check lines.
        if path == "/healthz":
            return self._send(200, "ok", "text/plain; charset=utf-8",
                              {"Cache-Control": "no-store"})

        # Printed QR codes point at /review. Deliberately a 302, not a 301:
        # browsers cache 301s hard, and the cards cannot be reprinted when the
        # target changes. Kept out of the sitemap on purpose.
        if path.rstrip("/") == "/review":
            target = CFG.get("review_url")
            if not target:
                return self._send(503, "Review link not configured yet.",
                                  "text/plain; charset=utf-8")
            self.send_response(302)
            self.send_header("Location", target)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        # Shorter URLs people type or say out loud. A visitor who guesses
        # "/tampa" off a yard sign should land on the city page, not a 404.
        # 301 because these are permanent aliases, unlike /review above.
        alias = ALIASES.get(path.rstrip("/").lower() or "/")
        if alias:
            self.send_response(301)
            self.send_header("Location", alias)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if path == "/app/manifest.webmanifest":
            return self._manifest()
        # friendly URLs -> files
        if path in ("/", ""):
            path = "/index.html"
        elif path == "/app" or path == "/app/":
            path = "/app/index.html"
        elif path == "/admin" or path == "/admin/":
            path = "/admin/index.html"
        elif path == "/favicon.ico":
            path = "/icons/favicon-32.png"   # browsers ask for this unprompted
        elif not os.path.splitext(path)[1]:
            path = path + ".html"

        rel = path.lstrip("/")
        if not SAFE.match(rel) or ".." in rel:
            return self._send(400, "Bad path", "text/plain")
        full = os.path.normpath(os.path.join(WEB, rel))
        if not full.startswith(WEB) or not os.path.isfile(full):
            notfound = os.path.join(WEB, "404.html")
            if os.path.isfile(notfound):
                with open(notfound, "rb") as f:
                    return self._send(404, f.read(), "text/html; charset=utf-8")
            return self._send(404, "Not found", "text/plain")

        ctype, _ = mimetypes.guess_type(full)
        ctype = ctype or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript",
                                                  "application/json",
                                                  "application/manifest+json",
                                                  "image/svg+xml"):
            ctype += "; charset=utf-8"
        # ETag from size+mtime so edits are picked up immediately, while
        # unchanged files still cost only a 304. Nothing here is content-hashed,
        # so "no-cache" (revalidate every time) is the only safe default for
        # HTML/CSS/JS — otherwise an edit stays invisible for the cache lifetime.
        st = os.stat(full)
        # Ad tags are injected per response, so they are part of the ETag.
        tag_suffix = tags.inject(b"</head>", rel)[1] if rel.endswith(".html") else ""
        etag = '"%x-%x%s"' % (int(st.st_mtime), st.st_size, tag_suffix)
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        with open(full, "rb") as f:
            data = f.read()
        if rel.endswith(".html"):
            data = tags.inject(data, rel)[0]
        cache = ("public, max-age=31536000, immutable" if rel.startswith("fonts/")
                 else "public, max-age=86400" if rel.startswith("icons/")
                 else "no-cache")
        self._send(200, data, ctype, {"Cache-Control": cache, "ETag": etag})

    def do_GET(self):    self._handle("GET")
    def do_HEAD(self):   self._handle("HEAD")
    def do_POST(self):   self._handle("POST")


def main():
    ap = argparse.ArgumentParser(description="Tampa Maids Cleaning server")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    ap.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    args = ap.parse_args()

    db.init()

    # Loud warning if a seeded default password is still usable. This is the
    # single most likely way a live install gets compromised.
    try:
        con = db.connect()
        weak = [r["email"] for r in db.rows(con.execute("SELECT email, pw_hash, pw_salt FROM staff WHERE active=1"))
                if db.verify_password("cleanup2026", r["pw_hash"], r["pw_salt"])]
        con.close()
        if weak:
            print("\n  !! WARNING: these accounts still use the default password 'cleanup2026':")
            for e in weak:
                print("     - %s" % e)
            print("     Anyone who reads this project's README can sign in as them.")
            print("     Fix before going live: Dashboard -> Team, add a real account,")
            print("     then deactivate these.\n")
    except Exception:
        pass

    if notify.configured():
        print("  Email: %s, sending from %s" % (notify.provider(), notify.MAIL_FROM))
    else:
        print("  Email: NOT CONFIGURED — customers get no confirmation.")
        print("         Set POSTMARK_TOKEN + MAIL_FROM (or SMTP_HOST/USER/PASS) to turn it on.")

    if os.environ.get("DAILY_TEXT", "1") != "0":
        import threading
        threading.Thread(target=_daily_text_loop, daemon=True).start()
    print("  Cards: %s · Texts: %s" % (payments.mode(), notify.sms_provider()))

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    url = "http://%s:%d" % ("localhost" if args.host == "127.0.0.1" else args.host, args.port)
    print("\n  %s" % CFG["name"])
    print("  " + "-" * (len(CFG["name"]) + 2))
    print("  Website      %s" % url)
    print("  Phone app    %s/app     (open on your phone, then Add to Home Screen)" % url)
    print("  Owner admin  %s/admin" % url)
    print("\n  Ctrl-C to stop.\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.\n")


if __name__ == "__main__":
    main()
