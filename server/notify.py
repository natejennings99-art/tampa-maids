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

def _esc(v):
    """Minimal HTML escape for values dropped into an email body."""
    return (str(v or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


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


def lead_alert(cfg, lead):
    """Tell the owner a contact-form enquiry arrived.

    The form answers "we'll be back to you within one business day", and
    nothing was notifying anybody -- not even a failed attempt. A promise like
    that is worse than no promise when it is kept by accident or not at all.
    """
    who = lead.get("name") or "Someone"
    kind = (lead.get("kind") or "contact").replace("_", " ")
    site = cfg.get("url", "https://tampamaidscleaning.com")
    lines = [
        "%s got in touch via the %s form." % (who, kind),
        "",
        "  Name     %s" % who,
        "  Email    %s" % (lead.get("email") or "-"),
        "  Phone    %s" % (lead.get("phone") or "-"),
        "",
        "  Message",
        "  %s" % ((lead.get("message") or "(none)").replace("\n", "\n  ")),
        "",
        "They were told we would reply within one business day.",
        "",
        "%s/admin  ->  Leads" % site,
    ]
    text = "\n".join(lines)
    html = ("<!doctype html><html><body style=\"font:16px/1.55 -apple-system,"
            "BlinkMacSystemFont,'Segoe UI',sans-serif;color:#14262e\">"
            "<p><b>%s</b> got in touch via the %s form.</p>"
            "<p>Email: %s<br>Phone: %s</p><blockquote style=\"margin:0;"
            "padding:10px 14px;border-left:3px solid #0c4a5c;background:#f4f1ea\">%s"
            "</blockquote><p>They were told we would reply <b>within one business "
            "day</b>.</p><p><a href=\"%s/admin\">Open the dashboard</a></p>"
            "</body></html>") % (
        _esc(who), _esc(kind), _esc(lead.get("email") or "-"),
        _esc(lead.get("phone") or "-"),
        _esc(lead.get("message") or "(none)"), site)
    return ("New enquiry: %s" % who, text, html)


def review_request(cfg, booking, customer):
    """(subject, text, html) asking for a review after a completed clean.

    Reviews are the gate on the Google local pack, which is where people
    actually click for a cleaner: the Tampa competitors sitting in that pack
    have between 27 and 604 of them and we have none. So every finished job has
    to ask, and it has to ask by itself rather than when someone remembers.

    Deliberately NOT a satisfaction filter. Asking only the happy customers, or
    routing unhappy ones to a private form instead, is review gating -- it
    breaks Google's policies and the FTC's rules on endorsements. Everyone gets
    the same link and the same invitation to say what actually happened.
    """
    name = (customer.get("name") or "").split(" ")[0] or "there"
    brand = cfg["name"]
    site = cfg.get("url", "https://tampamaidscleaning.com")
    link = cfg.get("review_url") or (site + "/review")

    text = "\n".join([
        "Hi %s," % name,
        "",
        "Your clean is done, and I hope the place looks the way you wanted it to.",
        "",
        "We're a new business in Tampa, so a review genuinely changes things for",
        "us -- it's most of how anyone local decides whether to take a chance on",
        "a company they haven't heard of. It takes about a minute:",
        "",
        "  %s" % link,
        "",
        "If something wasn't right, please say so -- in the review or by replying",
        "here, whichever you prefer. We re-clean anything missed free within 24",
        "hours, and I'd rather fix it than have you not mention it.",
        "",
        "Thank you for giving us the work.",
        "",
        "— %s" % brand,
        "%s · %s" % (cfg["phone"], site),
    ])

    html = """<!doctype html><html><body style="margin:0;background:#f4f1ea;
 font:16px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#14262e">
<div style="max-width:560px;margin:0 auto;padding:28px 20px">
  <p style="font-size:1.35rem;font-weight:700;margin:0 0 4px">How did we do?</p>
  <p style="color:#52646c;margin:0 0 20px">Hi %(name)s \u2014 your clean is done, and I hope
  the place looks the way you wanted it to.</p>
  <p style="margin:0 0 20px">We're a new business in Tampa, so a review genuinely changes
  things for us. It's most of how anyone local decides whether to take a chance on a
  company they haven't heard of, and it takes about a minute.</p>
  <p style="margin:22px 0"><a href="%(link)s"
   style="background:#0c4a5c;color:#f7f3ec;text-decoration:none;font-weight:700;
   padding:12px 20px;border-radius:999px;display:inline-block">Leave a review</a></p>
  <p style="color:#52646c;font-size:.94rem">If something wasn't right, please say so
  \u2014 in the review or by replying to this email, whichever you prefer. We re-clean
  anything missed free within 24 hours, and I'd rather fix it than have you not
  mention it.</p>
  <p style="color:#7d949a;font-size:.84rem;border-top:1px solid #e2dccf;padding-top:14px">
  %(brand)s \u00b7 <a href="tel:%(phone_raw)s" style="color:#0c4a5c">%(phone)s</a>
  \u00b7 <a href="%(site)s" style="color:#0c4a5c">%(site_short)s</a></p>
</div></body></html>""" % {
        "name": name, "link": link, "brand": brand, "phone": cfg["phone"],
        "phone_raw": cfg["phone_raw"], "site": site,
        "site_short": site.replace("https://", ""),
    }
    return ("How did we do? \u2014 %s" % brand, text, html)


def referral_invite(cfg, customer, code):
    """Give a customer their referral code after a completed clean.

    Cleaning is a referral trade: people ask their neighbours, not Google, and
    a happy customer with a code in their inbox is the cheapest acquisition
    there is. The credit was already configured and had never been built.

    Both sides get the credit. A one-sided offer asks someone to do unpaid
    marketing; a two-sided one gives them something to actually say.
    """
    name = (customer.get("name") or "").split(" ")[0] or "there"
    credit = _money(cfg["pricing"]["referral_credit"])
    site = cfg.get("url", "https://tampamaidscleaning.com")
    brand = cfg["name"]

    text = "\n".join([
        "Hi %s," % name,
        "",
        "If anyone asks you who cleans your place, here is something useful:",
        "",
        "  Your code:  %s" % code,
        "",
        "Give it to a friend and they get %s off their first clean." % credit,
        "You get %s off your next one when they book. No limit on how many," % credit,
        "and nothing expires.",
        "",
        "They just enter the code when they book at %s/book" % site,
        "",
        "No pressure at all -- it is only there if it is useful to you.",
        "",
        "- %s" % brand,
        "%s / %s" % (cfg["phone"], site),
    ])

    html = """<!doctype html><html><body style="margin:0;background:#f4f1ea;
 font:16px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#14262e">
<div style="max-width:560px;margin:0 auto;padding:28px 20px">
  <p style="font-size:1.35rem;font-weight:700;margin:0 0 4px">%(credit)s for you,
  %(credit)s for them.</p>
  <p style="color:#52646c;margin:0 0 20px">Hi %(name)s &mdash; if anyone asks who cleans
  your place, this is worth having.</p>
  <div style="background:#fff;border:1px solid #e2dccf;border-radius:12px;padding:18px;
   text-align:center;margin:0 0 20px">
    <div style="color:#52646c;font-size:.85rem;letter-spacing:.08em;text-transform:uppercase">
    Your code</div>
    <div style="font-size:1.8rem;font-weight:700;letter-spacing:.06em;margin-top:4px">%(code)s</div>
  </div>
  <p style="margin:0 0 20px">A friend gets <b>%(credit)s off</b> their first clean.
  You get <b>%(credit)s off</b> your next one when they book. No limit, nothing expires.</p>
  <p style="margin:22px 0"><a href="%(site)s/book"
   style="background:#0c4a5c;color:#f7f3ec;text-decoration:none;font-weight:700;
   padding:12px 20px;border-radius:999px;display:inline-block">Where they book</a></p>
  <p style="color:#7d949a;font-size:.84rem;border-top:1px solid #e2dccf;padding-top:14px">
  %(brand)s &middot; <a href="%(site)s" style="color:#0c4a5c">%(site_short)s</a></p>
</div></body></html>""" % {
        "name": name, "code": code, "credit": credit, "site": site, "brand": brand,
        "site_short": site.replace("https://", ""),
    }
    return ("%s off for a friend, %s for you" % (credit, credit), text, html)


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
