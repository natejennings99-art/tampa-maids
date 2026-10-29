#!/usr/bin/env python3
"""Shared loader for the queued outreach emails (stdlib only).

Reads marketing/command-center/outreach.json + state.json and returns the
emails that are actually sendable today: kind starts with "Email", not yet
sent, not expired, has a real address. Each item gets a subject (from its
"Subject:" first line) and a body with the CAN-SPAM footer filled in from
state.addr. Used by send_outreach.py (SMTP) and build_send_emails.py (page).
"""
import datetime
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CC = os.path.join(ROOT, "marketing", "command-center")
OUTREACH = os.path.join(CC, "outreach.json")
STATE = os.path.join(CC, "state.json")
SENT_LOG = os.path.join(CC, "dm-sent-log.txt")

GRACE_DAYS = 7
# Same company inbox server, same day: corporate filters flag a burst of
# near-identical mail, and colleagues compare notes. Two a day per company
# domain; the rest roll to tomorrow's page. Webmail domains are exempt.
DOMAIN_CAP = 2
FREE_MAIL = {"gmail.com", "aol.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "me.com", "msn.com", "live.com", "comcast.net", "verizon.net"}  # a news-hook email is still fine a week after its freshness date

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
SIGNOFF_ONELINER = re.compile(r"^Nate Jennings · (Tampa Maids Cleaning|Jennings Media) · \(571\) 317-3211 ·.*$", re.M)

# One inbox, two pitches: send the Jennings Media version first (bigger ticket,
# no insurance dependency) and hold the Tampa Maids twin for a week.
HOLD_TWINS = {
    "o-em-tm-ven-tampa-theatre-centennial-resto": "o-em-jm-ven-tampa-theatre-centennial-resto",
    "o-em-tm-ven-330-commerce-club": "o-em-jm-ven-330-commerce-club",
    "o-em-tm-ven-evergrove-estate": "o-em-jm-ven-evergrove-estate",
    "o-em-tm-sterling-noble-tavern": "o-em-jm-sterling-noble-tavern",
}


def load():
    items = json.load(open(OUTREACH, encoding="utf-8"))
    state = json.load(open(STATE, encoding="utf-8"))
    return items, state


def logged_addresses():
    """Addresses already written to dm-sent-log.txt (any campaign)."""
    out = set()
    if os.path.exists(SENT_LOG):
        for line in open(SENT_LOG, encoding="utf-8", errors="ignore"):
            for m in EMAIL_RE.findall(line):
                out.add(m.lower())
    return out


def split_subject(text):
    m = re.match(r"\s*Subject:\s*(.+?)\n", text, re.I)
    if not m:
        return None, text.strip()
    return m.group(1).strip(), text[m.end():].strip()


def finish_body(body, addr):
    body = body.replace("[MAILING ADDRESS]", addr)
    lines = body.split("\n")
    # Drop the one-line sign-off when a full signature block is already there.
    if sum(1 for l in lines if "(571) 317-3211" in l) > 1:
        body = SIGNOFF_ONELINER.sub("", body).rstrip()
    if addr not in body:
        body = body.rstrip() + "\n" + addr
    if "no thanks" not in body.lower():
        body += "\nReply \"no thanks\" and I won't email again."
    return body.strip() + "\n"


def sendable(today=None):
    """Returns (ready, skipped). ready = list of dicts with id, biz, to, name,
    subject, body, exp, kind. skipped = list of (id, reason)."""
    today = today or datetime.date.today().isoformat()
    items, state = load()
    sent = state.get("sent", {})
    addr = (state.get("addr") or "").strip()
    seen_log = logged_addresses()
    ready, skipped = [], []
    for it in items:
        if not it.get("kind", "").startswith("Email"):
            continue
        iid = it["id"]
        if iid in sent:
            skipped.append((iid, "already sent %s" % sent[iid])); continue
        if it.get("exp"):
            cutoff = (datetime.date.fromisoformat(today) - datetime.timedelta(days=GRACE_DAYS)).isoformat()
            if it["exp"] < cutoff:
                skipped.append((iid, "expired %s" % it["exp"])); continue
        m = EMAIL_RE.search(it.get("to", ""))
        if not m:
            skipped.append((iid, "no email address in 'to'")); continue
        subject, body = split_subject(it.get("text", ""))
        if not subject or not body:
            skipped.append((iid, "no subject/body (superseded draft)")); continue
        if not addr:
            skipped.append((iid, "no mailing address in state.addr (CAN-SPAM)")); continue
        if iid in HOLD_TWINS:
            skipped.append((iid, "same inbox as %s; send a week later" % HOLD_TWINS[iid])); continue
        to = m.group(0)
        if to.lower() in seen_log:
            skipped.append((iid, "address already in dm-sent-log.txt")); continue
        name = it["to"].split("<")[0].split("·")[0].strip(" ,:") or to
        ready.append({"id": iid, "biz": it["biz"], "to": to, "name": name,
                      "subject": subject, "body": finish_body(body, addr),
                      "exp": it.get("exp"), "kind": it["kind"]})
    # Money order: Tampa Maids B2B first (recurring), then JM, soonest expiry first.
    ready.sort(key=lambda r: (r["biz"] != "tm", r["exp"] or "9999"))
    capped, per_dom = [], {}
    for r in ready:
        dom = r["to"].split("@")[1].lower()
        if dom not in FREE_MAIL:
            per_dom[dom] = per_dom.get(dom, 0) + 1
            if per_dom[dom] > DOMAIN_CAP:
                skipped.append((r["id"], "domain cap: %d per day to %s, rolls to tomorrow" % (DOMAIN_CAP, dom)))
                continue
        capped.append(r)
    return capped, skipped


if __name__ == "__main__":
    r, s = sendable()
    print("READY %d" % len(r))
    for x in r:
        print("  %-3s %-50s %-40s %s" % (x["biz"], x["id"], x["to"], x["subject"][:50]))
    print("SKIPPED %d" % len(s))
    for iid, why in s:
        print("  %-50s %s" % (iid, why))
