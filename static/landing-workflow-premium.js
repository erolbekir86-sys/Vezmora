(() => {
  'use strict';

  const icons = [
    '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="13"/><circle cx="24" cy="24" r="5"/><path d="M24 5v6M24 37v6M5 24h6M37 24h6"/><path d="M34 14l5-5M14 34l-5 5"/><path d="M24 16l2.4 5.6L32 24l-5.6 2.4L24 32l-2.4-5.6L16 24l5.6-2.4L24 16Z"/></svg>',
    '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M15 34h18M18 40h12"/><path d="M14.5 28.5A14 14 0 1 1 33.5 28.5c-2.2 1.8-3.5 3.6-4 5.5h-11c-.5-1.9-1.8-3.7-4-5.5Z"/><path d="M19 22l4 4 7-8"/></svg>',
    '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M24 6 38 11v10c0 9.4-5.9 16.7-14 20-8.1-3.3-14-10.6-14-20V11l14-5Z"/><path d="m17 23 5 5 10-11"/></svg>',
    '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="15"/><path d="M18 30 31 17M23 17h8v8"/><path d="M15 34h18"/></svg>'
  ];

  const copy = {
    sv: [
      'Vexmera hittar signaler med tydlig potential.',
      'AI föreslår nästa åtgärd och visar varför.',
      'Du granskar förslaget och behåller kontrollen.',
      'Godkända beslut blir tydliga, spårade aktiviteter.'
    ],
    en: [
      'Vexmera finds signals with clear potential.',
      'AI suggests the next action and explains why.',
      'You review the proposal and stay in control.',
      'Approved decisions become clear, tracked actions.'
    ]
  };

  function apply() {
    const nodes = [...document.querySelectorAll('.workflow-section .workflow-node')];
    if (!nodes.length) return;
    const lang = document.documentElement.lang === 'en' ? 'en' : 'sv';

    nodes.forEach((node, index) => {
      let icon = node.querySelector(':scope > .workflow-premium-icon');
      if (!icon) {
        icon = document.createElement('div');
        icon.className = 'workflow-premium-icon';
        icon.setAttribute('aria-hidden', 'true');
        node.insertBefore(icon, node.firstChild);
      }
      icon.innerHTML = icons[index] || icons[3];

      const small = node.querySelector(':scope > small');
      if (small) {
        small.textContent = copy[lang][index] || copy[lang][3];
        small.removeAttribute('data-i18n');
      }
    });
  }

  function settle() {
    let attempts = 0;
    const tick = () => {
      attempts += 1;
      apply();
      if (document.querySelectorAll('.workflow-premium-icon').length >= 4 || attempts >= 20) return;
      window.setTimeout(tick, attempts < 5 ? 120 : 320);
    };
    tick();
  }

  document.addEventListener('click', (event) => {
    if (!event.target.closest('#languageToggle,#footerLanguage')) return;
    window.setTimeout(apply, 60);
    window.setTimeout(apply, 220);
  }, { passive:true });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', settle, { once:true });
  else settle();
})();
