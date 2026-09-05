(() => {
  'use strict';

  const STORAGE_KEY = 'vexmera_analytics_consent';
  const MEASUREMENT_ID = 'G-YZESEE7XW0';
  const VALID = new Set(['granted', 'denied']);
  let loaded = false;
  let banner = null;
  let manageButton = null;

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function gtag(){ window.dataLayer.push(arguments); };

  // Privacy-first default. Analytics is not loaded until the visitor opts in.
  window.gtag('consent', 'default', {
    analytics_storage: 'denied',
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    wait_for_update: 500
  });

  function readConsent() {
    try {
      const value = window.localStorage.getItem(STORAGE_KEY);
      return VALID.has(value) ? value : null;
    } catch (_) {
      return null;
    }
  }

  function writeConsent(value) {
    try { window.localStorage.setItem(STORAGE_KEY, value); } catch (_) {}
  }

  function analyticsCookieDomains() {
    const host = String(window.location.hostname || '').trim().toLowerCase();
    const domains = new Set(['']);
    if (!host || host === 'localhost' || /^[\d.]+$/.test(host)) return [...domains];

    domains.add(host);
    domains.add(`.${host}`);
    const parts = host.split('.').filter(Boolean);
    for (let index = 1; index <= parts.length - 2; index += 1) {
      domains.add(`.${parts.slice(index).join('.')}`);
    }
    return [...domains];
  }

  function clearAnalyticsCookies() {
    const names = document.cookie
      .split(';')
      .map((item) => item.split('=')[0].trim())
      .filter((name) => /^_ga(?:_|$)/.test(name));

    if (!names.length) return;
    const expires = 'Thu, 01 Jan 1970 00:00:00 GMT';
    names.forEach((name) => {
      analyticsCookieDomains().forEach((domain) => {
        const domainPart = domain ? `; domain=${domain}` : '';
        document.cookie = `${name}=; expires=${expires}; max-age=0; path=/${domainPart}; SameSite=Lax`;
      });
    });
  }

  function loadAnalytics() {
    if (loaded || document.querySelector('script[data-vexmera-analytics]')) return;
    loaded = true;
    window.gtag('consent', 'update', {
      analytics_storage: 'granted',
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied'
    });

    const script = document.createElement('script');
    script.async = true;
    script.dataset.vexmeraAnalytics = 'true';
    script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(MEASUREMENT_ID)}`;
    script.addEventListener('load', () => {
      window.gtag('js', new Date());
      window.gtag('config', MEASUREMENT_ID, {
        send_page_view: true,
        allow_google_signals: false,
        allow_ad_personalization_signals: false
      });
    }, {once: true});
    document.head.appendChild(script);
  }

  function disableAnalytics({clearCookies = true} = {}) {
    window.gtag('consent', 'update', {
      analytics_storage: 'denied',
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied'
    });
    if (clearCookies) clearAnalyticsCookies();
  }

  function ensureStyles() {
    if (document.getElementById('vexmeraConsentStyles')) return;
    const style = document.createElement('style');
    style.id = 'vexmeraConsentStyles';
    style.textContent = `
      .vex-consent{position:fixed;left:20px;right:20px;bottom:20px;z-index:9999;display:flex;align-items:center;justify-content:space-between;gap:20px;max-width:920px;margin:auto;padding:16px 18px;border:1px solid rgba(155,113,56,.28);border-radius:16px;background:rgba(17,19,24,.97);box-shadow:0 18px 54px rgba(0,0,0,.28);color:#f4f5f7;font-family:Inter,system-ui,sans-serif;backdrop-filter:blur(14px)}
      .vex-consent strong{display:block;font-size:13px}.vex-consent p{margin:4px 0 0;color:#aeb5bf;font-size:12px;line-height:1.5;max-width:610px}.vex-consent-actions{display:flex;gap:8px;flex:0 0 auto}.vex-consent button{min-height:38px;padding:0 13px;border-radius:10px;border:1px solid #3a414d;background:#181d25;color:#eef1f4;font:600 12px Inter,system-ui,sans-serif;cursor:pointer}.vex-consent button.primary{border-color:#9b7138;background:#9b7138;color:#fffaf2}.vex-consent button:focus-visible,.vex-consent-manage:focus-visible{outline:3px solid rgba(199,165,108,.42);outline-offset:2px}
      .vex-consent-manage{position:fixed;left:14px;bottom:14px;z-index:1200;padding:7px 9px;border:1px solid rgba(120,130,145,.28);border-radius:9px;background:rgba(17,19,24,.9);color:#aeb5bf;font:600 10px Inter,system-ui,sans-serif;cursor:pointer;opacity:.72}.vex-consent-manage:hover{opacity:1}
      @media(max-width:720px){.vex-consent{align-items:flex-start;flex-direction:column;gap:13px}.vex-consent-actions{width:100%}.vex-consent-actions button{flex:1}}
    `;
    document.head.appendChild(style);
  }

  function removeBanner() {
    if (banner) banner.remove();
    banner = null;
  }

  function renderManageButton() {
    if (manageButton || !document.body) return;
    ensureStyles();
    manageButton = document.createElement('button');
    manageButton.type = 'button';
    manageButton.className = 'vex-consent-manage';
    manageButton.textContent = 'Cookieinställningar';
    manageButton.setAttribute('aria-label', 'Öppna cookieinställningar');
    manageButton.addEventListener('click', () => renderBanner(true));
    document.body.appendChild(manageButton);
  }

  function applyChoice(value) {
    if (!VALID.has(value)) return;
    writeConsent(value);
    if (value === 'granted') loadAnalytics();
    else disableAnalytics({clearCookies: true});
    removeBanner();
    renderManageButton();
  }

  function renderBanner(force = false) {
    if (!document.body) return;
    if (!force && readConsent()) return;
    removeBanner();
    ensureStyles();

    banner = document.createElement('section');
    banner.className = 'vex-consent';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-modal', 'false');
    banner.setAttribute('aria-label', 'Cookieinställningar');
    banner.innerHTML = `
      <div><strong>Hjälp oss förbättra Vexmera</strong><p>Nödvändiga funktioner fungerar utan statistikcookies. Du kan frivilligt tillåta användningsstatistik via Google Analytics och ändra valet när som helst.</p></div>
      <div class="vex-consent-actions"><button type="button" data-consent="denied">Endast nödvändiga</button><button type="button" class="primary" data-consent="granted">Tillåt statistik</button></div>
    `;
    banner.querySelectorAll('[data-consent]').forEach((button) => {
      button.addEventListener('click', () => applyChoice(button.dataset.consent));
    });
    document.body.appendChild(banner);
  }

  function bindCookieSettingsLinks() {
    document.querySelectorAll('[data-vexmera-cookie-settings]').forEach((control) => {
      if (control.dataset.vexmeraCookieBound === 'true') return;
      control.dataset.vexmeraCookieBound = 'true';
      control.addEventListener('click', (event) => {
        event.preventDefault();
        renderBanner(true);
      });
    });
  }

  function init() {
    bindCookieSettingsLinks();
    const consent = readConsent();
    if (consent === 'granted') loadAnalytics();
    else if (consent === 'denied') disableAnalytics({clearCookies: true});
    else renderBanner();
    if (consent) renderManageButton();
  }

  window.vexmeraOpenCookieSettings = () => renderBanner(true);

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once: true});
  else init();
})();
