"""Customer notifications.

Deliberately provider-agnostic and deliberately fail-safe:

  * If nothing is configured, messages are written to the log and the booking
    still succeeds. The business works without email; it just works better
    with it.
  * A provider outage must never cost a booking. Every send is wrapped, and
    a failure is logged and swallowed. Losing a confirmation email is an
    annoyance; losing the booking is lost revenue.

To turn it on, set ONE of these in the host's environment:

  POSTMARK_TOKEN=...            and MAIL_FROM=hello@tampamaidscleaning.com
  SMTP_HOST=... SMTP_USER=... SMTP_PASS=...  (SMTP_PORT defaults to 587)

MAIL_FROM must be an address the provider has verified for your domain, or
mail will be rejected or land in spam.
"""
import os
import json
import datetime
import smtplib
import ssl
import urllib.request
import urllib.error
from email.message import EmailMessage

POSTMARK_TOKEN = os.environ.get("POSTMARK_TOKEN", "").strip()
SMTP_HOST = os.environ.get("SMTP_HOST", "").strip()
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "").strip()
SMTP_PASS = os.environ.get("SMTP_PASS", "")
MAIL_FROM = os.environ.get("MAIL_FROM", "").strip()
OWNER_NOTIFY = os.environ.get("OWNER_NOTIFY", "").strip()  # optional: copy of every booking


def configured():
    return bool((POSTMARK_TOKEN or SMTP_HOST) and MAIL_FROM)


def provider():
    if POSTMARK_TOKEN and MAIL_FROM:
        return "postmark"
    if SMTP_HOST and MAIL_FROM:
        return "smtp"
    return "none"


def _send_postmark(to, subject, text, html):
    body = json.dumps({
        "From": MAIL_FROM, "To": to, "Subject": subject,
        "TextBody": text, "HtmlBody": html, "MessageStream": "outbound",
    }).encode()
    req = urllib.request.Request(
        "https://api.postmarkapp.com/email", data=body, method="POST",
        headers={"Accept": "application/json", "Content-Type": "application/json",
                 "X-Postmark-Server-Token": POSTMARK_TOKEN})
    with urllib.request.urlopen(req, timeout=12) as r:
        return r.status == 200


def _send_smtp(to, subject, text, html):
    msg = EmailMessage()
    msg["From"] = MAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
        s.starttls(context=ctx)
        if SMTP_USER:
            s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
    return True


def send(to, subject, text, html):
    """Returns True if handed to a provider. Never raises."""
    p = provider()
    if p == "none" or not to:
        print("  [email not configured] would send to %s: %s" % (to, subject))
        return False
    try:
        ok = _send_postmark(to, subject, text, html) if p == "postmark" \
            else _send_smtp(to, subject, text, html)
        print("  [email sent via %s] %s: %s" % (p, to, subject))
        return ok
    except Exception as e:                                   # noqa: BLE001
        # Swallow deliberately: a booking must never fail because email did.
        print("  [email FAILED via %s] %s: %s — %s" % (p, to, subject, e))
        return False


# ---------------------------------------------------------------- content

def _money(c):
    return "${:,.2f}".format(c / 100.0)


def nice_date(iso):
    """2026-10-08 -> Thursday, October 8. Customers read dates, not ISO."""
    try:
        d = datetime.date.fromisoformat(iso)
        return "%s, %s %d" % (d.strftime("%A"), d.strftime("%B"), d.day)
    except Exception:
        return iso


