#!/usr/bin/env python3
"""Builds the booking wizard page.  python3 tools/build_book.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import page, NAME

HEAD = '''<style>
.book-layout{display:grid;grid-template-columns:1fr 380px;gap:40px;align-items:start}
.summary{position:sticky;top:96px}
.wizard-steps{display:flex;gap:6px;margin-bottom:32px;flex-wrap:wrap}
.wstep{flex:1;min-width:80px;padding-top:10px;border-top:3px solid var(--line);
  font-size:.78rem;font-weight:650;color:var(--ink-3);letter-spacing:.02em;transition:.2s}
.wstep.done{border-color:var(--teal-200);color:var(--teal-dark)}
.wstep.now{border-color:var(--teal);color:var(--teal-dark)}
.panel{display:none;animation:fade .25s ease}
.panel.active{display:block}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.panel h2{font-size:1.6rem;margin-bottom:.25em}
.panel .sub{color:var(--ink-2);margin-bottom:26px}
.nav-row{display:flex;gap:12px;margin-top:30px;align-items:center}
.nav-row .back{margin-right:auto}
.cal{display:grid;grid-template-columns:repeat(7,1fr);gap:5px}
.cal .dow{text-align:center;font-size:.7rem;font-weight:700;color:var(--ink-3);
  padding:6px 0;text-transform:uppercase;letter-spacing:.05em}
.cal button{aspect-ratio:1;border:1.5px solid var(--line);background:#fff;border-radius:10px;
  font:inherit;font-size:.92rem;font-weight:550;cursor:pointer;color:var(--ink);transition:.12s}
.cal button:hover:not(:disabled){border-color:var(--teal);background:var(--teal-50)}
.cal button:disabled{opacity:.3;cursor:not-allowed;background:#fafbfb}
.cal button.sel{background:var(--teal);border-color:var(--teal);color:#fff;font-weight:700}
.cal .blank{visibility:hidden}
.cal-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.cal-head button{background:none;border:1.5px solid var(--line);border-radius:9px;width:36px;
  height:36px;cursor:pointer;font-size:1.1rem;line-height:1;color:var(--ink-2)}
.cal-head button:disabled{opacity:.3;cursor:not-allowed}
.cal-head strong{font-size:1.02rem}
.slots{display:grid;grid-template-columns:repeat(auto-fill,minmax(112px,1fr));gap:9px;margin-top:18px}
.slots button{padding:.72em .6em;border:1.5px solid var(--line);background:#fff;border-radius:10px;
  font:inherit;font-weight:600;font-size:.92rem;cursor:pointer;transition:.12s}
.slots button:hover{border-color:var(--teal);background:var(--teal-50)}
.slots button.sel{background:var(--teal);border-color:var(--teal);color:#fff}
.sum-lines{margin:16px 0}
.sum-line{display:flex;justify-content:space-between;gap:12px;padding:9px 0;font-size:.91rem;
  border-bottom:1px solid var(--line);align-items:flex-start}
.sum-line:last-child{border-bottom:0}
.sum-line .lbl{color:var(--ink-2)}
.sum-line .lbl small{display:block;color:var(--ink-3);font-size:.78rem;line-height:1.35;margin-top:1px}
.sum-line .amt{font-weight:650;white-space:nowrap}
.sum-line.neg .amt{color:var(--ok)}
.sum-total{display:flex;justify-content:space-between;align-items:baseline;padding-top:14px;
  margin-top:6px;border-top:2px solid var(--ink);font-weight:700;font-size:1.05rem}
.sum-total .big{font-family:var(--display);font-size:1.9rem;font-weight:600}
.recurring-note{background:var(--ok-bg);color:var(--ok);border-radius:10px;padding:11px 13px;
  font-size:.85rem;margin-top:14px;font-weight:550}
@media(max-width:960px){
  .book-layout{grid-template-columns:1fr;gap:26px}
  .summary{position:static;order:-1}
}
</style>'''

BODY = '''
<section style="background:linear-gradient(180deg,var(--teal-50),#fff);padding:44px 0 26px">
  <div class="wrap center">
    <p class="eyebrow">Free instant quote</p>
    <h1 style="margin-bottom:.2em">Book your cleaning</h1>
    <p class="lede" style="margin-inline:auto">Real prices, calculated live. No card,
    no email required to see your number.</p>
  </div>
</section>

<section style="padding:34px 0 80px">
  <div class="wrap">
    <div class="book-layout">
      <div>
        <div class="wizard-steps" id="wsteps"></div>
        <div id="wizError"></div>

        <!-- 1. service -->
        <div class="panel active" data-step="0">
          <h2>What do you need cleaned?</h2>
          <p class="sub">Pick the closest match. You can add extras in a moment.</p>
          <div class="opts" id="svcOpts"></div>
          <div class="nav-row"><button class="btn btn-primary" data-next>Continue</button></div>
        </div>

        <!-- 2. size -->
        <div class="panel" data-step="1">
          <h2 id="sizeTitle">How big is your place?</h2>
          <p class="sub" id="sizeSub">This sets your price tier.</p>
          <div class="opts" id="tierOpts"></div>
          <div id="sqftWrap" style="display:none">
            <div class="field"><label for="sqft">Approximate square footage *</label>
              <input id="sqft" type="number" min="100" max="30000" step="50" placeholder="e.g. 1800">
              <p class="hint">A close estimate is fine &mdash; we confirm on the walkthrough.</p></div>
          </div>
          <div id="commWrap" style="display:none">
            <div class="field"><label for="commType">Type of space</label>
              <select id="commType"></select></div>
            <div class="field"><label for="visits">Cleanings per week</label>
              <select id="visits">
                <option value="1">Once a week</option>
                <option value="2">Twice a week</option>
                <option value="3">Three times a week</option>
                <option value="5">Every weeknight</option>
              </select></div>
          </div>
          <div class="nav-row"><button class="btn btn-ghost back" data-back>Back</button>
            <button class="btn btn-primary" data-next>Continue</button></div>
        </div>

        <!-- 3. frequency -->
        <div class="panel" data-step="2">
          <h2>How often should we come?</h2>
          <p class="sub">Recurring plans cost less per visit, and you keep the same crew.</p>
          <div class="opts" id="freqOpts"></div>
          <div class="alert alert-info" id="firstCleanNote" style="margin-top:18px"></div>
          <div class="nav-row"><button class="btn btn-ghost back" data-back>Back</button>
            <button class="btn btn-primary" data-next>Continue</button></div>
        </div>

        <!-- 4. add-ons -->
        <div class="panel" data-step="3">
          <h2>Anything extra?</h2>
          <p class="sub">Optional. Add now or ask the crew later &mdash; we always re-quote first.</p>
          <div class="opts cols-2" id="addonOpts"></div>
          <div class="nav-row"><button class="btn btn-ghost back" data-back>Back</button>
            <button class="btn btn-primary" data-next>Continue</button></div>
        </div>

        <!-- 5. when -->
        <div class="panel" data-step="4">
          <h2>Pick a day and time</h2>
          <p class="sub">Live availability. Grey days are full, closed or outside our window.</p>
          <div class="card">
            <div class="cal-head">
              <button type="button" id="calPrev" aria-label="Previous month">&#8249;</button>
              <strong id="calLabel"></strong>
              <button type="button" id="calNext" aria-label="Next month">&#8250;</button>
            </div>
            <div class="cal" id="cal"></div>
          </div>
          <div id="slotWrap" style="display:none;margin-top:20px">
            <label>Arrival window on <strong id="slotDate"></strong></label>
            <div class="slots" id="slots"></div>
            <p class="hint">We text you a 30-minute heads-up before the crew arrives.</p>
          </div>
          <div class="nav-row"><button class="btn btn-ghost back" data-back>Back</button>
            <button class="btn btn-primary" data-next>Continue</button></div>
        </div>

        <!-- 6. details -->
        <div class="panel" data-step="5">
          <h2>Where are we going?</h2>
          <p class="sub">Last step. No card needed &mdash; you pay after the clean is done.</p>
          <div class="field-row">
            <div class="field"><label for="f-name">Full name *</label>
              <input id="f-name" type="text" autocomplete="name" required></div>
            <div class="field"><label for="f-phone">Mobile number *</label>
              <input id="f-phone" type="tel" autocomplete="tel" required></div>
          </div>
          <div class="field"><label for="f-email">Email *</label>
            <input id="f-email" type="email" autocomplete="email" required>
            <p class="hint">Your confirmation and booking reference go here.</p></div>
          <div class="field"><label for="f-address">Street address *</label>
            <input id="f-address" type="text" autocomplete="street-address" required></div>
          <div class="field-row">
            <div class="field"><label for="f-city">City *</label>
              <select id="f-city" required></select></div>
            <div class="field"><label for="f-zip">ZIP</label>
              <input id="f-zip" type="text" inputmode="numeric" autocomplete="postal-code"
                maxlength="5"></div>
          </div>
          <div class="field"><label for="f-access">How do we get in?</label>
            <input id="f-access" type="text" placeholder="Door code, lockbox, key location, or 'I'll be home'">
            <p class="hint">Access details are stored in a chain-of-custody log and only shared
            with your assigned crew.</p></div>
          <div class="field"><label for="f-notes">Anything we should know?</label>
            <textarea id="f-notes" placeholder="Pets, allergies, fragile items, areas to skip, parking..."></textarea></div>
          <div class="alert alert-info" id="policyNote"></div>
          <div class="nav-row"><button class="btn btn-ghost back" data-back>Back</button>
            <button class="btn btn-primary btn-lg" id="submitBtn">Confirm booking</button></div>
        </div>

        <!-- 7. done -->
        <div class="panel" data-step="6"><div id="doneBox"></div></div>
      </div>

      <aside class="summary" id="summary"></aside>
    </div>
  </div>
</section>
'''

page("book.html", "Book a cleaning &mdash; instant price | %s" % NAME,
     "Get an instant flat-rate quote and book your Tampa Bay cleaning online in under a minute.",
     BODY, head=HEAD, scripts='<script src="/js/booking.js"></script>')
print("\n  build_book.py: booking wizard done")
