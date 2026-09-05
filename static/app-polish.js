(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);

  const pageMetaSv = {
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
    const meta = pageMetaSv[view];
    if (!meta) return;
    if ($('pageTitle')) $('pageTitle').textContent = meta[0];
    if ($('pageLead')) $('pageLead').textContent = meta[1];
  }

  document.querySelectorAll('.nav[data-view]').forEach((button) => {
    button.addEventListener('click', () => queueMicrotask(() => applyPageMeta(button.dataset.view)));
  });
  applyPageMeta(document.querySelector('.nav.active')?.dataset.view || 'dashboard');

  /* Keep the AI-response language selector clearly separate from UI language. */
  const language = $('language');
  if (language && !language.closest('.header-language-control')) {
    const wrap = document.createElement('label');
    wrap.className = 'header-language-control';
    wrap.setAttribute('aria-label', 'Språk för AI-svar');
    const label = document.createElement('span');
    label.textContent = 'AI-svar';
    language.parentNode.insertBefore(wrap, language);
    wrap.append(label, language);
    language.setAttribute('aria-label', 'Språk för AI-svar');
  }

  /* Add a quiet, truthful beta badge when older markup does not already have one. */
  document.querySelectorAll('.brand').forEach((brand) => {
    const copy = brand.querySelector('div:last-child');
    if (!copy || copy.querySelector('.beta-brand-badge')) return;
    const badge = document.createElement('span');
    badge.className = 'beta-brand-badge';
    badge.textContent = 'Privat beta';
    copy.appendChild(badge);
  });

  const exactPairs = new Map([
    ['Connected', 'Ansluten'],
    ['Ready to connect', 'Redo att ansluta'],
    ['Needs setup', 'Kräver konfiguration'],
    ['Connect', 'Anslut'],
    ['Sync', 'Synka'],
    ['Never synced', 'Aldrig synkad'],
    ['Approve', 'Godkänn'],
    ['Reject', 'Avvisa'],
    ['Preview', 'Förhandsgranska'],
    ['Execute', 'Utför'],
    ['Scan', 'Skanna'],
    ['Refresh', 'Uppdatera'],
    ['Suggest', 'Föreslå'],
    ['Assisted', 'Assisterad'],
    ['ENABLED', 'AKTIVERAD'],
    ['LOCKED', 'LÅST'],
    ['BLOCKED IN BETA', 'BLOCKERAD I BETA'],
    ['Platform', 'Plattform'],
    ['Campaign', 'Kampanj'],
    ['Spend', 'Kostnad'],
    ['Revenue', 'Omsättning'],
    ['Action', 'Åtgärd'],
    ['Request pause', 'Begär paus'],
    ['Sync-period', 'Synkperiod'],
    ['Pending', 'Väntar'],
    ['pending', 'väntar'],
    ['Approved', 'Godkänd'],
    ['approved', 'godkänd'],
    ['Rejected', 'Avvisad'],
    ['rejected', 'avvisad'],
    ['Executed', 'Utförd'],
    ['executed', 'utförd'],
    ['Failed', 'Misslyckad'],
    ['failed', 'misslyckad'],
    ['trialing', 'provperiod'],
    ['active', 'aktiv'],
    ['canceled', 'avslutad'],
    ['unpaid', 'obetald'],
    ['past_due', 'förfallen'],
    ['marketer', 'marknadsförare'],
    ['admin', 'administratör'],
    ['viewer', 'läsbehörighet'],
    ['high', 'hög'],
    ['medium', 'medel'],
    ['low', 'låg'],
    ['internal', 'internt'],
    ['google_ads', 'Google Ads'],
    ['meta_ads', 'Meta Ads'],
    ['google_analytics', 'Google Analytics'],
    ['sync_all', 'Synka alla'],
    ['detect_anomalies', 'Upptäck avvikelser'],
    ['No anomalies detected.', 'Inga avvikelser upptäckta.'],
    ['No worker jobs yet.', 'Inga datakörningar ännu.'],
    ['No campaign-level rows yet. Sync Google or Meta.', 'Ingen kampanjdata ännu. Synka Google eller Meta.'],
    ['No priority signals yet.', 'Inga prioriterade signaler ännu.'],
    ['No FX rates saved.', 'Inga valutakurser sparade.'],
    ['Core could not load priorities', 'Core kunde inte ladda prioriteringarna'],
    ['Your growth priorities', 'Dina tillväxtprioriteringar'],
    ['Inga actions i denna vy.', 'Inga åtgärder i den här vyn.'],
    ['Brief schema sparat.', 'Brief-schemat är sparat.'],
    ['Execute this already-approved external action?', 'Utför den här redan godkända externa åtgärden?'],
    ['Open', 'Öppna']
  ]);

  const phrasePairs = [
    ['OAuth credentials detected.', 'OAuth-konfiguration hittad.'],
    ['Last sync:', 'Senast synkad:'],
    ['Missing:', 'Saknas:'],
    ['Checked ', 'Kontrollerad '],
    [' · change detected', ' · förändring upptäckt'],
    [' · stable', ' · stabil'],
    ['Not scanned yet', 'Inte skannad ännu'],
    ['Scheduler is enabled in this runtime.', 'Schemaläggaren är aktiverad i den här miljön.'],
    ['Scheduler is disabled in this runtime; manual brief still works.', 'Schemaläggaren är avstängd i den här miljön. Manuell brief fungerar fortfarande.'],
    ['External execution', 'Extern körning'],
    ['Autopilot worker execution', 'Autopilot-körning'],
    ['High-risk autonomous actions', 'Autonoma högriskåtgärder'],
    ['Invite queued for email delivery.', 'Inbjudan är köad för e-postleverans.'],
    ['Invite created, but SMTP is not configured on this runtime.', 'Inbjudan skapades, men e-post är inte konfigurerad i den här miljön.'],
    ['Password updated. You can log in now.', 'Lösenordet är uppdaterat. Du kan logga in nu.'],
    ['Core is checking your workspace.', 'Core granskar ditt workspace.'],
    ['Loading your priorities…', 'Laddar dina prioriteringar…'],
    ['trial until ', 'provperiod till '],
    [' · Jobs ', ' · Jobb '],
    [' · Team ', ' · Team '],
    [' · attempts ', ' · försök '],
    [' · Stripe not configured', ' · Stripe är inte konfigurerat'],
    ['Execution adapter is not available for this provider.', 'Det finns ingen körningsadapter för den här leverantören.'],
    ['Pause campaign ', 'Pausa kampanj '],
    ['Pause ', 'Pausa '],
    [' after human review.', ' efter mänsklig granskning.'],
    ['Scanned ', 'Skannade '],
    [' competitors.', ' konkurrenter.'],
    ['No workspace available', 'Inget workspace är tillgängligt']
  ];

  function translateString(value) {
    if (typeof value !== 'string') return value;
    const trimmed = value.trim();
    if (exactPairs.has(trimmed)) return value.replace(trimmed, exactPairs.get(trimmed));
    let next = value;
    phrasePairs.forEach(([from, to]) => { next = next.split(from).join(to); });
    return next;
  }

  /* Product-grade toast feedback instead of raw browser alert dialogs. */
  let toastStack = document.querySelector('.vex-toast-stack');
  if (!toastStack) {
    toastStack = document.createElement('div');
    toastStack.className = 'vex-toast-stack';
    toastStack.setAttribute('aria-live', 'polite');
    document.body.appendChild(toastStack);
  }

  function toast(message, timeout = 6500) {
    const raw = typeof message === 'string' ? message : JSON.stringify(message, null, 2);
    const text = translateString(raw);
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

  const nativeConfirm = window.confirm.bind(window);
  window.confirm = (message) => nativeConfirm(translateString(String(message)));

  function translateTextNode(node) {
    if (node.nodeType !== Node.TEXT_NODE) return;
    const original = node.nodeValue;
    if (!original || !original.trim()) return;
    const next = translateString(original);
    if (next !== original) node.nodeValue = next;
  }

  function translateTree(root) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(translateTextNode);
  }

  async function disconnectConnector(provider, button) {
    const workspaceId = $('workspaceSelect')?.value;
    if (!workspaceId) {
      toast('Kunde inte hitta aktivt workspace.');
      return;
    }
    const label = provider === 'google' ? 'Google' : 'Meta';
    const confirmed = window.confirm(
      `Koppla från ${label}? Vexmera tar bort sparade anslutningsuppgifter och stoppar framtida synkning. Redan synkad rapporthistorik behålls.`
    );
    if (!confirmed) return;

    button.disabled = true;
    const previousText = button.textContent;
    button.textContent = 'Kopplar från…';
    try {
      const response = await fetch(`/api/connectors/${encodeURIComponent(provider)}/disconnect?workspace_id=${encodeURIComponent(workspaceId)}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
      });
      let payload = null;
      try { payload = await response.json(); } catch (_) {}
      if (!response.ok) {
        const detail = typeof payload?.detail === 'string' ? payload.detail : `HTTP ${response.status}`;
        throw new Error(detail);
      }
      toast(`${label} är frånkopplat. Sparade anslutningsuppgifter är raderade. Tidigare synkad rapporthistorik finns kvar.`);
      window.setTimeout(() => window.location.reload(), 900);
    } catch (error) {
      toast(`Kunde inte koppla från ${label}: ${error.message}`);
      button.disabled = false;
      button.textContent = previousText;
    }
  }

  function enhanceConnectorPrivacyControls() {
    document.querySelectorAll('#connectorGrid .connector-card').forEach((card) => {
      const sync = card.querySelector('[data-sync]');
      const actions = card.querySelector('.card-actions');
      if (!sync || !actions || sync.disabled) return;
      const provider = String(sync.dataset.sync || '').toLowerCase();
      if (!['google', 'meta'].includes(provider)) return;
      if (actions.querySelector(`[data-vex-disconnect="${provider}"]`)) return;

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'ghost danger vex-disconnect';
      button.dataset.vexDisconnect = provider;
      button.textContent = 'Koppla från';
      button.title = 'Tar bort sparade OAuth-uppgifter. Tidigare synkad rapporthistorik behålls.';
      button.addEventListener('click', () => disconnectConnector(provider, button));
      actions.appendChild(button);
    });
  }

  function polishDynamicUi() {
    [
      $('connect'), $('connectorGrid'), $('approvalList'), $('competitorList'), $('briefSchedulerState'),
      $('autopilotRuntime'), $('campaignInsights'), $('anomalyList'), $('jobList'),
      $('teamMembers'), $('inviteResult'), $('billingStatus'), $('fxList'), $('resetState'),
      $('coreHeadline'), $('coreTodayCards'), $('authError'), $('feedbackState'), $('profileState')
    ].forEach(translateTree);
    enhanceConnectorPrivacyControls();

    const mode = $('autopilotModeBadge');
    if (mode) {
      const v = mode.textContent.trim().toLowerCase();
      if (v === 'suggest') mode.textContent = 'Föreslå';
      if (v === 'assisted') mode.textContent = 'Assisterad';
    }

    const step = $('onboardingStepLabel');
    if (step) {
      const m = step.textContent.match(/Step\s+(\d+)\s+of\s+3/i);
      if (m) step.textContent = `Steg ${m[1]} av 3`;
    }

    const status = $('status');
    if (status) {
      status.textContent = status.textContent
        .replace('System online', 'Systemet är online')
        .replace('UI online · API-nyckel saknas i runtime', 'Gränssnittet är online · API-nyckel saknas i miljön');
    }
  }

  let queued = false;
  const observer = new MutationObserver(() => {
    if (queued) return;
    queued = true;
    queueMicrotask(() => {
      queued = false;
      polishDynamicUi();
    });
  });
  observer.observe(document.body, {subtree:true, childList:true, characterData:true});
  polishDynamicUi();

  /* Keep the beta product conservative: label execution controls clearly. */
  const runAutopilot = $('runAutopilotOnce');
  if (runAutopilot) runAutopilot.title = 'Kör endast en policykontroll. Extern körning styrs fortfarande av serverns säkerhetsspärrar.';
})();