def booking_confirmation(cfg, booking, customer, quote):
    """(subject, text, html) for the customer's confirmation."""
    name = (customer.get("name") or "").split(" ")[0] or "there"
    brand = cfg["name"]
    ref = booking["ref"]
    when = "%s at %s" % (nice_date(booking["date"]), booking["slot"])
    total = _money(booking["total_cents"])
    recurring = quote.get("recurring_total")
    site = cfg.get("url", "https://tampamaidscleaning.com")

    lines = [
        "Hi %s," % name,
        "",
        "You're booked. Here are the details:",
        "",
        "  Reference   %s" % ref,
        "  Service     %s" % quote.get("service", "Cleaning"),
        "  When        %s" % when,
        "  Address     %s, %s" % (customer.get("address", ""), customer.get("city", "")),
        "  Total       %s" % total,
    ]
    if recurring and recurring != booking["total_cents"]:
        lines.append("  After that  %s per visit" % _money(recurring))
    lines += [
        "",
        "Your first visit is priced as a deep clean to bring the home to a",
        "maintainable baseline. Every visit after that is your normal rate.",
        "",
        "No payment is due now — you're charged after the clean is done.",
        "",
        "Need to change or cancel? Free up to 48 hours before your visit:",
        "%s/track  (reference %s)" % (site, ref),
        "",
        "If anything is missed, tell us within 24 hours and we re-clean it free.",
        "",
        "Questions? Just reply to this email or call %s." % cfg["phone"],
        "",
        "— %s" % brand,
        "%s" % site,
    ]
    text = "\n".join(lines)

    rows = "".join(
        '<tr><td style="padding:6px 16px 6px 0;color:#52646c">%s</td>'
        '<td style="padding:6px 0;font-weight:600">%s</td></tr>' % (k, v)
        for k, v in [
            ("Reference", ref),
            ("Service", quote.get("service", "Cleaning")),
            ("When", when),
            ("Address", "%s, %s" % (customer.get("address", ""), customer.get("city", ""))),
            ("Total", total),
        ] + ([("After that", "%s per visit" % _money(recurring))]
             if recurring and recurring != booking["total_cents"] else []))

    html = """<!doctype html><html><body style="margin:0;background:#f4f1ea;
 font:16px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#14262e">
<div style="max-width:560px;margin:0 auto;padding:28px 20px">
  <p style="font-size:1.35rem;font-weight:700;margin:0 0 4px">You're booked.</p>
  <p style="color:#52646c;margin:0 0 22px">Hi %(name)s — here are your details.</p>
  <table style="width:100%%;background:#fff;border:1px solid #e2dccf;border-radius:12px;
   padding:14px 18px;border-collapse:separate">%(rows)s</table>
  <p style="color:#52646c;font-size:.94rem;margin:18px 0">Your first visit is priced as a
  deep clean to bring the home to a maintainable baseline. Every visit after that is your
  normal rate. <b>No payment is due now</b> — you're charged after the clean.</p>
  <p style="margin:22px 0"><a href="%(site)s/track"
   style="background:#0c4a5c;color:#f7f3ec;text-decoration:none;font-weight:700;
   padding:12px 20px;border-radius:999px;display:inline-block">Manage this booking</a></p>
  <p style="color:#52646c;font-size:.9rem">Change or cancel free up to 48 hours before your
  visit, using reference <b>%(ref)s</b>. If anything is missed, tell us within 24 hours and
  we re-clean it free.</p>
  <p style="color:#52646c;font-size:.9rem">Questions? Reply to this email or call
  <a href="tel:%(phone_raw)s" style="color:#0c4a5c">%(phone)s</a>.</p>
  <p style="color:#7d949a;font-size:.84rem;border-top:1px solid #e2dccf;padding-top:14px">
  %(brand)s · <a href="%(site)s" style="color:#0c4a5c">%(site_short)s</a></p>
</div></body></html>""" % {
        "name": name, "rows": rows, "site": site, "ref": ref,
        "phone": cfg["phone"], "phone_raw": cfg["phone_raw"], "brand": brand,
        "site_short": site.replace("https://", ""),
    }
    return ("Your cleaning is booked — %s" % ref, text, html)


def owner_alert(cfg, booking, customer, quote):
    ref = booking["ref"]
    text = "\n".join([
        "New booking: %s" % ref,
        "",
        "  %s — %s" % (quote.get("service", "Cleaning"), _money(booking["total_cents"])),
        "  %s at %s" % (nice_date(booking["date"]), booking["slot"]),
        "  %s · %s · %s" % (customer.get("name"), customer.get("phone"), customer.get("email")),
        "  %s, %s" % (customer.get("address", ""), customer.get("city", "")),
        "  Access: %s" % (booking.get("access_notes") or "not provided"),
        "  Notes: %s" % (booking.get("notes") or "none"),
        "",
        "%s/admin" % cfg.get("url", ""),
    ])
    html = "<pre style=\"font:14px/1.5 ui-monospace,monospace\">%s</pre>" % text
    return ("New booking %s — %s" % (ref, _money(booking["total_cents"])), text, html)


# Kept so nothing that imported the private name breaks.
_nice_date = nice_date
