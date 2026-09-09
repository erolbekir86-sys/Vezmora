(() => {
  'use strict';

  const plans = [
    {key: 'start', label: 'Start', price: '995 kr', button: 'Välj Start'},
    {key: 'growth', label: 'Growth', price: '1 495 kr', button: 'Välj Growth'},
    {key: 'pro', label: 'Pro', price: '2 995 kr', button: 'Välj Pro'},
  ];

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
        // app.js reads dataset.plan at click time, so updating it here also
        // updates the existing Checkout handler without rebinding listeners.
        button.dataset.plan = plan.key;
        button.textContent = plan.button;
        button.setAttribute('aria-label', `${plan.button}, ${plan.price} per månad exklusive moms`);
      }
    });

    const note = grid.nextElementSibling;
    if (note?.classList.contains('fineprint')) {
      note.textContent = 'Priser exkl. moms. Start, Growth och Pro använder samma planmodell på hemsidan, i Vexmera och i Checkout. Betalning öppnas först när den verifierade Stripe-miljön är redo.';
    }
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
  localizeOnboardingProgress();
  addOnboardingNextStep();
  routeCompletedOnboardingToConnections();
})();
