/* Shared renderer for the per-market local-SEO landing pages. */
(async () => {
  const cfg = await getConfig();
  const freqs = cfg.frequencies;

  document.getElementById('tierTable').innerHTML =
    `<thead><tr><th>Home size</th>${freqs.map(f =>
      `<th>${esc(f.name)}${f.default ? '<br><span style="font-weight:600;color:var(--teal)">Most popular</span>' : ''}</th>`
    ).join('')}</tr></thead><tbody>${cfg.home_tiers.map(t =>
      `<tr><td><strong>${esc(t.name)}</strong><br>
        <span class="muted" style="font-size:.85rem">${esc(t.detail)}</span></td>
      ${freqs.map(f => `<td class="${f.default ? 'pop' : ''}">
        ${t.custom_quote ? '<a href="/contact">Custom quote</a>'
                         : '<span class="amt">' + money0(t.prices[f.id]) + '</span>'}</td>`).join('')}
      </tr>`).join('')}</tbody>`;
  document.getElementById('firstNote').textContent = cfg.booking.first_clean_note;

  const lowest = Math.min(...cfg.home_tiers.filter(t => t.prices)
    .map(t => Math.min(...Object.values(t.prices))));
  document.getElementById('svcGrid').innerHTML = cfg.services.map(s => {
    let from;
    if (s.kind === 'residential') from = `From ${money0(lowest)} per visit`;
    else if (s.price_min) from = `${money0(s.price_min)}–${money0(s.price_max)}`;
    else from = 'Quoted per contract';
    return `<a class="card card-hover svc-card" href="/services#${s.id}"
      style="text-decoration:none;color:inherit">
      <div class="icon-badge">${icon(s.icon)}</div>
      <h3>${esc(s.name)}</h3><p>${esc(s.blurb)}</p>
      <div class="price-from">${from}</div></a>`;
  }).join('');

  document.getElementById('guarantees').innerHTML = cfg.guarantees.slice(0, 6).map(g =>
    `<div class="card"><div class="icon-badge amber">${icon(g.icon)}</div>
     <h3>${esc(g.title)}</h3><p>${esc(g.text)}</p></div>`).join('');

  document.getElementById('faqList').innerHTML = cfg.faq.slice(0, 6).map((f, i) =>
    `<details class="faq-item"${i === 0 ? ' open' : ''}>
      <summary>${esc(f.q)}</summary><div class="a">${esc(f.a)}</div></details>`).join('');
})();
