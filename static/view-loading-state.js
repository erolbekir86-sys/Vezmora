(() => {
  'use strict';

  const LOADERS = {
    loadDashboard: 'dashboard',
    loadCoreToday: 'dashboard',
    loadCompetitors: 'rivals',
    loadConnectors: 'connect',
    loadApprovals: 'queue',
    loadAutopilot: 'autopilot',
    loadBrief: 'brief',
    loadInsights: 'insights',
    loadTeam: 'team',
  };

  const busyCounts = new Map();

  function installStyles() {
    if (document.getElementById('vexmera-view-loading-styles')) return;
    const style = document.createElement('style');
    style.id = 'vexmera-view-loading-styles';
    style.textContent = `
      .view .vex-view-loading-status {
        width: max-content;
        max-width: 100%;
        margin: 0 0 12px auto;
        padding: 6px 10px;
        border: 1px solid var(--line, rgba(255,255,255,.12));
        border-radius: 999px;
        background: var(--panel, rgba(255,255,255,.04));
        color: var(--muted, currentColor);
        font-size: 12px;
        line-height: 1.2;
      }
      .view .vex-view-loading-status[hidden] { display: none !important; }
    `;
    document.head.appendChild(style);
  }

  function getView(viewId) {
    return document.getElementById(viewId);
  }

  function ensureStatus(view) {
    let status = view.querySelector('.vex-view-loading-status');
    if (status) return status;

    status = document.createElement('div');
    status.className = 'vex-view-loading-status';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    status.setAttribute('aria-atomic', 'true');
    status.textContent = 'Uppdaterar…';
    status.hidden = true;
    view.prepend(status);
    return status;
  }

  function beginBusy(viewId) {
    const view = getView(viewId);
    if (!view) return;

    const next = (busyCounts.get(viewId) || 0) + 1;
    busyCounts.set(viewId, next);
    view.setAttribute('aria-busy', 'true');
    ensureStatus(view).hidden = false;
  }

  function endBusy(viewId) {
    const view = getView(viewId);
    if (!view) return;

    const next = Math.max(0, (busyCounts.get(viewId) || 1) - 1);
    if (next > 0) {
      busyCounts.set(viewId, next);
      return;
    }

    busyCounts.delete(viewId);
    view.setAttribute('aria-busy', 'false');
    const status = view.querySelector('.vex-view-loading-status');
    if (status) status.hidden = true;
  }

  function wrapLoader(name, viewId) {
    const original = window[name];
    if (typeof original !== 'function' || original.__vexmeraLoadingStateGuard) return;

    async function guardedLoader(...args) {
      beginBusy(viewId);
      try {
        return await original.apply(this, args);
      } finally {
        endBusy(viewId);
      }
    }

    guardedLoader.__vexmeraLoadingStateGuard = true;
    guardedLoader.__vexmeraOriginalLoader = original;
    window[name] = guardedLoader;
  }

  function installViewLoadingStates() {
    installStyles();
    Object.entries(LOADERS).forEach(([name, viewId]) => wrapLoader(name, viewId));
  }

  function loadDashboardFirstUseGuide() {
    if (document.querySelector('script[data-vexmera-dashboard-first-use]')) return;
    const script = document.createElement('script');
    const build = encodeURIComponent(String(window.__VEXMERA_BUILD__ || 'local'));
    script.src = `/static/dashboard-first-use.js?build=${build}`;
    script.dataset.vexmeraDashboardFirstUse = '1';
    document.head.appendChild(script);
  }

  installViewLoadingStates();
  loadDashboardFirstUseGuide();
})();
