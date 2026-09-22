/* Owner dashboard. Every screen reads from the same API the app uses. */
let CFG = null, ME = null, PAGE = 'overview', STAFF = [];

const root = () => document.getElementById('root');
const STATUS = {
  requested: ['pill-warn', 'Requested'], confirmed: ['pill-info', 'Confirmed'],
  in_progress: ['pill-info', 'In progress'], completed: ['pill-ok', 'Completed'],
  cancelled: ['pill-grey', 'Cancelled'],
};
const LOGO = `<svg viewBox="0 0 40 40" fill="none"><rect width="40" height="40" rx="11" fill="#0b6e8f"/>
  <path d="M7 26c3.2 0 3.2-3 6.4-3s3.2 3 6.4 3 3.2-3 6.4-3 3.2 3 6.4 3" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>
  <path d="M20 8.5l1.9 4.4 4.4 1.9-4.4 1.9L20 21.1l-1.9-4.4-4.4-1.9 4.4-1.9z" fill="#f2a541"/></svg>`;

const openModal = html => {
  document.getElementById('modalBox').innerHTML = html;
  document.getElementById('modal').classList.add('open');
};
const closeModal = () => document.getElementById('modal').classList.remove('open');
document.getElementById('modal').addEventListener('click', e => {
  if (e.target.id === 'modal') closeModal();
});

/* ---------------------------------------------------------------- login */
function loginScreen(msg) {
  root().innerHTML = `<div class="login-wrap"><form class="login" id="lf">
    <div style="width:44px;margin-bottom:16px">${LOGO}</div>
    <h1>${esc(CFG.short_name)} Dashboard</h1>
    <p>Sign in with your staff account.</p>
    ${msg ? `<div class="alert alert-bad">${esc(msg)}</div>` : ''}
    <div class="field"><label for="e">Email</label>
      <input id="e" type="email" autocomplete="username" required></div>
    <div class="field"><label for="p">Password</label>
      <input id="p" type="password" autocomplete="current-password" required></div>
    <button class="btn btn-primary" style="width:100%" id="lb">Sign in</button>
    <p class="muted small" style="margin:16px 0 0;text-align:center">
      Crew members can use the <a href="/app">phone app</a> instead.</p>
  </form></div>`;

  document.getElementById('lf').onsubmit = async ev => {
    ev.preventDefault();
    const b = document.getElementById('lb');
    b.disabled = true; b.innerHTML = '<span class="spinner"></span>';
    try {
      const r = await API.post('/api/auth/login', {
        email: document.getElementById('e').value.trim(),
        password: document.getElementById('p').value,
      });
      ME = r.staff;
      if (!['owner', 'lead'].includes(ME.role)) {
        await API.post('/api/auth/logout'); ME = null;
        return loginScreen('That account is a crew account — please use the phone app.');
      }
      shell(); nav('overview');
    } catch (e) { loginScreen(e.message); }
  };
}

/* ---------------------------------------------------------------- shell */
function shell() {
  const items = [
    ['overview', 'Overview', 'chart'], ['bookings', 'Bookings', 'list'],
    ['schedule', 'Schedule', 'cal'], ['leads', 'Leads', 'mail'],
    ['team', 'Team', 'user'],
  ];
  root().innerHTML = `<div class="shell">
    <aside class="side">
      <div class="brand">${LOGO}<span>${esc(CFG.short_name)}</span></div>
      ${items.map(([id, label, ic]) =>
        `<button data-nav="${id}">${icon(ic)}<span>${esc(label)}</span>
         <span class="badge" id="badge-${id}" hidden></span></button>`).join('')}
      <div class="spacer"></div>
      <div class="who">${esc(ME.name)}<br><span style="text-transform:capitalize">${esc(ME.role)}</span></div>
      <button id="signout">${icon('logout')}<span>Sign out</span></button>
    </aside>
    <div class="main" id="main"></div></div>`;

  document.querySelectorAll('[data-nav]').forEach(b =>
    b.onclick = () => nav(b.dataset.nav));
  document.getElementById('signout').onclick = async () => {
    await API.post('/api/auth/logout'); ME = null; loginScreen();
  };
}

function nav(page) {
  PAGE = page;
  document.querySelectorAll('[data-nav]').forEach(b =>
    b.classList.toggle('on', b.dataset.nav === page));
  ({ overview: pageOverview, bookings: pageBookings, schedule: pageSchedule,
     leads: pageLeads, team: pageTeam }[page])();
}

