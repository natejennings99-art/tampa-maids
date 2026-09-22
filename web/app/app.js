/* Tampa Maids Cleaning — phone app.
   One shell, four tabs. Customers book and track; staff see their day and
   work the checklist. Everything talks to the same API as the website. */

let CFG = null, ME = null, TAB = 'home', installPrompt = null;

const store = {
  get(k, d) { try { return JSON.parse(localStorage.getItem('gc_' + k)) ?? d; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('gc_' + k, JSON.stringify(v)); } catch (e) {} },
  del(k) { try { localStorage.removeItem('gc_' + k); } catch (e) {} },
};

const view = () => document.getElementById('view');
const setBar = (t, s) => {
  document.getElementById('barTitle').innerHTML =
    esc(t) + (s ? `<span class="sub">${esc(s)}</span>` : '');
};
const STATUS = {
  requested: ['pill-warn', 'Pending'], confirmed: ['pill-info', 'Confirmed'],
  in_progress: ['pill-info', 'In progress'], completed: ['pill-ok', 'Done'],
  cancelled: ['pill-grey', 'Cancelled'],
};
const alertBox = (kind, msg, ic) =>
  `<div class="alert alert-${kind}">${icon(ic || (kind === 'bad' ? 'alert' : 'check'))}<span>${esc(msg)}</span></div>`;

