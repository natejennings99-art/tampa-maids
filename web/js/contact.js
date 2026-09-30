(() => {
  /* Contact details, hours and areas are rendered into the page (tools/inner_v2.py). */
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
