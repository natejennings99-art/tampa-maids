"""/work-with-us: the recruiting page the site never had.

Capacity is the binding constraint on this business -- 51 cleaners vetted, none
signed, and the delivery team is one person. Yet 45 pages sold to customers and
not one recruited the people who would do the work. Recruiting was entirely
manual outreach.

Pay figures come from economics.contractor_share so they cannot drift from the
contractor agreement, and the requirements are stated plainly rather than
buried: this is 1099 work, the contractor carries their own insurance, supplies
and transport, and there are no guaranteed hours. A cleaner who finds that out
after applying is a cleaner who quits in week two.

Called from build_markets.py.
"""
import json

from home_v2 import E, faq_items, final_cta, money
from inner_v2 import call_btn, page_hero

URL_PATH = "/work-with-us"


def _pay(cfg, tier_id, freq="biweekly"):
    t = next(x for x in cfg["home_tiers"] if x["id"] == tier_id)
    return round(t["prices"][freq] * cfg["economics"]["contractor_share"])


def body_for(cfg, origin):
    share = cfg["economics"]["contractor_share"]
    svc = {s["id"]: s for s in cfg["services"]}
    p2, p3, p4 = (_pay(cfg, t) for t in ("t2", "t3", "t4"))
    mv_lo = round(svc["move"]["price_min"] * share)
    mv_hi = round(svc["move"]["price_max"] * share)
    pc_hi = round(svc["construction"]["price_max"] * share)

    hero = page_hero(
        "Work with us",
        "Cleaning work in Tampa, paid per job.",
        "Half the price of every job you clean, told to you before you accept it. "
        "No hourly rate, no being sent somewhere for less than it is worth.",
        ctas=['<a class="btn btn-primary" href="#apply">Apply</a>', call_btn(cfg)],
        proof=["%d%% of the job price" % round(share * 100),
               "You choose which jobs", "Paid weekly"])

    pay = f'''
<section class="h-sec"><div class="wrap narrow">
  <div class="rv"><h2>What the work pays</h2>
  <p class="lede">You get <strong>{int(round(share * 100))}% of what the customer pays</strong>,
  and you see that number before you accept the job. Not an hourly rate that stays
  the same whether a house takes two hours or five.</p></div>
  <div class="p-table-wrap rv"><table class="p-table">
    <thead><tr><th>Job</th><th>You get</th></tr></thead>
    <tbody>
      <tr><td><strong>2 bed, every two weeks</strong><span>About 2.5&ndash;3 hours</span></td>
        <td class="amt">{money(p2)}</td></tr>
      <tr><td><strong>3 bed, every two weeks</strong><span>About 4&ndash;5 hours</span></td>
        <td class="amt">{money(p3)}</td></tr>
      <tr><td><strong>4 bed, every two weeks</strong></td><td class="amt">{money(p4)}</td></tr>
      <tr><td><strong>Move-out clean</strong><span>Half to full day</span></td>
        <td class="amt">{money(mv_lo)}&ndash;{money(mv_hi)}</td></tr>
      <tr><td><strong>Post-construction</strong><span>The biggest jobs we take</span></td>
        <td class="amt">up to {money(pc_hi)}</td></tr>
    </tbody></table></div>
  <p class="h-note rv" style="text-align:left">Paid weekly, every Friday, for the
  jobs you finished the week before.</p>
</div></section>'''

    honest = f'''
<section class="h-sec alt"><div class="wrap narrow rv">
  <h2>What this is, in plain terms</h2>
  <p class="lede">This is <strong>1099 independent contractor work, not a job</strong>.
  That cuts both ways and you should know which parts cut which way before you
  apply.</p>
  <h3>What you get</h3>
  <p>You pick the jobs you want. Nobody schedules you against your will. You are
  paid per job at a rate you agreed in advance, and a job that takes you less time
  pays the same. Tips are yours.</p>
  <h3>What you carry</h3>
  <p>Your own transport, your own supplies and equipment, and your own general
  liability insurance. You handle your own taxes &mdash; nothing is withheld. There
  are no guaranteed hours, no holiday pay and no benefits.</p>
  <p>If you want fixed hours and a payslip, this is honestly the wrong arrangement
  and we would rather tell you now than in week two.</p>
</div></section>'''

    expect = '''
<section class="h-sec"><div class="wrap">
  <div class="rv"><h2>What we expect</h2></div>
  <div class="h-grid-4 h-promises">
    <div class="rv"><h3>Turn up when you said</h3><p>The single thing that loses
      customers. If something goes wrong, tell us early rather than quietly.</p></div>
    <div class="rv"><h3>Work to the checklist</h3><p>Every job has a written list.
      It is how "clean" stops being a matter of opinion, and it protects you as
      much as the customer.</p></div>
    <div class="rv"><h3>Photos at the end</h3><p>Before and after, uploaded when
      you finish. It is the evidence the work was done properly.</p></div>
    <div class="rv"><h3>Say if you cannot</h3><p>Nobody is penalised for turning a
      job down. People are dropped for accepting and not appearing.</p></div>
  </div>
</div></section>'''

    faqs = [
      {"q": "How much work is there?",
       "a": "We are a new company and honest about it: there is not a full week of work "
            "waiting for you today. It suits someone building up their own client base or "
            "filling gaps around existing work, and it grows as we do."},
      {"q": "Do I need my own insurance?",
       "a": "Yes, general liability. It typically runs $30-60 a month for a solo cleaner. "
            "We cannot send you to a customer's home without it."},
      {"q": "Do I need my own supplies?",
       "a": "Yes - supplies, equipment and transport are yours. That is part of why the "
            "split is %d%% rather than an hourly wage." % int(round(share * 100))},
      {"q": "When am I paid?",
       "a": "Weekly, every Friday, covering the jobs you completed the previous Monday to "
            "Sunday, after the checklist is signed off."},
      {"q": "Do I have to take every job offered?",
       "a": "No. Jobs are offered and you accept or decline. What matters is that once you "
            "accept, you turn up."},
    ]
    faq_sec = '''
<section class="h-sec alt"><div class="wrap narrow">
  <div class="rv"><h2>Questions</h2></div>
  <div class="p-faq rv">%s</div>
</div></section>''' % faq_items(faqs)

    apply = f'''
<section class="h-sec" id="apply"><div class="wrap narrow rv">
  <h2>Apply</h2>
  <p class="lede">Tell us where you work, how much experience you have and when you
  are free. We reply to everyone.</p>
  <form id="applyForm" class="p-form" novalidate>
    <div class="field"><label for="a-name">Your name *</label>
      <input id="a-name" type="text" autocomplete="name" required></div>
    <div class="field-row">
      <div class="field"><label for="a-phone">Mobile *</label>
        <input id="a-phone" type="tel" autocomplete="tel" required></div>
      <div class="field"><label for="a-email">Email *</label>
        <input id="a-email" type="email" autocomplete="email" required></div>
    </div>
    <div class="field"><label for="a-area">Which areas can you work?</label>
      <input id="a-area" type="text" placeholder="e.g. South Tampa, Brandon, Riverview"></div>
    <div class="field"><label for="a-exp">Experience, insurance and availability</label>
      <textarea id="a-exp" placeholder="How long you have been cleaning, whether you
        already carry liability insurance, and which days you are free."></textarea></div>
    <div class="nav-row"><button type="submit" class="btn btn-primary btn-lg"
      id="applyBtn">Send application</button></div>
    <p class="hint" id="applyMsg"></p>
  </form>
  <p class="h-note" style="text-align:left">&iquest;Hablas espa&ntilde;ol?
    <a href="/trabaja-con-nosotros">Lee esta p&aacute;gina en espa&ntilde;ol</a>.</p>
</div></section>'''

    cta = final_cta(cfg, "Questions before you apply?",
                    "Call and ask. We would rather answer them now than have you "
                    "find out later.")

    body = hero + pay + honest + expect + faq_sec + apply + cta

    schema = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "FAQPage", "@id": origin + URL_PATH + "#faq",
             "mainEntity": [{"@type": "Question", "name": f["q"],
                             "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                            for f in faqs]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": origin + "/"},
                {"@type": "ListItem", "position": 2, "name": "Work with us",
                 "item": origin + URL_PATH}]},
        ]}, separators=(",", ":"))

    title = "Cleaning Jobs in Tampa | Work With Tampa Maids"
    desc = ("Cleaning work in Tampa paid per job, not per hour: %s of the job price, "
            "you choose the jobs, paid weekly. 1099 contract work."
            % ("%d%%" % int(round(share * 100))))
    return body, schema, desc, title


def build_careers_page(cfg, page, origin):
    body, schema, desc, title = body_for(cfg, origin)
    assert len(desc) <= 160, len(desc)
    assert len(title) <= 60, len(title)
    page("work-with-us.html", title, E(desc), body,
         head=('<script type="application/ld+json">%s</script>\n'
               '<link rel="alternate" hreflang="en" href="%s%s">\n'
               '<link rel="alternate" hreflang="es" href="%s/trabaja-con-nosotros">'
               % (schema, origin, URL_PATH, origin)),
         scripts='<script src="/js/careers.js"></script>', photo="hero")
    return [URL_PATH]
