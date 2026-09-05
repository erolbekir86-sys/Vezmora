(() => {
  'use strict';

  const team = document.getElementById('team');
  if (!team || document.querySelector('[data-vex-account-privacy]')) return;

  const style = document.createElement('style');
  style.textContent = `
    .account-privacy-panel{border-color:rgba(198,83,83,.24)!important;background:linear-gradient(180deg,rgba(198,83,83,.035),transparent 55%)}
    .account-privacy-panel .danger-title span{color:var(--danger,#c65353)}
    .account-delete-box{margin-top:16px;padding:18px;border:1px solid rgba(198,83,83,.2);border-radius:14px;background:rgba(198,83,83,.035)}
    .account-delete-box.hidden{display:none}
    .account-delete-summary{display:grid;gap:8px;margin:12px 0 16px}
    .account-delete-summary p{margin:0;color:var(--muted,#8f96a3);line-height:1.55}
    .account-delete-blocker{padding:10px 12px;border-radius:10px;background:rgba(198,83,83,.09);color:var(--danger,#c65353)!important}
    .account-delete-fields{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}
    .account-delete-fields.hidden{display:none}
    .account-delete-actions{display:flex;align-items:center;gap:12px;margin-top:14px;flex-wrap:wrap}
    .account-delete-danger{border-color:rgba(198,83,83,.45)!important;color:var(--danger,#c65353)!important}
    .account-delete-danger:hover{background:rgba(198,83,83,.08)!important}
    @media(max-width:760px){.account-delete-fields{grid-template-columns:1fr}}
  `;
  document.head.appendChild(style);

  const section = document.createElement('section');
  section.className = 'panel table-panel account-privacy-panel';
  section.dataset.vexAccountPrivacy = 'true';
  section.innerHTML = `
    <div class="module-head">
      <div>
        <div class="panel-title danger-title"><span>KONTO & INTEGRITET</span> Ta bort Vexmera-konto</div>
        <p>Permanent kontoborttagning är skyddad med lösenordsverifiering och en exakt bekräftelsefras. Vexmera blockerar radering om du först behöver hantera teamägarskap eller en aktiv prenumeration.</p>
      </div>
      <button id="accountDeletePrepare" type="button" class="ghost account-delete-danger">Granska kontoborttagning</button>
    </div>
    <div id="accountDeleteBox" class="account-delete-box hidden" aria-live="polite">
      <div id="accountDeleteSummary" class="account-delete-summary"><p>Kontrollerar vad som kan tas bort…</p></div>
      <div id="accountDeleteFields" class="account-delete-fields hidden">
        <label>Nuvarande lösenord<input id="accountDeletePassword" type="password" autocomplete="current-password" /></label>
        <label>Skriv exakt <strong>DELETE MY ACCOUNT</strong><input id="accountDeleteConfirmation" type="text" autocomplete="off" spellcheck="false" /></label>
      </div>
      <div class="account-delete-actions">
        <button id="accountDeleteRun" type="button" class="ghost account-delete-danger" disabled>Ta bort mitt konto permanent</button>
        <span id="accountDeleteState" class="fineprint"></span>
      </div>
    </div>
  `;
  team.appendChild(section);

  const prepare = document.getElementById('accountDeletePrepare');
  const box = document.getElementById('accountDeleteBox');
  const summary = document.getElementById('accountDeleteSummary');
  const fields = document.getElementById('accountDeleteFields');
  const password = document.getElementById('accountDeletePassword');
  const confirmation = document.getElementById('accountDeleteConfirmation');
  const run = document.getElementById('accountDeleteRun');
  const state = document.getElementById('accountDeleteState');
  let preview = null;

  const toast = (message) => {
    if (typeof window.vexmeraToast === 'function') window.vexmeraToast(message);
    else window.alert(message);
  };

  async function parseResponse(response) {
    let payload = null;
    try { payload = await response.json(); } catch (_) {}
    if (!response.ok) {
      const detail = typeof payload?.detail === 'string' ? payload.detail : `HTTP ${response.status}`;
      throw new Error(detail);
    }
    return payload;
  }

  function updateDeleteButton() {
    const exact = confirmation.value === 'DELETE MY ACCOUNT';
    run.disabled = !preview?.allowed || !password.value || !exact;
  }

  password.addEventListener('input', updateDeleteButton);
  confirmation.addEventListener('input', updateDeleteButton);

  async function loadPreview() {
    box.classList.remove('hidden');
    fields.classList.add('hidden');
    run.disabled = true;
    state.textContent = '';
    summary.innerHTML = '<p>Kontrollerar konto, workspaces och fakturering…</p>';
    try {
      preview = await parseResponse(await fetch('/api/privacy/account-deletion-preview', {
        credentials: 'same-origin',
        headers: {'Accept': 'application/json'}
      }));

      const owned = Array.isArray(preview.owned_workspaces) ? preview.owned_workspaces : [];
      const shared = Number(preview.shared_workspace_memberships || 0);
      const lines = [
        `<p><strong>${owned.length}</strong> workspace${owned.length === 1 ? '' : 'n'} ägs av kontot och raderas om raderingen genomförs.</p>`,
        `<p>Medlemskap i <strong>${shared}</strong> workspace${shared === 1 ? '' : 'n'} som ägs av andra tas bort utan att deras workspace raderas.</p>`,
        '<p>Lokala sessions-, konto- och workspace-data tas bort. Google/Meta-tokenåterkallelse försöks före lokal radering. Externa bokförings- eller betalningsuppgifter kan behöva behållas av betalningsleverantören.</p>'
      ];
      const blockers = Array.isArray(preview.blockers) ? preview.blockers : [];
      blockers.forEach((blocker) => {
        const name = blocker.workspace_name ? `${blocker.workspace_name}: ` : '';
        const message = blocker.code === 'workspace_has_other_members'
          ? 'Överför ägarskapet eller ta bort övriga medlemmar först.'
          : blocker.code === 'active_subscription'
            ? 'Avsluta den aktiva Stripe-prenumerationen först.'
            : String(blocker.message || 'Kontoborttagningen är blockerad.');
        lines.push(`<p class="account-delete-blocker"><strong>${escapeHtml(name)}</strong>${escapeHtml(message)}</p>`);
      });
      summary.innerHTML = lines.join('');
      if (preview.allowed) fields.classList.remove('hidden');
      else fields.classList.add('hidden');
      updateDeleteButton();
    } catch (error) {
      preview = null;
      summary.innerHTML = `<p class="account-delete-blocker">Kunde inte kontrollera kontoborttagning: ${escapeHtml(error.message)}</p>`;
    }
  }

  function escapeHtml(value = '') {
    return String(value).replace(/[&<>"']/g, (char) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    }[char]));
  }

  prepare.addEventListener('click', loadPreview);

  run.addEventListener('click', async () => {
    if (!preview?.allowed) return;
    if (confirmation.value !== 'DELETE MY ACCOUNT') {
      state.textContent = 'Bekräftelsefrasen är inte exakt.';
      return;
    }
    const confirmed = window.confirm(
      'Detta raderar ditt Vexmera-konto och alla workspaces som du ensam äger. Åtgärden kan inte ångras. Fortsätta?'
    );
    if (!confirmed) return;

    run.disabled = true;
    prepare.disabled = true;
    password.disabled = true;
    confirmation.disabled = true;
    state.textContent = 'Raderar konto…';
    try {
      const payload = await parseResponse(await fetch('/api/privacy/account', {
        method: 'DELETE',
        credentials: 'same-origin',
        headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
        body: JSON.stringify({
          password: password.value,
          confirmation: confirmation.value
        })
      }));
      if (!payload?.account_deleted) throw new Error('Kontot kunde inte bekräftas som raderat.');
      state.textContent = 'Kontot är raderat.';
      toast('Ditt Vexmera-konto och lokala kontodata är raderade.');
      window.setTimeout(() => { window.location.href = '/'; }, 900);
    } catch (error) {
      state.textContent = error.message;
      toast(`Kunde inte radera kontot: ${error.message}`);
      prepare.disabled = false;
      password.disabled = false;
      confirmation.disabled = false;
      updateDeleteButton();
    }
  });
})();
