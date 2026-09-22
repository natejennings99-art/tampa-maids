(async () => {
  const cfg = await getConfig();

  document.getElementById('heroPoints').innerHTML = [
    'Flat price quoted upfront, never by the hour',
    'Background-checked W-2 employees, never gig workers',
    'Free re-clean within 24 hours if anything is off',
    'Same crew every visit on recurring plans',
  ].map(t => `<li>${icon('check')}<span>${t}</span></li>`).join('');

  /* live mini-quote in the hero */
  const tiers = cfg.home_tiers.filter(t => !t.custom_quote);
  const q = document.getElementById('heroQuote');
  q.innerHTML = `
    <h3>What will it cost?</h3>
    <p class="sub">Real numbers from our published price list.</p>
    <div class="field">
      <label for="hq-tier">Your home</label>
      <select id="hq-tier">${tiers.map(t =>
        `<option value="${t.id}">${esc(t.name)} — ${esc(t.detail)}</option>`).join('')}</select>
    </div>
    <div class="field">
      <label for="hq-freq">How often</label>
      <select id="hq-freq">${cfg.frequencies.map(f =>
        `<option value="${f.id}"${f.default ? ' selected' : ''}>${esc(f.name)}</option>`).join('')}</select>
    </div>
    <div class="price-readout">
      <div><div class="cap">Per visit</div><div class="amt" id="hq-amt">—</div></div>
      <div style="text-align:right"><div class="cap" id="hq-cap"></div></div>
    </div>
    <a class="btn btn-primary" href="/book" style="width:100%">Get my exact price</a>
    <p class="hint center" style="margin-top:10px">No card. No obligation.</p>`;

  const tierSel = document.getElementById('hq-tier'),
        freqSel = document.getElementById('hq-freq'),
        amt = document.getElementById('hq-amt'),
        cap = document.getElementById('hq-cap');

  function update() {
    const t = tiers.find(x => x.id === tierSel.value);
    const f = freqSel.value;
    amt.textContent = money0(t.prices[f]);
    cap.textContent = f === 'once' ? 'One-time deep clean' : 'Recurring rate';
  }
  tierSel.onchange = freqSel.onchange = update;
  update();

  /* services */
  document.getElementById('svcGrid').innerHTML = cfg.services.map(s => {
    let from = '';
    if (s.kind === 'residential') {
      const lo = Math.min(...cfg.home_tiers.filter(t => t.prices)
        .map(t => Math.min(...Object.values(t.prices))));
      from = `From ${money0(lo)} per visit`;
    } else if (s.price_min) from = `${money0(s.price_min)}–${money0(s.price_max)}`;
    else from = 'Quoted per contract';
    return `<a class="card card-hover svc-card" href="/services#${s.id}" style="text-decoration:none;color:inherit">
      <div class="icon-badge">${icon(s.icon)}</div>
      <h3>${esc(s.name)}</h3>
      <p>${esc(s.blurb)}</p>
      <div class="price-from">${from} ${icon('arrow', 'inline-arrow')}</div></a>`;
  }).join('');
  document.querySelectorAll('.inline-arrow').forEach(s => {
    s.style.width = '15px'; s.style.height = '15px';
    s.style.display = 'inline-block'; s.style.verticalAlign = '-2px';
  });

  /* guarantees */
  document.getElementById('guarantees').innerHTML = cfg.guarantees.map(g =>
    `<div class="card"><div class="icon-badge amber">${icon(g.icon)}</div>
     <h3>${esc(g.title)}</h3><p>${esc(g.text)}</p></div>`).join('');

  /* testimonials */
  document.getElementById('testimonials').innerHTML = cfg.testimonials.slice(0, 6).map(t =>
    `<figure class="quote-tile" style="margin:0">${stars(t.rating)}
     <p>&ldquo;${esc(t.text)}&rdquo;</p>
     <figcaption class="quote-who">${esc(t.name)}<span>${esc(t.location)}</span></figcaption>
     </figure>`).join('');

  /* service area, grouped by market */
  document.getElementById('areaNote').textContent = cfg.service_area_note;
  const slug = n => n.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  document.getElementById('marketGrid').innerHTML = (cfg.markets || []).map(m => `
    <a class="card card-hover" href="/cleaning/${slug(m.name)}"
       style="text-decoration:none;color:inherit;background:#fff">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
        <h3 style="margin:0">${esc(m.name)}</h3>
        ${m.home_base ? '<span class="pill pill-info">Home base</span>' : ''}
      </div>
      <p style="font-size:.9rem;margin-bottom:12px">${esc(m.blurb)}</p>
      <div class="chips">${m.areas.filter(a => a !== m.name)
        .map(a => `<span class="chip" style="font-size:.8rem">${esc(a)}</span>`).join('')}</div>
      <div class="price-from" style="font-size:.88rem">Cleaning in ${esc(m.name)} &rarr;</div>
    </a>`).join('');
})();
