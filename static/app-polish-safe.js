(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);

  // Stability-first product polish. The previous helper observed the entire app
  // DOM (including characterData) and rescanned large dynamic regions after
  // every mutation. During bootstrap several panels update in parallel, which
  // can create a mutation storm and make the product tab appear frozen.
  // Keep this helper deliberately one-shot and event-driven.

  const pageMeta = {
    dashboard: ['Översikt.', 'Beslut, signaler och nästa drag på ett ställe.'],
    agent: ['Core.', 'Din AI Marketing Officer med permanent affärskontext.'],
    strategy: ['Pulse.', 'Bygg en mätbar tillväxtplan från verkliga signaler.'],
    campaign: ['Launch.', 'Från idé till kampanjförslag redo för godkännande.'],
    brief: ['Brief.', 'Din dagliga ledningsbrief för marknadsföringen.'],
    queue: ['Godkännanden.', 'Mänsklig kontroll före externa åtgärder.'],
    autopilot: ['Autopilot.', 'Bestäm exakt hur mycket Vexmera får göra inom dina gränser.'],
    rivals: ['Konkurrenter.', 'Bevaka publika förändringar hos konkurrenter.'],
    connect: ['Anslutningar.', 'Koppla och synka dina marknadsföringskällor.'],
    insights: ['Insikter.', 'Kampanjresultat, avvikelser och datakörningar.'],
    team: ['Team.', 'Medlemmar, plan, basvaluta och valutakurser.'],
    profile: ['Varumärkesprofil.', 'Företagsprofilen följer med i Vexmeras analyser.']
  };

  function applyPageMeta(view) {
    const meta = pageMeta[view];
    if (!meta) return;
    if ($('pageTitle')) $('pageTitle').textContent = meta[0];
    if ($('pageLead')) $('pageLead').textContent = meta[1];
  }

  document.querySelectorAll('.nav[data-view]').forEach((button) => {
    button.addEventListener('click', () => applyPageMeta(button.dataset.view));
  });
  applyPageMeta(document.querySelector('.nav.active')?.dataset.view || 'dashboard');

  let toastStack = document.querySelector('.vex-toast-stack');
  if (!toastStack) {
    toastStack = document.createElement('div');
    toastStack.className = 'vex-toast-stack';
    toastStack.setAttribute('aria-live', 'polite');
    document.body.appendChild(toastStack);
  }

  function toast(message, timeout = 6500) {
    const text = typeof message === 'string' ? message : JSON.stringify(message, null, 2);
    const node = document.createElement('div');
    node.className = 'vex-toast';
    node.innerHTML = '<span class="vex-toast-icon">V</span><p></p><button type="button" aria-label="Stäng">×</button>';
    node.querySelector('p').textContent = text;
    const close = () => node.remove();
    node.querySelector('button').addEventListener('click', close);
    toastStack.appendChild(node);
    if (timeout) window.setTimeout(close, timeout);
  }

  window.vexmeraToast = toast;
  window.alert = (message) => toast(message);

  const runAutopilot = $('runAutopilotOnce');
  if (runAutopilot) {
    runAutopilot.title = 'Kör endast en policykontroll. Extern körning styrs fortfarande av serverns säkerhetsspärrar.';
  }

  document.documentElement.dataset.vexmeraAppPolishStable = '1';
})();
