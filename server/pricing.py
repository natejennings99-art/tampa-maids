"""Quote engine.

Implements the pricing rules from Section 5 of the business plan:
  * Residential is a tier x frequency lookup, not an hourly rate.
  * First visits are priced as a deep clean (+35%).
  * Bi-weekly is the anchor plan; the intro offer is 15% off the first three
    cleans with a bi-weekly commitment.
  * Flat-rate lines (move-out, STR turnover, post-construction) interpolate
    across their published range by square footage.
  * Commercial is per-square-foot per-visit, with a monthly estimate.
  * Florida exempts residential dwelling cleaning; commercial is taxable.

All money is in integer CENTS. Never use floats for currency totals.
"""


def _round_cents(x):
    return int(round(x / 100.0)) * 100  # round to the nearest dollar


def _interp(sqft, lo_sqft, hi_sqft, lo_price, hi_price):
    if sqft is None:
        return (lo_price + hi_price) // 2
    if sqft <= lo_sqft:
        return lo_price
    if sqft >= hi_sqft:
        return hi_price
    frac = (sqft - lo_sqft) / float(hi_sqft - lo_sqft)
    return _round_cents(lo_price + frac * (hi_price - lo_price))


def find_tier(cfg, tier_id=None, sqft=None):
    tiers = cfg["home_tiers"]
    if tier_id:
        for t in tiers:
            if t["id"] == tier_id:
                return t
    if sqft is not None:
        for t in tiers:
            if t["sqft_max"] is None or sqft <= t["sqft_max"]:
                return t
    return tiers[1]  # sensible default: 2 BR / 2 BA


