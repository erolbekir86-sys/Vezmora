(() => {
  'use strict';

  const PROVIDERS = ['google', 'meta'];

  function safeCount(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
  }

  function warningTexts(lastSync) {
    return Array.isArray(lastSync?.warnings)
      ? lastSync.warnings.map((value) => String(value).toLowerCase())
      : [];
  }

  function isFailedSync(lastSync) {
    if (!lastSync || typeof lastSync !== 'object' || Array.isArray(lastSync)) return false;
    if (lastSync.error || lastSync.ok === false || lastSync.success === false) return true;
    const status = Number(lastSync.status || 0);
    return Number.isFinite(status) && status >= 400;
  }

  function classifyLastSync(lastSync) {
    if (!lastSync || typeof lastSync !== 'object' || Array.isArray(lastSync)) return 'unsynced';
    if (isFailedSync(lastSync)) return 'error';

    const rows =
      safeCount(lastSync.campaign_rows) +
      safeCount(lastSync.ads_rows) +
      safeCount(lastSync.analytics_rows);
    const warnings = warningTexts(lastSync);
    const hasWarning = warnings.length > 0;
    const explicitEmpty = warnings.some((text) => text.includes('no campaign data found'));
    const blockingWarning = warnings.some(
      (text) => text.includes('sync failed') || text.includes('access token') || text.includes('reconnect')
    );

    if (blockingWarning && rows === 0) return 'error';
    if (rows > 0 && hasWarning) return 'data-warning';
    if (rows > 0) return 'data';
    if (explicitEmpty || rows === 0) return 'empty';
    return 'unsynced';
  }

  function stateCopy(state) {
    const states = {
      unsynced: {
        label: 'Ansluten · inte synkad',
        detail: 'Kör Synka för att hämta den första read-only-datan.',
        className: 'vex-state-unsynced',
      },
      data: {
        label: 'Data mottagen',
        detail: 'Senaste synken gav användbar data till Vexmera.',
        className: 'vex-state-data',
      },
      'data-warning': {
        label: 'Data mottagen · kontroll behövs',
        detail: 'Viss data kom in, men anslutningen behöver kontrolleras innan resultatet behandlas som komplett.',
        className: 'vex-state-warning',
      },
      empty: {
        label: 'Ansluten · ingen kampanjdata',
        detail: 'Anslutningen kan vara frisk. Prova en annan synkperiod eller kontrollera att kontot har aktivitet.',
        className: 'vex-state-empty',
      },
      error: {
        label: 'Synkfel',
        detail: 'Senaste synken kunde inte slutföras. Kontrollera anslutningen och försök igen.',
        className: 'vex-state-error',
      },
    };
    return states[state] || states.unsynced;
  }

  function installStyles() {
    if (document.getElementById('vexmera-connector-state-styles')) return;
    const style = document.createElement('style');
    style.id = 'vexmera-connector-state-styles';
    style.textContent = `
      #connectorGrid .state-pill.vex-state-data{color:var(--ok)}
      #connectorGrid .state-pill.vex-state-warning{color:var(--accent)}
      #connectorGrid .state-pill.vex-state-empty{color:var(--muted)}
      #connectorGrid .state-pill.vex-state-error{color:var(--danger)}
      #connectorGrid .vex-connector-state-detail{margin-top:10px;line-height:1.5}
    `;
    document.head.appendChild(style);
  }

  function applyProviderState(provider, connection) {
    const button = document.querySelector(`#connectorGrid [data-sync="${provider}"]`);
    const card = button?.closest('.connector-card');
    if (!card || connection?.status !== 'connected') return;

    const lastSync = connection?.metadata?.last_sync;
    const state = classifyLastSync(lastSync);
    const copy = stateCopy(state);
    const pill = card.querySelector('.state-pill');
    if (pill) {
      [...pill.classList]
        .filter((name) => name.startsWith('vex-state-'))
        .forEach((name) => pill.classList.remove(name));
      pill.classList.add(copy.className);
      pill.textContent = copy.label;
      pill.setAttribute('aria-label', copy.label);
    }

    let detail = card.querySelector('.vex-connector-state-detail');
    if (!detail) {
      detail = document.createElement('p');
      detail.className = 'fineprint vex-connector-state-detail';
      const actions = card.querySelector('.card-actions');
      if (actions) card.insertBefore(detail, actions);
      else card.appendChild(detail);
    }
    detail.textContent = copy.detail;
    detail.dataset.syncState = state;
  }

  async function enrichPersistentConnectorStates() {
    if (typeof api !== 'function' || typeof ws !== 'function') return;
    try {
      const data = await api(ws('/api/connectors'));
      if (!data || typeof data !== 'object' || Array.isArray(data)) return;
      PROVIDERS.forEach((provider) => applyProviderState(provider, data[provider]?.connection));
    } catch (_) {
      // Do not replace the existing connector UI with raw fetch/provider errors.
    }
  }

  function installConnectorStateGuard() {
    const originalLoadConnectors = typeof window.loadConnectors === 'function' ? window.loadConnectors : null;
    if (!originalLoadConnectors || originalLoadConnectors.__vexmeraPersistentStates) return;

    async function guardedLoadConnectors(...args) {
      const result = await originalLoadConnectors.apply(this, args);
      await enrichPersistentConnectorStates();
      return result;
    }

    guardedLoadConnectors.__vexmeraPersistentStates = true;
    window.loadConnectors = guardedLoadConnectors;
  }

  function loadDisconnectUi() {
    if (document.querySelector('script[data-vexmera-disconnect-ui]')) return;
    const script = document.createElement('script');
    const build = encodeURIComponent(window.__VEXMERA_BUILD__ || 'local');
    script.src = `/static/connector-disconnect-ui.js?build=${build}`;
    script.defer = true;
    script.dataset.vexmeraDisconnectUi = 'true';
    document.head.appendChild(script);
  }

  installStyles();
  installConnectorStateGuard();
  loadDisconnectUi();
  if (document.querySelector('#connectorGrid .connector-card')) {
    enrichPersistentConnectorStates();
  }
})();
