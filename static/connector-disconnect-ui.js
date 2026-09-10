(() => {
  'use strict';

  const PROVIDERS = ['google', 'meta'];
  let workspaceRoles = null;

  function providerLabel(provider) {
    return provider === 'google' ? 'Google' : provider === 'meta' ? 'Meta' : 'Datakällan';
  }

  function showMessage(message) {
    if (typeof window.vexmeraToast === 'function') window.vexmeraToast(message);
    else if (typeof window.alert === 'function') window.alert(message);
  }

  async function loadWorkspaceRoles() {
    if (workspaceRoles instanceof Map) return workspaceRoles;
    if (typeof api !== 'function') return new Map();

    try {
      const me = await api('/api/auth/me');
      const roles = new Map();
      const workspaces = Array.isArray(me?.workspaces) ? me.workspaces : [];
      workspaces.forEach((workspace) => {
        const id = Number(workspace?.id);
        const role = String(workspace?.role || '').toLowerCase();
        if (Number.isFinite(id) && role) roles.set(id, role);
      });
      workspaceRoles = roles;
      return roles;
    } catch (_) {
      // Fail closed: do not expose a destructive credential control when role
      // information cannot be verified.
      return new Map();
    }
  }

  async function disconnectProvider(provider, button) {
    if (!PROVIDERS.includes(provider) || typeof api !== 'function' || typeof ws !== 'function') return;
    if (typeof window.confirm !== 'function') return;

    const label = providerLabel(provider);
    const confirmed = window.confirm(
      `Koppla från ${label}? Vexmera tar bort sparade anslutningsuppgifter och försöker återkalla åtkomsten hos leverantören. Tidigare synkad historik behålls.`
    );
    if (!confirmed) return;

    const previousText = button.textContent;
    button.disabled = true;
    button.textContent = 'Kopplar från…';

    try {
      const result = await api(ws(`/api/connectors/${provider}/disconnect`), {method: 'POST'});
      if (result?.provider_revoke_attempted === true && result?.provider_revoke_succeeded === false) {
        showMessage(`${label} är frånkopplad i Vexmera. Lokal åtkomst är borttagen, men leverantörens återkallning kunde inte bekräftas.`);
      } else {
        showMessage(`${label} är frånkopplad. Tidigare synkhistorik finns kvar i workspacet.`);
      }
      if (typeof window.loadConnectors === 'function') await window.loadConnectors();
    } catch (_) {
      showMessage(`Det gick inte att koppla från ${label}. Försök igen. Endast owner eller admin kan ändra anslutningen.`);
    } finally {
      if (button.isConnected) {
        button.disabled = false;
        button.textContent = previousText;
      }
    }
  }

  async function bindDisconnectControls() {
    if (typeof currentWorkspaceId === 'undefined' || currentWorkspaceId == null) return;
    const roles = await loadWorkspaceRoles();
    const role = roles.get(Number(currentWorkspaceId));
    const allowed = role === 'owner' || role === 'admin';

    PROVIDERS.forEach((provider) => {
      const syncButton = document.querySelector(`#connectorGrid [data-sync="${provider}"]`);
      const card = syncButton?.closest('.connector-card');
      if (!card) return;

      const connected = syncButton.disabled === false;
      const existing = card.querySelector('[data-vexmera-disconnect]');
      if (!allowed || !connected) {
        if (existing) existing.remove();
        return;
      }
      if (existing) return;

      const actions = card.querySelector('.card-actions');
      if (!actions) return;

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'ghost danger vexmera-disconnect';
      button.dataset.vexmeraDisconnect = provider;
      button.textContent = 'Koppla från';
      button.setAttribute('aria-label', `Koppla från ${providerLabel(provider)}`);
      button.onclick = () => disconnectProvider(provider, button);
      actions.appendChild(button);
    });
  }

  function installDisconnectGuard() {
    const originalLoadConnectors = typeof window.loadConnectors === 'function' ? window.loadConnectors : null;
    if (!originalLoadConnectors || originalLoadConnectors.__vexmeraDisconnectUi) return;

    async function guardedLoadConnectors(...args) {
      const result = await originalLoadConnectors.apply(this, args);
      await bindDisconnectControls();
      return result;
    }

    guardedLoadConnectors.__vexmeraDisconnectUi = true;
    window.loadConnectors = guardedLoadConnectors;
  }

  installDisconnectGuard();
  if (document.querySelector('#connectorGrid .connector-card')) bindDisconnectControls();
})();