const head = (title, sub, right) => `<div class="head">
  <div><h1>${esc(title)}</h1><div class="sub">${esc(sub)}</div></div>
  <div class="btn-row">${right || ''}</div></div>`;

/* ---------------------------------------------------------------- overview */
async function pageOverview() {
  const m = document.getElementById('main');
  m.innerHTML = '<div class="boot">Loading…</div>';
  try {
    const o = await API.get('/api/admin/overview');
    const svcName = id => (CFG.services.find(s => s.id === id) || {}).name || id;
    const maxCents = Math.max(1, ...o.next_7_days.map(d => d.cents));

    /* fill the next 7 calendar days so gaps are visible, not hidden */
    const days = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(o.today + 'T00:00:00');
      d.setDate(d.getDate() + i);
      const iso = d.toISOString().slice(0, 10);
      const hit = o.next_7_days.find(x => x.date === iso);
      days.push(hit || { date: iso, n: 0, cents: 0 });
    }

    m.innerHTML = head('Overview', fmtDateLong(o.today),
      '<a class="btn btn-ghost" href="/" target="_blank">View website</a>' +
      '<a class="btn btn-primary" href="/book" target="_blank">New booking</a>') + `

      <div class="stats">
        <div class="stat hl"><div class="n">${o.jobs_today}</div><div class="l">Jobs today</div></div>
        <div class="stat"><div class="n">${o.requested}</div><div class="l">Awaiting confirmation</div></div>
        <div class="stat"><div class="n">${o.unassigned}</div><div class="l">Unassigned</div></div>
        <div class="stat"><div class="n">${o.recurring_clients}</div><div class="l">Recurring clients</div></div>
        <div class="stat"><div class="n">${money0(o.booked_month_cents)}</div><div class="l">Booked this month</div></div>
        <div class="stat"><div class="n">${money0(o.completed_month_cents)}</div><div class="l">Completed this month</div></div>
      </div>

      <div class="panel">
        <div class="panel-h"><h3>Next 7 days</h3>
          <span class="muted small">${o.jobs_upcoming} upcoming jobs total</span></div>
        <div class="panel-b"><div class="bars">${days.map(d => `
          <div class="b ${d.cents ? '' : 'empty-day'}" title="${d.n} job(s)">
            <b>${d.cents ? money0(d.cents) : ''}</b>
            <div class="track"><i style="height:${d.cents ? Math.max(4, Math.round(d.cents / maxCents * 100)) : 1}%"></i></div>
            <span>${esc(fmtDate(d.date, { weekday: 'short' }))}</span>
            <span class="muted">${esc(fmtDate(d.date, { day: 'numeric' }))}</span>
          </div>`).join('')}</div></div>
      </div>

      <div class="panel">
        <div class="panel-h"><h3>Revenue by service</h3></div>
        <div class="tbl-scroll"><table>
          <thead><tr><th>Service</th><th>Jobs</th><th>Booked value</th><th>Average</th></tr></thead>
          <tbody>${o.revenue_by_service.map(r => `<tr>
            <td><strong>${esc(svcName(r.service_id))}</strong></td>
            <td>${r.n}</td><td>${money(r.cents)}</td>
            <td class="muted">${money(Math.round(r.cents / r.n))}</td></tr>`).join('')
            || '<tr><td colspan="4" class="empty">No bookings yet.</td></tr>'}</tbody>
        </table></div>
      </div>

      <div class="panel"><div class="panel-h"><h3>Needs attention</h3></div>
        <div class="panel-b">
          ${o.requested ? `<div class="alert alert-info">
            <strong>${o.requested}</strong> booking(s) still awaiting your confirmation.
            <a href="#" data-jump="requested">Review them</a></div>` : ''}
          ${o.unassigned ? `<div class="alert alert-info">
            <strong>${o.unassigned}</strong> confirmed job(s) have no crew assigned.
            <a href="#" data-jump="unassigned">Assign a crew</a></div>` : ''}
          ${o.new_leads ? `<div class="alert alert-info">
            <strong>${o.new_leads}</strong> new lead(s) waiting for a reply.
            <a href="#" data-jump="leads">Open leads</a></div>` : ''}
          ${!o.requested && !o.unassigned && !o.new_leads
            ? '<p class="muted" style="margin:0">All clear. Nothing needs you right now.</p>' : ''}
        </div></div>`;

    const b1 = document.getElementById('badge-leads');
    if (o.new_leads) { b1.hidden = false; b1.textContent = o.new_leads; }
    const b2 = document.getElementById('badge-bookings');
    if (o.requested) { b2.hidden = false; b2.textContent = o.requested; }

    document.querySelectorAll('[data-jump]').forEach(a => a.onclick = e => {
      e.preventDefault();
      const j = a.dataset.jump;
      if (j === 'leads') nav('leads');
      else { nav('bookings'); setTimeout(() => {
        const sel = document.getElementById('fStatus');
        if (sel && j === 'requested') { sel.value = 'requested'; sel.dispatchEvent(new Event('change')); }
      }, 60); }
    });
  } catch (e) {
    m.innerHTML = `<div class="alert alert-bad">${esc(e.message)}</div>`;
  }
}

