/* Shared helpers for the website and phone app. */

const API = {
  async req(method, path, body) {
    const opt = { method, headers: {}, credentials: 'same-origin' };
    if (body !== undefined) {
      opt.headers['Content-Type'] = 'application/json';
      opt.body = JSON.stringify(body);
    }
    let res;
    try {
      res = await fetch(path, opt);
    } catch (e) {
      throw new Error("Can't reach the server. Check your connection and try again.");
    }
    let data;
    try { data = await res.json(); }
    catch (e) { throw new Error('The server sent back an unexpected response.'); }
    if (!res.ok) throw new Error(data.error || 'Something went wrong.');
    return data;
  },
  get(p) { return this.req('GET', p); },
  post(p, b) { return this.req('POST', p, b || {}); },
};

/* business config, fetched once and cached for the session */
let _cfg = null;
async function getConfig() {
  if (_cfg) return _cfg;
  try {
    _cfg = await API.get('/api/config');
    try { localStorage.setItem('gc_cfg', JSON.stringify(_cfg)); } catch (e) {}
  } catch (e) {
    try { _cfg = JSON.parse(localStorage.getItem('gc_cfg') || 'null'); } catch (e2) {}
    if (!_cfg) throw e;
  }
  return _cfg;
}

const money = c => '$' + (c / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const money0 = c => '$' + Math.round(c / 100).toLocaleString('en-US');

function fmtDate(iso, opts) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('en-US',
    opts || { weekday: 'short', month: 'short', day: 'numeric' });
}
function fmtDateLong(iso) {
  return fmtDate(iso, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
}

const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g,
  c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/* ---- icons ---- */
const ICONS = {
  check: '<path d="M20 6L9 17l-5-5"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
  tag: '<path d="M20.6 13.4L12 22l-9-9V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"/><circle cx="7.5" cy="7.5" r="1.5" fill="currentColor"/>',
  refresh: '<path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 3v6h-6"/>',
  leaf: '<path d="M11 20A7 7 0 0 1 4 13c0-6 8-10 16-10 0 8-4 16-10 16z"/><path d="M4 21c3-6 7-9 12-11"/>',
  camera: '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/>',
  pin: '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
  home: '<path d="M3 10l9-7 9 7v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/>',
  sparkle: '<path d="M12 2l2.2 6.3L20.5 10l-6.3 2.2L12 18.5l-2.2-6.3L3.5 10l6.3-1.7z"/><path d="M19 15l.9 2.4L22 18l-2.1.8L19 21l-.9-2.2L16 18l2.1-.6z"/>',
  box: '<path d="M21 8l-9-5-9 5v8l9 5 9-5z"/><path d="M3 8l9 5 9-5"/><path d="M12 13v8"/>',
  key: '<circle cx="8" cy="15" r="5"/><path d="M11.6 11.4L21 2m-4 3l2.5 2.5M14 8l2.5 2.5"/>',
  building: '<path d="M4 22V4a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v18"/><path d="M15 9h4a1 1 0 0 1 1 1v12"/><path d="M2 22h20"/><path d="M8 7h3M8 11h3M8 15h3"/>',
  tool: '<path d="M14.7 6.3a4 4 0 0 1 5 5l-9.6 9.6a2.1 2.1 0 0 1-3-3z"/><path d="M18 2l4 4-2 2-4-4z"/>',
  phone: '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2 4.2 2 2 0 0 1 4 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.4 2.1L8 10a16 16 0 0 0 6 6l1.4-1.3a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>',
  mail: '<path d="M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/><path d="M22 6l-10 7L2 6"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  cal: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  star: '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.9L12 17.8 5.8 21l1.2-6.9-5-4.9 6.9-1z"/>',
  arrow: '<path d="M5 12h14M12 5l7 7-7 7"/>',
  alert: '<circle cx="12" cy="12" r="10"/><path d="M12 8v5M12 16.5v.01"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5M21 12H9"/>',
  list: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
  chart: '<path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/>',
};
function icon(name, cls) {
  const p = ICONS[name] || ICONS.check;
  return `<svg class="${cls || ''}" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${p}</svg>`;
}

/* fill <span data-biz="phone"> etc. from config; keeps business.json authoritative */
function hydrateBiz(cfg) {
  document.querySelectorAll('[data-biz]').forEach(el => {
    const key = el.dataset.biz;
    const val = key.split('.').reduce((o, k) => (o == null ? o : o[k]), cfg);
    if (val == null) return;
    if (el.tagName === 'A') {
      el.textContent = val;
      if (key === 'phone') el.href = 'tel:' + cfg.phone_raw;
      if (key === 'email') el.href = 'mailto:' + cfg.email;
    } else el.textContent = val;
  });
  document.querySelectorAll('[data-biz-href="phone"]').forEach(a => a.href = 'tel:' + cfg.phone_raw);
  document.querySelectorAll('[data-biz-href="email"]').forEach(a => a.href = 'mailto:' + cfg.email);
}

/* mobile nav + active link */
function initHeader() {
  const btn = document.querySelector('.menu-btn'), nav = document.querySelector('.nav');
  if (btn && nav) btn.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    btn.setAttribute('aria-expanded', open);
  });
  const here = location.pathname.replace(/\/$/, '') || '/index.html';
  document.querySelectorAll('.nav a').forEach(a => {
    const href = a.getAttribute('href');
    if (href && (here.endsWith(href.replace('/', '')) || (href === '/' && here === '/index.html')))
      a.classList.add('active');
  });
}

function stars(n) {
  return '<span class="stars" aria-label="' + n + ' out of 5 stars">' + '★'.repeat(n) + '</span>';
}
