(() => {
  'use strict';

  const SVG = (body) => `<svg class="vex-premium-icon" viewBox="0 0 24 24" aria-hidden="true">${body}</svg>`;

  const icons = {
    growth: SVG('<path d="M4 18V7"/><path d="M4 18h16"/><path d="m7 14 4-4 3 2 5-6"/><path d="M16.5 6H20v3.5"/><circle cx="7" cy="14" r="1"/><circle cx="11" cy="10" r="1"/><circle cx="14" cy="12" r="1"/>'),
    insight: SVG('<path d="M9 18h6"/><path d="M10 21h4"/><path d="M8.4 14.6A6 6 0 1 1 15.6 14.6c-.8.7-1.25 1.5-1.45 2.4h-4.3c-.2-.9-.65-1.7-1.45-2.4Z"/><path d="M12 6.5v2.2M8.6 8l1.5 1.5M15.4 8l-1.5 1.5"/>'),
    control: SVG('<path d="M12 3 20 6v5c0 5-3.4 8.6-8 10-4.6-1.4-8-5-8-10V6l8-3Z"/><path d="M8 10h8M8 14h8"/><circle cx="10" cy="10" r="1.4" fill="currentColor" stroke="none"/><circle cx="14" cy="14" r="1.4" fill="currentColor" stroke="none"/>'),
    simple: SVG('<rect x="4" y="4" width="7" height="7" rx="2"/><rect x="13" y="4" width="7" height="7" rx="2"/><rect x="4" y="13" width="7" height="7" rx="2"/><path d="m14.5 16.5 1.8 1.8 3.2-3.8"/>'),
    fast: SVG('<path d="M4 7h7M2 12h9M5 17h6"/><path d="m12 6 6 6-6 6"/><path d="M18 7.5 22 12l-4 4.5"/>'),
    smart: SVG('<path d="M9 18h6M10 21h4"/><path d="M8.2 14.8A6 6 0 1 1 15.8 14.8c-.9.8-1.35 1.5-1.55 2.2h-4.5c-.2-.7-.65-1.4-1.55-2.2Z"/><circle cx="9" cy="10" r="1"/><circle cx="15" cy="10" r="1"/><circle cx="12" cy="7" r="1"/><path d="m9.8 9.4 1.4-1.6M14.2 9.4l-1.4-1.6M10 10h4"/>'),
    time: SVG('<circle cx="11.5" cy="12" r="7.5"/><path d="M11.5 7.5V12l3.1 1.8"/><path d="M4.8 5.4 3.4 4M18.2 5.1 20 3.6"/><path d="M18.5 15.5h2.7M19.85 14.15v2.7"/>'),
    budget: SVG('<path d="M4 19V13M9 19V9M14 19v-5M3 21h13"/><path d="m4.5 11 4-3 4 2 4.2-5"/><path d="M14.8 5H17v2.2"/><circle cx="18.5" cy="16.5" r="3.2"/><path d="M18.5 14.7v3.6M17.3 15.4h1.8M17.9 17.7h1.8"/>'),
    detect: SVG('<circle cx="11.5" cy="12" r="7.5"/><circle cx="11.5" cy="12" r="3.2"/><path d="M11.5 4.5V2.5M19 12h2M11.5 19.5v2M4 12H2"/><path d="m13.8 9.7 4.6-4.6"/><path d="M17.2 5.1h2.2v2.2"/><circle cx="18.6" cy="18" r="1.5" fill="currentColor" stroke="none"/>'),
    next: SVG('<circle cx="12" cy="12" r="8"/><path d="M8.5 15.5 15.5 8.5"/><path d="M11.7 8.5h3.8v3.8"/><path d="M7.4 9.2 5.7 7.5M16.6 14.8l1.7 1.7"/>'),
    demo: SVG('<rect x="4" y="5" width="16" height="14" rx="3"/><path d="M8 9h8M8 13h5"/><circle cx="17" cy="15" r="2"/>'),
    betaControl: SVG('<path d="M12 3 20 6v5c0 5-3.4 8.6-8 10-4.6-1.4-8-5-8-10V6l8-3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/>'),
    channels: SVG('<circle cx="6" cy="12" r="2.2"/><circle cx="18" cy="7" r="2.2"/><circle cx="18" cy="17" r="2.2"/><path d="m8.2 11 7.6-3M8.2 13l7.6 3"/>'),
    core: SVG('<path d="m12 3 7 9-7 9-7-9 7-9Z"/><path d="M9 12h6M12 9v6"/>'),
    pulse: SVG('<path d="M3 12h4l2-5 4 10 2-5h6"/><circle cx="9" cy="7" r="1" fill="currentColor" stroke="none"/><circle cx="13" cy="17" r="1" fill="currentColor" stroke="none"/>'),
    launch: SVG('<path d="M14 5c2.4-1.4 4.7-1.8 6.5-1.5.3 1.8-.1 4.1-1.5 6.5l-5.5 5.5-5-5L14 5Z"/><path d="m9 15-3 1-2 4 4-2 1-3Z"/><circle cx="16.5" cy="7.5" r="1.4"/>'),
    autopilot: SVG('<path d="M4 15a8 8 0 1 1 16 0"/><path d="m12 15 4-5"/><circle cx="12" cy="15" r="1.5"/><path d="M6 19h12"/>'),
    googleAds: SVG('<circle cx="9" cy="15" r="3"/><path d="m11 12 4.8-8"/><path d="M15.8 4 21 13"/><circle cx="18.5" cy="15.5" r="2.5"/>'),
    meta: SVG('<path d="M4 14c2.5-7.5 5-8.5 8-1.5 3-7 5.5-6 8 1.5 1.5 4.5-1 5-3 1-2-4-3.2-6-5-6-2 0-3 2-5 6-2 4-4.5 4.5-5 1Z"/>'),
    analytics: SVG('<path d="M4 19V10M10 19V5M16 19v-7M22 19H2"/><path d="m4 8 6-4 6 6 4-5"/>'),
    briefcase: SVG('<rect x="3" y="7" width="18" height="12" rx="2"/><path d="M8 7V5h8v2M3 12h18"/>'),
    play: SVG('<path d="M10 8v8l6-4-6-4Z"/><rect x="4" y="3" width="16" height="18" rx="4"/>'),
    bag: SVG('<path d="M5 8h14l-1 13H6L5 8Z"/><path d="M9 9V6a3 3 0 0 1 6 0v3"/>'),
    home: SVG('<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>'),
    settings: SVG('<circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.4-2.4 1a7 7 0 0 0-1.8-1L14.4 3h-4.8l-.3 3.1a7 7 0 0 0-1.8 1l-2.4-1-2 3.4 2 1.5a7 7 0 0 0 0 2l-2 1.5 2 3.4 2.4-1a7 7 0 0 0 1.8 1l.3 3.1h4.8l.3-3.1a7 7 0 0 0 1.8-1l2.4 1 2-3.4-2-1.5c.1-.3.1-.7.1-1Z"/>')
  };

  const outcomeCopy = {
    sv: [
      'Vexmera samlar signalerna och lyfter det viktigaste, så att du slipper fastna i dashboards.',
      'Se tydligare var pengarna gör mest nytta och vad som bör justeras.',
      'Upptäck negativa förändringar tidigt innan de hinner bli kostsamma.',
      'Få prioriterade rekommendationer som gör nästa beslut enklare.'
    ],
    en: [
      'Vexmera brings the signals together and surfaces what matters, so you spend less time inside dashboards.',
      'See more clearly where spend creates value and what should be adjusted.',
      'Catch negative changes early before they become costly.',
      'Get prioritized recommendations that make the next decision easier.'
    ]
  };

  function setIcon(el, name) {
    if (!el || !icons[name]) return;
    el.innerHTML = icons[name];
    el.dataset.vexPremiumIcon = name;
  }

  function upgradeTrust() {
    document.querySelectorAll('.trust-icon').forEach((el, i) => setIcon(el, ['growth','insight','control'][i] || 'insight'));
  }

  function upgradeValues() {
    document.querySelectorAll('.value-card>.icon-box').forEach((el, i) => setIcon(el, ['simple','fast','smart'][i] || 'smart'));
  }

  function upgradeOutcomes() {
    const cards = [...document.querySelectorAll('.outcome-grid article')];
    const language = (document.documentElement.lang || 'sv').toLowerCase().startsWith('en') ? 'en' : 'sv';
    cards.forEach((card, i) => {
      const icon = card.querySelector('.premium-outcome-icon');
      if (icon) setIcon(icon, ['time','budget','detect','next'][i] || 'next');

      let copy = card.querySelector(':scope > .outcome-support-copy');
      if (!copy) {
        copy = document.createElement('p');
        copy.className = 'outcome-support-copy';
        const title = card.querySelector('h3');
        if (title) title.insertAdjacentElement('afterend', copy);
        else card.appendChild(copy);
      }
      copy.textContent = outcomeCopy[language][i] || outcomeCopy[language][3];
    });
  }

  function upgradeBeta() {
    document.querySelectorAll('.beta-proof-icon').forEach((el, i) => setIcon(el, ['demo','betaControl','channels'][i] || 'channels'));
  }

  function upgradeModules() {
    document.querySelectorAll('.module-card').forEach((card) => {
      const el = card.querySelector('.module-letter');
      if (!el) return;
      const text = (card.textContent || '').toLowerCase();
      const name = text.includes('pulse') ? 'pulse' : text.includes('launch') ? 'launch' : text.includes('autopilot') ? 'autopilot' : 'core';
      el.classList.add('ux-symbol');
      setIcon(el, name);
    });
  }

  function upgradeIntegrations() {
    document.querySelectorAll('.integration-card').forEach((card) => {
      const el = card.querySelector('.source-logo');
      if (!el) return;
      const text = (card.textContent || '').toLowerCase();
      let name = 'channels';
      if (text.includes('google')) name = 'googleAds';
      else if (text.includes('meta')) name = 'meta';
      else if (text.includes('analytics')) name = 'analytics';
      else if (text.includes('linkedin')) name = 'briefcase';
      else if (text.includes('tiktok')) name = 'play';
      else if (text.includes('shopify')) name = 'bag';
      el.classList.add('ux-source');
      setIcon(el, name);
    });
  }

  function upgradeDashboard() {
    document.querySelectorAll('.dash-nav').forEach((nav) => {
      const text = (nav.textContent || '').trim().toLowerCase();
      let name = 'home';
      if (text.includes('core')) name = 'core';
      else if (text.includes('pulse')) name = 'pulse';
      else if (text.includes('launch')) name = 'launch';
      else if (text.includes('autopilot')) name = 'autopilot';
      else if (text.includes('inställ') || text.includes('setting')) name = 'settings';
      const existing = nav.querySelector('.ux-icon,.vex-premium-icon,b');
      if (existing) existing.outerHTML = icons[name];
      else nav.insertAdjacentHTML('afterbegin', icons[name]);
    });
  }

  function run() {
    upgradeTrust();
    upgradeValues();
    upgradeOutcomes();
    upgradeBeta();
    upgradeModules();
    upgradeIntegrations();
    upgradeDashboard();
    document.documentElement.classList.add('vexmera-premium-icons-ready');
  }

  function settle() {
    let attempts = 0;
    const tick = () => {
      attempts += 1;
      run();
      const baseReady = document.querySelectorAll('.trust-icon .vex-premium-icon').length >= 3 && document.querySelectorAll('.value-card>.icon-box .vex-premium-icon').length >= 3;
      const dynamicReady = document.querySelectorAll('.premium-outcome-icon').length === 0 || document.querySelectorAll('.premium-outcome-icon .vex-premium-icon').length === document.querySelectorAll('.premium-outcome-icon').length;
      const betaReady = document.querySelectorAll('.beta-proof-icon').length === 0 || document.querySelectorAll('.beta-proof-icon .vex-premium-icon').length === document.querySelectorAll('.beta-proof-icon').length;
      if (baseReady && dynamicReady && betaReady && attempts > 5) return;
      if (attempts < 24) window.setTimeout(tick, attempts < 6 ? 130 : 340);
    };
    tick();
  }

  document.addEventListener('click', (event) => {
    if (!event.target.closest('[data-lang-toggle],#footerLanguage,.language-toggle')) return;
    window.setTimeout(run, 80);
    window.setTimeout(run, 260);
  }, { passive:true });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', settle, { once:true });
  else settle();
})();