/* ---------------------------------------------------------------- bookings */
async function pageBookings() {
  const m = document.getElementById('main');
  m.innerHTML = head('Bookings', 'Confirm, assign and track every job') + `
    <div class="panel"><div class="panel-b filters">
      <div class="field"><label for="fStatus">Status</label>
        <select id="fStatus">
          <option value="all">All statuses</option>
          ${Object.keys(STATUS).map(s =>
            `<option value="${s}">${esc(STATUS[s][1])}</option>`).join('')}
        </select></div>
      <div class="field"><label for="fFrom">From</label><input id="fFrom" type="date"></div>
      <div class="field"><label for="fTo">To</label><input id="fTo" type="date"></div>
      <div class="field" style="flex:1"><label for="fSearch">Search</label>
        <input id="fSearch" placeholder="Name, email, address or reference"></div>
      <button class="btn btn-ghost" id="fClear">Clear</button>
    </div></div>
    <div class="panel"><div id="bkTable"><div class="boot">Loading…</div></div></div>`;

  if (!STAFF.length) {
    try { STAFF = (await API.get('/api/admin/staff')).staff; } catch (e) {}
  }

  let timer;
  const load = async () => {
    const p = new URLSearchParams();
    const s = document.getElementById('fStatus').value;
    if (s !== 'all') p.set('status', s);
    ['From', 'To', 'Search'].forEach(k => {
      const v = document.getElementById('f' + k).value.trim();
      if (v) p.set(k.toLowerCase(), v);
    });
    const box = document.getElementById('bkTable');
    try {
      const r = await API.get('/api/admin/bookings?' + p);
      if (!r.bookings.length) {
        box.innerHTML = '<div class="empty">No bookings match those filters.</div>';
        return;
      }
      box.innerHTML = `<div class="tbl-scroll"><table>
        <thead><tr><th>When</th><th>Client</th><th>Service</th><th>Crew</th>
          <th>Total</th><th>Status</th><th></th></tr></thead>
        <tbody>${r.bookings.map(b => `<tr>
          <td><strong>${esc(fmtDate(b.date))}</strong><br>
            <span class="muted small">${esc(b.slot)}</span></td>
          <td><strong>${esc(b.customer.name)}</strong><br>
            <span class="muted small">${esc(b.customer.city)} · ${esc(b.ref)}</span></td>
          <td>${esc(b.service)}<br>
            <span class="muted small">${esc(b.frequency)}</span></td>
          <td>${b.assigned_name
              ? esc(b.assigned_name)
              : '<span class="muted small">Unassigned</span>'}</td>
          <td><strong>${money(b.total)}</strong></td>
          <td><span class="pill ${STATUS[b.status][0]}">${esc(STATUS[b.status][1])}</span></td>
          <td><button class="btn btn-ghost btn-xs" data-open="${b.id}">Manage</button></td>
        </tr>`).join('')}</tbody></table></div>`;
      document.querySelectorAll('[data-open]').forEach(btn => btn.onclick = () =>
        bookingModal(r.bookings.find(x => String(x.id) === btn.dataset.open)));
    } catch (e) {
      box.innerHTML = `<div class="alert alert-bad">${esc(e.message)}</div>`;
    }
  };

  document.getElementById('fStatus').onchange = load;
  document.getElementById('fFrom').onchange = load;
  document.getElementById('fTo').onchange = load;
  document.getElementById('fSearch').oninput = () => {
    clearTimeout(timer); timer = setTimeout(load, 320);
  };
  document.getElementById('fClear').onclick = () => {
    document.getElementById('fStatus').value = 'all';
    ['fFrom', 'fTo', 'fSearch'].forEach(id => document.getElementById(id).value = '');
    load();
  };
  load();
}

