(() => {
  'use strict';

  const GUIDE_ID = 'vexmera-dashboard-first-use';

  function kpiTableIsEmpty() {
    const rows = document.getElementById('kpiRows');
    if (!rows || rows.querySelector('.error-text')) return false;
    return rows.textContent.includes('Ingen KPI-data ännu.');
  }

  function removeGuide() {
    document.getElementById(GUIDE_ID)?.remove();
  }

  function openConnections() {
    if (typeof window.activateView === 'function') {
      window.activateView('connect');
      return;
    }
    const button = document.querySelector('[data-view="connect"]');
    if (button instanceof HTMLElement) button.click();
  }

  function renderGuide() {
    if (!kpiTableIsEmpty()) {
      removeGuide();
      return;
    }

    const rows = document.getElementById('kpiRows');
    const panel = rows?.closest('.panel');
    if (!panel || document.getElementById(GUIDE_ID)) return;

    const guide = document.createElement('div');
    guide.id = GUIDE_ID;
    guide.className = 'vex-dashboard-first-use';
    guide.setAttribute('role', 'status');
    guide.innerHTML = `
      <div>
        <strong>Kom igång med riktig data</strong>
        <p>Anslut en datakälla så kan Vexmera börja bygga din översikt.</p>
      </div>
      <button type="button" class="ghost" data-vexmera-open-connect>Anslut datakälla</button>
    `;
    guide.querySelector('[data-vexmera-open-connect]')?.addEventListener('click', openConnections);
    panel.prepend(guide);
  }

  function installStyles() {
    if (document.getElementById('vexmera-dashboard-first-use-styles')) return;
    const style = document.createElement('style');
    style.id = 'vexmera-dashboard-first-use-styles';
    style.textContent = `
      .vex-dashboard-first-use {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 16px;
        padding: 14px 16px;
        border: 1px solid var(--line, rgba(255,255,255,.12));
        border-radius: 14px;
        background: var(--panel, rgba(255,255,255,.04));
      }
      .vex-dashboard-first-use p { margin: 4px 0 0; color: var(--muted, currentColor); }
      .vex-dashboard-first-use button { flex: 0 0 auto; min-height: 44px; }
      @media (max-width: 680px) {
        .vex-dashboard-first-use { align-items: stretch; flex-direction: column; }
        .vex-dashboard-first-use button { width: 100%; }
      }
    `;
    document.head.appendChild(style);
  }

  function installDashboardFirstUse() {
    installStyles();

    const original = window.loadDashboard;
    if (typeof original === 'function' && !original.__vexmeraFirstUseGuard) {
      async function guardedLoadDashboard(...args) {
        const result = await original.apply(this, args);
        renderGuide();
        return result;
      }
      guardedLoadDashboard.__vexmeraFirstUseGuard = true;
      guardedLoadDashboard.__vexmeraOriginalLoader = original;
      window.loadDashboard = guardedLoadDashboard;
    }

    queueMicrotask(renderGuide);
  }

  installDashboardFirstUse();
})();
