(async () => {
  const cfg = await getConfig();
  document.getElementById('faqList').innerHTML = cfg.faq.map((f, i) =>
    `<details class="faq-item"${i === 0 ? ' open' : ''}>
      <summary>${esc(f.q)}</summary><div class="a">${esc(f.a)}</div></details>`).join('');

  const ld = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    mainEntity: cfg.faq.map(f => ({
      '@type': 'Question', name: f.q,
      acceptedAnswer: { '@type': 'Answer', text: f.a },
    })),
  };
  const s = document.createElement('script');
  s.type = 'application/ld+json';
  s.textContent = JSON.stringify(ld);
  document.head.appendChild(s);
})();
