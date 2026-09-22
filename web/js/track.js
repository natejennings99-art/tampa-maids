(async () => {
  const cfg = await getConfig();
  const form = document.getElementById('trackForm'),
        msg = document.getElementById('trackMsg'),
        out = document.getElementById('trackResult'),
        btn = document.getElementById('tfBtn');

  const params = new URLSearchParams(location.search);
  if (params.get('ref')) document.getElementById('tf-ref').value = params.get('ref');
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
         ['Crew', b.assigned_name || 'Being assigned'],
         ['Checklist', b.tasks_done + ' of ' + b.tasks_total + ' complete']]
        .map(([k, v]) => `<div style="display:flex;justify-content:space-between;gap:14px;
          padding:11px 0;border-bottom:1px solid var(--line);font-size:.95rem">
          <span class="muted">${esc(k)}</span>
          <strong style="text-align:right">${esc(v)}</strong></div>`).join('')}
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
