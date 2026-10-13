/* Applications from the work-with-us page.
   Posts to /api/leads with kind="applicant" so an application lands in the same
   place as every other enquiry and triggers the same owner alert -- recruiting
   was entirely manual outreach before this, and an application that nobody sees
   is worse than no application form at all. */
(function () {
  const form = document.getElementById('applyForm');
  if (!form) return;
  const msg = document.getElementById('applyMsg');
  const btn = document.getElementById('applyBtn');
  const v = id => (document.getElementById(id) || {}).value || '';

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const name = v('a-name').trim(), email = v('a-email').trim(), phone = v('a-phone').trim();
    if (!name || !email || !phone) {
      msg.textContent = 'Name, mobile and email are all needed so we can reply.';
      return;
    }
    btn.disabled = true;
    msg.textContent = 'Sending…';
    try {
      const r = await API.post('/api/leads', {
        name, email, phone, kind: 'applicant',
        message: 'AREAS: ' + (v('a-area') || 'not given') +
                 '\nEXPERIENCE / INSURANCE / AVAILABILITY: ' + (v('a-exp') || 'not given'),
      });
      form.reset();
      msg.textContent = r.message || 'Thanks — we reply to everyone.';
    } catch (err) {
      /* Never swallow it silently: a cleaner who thinks they applied and hears
         nothing is one we lose twice. */
      btn.disabled = false;
      msg.textContent = 'That did not send. Please call ' +
        (window.CFG && CFG.phone ? CFG.phone : 'us') + ' instead.';
    }
  });
})();