function bookingModal(b) {
  const q = b.quote || {};
  openModal(`
    <div class="modal-head">
      <div><h2>${esc(b.service)}</h2>
        <p class="muted small" style="margin:0">${esc(b.ref)} ·
          booked ${esc(b.created_at.slice(0, 10))}</p></div>
      <button class="x" onclick="closeModal()">&times;</button>
    </div>
    <div id="mErr"></div>
    <div class="kv"><span class="k">Client</span><span class="v">${esc(b.customer.name)}</span></div>
    <div class="kv"><span class="k">Contact</span>
      <span class="v"><a href="tel:${esc(b.customer.phone || '')}">${esc(b.customer.phone || '—')}</a><br>
      <a href="mailto:${esc(b.customer.email)}">${esc(b.customer.email)}</a></span></div>
    <div class="kv"><span class="k">Address</span>
      <span class="v">${esc(b.customer.address)}<br>${esc(b.customer.city)} ${esc(b.customer.zip || '')}</span></div>
    <div class="kv"><span class="k">Access</span>
      <span class="v">${esc(b.access_notes || 'Not provided')}</span></div>
    ${b.notes ? `<div class="kv"><span class="k">Client notes</span>
      <span class="v">${esc(b.notes)}</span></div>` : ''}
    <div class="kv"><span class="k">Checklist</span>
      <span class="v">${b.tasks_done} / ${b.tasks_total} complete</span></div>

    ${q.lines ? `<h3 style="margin:20px 0 6px">Quote breakdown</h3>
      ${q.lines.map(l => `<div class="kv"><span class="k">${esc(l.label)}</span>
        <span class="v">${l.amount < 0 ? '−' : ''}${money(Math.abs(l.amount))}</span></div>`).join('')}
      ${q.tax ? `<div class="kv"><span class="k">Sales tax</span>
        <span class="v">${money(q.tax)}</span></div>` : ''}
      <div class="kv"><span class="k"><strong>Total</strong></span>
        <span class="v"><strong>${money(b.total)}</strong></span></div>` : ''}

    <h3 style="margin:22px 0 10px">Manage</h3>
    <div class="field"><label for="mStatus">Status</label>
      <select id="mStatus">${Object.keys(STATUS).map(s =>
        `<option value="${s}"${s === b.status ? ' selected' : ''}>${esc(STATUS[s][1])}</option>`
      ).join('')}</select></div>
    <div class="field"><label for="mCrew">Assigned crew</label>
      <select id="mCrew"><option value="">Unassigned</option>
        ${STAFF.map(s => `<option value="${s.id}"${s.id === b.assigned_to ? ' selected' : ''}>
          ${esc(s.name)} (${esc(s.role)})</option>`).join('')}</select></div>
    <div class="btn-row" style="margin-top:18px">
      <button class="btn btn-primary" id="mSave">Save changes</button>
      <button class="btn btn-ghost" onclick="closeModal()">Cancel</button>
    </div>`);

  document.getElementById('mSave').onclick = async () => {
    const btn = document.getElementById('mSave');
    btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Saving…';
    try {
      const crew = document.getElementById('mCrew').value;
      await API.post('/api/admin/bookings/' + b.id, {
        status: document.getElementById('mStatus').value,
        assigned_to: crew ? +crew : null,
      });
      closeModal();
      nav('bookings');
    } catch (e) {
      document.getElementById('mErr').innerHTML = `<div class="alert alert-bad">${esc(e.message)}</div>`;
      btn.disabled = false; btn.textContent = 'Save changes';
    }
  };
}

