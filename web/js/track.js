(async () => {
  const cfg = await getConfig();
  const form = document.getElementById('trackForm'),
        msg = document.getElementById('trackMsg'),
        out = document.getElementById('trackResult'),
        btn = document.getElementById('tfBtn');

  const params = new URLSearchParams(location.search);
  if (params.get('ref')) document.getElementById('tf-ref').value = params.get('ref');
  // Back from Stripe: ask the server to check the session with Stripe itself.
  if (params.get('session_id')) {
    try {
      const r = await API.get('/api/payments/return?session_id=' +
                              encodeURIComponent(params.get('session_id')));
      // Once per Stripe session, so a reload doesn't count the sale twice.
      const seen = 'tm_tracked_' + params.get('session_id');
      let fresh = true;
      try { fresh = !sessionStorage.getItem(seen); sessionStorage.setItem(seen, '1'); } catch (e) {}
      if (fresh && r.result === 'paid') tmTrack('purchase', r.amount_cents, r.ref);
      if (fresh && r.result === 'card_saved') tmTrack('card', 0, r.ref);
      msg.innerHTML = `<div class="alert alert-ok">${icon('check')}<span>${
        r.result === 'paid' ? 'Payment received. Thank you!' :
        r.result === 'card_saved' ? "Card saved. Nothing has been charged; we'll charge it after your cleaning." :
        'Thanks, we are confirming that with the bank.'}</span></div>`;
    } catch (e) {
      msg.innerHTML = `<div class="alert alert-warn">${icon('alert')}<span>${esc(e.message)}</span></div>`;
    }
  } else if (params.get('card') === 'skipped') {
    msg.innerHTML = `<div class="alert alert-info">${icon('alert')}<span>No card saved. That's fine, we'll confirm how you'd like to pay before your visit.</span></div>`;
  }
  try {
    const saved = localStorage.getItem('gc_email');
    if (saved) document.getElementById('tf-email').value = saved;
  } catch (e) {}

  const STATUS = {
    requested: ['pill-warn', 'Awaiting confirmation'],
    confirmed: ['pill-info', 'Confirmed'],
    in_progress: ['pill-info', 'Crew on site'],
    completed: ['pill-ok', 'Completed'],
    cancelled: ['pill-grey', 'Cancelled'],
  };

  function show(b) {
    const [cls, label] = STATUS[b.status] || ['pill-grey', b.status];
    out.innerHTML = `<div class="card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:14px;
        flex-wrap:wrap;margin-bottom:18px">
        <div><h2 style="margin:0 0 4px;font-size:1.45rem">${esc(b.service)}</h2>
          <p class="muted" style="margin:0;font-size:.9rem">Reference ${esc(b.ref)}</p></div>
        <span class="pill ${cls}">${esc(label)}</span>
      </div>
      ${[['When', fmtDateLong(b.date) + ' · ' + b.slot],
         ['Address', b.customer.address + ', ' + b.customer.city],
         ['Total', money(b.total)],
         ...(b.payment_status === 'paid' ? [['Payment', 'Paid ' + money(b.paid_cents || b.total)]] :
             b.payment_status === 'card_saved' ? [['Payment', 'Card on file, charged after the clean']] : []),
         ['Crew', b.assigned_name || 'Being assigned'],
         ['Checklist', b.tasks_done + ' of ' + b.tasks_total + ' complete']]
        .map(([k, v]) => `<div style="display:flex;justify-content:space-between;gap:14px;
          padding:11px 0;border-bottom:1px solid var(--line);font-size:.95rem">
          <span class="muted">${esc(k)}</span>
          <strong style="text-align:right">${esc(v)}</strong></div>`).join('')}
      ${b.pay_link_url && b.payment_status !== 'paid' ? `
        <a class="btn btn-primary" style="margin-top:18px" href="${esc(b.pay_link_url)}">Pay ${money(b.total)} by card</a>` : ''}
      ${b.status === 'completed' || b.status === 'cancelled' ? '' : `
        <div class="alert alert-info" style="margin-top:20px">${icon('alert')}
          <span>${esc(cfg.booking.cancellation_policy)}</span></div>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          ${b.can_change ? `<button class="btn btn-ghost" id="moveBtn">Reschedule</button>` :
            `<a class="btn btn-ghost" href="tel:${esc(cfg.phone_raw || '')}">Call to reschedule</a>`}
          ${b.can_skip ? `<button class="btn btn-ghost" id="skipBtn">Skip this visit</button>` : ''}
          <button class="btn btn-ghost" id="cancelBtn">${b.can_skip ? 'Cancel and end my plan' : 'Cancel this booking'}</button>
        </div>
        <div id="movePanel" hidden style="margin-top:16px">
          <label class="muted" for="mv-date" style="display:block;font-size:.9rem">New date</label>
          <input type="date" id="mv-date" class="input" style="margin:4px 0 10px">
          <div id="mv-slots" style="display:flex;flex-wrap:wrap;gap:8px"></div>
        </div>`}
    </div>`;
    const email = () => document.getElementById('tf-email').value.trim();
    const done = (r, warn) => {
      out.innerHTML = `<div class="alert ${warn ? 'alert-warn' : 'alert-ok'}">
        ${icon(warn ? 'alert' : 'check')}<span>${esc(r.message)}</span></div>`;
    };
    const fail = e => out.insertAdjacentHTML('afterbegin',
      `<div class="alert alert-bad">${icon('alert')}<span>${esc(e.message)}</span></div>`);

    const sb = document.getElementById('skipBtn');
    if (sb) sb.addEventListener('click', async () => {
      if (!confirm('Skip this visit? Your plan continues and the next one is booked for you.')) return;
      sb.disabled = true; sb.innerHTML = '<span class="spinner"></span> Skipping…';
      try { done(await API.post('/api/bookings/skip', { ref: b.ref, email: email() })); }
      catch (e) { sb.disabled = false; sb.textContent = 'Skip this visit'; fail(e); }
    });

    const mb = document.getElementById('moveBtn');
    if (mb) {
      const panel = document.getElementById('movePanel'),
            di = document.getElementById('mv-date'),
            slots = document.getElementById('mv-slots');
      mb.addEventListener('click', () => { panel.hidden = !panel.hidden; if (!panel.hidden) di.focus(); });
      di.addEventListener('change', async () => {
        slots.innerHTML = '<span class="spinner"></span>';
        try {
          const a = await API.get(`/api/availability?date=${encodeURIComponent(di.value)}` +
                                  `&service=${encodeURIComponent(b.service_id)}`);
          slots.innerHTML = a.open && (a.slots || []).length ? a.slots.map(s =>
            `<button class="btn btn-ghost" data-slot="${esc(s)}">${esc(s)}</button>`).join('') :
            `<span class="muted">${esc(a.reason || 'No times free that day')}. Try another date.</span>`;
        } catch (e) { slots.innerHTML = `<span class="muted">${esc(e.message)}</span>`; }
      });
      slots.addEventListener('click', async e => {
        const t = e.target.closest('[data-slot]');
        if (!t) return;
        t.disabled = true; t.innerHTML = '<span class="spinner"></span>';
        try {
          done(await API.post('/api/bookings/reschedule',
            { ref: b.ref, email: email(), date: di.value, slot: t.dataset.slot }));
        } catch (err) { t.disabled = false; t.textContent = t.dataset.slot; fail(err); }
      });
    }

    const cb = document.getElementById('cancelBtn');
    if (cb) cb.addEventListener('click', async () => {
      if (!confirm(b.can_skip ? 'Cancel this visit and end your plan? To keep your plan, use Skip this visit instead.' :
                   'Cancel this cleaning? This cannot be undone.')) return;
      cb.disabled = true; cb.innerHTML = '<span class="spinner"></span> Cancelling…';
      try {
        const r = await API.post('/api/bookings/cancel',
          { ref: b.ref, email: document.getElementById('tf-email').value.trim() });
        out.innerHTML = `<div class="alert ${r.fee_applies ? 'alert-warn' : 'alert-ok'}">
          ${icon(r.fee_applies ? 'alert' : 'check')}<span>${esc(r.message)}</span></div>
          <a class="btn btn-primary" href="/book">Book a new cleaning</a>`;
      } catch (e) {
        cb.disabled = false; cb.textContent = b.can_skip ? 'Cancel and end my plan' : 'Cancel this booking';
        out.insertAdjacentHTML('afterbegin',
          `<div class="alert alert-bad">${icon('alert')}<span>${esc(e.message)}</span></div>`);
      }
    });
  }

  form.addEventListener('submit', async e => {
    e.preventDefault();
    msg.innerHTML = ''; out.innerHTML = '';
    const ref = document.getElementById('tf-ref').value.trim().toUpperCase();
    const email = document.getElementById('tf-email').value.trim();
    if (!ref || !email) {
      msg.innerHTML = `<div class="alert alert-bad">${icon('alert')}
        <span>Enter both your reference and email.</span></div>`;
      return;
    }
    btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Looking up…';
    try {
      show(await API.get(
        `/api/bookings/track?ref=${encodeURIComponent(ref)}&email=${encodeURIComponent(email)}`));
    } catch (err) {
      msg.innerHTML = `<div class="alert alert-bad">${icon('alert')}<span>${esc(err.message)}</span></div>`;
    }
    btn.disabled = false; btn.textContent = 'Find my booking';
  });

  if (params.get('ref')) form.dispatchEvent(new Event('submit'));
})();
