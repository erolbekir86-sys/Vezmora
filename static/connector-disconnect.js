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
      await Promise.all([
        originalLoadConnectors(),
        typeof loadDashboard === 'function' ? loadDashboard() : Promise.resolve(),
      ]);
    } catch (_) {
      window.alert('Kunde inte koppla från kontot. Försök igen.');
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
