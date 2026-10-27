"""Contractor payout ledger: what each cleaner earned, and what is due Friday.

Cleaners are 1099 independent contractors, paid per completed job under one
of three bases, set per cleaner in the owner page:

  split_a   Schedule A (solo cleaners): 50% of the job price
            (independent-contractor-agreement.md section 3).
  split_b   Schedule B (established companies): their own rate, capped at
            65% of the job price AND at whatever leaves us $45 on the job.
  hourly    an hourly rate x hours on the job. Nate asked for this. It is
            supported, but paying by the hour for set hours is one of the
            things that makes a contractor look like an employee, so the
            payout summary carries a warning until an attorney signs off.

Money is integer cents throughout. Pay is never negative, and a job that pays
the cleaner more than leaves the minimum margin is flagged, not silently cut,
except under Schedule B where the cap is the contract.
"""
import datetime

SPLIT_A_SHARE = 0.50
SPLIT_B_CAP = 0.65
MIN_MARGIN_CENTS = 4500

BASES = ("split_a", "split_b", "hourly")

HOURLY_1099_WARNING = (
    "Heads up: paying a contractor by the hour for hours you set is one of the "
    "factors the IRS and Florida use to treat a contractor as an employee. "
    "Per-job pay (Schedule A/B) is the safer default. Have the attorney review "
    "hourly pay before relying on it.")


def compute_pay(basis, price_cents, hours=None, hourly_rate_cents=None,
                company_rate_cents=None, share=SPLIT_A_SHARE):
    """Returns (pay_cents, flags). flags is a list of short strings."""
    price = max(0, int(price_cents or 0))
    flags = []
    if basis == "split_a":
        pay = int(round(price * share))
    elif basis == "split_b":
        rate = int(company_rate_cents if company_rate_cents is not None else price)
        cap = min(int(price * SPLIT_B_CAP), price - MIN_MARGIN_CENTS)
        if rate > cap:
            flags.append("capped")
        pay = min(rate, cap)
    elif basis == "hourly":
        if hours is None or hourly_rate_cents is None:
            raise ValueError("hourly pay needs hours and an hourly rate")
        pay = int(round(float(hours) * int(hourly_rate_cents)))
        flags.append("hourly")
    else:
        raise ValueError("unknown pay basis %r" % basis)
    pay = max(0, pay)
    if price - pay < MIN_MARGIN_CENTS:
        flags.append("low_margin")
    return pay, flags


def week_ending_friday(d):
    """The Friday a job's pay is due. Weeks run Saturday to Friday, so a job
    on Friday is paid that same Friday, and a Saturday job the next one."""
    if isinstance(d, str):
        d = datetime.date.fromisoformat(d[:10])
    return d + datetime.timedelta(days=(4 - d.weekday()) % 7)


def hours_between(started_at, completed_at):
    try:
        a = datetime.datetime.fromisoformat(started_at)
        b = datetime.datetime.fromisoformat(completed_at)
    except (TypeError, ValueError):
        return None
    h = (b - a).total_seconds() / 3600.0
    return round(h, 2) if 0.25 <= h <= 14 else None


def record_for_booking(con, booking, now_s):
    """Create (or refresh, if still unpaid) the ledger line for a completed job.
    Returns the payout row id, or None when nobody is assigned."""
    sid = booking.get("assigned_to")
    if not sid:
        return None
    st = con.execute("SELECT * FROM staff WHERE id=?", (sid,)).fetchone()
    if not st:
        return None
    st = dict(st)
    existing = con.execute("SELECT * FROM payouts WHERE booking_id=?",
                           (booking["id"],)).fetchone()
    if existing and existing["paid_at"]:
        return existing["id"]                  # never rewrite a paid line
    basis = st.get("pay_basis") or "split_a"
    hours = (existing["hours"] if existing and existing["hours_override"] else None) \
        or hours_between(booking.get("started_at"), booking.get("completed_at"))
    rate = st.get("hourly_rate_cents")
    if basis == "hourly" and (hours is None or not rate):
        # Can't price it yet. Record the line with zero pay and a flag so it
        # shows up for Nate to fill in, instead of disappearing.
        pay, flags = 0, ["needs_hours" if hours is None else "needs_rate", "hourly"]
    else:
        pay, flags = compute_pay(basis, booking["total_cents"], hours, rate,
                                 st.get("company_rate_cents"))
    week = week_ending_friday(booking["date"]).isoformat()
    if existing:
        con.execute("UPDATE payouts SET staff_id=?, hours=?, job_price_cents=?, pay_cents=?, "
                    "pay_basis=?, flags=?, week_ending=? WHERE id=?",
                    (sid, hours, booking["total_cents"], pay, basis, ",".join(flags),
                     week, existing["id"]))
        return existing["id"]
    cur = con.execute(
        "INSERT INTO payouts (booking_id, staff_id, job_date, hours, job_price_cents, "
        "pay_cents, pay_basis, flags, week_ending, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (booking["id"], sid, booking["date"], hours, booking["total_cents"], pay, basis,
         ",".join(flags), week, now_s))
    return cur.lastrowid


