(async () => {
  const cfg = await getConfig();

  document.getElementById('contactDetails').innerHTML = `
    <p style="display:flex;gap:10px;align-items:center;margin-bottom:12px">
      ${icon('phone', 'i16')}<a href="tel:${esc(cfg.phone_raw)}"><strong>${esc(cfg.phone)}</strong></a></p>
    <p style="display:flex;gap:10px;align-items:center;margin-bottom:12px">
      ${icon('mail', 'i16')}<a href="mailto:${esc(cfg.email)}">${esc(cfg.email)}</a></p>
    <p style="display:flex;gap:10px;align-items:flex-start;margin:0">
      ${icon('pin', 'i16')}<span>${esc(cfg.city)}, ${esc(cfg.state)}<br>
      <span class="muted" style="font-size:.88rem">${esc(cfg.region)}</span></span></p>`;

  document.getElementById('hoursList').innerHTML = [
    ['Residential', cfg.hours.residential],
    ['Commercial', cfg.hours.commercial],
    ['Vacation rentals', cfg.hours.vacation_rental],
  ].map(([k, v]) => `<div style="padding:9px 0;border-bottom:1px solid var(--line)">
      <div style="font-weight:650;font-size:.9rem">${esc(k)}</div>
      <div class="muted" style="font-size:.9rem">${esc(v)}</div></div>`).join('');

  document.querySelectorAll('.i16').forEach(s => {
    s.style.width = '18px'; s.style.height = '18px';
    s.style.flexShrink = '0'; s.style.color = 'var(--teal)';
  });

  const chips = document.getElementById('areaChips');
  if (chips) chips.innerHTML = (cfg.markets || []).map(m =>
    `<span class="chip" style="font-weight:650;background:var(--teal-50);
      border-color:var(--teal-200)">${esc(m.name)}</span>` +
    m.areas.filter(a => a !== m.name)
      .map(a => `<span class="chip">${esc(a)}</span>`).join('')).join('');
  const note = document.getElementById('areaNote');
  if (note) note.textContent = cfg.service_area_note;

  const form = document.getElementById('contactForm'),
        msg = document.getElementById('contactMsg'),
        btn = document.getElementById('cfBtn');

  form.addEventListener('submit', async e => {
    e.preventDefault();
    msg.innerHTML = '';
    const body = {
      name: form.name.value.trim(), email: form.email.value.trim(),
      phone: form.phone.value.trim(), kind: form.kind.value,
      message: form.message.value.trim(),
    };
    if (!body.name || !body.email || !body.message) {
      msg.innerHTML = `<div class="alert alert-bad">${icon('alert')}
        <span>Please fill in your name, email and a message.</span></div>`;
      return;
    }
    btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Sending…';
    try {
      const r = await API.post('/api/leads', body);
      form.innerHTML = `<div class="alert alert-ok">${icon('check')}
        <span><strong>Message sent.</strong> ${esc(r.message)}</span></div>
        <p>In the meantime you can <a href="/book">get an instant price</a> for
        standard home cleaning.</p>`;
    } catch (err) {
      msg.innerHTML = `<div class="alert alert-bad">${icon('alert')}<span>${esc(err.message)}</span></div>`;
      btn.disabled = false; btn.textContent = 'Send message';
    }
  });
})();
