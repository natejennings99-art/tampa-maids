(async () => {
  const cfg = await getConfig();
  const lowest = Math.min(...cfg.home_tiers.filter(t => t.prices)
    .map(t => Math.min(...Object.values(t.prices))));

  document.getElementById('svcDetail').innerHTML = cfg.services.map((s, i) => {
    let price;
    if (s.kind === 'residential') price = `From <strong>${money0(lowest)}</strong> per visit`;
    else if (s.kind === 'commercial') price = 'Contracted per square foot';
    else price = `<strong>${money0(s.price_min)}–${money0(s.price_max)}</strong> flat`;

    const rates = s.rates ? `<div class="table-scroll" style="margin-top:18px">
      <table class="ptable"><thead><tr><th>Space</th><th>Rate</th><th>Typical monthly</th></tr></thead>
      <tbody>${s.rates.map(r => `<tr><td><strong>${esc(r.name)}</strong><br>
        <span class="muted" style="font-size:.85rem">${esc(r.detail)}</span></td>
        <td class="amt">${r.per_sqft_min
          ? '$' + (r.per_sqft_min / 100).toFixed(2) + '–$' + (r.per_sqft_max / 100).toFixed(2) + ' / sq ft'
          : money0(r.flat_min) + '–' + money0(r.flat_max) + ' / visit'}</td>
        <td>${esc(r.typical_monthly)}</td></tr>`).join('')}</tbody></table></div>` : '';

    return `<article id="${s.id}" style="scroll-margin-top:96px;padding:38px 0;
      ${i ? 'border-top:1px solid var(--line)' : ''}">
      <div class="grid grid-2" style="gap:44px;align-items:start">
        <div>
          <div class="icon-badge">${icon(s.icon)}</div>
          <h2 style="margin-bottom:.2em">${esc(s.name)}</h2>
          <p class="lede" style="font-size:1.05rem">${esc(s.blurb)}</p>
          <p class="muted" style="font-size:.92rem">${icon('clock', 'ico')} ${esc(s.duration_note)}</p>
          ${s.audience ? `<p class="muted" style="font-size:.92rem">${icon('user', 'ico')} ${esc(s.audience)}</p>` : ''}
          <p style="margin-top:16px;font-size:1.02rem">${price}</p>
          <div class="btn-row" style="margin-top:18px">
            <a class="btn btn-primary" href="/book?service=${s.id}">Get a price</a>
            ${s.kind === 'commercial'
              ? '<a class="btn btn-ghost" href="/contact">Request a walkthrough</a>' : ''}
          </div>
        </div>
        <div class="card" style="background:var(--sand);border:0">
          <h3>What's included</h3>
          <ul class="svc-list">${s.includes.map(x =>
            `<li>${icon('check')}<span>${esc(x)}</span></li>`).join('')}</ul>
          ${s.contract_note ? `<p class="hint" style="margin-top:16px">${esc(s.contract_note)}</p>` : ''}
        </div>
      </div>${rates}</article>`;
  }).join('');

  document.querySelectorAll('.ico').forEach(s => {
    s.style.width = '15px'; s.style.height = '15px';
    s.style.display = 'inline-block'; s.style.verticalAlign = '-2px';
  });

  document.getElementById('addonGrid').innerHTML = cfg.addons.map(a =>
    `<div class="card" style="padding:20px">
      <div style="font-weight:650;font-size:.98rem">${esc(a.name)}</div>
      <div style="color:var(--teal-dark);font-weight:700;font-size:1.15rem;margin-top:6px">
        +${money0(a.price)}</div>
      ${a.minutes ? `<div class="muted" style="font-size:.83rem">about ${a.minutes} min</div>` : ''}
    </div>`).join('');

  /* deep-link to a service section */
  if (location.hash) {
    const el = document.querySelector(location.hash);
    if (el) setTimeout(() => el.scrollIntoView({ behavior: 'smooth', block: 'start' }), 80);
  }
})();
