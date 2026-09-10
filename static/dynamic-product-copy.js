(() => {
  'use strict';

  const exact = new Map([
    ['Connected', 'Ansluten'],
    ['Ready to connect', 'Redo att ansluta'],
    ['Needs setup', 'Kräver konfiguration'],
    ['Connect', 'Anslut'],
    ['Sync', 'Synka'],
    ['Never synced', 'Aldrig synkad'],
    ['Approve', 'Godkänn'],
    ['Reject', 'Avvisa'],
    ['Preview', 'Förhandsgranska'],
    ['Scan', 'Skanna'],
    ['pending', 'väntar'],
    ['approved', 'godkänd'],
    ['rejected', 'avvisad'],
    ['executed', 'utförd'],
    ['failed', 'misslyckad'],
    ['high', 'hög'],
    ['medium', 'medel'],
    ['low', 'låg'],
    ['internal', 'internt'],
    ['google_ads', 'Google Ads'],
    ['meta_ads', 'Meta Ads'],
    ['google_analytics', 'Google Analytics'],
    ['Inga actions i denna vy.', 'Inga åtgärder i den här vyn.'],
    ['Scheduler is enabled in this runtime.', 'Schemaläggaren är aktiverad i den här miljön.'],
    ['Scheduler is disabled in this runtime; manual brief still works.', 'Schemaläggaren är avstängd i den här miljön. Manuell brief fungerar fortfarande.'],
    ['External execution', 'Extern körning'],
    ['Autopilot worker execution', 'Autopilot-körning'],
    ['High-risk autonomous actions', 'Autonoma högriskåtgärder'],
    ['ENABLED', 'AKTIVERAD'],
    ['LOCKED', 'LÅST'],
    ['BLOCKED IN BETA', 'BLOCKERAD I BETA'],
    ['Suggest', 'Föreslå'],
    ['Assisted', 'Assisterad'],
    ['Autonomous', 'Autonom'],
  ]);

  function translateExact(node) {
    if (!node) return;
    const value = node.textContent.trim();
    const translated = exact.get(value);
    if (translated) node.textContent = translated;
  }

  function enhanceConnect() {
    const period = document.getElementById('syncDays')?.closest('label');
    if (period?.firstChild?.nodeType === Node.TEXT_NODE) {
      period.firstChild.nodeValue = 'Synkperiod ';
    }

    document.querySelectorAll('#connectorGrid .connector-card').forEach((card) => {
      translateExact(card.querySelector('.state-pill'));
      translateExact(card.querySelector('[data-connect]'));
      translateExact(card.querySelector('[data-sync]'));

      card.querySelectorAll('p').forEach((paragraph) => {
        const text = paragraph.textContent.trim();
        if (text === 'OAuth credentials detected.') {
          paragraph.textContent = 'OAuth-konfiguration hittad.';
        } else if (text.startsWith('Missing:')) {
          paragraph.textContent = `Saknas:${text.slice('Missing:'.length)}`;
        }
      });

      const last = card.querySelector('small');
      if (last) {
        const text = last.textContent.trim();
        if (text === 'Never synced') last.textContent = 'Aldrig synkad';
        else if (text.startsWith('Last sync:')) last.textContent = `Senast synkad:${text.slice('Last sync:'.length)}`;
      }
    });
  }

  function enhanceQueue() {
    const list = document.getElementById('approvalList');
    if (!list) return;

    const empty = list.querySelector('.muted');
    translateExact(empty);

    list.querySelectorAll('.approval-card').forEach((card) => {
      translateExact(card.querySelector('.risk'));
      translateExact(card.querySelector('.state-pill'));
      translateExact(card.querySelector('[data-approve]'));
      translateExact(card.querySelector('[data-reject]'));
      translateExact(card.querySelector('[data-preview]'));

      const meta = card.querySelector('small');
      if (meta) {
        const parts = meta.textContent.split(' · ');
        if (parts.length > 1) {
          const provider = exact.get(parts[0].trim()) || parts[0].trim();
          meta.textContent = `${provider} · ${parts.slice(1).join(' · ')}`;
        }
      }

      const execute = card.querySelector('[data-execute]');
      if (execute) {
        execute.disabled = true;
        execute.onclick = null;
        execute.setAttribute('aria-disabled', 'true');
        execute.dataset.vexmeraExecutionLocked = 'true';
        execute.textContent = 'Extern körning avstängd';
        execute.title = 'Private beta är recommendation-only. Vexmera ändrar inte kampanjer, budgetar eller bud externt.';
      }
    });
  }

  function enhanceRivals() {
    const list = document.getElementById('competitorList');
    if (!list) return;

    list.querySelectorAll('[data-scan]').forEach(translateExact);
    list.querySelectorAll('.competitor-card small').forEach((node) => {
      let text = node.textContent.trim();
      if (text === 'Not scanned yet') {
        node.textContent = 'Inte skannad ännu';
        return;
      }
      if (text.startsWith('Checked ')) text = `Kontrollerad ${text.slice('Checked '.length)}`;
      text = text.replace(' · change detected', ' · förändring upptäckt');
      text = text.replace(' · stable', ' · stabil');
      node.textContent = text;
    });
  }

  function enhanceBrief() {
    translateExact(document.getElementById('briefSchedulerState'));
  }

  function enhanceAutopilot() {
    document.querySelectorAll('#autopilotRuntime .safety-row span, #autopilotRuntime .safety-row strong')
      .forEach(translateExact);
    translateExact(document.getElementById('autopilotModeBadge'));
  }

  function wrapLoader(name, enhancer) {
    const original = window[name];
    if (typeof original !== 'function' || original.__vexmeraDynamicCopyGuard) return;

    async function guardedLoader(...args) {
      const result = await original.apply(this, args);
      enhancer();
      return result;
    }

    guardedLoader.__vexmeraDynamicCopyGuard = true;
    guardedLoader.__vexmeraOriginalLoader = original;
    window[name] = guardedLoader;
  }

  function install() {
    wrapLoader('loadConnectors', enhanceConnect);
    wrapLoader('loadApprovals', enhanceQueue);
    wrapLoader('loadCompetitors', enhanceRivals);
    wrapLoader('loadBrief', enhanceBrief);
    wrapLoader('loadAutopilot', enhanceAutopilot);

    queueMicrotask(() => {
      enhanceConnect();
      enhanceQueue();
      enhanceRivals();
      enhanceBrief();
      enhanceAutopilot();
    });
  }

  install();
})();
