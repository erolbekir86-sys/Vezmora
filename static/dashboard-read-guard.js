(() => {
  if (typeof api !== 'function') return;

  const originalApi = api;
  const guardedMetricIds = [
    'metricRevenue',
    'metricSpend',
    'metricRoas',
    'metricLeads',
    'metricConversions',
    'metricCtr',
    'metricApprovals',
    'metricAlerts',
    'metricAnomalies',
  ];

  function isDashboardRead(path, options = {}) {
    const method = String(options.method || 'GET').toUpperCase();
    if (method !== 'GET') return false;
    const value = String(path || '');
    const pathname = value.split('?')[0].replace(/\/+$/, '');
    return pathname.endsWith('/api/dashboard') || pathname.endsWith('/api/kpis');
  }

  function showDashboardReadFailure() {
    guardedMetricIds.forEach((id) => {
      const node = document.getElementById(id);
      if (node) node.textContent = '—';
    });

    const rows = document.getElementById('kpiRows');
    if (rows) {
      rows.innerHTML = '<tr><td colspan="8" class="error-text">Kunde inte hämta aktuell data. Försök uppdatera igen.</td></tr>';
    }

    const bars = document.getElementById('kpiBars');
    if (bars) {
      bars.innerHTML = '<p class="error-text">Aktuell KPI-data kunde inte verifieras.</p>';
    }
  }

  api = async function guardedApi(path, options = {}) {
    try {
      return await originalApi(path, options);
    } catch (err) {
      if (isDashboardRead(path, options)) showDashboardReadFailure();
      throw err;
    }
  };
})();

(() => {
  if (typeof loadConnectors !== 'function' || typeof api !== 'function' || typeof ws !== 'function') return;

  const originalLoadConnectors = loadConnectors;

  async function disconnectConnector(provider, button) {
    if (!['google', 'meta'].includes(provider)) return;
    const label = provider === 'google' ? 'Google' : 'Meta';
    if (!window.confirm(`Koppla från ${label}? Vexmera tar bort sparade anslutningsuppgifter och stoppar framtida synkning. Redan synkad rapporthistorik behålls.`)) return;

    const oldText = button.textContent;
    button.disabled = true;
    button.textContent = 'Kopplar från…';
    try {
      await api(ws(`/api/connectors/${provider}/disconnect`), { method: 'POST' });
      window.alert(`${label} är frånkopplat. Du kan nu ansluta kontot igen.`);
      await Promise.all([originalLoadConnectors(), typeof loadDashboard === 'function' ? loadDashboard() : Promise.resolve()]);
    } catch (err) {
      window.alert(err?.message || 'Kunde inte koppla från kontot.');
      button.disabled = false;
      button.textContent = oldText;
    }
  }

  function addDisconnectButtons() {
    document.querySelectorAll('[data-connect]').forEach((connectButton) => {
      const provider = connectButton.dataset.connect;
      if (!['google', 'meta'].includes(provider)) return;
      if (connectButton.textContent.trim().toLowerCase() !== 'connected') return;
      const actions = connectButton.closest('.card-actions');
      if (!actions || actions.querySelector(`[data-disconnect="${provider}"]`)) return;

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'ghost danger';
      button.dataset.disconnect = provider;
      button.textContent = 'Koppla från';
      button.addEventListener('click', () => disconnectConnector(provider, button));
      actions.appendChild(button);
    });
  }

  loadConnectors = async function loadConnectorsWithDisconnect() {
    const result = await originalLoadConnectors.apply(this, arguments);
    addDisconnectButtons();
    return result;
  };
})();