/* ---------------------------------------------------------------- sheet */
function openSheet(html) {
  document.getElementById('sheetBody').innerHTML = '<div class="grabber"></div>' + html;
  document.getElementById('sheet').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeSheet() {
  document.getElementById('sheet').classList.remove('open');
  document.body.style.overflow = '';
}
document.getElementById('sheet').addEventListener('click', e => {
  if (e.target.id === 'sheet') closeSheet();
});

/* ---------------------------------------------------------------- tabs */
function tabs() {
  const staff = !!ME;
  return staff
    ? [['home', 'Today', 'home'], ['jobs', 'My jobs', 'list'],
       ['book', 'Book', 'cal'], ['account', 'Account', 'user']]
    : [['home', 'Home', 'home'], ['book', 'Book', 'cal'],
       ['jobs', 'My cleans', 'list'], ['account', 'Account', 'user']];
}
function drawTabs() {
  document.getElementById('tabbar').innerHTML = tabs().map(([id, label, ic]) =>
    `<button data-tab="${id}" class="${TAB === id ? 'on' : ''}">
      ${icon(ic)}<span>${esc(label)}</span></button>`).join('');
  document.querySelectorAll('#tabbar button').forEach(b =>
    b.addEventListener('click', () => go(b.dataset.tab)));
}
function go(tab) {
  TAB = tab;
  drawTabs();
  history.replaceState(null, '', '?tab=' + tab);
  ({ home: viewHome, book: viewBook, jobs: viewJobs, account: viewAccount }[tab] || viewHome)();
  window.scrollTo(0, 0);
}

/* ---------------------------------------------------------------- home */
function viewHome() {
  if (ME) return viewCrewToday();
  setBar(CFG.short_name, CFG.tagline);
  document.getElementById('barAction').hidden = true;

  const cheapest = Math.min(...CFG.home_tiers.filter(t => t.prices)
    .map(t => Math.min(...Object.values(t.prices))));

  view().innerHTML = `
    ${installPrompt ? `<div class="install-bar">${icon('sparkle')}
      <div style="flex:1">Add ${esc(CFG.short_name)} to your home screen for one-tap booking.</div>
      <button class="btn btn-sm btn-primary" id="installBtn">Install</button></div>` : ''}

    <div class="card hero-card">
      <h2>Get your time back.</h2>
      <p>Flat prices, a bonded team, and a free re-clean if anything's off.
         From ${money0(cheapest)} a visit.</p>
      <button class="btn btn-accent" id="goBook" style="margin-top:6px">See my price</button>
    </div>

    <h3 style="margin:22px 0 10px">What we clean</h3>
    ${CFG.services.map(s => `<button class="job" data-svc="${s.id}">
      <div class="job-top">
        <div style="display:flex;gap:12px;align-items:center;min-width:0">
          <span style="width:38px;height:38px;border-radius:11px;background:var(--teal-50);
            color:var(--teal);display:grid;place-items:center;flex-shrink:0">
            ${icon(s.icon)}</span>
          <span style="min-width:0"><span class="job-title">${esc(s.name)}</span></span>
        </div>
        ${icon('arrow', 'arr')}
      </div>
      <div class="job-meta">${esc(s.blurb)}</div></button>`).join('')}

    <div class="card" style="margin-top:18px">
      <h3>Why people stay</h3>
      ${CFG.guarantees.slice(0, 4).map(g => `<div class="row" style="align-items:flex-start">
        <span style="color:var(--teal);flex-shrink:0;margin-top:2px">${icon(g.icon, 'g16')}</span>
        <span class="v" style="text-align:left;flex:1;font-weight:400">
          <strong style="display:block">${esc(g.title)}</strong>
          <span class="muted small">${esc(g.text)}</span></span></div>`).join('')}
    </div>

    <div class="card">
      <h3>Need a person?</h3>
      <div class="btn-row" style="margin-top:10px">
        <a class="btn btn-ghost" href="tel:${esc(CFG.phone_raw)}">${icon('phone')} Call</a>
        <a class="btn btn-ghost" href="mailto:${esc(CFG.email)}">${icon('mail')} Email</a>
      </div>
      <p class="hint center" style="margin-top:10px">${esc(CFG.hours.residential)}</p>
    </div>`;

  document.querySelectorAll('.arr,.g16').forEach(s => {
    s.style.width = '18px'; s.style.height = '18px'; s.style.flexShrink = '0';
    s.style.color = 'var(--ink-3)';
  });
  document.querySelectorAll('.g16').forEach(s => { s.style.color = 'inherit'; });
  document.getElementById('goBook').onclick = () => go('book');
  document.querySelectorAll('[data-svc]').forEach(b =>
    b.onclick = () => { store.set('svc', b.dataset.svc); go('book'); });
  const ib = document.getElementById('installBtn');
  if (ib) ib.onclick = async () => {
    if (!installPrompt) return;
    installPrompt.prompt();
    await installPrompt.userChoice;
    installPrompt = null;
    viewHome();
  };
}

/* ---------------------------------------------------------------- book */
function viewBook() {
  setBar('Book a cleaning', 'Instant flat price');
  document.getElementById('barAction').hidden = true;

  const S = {
    service: store.get('svc', 'residential'),
    tier_id: 't2', sqft: null, frequency: 'biweekly', addons: [],
    date: null, slot: null, commercial_type: 'office', visits_per_week: 1,
  };
  store.del('svc');
  if (!CFG.services.some(s => s.id === S.service)) S.service = 'residential';
  const svcOf = id => CFG.services.find(s => s.id === id);
  const kind = () => svcOf(S.service).kind;
  if (kind() !== 'residential') S.frequency = 'once';

  view().innerHTML = `
    <div id="bkErr"></div>
    <div class="card">
      <h3>What do you need?</h3>
      <div class="field" style="margin-top:10px">
        <select id="b-svc">${CFG.services.map(s =>
          `<option value="${s.id}"${s.id === S.service ? ' selected' : ''}>${esc(s.name)}</option>`
        ).join('')}</select>
      </div>
      <div id="sizeBox"></div>
    </div>

    <div class="card" id="freqCard">
      <h3>How often?</h3>
      <div class="seg" id="b-freq" style="margin-top:10px"></div>
      <p class="hint" id="freqHint"></p>
    </div>

    <div class="card">
      <h3>Add-ons <span class="muted small" style="font-weight:400">optional</span></h3>
      <div id="addonBox" style="margin-top:10px"></div>
    </div>

    <div class="card">
      <h3>When?</h3>
      <div class="field" style="margin-top:10px">
        <label for="b-date">Date</label>
        <select id="b-date"><option value="">Loading availability…</option></select>
      </div>
      <div class="field" id="slotField" style="display:none">
        <label for="b-slot">Arrival window</label>
        <select id="b-slot"></select>
      </div>
    </div>

    <div class="card" id="quoteCard"><div class="loading">Calculating…</div></div>

    <div class="card">
      <h3>Your details</h3>
      <div style="margin-top:12px">
        <div class="field"><label for="b-name">Full name</label><input id="b-name" autocomplete="name"></div>
        <div class="field2">
          <div class="field"><label for="b-phone">Mobile</label><input id="b-phone" type="tel" autocomplete="tel"></div>
          <div class="field"><label for="b-zip">ZIP</label><input id="b-zip" inputmode="numeric" maxlength="5" autocomplete="postal-code"></div>
        </div>
        <div class="field"><label for="b-email">Email</label><input id="b-email" type="email" autocomplete="email"></div>
        <div class="field"><label for="b-address">Street address</label><input id="b-address" autocomplete="street-address"></div>
        <div class="field"><label for="b-city">City</label><select id="b-city">
          <option value="">Choose…</option>
          ${CFG.service_area.map(c => `<option>${esc(c)}</option>`).join('')}
          <option>Other</option></select></div>
        <div class="field"><label for="b-access">How do we get in?</label>
          <input id="b-access" placeholder="Door code, lockbox, or I'll be home"></div>
        <div class="field"><label for="b-notes">Anything we should know?</label>
          <textarea id="b-notes" placeholder="Pets, allergies, parking, areas to skip…"></textarea></div>
      </div>
    </div>

    <button class="btn btn-primary" id="bkSubmit" style="margin-bottom:20px">Confirm booking</button>
    <p class="hint center" style="margin-bottom:8px">No card needed. You pay after the clean.</p>`;

  const $ = id => document.getElementById(id);
  const emailSaved = store.get('email', '');
  if (emailSaved) $('b-email').value = emailSaved;

  function buildSize() {
    const k = kind();
    if (k === 'residential') {
      $('sizeBox').innerHTML = `<div class="field"><label for="b-tier">Home size</label>
        <select id="b-tier">${CFG.home_tiers.map(t =>
          `<option value="${t.id}"${t.id === S.tier_id ? ' selected' : ''}>
            ${esc(t.name)} — ${esc(t.detail)}</option>`).join('')}</select></div>`;
      $('b-tier').onchange = e => { S.tier_id = e.target.value; quote(); };
      $('freqCard').style.display = '';
    } else if (k === 'commercial') {
      $('sizeBox').innerHTML = `
        <div class="field"><label for="b-ct">Type of space</label><select id="b-ct">
          ${svcOf(S.service).rates.map(r =>
            `<option value="${r.id}">${esc(r.name)}</option>`).join('')}</select></div>
        <div class="field2">
          <div class="field"><label for="b-sqft">Square feet</label>
            <input id="b-sqft" type="number" inputmode="numeric" placeholder="2000"></div>
          <div class="field"><label for="b-vpw">Visits / week</label><select id="b-vpw">
            <option value="1">1</option><option value="2">2</option>
            <option value="3">3</option><option value="5">5</option></select></div>
        </div>`;
      $('b-ct').onchange = e => { S.commercial_type = e.target.value; quote(); };
      $('b-vpw').onchange = e => { S.visits_per_week = +e.target.value; quote(); };
      bindSqft();
      $('freqCard').style.display = 'none';
    } else {
      $('sizeBox').innerHTML = `<div class="field"><label for="b-sqft">Square feet</label>
        <input id="b-sqft" type="number" inputmode="numeric" placeholder="1500">
        <p class="hint">A close estimate is fine.</p></div>`;
      bindSqft();
      $('freqCard').style.display = 'none';
    }
  }
  let t;
  function bindSqft() {
    $('b-sqft').oninput = e => {
      clearTimeout(t);
      t = setTimeout(() => { S.sqft = e.target.value ? +e.target.value : null; quote(); }, 350);
    };
  }

  function buildFreq() {
    $('b-freq').innerHTML = CFG.frequencies.map(f =>
      `<button data-f="${f.id}" class="${f.id === S.frequency ? 'on' : ''}">${esc(f.name)}</button>`
    ).join('');
    $('freqHint').textContent = CFG.booking.first_clean_note;
    $('b-freq').querySelectorAll('button').forEach(b => b.onclick = () => {
      S.frequency = b.dataset.f; buildFreq(); quote();
    });
  }

  function buildAddons() {
    const list = CFG.addons.filter(a => a.applies.includes(S.service));
    $('addonBox').innerHTML = list.length ? list.map(a =>
      `<label class="task ${S.addons.includes(a.id) ? 'done' : ''}" data-a="${a.id}">
        <span class="box">${icon('check')}</span>
        <span style="flex:1">${esc(a.name)}</span>
        <strong style="color:var(--teal)">+${money0(a.price)}</strong></label>`).join('')
      : '<p class="muted small">Everything is included for this service.</p>';
    $('addonBox').querySelectorAll('[data-a]').forEach(el => el.onclick = e => {
      e.preventDefault();
      const id = el.dataset.a;
      S.addons = S.addons.includes(id) ? S.addons.filter(x => x !== id) : [...S.addons, id];
      buildAddons(); quote();
    });
  }

  async function loadDates() {
    try {
      const a = await API.get('/api/availability?service=' + S.service);
      const open = a.days.filter(d => d.open);
      $('b-date').innerHTML = '<option value="">Choose a date…</option>' + open.map(d =>
        `<option value="${d.date}" data-slots="${esc(d.slots.join('|'))}">
          ${esc(fmtDate(d.date, { weekday: 'long', month: 'short', day: 'numeric' }))}</option>`).join('');
      $('b-date').onchange = e => {
        const opt = e.target.selectedOptions[0];
        S.date = e.target.value || null;
        S.slot = null;
        if (!S.date) { $('slotField').style.display = 'none'; return; }
        const slots = (opt.dataset.slots || '').split('|').filter(Boolean);
        $('slotField').style.display = '';
        $('b-slot').innerHTML = slots.map(s => `<option>${esc(s)}</option>`).join('');
        S.slot = slots[0] || null;
        $('b-slot').onchange = ev => { S.slot = ev.target.value; };
      };
    } catch (e) {
      $('b-date').innerHTML = `<option value="">${esc(e.message)}</option>`;
    }
  }

  let seq = 0;
  async function quote() {
    const n = ++seq;
    try {
      const q = await API.post('/api/quote', {
        service: S.service, tier_id: S.tier_id, sqft: S.sqft, frequency: S.frequency,
        addons: S.addons, city: $('b-city').value || null, is_first_clean: true,
        commercial_type: S.commercial_type, visits_per_week: S.visits_per_week,
      });
      if (n !== seq) return;
      if (q.custom_quote) {
        $('quoteCard').innerHTML = `<h3>Custom quote needed</h3>
          <p class="small muted">${esc(q.message)}</p>
          <a class="btn btn-ghost" href="tel:${esc(CFG.phone_raw)}">Call for a quote</a>`;
        return;
      }
      $('quoteCard').innerHTML = `
        <h3>Your price</h3>
        <div style="margin-top:8px">${q.lines.map(l => `<div class="row">
          <span class="k">${esc(l.label)}</span>
          <span class="v" style="${l.amount < 0 ? 'color:var(--ok)' : ''}">
            ${l.amount < 0 ? '−' : ''}${money(Math.abs(l.amount))}</span></div>`).join('')}
          ${q.tax ? `<div class="row"><span class="k">Sales tax (${q.tax_rate}%)</span>
            <span class="v">${money(q.tax)}</span></div>` : ''}</div>
        <div style="display:flex;justify-content:space-between;align-items:baseline;
          padding-top:13px;margin-top:6px;border-top:2px solid var(--ink)">
          <strong>${q.recurring_total ? 'First visit' : 'Total'}</strong>
          <span style="font-family:var(--display);font-size:1.75rem;font-weight:600">
            ${money(q.total)}</span></div>
        ${q.recurring_total && q.recurring_total !== q.total
          ? `<div class="alert alert-ok" style="margin-top:12px">${icon('check')}
             <span>Then ${money(q.recurring_total)} per visit</span></div>` : ''}
        ${q.monthly_estimate
          ? `<div class="alert alert-info" style="margin-top:12px">${icon('chart')}
             <span>About ${money(q.monthly_estimate)} per month</span></div>` : ''}`;
    } catch (e) {
      if (n !== seq) return;
      $('quoteCard').innerHTML = alertBox('bad', e.message);
    }
  }

  $('b-svc').onchange = e => {
    S.service = e.target.value;
    S.frequency = kind() === 'residential' ? 'biweekly' : 'once';
    S.addons = [];
    buildSize(); buildFreq(); buildAddons(); loadDates(); quote();
  };
  $('b-city').onchange = quote;

  $('bkSubmit').onclick = async () => {
    const v = id => $(id).value.trim();
    const err = m => { $('bkErr').innerHTML = alertBox('bad', m); window.scrollTo(0, 0); };
    if (!v('b-name') || !v('b-email') || !v('b-phone') || !v('b-address') || !v('b-city'))
      return err('Fill in your name, mobile, email, address and city.');
    if (!S.date || !S.slot) return err('Pick a date and arrival window.');

    const btn = $('bkSubmit');
    btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Booking…';
    try {
      const r = await API.post('/api/bookings', {
        name: v('b-name'), email: v('b-email'), phone: v('b-phone'),
        address: v('b-address'), city: v('b-city'), zip: v('b-zip'),
        access_notes: v('b-access'), notes: v('b-notes'),
        service: S.service, tier_id: S.tier_id, sqft: S.sqft, frequency: S.frequency,
        addons: S.addons, date: S.date, slot: S.slot, is_first_clean: true,
        commercial_type: S.commercial_type, visits_per_week: S.visits_per_week,
      });
      store.set('email', v('b-email'));
      view().innerHTML = `<div class="card center" style="padding:34px 20px">
        <div style="width:62px;height:62px;border-radius:50%;background:var(--ok-bg);color:var(--ok);
          display:grid;place-items:center;margin:0 auto 16px">${icon('check')}</div>
        <h2>You're booked</h2>
        <p class="muted small">${esc(r.message)}</p>
        <div style="text-align:left;margin-top:18px">
          <div class="row"><span class="k">Reference</span><span class="v">${esc(r.ref)}</span></div>
          <div class="row"><span class="k">When</span>
            <span class="v">${esc(fmtDate(r.date))} · ${esc(r.slot)}</span></div>
          <div class="row"><span class="k">Total</span><span class="v">${money(r.quote.total)}</span></div>
        </div>
        <button class="btn btn-primary" id="toJobs" style="margin-top:18px">See my cleanings</button>
      </div>`;
      $('toJobs').onclick = () => go('jobs');
      window.scrollTo(0, 0);
    } catch (e) {
      err(e.message);
      btn.disabled = false; btn.textContent = 'Confirm booking';
    }
  };

  buildSize(); buildFreq(); buildAddons(); loadDates(); quote();
}

/* ---------------------------------------------------------------- jobs */
function viewJobs() { return ME ? viewCrewJobs() : viewMyCleans(); }

async function viewMyCleans() {
  setBar('My cleanings', 'Look up by email');
  document.getElementById('barAction').hidden = true;
  const email = store.get('email', '');

  if (!email) {
    view().innerHTML = `<div class="card">
      <h3>Find your cleanings</h3>
      <p class="muted small">Enter the email you booked with.</p>
      <div class="field"><input id="lookup" type="email" placeholder="you@example.com"
        autocomplete="email"></div>
      <button class="btn btn-primary" id="lookupBtn">Show my cleanings</button></div>
      <p class="hint center">Not booked yet? <a href="#" id="toBook">Get a price</a>.</p>`;
    document.getElementById('lookupBtn').onclick = () => {
      const v = document.getElementById('lookup').value.trim();
      if (!v) return;
      store.set('email', v); viewMyCleans();
    };
    document.getElementById('toBook').onclick = e => { e.preventDefault(); go('book'); };
    return;
  }

  view().innerHTML = '<div class="loading">Loading your cleanings…</div>';
  try {
    const r = await API.get('/api/bookings/mine?email=' + encodeURIComponent(email));
    const upcoming = r.bookings.filter(b => !['completed', 'cancelled'].includes(b.status));
    const past = r.bookings.filter(b => ['completed', 'cancelled'].includes(b.status));

    view().innerHTML = `
      <p class="hint" style="margin-bottom:12px">Showing cleanings for
        <strong>${esc(email)}</strong> ·
        <a href="#" id="switchEmail">change</a></p>
      ${upcoming.length ? `<h3 style="margin-bottom:10px">Upcoming</h3>
        ${upcoming.map(jobCard).join('')}` : `<div class="card center" style="padding:30px 18px">
        <p class="muted">No upcoming cleanings.</p>
        <button class="btn btn-primary" id="bookNow">Book one</button></div>`}
      ${past.length ? `<h3 style="margin:22px 0 10px">Past</h3>
        ${past.map(jobCard).join('')}` : ''}`;

    document.getElementById('switchEmail').onclick = e => {
      e.preventDefault(); store.del('email'); viewMyCleans();
    };
    const bn = document.getElementById('bookNow');
    if (bn) bn.onclick = () => go('book');
    bindJobCards(r.bookings, customerSheet);
  } catch (e) {
    view().innerHTML = alertBox('bad', e.message) +
      '<button class="btn btn-ghost" onclick="viewMyCleans()">Try again</button>';
  }
}

function jobCard(b) {
  const [cls, label] = STATUS[b.status] || ['pill-grey', b.status];
  return `<button class="job" data-id="${b.id}">
    <div class="job-top">
      <div style="min-width:0">
        <div class="job-title">${esc(b.service)}</div>
        <div class="job-meta">${esc(b.customer.address)}, ${esc(b.customer.city)}</div>
      </div>
      <span class="pill ${cls}">${esc(label)}</span>
    </div>
    <div class="job-when">${icon('cal')} ${esc(fmtDate(b.date))} · ${esc(b.slot)}
      <span class="muted" style="margin-left:auto;font-weight:600">${money(b.total)}</span></div>
    ${b.status === 'in_progress' || b.status === 'completed'
      ? `<div class="progress"><i style="width:${b.tasks_total ? Math.round(b.tasks_done / b.tasks_total * 100) : 0}%"></i></div>
         <div class="job-meta" style="margin-top:5px">${b.tasks_done} of ${b.tasks_total} checklist items</div>`
      : ''}</button>`;
}

function bindJobCards(list, handler) {
  document.querySelectorAll('.job[data-id]').forEach(el => el.onclick = () => {
    const b = list.find(x => String(x.id) === el.dataset.id);
    if (b) handler(b);
  });
}

function customerSheet(b) {
  const [cls, label] = STATUS[b.status] || ['pill-grey', b.status];
  const canCancel = !['completed', 'cancelled'].includes(b.status);
  openSheet(`
    <div class="sheet-head">
      <div><h2>${esc(b.service)}</h2>
        <p class="muted small" style="margin:0">Reference ${esc(b.ref)}</p></div>
      <span class="pill ${cls}">${esc(label)}</span>
    </div>
    <div class="card">
      <div class="row"><span class="k">When</span>
        <span class="v">${esc(fmtDateLong(b.date))}<br>${esc(b.slot)}</span></div>
      <div class="row"><span class="k">Address</span>
        <span class="v">${esc(b.customer.address)}, ${esc(b.customer.city)}</span></div>
      <div class="row"><span class="k">Total</span><span class="v">${money(b.total)}</span></div>
      <div class="row"><span class="k">Crew</span>
        <span class="v">${esc(b.assigned_name || 'Being assigned')}</span></div>
      <div class="row"><span class="k">Checklist</span>
        <span class="v">${b.tasks_done} / ${b.tasks_total} done</span></div>
    </div>
    ${canCancel ? `<div class="alert alert-info">${icon('alert')}
      <span>${esc(CFG.booking.cancellation_policy)}</span></div>
      <button class="btn btn-danger" id="cxl">Cancel this cleaning</button>` : ''}
    <div class="btn-row" style="margin-top:10px">
      <a class="btn btn-ghost" href="tel:${esc(CFG.phone_raw)}">${icon('phone')} Call us</a>
      <button class="btn btn-ghost" onclick="closeSheet()">Close</button>
    </div>`);

  const c = document.getElementById('cxl');
  if (c) c.onclick = async () => {
    if (!confirm('Cancel this cleaning?')) return;
    c.disabled = true; c.innerHTML = '<span class="spinner"></span> Cancelling…';
    try {
      const r = await API.post('/api/bookings/cancel',
        { ref: b.ref, email: store.get('email', '') });
      closeSheet();
      viewMyCleans();
      setTimeout(() => alert(r.message), 120);
    } catch (e) {
      c.disabled = false; c.textContent = 'Cancel this cleaning';
      alert(e.message);
    }
  };
}

/* ---------------------------------------------------------------- crew */
async function viewCrewToday() {
  setBar('Today', ME.name);
  document.getElementById('barAction').hidden = true;
  view().innerHTML = '<div class="loading">Loading your day…</div>';
  try {
    const r = await API.get('/api/crew/jobs');
    const today = r.jobs_today;
    const done = today.filter(j => j.status === 'completed').length;
    const revenue = today.reduce((a, j) => a + j.total, 0);
    view().innerHTML = `
      <div class="stat-grid">
        <div class="stat accent"><div class="n">${today.length}</div><div class="l">Jobs today</div></div>
        <div class="stat"><div class="n">${done}</div><div class="l">Completed</div></div>
        <div class="stat"><div class="n">${money0(revenue)}</div><div class="l">Today's value</div></div>
        <div class="stat"><div class="n">${r.jobs.length}</div><div class="l">Upcoming</div></div>
      </div>
      <h3 style="margin:20px 0 10px">${esc(fmtDateLong(r.today))}</h3>
      ${today.length ? today.map(jobCard).join('')
        : `<div class="empty">${icon('cal')}<p>Nothing scheduled today. Enjoy it.</p></div>`}`;
    bindJobCards(r.jobs, crewSheet);
  } catch (e) {
    view().innerHTML = alertBox('bad', e.message);
  }
}

async function viewCrewJobs() {
  setBar('My jobs', ME.role === 'owner' ? 'All upcoming work' : 'Assigned to you');
  document.getElementById('barAction').hidden = true;
  view().innerHTML = '<div class="loading">Loading jobs…</div>';
  try {
    const r = await API.get('/api/crew/jobs');
    const byDate = {};
    r.jobs.forEach(j => (byDate[j.date] = byDate[j.date] || []).push(j));
    view().innerHTML = Object.keys(byDate).sort().map(d =>
      `<h3 style="margin:18px 0 9px">${esc(fmtDateLong(d))}</h3>
       ${byDate[d].map(jobCard).join('')}`).join('') ||
      `<div class="empty">${icon('list')}<p>No jobs assigned yet.</p></div>`;
    bindJobCards(r.jobs, crewSheet);
  } catch (e) {
    view().innerHTML = alertBox('bad', e.message);
  }
}

function crewSheet(b) {
  const [cls, label] = STATUS[b.status] || ['pill-grey', b.status];
  const areas = {};
  b.tasks.forEach(t => (areas[t.area] = areas[t.area] || []).push(t));
  const pct = b.tasks_total ? Math.round(b.tasks_done / b.tasks_total * 100) : 0;

  openSheet(`
    <div class="sheet-head">
      <div><h2>${esc(b.service)}</h2>
        <p class="muted small" style="margin:0">${esc(b.ref)} · ${esc(fmtDate(b.date))} ${esc(b.slot)}</p></div>
      <span class="pill ${cls}">${esc(label)}</span>
    </div>

    <div class="card">
      <div class="row"><span class="k">Client</span><span class="v">${esc(b.customer.name)}</span></div>
      <div class="row"><span class="k">Address</span>
        <span class="v">${esc(b.customer.address)}<br>${esc(b.customer.city)} ${esc(b.customer.zip || '')}</span></div>
      <div class="row"><span class="k">Access</span>
        <span class="v">${esc(b.access_notes || 'Not provided')}</span></div>
      ${b.notes ? `<div class="row"><span class="k">Notes</span><span class="v">${esc(b.notes)}</span></div>` : ''}
      <div class="btn-row" style="margin-top:12px">
        <a class="btn btn-ghost btn-sm" href="tel:${esc((b.customer.phone || '').replace(/[^0-9+]/g, ''))}">
          ${icon('phone')} Call</a>
        <a class="btn btn-ghost btn-sm" target="_blank" rel="noopener"
          href="https://maps.apple.com/?q=${encodeURIComponent(b.customer.address + ', ' + b.customer.city)}">
          ${icon('pin')} Directions</a>
      </div>
    </div>

    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <h3>Checklist</h3>
        <strong id="ckCount">${b.tasks_done} / ${b.tasks_total}</strong>
      </div>
      <div class="progress" style="margin-top:8px"><i id="ckBar" style="width:${pct}%"></i></div>
    </div>

    <div id="taskList">${Object.keys(areas).map(a =>
      `<div class="area-h">${esc(a)}</div>
       ${areas[a].map(t => `<label class="task ${t.done ? 'done' : ''}" data-t="${t.id}">
         <span class="box">${icon('check')}</span><span>${esc(t.label)}</span></label>`).join('')}`
    ).join('')}</div>

    <div style="position:sticky;bottom:0;background:var(--bg);padding:12px 0 4px;
      margin-top:10px;border-top:1px solid var(--line)">
      ${b.status === 'completed'
        ? '<button class="btn btn-ghost" onclick="closeSheet()">Close</button>'
        : `<div class="btn-row">
            ${b.status !== 'in_progress'
              ? '<button class="btn btn-ghost" data-st="in_progress">Start job</button>' : ''}
            <button class="btn btn-primary" data-st="completed">Mark complete</button>
          </div>`}
    </div>`);

  /* checklist ticking */
  document.querySelectorAll('[data-t]').forEach(el => el.onclick = async e => {
    e.preventDefault();
    const id = el.dataset.t, willBeDone = !el.classList.contains('done');
    el.classList.toggle('done', willBeDone);
    try {
      const r = await API.post('/api/crew/tasks/' + id, { done: willBeDone });
      document.getElementById('ckCount').textContent = r.tasks_done + ' / ' + r.tasks_total;
      document.getElementById('ckBar').style.width =
        Math.round(r.tasks_done / r.tasks_total * 100) + '%';
      b.tasks_done = r.tasks_done;
    } catch (err) {
      el.classList.toggle('done', !willBeDone);   // roll the tick back
      alert(err.message);
    }
  });

  /* status buttons */
  document.querySelectorAll('[data-st]').forEach(btn => btn.onclick = async () => {
    const status = btn.dataset.st;
    const orig = btn.textContent;
    btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>';
    try {
      await API.post(`/api/crew/jobs/${b.id}/status`, { status });
      closeSheet();
      TAB === 'home' ? viewCrewToday() : viewCrewJobs();
    } catch (e) {
      btn.disabled = false; btn.textContent = orig;
      if (/checklist item/.test(e.message) && confirm(e.message + '\n\nComplete anyway?')) {
        try {
          await API.post(`/api/crew/jobs/${b.id}/status`, { status, force: true });
          closeSheet();
          TAB === 'home' ? viewCrewToday() : viewCrewJobs();
        } catch (e2) { alert(e2.message); }
      } else if (!/checklist item/.test(e.message)) alert(e.message);
    }
  });
}

/* ---------------------------------------------------------------- account */
function viewAccount() {
  setBar('Account', ME ? ME.role : CFG.short_name);
  document.getElementById('barAction').hidden = true;

  if (ME) {
    view().innerHTML = `
      <div class="card">
        <div style="display:flex;gap:14px;align-items:center">
          <div style="width:52px;height:52px;border-radius:50%;background:var(--teal);color:#fff;
            display:grid;place-items:center;font-weight:800;font-size:1.2rem">
            ${esc(ME.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase())}</div>
          <div><strong style="display:block">${esc(ME.name)}</strong>
            <span class="muted small">${esc(ME.email)}</span></div>
        </div>
        <div class="row" style="margin-top:14px"><span class="k">Role</span>
          <span class="v" style="text-transform:capitalize">${esc(ME.role)}</span></div>
      </div>
      ${['owner', 'lead'].includes(ME.role) ? `<div class="card">
        <h3>Owner tools</h3>
        <p class="muted small">The full dashboard — bookings, leads, crew and revenue —
        works best on a bigger screen.</p>
        <a class="btn btn-ghost" href="/admin" target="_blank" rel="noopener">
          ${icon('chart')} Open dashboard</a></div>` : ''}
      <button class="btn btn-danger" id="out">${icon('logout')} Sign out</button>`;
    document.getElementById('out').onclick = async () => {
      await API.post('/api/auth/logout');
      ME = null; store.del('staff');
      go('home');
    };
    return;
  }

  const email = store.get('email', '');
  view().innerHTML = `
    <div class="card">
      <h3>Your bookings</h3>
      ${email ? `<p class="muted small">Signed in as <strong>${esc(email)}</strong></p>
        <button class="btn btn-ghost" id="forget">Use a different email</button>`
        : `<p class="muted small">We look up your cleanings by the email you booked with.</p>
           <div class="field"><input id="setEmail" type="email" placeholder="you@example.com"
             autocomplete="email"></div>
           <button class="btn btn-primary" id="saveEmail">Save</button>`}
    </div>

    <div class="card">
      <h3>Contact ${esc(CFG.short_name)}</h3>
      <div class="row"><span class="k">Phone</span>
        <a class="v" href="tel:${esc(CFG.phone_raw)}">${esc(CFG.phone)}</a></div>
      <div class="row"><span class="k">Email</span>
        <a class="v" href="mailto:${esc(CFG.email)}">${esc(CFG.email)}</a></div>
      <div class="row"><span class="k">Area</span>
        <span class="v">${esc(CFG.region)}</span></div>
    </div>

    <div class="card">
      <h3>Hours</h3>
      <div class="row"><span class="k">Residential</span><span class="v">${esc(CFG.hours.residential)}</span></div>
      <div class="row"><span class="k">Commercial</span><span class="v">${esc(CFG.hours.commercial)}</span></div>
      <div class="row"><span class="k">Rentals</span><span class="v">${esc(CFG.hours.vacation_rental)}</span></div>
    </div>

    <div class="card">
      <h3>Team sign-in</h3>
      <p class="muted small">For ${esc(CFG.short_name)} staff only.</p>
      <div id="loginErr"></div>
      <div class="field"><label for="l-email">Work email</label>
        <input id="l-email" type="email" autocomplete="username"></div>
      <div class="field"><label for="l-pw">Password</label>
        <input id="l-pw" type="password" autocomplete="current-password"></div>
      <button class="btn btn-primary" id="loginBtn">Sign in</button>
    </div>

    <p class="hint center" style="padding-bottom:10px">${esc(CFG.license)}</p>`;

  const se = document.getElementById('saveEmail');
  if (se) se.onclick = () => {
    const v = document.getElementById('setEmail').value.trim();
    if (v) { store.set('email', v); viewAccount(); }
  };
  const fg = document.getElementById('forget');
  if (fg) fg.onclick = () => { store.del('email'); viewAccount(); };

  document.getElementById('loginBtn').onclick = async () => {
    const btn = document.getElementById('loginBtn');
    const email = document.getElementById('l-email').value.trim();
    const pw = document.getElementById('l-pw').value;
    if (!email || !pw) {
      document.getElementById('loginErr').innerHTML = alertBox('bad', 'Enter your email and password.');
      return;
    }
    btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Signing in…';
    try {
      const r = await API.post('/api/auth/login', { email, password: pw });
      ME = r.staff;
      store.set('staff', ME);
      go('home');
    } catch (e) {
      document.getElementById('loginErr').innerHTML = alertBox('bad', e.message);
      btn.disabled = false; btn.textContent = 'Sign in';
    }
  };
}

/* ---------------------------------------------------------------- boot */
window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  installPrompt = e;
  if (TAB === 'home' && !ME) viewHome();
});

(async () => {
  try {
    CFG = await getConfig();
  } catch (e) {
    view().innerHTML = alertBox('bad',
      "Can't reach the server right now. Check your connection and pull to refresh.");
    return;
  }
  try {
    const r = await API.get('/api/auth/me');
    ME = r.staff;
    if (ME) store.set('staff', ME); else store.del('staff');
  } catch (e) {
    ME = store.get('staff', null);   // offline: trust the last known session
  }

  const wanted = new URLSearchParams(location.search).get('tab');
  TAB = tabs().some(t => t[0] === wanted) ? wanted : 'home';
  drawTabs();
  go(TAB);

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/app/sw.js', { scope: '/app/' }).catch(() => {});
  }
})();