def friday_summary(con, through=None):
    """Unpaid pay grouped per cleaner, for every Friday up to `through`."""
    if through is None:
        through = week_ending_friday(datetime.date.today())
    if not isinstance(through, str):
        through = through.isoformat()
    rows = [dict(r) for r in con.execute(
        "SELECT p.*, s.name, s.payout_handle, s.payout_method, b.ref "
        "FROM payouts p JOIN staff s ON s.id = p.staff_id "
        "JOIN bookings b ON b.id = p.booking_id "
        "WHERE p.paid_at IS NULL AND p.week_ending <= ? "
        "ORDER BY s.name, p.job_date", (through,))]
    people = {}
    for r in rows:
        p = people.setdefault(r["staff_id"], {
            "staff_id": r["staff_id"], "name": r["name"],
            "method": r["payout_method"] or "", "handle": r["payout_handle"] or "",
            "amount_cents": 0, "jobs": [], "hourly": False, "needs_attention": False})
        p["amount_cents"] += r["pay_cents"]
        p["jobs"].append({"id": r["id"], "ref": r["ref"], "date": r["job_date"],
                          "hours": r["hours"], "price_cents": r["job_price_cents"],
                          "pay_cents": r["pay_cents"], "basis": r["pay_basis"],
                          "flags": [f for f in (r["flags"] or "").split(",") if f]})
        flags = r["flags"] or ""
        p["hourly"] = p["hourly"] or r["pay_basis"] == "hourly"
        p["needs_attention"] = p["needs_attention"] or "needs_" in flags
    out = sorted(people.values(), key=lambda p: p["name"].lower())
    return {"through": through, "cleaners": out,
            "total_cents": sum(p["amount_cents"] for p in out),
            "warning": HOURLY_1099_WARNING if any(p["hourly"] for p in out) else None}


def totals_1099(con, year, threshold_cents):
    """Paid per cleaner in a calendar year (cash basis: by the date Nate paid)."""
    rows = [dict(r) for r in con.execute(
        "SELECT s.id staff_id, s.name, COALESCE(SUM(p.pay_cents),0) paid_cents, COUNT(p.id) jobs "
        "FROM staff s JOIN payouts p ON p.staff_id = s.id "
        "WHERE p.paid_at IS NOT NULL AND substr(p.paid_at,1,4) = ? "
        "GROUP BY s.id ORDER BY paid_cents DESC", (str(year),))]
    for r in rows:
        r["needs_1099"] = r["paid_cents"] >= threshold_cents
    return {"year": int(year), "threshold_cents": threshold_cents, "cleaners": rows}


def text_summary(summary, money):
    """The Friday text: one line per cleaner, short enough for an SMS."""
    if not summary["cleaners"]:
        return "Payouts: nothing due this Friday."
    lines = ["Payouts due Fri %s: %s total" % (summary["through"][5:], money(summary["total_cents"]))]
    for p in summary["cleaners"]:
        handle = ("%s %s" % (p["method"], p["handle"])).strip() or "no handle on file"
        lines.append("- %s %s (%d job%s) -> %s%s" % (
            p["name"], money(p["amount_cents"]), len(p["jobs"]),
            "" if len(p["jobs"]) == 1 else "s", handle,
            " CHECK HOURS" if p["needs_attention"] else ""))
    if summary["warning"]:
        lines.append("Hourly pay = 1099 risk, ask the attorney.")
    return "\n".join(lines)
