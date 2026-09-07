(() => {
  'use strict';

  // Keep the marketing page enhancement layer deliberately one-shot.
  // The previous UX helper observed the entire DOM and rewrote icon innerHTML
  // from inside its own MutationObserver callback, which could create a
  // self-triggering mutation loop and freeze/crash the tab during refresh.

  if (localStorage.getItem('vexmera-sound') === null) {
    localStorage.setItem('vexmera-sound', 'on');
  }

  const svg = (body) => `<svg class="ux-icon" viewBox="0 0 24 24" aria-hidden="true">${body}</svg>`;
  const icons = {
    growth: svg('<path d="M4 18V6"/><path d="M4 18h16"/><path d="m7 14 4-4 3 2 5-6"/><path d="M16 6h3v3"/>'),
    spark: svg('<path d="M12 3l1.35 4.15L17.5 8.5l-4.15 1.35L12 14l-1.35-4.15L6.5 8.5l4.15-1.35L12 3Z"/>'),
    shield: svg('<path d="M12 3 20 6v5c0 5-3.4 8.6-8 10-4.6-1.4-8-5-8-10V6l8-3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/>'),
    layers: svg('<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 16 9 5 9-5"/>'),
    arrow: svg('<path d="M4 12h15"/><path d="m14 7 5 5-5 5"/>'),
    target: svg('<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>'),
    home: svg('<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>'),
    core: svg('<path d="m12 3 7 9-7 9-7-9 7-9Z"/><path d="M9.5 12h5M12 9.5v5"/>'),
    pulse: svg('<path d="M3 12h4l2-5 4 10 2-5h6"/>'),
    launch: svg('<path d="M14 5c2.4-1.4 4.7-1.8 6.5-1.5.3 1.8-.1 4.1-1.5 6.5l-5.5 5.5-5-5L14 5Z"/><circle cx="16.5" cy="7.5" r="1.5"/>'),
    autopilot: svg('<path d="M4 15a8 8 0 1 1 16 0"/><path d="m12 15 4-5"/><circle cx="12" cy="15" r="1.5"/>'),
    settings: svg('<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>'),
    users: svg('<circle cx="9" cy="8" r="3"/><path d="M3.5 19c.5-3.2 2.4-5 5.5-5s5 1.8 5.5 5"/><path d="M15 6.2a3 3 0 0 1 0 5.6"/>'),
    link: svg('<path d="M10 13a4 4 0 0 0 5.7 0l2.3-2.3A4 4 0 1 0 12.3 5L11 6.3"/><path d="M14 11a4 4 0 0 0-5.7 0L6 13.3A4 4 0 0 0 11.7 19l1.3-1.3"/>'),
    chart: svg('<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>')
  };

  const setOnce = (element, name) => {
    if (!element || !icons[name] || element.dataset.safeIcon === name) return;
    element.innerHTML = icons[name];
    element.dataset.safeIcon = name;
  };

  function enhanceIconsOnce() {
    document.querySelectorAll('.trust-icon').forEach((el, i) => setOnce(el, ['growth', 'spark', 'shield'][i] || 'spark'));
    document.querySelectorAll('.value-card .icon-box').forEach((el, i) => setOnce(el, ['layers', 'arrow', 'target'][i] || 'spark'));

    document.querySelectorAll('.dash-nav').forEach((nav) => {
      const text = (nav.textContent || '').trim().toLowerCase();
      let name = 'home';
      if (text.includes('core')) name = 'core';
      else if (text.includes('pulse')) name = 'pulse';
      else if (text.includes('launch')) name = 'launch';
      else if (text.includes('autopilot')) name = 'autopilot';
      else if (text.includes('inställ') || text.includes('setting')) name = 'settings';
      else if (text.includes('konkurrent') || text.includes('competitor')) name = 'users';
      else if (text.includes('anslut') || text.includes('connection')) name = 'link';
      else if (text.includes('insikt') || text.includes('insight')) name = 'chart';

      const old = nav.querySelector('b');
      if (old) {
        const holder = document.createElement('span');
        holder.className = 'safe-nav-icon';
        holder.innerHTML = icons[name];
        holder.dataset.safeIcon = name;
        old.replaceWith(holder);
      }
    });
  }

  function boot() {
    enhanceIconsOnce();
    document.documentElement.dataset.vexmeraRuntimeStable = '1';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, {once: true});
  } else {
    boot();
  }
})();
