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
      $('onboardingError').textContent = `Kunde inte spara steget: ${err.message}`;
    } finally {
      next.disabled = false;
      next.textContent = previousLabel;
    }
  };
})();
