(() => {
  'use strict';

  const allowedPlans = new Set(['start', 'growth', 'pro']);
  const params = new URLSearchParams(window.location.search);
  const requestedPlan = String(params.get('plan') || '').trim().toLowerCase();

  if (!requestedPlan) return;

  function replaceUrlWithoutPlan() {
    const clean = new URLSearchParams(window.location.search);
    clean.delete('plan');
    const query = clean.toString();
    history.replaceState({}, '', `${window.location.pathname}${query ? `?${query}` : ''}`);
  }

  if (!allowedPlans.has(requestedPlan)) {
    replaceUrlWithoutPlan();
    return;
  }

  const appShell = document.getElementById('appShell');
  if (!appShell) return;

  let started = false;
  let observer = null;

  async function tryStartCheckout() {
    if (started) return;
    if (typeof currentWorkspaceId === 'undefined' || !currentWorkspaceId) return;
    if (typeof api !== 'function' || typeof ws !== 'function' || typeof startCheckout !== 'function') return;

    started = true;
    if (observer) observer.disconnect();
    replaceUrlWithoutPlan();

    if (typeof activateView === 'function') activateView('team');

    try {
      const billing = await api(ws('/api/billing'));
      if (billing?.checkout_ready !== true) {
        if (typeof loadTeam === 'function') {
          try { await loadTeam(); } catch (_) {}
        }
        return;
      }
    } catch (_) {
      if (typeof loadTeam === 'function') {
        try { await loadTeam(); } catch (_) {}
      }
      return;
    }

    await startCheckout(requestedPlan);
  }

  observer = new MutationObserver(() => { void tryStartCheckout(); });
  observer.observe(appShell, {attributes: true, attributeFilter: ['class']});
  void tryStartCheckout();

  // Logged-out users keep ?plan=... through the normal login/register reload.
  // Stop observing after bootstrap has had ample time; the next page load resumes.
  window.setTimeout(() => observer?.disconnect(), 15_000);
})();
