(() => {
  'use strict';

  const params = new URLSearchParams(window.location.search);
  const result = params.get('billing');
  if (result !== 'success' && result !== 'cancelled') return;

  // Checkout Session IDs are not needed after the browser returns to Vexmera.
  // Remove the billing return markers before showing feedback so refreshes do
  // not repeat stale messages or retain provider identifiers in the address bar.
  params.delete('billing');
  params.delete('session_id');
  const query = params.toString();
  const cleanUrl = `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash || ''}`;
  window.history.replaceState({}, '', cleanUrl);

  const message = result === 'success'
    ? 'Checkout slutförd. Vexmera verifierar abonnemangsstatus via Stripe innan planen uppdateras.'
    : 'Checkout avbröts. Inga abonnemangsändringar genomfördes.';

  if (typeof window.vexmeraToast === 'function') {
    window.vexmeraToast(message);
  }
})();
