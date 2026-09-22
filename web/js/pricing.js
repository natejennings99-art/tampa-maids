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

  document.getElementById('flatGrid').innerHTML = cfg.services
    .filter(s => s.kind === 'flat').map(s =>
      `<div class="card"><div class="icon-badge">${icon(s.icon)}</div>
       <h3>${esc(s.name)}</h3>
       <p style="font-family:var(--display);font-size:1.7rem;color:var(--teal-dark);
          font-weight:600;margin:.2em 0">${money0(s.price_min)}–${money0(s.price_max)}</p>
       <p>${esc(s.blurb)}</p>
       <a class="btn btn-ghost btn-sm" style="margin-top:16px" href="/book?service=${s.id}">Get a price</a>
      </div>`).join('');

  const comm = cfg.services.find(s => s.kind === 'commercial');
  document.getElementById('commTable').innerHTML =
    `<thead><tr><th>Client type</th><th>Rate structure</th><th>Typical monthly</th></tr></thead>
     <tbody>${comm.rates.map(r => `<tr>
       <td><strong>${esc(r.name)}</strong><br>
         <span class="muted" style="font-size:.85rem">${esc(r.detail)}</span></td>
       <td class="amt">${r.per_sqft_min
         ? '$' + (r.per_sqft_min / 100).toFixed(2) + '–$' + (r.per_sqft_max / 100).toFixed(2) + ' / sq ft / visit'
         : money0(r.flat_min) + '–' + money0(r.flat_max) + ' per visit'}</td>
       <td>${esc(r.typical_monthly)}</td></tr>`).join('')}</tbody>`;
  document.getElementById('commNote').textContent =
    comm.contract_note + ' ' + cfg.pricing.tax_note;

  document.getElementById('incGrid').innerHTML = cfg.guarantees.map(g =>
    `<div class="card" style="background:#fff"><div class="icon-badge">${icon(g.icon)}</div>
     <h3>${esc(g.title)}</h3><p>${esc(g.text)}</p></div>`).join('');
})();
