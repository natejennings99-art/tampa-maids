/* Booking wizard. All prices come from POST /api/quote so the browser never
   re-implements the pricing rules — the server stays the single authority. */
(async () => {
  const cfg = await getConfig();
  const params = new URLSearchParams(location.search);

  const S = {
    service: 'residential', tier_id: 't2', sqft: null,
    frequency: 'biweekly', addons: [], date: null, slot: null,
    commercial_type: 'office', visits_per_week: 1, is_first_clean: true,
  };
  if (params.get('service') && cfg.services.some(s => s.id === params.get('service')))
    S.service = params.get('service');

  const svcOf = id => cfg.services.find(s => s.id === id);
  const kind = () => svcOf(S.service).kind;

  /* which panels apply to the chosen service */
  const STEP_NAMES = ['Service', 'Size', 'How often', 'Extras', 'Date & time', 'Your details'];
  function activeSteps() {
    const k = kind();
    const list = [0, 1];
    if (k === 'residential') list.push(2);
    list.push(3, 4, 5);
    return list;
  }
  let stepIdx = 0;  // index into activeSteps()

  const panels = [...document.querySelectorAll('.panel')];
  const wsteps = document.getElementById('wsteps');
  const errBox = document.getElementById('wizError');

  function showError(m) {
    errBox.innerHTML = m ? `<div class="alert alert-bad">${icon('alert')}<span>${esc(m)}</span></div>` : '';
    if (m) errBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function render() {
    const steps = activeSteps();
    const cur = steps[stepIdx];
    panels.forEach(p => p.classList.toggle('active', +p.dataset.step === cur));
    wsteps.innerHTML = steps.map((s, i) =>
      `<div class="wstep ${i < stepIdx ? 'done' : ''} ${i === stepIdx ? 'now' : ''}">
        ${esc(STEP_NAMES[s])}</div>`).join('');
    wsteps.style.display = cur === 6 ? 'none' : 'flex';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    showError('');
  }

  /* ---------------- step 1: service ---------------- */
  document.getElementById('svcOpts').innerHTML = cfg.services.map(s =>
    `<label class="opt"><input type="radio" name="svc" value="${s.id}"
       ${s.id === S.service ? 'checked' : ''}><span class="opt-mark"></span>
     <span class="opt-body"><span class="opt-title">${esc(s.name)}</span>
     <span class="opt-desc">${esc(s.blurb)}</span></span></label>`).join('');
  document.querySelectorAll('input[name=svc]').forEach(r =>
    r.addEventListener('change', () => {
      S.service = r.value;
      if (kind() !== 'residential') S.frequency = 'once';
      else S.frequency = 'biweekly';
      S.addons = S.addons.filter(a =>
        cfg.addons.find(x => x.id === a).applies.includes(S.service));
      buildSize(); buildAddons(); quote();
    }));

  /* ---------------- step 2: size ---------------- */
  function buildSize() {
    const k = kind();
    const title = document.getElementById('sizeTitle'),
          sub = document.getElementById('sizeSub'),
          tierWrap = document.getElementById('tierOpts'),
          sqftWrap = document.getElementById('sqftWrap'),
          commWrap = document.getElementById('commWrap');

    tierWrap.style.display = k === 'residential' ? 'grid' : 'none';
    sqftWrap.style.display = (k === 'flat' || k === 'commercial') ? 'block' : 'none';
    commWrap.style.display = k === 'commercial' ? 'block' : 'none';

    if (k === 'residential') {
      title.textContent = 'How big is your home?';
      sub.textContent = 'This sets your price tier. Pick the closest match.';
      tierWrap.innerHTML = cfg.home_tiers.map(t =>
        `<label class="opt"><input type="radio" name="tier" value="${t.id}"
           ${t.id === S.tier_id ? 'checked' : ''}><span class="opt-mark"></span>
         <span class="opt-body"><span class="opt-title"><span>${esc(t.name)}</span>
         <span class="opt-price">${t.custom_quote ? 'Custom quote'
            : money0(t.prices[S.frequency] ?? t.prices.biweekly)}</span></span>
         <span class="opt-desc">${esc(t.detail)}</span></span></label>`).join('');
      tierWrap.querySelectorAll('input').forEach(r =>
        r.addEventListener('change', () => { S.tier_id = r.value; quote(); }));
    } else if (k === 'commercial') {
      title.textContent = 'Tell us about the space';
      sub.textContent = 'Commercial work is priced per square foot and confirmed on a walkthrough.';
      const sel = document.getElementById('commType');
      sel.innerHTML = svcOf(S.service).rates.map(r =>
        `<option value="${r.id}">${esc(r.name)} — ${esc(r.detail)}</option>`).join('');
      sel.value = S.commercial_type;
      sel.onchange = () => { S.commercial_type = sel.value; quote(); };
      const v = document.getElementById('visits');
      v.value = S.visits_per_week;
      v.onchange = () => { S.visits_per_week = +v.value; quote(); };
    } else {
      title.textContent = 'How big is the property?';
      sub.textContent = 'Flat-rate jobs are quoted on square footage and condition.';
    }
  }

  const sqftInput = document.getElementById('sqft');
  let sqftTimer;
  sqftInput.addEventListener('input', () => {
    clearTimeout(sqftTimer);
    sqftTimer = setTimeout(() => {
      S.sqft = sqftInput.value ? +sqftInput.value : null;
      quote();
    }, 350);
  });

  /* ---------------- step 3: frequency ---------------- */
  function buildFreq() {
    document.getElementById('freqOpts').innerHTML = cfg.frequencies.map(f => {
      const t = cfg.home_tiers.find(x => x.id === S.tier_id);
      const p = t && t.prices ? money0(t.prices[f.id]) : '';
      return `<label class="opt">${f.default ? '<span class="badge-pop">Most popular</span>' : ''}
        <input type="radio" name="freq" value="${f.id}" ${f.id === S.frequency ? 'checked' : ''}>
        <span class="opt-mark"></span><span class="opt-body">
        <span class="opt-title"><span>${esc(f.name)}</span>
        <span class="opt-price">${p}${p ? ' / visit' : ''}</span></span>
        <span class="opt-desc">${esc(f.blurb)}</span></span></label>`;
    }).join('');
    document.querySelectorAll('input[name=freq]').forEach(r =>
      r.addEventListener('change', () => { S.frequency = r.value; buildSize(); quote(); }));

    document.getElementById('firstCleanNote').innerHTML =
      icon('alert') + '<span>' + esc(cfg.booking.first_clean_note) + '</span>';
  }

  /* ---------------- step 4: add-ons ---------------- */
  function buildAddons() {
    const list = cfg.addons.filter(a => a.applies.includes(S.service));
    const box = document.getElementById('addonOpts');
    box.innerHTML = list.length ? list.map(a =>
      `<label class="opt"><input type="checkbox" value="${a.id}"
        ${S.addons.includes(a.id) ? 'checked' : ''}><span class="opt-mark"></span>
       <span class="opt-body"><span class="opt-title"><span>${esc(a.name)}</span>
       <span class="opt-price">+${money0(a.price)}</span></span>
       ${a.minutes ? `<span class="opt-desc">adds about ${a.minutes} min</span>` : ''}
       </span></label>`).join('')
      : '<p class="muted">No add-ons apply to this service — everything is included.</p>';
    box.querySelectorAll('input').forEach(c =>
      c.addEventListener('change', () => {
        S.addons = [...box.querySelectorAll('input:checked')].map(x => x.value);
        quote();
      }));
  }

  /* ---------------- step 5: calendar ---------------- */
  let calMonth = null, monthData = null;
  const calEl = document.getElementById('cal');

  async function loadMonth(m) {
    calEl.innerHTML = '<div class="skeleton" style="grid-column:1/-1;height:220px"></div>';
    try {
      monthData = await API.get(`/api/availability?month=${m}&service=${S.service}`);
      calMonth = monthData.month;
      drawCal();
    } catch (e) {
      calEl.innerHTML = `<p class="muted" style="grid-column:1/-1">${esc(e.message)}</p>`;
    }
  }

  function drawCal() {
    const [y, mo] = calMonth.split('-').map(Number);
    document.getElementById('calLabel').textContent =
      new Date(y, mo - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    const firstDow = new Date(y, mo - 1, 1).getDay();
    let html = ['S', 'M', 'T', 'W', 'T', 'F', 'S']
      .map(d => `<div class="dow">${d}</div>`).join('');
    html += '<div class="blank"></div>'.repeat(firstDow);
    html += monthData.days.map(d => {
      const day = +d.date.split('-')[2];
      return `<button type="button" data-date="${d.date}" ${d.open ? '' : 'disabled'}
        class="${S.date === d.date ? 'sel' : ''}"
        title="${esc(d.open ? (d.slots.length + ' windows open') : (d.reason || 'Unavailable'))}"
        >${day}</button>`;
    }).join('');
    calEl.innerHTML = html;
    calEl.querySelectorAll('button[data-date]').forEach(b =>
      b.addEventListener('click', () => pickDate(b.dataset.date)));

    const today = new Date();
    document.getElementById('calPrev').disabled =
      calMonth <= `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
  }

  function pickDate(date) {
    S.date = date; S.slot = null;
    drawCal();
    const day = monthData.days.find(d => d.date === date);
    document.getElementById('slotWrap').style.display = 'block';
    document.getElementById('slotDate').textContent = fmtDateLong(date);
    document.getElementById('slots').innerHTML = day.slots.map(s =>
      `<button type="button" data-slot="${esc(s)}">${esc(s)}</button>`).join('');
    document.querySelectorAll('#slots button').forEach(b =>
      b.addEventListener('click', () => {
        S.slot = b.dataset.slot;
        document.querySelectorAll('#slots button').forEach(x =>
          x.classList.toggle('sel', x === b));
        renderSummary();
      }));
    renderSummary();
  }

  function shiftMonth(delta) {
    let [y, m] = calMonth.split('-').map(Number);
    m += delta;
    if (m < 1) { m = 12; y--; } if (m > 12) { m = 1; y++; }
    loadMonth(`${y}-${String(m).padStart(2, '0')}`);
  }
  document.getElementById('calPrev').onclick = () => shiftMonth(-1);
  document.getElementById('calNext').onclick = () => shiftMonth(1);

  /* ---------------- step 6: details ---------------- */
  const citySel = document.getElementById('f-city');
  citySel.innerHTML = '<option value="">Select your city…</option>' +
    cfg.service_area.map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join('') +
    '<option value="Other">Somewhere else nearby</option>';
  citySel.addEventListener('change', quote);
  document.getElementById('policyNote').innerHTML =
    icon('alert') + '<span>' + esc(cfg.booking.cancellation_policy) + '</span>';

  /* ---------------- quote + summary ---------------- */
  let lastQuote = null, quoteSeq = 0;

  async function quote() {
    const seq = ++quoteSeq;
    const body = {
      service: S.service, tier_id: S.tier_id, sqft: S.sqft, frequency: S.frequency,
      addons: S.addons, city: citySel.value || null, is_first_clean: S.is_first_clean,
      commercial_type: S.commercial_type, visits_per_week: S.visits_per_week,
    };
    try {
      const q = await API.post('/api/quote', body);
      if (seq !== quoteSeq) return;      // a newer request already won
      lastQuote = q;
    } catch (e) {
      if (seq !== quoteSeq) return;
      lastQuote = { error: e.message };
    }
    renderSummary();
  }

  function renderSummary() {
    const box = document.getElementById('summary');
    const q = lastQuote;
    if (!q) { box.innerHTML = '<div class="card"><div class="skeleton" style="height:180px"></div></div>'; return; }

    if (q.error) {
      box.innerHTML = `<div class="card"><div class="alert alert-bad">${icon('alert')}
        <span>${esc(q.error)}</span></div></div>`;
      return;
    }

    if (q.custom_quote) {
      box.innerHTML = `<div class="card">
        <h3>Custom quote</h3><p style="font-size:.93rem">${esc(q.message)}</p>
        <a class="btn btn-primary" href="/contact" style="width:100%;margin-top:10px">Request a quote</a>
      </div>`;
      return;
    }

    const when = S.date
      ? `${fmtDate(S.date, { weekday: 'long', month: 'long', day: 'numeric' })}${S.slot ? ' · ' + S.slot : ''}`
      : 'Not chosen yet';

    box.innerHTML = `<div class="card">
      <h3 style="margin-bottom:2px">Your quote</h3>
      <p class="muted" style="font-size:.86rem;margin-bottom:0">${esc(q.service)}</p>
      <div class="sum-lines">${q.lines.map(l =>
        `<div class="sum-line ${l.amount < 0 ? 'neg' : ''}">
          <span class="lbl">${esc(l.label)}<small>${esc(l.detail || '')}</small></span>
          <span class="amt">${l.amount < 0 ? '−' : ''}${money(Math.abs(l.amount))}</span>
        </div>`).join('')}</div>
      ${q.tax ? `<div class="sum-line"><span class="lbl">Florida sales tax (${q.tax_rate}%)</span>
        <span class="amt">${money(q.tax)}</span></div>` : ''}
      <div class="sum-total"><span>${q.is_first_clean && q.recurring_total ? 'First visit' : 'Total'}</span>
        <span class="big">${money(q.total)}</span></div>
      ${q.recurring_total && q.recurring_total !== q.total
        ? `<div class="recurring-note">Then ${money(q.recurring_total)} per visit,
           ${esc((q.recurring_label || '').toLowerCase())}</div>` : ''}
      ${q.monthly_estimate
        ? `<div class="recurring-note">About ${money(q.monthly_estimate)} per month at
           ${q.visits_per_week}× a week</div>` : ''}
      <div style="margin-top:16px;padding-top:14px;border-top:1px solid var(--line);
        font-size:.86rem;color:var(--ink-2)">
        <div style="display:flex;justify-content:space-between;gap:10px;padding:3px 0">
          <span class="muted">When</span><strong style="text-align:right">${esc(when)}</strong></div>
      </div>
      <p class="hint" style="margin-top:12px">${q.tax_note ? esc(q.tax_note)
        : 'Residential cleaning is exempt from Florida sales tax.'}</p>
    </div>
    <p class="hint center" style="margin-top:12px">No payment now — you're charged after the clean.</p>`;
  }

  /* ---------------- navigation ---------------- */
  function validateStep(cur) {
    if (cur === 1) {
      if (kind() === 'residential') {
        const t = cfg.home_tiers.find(x => x.id === S.tier_id);
        if (t.custom_quote) return 'That size needs a custom quote — use the button in the summary.';
      } else if (!S.sqft || S.sqft < 100) {
        return 'Enter an approximate square footage so we can price the job.';
      }
    }
    if (cur === 4) {
      if (!S.date) return 'Pick a date for your cleaning.';
      if (!S.slot) return 'Pick an arrival window.';
    }
    return null;
  }

  document.querySelectorAll('[data-next]').forEach(b => b.addEventListener('click', () => {
    const steps = activeSteps(), cur = steps[stepIdx];
    const err = validateStep(cur);
    if (err) return showError(err);
    if (stepIdx < steps.length - 1) {
      stepIdx++;
      const next = activeSteps()[stepIdx];
      if (next === 2) buildFreq();
      if (next === 3) buildAddons();
      if (next === 4 && !monthData) loadMonth(new Date().toISOString().slice(0, 7));
      render();
    }
  }));
  document.querySelectorAll('[data-back]').forEach(b => b.addEventListener('click', () => {
    if (stepIdx > 0) { stepIdx--; render(); }
  }));

  /* ---------------- submit ---------------- */
  document.getElementById('submitBtn').addEventListener('click', async () => {
    const g = id => document.getElementById(id).value.trim();
    const body = {
      name: g('f-name'), email: g('f-email'), phone: g('f-phone'),
      address: g('f-address'), city: citySel.value, zip: g('f-zip'),
      access_notes: g('f-access'), notes: g('f-notes'),
      service: S.service, tier_id: S.tier_id, sqft: S.sqft, frequency: S.frequency,
      addons: S.addons, date: S.date, slot: S.slot, is_first_clean: S.is_first_clean,
      commercial_type: S.commercial_type, visits_per_week: S.visits_per_week,
    };
    if (!body.name || !body.email || !body.phone || !body.address || !body.city)
      return showError('Please fill in your name, phone, email, address and city.');

    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Booking…';
    try {
      const r = await API.post('/api/bookings', body);
      try { localStorage.setItem('gc_email', body.email); } catch (e) {}
      stepIdx = activeSteps().length - 1;
      panels.forEach(p => p.classList.toggle('active', +p.dataset.step === 6));
      wsteps.style.display = 'none';
      document.getElementById('doneBox').innerHTML = `
        <div class="center" style="padding:20px 0 10px">
          <div class="icon-badge" style="margin:0 auto 18px;width:64px;height:64px;
            background:var(--ok-bg);color:var(--ok);border-radius:50%">
            ${icon('check')}</div>
          <h2>You're booked.</h2>
          <p class="lede" style="margin-inline:auto">${esc(r.message)}</p>
          <div class="card" style="max-width:420px;margin:26px auto;text-align:left">
            <div style="display:flex;justify-content:space-between;padding:8px 0;
              border-bottom:1px solid var(--line)">
              <span class="muted">Reference</span><strong>${esc(r.ref)}</strong></div>
            <div style="display:flex;justify-content:space-between;padding:8px 0;
              border-bottom:1px solid var(--line)">
              <span class="muted">When</span><strong>${esc(fmtDateLong(r.date))}, ${esc(r.slot)}</strong></div>
            <div style="display:flex;justify-content:space-between;padding:8px 0">
              <span class="muted">Total</span><strong>${money(r.quote.total)}</strong></div>
          </div>
          <p class="muted" style="font-size:.92rem">Save your reference — you'll need it
          to look up or change this booking.</p>
          <div class="btn-row" style="justify-content:center;margin-top:20px">
            <a class="btn btn-primary" href="/track?ref=${encodeURIComponent(r.ref)}">Track my booking</a>
            <a class="btn btn-ghost" href="/app">Get the app</a>
          </div>
        </div>`;
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) {
      showError(e.message);
      btn.disabled = false;
      btn.textContent = 'Confirm booking';
    }
  });

  /* boot */
  buildSize(); buildAddons(); render(); quote();
})();
