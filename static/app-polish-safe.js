(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);

  // Stability-first product polish. Keep this helper deliberately one-shot and
  // event-driven: the old whole-document MutationObserver could create a
  // mutation storm while several product panels bootstrapped in parallel.

  const modernCss = document.createElement('link');
  modernCss.rel = 'stylesheet';
  modernCss.href = `/static/app-modern.css${window.__VEXMERA_BUILD__ ? `?build=${encodeURIComponent(window.__VEXMERA_BUILD__)}` : ''}`;
  modernCss.dataset.vexmeraModernUi = '1';
  if (!document.querySelector('link[data-vexmera-modern-ui]')) document.head.appendChild(modernCss);

  const THEME_KEY = 'vexmera-theme';
  const themeColor = document.querySelector('meta[name="theme-color"]');

  function preferredTheme() {
    try {
      const stored = localStorage.getItem(THEME_KEY);
      if (stored === 'light' || stored === 'dark') return stored;
    } catch (_) {}
    return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }

  function themeIcon(theme) {
    return theme === 'dark'
      ? '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.66 6.34l1.41-1.41"></path></svg>'
      : '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z"></path></svg>';
  }

  function applyTheme(theme, persist = false) {
    const next = theme === 'light' ? 'light' : 'dark';
    document.documentElement.dataset.vexTheme = next;
    if (themeColor) themeColor.setAttribute('content', next === 'light' ? '#f3f5f8' : '#0a0e14');
    if (persist) {
      try { localStorage.setItem(THEME_KEY, next); } catch (_) {}
    }

    const button = document.querySelector('[data-vex-theme-toggle]');
    if (button) {
      const target = next === 'dark' ? 'light' : 'dark';
      button.innerHTML = `${themeIcon(next)}<span class="vex-theme-label">${target === 'light' ? 'Ljust' : 'Mörkt'}</span>`;
      button.setAttribute('aria-label', `Byt till ${target === 'light' ? 'ljust' : 'mörkt'} tema`);
      button.title = `Byt till ${target === 'light' ? 'ljust' : 'mörkt'} tema`;
    }
  }

  applyTheme(preferredTheme());

  const pageMeta = {
    dashboard: ['Översikt.', 'Beslut, signaler och nästa drag på ett ställe.'],
    agent: ['Core.', 'Din AI Marketing Officer med permanent affärskontext.'],
    strategy: ['Pulse.', 'Bygg en mätbar tillväxtplan från verkliga signaler.'],
    campaign: ['Launch.', 'Från idé till kampanjförslag redo för godkännande.'],
    brief: ['Brief.', 'Din dagliga ledningsbrief för marknadsföringen.'],
    queue: ['Godkännanden.', 'Mänsklig kontroll före externa åtgärder.'],
    autopilot: ['Autopilot.', 'Bestäm exakt hur mycket Vexmera får göra inom dina gränser.'],
    rivals: ['Konkurrenter.', 'Bevaka publika förändringar hos konkurrenter.'],
    connect: ['Anslutningar.', 'Koppla och synka dina marknadsföringskällor.'],
    insights: ['Insikter.', 'Kampanjresultat, avvikelser och datakörningar.'],
    team: ['Team.', 'Medlemmar, plan, basvaluta och valutakurser.'],
    profile: ['Varumärkesprofil.', 'Företagsprofilen följer med i Vexmeras analyser.']
  };

  function applyPageMeta(view) {
    const meta = pageMeta[view];
    if (!meta) return;
    if ($('pageTitle')) $('pageTitle').textContent = meta[0];
    if ($('pageLead')) $('pageLead').textContent = meta[1];
  }

  const icons = {
    dashboard: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"></rect><rect x="14" y="3" width="7" height="7" rx="1"></rect><rect x="3" y="14" width="7" height="7" rx="1"></rect><rect x="14" y="14" width="7" height="7" rx="1"></rect></svg>',
    agent: '<svg viewBox="0 0 24 24"><path d="M12 3l1.3 4.2L17.5 8.5l-4.2 1.3L12 14l-1.3-4.2-4.2-1.3 4.2-1.3L12 3Z"></path><path d="M18 14l.8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8L18 14Z"></path></svg>',
    strategy: '<svg viewBox="0 0 24 24"><path d="M4 19V9M10 19V5M16 19v-7M22 19V3"></path><path d="M2 19h20"></path></svg>',
    campaign: '<svg viewBox="0 0 24 24"><path d="M4 13v-2l12-5v12L4 13Z"></path><path d="M8 14v5H5v-6"></path><path d="M19 9a4 4 0 0 1 0 6"></path></svg>',
    brief: '<svg viewBox="0 0 24 24"><path d="M6 3h9l4 4v14H6z"></path><path d="M15 3v5h5M9 12h7M9 16h7"></path></svg>',
    queue: '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"></rect><path d="m8 12 2.5 2.5L16 9"></path></svg>',
    autopilot: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"></circle><path d="M12 7v5l3 2M4.9 4.9l2 2M17.1 17.1l2 2"></path></svg>',
    rivals: '<svg viewBox="0 0 24 24"><path d="M3 17l5-5 4 4 7-9"></path><path d="M15 7h4v4"></path></svg>',
    connect: '<svg viewBox="0 0 24 24"><path d="M8 12h8M5 8h3v8H5a3 3 0 0 1-3-3v-2a3 3 0 0 1 3-3ZM19 8h-3v8h3a3 3 0 0 0 3-3v-2a3 3 0 0 0-3-3Z"></path></svg>',
    insights: '<svg viewBox="0 0 24 24"><path d="M4 19V5M4 19h16"></path><path d="m7 15 4-4 3 2 5-6"></path></svg>',
    team: '<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3"></circle><circle cx="17" cy="9" r="2"></circle><path d="M3 20a6 6 0 0 1 12 0M14 15a5 5 0 0 1 7 5"></path></svg>',
    profile: '<svg viewBox="0 0 24 24"><path d="M12 3l8 4v5c0 5-3.4 8-8 9-4.6-1-8-4-8-9V7l8-4Z"></path><path d="M9 12l2 2 4-4"></path></svg>'
  };

  document.querySelectorAll('.nav[data-view]').forEach((button) => {
    const view = button.dataset.view;
    if (!button.querySelector('.vex-nav-icon')) {
      const icon = document.createElement('span');
      icon.className = 'vex-nav-icon';
      icon.setAttribute('aria-hidden', 'true');
      icon.innerHTML = icons[view] || icons.dashboard;
      button.insertBefore(icon, button.firstChild);
    }
    button.addEventListener('click', () => applyPageMeta(view));
  });
  applyPageMeta(document.querySelector('.nav.active')?.dataset.view || 'dashboard');

  const headerControls = document.querySelector('.header-controls');
  if (headerControls && !headerControls.querySelector('[data-vex-theme-toggle]')) {
    const themeButton = document.createElement('button');
    themeButton.type = 'button';
    themeButton.className = 'ghost vex-theme-toggle';
    themeButton.dataset.vexThemeToggle = '1';
    themeButton.addEventListener('click', () => {
      const current = document.documentElement.dataset.vexTheme || 'dark';
      applyTheme(current === 'dark' ? 'light' : 'dark', true);
    });
    headerControls.insertBefore(themeButton, headerControls.firstChild);
    applyTheme(document.documentElement.dataset.vexTheme || preferredTheme());
  }

  const metricIcons = {
    metricRevenue: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"></circle><path d="M15 9.5c-.7-1-1.8-1.5-3-1.5-1.7 0-3 1-3 2.3 0 1.4 1.2 2 3 2.4 1.8.4 3 .9 3 2.3 0 1.3-1.3 2.3-3 2.3-1.4 0-2.7-.6-3.4-1.7M12 6v12"></path></svg>',
    metricSpend: '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"></rect><path d="M3 10h18M7 15h3"></path></svg>',
    metricRoas: '<svg viewBox="0 0 24 24"><path d="M4 17l5-5 4 3 6-8"></path><path d="M15 7h4v4"></path></svg>',
    metricLeads: '<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3"></circle><path d="M3 20a6 6 0 0 1 12 0M18 8v6M15 11h6"></path></svg>',
    metricConversions: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"></circle><circle cx="12" cy="12" r="3"></circle><path d="M12 2v3M22 12h-3"></path></svg>',
    metricCtr: '<svg viewBox="0 0 24 24"><path d="m5 3 12 8-6 2-2 6L5 3Z"></path></svg>',
    metricApprovals: '<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"></rect><path d="m8 12 2.5 2.5L16 9"></path></svg>',
    metricAlerts: '<svg viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"></path><path d="M10 21h4"></path></svg>',
    metricAnomalies: '<svg viewBox="0 0 24 24"><path d="M3 12h4l2-6 4 12 2-6h6"></path></svg>'
  };

  function decorateMetrics() {
    document.querySelectorAll('.metric strong[id]').forEach((value) => {
      const card = value.closest('.metric');
      if (!card) return;
      if (!card.querySelector('.vex-metric-icon')) {
        const icon = document.createElement('span');
        icon.className = 'vex-metric-icon';
        icon.setAttribute('aria-hidden', 'true');
        icon.innerHTML = metricIcons[value.id] || metricIcons.metricRoas;
        card.insertBefore(icon, card.firstChild);
      }
      card.classList.remove('vex-positive', 'vex-negative');
      const text = value.textContent.trim();
      if (/^\+/.test(text)) card.classList.add('vex-positive');
      if (/^[-−]/.test(text)) card.classList.add('vex-negative');
    });
  }

  decorateMetrics();
  window.setTimeout(decorateMetrics, 800);
  window.setTimeout(decorateMetrics, 2500);

  let toastStack = document.querySelector('.vex-toast-stack');
  if (!toastStack) {
    toastStack = document.createElement('div');
    toastStack.className = 'vex-toast-stack';
    toastStack.setAttribute('aria-live', 'polite');
    document.body.appendChild(toastStack);
  }

  function toast(message, timeout = 6500) {
    const text = typeof message === 'string' ? message : JSON.stringify(message, null, 2);
    const node = document.createElement('div');
    node.className = 'vex-toast';
    node.innerHTML = '<span class="vex-toast-icon">V</span><p></p><button type="button" aria-label="Stäng">×</button>';
    node.querySelector('p').textContent = text;
    const close = () => node.remove();
    node.querySelector('button').addEventListener('click', close);
    toastStack.appendChild(node);
    if (timeout) window.setTimeout(close, timeout);
  }

  window.vexmeraToast = toast;
  window.alert = (message) => toast(message);

  const runAutopilot = $('runAutopilotOnce');
  if (runAutopilot) {
    runAutopilot.title = 'Kör endast en policykontroll. Extern körning styrs fortfarande av serverns säkerhetsspärrar.';
  }

  document.documentElement.dataset.vexmeraAppPolishStable = '1';
  document.documentElement.dataset.vexmeraUi = 'modern-1';
})();