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
        <button class="btn btn-ghost" id="cancelBtn">Cancel this booking</button>
        <a class="btn btn-ghost" href="/contact" style="margin-left:8px">Reschedule</a>`}
    </div>`;

    const cb = document.getElementById('cancelBtn');
    if (cb) cb.addEventListener('click', async () => {
      if (!confirm('Cancel this cleaning? This cannot be undone.')) return;
      cb.disabled = true; cb.innerHTML = '<span class="spinner"></span> Cancelling…';
      try {
        const r = await API.post('/api/bookings/cancel',
          { ref: b.ref, email: document.getElementById('tf-email').value.trim() });
        out.innerHTML = `<div class="alert ${r.fee_applies ? 'alert-warn' : 'alert-ok'}">
          ${icon(r.fee_applies ? 'alert' : 'check')}<span>${esc(r.message)}</span></div>
          <a class="btn btn-primary" href="/book">Book a new cleaning</a>`;
      } catch (e) {
        cb.disabled = false; cb.textContent = 'Cancel this booking';
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
