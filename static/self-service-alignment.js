(() => {
  'use strict';

  const plans = [
    {key: 'start', label: 'Start', price: '995 kr', button: 'Välj Start'},
    {key: 'growth', label: 'Growth', price: '1 495 kr', button: 'Välj Growth'},
    {key: 'pro', label: 'Pro', price: '2 995 kr', button: 'Välj Pro'},
  ];

  const checkoutClosedMessage = 'Betalning öppnas när den verifierade Stripe-miljön är redo.';

  function setCheckoutAvailability(ready) {
    document.querySelectorAll('#team .plan-button').forEach((button) => {
      button.disabled = ready !== true;
      button.dataset.checkoutReady = ready === true ? 'true' : 'false';
      if (ready === true) {
        button.removeAttribute('title');
      } else {
        button.title = checkoutClosedMessage;
      }
    });

    const grid = document.querySelector('#team .plan-grid');
    const note = grid?.nextElementSibling;
    if (note?.classList.contains('fineprint')) {
      note.textContent = ready === true
        ? 'Priser exkl. moms. Start, Growth och Pro använder samma planmodell på hemsidan, i Vexmera och i Checkout.'
        : `Priser exkl. moms. ${checkoutClosedMessage}`;
    }
  }

  function alignBillingPlans() {
    const grid = document.querySelector('#team .plan-grid');
    if (!grid) return;

    const cards = [...grid.querySelectorAll('.plan-card')];
    plans.forEach((plan, index) => {
      const card = cards[index];
      if (!card) return;
      const label = card.querySelector('span');
      const price = card.querySelector('strong');
      const button = card.querySelector('.plan-button');
      if (label) label.textContent = plan.label;
      if (price) price.textContent = plan.price;
      if (button) {
        button.dataset.plan = plan.key;
        button.textContent = plan.button;
        button.setAttribute('aria-label', `${plan.button}, ${plan.price} per månad exklusive moms`);
      }
    });

    setCheckoutAvailability(false);
  }

  function installCheckoutReadinessGuard() {
    const originalLoadTeam = typeof window.loadTeam === 'function' ? window.loadTeam : null;
    if (!originalLoadTeam || originalLoadTeam.__vexmeraCheckoutGuarded) return;

    async function guardedLoadTeam(...args) {
      setCheckoutAvailability(false);
      await originalLoadTeam.apply(this, args);

      if (typeof api !== 'function' || typeof ws !== 'function') return;
      try {
        const billing = await api(ws('/api/billing'));
        setCheckoutAvailability(billing?.checkout_ready === true);
      } catch (_) {
        setCheckoutAvailability(false);
      }
    }

    guardedLoadTeam.__vexmeraCheckoutGuarded = true;
    window.loadTeam = guardedLoadTeam;
  }

  function renderRuntimeStatus(payload) {
    const status = document.getElementById('status');
    if (!status) return;

    if (payload?.ok === true) {
      const version = payload.version ? ` · v${payload.version}` : '';
      status.textContent = `System online${version}`;
      status.style.color = 'var(--ok)';
      return;
    }

    status.textContent = 'Systemstatus kunde inte verifieras.';
    status.style.color = 'var(--danger)';
  }

  function installRuntimeStatusGuard() {
    if (typeof api !== 'function') return;

    async function guardedLoadSystemStatus() {
      try {
        const payload = await api('/health');
        renderRuntimeStatus(payload);
      } catch (_) {
        renderRuntimeStatus(null);
      }
    }

    guardedLoadSystemStatus.__vexmeraMinimalHealthAware = true;
    window.loadSystemStatus = guardedLoadSystemStatus;
  }

  function installBriefSchedulerStatusGuard() {
    const originalLoadBrief = typeof window.loadBrief === 'function' ? window.loadBrief : null;
    if (!originalLoadBrief || originalLoadBrief.__vexmeraMinimalHealthAware || typeof api !== 'function') return;

    async function guardedLoadBrief(...args) {
      const result = await originalLoadBrief.apply(this, args);
      const state = document.getElementById('briefSchedulerState');
      if (!state) return result;

      try {
        const health = await api('/health');
        if (!Object.prototype.hasOwnProperty.call(health || {}, 'scheduler_enabled')) {
          state.textContent = 'Schemaläggarstatus hanteras i drift och visas inte i den publika produktvyn.';
        }
      } catch (_) {
        state.textContent = 'Schemaläggarstatus kunde inte verifieras.';
      }
      return result;
    }

    guardedLoadBrief.__vexmeraMinimalHealthAware = true;
    window.loadBrief = guardedLoadBrief;
  }

  function providerSyncSummary(label, result) {
    if (!result || typeof result !== 'object' || Array.isArray(result)) {
      return `${label}: synkresultatet kunde inte verifieras.`;
    }
    if (result.error) return `${label}: synken kunde inte slutföras.`;

    const rowCandidates = [result.campaign_rows, result.analytics_rows, result.ads_rows]
      .map((value) => Number(value))
      .filter((value) => Number.isFinite(value) && value >= 0);
    const rows = rowCandidates.reduce((total, value) => total + value, 0);
    const warningCount = Array.isArray(result.warnings) ? result.warnings.length : 0;
    const rowText = rows > 0 ? ` ${rows} datapunkter mottagna.` : ' Synken slutfördes.';
    const warningText = warningCount > 0 ? ' Kontrollera anslutningsinställningarna eftersom synken gav en varning.' : '';
    return `${label}:${rowText}${warningText}`;
  }

  function summarizeConnectorSync(payload) {
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
      return 'Synkningen slutfördes, men resultatet kunde inte verifieras. Uppdatera sidan innan du använder datan.';
    }
    return [
      providerSyncSummary('Google', payload.google),
      providerSyncSummary('Meta', payload.meta),
    ].join(' ');
  }

  function showCustomerSyncMessage(message) {
    if (typeof window.vexmeraToast === 'function') {
      window.vexmeraToast(message);
    } else if (typeof window.alert === 'function') {
      window.alert(message);
    }
  }

  function connectorProviderLabel(provider) {
    if (provider === 'google') return 'Google';
    if (provider === 'meta') return 'Meta';
    return 'Datakällan';
  }

  async function runIndividualConnectorSync(button) {
    const provider = String(button?.dataset?.sync || '').toLowerCase();
    if (!button || !['google', 'meta'].includes(provider) || typeof api !== 'function' || typeof ws !== 'function') return;

    button.disabled = true;
    const previousText = button.textContent;
    button.textContent = 'Synkar…';
    try {
      const result = await api(ws(`/api/connectors/${provider}/sync`), {
        method: 'POST',
        body: JSON.stringify({days: typeof selectedSyncDays === 'function' ? selectedSyncDays() : 30}),
      });
      showCustomerSyncMessage(providerSyncSummary(connectorProviderLabel(provider), result));
      if (typeof loadDashboard === 'function') await loadDashboard();
      if (typeof window.loadConnectors === 'function') await window.loadConnectors();
    } catch (_) {
      showCustomerSyncMessage(`${connectorProviderLabel(provider)}: synken kunde inte slutföras. Kontrollera anslutningen och försök igen.`);
    } finally {
      if (button.isConnected) {
        button.disabled = false;
        button.textContent = previousText;
      }
    }
  }

  function bindIndividualConnectorSyncFeedback() {
    document.querySelectorAll('#connectorGrid [data-sync]').forEach((button) => {
      const provider = String(button.dataset.sync || '').toLowerCase();
      if (!['google', 'meta'].includes(provider) || button.dataset.vexmeraSafeSync === 'true') return;
      button.dataset.vexmeraSafeSync = 'true';
      button.onclick = () => runIndividualConnectorSync(button);
    });
  }

  function installConnectorSyncFeedbackGuard() {
    const originalSyncAll = typeof window.syncAll === 'function' ? window.syncAll : null;
    if (originalSyncAll && !originalSyncAll.__vexmeraFeedbackGuarded) {
      async function guardedSyncAll(button) {
        if (!button || typeof api !== 'function' || typeof ws !== 'function') return;
        button.disabled = true;
        const previousText = button.textContent;
        button.textContent = 'Synkar…';
        try {
          const result = await api(ws('/api/connectors/all/sync'), {
            method: 'POST',
            body: JSON.stringify({days: typeof selectedSyncDays === 'function' ? selectedSyncDays() : 30}),
          });
          showCustomerSyncMessage(summarizeConnectorSync(result));
          if (typeof loadDashboard === 'function' && typeof loadConnectors === 'function') {
            await Promise.all([loadDashboard(), loadConnectors()]);
          }
        } catch (_) {
          showCustomerSyncMessage('Synkningen kunde inte slutföras. Kontrollera anslutningarna och försök igen.');
        } finally {
          button.disabled = false;
          button.textContent = previousText;
        }
      }

      guardedSyncAll.__vexmeraFeedbackGuarded = true;
      window.syncAll = guardedSyncAll;
    }

    const originalLoadConnectors = typeof window.loadConnectors === 'function' ? window.loadConnectors : null;
    if (originalLoadConnectors && !originalLoadConnectors.__vexmeraFeedbackGuarded) {
      async function guardedLoadConnectors(...args) {
        const result = await originalLoadConnectors.apply(this, args);
        bindIndividualConnectorSyncFeedback();
        return result;
      }
      guardedLoadConnectors.__vexmeraFeedbackGuarded = true;
      window.loadConnectors = guardedLoadConnectors;
    }

    bindIndividualConnectorSyncFeedback();
  }

  function localizeOnboardingProgress() {
    if (typeof renderOnboardingStep !== 'function') return;
    const originalRender = renderOnboardingStep;
    renderOnboardingStep = function alignedRenderOnboardingStep() {
      originalRender();
      const label = document.getElementById('onboardingStepLabel');
      if (label && typeof onboardingStep !== 'undefined') label.textContent = `Steg ${onboardingStep} av 3`;
    };
    renderOnboardingStep();
  }

  function addOnboardingNextStep() {
    const step = document.querySelector('[data-onboarding-step="3"]');
    if (!step || step.querySelector('[data-vexmera-onboarding-next-step]')) return;

    const note = document.createElement('p');
    note.className = 'fineprint';
    note.dataset.vexmeraOnboardingNextStep = 'true';
    note.textContent = 'Nästa steg: koppla Google eller Meta under Anslutningar. Under privat beta läser Vexmera data och ger rekommendationer utan att ändra kampanjer, budgetar eller bud automatiskt.';
    step.appendChild(note);
  }

  function routeCompletedOnboardingToConnections() {
    const finish = document.getElementById('onboardingFinish');
    const modal = document.getElementById('onboardingModal');
    if (!finish || !modal || typeof finish.onclick !== 'function' || finish.dataset.vexmeraAligned === 'true') return;

    const originalFinish = finish.onclick;
    finish.dataset.vexmeraAligned = 'true';
    finish.onclick = async function alignedOnboardingFinish(event) {
      await originalFinish.call(this, event);
      if (!modal.classList.contains('hidden')) return;

      if (typeof activateView === 'function') activateView('connect');
      if (typeof loadConnectors === 'function') {
        try { await loadConnectors(); } catch (_) {}
      }
      if (typeof window.vexmeraToast === 'function') {
        window.vexmeraToast('Företagsprofilen är klar. Koppla nu en datakälla för att få verkliga insikter i Vexmera.');
      }
    };
  }

  alignBillingPlans();
  installCheckoutReadinessGuard();
  installRuntimeStatusGuard();
  installBriefSchedulerStatusGuard();
  installConnectorSyncFeedbackGuard();
  localizeOnboardingProgress();
  addOnboardingNextStep();
  routeCompletedOnboardingToConnections();
})();
