(() => {
  'use strict';

  const build = window.__VEXMERA_BUILD__ || 'local';

  if (!document.querySelector('link[data-vexmera-conversion]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = `/static/landing-conversion.css?build=${encodeURIComponent(build)}`;
    link.dataset.vexmeraConversion = 'true';
    document.head.appendChild(link);
  }

  const copy = {
    sv: {
      heroNote: 'Privat beta · Google Ads + Meta Ads + GA4 · Du behåller kontrollen',
      proofKicker: 'ILLUSTRATIVT PRODUKTEXEMPEL',
      proofTitle: 'Från signal till beslut, utan ett kalkylark emellan.',
      proofBody: 'Vexmera är byggt för att göra analyskedjan kortare. Ett relevant mönster blir en förklaring, en prioritering och ett konkret nästa steg i samma vy.',
      bullet1: 'Se vad som förändrats',
      bullet2: 'Förstå varför det är viktigt',
      bullet3: 'Få ett prioriterat nästa steg',
      demoTitle: 'Så kan Vexmera prioritera ett beslut',
      demoBadge: 'DEMODATA',
      signalLabel: 'SIGNAL',
      signalTitle: 'Google Search överpresterar',
      signalBody: 'Illustrativt exempel: 31 % över kontots genomsnittliga ROAS.',
      whyLabel: 'FÖRKLARING',
      whyTitle: 'Mer budget kan arbeta bättre',
      whyBody: 'Vexmera jämför signalerna och visar varför förändringen kan vara relevant.',
      nextLabel: 'NÄSTA STEG',
      nextTitle: 'Agera kontrollerat',
      nextBody: 'Få en tydlig rekommendation som kan granskas innan något ändras.',
      recommendationLabel: 'EXEMPEL PÅ REKOMMENDATION',
      recommendation: 'Flytta 15 % av kommande budget till kanalen med starkast lönsamhet.',
      cta1Title: 'Vill du se samma logik på din egen data?',
      cta1Body: 'Koppla dina kanaler i privat beta och låt Vexmera prioritera vad som är värt din uppmärksamhet.',
      cta1Button: 'Prova Vexmera',
      cta2Title: 'Mindre dashboardarbete. Mer beslut.',
      cta2Body: 'Välj den nivå som passar företaget och börja med kontroll före automation.',
      cta2Button: 'Se planerna',
      betaBadge: 'PRIVAT BETA',
      betaTitle: 'Förtroende före hype.',
      betaBody: 'Vexmera är fortfarande i privat beta. Därför skiljer vi tydligt mellan illustrativ demodata och faktiskt ansluten kunddata.',
      beta1Title: 'Tydligt märkt demodata',
      beta1Body: 'Illustrativa siffror presenteras som demo, inte som verkliga kundresultat.',
      beta2Title: 'Kontroll före automation',
      beta2Body: 'Du bestämmer när mänskligt godkännande krävs och hur långt automationen får gå.',
      beta3Title: 'Fokus på riktiga kanaler',
      beta3Body: 'Google Ads, Meta Ads och GA4 är i fokus i den nuvarande betan. Fler integrationer byggs stegvis.'
    },
    en: {
      heroNote: 'Private beta · Google Ads + Meta Ads + GA4 · You stay in control',
      proofKicker: 'ILLUSTRATIVE PRODUCT EXAMPLE',
      proofTitle: 'From signal to decision, without another spreadsheet in between.',
      proofBody: 'Vexmera is built to shorten the analysis chain. A relevant pattern becomes an explanation, a priority and a concrete next step in the same view.',
      bullet1: 'See what changed',
      bullet2: 'Understand why it matters',
      bullet3: 'Get a prioritized next step',
      demoTitle: 'How Vexmera can prioritize a decision',
      demoBadge: 'DEMO DATA',
      signalLabel: 'SIGNAL',
      signalTitle: 'Google Search is outperforming',
      signalBody: 'Illustrative example: 31% above the account average ROAS.',
      whyLabel: 'EXPLANATION',
      whyTitle: 'More budget can work harder',
      whyBody: 'Vexmera compares the signals and explains why the change may be relevant.',
      nextLabel: 'NEXT STEP',
      nextTitle: 'Act with control',
      nextBody: 'Get a clear recommendation that can be reviewed before anything changes.',
      recommendationLabel: 'EXAMPLE RECOMMENDATION',
      recommendation: 'Move 15% of upcoming budget to the channel with the strongest profitability.',
      cta1Title: 'Want to see the same logic on your own data?',
      cta1Body: 'Connect your channels in private beta and let Vexmera prioritize what deserves your attention.',
      cta1Button: 'Try Vexmera',
      cta2Title: 'Less dashboard work. More decisions.',
      cta2Body: 'Choose the level that fits your company and start with control before automation.',
      cta2Button: 'See plans',
      betaBadge: 'PRIVATE BETA',
      betaTitle: 'Trust before hype.',
      betaBody: 'Vexmera is still in private beta. That is why we clearly separate illustrative demo data from actually connected customer data.',
      beta1Title: 'Clearly labeled demo data',
      beta1Body: 'Illustrative figures are presented as demo data, not as real customer results.',
      beta2Title: 'Control before automation',
      beta2Body: 'You decide when human approval is required and how far automation is allowed to go.',
      beta3Title: 'Focused on real channels',
      beta3Body: 'Google Ads, Meta Ads and GA4 are the current beta focus. More integrations are being added step by step.'
    }
  };

  function lang() {
    return document.documentElement.lang?.toLowerCase().startsWith('en') ? 'en' : 'sv';
  }

  function t(key) {
    return copy[lang()][key] || copy.sv[key] || key;
  }

  function textNode(tag, className, key) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    node.dataset.conversionCopy = key;
    node.textContent = t(key);
    return node;
  }

  function applyLanguage() {
    document.querySelectorAll('[data-conversion-copy]').forEach((node) => {
      const key = node.dataset.conversionCopy;
      if (copy[lang()][key]) node.textContent = copy[lang()][key];
    });
  }

  function installHeroNote() {
    const actions = document.querySelector('.hero-actions');
    if (!actions || document.querySelector('.conversion-hero-note')) return;
    const note = textNode('div', 'conversion-hero-note', 'heroNote');
    note.style.marginTop = '14px';
    note.style.color = 'var(--premium-muted,#59616c)';
    note.style.fontSize = '12px';
    note.style.fontWeight = '650';
    note.style.letterSpacing = '.015em';
    actions.insertAdjacentElement('afterend', note);
  }

  function installProductProof() {
    const productDemo = document.querySelector('.product-demo');
    if (!productDemo || document.getElementById('conversionProof')) return;

    const section = document.createElement('section');
    section.className = 'conversion-section';
    section.id = 'conversionProof';
    section.setAttribute('aria-label', 'Product example');

    section.innerHTML = `
      <div class="conversion-proof">
        <div class="conversion-copy">
          <div class="conversion-kicker" data-conversion-copy="proofKicker">${t('proofKicker')}</div>
          <h2 data-conversion-copy="proofTitle">${t('proofTitle')}</h2>
          <p data-conversion-copy="proofBody">${t('proofBody')}</p>
          <ul class="conversion-bullets">
            <li><i>✓</i><span data-conversion-copy="bullet1">${t('bullet1')}</span></li>
            <li><i>✓</i><span data-conversion-copy="bullet2">${t('bullet2')}</span></li>
            <li><i>✓</i><span data-conversion-copy="bullet3">${t('bullet3')}</span></li>
          </ul>
        </div>
        <div class="conversion-demo-window" aria-label="Illustrative Vexmera decision flow">
          <div class="conversion-demo-head">
            <strong data-conversion-copy="demoTitle">${t('demoTitle')}</strong>
            <span data-conversion-copy="demoBadge">${t('demoBadge')}</span>
          </div>
          <div class="conversion-decision-flow">
            <article class="conversion-flow-card">
              <small data-conversion-copy="signalLabel">${t('signalLabel')}</small>
              <strong data-conversion-copy="signalTitle">${t('signalTitle')}</strong>
              <p data-conversion-copy="signalBody">${t('signalBody')}</p>
            </article>
            <div class="conversion-flow-arrow" aria-hidden="true">→</div>
            <article class="conversion-flow-card">
              <small data-conversion-copy="whyLabel">${t('whyLabel')}</small>
              <strong data-conversion-copy="whyTitle">${t('whyTitle')}</strong>
              <p data-conversion-copy="whyBody">${t('whyBody')}</p>
            </article>
            <div class="conversion-flow-arrow" aria-hidden="true">→</div>
            <article class="conversion-flow-card">
              <small data-conversion-copy="nextLabel">${t('nextLabel')}</small>
              <strong data-conversion-copy="nextTitle">${t('nextTitle')}</strong>
              <p data-conversion-copy="nextBody">${t('nextBody')}</p>
            </article>
          </div>
          <div class="conversion-recommendation">
            <span data-conversion-copy="recommendationLabel">${t('recommendationLabel')}</span>
            <strong data-conversion-copy="recommendation">${t('recommendation')}</strong>
          </div>
        </div>
      </div>`;

    productDemo.insertAdjacentElement('afterend', section);
  }

  function createInlineCta(id, titleKey, bodyKey, buttonKey, href) {
    const section = document.createElement('section');
    section.id = id;
    section.className = 'conversion-inline-cta';

    const copyWrap = document.createElement('div');
    copyWrap.appendChild(textNode('strong', '', titleKey));
    copyWrap.appendChild(textNode('p', '', bodyKey));

    const button = textNode('a', 'button button-primary', buttonKey);
    button.href = href;
    button.appendChild(document.createTextNode(' →'));

    section.append(copyWrap, button);
    return section;
  }

  function installCtas() {
    const proof = document.getElementById('conversionProof');
    if (proof && !document.getElementById('conversionCtaOne')) {
      proof.insertAdjacentElement('afterend', createInlineCta('conversionCtaOne', 'cta1Title', 'cta1Body', 'cta1Button', '/app'));
    }

    const outcomes = document.querySelector('.outcomes-section');
    if (outcomes && !document.getElementById('conversionCtaTwo')) {
      outcomes.insertAdjacentElement('afterend', createInlineCta('conversionCtaTwo', 'cta2Title', 'cta2Body', 'cta2Button', '#pris'));
    }
  }

  function installBetaProof() {
    const pricing = document.getElementById('pris');
    if (!pricing) return;

    let section = document.getElementById('betaProofSection');
    if (!section) {
      section = document.createElement('section');
      section.id = 'betaProofSection';
      section.className = 'beta-proof-section';
      section.innerHTML = `
        <div class="beta-proof-head">
          <div>
            <div class="beta-proof-badge" data-conversion-copy="betaBadge">${t('betaBadge')}</div>
            <h2 data-conversion-copy="betaTitle">${t('betaTitle')}</h2>
          </div>
          <p data-conversion-copy="betaBody">${t('betaBody')}</p>
        </div>
        <div class="beta-proof-grid">
          <article class="beta-proof-card">
            <div class="beta-proof-icon" aria-hidden="true">D</div>
            <strong data-conversion-copy="beta1Title">${t('beta1Title')}</strong>
            <p data-conversion-copy="beta1Body">${t('beta1Body')}</p>
          </article>
          <article class="beta-proof-card">
            <div class="beta-proof-icon" aria-hidden="true">✓</div>
            <strong data-conversion-copy="beta2Title">${t('beta2Title')}</strong>
            <p data-conversion-copy="beta2Body">${t('beta2Body')}</p>
          </article>
          <article class="beta-proof-card">
            <div class="beta-proof-icon" aria-hidden="true">↗</div>
            <strong data-conversion-copy="beta3Title">${t('beta3Title')}</strong>
            <p data-conversion-copy="beta3Body">${t('beta3Body')}</p>
          </article>
        </div>`;
      pricing.insertAdjacentElement('beforebegin', section);
    }

    // Founder is injected asynchronously. Keep trust proof directly after founder when available.
    const founder = document.querySelector('.founder-section');
    if (founder && founder.nextElementSibling !== section) founder.insertAdjacentElement('afterend', section);
  }

  function markIllustrativeProductData() {
    const hero = document.querySelector('.hero-visual');
    if (hero && !hero.querySelector('.conversion-demo-chip')) {
      const chip = document.createElement('span');
      chip.className = 'conversion-demo-chip';
      chip.textContent = lang() === 'en' ? 'ILLUSTRATIVE DEMO' : 'ILLUSTRATIV DEMO';
      chip.style.position = 'absolute';
      chip.style.right = '18px';
      chip.style.top = '18px';
      chip.style.zIndex = '6';
      chip.style.padding = '6px 9px';
      chip.style.borderRadius = '999px';
      chip.style.background = 'rgba(12,16,22,.76)';
      chip.style.border = '1px solid rgba(255,255,255,.13)';
      chip.style.color = '#e9d4ad';
      chip.style.fontSize = '8px';
      chip.style.fontWeight = '850';
      chip.style.letterSpacing = '.12em';
      chip.style.backdropFilter = 'blur(8px)';
      hero.style.position = 'relative';
      hero.appendChild(chip);
    }
    const chip = hero?.querySelector('.conversion-demo-chip');
    if (chip) chip.textContent = lang() === 'en' ? 'ILLUSTRATIVE DEMO' : 'ILLUSTRATIV DEMO';
  }

  function run() {
    installHeroNote();
    installProductProof();
    installCtas();
    installBetaProof();
    markIllustrativeProductData();
    applyLanguage();
  }

  function settle() {
    let attempts = 0;
    const tick = () => {
      attempts += 1;
      run();
      const founderReady = !!document.querySelector('.founder-section');
      const pricingReady = !!document.getElementById('pris');
      if ((founderReady && pricingReady) || attempts >= 20) return;
      window.setTimeout(tick, attempts < 6 ? 140 : 320);
    };
    tick();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', settle, { once:true });
  } else {
    settle();
  }

  const langObserver = new MutationObserver(() => {
    applyLanguage();
    markIllustrativeProductData();
  });
  langObserver.observe(document.documentElement, { attributes:true, attributeFilter:['lang'] });
})();
