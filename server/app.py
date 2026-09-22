#!/usr/bin/env python3
"""Tampa Maids Cleaning — website, booking API, admin and crew backend.

Stdlib only. No pip install, no virtualenv, no build step.

    python3 server/app.py            # http://localhost:8000
    python3 server/app.py --port 9000 --host 0.0.0.0
"""
import os, sys, json, re, io, time, argparse, datetime, mimetypes, secrets, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db, pricing, checklists

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
CONFIG_PATH = os.path.join(ROOT, "business.json")

SESSION_DAYS = 14

# Set these in production (see README "Going live").
TRUST_PROXY = os.environ.get("TRUST_PROXY", "").lower() in ("1", "true", "yes")
FORCE_HTTPS = os.environ.get("FORCE_HTTPS", "").lower() in ("1", "true", "yes")
mimetypes.add_type("application/manifest+json", ".webmanifest")
mimetypes.add_type("image/svg+xml", ".svg")


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

    d = parse_date(date_s)
    avail = api_availability({**ctx, "query": {"date": [date_s],
                                               "service": [b.get("service", "residential")]}})
    if not avail.get("open") or slot not in (avail.get("slots") or []):
        raise ApiError("Sorry — %s at %s just filled up. Please pick another time." % (date_s, slot))

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

    ref = db.new_ref(CFG["booking"].get("ref_prefix", "TM"))
    while db.one(con.execute("SELECT id FROM bookings WHERE ref=?", (ref,))):
        ref = db.new_ref(CFG["booking"].get("ref_prefix", "TM"))

    cur = con.execute(
        "INSERT INTO bookings (ref,customer_id,service_id,tier_id,frequency,sqft,addons,"
        "date,slot,status,is_first_clean,quote,total_cents,access_notes,notes,created_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (ref, cid, b.get("service", "residential"), b.get("tier_id"),
         b.get("frequency", "once"), b.get("sqft") or None,
         json.dumps(b.get("addons") or []), date_s, slot, "requested",
         1 if b.get("is_first_clean", True) else 0,
         json.dumps(q), q["total"], b.get("access_notes"), b.get("notes"), db.now()))
    bid = cur.lastrowid

    for i, (area, label) in enumerate(checklists.for_service(b.get("service", "residential"))):
        con.execute("INSERT INTO tasks (booking_id,area,label,sort) VALUES (?,?,?,?)",
                    (bid, area, label, i))

    log(con, bid, name, "created", "Booked online for %s at %s" % (date_s, slot))
    con.commit()
    return {"ok": True, "ref": ref, "id": bid, "quote": q,
            "date": date_s, "slot": slot,
            "message": "You're booked. A confirmation is on its way to %s." % email}


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
        "assigned_to": row.get("assigned_to"), "assigned_name": assigned,
        "customer": {"name": cust["name"], "email": cust["email"], "phone": cust["phone"],
                     "address": cust["address"], "city": cust["city"], "zip": cust["zip"]},
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


@route("POST", "/api/bookings/cancel")
def api_cancel(ctx):
    ref, email = require(ctx["body"], "ref", "email")
    con = ctx["con"]
    row = db.one(con.execute(
        "SELECT b.* FROM bookings b JOIN customers c ON c.id=b.customer_id "
        "WHERE upper(b.ref)=? AND lower(c.email)=lower(?)", (ref.upper(), email)))
    if not row:
        raise ApiError("We couldn't find that booking.", 404)
    if row["status"] in ("cancelled", "completed"):
        raise ApiError("That booking is already %s." % row["status"])

    when = datetime.datetime.fromisoformat(row["date"] + "T00:00:00")
    hours = (when - datetime.datetime.now()).total_seconds() / 3600.0
    fee = hours < 48
    con.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (row["id"],))
    log(con, row["id"], email, "cancelled",
        "Inside 48 hours — fee applies" if fee else "Free cancellation")
    con.commit()
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
    con = ctx["con"]
    con.execute(
        "INSERT INTO leads (name,email,phone,kind,message,payload,created_at) VALUES (?,?,?,?,?,?,?)",
        (name, email, b.get("phone"), b.get("kind", "contact"), b.get("message"),
         json.dumps(b), db.now()))
    con.commit()
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
# HTTP plumbing
# --------------------------------------------------------------------------
SAFE = re.compile(r"^[A-Za-z0-9_\-./]*$")


class Handler(BaseHTTPRequestHandler):
    server_version = "TampaMaids/1.0"
    sys_version = ""          # don't advertise the exact Python version publicly
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
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
                   "ip": self._client_ip(), "https": self._is_https()}

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
        etag = '"%x-%x"' % (int(st.st_mtime), st.st_size)
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        with open(full, "rb") as f:
            data = f.read()
        cache = ("public, max-age=86400" if rel.startswith("icons/")
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
