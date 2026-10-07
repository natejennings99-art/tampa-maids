#!/usr/bin/env python3
"""What the business actually earns, and how much work a living requires.

Nobody had worked this out. The prices were set from the business plan and the
contractor split from the agreement, but the two had never been put together to
answer the only question that matters: how many cleans a week does this need?

Everything is read from business.json. Where a number is an assumption rather
than a fact it says so, because a model that hides its guesses is worse than no
model.

    python3 tools/unit_economics.py
    python3 tools/unit_economics.py --profit 8000   # target a different monthly profit
"""
import argparse, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "business.json"), encoding="utf-8"))
E = CFG["economics"]


def money(cents):
    return "${:,.2f}".format(cents / 100.0)


def contribution(price_cents):
    """What a job leaves after the costs that scale with it."""
    pay = round(price_cents * E["contractor_share"])
    card = 0
    if E.get("card_payments_live"):
        cp = E["card_processing"]
        card = round(price_cents * cp["percent"]) + cp["fixed_cents"]
    return price_cents - pay - card, pay, card


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profit", type=float, default=None,
                    help="target monthly profit in dollars (default: from business.json)")
    a = ap.parse_args(argv)
    target = (int(a.profit * 100) if a.profit is not None
              else E["owner_target_monthly_profit_cents"])

    fixed = sum(E["fixed_monthly_cents"].values())

    print("=" * 66)
    print("  UNIT ECONOMICS  ".center(66, "="))
    print("=" * 66)

    print("\nPER JOB  (contractor takes %d%% of the price)" % round(E["contractor_share"] * 100))
    print("  %-26s %10s %10s %10s" % ("job", "price", "cleaner", "you keep"))
    tiers = [t for t in CFG["home_tiers"] if t.get("prices")]
    rows = []
    for t in tiers:
        for freq in ("biweekly", "monthly", "once"):
            price = t["prices"][freq]
            keep, pay, _ = contribution(price)
            rows.append((("%s %s" % (t["name"], freq)), price, pay, keep))
    for name, price, pay, keep in rows:
        print("  %-26s %10s %10s %10s" % (name, money(price), money(pay), money(keep)))

    svc = {s["id"]: s for s in CFG["services"]}
    print("\n  flat-rate work")
    for sid, label in (("move", "move-out"), ("str", "turnover"),
                       ("construction", "post-construction")):
        s = svc.get(sid) or {}
        if s.get("price_min"):
            for p, tag in ((s["price_min"], "low"), (s["price_max"], "high")):
                keep, pay, _ = contribution(p)
                print("  %-26s %10s %10s %10s" % ("%s (%s)" % (label, tag), money(p), money(pay), money(keep)))

    print("\nFIXED COSTS PER MONTH")
    for k, v in sorted(E["fixed_monthly_cents"].items(), key=lambda x: -x[1]):
        note = E["fixed_monthly_notes"].get(k, "")
        print("  %-20s %10s   %s" % (k.replace("_", " "), money(v), note))
    print("  %-20s %10s" % ("TOTAL", money(fixed)))
    if not E.get("card_payments_live"):
        print("\n  Note: card payments are not built, so no processing fees are counted.")
        print("        Adding Stripe would take %.1f%% + %s off every job."
              % (E["card_processing"]["percent"] * 100, money(E["card_processing"]["fixed_cents"])))

    # Anchor on the most common job rather than an average of everything.
    anchor = next(t for t in tiers if t["id"] == "t2")
    anchor_price = anchor["prices"]["biweekly"]
    keep, pay, _ = contribution(anchor_price)

    print("\n" + "-" * 66)
    print("BREAK-EVEN  (using a %s at %s, the most common job)"
          % (anchor["name"], money(anchor_price)))
    print("  you keep %s per job, fixed costs are %s a month" % (money(keep), money(fixed)))
    be = fixed / float(keep)
    print("  -> break-even: %.1f jobs a month. Roughly %.1f a week." % (be, be / 4.33))
    print("     Fixed costs are tiny, so the business covers itself almost immediately.")
    print("     The real question is not survival, it is how much work a living takes.")

    print("\n" + "-" * 66)
    print("WHAT A LIVING LOOKS LIKE  (target %s/month profit)" % money(target))
    need_jobs = (target + fixed) / float(keep)
    per_week = need_jobs / 4.33
    per_day = per_week / 5.0
    cleaners = per_day / E["jobs_per_cleaner_per_day"]
    revenue = need_jobs * anchor_price
    print("  jobs needed        %8.0f a month   (%.0f a week, %.1f a weekday)"
          % (need_jobs, per_week, per_day))
    print("  revenue            %10s a month" % money(revenue))
    print("  paid to cleaners   %10s a month" % money(revenue - (need_jobs * keep)))
    print("  cleaners needed    %8.1f  (at %s jobs per cleaner per day -- AN ASSUMPTION)"
          % (cleaners, E["jobs_per_cleaner_per_day"]))
    print("  recurring clients  %8.0f  if everyone is biweekly (each gives ~2.17 jobs/month)"
          % (need_jobs / 2.17))

    print("\n" + "-" * 66)
    print("WHAT THIS MEANS")
    print("  * Fixed costs are trivial. Nothing here fails from overheads.")
    print("  * At a 50%% split, every job leaves %s. Volume is the whole game." % money(keep))
    print("  * %.0f recurring biweekly clients covers the target. That is a"
          % (need_jobs / 2.17))
    print("    knowable number of customers, not an abstraction.")
    print("  * Bigger homes pay disproportionately: a 4 BR biweekly leaves %s"
          % money(contribution(tiers[3]["prices"]["biweekly"])[0]))
    print("    versus %s for a 2 BR -- same visit, same admin." % money(keep))
    best = max(((s["price_max"], l) for l, s in
                (("post-construction", svc.get("construction") or {}),
                 ("move-out", svc.get("move") or {})) if s.get("price_max")), default=None)
    if best:
        print("  * One %s at %s leaves %s -- worth %.0f standard cleans."
              % (best[1], money(best[0]), money(contribution(best[0])[0]),
                 contribution(best[0])[0] / float(keep)))
    print("\n  Assumption flagged: %s" % E["assumption_note"])
    print("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
