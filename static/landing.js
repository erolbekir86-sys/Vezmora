(() => {
  const polishStylesheet = document.createElement('link');
  polishStylesheet.rel = 'stylesheet';
  polishStylesheet.href = '/static/landing-polish.css?v=1';
  document.head.appendChild(polishStylesheet);

  const founderStylesheet = document.createElement('link');
  founderStylesheet.rel = 'stylesheet';
  founderStylesheet.href = '/static/landing-founder.css?v=2';
  document.head.appendChild(founderStylesheet);

  const root = document.documentElement;
  const body = document.body;
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  const copy = {
    en: {
      'nav.product':'Product','nav.how':'How it works','nav.features':'Features','nav.pricing':'Pricing','nav.login':'Log in','nav.start':'Get started',
      'hero.eyebrow':'AI-DRIVEN MARKETING INTELLIGENCE','hero.title1':'Understand your marketing.','hero.title2':'Know exactly what to do next.','hero.lead':'Vexmera brings your marketing data together, analyzes what actually drives results and turns complex information into clear decisions.','hero.cta':'Try Vexmera →','hero.demo':'See how it works','hero.proof1':'Built for small and growing companies','hero.proof2':'Clear recommendations','hero.proof3':'Control before automation',
      'dash.overview':'Overview','dash.settings':'Settings','dash.queue':'Queue','dash.rivals':'Rivals','dash.connect':'Connect','dash.insights':'Insights','dash.demo':'DEMO DATA','dash.overviewUpper':'OVERVIEW','dash.morning':'Good morning.','dash.summary':'Here is what is happening in your marketing.','dash.days':'days','dash.revenue':'Revenue','dash.leads':'Leads','dash.recommends':'CORE RECOMMENDS','dash.recTitle':'Move 15% more budget to the campaign with the highest profitability.','dash.recBody':'Google Search is performing 31% above the account’s average ROAS over the last 14 days.','dash.effect':'Estimated impact','dash.viewAnalysis':'View analysis','dash.performance':'Performance trend','dash.days30':'30 days','dash.approvals':'Pending approvals','dash.approvalCount':'2 waiting for review','dash.sources':'Connected sources','dash.sourceCount':'Google + Meta',
      'float.opportunities':'3 opportunities found','float.priority':'Prioritized by business impact','float.synced':'Synced and analyzed',
      'trust.oneTitle':'Built for growing companies','trust.oneBody':'Powerful without becoming overwhelming.','trust.twoTitle':'Clear recommendations','trust.twoBody':'Concrete decisions, not just more data.','trust.threeTitle':'You stay in control','trust.threeBody':'Vexmera recommends. You decide.',
      'problem.eyebrow':'ONE PLACE. ONE LANGUAGE. BETTER DECISIONS.','problem.title':'Marketing should not require five dashboards.','problem.body':'The data already exists. The problem is that it is scattered. Vexmera brings the signals together and makes them understandable.','problem.output':'Prioritized intelligence',
      'demo.eyebrow':'FROM SIGNAL TO NEXT MOVE','demo.title':'Vexmera does not only show what happened. It helps you understand what you should do.','demo.body':'Insights are prioritized by potential business impact, so you can spend time where it actually matters.','demo.item1':'Explains why something changed','demo.item2':'Prioritizes by impact','demo.item3':'Gives you the next concrete step','demo.justNow':'Just now','demo.insightTitle':'Google Search generates 37% higher ROAS than Meta Prospecting.','demo.current':'Current ROAS','demo.potential':'Potential','demo.recommendation':'RECOMMENDATION','demo.recommendText':'Move SEK 4,000 of next week’s budget from Meta Prospecting to Google Search.','demo.show':'View analysis',
      'value.simple':'Simpler','value.simpleBody':'All important marketing data in one place. Less jumping between tools.','value.fast':'Faster','value.fastBody':'Go from “what does this mean?” to a clear next step in minutes instead of hours.','value.smart':'Smarter','value.smartBody':'AI prioritizes the signals that can actually affect profitability and growth.',
      'how.eyebrow':'HOW IT WORKS','how.title':'From data to decisions in three steps.','how.body':'Connect your channels and let Vexmera start building a clearer picture of what works.','how.step1':'Connect your channels','how.step1Body':'Bring Google Ads and Meta Ads into one shared view.','how.step2':'Vexmera analyzes','how.step2Body':'AI looks for anomalies, patterns and opportunities with the highest business value.','how.priority':'PRIORITY','how.action':'Increase budget','how.impact':'Expected impact +18%','how.step3':'Act with clarity','how.step3Body':'Get recommendations that are understandable, prioritized and actionable.',
      'modules.eyebrow':'AN AI MARKETING OFFICER','modules.title':'One system for the entire decision chain.','modules.body':'From analysis and strategy to campaign suggestions and controlled automation.','modules.core':'Your strategic AI operator that understands the business, the data and the priorities.','modules.pulse':'Detects changes, anomalies and opportunities before they are easy to miss.','modules.launch':'Creates campaign proposals that can be reviewed and approved before anything goes live.','modules.ready':'Campaign ready','modules.review':'Review →','modules.auto':'Automate when you are ready, with clear boundaries, approvals and control.',
      'pulse.title':'Spot what is changing before it becomes a problem.','pulse.body':'Vexmera follows signals over time and helps you separate meaningful change from normal noise.','pulse.signal1':'Meta CPA has increased 21% in five days.','pulse.signal2':'Google Search ROAS remains consistently above target.','pulse.signal3':'Two campaigns account for 68% of growth.','pulse.performance':'Performance pulse','pulse.conversions':'Conversions',
      'workflow.title':'Automation without losing control.','workflow.body':'Vexmera can help all the way from opportunity to action, but you decide how far automation is allowed to go.','workflow.opportunity':'Opportunity','workflow.detected':'Signal detected','workflow.recommendation':'Recommendation','workflow.prioritized':'Prioritized action','workflow.approval':'Approval','workflow.human':'Human decision','workflow.action':'Action','workflow.logged':'Tracked activity','workflow.control1':'Human approval','workflow.control2':'Budget limits','workflow.control3':'Activity log','workflow.control4':'Pause anytime',
      'integrations.eyebrow':'INTEGRATIONS','integrations.title':'Vexmera works with the tools you already use.','integrations.connected':'Available','integrations.soon':'Coming soon',
      'outcomes.eyebrow':'WHAT VEXMERA IMPROVES','outcomes.title':'Less analysis work. Clearer priorities.','outcomes.body':'We do not use invented customer quotes or results. Vexmera should earn trust through a clear product and real case studies when they exist.','outcomes.one':'Less time spent on analysis','outcomes.two':'Better budget decisions','outcomes.three':'Faster problem detection','outcomes.four':'Clearer next steps',
      'founder.eyebrow':'WHY VEXMERA EXISTS','founder.title':'Built to turn more data into better decisions.','founder.lead':'Vexmera started from a simple problem: businesses have access to more marketing data than ever, but it is still difficult to know what actually deserves attention next.','founder.quote':'“The goal is not to give companies another dashboard. The goal is to make the path from signal to action clearer.”','founder.name':'Erol Bekir','founder.role':'Founder, Vexmera','founder.placeholder':'Founder portrait','founder.placeholderNote':'Final portrait added after image approval',
      'pricing.eyebrow':'PRICING','pricing.title':'A plan for every stage of growth.','pricing.body':'Clear pricing. No unnecessary complexity.','pricing.monthly':'Monthly','pricing.yearly':'Yearly','pricing.save':'2 months included','pricing.starterFor':'FOR SMALLER COMPANIES','pricing.starterBody':'For companies that want to bring their data together and understand marketing better.','pricing.growthFor':'FOR GROWING COMPANIES','pricing.growthBody':'The complete Vexmera experience for companies that want to grow smarter.','pricing.scaleFor':'FOR TEAMS & SCALE','pricing.scaleBody':'More capacity, more users and advanced controlled automation.','pricing.perMonth':'/ month','pricing.googleMeta':'Google + Meta','pricing.dashboard':'Dashboard & KPIs','pricing.basicInsights':'Basic AI insights','pricing.oneUser':'1 user','pricing.chooseStarter':'Choose Starter','pricing.popular':'MOST POPULAR','pricing.everythingStarter':'Everything in Starter','pricing.advancedInsights':'Advanced AI insights','pricing.competitors':'Competitor monitoring','pricing.threeUsers':'3 users','pricing.prioritySupport':'Priority support','pricing.chooseGrowth':'Choose Growth','pricing.everythingGrowth':'Everything in Growth','pricing.advancedWorkflows':'Advanced workflows','pricing.tenUsers':'10 users','pricing.onboarding':'Personal onboarding','pricing.premiumSupport':'Premium support','pricing.chooseScale':'Choose Scale','pricing.note':'Prices exclude VAT. The annual plan equals 10 months of payment for 12 months of usage.',
      'security.eyebrow':'SECURITY & CONTROL','security.title':'Your data. Your control.','security.body':'Vexmera is built to help you make decisions without taking control away from you.','security.permissions':'Permission controls','security.approvals':'Approval system','security.audit':'Activity log','security.encrypted':'Encrypted communication','security.rules':'Clear automation rules',
      'faq.title':'Frequently asked questions.','faq.q1':'What is Vexmera?','faq.a1':'Vexmera is an AI-powered marketing platform that helps companies bring data together, understand performance and prioritize what to do next.','faq.q2':'Do I need to be a marketing expert?','faq.a2':'No. Vexmera is built to make complex marketing data understandable and actionable.','faq.q3':'Can Vexmera change my campaigns automatically?','faq.a3':'Automation should happen within clear rules and control levels. You choose how much Vexmera is allowed to do and when human approval is required.','faq.q4':'Which platforms are supported?','faq.a4':'Google Ads and Meta Ads are the focus in the current beta. More integrations are being built step by step.','faq.q5':'Can I change language and theme?','faq.a5':'Yes. Vexmera is built with Swedish and English from the start, plus light, dark and system-based theme handling.','faq.q6':'How is my data protected?','faq.a6':'Vexmera uses permission controls, clear approval flows and the principle of never inventing live data that is not connected.',
      'final.title':'Market smarter.','final.line1':'Understand what is happening.','final.line2':'Know what to do next.','final.cta':'Try Vexmera →',
      'footer.product':'Product','footer.company':'Company','footer.about':'About Vexmera','footer.contact':'Contact','footer.legal':'Legal','footer.privacy':'Privacy','footer.cookies':'Cookies','footer.terms':'Terms','footer.theme':'Theme'
    }
  };

  let currentLanguage = localStorage.getItem('vexmera-language') || 'sv';
  let themePreference = localStorage.getItem('vexmera-theme') || 'light';
  let soundEnabled = localStorage.getItem('vexmera-sound') === 'on';
  let audioContext = null;

  const languageButton = document.getElementById('languageToggle');
  const footerLanguage = document.getElementById('footerLanguage');
  const themeButton = document.getElementById('themeToggle');
  const footerTheme = document.getElementById('footerTheme');
  const soundButton = document.getElementById('soundToggle');
  const menuButton = document.getElementById('menuToggle');
  const mobileMenu = document.getElementById('mobileMenu');
  const header = document.getElementById('siteHeader');

  function enhanceProductPreview() {
    const sidebar = document.querySelector('.dash-sidebar');
    const autopilot = Array.from(sidebar?.querySelectorAll('.dash-nav') || []).find((item) => item.textContent.trim().includes('Autopilot'));
    const spacer = sidebar?.querySelector('.dash-spacer');

    if (sidebar && autopilot && !sidebar.querySelector('[data-real-nav="queue"]')) {
      const queue = document.createElement('div');
      queue.className = 'dash-nav product-real';
      queue.dataset.realNav = 'queue';
      queue.innerHTML = '<b></b><span data-i18n="dash.queue">Queue</span><small>Approvals</small>';
      sidebar.insertBefore(queue, autopilot);
    }

    if (sidebar && autopilot && !sidebar.querySelector('[data-real-nav="rivals"]')) {
      const rivals = document.createElement('div');
      rivals.className = 'dash-nav product-real';
      rivals.dataset.realNav = 'rivals';
      rivals.innerHTML = '<b></b><span data-i18n="dash.rivals">Rivals</span><small>Watch</small>';
      autopilot.insertAdjacentElement('afterend', rivals);
    }

    if (sidebar && spacer && !sidebar.querySelector('[data-real-nav="connect"]')) {
      const connect = document.createElement('div');
      connect.className = 'dash-nav product-real muted';
      connect.dataset.realNav = 'connect';
      connect.innerHTML = '<b></b><span data-i18n="dash.connect">Connect</span><small>Data</small>';
      spacer.insertAdjacentElement('afterend', connect);
    }

    const connect = sidebar?.querySelector('[data-real-nav="connect"]');
    if (sidebar && connect && !sidebar.querySelector('[data-real-nav="insights"]')) {
      const insights = document.createElement('div');
      insights.className = 'dash-nav product-real muted';
      insights.dataset.realNav = 'insights';
      insights.innerHTML = '<b></b><span data-i18n="dash.insights">Insights</span><small>Reports</small>';
      connect.insertAdjacentElement('afterend', insights);
    }

    const dashTop = document.querySelector('.dash-top');
    if (dashTop && !dashTop.querySelector('.demo-data-pill')) {
      const demo = document.createElement('span');
      demo.className = 'demo-data-pill';
      demo.dataset.i18n = 'dash.demo';
      demo.textContent = 'DEMO DATA';
      dashTop.appendChild(demo);
    }

    const dashMain = document.querySelector('.dash-main');
    const dashGrid = dashMain?.querySelector('.dash-grid');
    if (dashMain && dashGrid && !dashMain.querySelector('.dash-status-row')) {
      const statusRow = document.createElement('div');
      statusRow.className = 'dash-status-row';
      statusRow.innerHTML = `
        <div class="dash-status-card">
          <div class="dash-status-icon">✓</div>
          <div><span data-i18n="dash.approvals">VÄNTANDE GODKÄNNANDEN</span><strong data-i18n="dash.approvalCount">2 väntar på granskning</strong></div>
          <small>Queue</small>
        </div>
        <div class="dash-status-card">
          <div class="dash-status-icon">↔</div>
          <div><span data-i18n="dash.sources">ANSLUTNA KÄLLOR</span><strong data-i18n="dash.sourceCount">Google + Meta</strong></div>
          <small>Live sync</small>
        </div>`;
      dashGrid.insertAdjacentElement('afterend', statusRow);
    }
  }

  function injectFounderSection() {
    const pricing = document.getElementById('pris');
    if (!pricing || document.querySelector('.founder-section')) return;
    const section = document.createElement('section');
    section.className = 'section founder-section section-wrap';
    section.id = 'founder';
    section.innerHTML = `
      <div class="founder-card reveal">
        <div class="founder-portrait" role="img" aria-label="Erol Bekir, grundare av Vexmera">
          <div class="founder-placeholder-label"><span data-i18n="founder.placeholder">Grundarporträtt</span><small data-i18n="founder.placeholderNote">Slutlig bild läggs in efter bildgodkännande</small></div>
        </div>
        <div class="founder-copy">
          <div class="eyebrow" data-i18n="founder.eyebrow">VARFÖR VEXMERA FINNS</div>
          <h2 data-i18n="founder.title">Byggt för att göra mer data till bättre beslut.</h2>
          <p class="founder-lead" data-i18n="founder.lead">Vexmera började i ett enkelt problem: företag har tillgång till mer marknadsföringsdata än någonsin, men det är fortfarande svårt att veta vad som faktiskt förtjänar uppmärksamhet härnäst.</p>
          <p class="founder-quote" data-i18n="founder.quote">“Målet är inte att ge företag ännu en dashboard. Målet är att göra vägen från signal till handling tydligare.”</p>
          <div class="founder-meta"><span class="founder-meta-mark">V</span><div><strong data-i18n="founder.name">Erol Bekir</strong><small data-i18n="founder.role">Grundare, Vexmera</small></div></div>
        </div>
      </div>`;
    pricing.parentNode.insertBefore(section, pricing);
  }

  enhanceProductPreview();
  injectFounderSection();

  function applyLanguage(lang) {
    currentLanguage = lang === 'en' ? 'en' : 'sv';
    localStorage.setItem('vexmera-language', currentLanguage);
    document.documentElement.lang = currentLanguage;
    if (languageButton) languageButton.textContent = currentLanguage.toUpperCase();
    document.querySelectorAll('[data-i18n]').forEach((element) => {
      const key = element.dataset.i18n;
      if (currentLanguage === 'en' && copy.en[key]) element.textContent = copy.en[key];
      if (currentLanguage === 'sv' && element.dataset.sv) element.textContent = element.dataset.sv;
    });
    if (currentLanguage === 'sv') restoreSwedish();
    updateBillingLabels();
  }

  const swedishOriginals = new Map();
  document.querySelectorAll('[data-i18n]').forEach((element) => swedishOriginals.set(element, element.textContent));
  function restoreSwedish() {
    swedishOriginals.forEach((value, element) => { element.textContent = value; });
  }

  function resolvedTheme(preference) {
    if (preference === 'system') return prefersDark.matches ? 'dark' : 'light';
    return preference === 'dark' ? 'dark' : 'light';
  }

  function applyTheme(preference) {
    themePreference = ['light','dark','system'].includes(preference) ? preference : 'light';
    localStorage.setItem('vexmera-theme', themePreference);
    const theme = resolvedTheme(themePreference);
    root.dataset.theme = theme;
    const themeMeta = document.querySelector('meta[name="theme-color"]');
    if (themeMeta) themeMeta.setAttribute('content', theme === 'dark' ? '#0d1117' : '#f7f5f0');
    if (themeButton) {
      const icon = themeButton.querySelector('.theme-icon');
      if (icon) icon.textContent = themePreference === 'light' ? '☼' : themePreference === 'dark' ? '◐' : '◒';
      themeButton.title = themePreference === 'system' ? 'System' : themePreference === 'dark' ? 'Dark' : 'Light';
    }
  }

  function cycleTheme() {
    const order = ['light','dark','system'];
    applyTheme(order[(order.indexOf(themePreference) + 1) % order.length]);
  }

  function updateSoundUI() {
    if (!soundButton) return;
    soundButton.classList.toggle('enabled', soundEnabled);
    soundButton.setAttribute('aria-label', soundEnabled ? 'Ljud på' : 'Ljud av');
    soundButton.title = soundEnabled ? 'Sound on' : 'Sound off';
  }

  function toggleSound() {
    soundEnabled = !soundEnabled;
    localStorage.setItem('vexmera-sound', soundEnabled ? 'on' : 'off');
    updateSoundUI();
    if (soundEnabled) playTone('enable');
  }

  function playTone(type = 'insight') {
    if (!soundEnabled) return;
    try {
      audioContext ||= new (window.AudioContext || window.webkitAudioContext)();
      if (audioContext.state === 'suspended') audioContext.resume();
      const now = audioContext.currentTime;
      const master = audioContext.createGain();
      master.gain.setValueAtTime(0.0001, now);
      master.gain.exponentialRampToValueAtTime(type === 'enable' ? 0.035 : 0.045, now + 0.025);
      master.gain.exponentialRampToValueAtTime(0.0001, now + 0.55);
      master.connect(audioContext.destination);

      const notes = type === 'enable' ? [392, 523.25] : [440, 554.37, 659.25];
      notes.forEach((frequency, index) => {
        const osc = audioContext.createOscillator();
        const gain = audioContext.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(frequency, now);
        gain.gain.setValueAtTime(0.0001, now + index * 0.055);
        gain.gain.exponentialRampToValueAtTime(0.32 / notes.length, now + 0.04 + index * 0.055);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.42 + index * 0.055);
        osc.connect(gain); gain.connect(master);
        osc.start(now + index * 0.055); osc.stop(now + 0.62);
      });
    } catch (_) {
      soundEnabled = false;
      updateSoundUI();
    }
  }

  let billingMode = 'monthly';
  function updateBillingLabels() {
    document.querySelectorAll('[data-monthly][data-yearly]').forEach((price) => {
      price.textContent = price.dataset[billingMode];
    });
    document.querySelectorAll('[data-price-period]').forEach((label) => {
      if (billingMode === 'monthly') label.textContent = currentLanguage === 'en' ? '/ month' : '/ mån';
      else label.textContent = currentLanguage === 'en' ? '/ year' : '/ år';
    });
  }

  document.querySelectorAll('[data-billing]').forEach((button) => {
    button.addEventListener('click', () => {
      billingMode = button.dataset.billing;
      document.querySelectorAll('[data-billing]').forEach((item) => item.classList.toggle('active', item === button));
      updateBillingLabels();
    });
  });

  function toggleMenu(force) {
    const open = typeof force === 'boolean' ? force : !mobileMenu.classList.contains('open');
    mobileMenu.classList.toggle('open', open);
    body.classList.toggle('menu-open', open);
    menuButton?.setAttribute('aria-expanded', String(open));
  }

  languageButton?.addEventListener('click', () => applyLanguage(currentLanguage === 'sv' ? 'en' : 'sv'));
  footerLanguage?.addEventListener('click', () => applyLanguage(currentLanguage === 'sv' ? 'en' : 'sv'));
  themeButton?.addEventListener('click', cycleTheme);
  footerTheme?.addEventListener('click', cycleTheme);
  soundButton?.addEventListener('click', toggleSound);
  menuButton?.addEventListener('click', () => toggleMenu());
  mobileMenu?.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => toggleMenu(false)));
  document.querySelectorAll('[data-sound="insight"]').forEach((button) => button.addEventListener('click', () => playTone('insight')));

  prefersDark.addEventListener?.('change', () => { if (themePreference === 'system') applyTheme('system'); });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('in-view');
      const parentSection = entry.target.closest('.section, .hero, .section-wrap');
      parentSection?.classList.add('in-view');
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.14, rootMargin: '0px 0px -7% 0px' });
  document.querySelectorAll('.reveal,.pulse-chart-card').forEach((element) => observer.observe(element));

  window.addEventListener('scroll', () => header?.classList.toggle('scrolled', window.scrollY > 18), { passive: true });

  if (!prefersReducedMotion.matches && window.matchMedia('(pointer:fine)').matches) {
    let targetX = window.innerWidth / 2, targetY = window.innerHeight / 2, currentX = targetX, currentY = targetY;
    window.addEventListener('pointermove', (event) => { targetX = event.clientX; targetY = event.clientY; }, { passive: true });
    const follow = () => {
      currentX += (targetX - currentX) * 0.065;
      currentY += (targetY - currentY) * 0.065;
      root.style.setProperty('--px', `${currentX}px`);
      root.style.setProperty('--py', `${currentY}px`);
      requestAnimationFrame(follow);
    };
    requestAnimationFrame(follow);
  }

  applyTheme(themePreference);
  updateSoundUI();
  applyLanguage(currentLanguage);
})();