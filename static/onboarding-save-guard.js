(() => {
  const next = document.getElementById('onboardingNext');
  if (!next || typeof onboardingPayload !== 'function' || typeof api !== 'function') return;

  next.onclick = async () => {
    const payload = onboardingPayload();
    if (onboardingStep === 1 && (!payload.company_name || !payload.industry || !payload.offer)) {
      $('onboardingError').textContent = 'Fyll i företagsnamn, bransch och erbjudande.';
      return;
    }
    if (onboardingStep === 2 && !payload.audience) {
      $('onboardingError').textContent = 'Beskriv målgruppen innan du fortsätter.';
      return;
    }

    $('onboardingError').textContent = '';
    next.disabled = true;
    const previousLabel = next.textContent;
    next.textContent = 'Sparar…';
    try {
      await api(ws('/api/onboarding'), {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
      onboardingStep = Math.min(3, onboardingStep + 1);
      renderOnboardingStep();
    } catch (err) {
      // Do not surface raw API/provider error text in the onboarding UI. The user
      // only needs a safe, actionable retry message; detailed diagnostics stay in
      // the existing protected diagnostic paths.
      $('onboardingError').textContent = 'Kunde inte spara steget. Kontrollera anslutningen och försök igen.';
    } finally {
      next.disabled = false;
      next.textContent = previousLabel;
    }
  };
})();
