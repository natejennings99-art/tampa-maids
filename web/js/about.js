(async () => {
  const cfg = await getConfig();
  document.getElementById('mission').textContent = cfg.mission;

  document.getElementById('glance').innerHTML = [
    ['Founded', cfg.founded],
    ['Based in', cfg.city + ', ' + cfg.state],
    ['Serving', cfg.service_area.length + ' Tampa Bay communities'],
    ['Team', 'W-2 employees, background-checked'],
    ['Insurance', '$1M/$2M liability + $25,000 bond'],
    ['Products', 'EPA Safer Choice certified'],
  ].map(([k, v]) => `<div style="display:flex;justify-content:space-between;gap:14px;
      padding:9px 0;border-bottom:1px solid var(--line);font-size:.92rem">
      <span class="muted">${esc(k)}</span><strong style="text-align:right">${esc(v)}</strong></div>`)
    .join('');

  document.getElementById('values').innerHTML = cfg.values.map((v, i) =>
    `<div class="card"><div class="icon-badge">${icon(['shield', 'user', 'tag', 'leaf'][i] || 'check')}</div>
     <h3>${esc(v.title)}</h3><p>${esc(v.text)}</p></div>`).join('');

  document.getElementById('segTable').innerHTML =
    `<thead><tr><th>Who</th><th>Typical job</th><th>How often</th></tr></thead>
     <tbody>${cfg.segments.map(s => `<tr>
       <td><strong>${esc(s.name)}</strong><br>
         <span class="muted" style="font-size:.86rem">${esc(s.profile)}</span></td>
       <td class="amt">${esc(s.typical)}</td><td>${esc(s.frequency)}</td></tr>`).join('')}</tbody>`;
})();
