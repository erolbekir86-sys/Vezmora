(() => {
  'use strict';

  const build = window.__VEXMERA_BUILD__ || 'local';

  // Vexmera's brand-first experience is dark. Apply it once only when there is
  // no valid saved preference, then keep respecting the visitor's explicit choice.
  function installDarkDefault() {
    try {
      const rolloutKey = 'vexmera-dark-default-v1';
      if (localStorage.getItem(rolloutKey) === '1') return;

      const savedTheme = localStorage.getItem('vexmera-theme');
      const hasExplicitTheme = savedTheme === 'light' || savedTheme === 'dark';
      const theme = hasExplicitTheme ? savedTheme : 'dark';

      if (!hasExplicitTheme) localStorage.setItem('vexmera-theme', theme);
      localStorage.setItem(rolloutKey, '1');
      document.documentElement.setAttribute('data-theme', theme);
      document.documentElement.style.colorScheme = theme;
      const themeColor = document.querySelector('meta[name="theme-color"]');
      if (themeColor) themeColor.setAttribute('content', theme === 'dark' ? '#0f1319' : '#f7f3ec');
    } catch (_) {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.style.colorScheme = 'dark';
    }
  }

  installDarkDefault();

  const addStylesheet = (href, marker) => {
    if (document.querySelector(`link[${marker}]`)) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    link.setAttribute(marker, 'true');
    document.head.appendChild(link);
  };

  const addScript = (src, marker) => {
    if (document.querySelector(`script[${marker}]`)) return;
    const script = document.createElement('script');
    script.src = src;
    script.defer = true;
    script.setAttribute(marker, 'true');
    document.head.appendChild(script);
  };

  addStylesheet(`/static/landing-premium.css?build=${encodeURIComponent(build)}`, 'data-vexmera-premium');
  addStylesheet(`/static/landing-mobile-final.css?build=${encodeURIComponent(build)}`, 'data-vexmera-mobile-final');
  addStylesheet(`/static/landing-ai-workflow.css?build=${encodeURIComponent(build)}`, 'data-vexmera-ai-workflow');
  addStylesheet(`/static/landing-ai-opportunity.css?build=${encodeURIComponent(build)}`, 'data-vexmera-ai-opportunity');
  addStylesheet(`/static/landing-ai-recommendation.css?build=${encodeURIComponent(build)}`, 'data-vexmera-ai-recommendation');
  addStylesheet(`/static/landing-ai-approval.css?build=${encodeURIComponent(build)}`, 'data-vexmera-ai-approval');
  addStylesheet(`/static/landing-ai-action.css?build=${encodeURIComponent(build)}`, 'data-vexmera-ai-action');
  addStylesheet(`/static/landing-workflow-premium.css?build=${encodeURIComponent(build)}`, 'data-vexmera-workflow-premium');
  addScript(`/static/landing-workflow-premium.js?build=${encodeURIComponent(build)}`, 'data-vexmera-workflow-premium-script');
  addScript(`/static/landing-conversion.js?build=${encodeURIComponent(build)}`, 'data-vexmera-conversion-script');

  const icons = {
    simple: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 7h14M5 12h14M5 17h9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    fast: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    smart: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M9 18h6M10 21h4M8.3 14.7A6 6 0 1 1 15.7 14.7c-.8.7-1.3 1.5-1.5 2.3h-4.4c-.2-.8-.7-1.6-1.5-2.3Z" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    time: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="8" stroke="currentColor" stroke-width="1.9"/><path d="M12 8v5l3 2" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    budget: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 18V11M10 18V7M15 18v-4M20 18V5" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/><path d="M3 20h18" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg>',
    alert: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 17l5-5 4 3 7-8" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="12" r="1.4" fill="currentColor"/></svg>',
    next: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  };

  function normalizeValueIcons() {
    const cards = [...document.querySelectorAll('.value-card')];
    const ordered = [icons.simple, icons.fast, icons.smart];
    cards.forEach((card, index) => {
      const oldIndex = card.querySelector(':scope > .index');
      if (oldIndex) oldIndex.style.display = 'none';
      let box = card.querySelector(':scope > .icon-box');
      if (!box) {
        box = document.createElement('div');
        box.className = 'icon-box';
        const title = card.querySelector('h3');
        card.insertBefore(box, title || card.firstChild);
      }
      box.innerHTML = ordered[index] || icons.smart;
      box.setAttribute('aria-hidden', 'true');
    });
  }

  function normalizeOutcomeIcons() {
    const cards = [...document.querySelectorAll('.outcome-grid article')];
    const ordered = [icons.time, icons.budget, icons.alert, icons.next];
    cards.forEach((card, index) => {
      const first = card.querySelector(':scope > span');
      if (first && /^\s*0?\d+\s*$/.test(first.textContent || '')) first.style.display = 'none';
      let box = card.querySelector(':scope > .premium-outcome-icon');
      if (!box) {
        box = document.createElement('div');
        box.className = 'premium-outcome-icon';
        const title = card.querySelector('h3');
        card.insertBefore(box, title || card.firstChild);
      }
      box.innerHTML = ordered[index] || icons.next;
      box.setAttribute('aria-hidden', 'true');
    });
  }

  function installFounderPhoto() {
    const current = document.querySelector('.founder-portrait');
    if (!current) return false;

    const expected = `/static/vexmera-founder.jpg?build=${encodeURIComponent(build)}`;
    let image = current;

    if (current.tagName !== 'IMG') {
      image = document.createElement('img');
      image.className = current.className;
      image.alt = document.documentElement.lang === 'en'
        ? 'Erol Bekir, founder of Vexmera'
        : 'Erol Bekir, grundare av Vexmera';
      image.width = 640;
      image.height = 800;
      current.replaceWith(image);
    }

    image.src = expected;
    image.loading = 'eager';
    image.decoding = 'async';
    image.fetchPriority = 'high';
    image.style.display = 'block';
    image.style.visibility = 'visible';
    image.style.opacity = '1';
    image.style.objectFit = 'cover';
    image.style.objectPosition = 'center 32%';

    image.onerror = () => {
      if (image.dataset.vexmeraRetry === '1') return;
      image.dataset.vexmeraRetry = '1';
      image.src = `/static/vexmera-founder.jpg?build=${encodeURIComponent(build)}&retry=1`;
    };

    return true;
  }

  function runVisualPass() {
    normalizeValueIcons();
    normalizeOutcomeIcons();
    installFounderPhoto();
    document.documentElement.classList.add('vexmera-premium-ready');
  }

  function settleDynamicLanding() {
    let attempts = 0;
    const tick = () => {
      attempts += 1;
      runVisualPass();
      const founderReady = document.querySelector('.founder-portrait')?.tagName === 'IMG';
      const valueReady = document.querySelectorAll('.value-card .icon-box svg').length >= 3;
      const outcomeCount = document.querySelectorAll('.outcome-grid article').length;
      const outcomeReady = outcomeCount === 0 || document.querySelectorAll('.premium-outcome-icon svg').length >= outcomeCount;
      if (founderReady && valueReady && outcomeReady) return;
      if (attempts < 24) window.setTimeout(tick, attempts < 5 ? 120 : 350);
    };
    tick();
  }

  function installMicroSound() {
    if (document.documentElement.dataset.vexmeraSoundInstalled === '1') return;
    document.documentElement.dataset.vexmeraSoundInstalled = '1';

    let audioContext = null;
    const ping = (frequency = 620, duration = 0.035, volume = 0.012) => {
      try {
        audioContext ||= new (window.AudioContext || window.webkitAudioContext)();
        const now = audioContext.currentTime;
        const oscillator = audioContext.createOscillator();
        const gain = audioContext.createGain();
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(frequency, now);
        gain.gain.setValueAtTime(0.0001, now);
        gain.gain.exponentialRampToValueAtTime(volume, now + 0.006);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
        oscillator.connect(gain);
        gain.connect(audioContext.destination);
        oscillator.start(now);
        oscillator.stop(now + duration + 0.012);
      } catch (_) {
      }
    };

    document.addEventListener('click', (event) => {
      const target = event.target.closest('button, .button, summary, .menu-toggle, [data-theme-toggle], [data-lang-toggle]');
      if (!target) return;
      if (target.matches('[data-theme-toggle], #footerTheme')) ping(720, 0.045, 0.014);
      else if (target.matches('.menu-toggle, [aria-controls*="nav"]')) ping(540, 0.04, 0.012);
      else ping(630, 0.032, 0.010);
    }, { passive: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', settleDynamicLanding, { once: true });
  } else {
    settleDynamicLanding();
  }

  installMicroSound();
})();