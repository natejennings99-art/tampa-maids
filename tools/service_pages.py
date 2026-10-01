"""Greater-Tampa landing page for each service: /services/<service>-tampa.

One page per service in business.json, aimed at searches like "deep cleaning Tampa".
Everything (scope, prices, FAQs, areas) comes from business.json; the layout reuses the
v2 helpers so the pages match the rest of the site. Called from build_markets.py.
"""
import json

from home_v2 import (E, PHOTOS, SERVICE_PAGES, faq_items, final_cta, guarantee_list, icon,
                     money, service_from, service_url, slug, svc_cards)
from inner_v2 import book_btn, call_btn, page_hero, price_matrix, rates_table

# Search-friendly label per service (the page's keyword) and a unique Tampa intro.
LABELS = {
    "residential": "House Cleaning",
    "deep": "Deep Cleaning",
    "move": "Move-Out Cleaning",
    "str": "Airbnb Cleaning",
    "commercial": "Office Cleaning",
    "construction": "Post-Construction Cleaning",
}
INTROS = {
    "residential": "Weekly, every-two-weeks or monthly house cleaning for homes across greater Tampa, from "
                   "South Tampa and Hyde Park bungalows to Westchase, Carrollwood and New Tampa family homes. "
                   "You see a flat price before you book, and every visit follows the same written checklist.",
    "deep": "A top-to-bottom reset for Tampa homes: baseboards and door frames, inside the oven and fridge, "
            "vents and ceiling fans, grout and hard-water buildup. It's how every recurring plan starts, and a "
            "smart seasonal refresh anywhere from Temple Terrace to Apollo Beach.",
    "move": "Flat-rate move-in and move-out cleaning built to pass a landlord or property-manager walkthrough, "
            "for apartments and homes from Hyde Park and Town 'n' Country to Brandon, Riverview and Wesley Chapel.",
    "str": "Same-day turnovers for Airbnb and VRBO hosts around Tampa Bay: a full linen strip and re-make, "
           "restocks to your par levels, and photos of every room before we leave. Downtown and South Tampa "
           "rentals, plus St. Pete Beach and Clearwater Beach.",
    "commercial": "After-hours cleaning for small offices, medical and dental suites, and boutique retail in "
                  "Tampa, from Westshore and downtown to Carrollwood and Brandon. Priced per square foot, "
                  "contracted and predictable.",
    "construction": "Multi-pass fine-dust removal that turns a finished Tampa remodel or new build back into a "
                    "livable space, for general contractors, remodelers and homeowners across Hillsborough County.",
}
DESCS = {
    "residential": "Weekly, biweekly or monthly house cleaning in Tampa by personally vetted independent pros. "
                   "Flat prices from {low}, a written checklist and a free re-clean.",
    "deep": "Deep cleaning in Tampa: baseboards, inside the oven and fridge, grout and vents. Flat one-time "
            "prices from {low}, booked online in a minute.",
    "move": "Move-in and move-out cleaning in Tampa built to pass a landlord walkthrough. Flat rates {range}, "
            "set before we start.",
    "str": "Airbnb and VRBO turnover cleaning around Tampa Bay: linen resets, restocks and photo checks inside "
           "your check-in window. {range} per turn.",
    "commercial": "After-hours office, medical and dental suite cleaning in Tampa. Contracted, per-square-foot "
                  "pricing and a walkthrough before we quote.",
    "construction": "Post-construction cleaning in Tampa for remodels and new builds. Multi-pass dust removal, "
                    "flat rates {range} after a walkthrough.",
}
# FAQs picked by a phrase in the question, so reordering business.json doesn't break them.
FAQ_PICKS = {
    "residential": ["How is my price", "same cleaners", "be home", "cancellation", "own supplies"],
    "deep": ["first clean more expensive", "How is my price", "own supplies", "isn't right"],
    "move": ["How is my price", "isn't right", "How do I pay", "be home"],
    "str": ["vacation rental", "cancellation", "isn't right", "own supplies"],
    "commercial": ["sales tax", "How do I pay", "insured", "isn't right"],
    "construction": ["How is my price", "insured", "How do I pay", "isn't right"],
}


