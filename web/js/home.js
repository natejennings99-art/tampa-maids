/* Page enhancements for every v2 page (home and inner pages). Pages are fully
   rendered HTML (tools/home_v2.py, tools/inner_v2.py);
   this adds the live price picker, counters, scroll reveals, a light hero
   parallax and the mobile booking bar. Everything degrades to static content. */
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- instant price ---- */
  const dataEl = document.getElementById('priceData');
  const form = document.getElementById('quote');
  if (dataEl && form) {
    const data = JSON.parse(dataEl.textContent);
    const tierSel = document.getElementById('q-tier');
    const amt = document.getElementById('q-amt');
    const cap = document.getElementById('q-cap');
    const save = document.getElementById('q-save');
    const btns = form.querySelectorAll('.seg button');
    let freq = data.freq;
    const fmt = c => '$' + Math.round(c / 100);

    function tick(from, to) {
      if (reduce || from === to) { amt.textContent = fmt(to); return; }
      const t0 = performance.now(), d = 320;
      (function step(t) {
        const k = Math.min(1, (t - t0) / d), e = 1 - Math.pow(1 - k, 3);
        amt.textContent = fmt(from + (to - from) * e);
        if (k < 1) requestAnimationFrame(step);
      })(t0);
    }
    let shown = null;
    function update() {
      const tier = data.tiers.find(t => t.id === tierSel.value) || data.tiers[0];
      const p = tier.prices[freq], once = tier.prices.once;
      tick(shown == null ? p : shown, p); shown = p;
      cap.textContent = freq === 'once' ? 'One-time clean' : 'Per visit';
      save.textContent = freq !== 'once' && once && p < once
        ? 'Save ' + Math.round((1 - p / once) * 100) + '% vs one-time' : '';
      btns.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.freq === freq)));
    }
    btns.forEach(b => b.addEventListener('click', () => { freq = b.dataset.freq; update(); }));
    tierSel.addEventListener('change', update);
    form.addEventListener('submit', e => {
      e.preventDefault();
      location.href = '/book?tier=' + encodeURIComponent(tierSel.value) + '&freq=' + encodeURIComponent(freq);
    });
    update();
  }

  /* ---- counters ---- */
  function count(el) {
    const to = +el.dataset.count, pre = el.dataset.prefix || '', suf = el.dataset.suffix || '';
    if (reduce || !to) { el.textContent = pre + to + suf; return; }
    const t0 = performance.now(), d = 1100;
    (function step(t) {
      const k = Math.min(1, (t - t0) / d), e = 1 - Math.pow(1 - k, 3);
      el.textContent = pre + Math.round(to * e) + suf;
      if (k < 1) requestAnimationFrame(step);
    })(t0);
  }

  /* ---- reveal on scroll ---- */
  const els = document.querySelectorAll('.rv');
  if ('IntersectionObserver' in window && !reduce) {
    const io = new IntersectionObserver(entries => entries.forEach(en => {
      if (!en.isIntersecting) return;
      const el = en.target;
      const sibs = el.parentElement ? [...el.parentElement.children].filter(c => c.classList.contains('rv')) : [el];
      el.style.transitionDelay = Math.min(sibs.indexOf(el), 5) * 70 + 'ms';
      el.classList.add('in');
      el.querySelectorAll('[data-count]').forEach(count);
      io.unobserve(el);
    }), { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    els.forEach(el => io.observe(el));
  } else {
    els.forEach(el => el.classList.add('in'));
    document.querySelectorAll('[data-count]').forEach(count);
  }

  /* ---- hero parallax + mobile bar ---- */
  const photo = document.querySelector('.h-photo img');
  const hero = document.querySelector('.h-hero, .p-hero');
  const bar = document.getElementById('mbar');
  let ticking = false;
  function onScroll() {
    ticking = false;
    const y = scrollY;
    if (photo && !reduce && y < 900) photo.style.transform = 'scale(1.12) translateY(' + Math.min(y * 0.05, 22).toFixed(1) + 'px)';
    if (bar && hero) bar.classList.toggle('show', y > hero.offsetHeight * 0.6);
  }
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();
})();
