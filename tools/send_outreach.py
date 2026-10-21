#!/usr/bin/env python3
"""Send the queued outreach emails over SMTP (stdlib only).

  python3 tools/send_outreach.py --dry-run          # writes .eml previews, sends nothing
  python3 tools/send_outreach.py --send --limit 10  # really sends, 10 at a time
  python3 tools/send_outreach.py --send --ids o-em-co-wrightdavis,o-em-co-trident

Needs the same six values as the website (ops/turn-on-email.md):
  SMTP_HOST=smtp.gmail.com SMTP_PORT=587 SMTP_USER=... SMTP_PASS=<app password>
  MAIL_FROM=<same as SMTP_USER>   (OWNER_NOTIFY optional)
Every real send is appended to marketing/command-center/dm-sent-log.txt and
recorded in state.json under sent[id] (the Command Center then hides it and
schedules the 3-day follow-up). state.json is backed up first.
"""
import argparse
import datetime
import json
import os
import shutil
import smtplib
import ssl
import sys
import time
from email.message import EmailMessage
from email.utils import formataddr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outreach_mail as om  # noqa: E402

SENDER_NAME = "Nate Jennings"


def build_message(r, mail_from):
    msg = EmailMessage()
    msg["From"] = formataddr((SENDER_NAME, mail_from))
    msg["To"] = formataddr((r["name"], r["to"])) if r["name"] != r["to"] else r["to"]
    msg["Subject"] = r["subject"]
    msg["Reply-To"] = mail_from
    msg.set_content(r["body"])
    return msg


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--send", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--ids", default="")
    ap.add_argument("--pause", type=float, default=4.0, help="seconds between sends")
    ap.add_argument("--out", default=os.path.join(os.environ.get("TMPDIR", "/tmp"), "outreach-eml"))
    a = ap.parse_args()

    ready, skipped = om.sendable()
    if a.ids:
        want = set(a.ids.split(","))
        ready = [r for r in ready if r["id"] in want]
    if a.limit:
        ready = ready[:a.limit]

    if a.dry_run:
        os.makedirs(a.out, exist_ok=True)
        for r in ready:
            path = os.path.join(a.out, r["id"] + ".eml")
            with open(path, "w", encoding="utf-8") as f:
                f.write(build_message(r, "natejennings99@gmail.com").as_string())
        print("DRY RUN: %d messages written to %s, %d skipped" % (len(ready), a.out, len(skipped)))
        for iid, why in skipped:
            print("  skip %-48s %s" % (iid, why))
        return 0

    host = os.environ.get("SMTP_HOST", "").strip()
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "").strip()
    pw = os.environ.get("SMTP_PASS", "")
    mail_from = os.environ.get("MAIL_FROM", "").strip()
    if not (host and user and pw and mail_from):
        print("SMTP_HOST, SMTP_USER, SMTP_PASS and MAIL_FROM must be set (see ops/turn-on-email.md)")
        return 2
    if mail_from.lower() != user.lower():
        print("MAIL_FROM must equal SMTP_USER for Gmail; refusing to send.")
        return 2
    if not ready:
        print("Nothing to send."); return 0

    shutil.copy(om.STATE, om.STATE + ".bak-send-" + datetime.date.today().strftime("%m%d"))
    state = json.load(open(om.STATE, encoding="utf-8"))
    state.setdefault("sent", {})
    today = datetime.date.today().isoformat()
    ctx = ssl.create_default_context()
    ok = fail = 0
    with smtplib.SMTP(host, port, timeout=20) as s:
        s.starttls(context=ctx)
        s.login(user, pw)
        for i, r in enumerate(ready):
            try:
                s.send_message(build_message(r, mail_from))
                ok += 1
                state["sent"][r["id"]] = today
                with open(om.SENT_LOG, "a", encoding="utf-8") as f:
                    f.write("%s | %s | %s | sent | %s\n" % (today, r["id"], r["to"], r["subject"]))
                json.dump(state, open(om.STATE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
                print("  sent  %-48s %s" % (r["id"], r["to"]))
            except Exception as e:  # noqa: BLE001
                fail += 1
                print("  FAIL  %-48s %s — %s" % (r["id"], r["to"], e))
            if i < len(ready) - 1:
                time.sleep(a.pause)
    print("done: %d sent, %d failed, %d skipped" % (ok, fail, len(skipped)))
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