def _title(label, name):
    t = "%s in Tampa, FL | %s" % (label, name)
    return t if len(t) <= 60 else "%s in Tampa | Tampa Maids" % label


def _offer(cfg, s):
    tiers = [t for t in cfg["home_tiers"] if t.get("prices")]
    if s["id"] == "deep":
        once = [t["prices"]["once"] for t in tiers if "once" in t["prices"]]
        return min(once), max(once)
    if s["kind"] == "residential":
        allp = [p for t in tiers for p in t["prices"].values()]
        return min(allp), max(allp)
    if s.get("price_min"):
        return s["price_min"], s["price_max"]
    return None


def service_page_body(cfg, s, origin):
    sid, label = s["id"], LABELS.get(s["id"], s["name"])
    tampa = cfg["markets"][0]
    path = service_url(sid)
    crumbs = ('<nav class="p-crumbs" aria-label="Breadcrumb"><div class="wrap"><a href="/">Home</a> / '
              '<a href="/services">Services</a> / <span>%s in Tampa</span></div></nav>' % E(label))
    hero = page_hero(
        "Greater Tampa", "%s in <em>Tampa.</em>" % E(label), E(INTROS.get(sid, s["blurb"])),
        photo=sid if sid in PHOTOS else "residential", alt="%s in Tampa" % label,
        ctas=[book_btn(cfg, "See my price", "/book?service=%s" % sid), call_btn(cfg)],
        proof=["Flat upfront pricing", "Personally vetted independent pros", "Free 24-hour re-clean"])

    incl = "".join("<li>%s<span>%s</span></li>" % (icon("check"), E(x)) for x in s["includes"])
    price_line = service_from(cfg, s)
    glance = [("Price", price_line), ("Time", E(s.get("duration_note", ""))),
              ("Best for", E(s.get("audience") or "Homeowners and renters across greater Tampa")),
              ("Area", "Greater Tampa")]
    glance_html = "".join("<div><span>%s</span><strong>%s</strong></div>" % kv for kv in glance)
    included = f'''
<section class="h-sec">
  <div class="wrap p-story">
    <div class="rv p-prose">
      <p class="h-kicker">What's included</p>
      <h2>Every {E(label.lower())} covers this.</h2>
      <ul class="p-checks">{incl}</ul>
    </div>
    <aside class="p-glance rv"><h3>At a glance</h3>{glance_html}
      <p class="p-glance-note">{icon("refresh")}Tell us within 24 hours if anything's missed and we re-clean it free.</p>
    </aside>
  </div>
</section>'''

    if s["kind"] == "residential":
        lead = ("Deep cleans are booked at our one-time rates, and every recurring plan starts with one."
                if sid == "deep" else "Tap any price to book it. Every 2 weeks is the most popular plan.")
        pricing = f'''
<section class="h-sec sand">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Pricing</p><h2>Flat prices for Tampa homes.</h2><p>{lead}</p></div>
    {price_matrix(cfg)}
    <p class="h-note" style="text-align:left">{E(cfg["booking"]["first_clean_note"])}</p>
  </div>
</section>'''
    elif s.get("rates"):
        pricing = f'''
<section class="h-sec sand">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Pricing</p><h2>Contracted and predictable.</h2>
      <p>We walk the space first and quote in writing.</p></div>
    {rates_table(s["rates"])}
    <p class="h-note" style="text-align:left">{E(s.get("contract_note", ""))}</p>
    <div class="h-cta"><a class="btn btn-primary" href="/contact">Request a walkthrough</a></div>
  </div>
</section>'''
    else:
        pricing = f'''
<section class="h-sec sand">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Pricing</p><h2>{money(s["price_min"])}&ndash;{money(s["price_max"])}, flat.</h2>
      <p>Set by size and condition, in writing, before we start. Never changed at the door.</p></div>
    <div class="h-cta"><a class="btn btn-primary" href="/book?service={sid}">Get my exact price</a>
      <a class="btn btn-ghost" href="/contact">Ask a question</a></div>
  </div>
</section>'''

    chips = "".join('<span>%s%s</span>' % (icon("pin"), E(a)) for a in tampa["areas"])
    others = [m for m in cfg["markets"] if m is not tampa]
    areas = f'''
<section class="h-sec">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Where we clean</p><h2>{E(label)} across greater Tampa.</h2>
      <p>Based in Tampa. See <a href="/cleaning/tampa">house cleaning in Tampa</a>, or our
      {", ".join('<a href="/cleaning/%s">%s</a>' % (slug(m["name"]), E(m["name"])) for m in others)} pages.</p></div>
    <div class="p-chips rv">{chips}</div>
  </div>
</section>'''

    promise = f'''
<section class="h-sec sand">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Why Tampa Maids</p><h2>Written standards, flat prices, a real guarantee.</h2></div>
    <div class="h-list p-promise">{guarantee_list(cfg)}</div>
  </div>
</section>'''

    picks = []
    for phrase in FAQ_PICKS.get(sid, []):
        f = next((f for f in cfg.get("faq", []) if phrase.lower() in f["q"].lower()), None)
        if f and f not in picks:
            picks.append(f)
    faq = f'''
<section class="h-sec">
  <div class="wrap">
    <div class="h-head center rv"><p class="h-kicker">Questions</p><h2>{E(label)} questions.</h2></div>
    <div class="h-faq">{faq_items(picks)}</div>
    <p class="h-note"><a href="/faq">All frequently asked questions &rarr;</a></p>
  </div>
</section>''' if picks else ""

    more = f'''
<section class="h-sec sand">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">More services</p><h2>Other cleaning in Tampa.</h2></div>
    <div class="h-svc">{svc_cards(cfg, only=[x["id"] for x in cfg["services"] if x["id"] != sid])}</div>
  </div>
</section>'''

    body = (crumbs + hero + included + pricing + areas + promise + faq + more
            + final_cta(cfg, "Book %s in Tampa." % E(label.lower()),
                        "Flat written price in about a minute. No card, no obligation."))

    offer = _offer(cfg, s)
    service_ld = {
        "@type": "Service", "name": "%s in Tampa, FL" % label, "serviceType": s["name"],
        "description": s["blurb"], "url": origin + path,
        "provider": {"@type": "HouseCleaningService", "name": cfg["name"], "url": origin + "/",
                     "telephone": cfg["phone"]},
        "areaServed": [{"@type": "City", "name": a} for a in tampa["areas"]],
    }
    if offer:
        service_ld["offers"] = {"@type": "AggregateOffer", "priceCurrency": "USD",
                                "lowPrice": round(offer[0] / 100), "highPrice": round(offer[1] / 100)}
    crumbs_ld = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": origin + "/"},
        {"@type": "ListItem", "position": 2, "name": "Services", "item": origin + "/services"},
        {"@type": "ListItem", "position": 3, "name": "%s in Tampa" % label, "item": origin + path}]}
    schema = json.dumps({"@context": "https://schema.org", "@graph": [service_ld, crumbs_ld]}, indent=2)

    low = money(offer[0]) if offer else ""
    rng = ("%s&ndash;%s" % (money(offer[0]), money(offer[1]))) if offer else ""
    desc = DESCS.get(sid, s["blurb"]).format(low=low, range=rng.replace("&ndash;", "–"))
    return body, schema, desc, _title(label, cfg["name"])


def build_service_pages(cfg, page, origin):
    """Write web/services/<slug>.html for every service; returns the URL paths written."""
    paths = []
    for s in cfg["services"]:
        if s["id"] not in SERVICE_PAGES:
            continue
        body, schema, desc, title = service_page_body(cfg, s, origin)
        assert len(desc) <= 160, (s["id"], len(desc))
        slug = SERVICE_PAGES[s["id"]]
        page("services/%s.html" % slug, title, E(desc), body,
             head='<script type="application/ld+json">%s</script>' % schema,
             scripts='<script src="/js/home.js"></script>', photo=s["id"] if s["id"] in PHOTOS else "hero")
        paths.append(service_url(s["id"]))
    return paths