/* ---------------------------------------------------------------- schedule */
async function pageSchedule() {
  const m = document.getElementById('main');
  m.innerHTML = head('Schedule', 'Block out days the team is unavailable') +
    '<div class="boot">Loading…</div>';
  try {
    const r = await API.get('/api/admin/blackouts');
    m.innerHTML = head('Schedule', 'Block out days the team is unavailable') + `
      <div class="panel">
        <div class="panel-h"><h3>Add a blocked day</h3></div>
        <div class="panel-b filters">
          <div class="field"><label for="boDate">Date</label><input id="boDate" type="date"></div>
          <div class="field" style="flex:1"><label for="boWhy">Reason</label>
            <input id="boWhy" placeholder="Training day, holiday, storm closure…"></div>
          <button class="btn btn-primary" id="boAdd">Block this day</button>
        </div>
        <div class="panel-b" style="padding-top:0">
          <p class="muted small" style="margin:0">Blocked days disappear from the public booking
          calendar immediately. Existing bookings on that day are not cancelled.</p></div>
      </div>
      <div class="panel">
        <div class="panel-h"><h3>Blocked days</h3></div>
        ${r.blackouts.length ? `<div class="tbl-scroll"><table>
          <thead><tr><th>Date</th><th>Reason</th><th></th></tr></thead>
          <tbody>${r.blackouts.map(b => `<tr>
            <td><strong>${esc(fmtDateLong(b.date))}</strong></td>
            <td>${esc(b.reason || '—')}</td>
            <td><button class="btn btn-danger btn-xs" data-del="${esc(b.date)}">Remove</button></td>
          </tr>`).join('')}</tbody></table></div>`
          : '<div class="empty">No blocked days. The calendar is fully open.</div>'}
      </div>
      <div class="panel">
        <div class="panel-h"><h3>Standing hours</h3></div>
        <div class="panel-b">
          <div class="kv"><span class="k">Residential</span>
            <span class="v">${esc(CFG.hours.residential)}</span></div>
          <div class="kv"><span class="k">Commercial</span>
            <span class="v">${esc(CFG.hours.commercial)}</span></div>
          <div class="kv"><span class="k">Vacation rentals</span>
            <span class="v">${esc(CFG.hours.vacation_rental)}</span></div>
          <div class="kv"><span class="k">Arrival windows</span>
            <span class="v">${esc(CFG.booking.time_slots.join(', '))}</span></div>
          <div class="kv"><span class="k">Capacity per window</span>
            <span class="v">${CFG.booking.max_jobs_per_slot} jobs</span></div>
          <p class="muted small" style="margin:14px 0 0">These come from
          <code>business.json</code>. Edit that file and restart the server to change them.</p>
        </div>
      </div>`;

    document.getElementById('boAdd').onclick = async () => {
      const d = document.getElementById('boDate').value;
      if (!d) return alert('Pick a date first.');
      try {
        await API.post('/api/admin/blackouts',
          { date: d, reason: document.getElementById('boWhy').value.trim() });
        nav('schedule');
      } catch (e) { alert(e.message); }
    };
    document.querySelectorAll('[data-del]').forEach(b => b.onclick = async () => {
      try { await API.post('/api/admin/blackouts/delete', { date: b.dataset.del }); nav('schedule'); }
      catch (e) { alert(e.message); }
    });
  } catch (e) {
    m.innerHTML = `<div class="alert alert-bad">${esc(e.message)}</div>`;
  }
}

/* ---------------------------------------------------------------- leads */
async function pageLeads() {
  const m = document.getElementById('main');
  m.innerHTML = head('Leads', 'Enquiries from the website contact form') +
    '<div class="boot">Loading…</div>';
  try {
    const r = await API.get('/api/admin/leads');
    m.innerHTML = head('Leads', 'Enquiries from the website contact form') + `
      <div class="panel">${r.leads.length ? `<div class="tbl-scroll"><table>
        <thead><tr><th>Received</th><th>Who</th><th>About</th><th>Message</th><th></th></tr></thead>
        <tbody>${r.leads.map(l => `<tr style="${l.handled ? 'opacity:.55' : ''}">
          <td class="small">${esc(l.created_at.slice(0, 16))}</td>
          <td><strong>${esc(l.name)}</strong><br>
            <a class="small" href="mailto:${esc(l.email || '')}">${esc(l.email || '')}</a><br>
            <span class="muted small">${esc(l.phone || '')}</span></td>
          <td><span class="pill pill-info">${esc(l.kind)}</span></td>
          <td class="small" style="max-width:360px">${esc(l.message || '')}</td>
          <td><button class="btn btn-xs ${l.handled ? 'btn-ghost' : 'btn-primary'}"
            data-h="${l.id}" data-v="${l.handled ? 0 : 1}">
            ${l.handled ? 'Reopen' : 'Mark handled'}</button></td>
        </tr>`).join('')}</tbody></table></div>`
        : '<div class="empty">No leads yet. They arrive here from the contact form.</div>'}
      </div>`;
    document.querySelectorAll('[data-h]').forEach(b => b.onclick = async () => {
      try { await API.post('/api/admin/leads/' + b.dataset.h, { handled: b.dataset.v === '1' }); nav('leads'); }
      catch (e) { alert(e.message); }
    });
  } catch (e) {
    m.innerHTML = `<div class="alert alert-bad">${esc(e.message)}</div>`;
  }
}

