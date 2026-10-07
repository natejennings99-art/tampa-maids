#!/usr/bin/env python3
"""Send review requests for finished jobs that never got one.

A review is asked for when a crew marks a job completed, but only if the mail
provider is configured at that moment -- we do not stamp a job as asked when
nothing actually went out. Mail is not configured yet, so every job completed
before POSTMARK_TOKEN is set would otherwise lose its review request forever.
Reviews are the gate on the Google local pack, so losing one matters.

Run this once after configuring mail, and any time a send outage is over.

    python3 -m server.review_catchup            # dry run, shows who would get one
    python3 -m server.review_catchup --send     # actually send
    python3 -m server.review_catchup --send --max 20

Dry run is the default on purpose: this writes to real customers.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import db, notify  # noqa: E402

CFG = json.load(open(os.path.join(os.path.dirname(HERE), "business.json"), encoding="utf-8"))

SQL = """
SELECT b.id, b.ref, b.date, b.completed_at, c.name, c.email
  FROM bookings b JOIN customers c ON c.id = b.customer_id
 WHERE b.status = 'completed'
   AND (b.review_requested_at IS NULL OR b.review_requested_at = '')
   AND c.email IS NOT NULL AND c.email <> ''
 ORDER BY b.completed_at
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--send", action="store_true",
                    help="actually send; without it nothing leaves the machine")
    ap.add_argument("--max", type=int, default=50,
                    help="stop after this many (default 50)")
    a = ap.parse_args(argv)

    con = db.connect()
    rows = list(con.execute(SQL))
    if not rows:
        print("Nothing to do: every completed job has already been asked.")
        return 0

    print("%d completed job(s) never asked for a review." % len(rows))
    if a.send and not notify.configured():
        print("\nMail is not configured (no POSTMARK_TOKEN or SMTP_HOST), so --send "
              "would do nothing.\nSet it first, then run this again.")
        return 1

    sent = failed = 0
    for i, r in enumerate(rows):
        if i >= a.max:
            print("\nStopped at --max %d; %d left." % (a.max, len(rows) - a.max))
            break
        who = "%s <%s>" % (r["name"] or "?", r["email"])
        if not a.send:
            print("  would ask  %-10s %-12s %s" % (r["ref"], r["date"], who))
            continue
        try:
            subj, text, html = notify.review_request(
                CFG, {"ref": r["ref"]}, {"name": r["name"], "email": r["email"]})
            if notify.send(r["email"], subj, text, html):
                con.execute("UPDATE bookings SET review_requested_at=? WHERE id=?",
                            (db.now(), r["id"]))
                con.commit()
                sent += 1
                print("  asked      %-10s %s" % (r["ref"], who))
            else:
                failed += 1
                print("  FAILED     %-10s %s" % (r["ref"], who))
        except Exception as e:                               # noqa: BLE001
            failed += 1
            print("  ERROR      %-10s %s: %s" % (r["ref"], who, e))

    if not a.send:
        print("\nDry run. Re-run with --send to actually send.")
    else:
        print("\nSent %d, failed %d." % (sent, failed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
