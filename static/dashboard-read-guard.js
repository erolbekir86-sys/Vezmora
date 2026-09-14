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
  const profileFieldIds = [
    'name',
    'industry',
    'market',
    'website',
    'audience',
    'offer',
    'voice',
    'language',
  ];

  function readPath(path, options = {}) {
    const method = String(options.method || 'GET').toUpperCase();
    if (method !== 'GET') return '';
    return String(path || '').split('?')[0].replace(/\/+$/, '');
  }

  function isDashboardRead(path, options = {}) {
    const pathname = readPath(path, options);
    return pathname.endsWith('/api/dashboard') || pathname.endsWith('/api/kpis');
  }

  function isNotificationRead(path, options = {}) {
    const pathname = readPath(path, options);
    return pathname.endsWith('/api/notifications');
  }

  function isProfileRead(path, options = {}) {
    const pathname = readPath(path, options);
    return pathname.endsWith('/api/company');
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

  function showNotificationReadFailure() {
    const count = document.getElementById('notificationCount');
    if (count) count.textContent = '—';

    const list = document.getElementById('notificationList');
    if (list) {
      list.innerHTML = '<p class="error-text">Aktuella signaler kunde inte verifieras. Försök uppdatera igen.</p>';
    }
  }

  function setProfileReadBlocked(blocked) {
    profileFieldIds.forEach((id) => {
      const field = document.getElementById(id);
      if (field) field.disabled = blocked;
    });

    const state = document.getElementById('profileState');
    if (!state) return;

    if (blocked) {
      state.dataset.readIntegrity = 'error';
      state.textContent = 'Den sparade företagsprofilen kunde inte verifieras. Fälten är låsta tills profilen kan hämtas igen.';
      state.classList.add('error-text');
      return;
    }

    if (state.dataset.readIntegrity === 'error') {
      delete state.dataset.readIntegrity;
      state.textContent = 'Företagsprofilen är verifierad och redo att redigeras.';
      state.classList.remove('error-text');
    }
  }

  api = async function guardedApi(path, options = {}) {
    const profileRead = isProfileRead(path, options);
    try {
      const result = await originalApi(path, options);
      if (profileRead) setProfileReadBlocked(false);
      return result;
    } catch (err) {
      if (isDashboardRead(path, options)) showDashboardReadFailure();
      if (isNotificationRead(path, options)) showNotificationReadFailure();
      if (profileRead) setProfileReadBlocked(true);
      throw err;
    }
  };
})();