def quote(cfg, req):
    """req: dict with service, tier_id/sqft, frequency, addons[], city,
    is_first_clean, visits_per_week (commercial), commercial_type."""
    service_id = req.get("service") or "residential"
    service = next((s for s in cfg["services"] if s["id"] == service_id), None)
    if service is None:
        return {"error": "Unknown service: %s" % service_id}

    freq = req.get("frequency") or "once"
    sqft = req.get("sqft")
    try:
        sqft = int(sqft) if sqft not in (None, "") else None
    except (TypeError, ValueError):
        sqft = None

    lines = []
    custom = False
    kind = service["kind"]
    P = cfg["pricing"]

    # ---------- base price ----------
    if kind == "residential":
        tier = find_tier(cfg, req.get("tier_id"), sqft)
        if tier.get("custom_quote"):
            return {
                "custom_quote": True,
                "service": service["name"],
                "tier": tier["name"],
                "message": "Homes over 3,000 sq ft are quoted individually so we "
                           "can scope the job properly. Send us the details and "
                           "we'll come back within one business day.",
            }
        if freq not in tier["prices"]:
            freq = "biweekly"
        base = tier["prices"][freq]
        freq_name = next((f["name"] for f in cfg["frequencies"] if f["id"] == freq), freq)
        lines.append({
            "label": "%s — %s" % (tier["name"], freq_name),
            "detail": tier["detail"],
            "amount": base,
        })

    elif kind == "flat":
        base = _interp(sqft, 900, 3000, service["price_min"], service["price_max"])
        if service_id == "str":
            base = _interp(sqft, 700, 2000, service["price_min"], service["price_max"])
        elif service_id == "construction":
            base = _interp(sqft, 1000, 4000, service["price_min"], service["price_max"])
        lines.append({
            "label": service["name"],
            "detail": ("%s sq ft, flat rate" % f"{sqft:,}") if sqft else "Flat rate estimate",
            "amount": base,
        })

    elif kind == "commercial":
        ctype = req.get("commercial_type") or "office"
        rate = next((r for r in service["rates"] if r["id"] == ctype), service["rates"][0])
        if "flat_min" in rate:
            base = _interp(sqft, 900, 4000, rate["flat_min"], rate["flat_max"])
            detail = "Flat per visit"
        else:
            if not sqft:
                return {
                    "custom_quote": True,
                    "service": service["name"],
                    "message": "Tell us your square footage and cleaning frequency "
                               "and we'll price the contract on a walkthrough.",
                }
            mid = (rate["per_sqft_min"] + rate["per_sqft_max"]) / 2.0
            base = _round_cents(sqft * mid)
            detail = "%s sq ft x $%.2f/sq ft" % (f"{sqft:,}", mid / 100.0)
        lines.append({"label": "%s — per visit" % rate["name"], "detail": detail, "amount": base})
    else:
        return {"error": "Unpriceable service kind"}

    # ---------- first-visit deep clean premium ----------
    first = bool(req.get("is_first_clean", True))
    if kind == "residential" and first and freq != "once":
        premium = _round_cents(base * P["first_clean_premium"])
        lines.append({
            "label": "First visit — deep clean",
            "detail": "+%d%% one time, to bring the home to a maintainable baseline"
                      % round(P["first_clean_premium"] * 100),
            "amount": premium,
        })
    else:
        premium = 0

    # ---------- add-ons ----------
    chosen = req.get("addons") or []
    addon_total = 0
    for a in cfg["addons"]:
        if a["id"] in chosen and service_id in a["applies"]:
            addon_total += a["price"]
            lines.append({"label": a["name"], "detail": "Add-on", "amount": a["price"]})

    subtotal = base + premium + addon_total

    # ---------- intro offer ----------
    discount = 0
    intro = P.get("intro_offer") or {}
    if kind == "residential" and first and freq == intro.get("requires"):
        discount = _round_cents(subtotal * intro["percent"])
        lines.append({
            "label": intro["label"],
            "detail": "Applied to your first three visits",
            "amount": -discount,
        })

    # ---------- drive-time surcharge ----------
    # `cities` may be a dict of {city: cents} (different markets cost different
    # drive time -- Sarasota is far further than Brandon) or, in older configs,
    # a plain list that all share `amount`/`default`.
    surcharge = 0
    sc = cfg.get("surcharge_zones") or {}
    city = (req.get("city") or "").strip().lower()
    if city:
        zones = sc.get("cities") or {}
        fallback = sc.get("default", sc.get("amount", 0))
        if isinstance(zones, dict):
            lookup = {k.lower(): v for k, v in zones.items()}
            surcharge = lookup.get(city, 0)
        elif city in [c.lower() for c in zones]:
            surcharge = fallback
    if surcharge:
        lines.append({
            "label": "Drive-time surcharge",
            "detail": req.get("city"),
            "amount": surcharge,
        })

    taxable = subtotal - discount + surcharge

    # ---------- tax ----------
    rate = P["commercial_tax_percent"] if kind == "commercial" else P["residential_tax_percent"]
    tax = int(round(taxable * rate / 100.0))
    total = taxable + tax

    out = {
        "custom_quote": False,
        "service": service["name"],
        "service_id": service_id,
        "kind": kind,
        "frequency": freq,
        "lines": lines,
        "subtotal": subtotal,
        "discount": discount,
        "surcharge": surcharge,
        "tax": tax,
        "tax_rate": rate,
        "tax_note": None if rate == 0 else cfg["pricing"]["tax_note"],
        "total": total,
        "is_first_clean": first,
    }

    # what the customer pays on every visit after the first
    if kind == "residential" and freq != "once":
        recurring = base + addon_total + surcharge
        out["recurring_total"] = recurring + int(round(recurring * rate / 100.0))
        out["recurring_label"] = next(
            (f["name"] for f in cfg["frequencies"] if f["id"] == freq), freq)

    if kind == "commercial":
        vpw = float(req.get("visits_per_week") or 1)
        out["visits_per_week"] = vpw
        out["monthly_estimate"] = int(round(total * vpw * 52 / 12.0))

    return out


def money(cents):
    return "${:,.2f}".format(cents / 100.0)
