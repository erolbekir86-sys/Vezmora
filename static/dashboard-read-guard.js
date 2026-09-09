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
    return value.includes('/api/dashboard') || value.includes('/api/kpis?');
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