/* ---------------------------------------------------------------- team */
async function pageTeam() {
  const m = document.getElementById('main');
  m.innerHTML = head('Team', 'Staff accounts for the phone app and this dashboard',
    ME.role === 'owner' ? '<button class="btn btn-primary" id="addStaff">Add team member</button>' : '')
    + '<div class="boot">Loading…</div>';
  try {
    const r = await API.get('/api/admin/staff');
    STAFF = r.staff;
    m.innerHTML = head('Team', 'Staff accounts for the phone app and this dashboard',
      ME.role === 'owner' ? '<button class="btn btn-primary" id="addStaff">Add team member</button>' : '') + `
      <div class="panel"><div class="tbl-scroll"><table>
        <thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Role</th><th>Access</th></tr></thead>
        <tbody>${r.staff.map(s => `<tr>
          <td><strong>${esc(s.name)}</strong></td>
          <td class="small">${esc(s.email)}</td>
          <td class="small">${esc(s.phone || '—')}</td>
          <td><span class="pill ${s.role === 'owner' ? 'pill-ok' : 'pill-info'}"
            >${esc(s.role)}</span></td>
          <td class="small muted">${s.role === 'cleaner'
            ? 'Phone app — assigned jobs only' : 'Phone app + dashboard'}</td>
        </tr>`).join('')}</tbody></table></div></div>`;

    const add = document.getElementById('addStaff');
    if (add) add.onclick = () => {
      openModal(`
        <div class="modal-head"><h2>Add a team member</h2>
          <button class="x" onclick="closeModal()">&times;</button></div>
        <div id="sErr"></div>
        <div class="field"><label for="sName">Full name</label><input id="sName"></div>
        <div class="field"><label for="sEmail">Work email</label><input id="sEmail" type="email"></div>
        <div class="field"><label for="sPhone">Phone</label><input id="sPhone" type="tel"></div>
        <div class="field"><label for="sRole">Role</label><select id="sRole">
          <option value="cleaner">Cleaning technician — phone app, assigned jobs only</option>
          <option value="lead">Lead technician — phone app + dashboard</option>
          <option value="owner">Owner — full access</option></select></div>
        <div class="field"><label for="sPw">Temporary password</label>
          <input id="sPw" type="text" value="${esc(tempPassword())}">
          <p class="muted small" style="margin-top:5px">Share this with them; they use it to sign
          into the phone app. At least 8 characters.</p></div>
        <div class="btn-row"><button class="btn btn-primary" id="sSave">Create account</button>
          <button class="btn btn-ghost" onclick="closeModal()">Cancel</button></div>`);

      document.getElementById('sSave').onclick = async () => {
        const btn = document.getElementById('sSave');
        btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>';
        try {
          await API.post('/api/admin/staff', {
            name: document.getElementById('sName').value.trim(),
            email: document.getElementById('sEmail').value.trim(),
            phone: document.getElementById('sPhone').value.trim(),
            role: document.getElementById('sRole').value,
            password: document.getElementById('sPw').value,
          });
          closeModal(); nav('team');
        } catch (err) {
          document.getElementById('sErr').innerHTML =
            `<div class="alert alert-bad">${esc(err.message)}</div>`;
          btn.disabled = false; btn.textContent = 'Create account';
        }
      };
    };
  } catch (e) {
    m.innerHTML = `<div class="alert alert-bad">${esc(e.message)}</div>`;
  }
}

function tempPassword() {
  const w = ['gulf', 'tide', 'shore', 'palm', 'bay', 'sand', 'reef', 'wave'];
  return w[Math.floor(Math.random() * w.length)] +
         w[Math.floor(Math.random() * w.length)] +
         Math.floor(1000 + Math.random() * 9000);
}

/* ---------------------------------------------------------------- boot */
(async () => {
  try { CFG = await getConfig(); } catch (e) {
    root().innerHTML = '<div class="boot">Cannot reach the server. Is it running?</div>';
    return;
  }
  try {
    const r = await API.get('/api/auth/me');
    ME = r.staff;
  } catch (e) { ME = null; }

  if (ME && ['owner', 'lead'].includes(ME.role)) { shell(); nav('overview'); }
  else loginScreen();
})();
