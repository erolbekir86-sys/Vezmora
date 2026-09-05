(() => {
  const addStylesheet = (href) => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    document.head.appendChild(link);
  };

  addStylesheet('/static/landing-polish.css?v=4');
  addStylesheet('/static/landing-founder.css?v=4');
  addStylesheet('/static/landing-final.css?v=1');

  const root = document.documentElement;
  const body = document.body;
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  const copy = {
    sv: {
      'nav.product':'Produkt','nav.how':'Så fungerar det','nav.features':'Funktioner','nav.pricing':'Pris','nav.login':'Logga in','nav.start':'Kom igång',
      'hero.eyebrow':'AI-DRIVEN MARKETING INTELLIGENCE','hero.title1':'Förstå din marknadsföring.','hero.title2':'Vet exakt vad du ska göra härnäst.','hero.lead':'Vexmera samlar din marknadsföringsdata, analyserar vad som faktiskt driver resultat och förvandlar komplex information till tydliga beslut.','hero.cta':'Prova Vexmera →','hero.demo':'Se hur det fungerar','hero.proof1':'Byggt för små och växande företag','hero.proof2':'Tydliga rekommendationer','hero.proof3':'Kontroll före automation',
      'dash.overview':'Översikt','dash.settings':'Inställningar','dash.campaigns':'Kampanjer','dash.competitors':'Konkurrenter','dash.connections':'Anslutningar','dash.insights':'Insikter','dash.demo':'DEMODATA','dash.beta':'PRIVAT BETA','dash.overviewUpper':'ÖVERSIKT','dash.morning':'God morgon.','dash.summary':'Här är vad som händer i din marknadsföring.','dash.days':'dagar','dash.revenue':'Omsättning','dash.leads':'Leads','dash.recommends':'CORE REKOMMENDERAR','dash.recTitle':'Flytta 15 % mer budget till kampanjen med högst lönsamhet.','dash.recBody':'Google Search presterar 31 % över kontots genomsnittliga ROAS de senaste 14 dagarna.','dash.effect':'Beräknad effekt','dash.viewAnalysis':'Visa analys','dash.performance':'Resultatutveckling','dash.days30':'30 dagar','dash.approvalsLabel':'GODKÄNNANDEN','dash.approvalsValue':'2 väntar på granskning','dash.approvalsMeta':'Queue','dash.sourcesLabel':'ANSLUTNA KÄLLOR','dash.sourcesValue':'Google Ads + Meta Ads','dash.sourcesMeta':'Synkroniseras',
      'float.opportunities':'3 möjligheter hittade','float.priority':'Prioriterade efter affärseffekt','float.synced':'Synkat och analyserat',
      'trust.oneTitle':'Byggt för växande företag','trust.oneBody':'Kraftfullt utan att bli överväldigande.','trust.twoTitle':'Tydliga rekommendationer','trust.twoBody':'Konkreta beslut, inte bara mer data.','trust.threeTitle':'Du behåller kontrollen','trust.threeBody':'Vexmera föreslår. Du bestämmer.',
      'problem.eyebrow':'ETT STÄLLE. ETT SPRÅK. BÄTTRE BESLUT.','problem.title':'Marknadsföring borde inte kräva fem dashboards.','problem.body':'Datan finns redan. Problemet är att den ligger utspridd. Vexmera samlar signalerna och gör dem begripliga.','problem.output':'Prioriterad intelligens',
      'demo.eyebrow':'FRÅN SIGNAL TILL NÄSTA DRAG','demo.title':'Vexmera visar inte bara vad som hände. Den hjälper dig förstå vad du bör göra härnäst.','demo.body':'Insikterna prioriteras efter potentiell affärseffekt, så att du kan lägga tiden där den faktiskt spelar roll.','demo.item1':'Förklarar varför något förändrats','demo.item2':'Prioriterar efter påverkan','demo.item3':'Ger ett tydligt nästa steg','demo.justNow':'Just nu','demo.insightTitle':'Google Search genererar 37 % högre ROAS än Meta Prospecting.','demo.current':'Nuvarande ROAS','demo.potential':'Potential','demo.recommendation':'REKOMMENDATION','demo.recommendText':'Flytta 4 000 kr av kommande veckas budget från Meta Prospecting till Google Search.','demo.show':'Visa analys',
      'value.simple':'Enklare','value.simpleBody':'All viktig marknadsföringsdata på ett ställe. Mindre hoppande mellan verktyg.','value.fast':'Snabbare','value.fastBody':'Från ”vad betyder det här?” till ett tydligt nästa steg på minuter, inte timmar.','value.smart':'Smartare','value.smartBody':'AI prioriterar signalerna som faktiskt kan påverka lönsamhet och tillväxt.',
      'how.eyebrow':'SÅ FUNGERAR DET','how.title':'Från data till beslut på tre steg.','how.body':'Koppla dina kanaler och låt Vexmera bygga en tydligare bild av vad som fungerar.','how.step1':'Koppla dina kanaler','how.step1Body':'Samla Google Ads och Meta Ads i en gemensam vy.','how.step2':'Vexmera analyserar','how.step2Body':'AI letar efter avvikelser, mönster och möjligheter med högst affärsvärde.','how.priority':'PRIORITET','how.action':'Öka budget','how.impact':'Förväntad effekt +18 %','how.step3':'Agera med tydlighet','how.step3Body':'Få rekommendationer som är begripliga, prioriterade och möjliga att agera på.',
      'modules.eyebrow':'DIN AI MARKETING OFFICER','modules.title':'Ett system för hela beslutskedjan.','modules.body':'Från analys och strategi till kampanjförslag och kontrollerad automation.','modules.core':'Din strategiska AI-operatör som förstår verksamheten, datan och prioriteringarna.','modules.pulse':'Upptäcker förändringar, avvikelser och möjligheter innan de blir lätta att missa.','modules.launch':'Skapar kampanjförslag som kan granskas och godkännas innan något går live.','modules.ready':'Kampanj redo','modules.review':'Granska →','modules.auto':'Automatisera när du är redo, med tydliga gränser, godkännanden och full kontroll.',
      'visual.coreLabel':'HÖGST PRIORITET','visual.coreTitle':'Budgetmöjlighet upptäckt','visual.coreMeta':'Google Search över målet','visual.impact':'effekt','visual.pulseLabel':'SIGNAL','visual.pulseAlert':'CPA +21 %','visual.launchLabel':'KAMPANJFÖRSLAG','visual.launchTitle':'Search · Sverige','visual.launchMeta':'Budget 2 000 kr/dag','visual.review':'Granska','visual.autoSuggest':'Föreslå','visual.autoAssisted':'Assisterad','visual.autoAuto':'Auto','visual.safety1':'Budgetgräns','visual.safety2':'Godkännande','visual.safety3':'Loggning',
      'pulse.title':'Upptäck vad som förändras innan det blir ett problem.','pulse.body':'Vexmera följer signaler över tid och hjälper dig skilja verkliga förändringar från vanligt brus.','pulse.signal1':'Meta CPA har ökat 21 % på fem dagar.','pulse.signal2':'Google Search ROAS ligger stabilt över målet.','pulse.signal3':'Två kampanjer står för 68 % av tillväxten.','pulse.performance':'Resultatpuls','pulse.conversions':'Konverteringar',
      'workflow.title':'Automation utan att tappa kontrollen.','workflow.body':'Vexmera kan hjälpa dig hela vägen från möjlighet till åtgärd, men du bestämmer hur långt automationen får gå.','workflow.opportunity':'Möjlighet','workflow.detected':'Signal upptäckt','workflow.recommendation':'Rekommendation','workflow.prioritized':'Prioriterad åtgärd','workflow.approval':'Godkännande','workflow.human':'Mänskligt beslut','workflow.action':'Åtgärd','workflow.logged':'Spårad aktivitet','workflow.control1':'Mänskligt godkännande','workflow.control2':'Budgetgränser','workflow.control3':'Aktivitetslogg','workflow.control4':'Pausa när som helst',
      'integrations.eyebrow':'INTEGRATIONER','integrations.title':'Vexmera arbetar med verktygen du redan använder.','integrations.connected':'Privat beta','integrations.soon':'Kommer snart',
      'outcomes.eyebrow':'VAD VEXMERA FÖRBÄTTRAR','outcomes.title':'Mindre analysarbete. Tydligare prioriteringar.','outcomes.body':'Vexmera är byggt för att korta vägen från data till beslut, så att du kan lägga mindre tid på att tolka dashboards och mer tid på rätt nästa steg.','outcomes.one':'Mindre tid på analys','outcomes.two':'Bättre budgetbeslut','outcomes.three':'Snabbare problemupptäckt','outcomes.four':'Tydligare nästa steg',
      'founder.eyebrow':'VARFÖR VEXMERA FINNS','founder.title':'Byggt för att göra mer data till bättre beslut.','founder.lead':'Vexmera föddes ur ett enkelt problem: företag har tillgång till mer marknadsföringsdata än någonsin, men det är fortfarande svårt att veta vad som faktiskt förtjänar uppmärksamhet härnäst.','founder.quote':'“Målet är inte att ge företag ännu en dashboard. Målet är att göra vägen från signal till handling tydligare.”','founder.name':'Erol Bekir','founder.role':'Grundare, Vexmera',
      'pricing.eyebrow':'PRISER','pricing.title':'En plan för varje tillväxtfas.','pricing.body':'Tydliga priser. Ingen onödig komplexitet.','pricing.monthly':'Månadsvis','pricing.yearly':'Årsvis','pricing.save':'2 månader på köpet','pricing.starterFor':'FÖR MINDRE FÖRETAG','pricing.starterBody':'För dig som vill samla datan och förstå marknadsföringen bättre.','pricing.growthFor':'FÖR VÄXANDE FÖRETAG','pricing.growthBody':'Den kompletta Vexmera-upplevelsen för företag som vill växa smartare.','pricing.scaleFor':'FÖR TEAM & SKALA','pricing.scaleBody':'Mer kapacitet, fler användare och avancerad, kontrollerad automation.','pricing.perMonth':'/ mån','pricing.googleMeta':'Google Ads + Meta Ads','pricing.dashboard':'Dashboard och KPI:er','pricing.basicInsights':'Grundläggande AI-insikter','pricing.oneUser':'1 användare','pricing.chooseStarter':'Välj Starter','pricing.popular':'POPULÄRAST','pricing.everythingStarter':'Allt i Starter','pricing.advancedInsights':'Avancerade AI-insikter','pricing.competitors':'Konkurrentbevakning','pricing.threeUsers':'3 användare','pricing.prioritySupport':'Prioriterad support','pricing.chooseGrowth':'Välj Growth','pricing.everythingGrowth':'Allt i Growth','pricing.advancedWorkflows':'Avancerade arbetsflöden','pricing.tenUsers':'10 användare','pricing.onboarding':'Personlig onboarding','pricing.premiumSupport':'Premiumsupport','pricing.chooseScale':'Välj Scale','pricing.note':'Priser exkl. moms. Årsplanen motsvarar 10 månaders betalning för 12 månaders användning.',
      'security.eyebrow':'SÄKERHET & KONTROLL','security.title':'Din data. Din kontroll.','security.body':'Vexmera är byggt för att hjälpa dig fatta bättre beslut utan att ta kontrollen ifrån dig.','security.permissions':'Behörighetsstyrning','security.approvals':'Godkännandeflöden','security.audit':'Aktivitetslogg','security.encrypted':'Krypterad kommunikation','security.rules':'Tydliga automationsregler',
      'faq.title':'Vanliga frågor.','faq.q1':'Vad är Vexmera?','faq.a1':'Vexmera är en AI-driven marknadsföringsplattform som hjälper företag att samla data, förstå resultat och prioritera nästa steg.','faq.q2':'Behöver jag vara marknadsföringsexpert?','faq.a2':'Nej. Vexmera är byggt för att göra komplex marknadsföringsdata begriplig och handlingsbar.','faq.q3':'Kan Vexmera ändra mina kampanjer automatiskt?','faq.a3':'Automation sker inom tydliga regler och kontrollnivåer. Du väljer hur mycket Vexmera får göra och när mänskligt godkännande krävs.','faq.q4':'Vilka plattformar stöds?','faq.a4':'Google Ads och Meta Ads är i fokus i den nuvarande privata betan. Fler integrationer byggs stegvis.','faq.q5':'Kan jag byta språk och tema?','faq.a5':'Ja. Vexmera är byggt med svenska och engelska från start samt stöd för ljust, mörkt och systembaserat tema.','faq.q6':'Hur skyddas min data?','faq.a6':'Vexmera använder behörighetsstyrning, tydliga godkännandeflöden och visar aldrig live-data som inte faktiskt är ansluten.',
      'final.title':'Marknadsför smartare.','final.line1':'Förstå vad som händer.','final.line2':'Vet vad du ska göra härnäst.','final.cta':'Prova Vexmera →',
      'footer.product':'Produkt','footer.company':'Företag','footer.about':'Om Vexmera','footer.contact':'Kontakt','footer.legal':'Juridik','footer.privacy':'Integritet','footer.cookies':'Cookies','footer.terms':'Villkor','footer.theme':'Tema'
    },
    en: {
      'nav.product':'Product','nav.how':'How it works','nav.features':'Features','nav.pricing':'Pricing','nav.login':'Log in','nav.start':'Get started',
      'hero.eyebrow':'AI-DRIVEN MARKETING INTELLIGENCE','hero.title1':'Understand your marketing.','hero.title2':'Know exactly what to do next.','hero.lead':'Vexmera brings your marketing data together, analyzes what actually drives results, and turns complex information into clear decisions.','hero.cta':'Try Vexmera →','hero.demo':'See how it works','hero.proof1':'Built for small and growing companies','hero.proof2':'Clear recommendations','hero.proof3':'Control before automation',
      'dash.overview':'Overview','dash.settings':'Settings','dash.campaigns':'Campaigns','dash.competitors':'Competitors','dash.connections':'Connections','dash.insights':'Insights','dash.demo':'DEMO DATA','dash.beta':'PRIVATE BETA','dash.overviewUpper':'OVERVIEW','dash.morning':'Good morning.','dash.summary':'Here is what is happening in your marketing.','dash.days':'days','dash.revenue':'Revenue','dash.leads':'Leads','dash.recommends':'CORE RECOMMENDS','dash.recTitle':'Move 15% more budget to the campaign with the highest profitability.','dash.recBody':'Google Search is performing 31% above the account’s average ROAS over the last 14 days.','dash.effect':'Estimated impact','dash.viewAnalysis':'View analysis','dash.performance':'Performance trend','dash.days30':'30 days','dash.approvalsLabel':'APPROVALS','dash.approvalsValue':'2 waiting for review','dash.approvalsMeta':'Queue','dash.sourcesLabel':'CONNECTED SOURCES','dash.sourcesValue':'Google Ads + Meta Ads','dash.sourcesMeta':'Syncing',
      'float.opportunities':'3 opportunities found','float.priority':'Prioritized by business impact','float.synced':'Synced and analyzed',
      'trust.oneTitle':'Built for growing companies','trust.oneBody':'Powerful without becoming overwhelming.','trust.twoTitle':'Clear recommendations','trust.twoBody':'Concrete decisions, not just more data.','trust.threeTitle':'You stay in control','trust.threeBody':'Vexmera recommends. You decide.',
      'problem.eyebrow':'ONE PLACE. ONE LANGUAGE. BETTER DECISIONS.','problem.title':'Marketing should not require five dashboards.','problem.body':'The data already exists. The problem is that it is scattered. Vexmera brings the signals together and makes them understandable.','problem.output':'Prioritized intelligence',
      'demo.eyebrow':'FROM SIGNAL TO NEXT MOVE','demo.title':'Vexmera doesn’t just show what happened. It helps you understand what to do next.','demo.body':'Insights are prioritized by potential business impact, so you can spend your time where it actually matters.','demo.item1':'Explains why something changed','demo.item2':'Prioritizes by impact','demo.item3':'Gives you a clear next step','demo.justNow':'Just now','demo.insightTitle':'Google Search generates 37% higher ROAS than Meta Prospecting.','demo.current':'Current ROAS','demo.potential':'Potential','demo.recommendation':'RECOMMENDATION','demo.recommendText':'Move SEK 4,000 of next week’s budget from Meta Prospecting to Google Search.','demo.show':'View analysis',
      'value.simple':'Simpler','value.simpleBody':'All important marketing data in one place. Less jumping between tools.','value.fast':'Faster','value.fastBody':'Go from “what does this mean?” to a clear next step in minutes, not hours.','value.smart':'Smarter','value.smartBody':'AI prioritizes the signals that can actually affect profitability and growth.',
      'how.eyebrow':'HOW IT WORKS','how.title':'From data to decisions in three steps.','how.body':'Connect your channels and let Vexmera build a clearer picture of what works.','how.step1':'Connect your channels','how.step1Body':'Bring Google Ads and Meta Ads into one shared view.','how.step2':'Vexmera analyzes','how.step2Body':'AI looks for anomalies, patterns, and opportunities with the highest business value.','how.priority':'PRIORITY','how.action':'Increase budget','how.impact':'Expected impact +18%','how.step3':'Act with clarity','how.step3Body':'Get recommendations that are understandable, prioritized, and actionable.',
      'modules.eyebrow':'YOUR AI MARKETING OFFICER','modules.title':'One system for the entire decision chain.','modules.body':'From analysis and strategy to campaign proposals and controlled automation.','modules.core':'Your strategic AI operator that understands the business, the data, and the priorities.','modules.pulse':'Detects changes, anomalies, and opportunities before they are easy to miss.','modules.launch':'Creates campaign proposals that can be reviewed and approved before anything goes live.','modules.ready':'Campaign ready','modules.review':'Review →','modules.auto':'Automate when you are ready, with clear boundaries, approvals, and full control.',
      'visual.coreLabel':'TOP PRIORITY','visual.coreTitle':'Budget opportunity detected','visual.coreMeta':'Google Search above target','visual.impact':'impact','visual.pulseLabel':'SIGNAL','visual.pulseAlert':'CPA +21%','visual.launchLabel':'CAMPAIGN PROPOSAL','visual.launchTitle':'Search · Sweden','visual.launchMeta':'Budget SEK 2,000/day','visual.review':'Review','visual.autoSuggest':'Suggest','visual.autoAssisted':'Assisted','visual.autoAuto':'Auto','visual.safety1':'Budget limit','visual.safety2':'Approval','visual.safety3':'Logging',
      'pulse.title':'Spot what is changing before it becomes a problem.','pulse.body':'Vexmera follows signals over time and helps you separate meaningful change from normal noise.','pulse.signal1':'Meta CPA has increased 21% in five days.','pulse.signal2':'Google Search ROAS remains consistently above target.','pulse.signal3':'Two campaigns account for 68% of growth.','pulse.performance':'Performance pulse','pulse.conversions':'Conversions',
      'workflow.title':'Automation without losing control.','workflow.body':'Vexmera can help all the way from opportunity to action, but you decide how far automation is allowed to go.','workflow.opportunity':'Opportunity','workflow.detected':'Signal detected','workflow.recommendation':'Recommendation','workflow.prioritized':'Prioritized action','workflow.approval':'Approval','workflow.human':'Human decision','workflow.action':'Action','workflow.logged':'Tracked activity','workflow.control1':'Human approval','workflow.control2':'Budget limits','workflow.control3':'Activity log','workflow.control4':'Pause anytime',
      'integrations.eyebrow':'INTEGRATIONS','integrations.title':'Vexmera works with the tools you already use.','integrations.connected':'Private beta','integrations.soon':'Coming soon',
      'outcomes.eyebrow':'WHAT VEXMERA IMPROVES','outcomes.title':'Less analysis work. Clearer priorities.','outcomes.body':'Vexmera is built to shorten the path from data to decision, so you can spend less time interpreting dashboards and more time acting on the right next step.','outcomes.one':'Less time spent on analysis','outcomes.two':'Better budget decisions','outcomes.three':'Faster problem detection','outcomes.four':'Clearer next steps',
      'founder.eyebrow':'WHY VEXMERA EXISTS','founder.title':'Built to turn more data into better decisions.','founder.lead':'Vexmera was born from a simple problem: businesses have access to more marketing data than ever, yet it is still difficult to know what actually deserves attention next.','founder.quote':'“The goal isn’t to give companies another dashboard. It’s to make the path from signal to action clearer.”','founder.name':'Erol Bekir','founder.role':'Founder, Vexmera',
      'pricing.eyebrow':'PRICING','pricing.title':'A plan for every stage of growth.','pricing.body':'Clear pricing. No unnecessary complexity.','pricing.monthly':'Monthly','pricing.yearly':'Yearly','pricing.save':'2 months included','pricing.starterFor':'FOR SMALLER COMPANIES','pricing.starterBody':'For companies that want to bring their data together and understand marketing better.','pricing.growthFor':'FOR GROWING COMPANIES','pricing.growthBody':'The complete Vexmera experience for companies that want to grow smarter.','pricing.scaleFor':'FOR TEAMS & SCALE','pricing.scaleBody':'More capacity, more users, and advanced controlled automation.','pricing.perMonth':'/ month','pricing.googleMeta':'Google Ads + Meta Ads','pricing.dashboard':'Dashboard and KPIs','pricing.basicInsights':'Basic AI insights','pricing.oneUser':'1 user','pricing.chooseStarter':'Choose Starter','pricing.popular':'MOST POPULAR','pricing.everythingStarter':'Everything in Starter','pricing.advancedInsights':'Advanced AI insights','pricing.competitors':'Competitor monitoring','pricing.threeUsers':'3 users','pricing.prioritySupport':'Priority support','pricing.chooseGrowth':'Choose Growth','pricing.everythingGrowth':'Everything in Growth','pricing.advancedWorkflows':'Advanced workflows','pricing.tenUsers':'10 users','pricing.onboarding':'Personal onboarding','pricing.premiumSupport':'Premium support','pricing.chooseScale':'Choose Scale','pricing.note':'Prices exclude VAT. The annual plan equals 10 months of payment for 12 months of usage.',
      'security.eyebrow':'SECURITY & CONTROL','security.title':'Your data. Your control.','security.body':'Vexmera is built to help you make better decisions without taking control away from you.','security.permissions':'Permission controls','security.approvals':'Approval workflows','security.audit':'Activity log','security.encrypted':'Encrypted communication','security.rules':'Clear automation rules',
      'faq.title':'Frequently asked questions.','faq.q1':'What is Vexmera?','faq.a1':'Vexmera is an AI-powered marketing platform that helps companies bring data together, understand performance, and prioritize what to do next.','faq.q2':'Do I need to be a marketing expert?','faq.a2':'No. Vexmera is built to make complex marketing data understandable and actionable.','faq.q3':'Can Vexmera change my campaigns automatically?','faq.a3':'Automation happens within clear rules and control levels. You choose how much Vexmera is allowed to do and when human approval is required.','faq.q4':'Which platforms are supported?','faq.a4':'Google Ads and Meta Ads are the focus of the current private beta. More integrations are being added step by step.','faq.q5':'Can I change the language and theme?','faq.a5':'Yes. Vexmera is built with Swedish and English from the start, plus light, dark, and system-based theme support.','faq.q6':'How is my data protected?','faq.a6':'Vexmera uses permission controls, clear approval workflows, and never presents live data that is not actually connected.',
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
    if (sidebar && !sidebar.dataset.enhanced) {
      sidebar.dataset.enhanced = 'true';
      sidebar.innerHTML = `
        <div class="mini-brand">V</div>
        <div class="dash-nav active"><b></b><span data-i18n="dash.overview">Översikt</span></div>
        <div class="dash-nav"><b></b><span>Core</span></div>
        <div class="dash-nav"><b></b><span>Pulse</span></div>
        <div class="dash-nav"><b></b><span>Launch</span></div>
        <div class="dash-nav"><b></b><span>Autopilot</span></div>
        <div class="dash-nav" data-extra="true"><b></b><span data-i18n="dash.campaigns">Kampanjer</span></div>
        <div class="dash-nav" data-extra="true"><b></b><span data-i18n="dash.competitors">Konkurrenter</span></div>
        <div class="dash-nav" data-extra="true"><b></b><span data-i18n="dash.connections">Anslutningar</span></div>
        <div class="dash-nav" data-extra="true"><b></b><span data-i18n="dash.insights">Insikter</span></div>
        <div class="dash-spacer"></div>
        <div class="dash-nav muted"><b></b><span data-i18n="dash.settings">Inställningar</span></div>`;
    }

    const dashTop = document.querySelector('.dash-top');
    if (dashTop && !dashTop.querySelector('.dash-top-actions')) {
      const date = dashTop.querySelector('.dash-date');
      const actions = document.createElement('div');
      actions.className = 'dash-top-actions';
      if (date) actions.appendChild(date);
      const demo = document.createElement('span');
      demo.className = 'demo-data-pill';
      demo.dataset.i18n = 'dash.demo';
      demo.textContent = 'DEMODATA';
      const beta = document.createElement('span');
      beta.className = 'beta-data-pill';
      beta.dataset.i18n = 'dash.beta';
      beta.textContent = 'PRIVAT BETA';
      actions.append(demo,beta);
      dashTop.appendChild(actions);
    }

    const dashGrid = document.querySelector('.dash-grid');
    if (dashGrid && !document.querySelector('.dashboard-status-row')) {
      const row = document.createElement('div');
      row.className = 'dashboard-status-row';
      row.innerHTML = `
        <div class="dashboard-status-card">
          <span class="dashboard-status-icon">✓</span>
          <div><small data-i18n="dash.approvalsLabel">GODKÄNNANDEN</small><strong data-i18n="dash.approvalsValue">2 väntar på granskning</strong></div>
          <span data-i18n="dash.approvalsMeta">Queue</span>
        </div>
        <div class="dashboard-status-card">
          <span class="dashboard-status-icon">↔</span>
          <div><small data-i18n="dash.sourcesLabel">ANSLUTNA KÄLLOR</small><strong data-i18n="dash.sourcesValue">Google Ads + Meta Ads</strong></div>
          <span data-i18n="dash.sourcesMeta">Synkroniseras</span>
        </div>`;
      dashGrid.insertAdjacentElement('afterend',row);
    }
  }

  function enhanceModuleVisuals() {
    document.querySelectorAll('.module-card').forEach((card) => {
      if (card.querySelector('.module-visual-final')) return;
      const name = card.querySelector('h3')?.textContent?.trim();
      const visual = document.createElement('div');
      visual.className = 'module-visual-final';
      if (name === 'Core') {
        visual.classList.add('mv-core');
        visual.innerHTML = `<div class="mv-copy"><span class="mv-label" data-i18n="visual.coreLabel">HÖGST PRIORITET</span><strong data-i18n="visual.coreTitle">Budgetmöjlighet upptäckt</strong><small data-i18n="visual.coreMeta">Google Search över målet</small></div><div class="mv-impact">+18%<small data-i18n="visual.impact">effekt</small></div>`;
      } else if (name === 'Pulse') {
        visual.classList.add('mv-pulse');
        visual.innerHTML = `<div class="mv-pulse-head"><span class="mv-label" data-i18n="visual.pulseLabel">SIGNAL</span><span class="mv-alert" data-i18n="visual.pulseAlert">CPA +21 %</span></div><div class="mv-bars"><i></i><i></i><i></i><i></i><i></i><i></i></div>`;
      } else if (name === 'Launch') {
        visual.classList.add('mv-launch');
        visual.innerHTML = `<div class="mv-ad">Ad</div><div class="mv-copy"><span class="mv-label" data-i18n="visual.launchLabel">KAMPANJFÖRSLAG</span><strong data-i18n="visual.launchTitle">Search · Sverige</strong><small data-i18n="visual.launchMeta">Budget 2 000 kr/dag</small></div><span class="mv-review" data-i18n="visual.review">Granska</span>`;
      } else if (name === 'Autopilot') {
        visual.classList.add('mv-auto');
        visual.innerHTML = `<div class="mv-modes"><span data-i18n="visual.autoSuggest">Föreslå</span><span class="active" data-i18n="visual.autoAssisted">Assisterad</span><span data-i18n="visual.autoAuto">Auto</span></div><div class="mv-safety"><span data-i18n="visual.safety1">Budgetgräns</span><span data-i18n="visual.safety2">Godkännande</span><span data-i18n="visual.safety3">Loggning</span></div>`;
      } else {
        return;
      }
      card.appendChild(visual);
    });
  }

  function injectFounderSection() {
    const pricing = document.getElementById('pris');
    if (!pricing || document.querySelector('.founder-section')) return;
    const section = document.createElement('section');
    section.className = 'section founder-section section-wrap';
    section.id = 'founder';
    section.innerHTML = `
      <div class="founder-card reveal">
        <div class="founder-portrait" role="img" aria-label="Erol Bekir, grundare av Vexmera"></div>
        <div class="founder-copy">
          <div class="eyebrow" data-i18n="founder.eyebrow">VARFÖR VEXMERA FINNS</div>
          <h2 data-i18n="founder.title">Byggt för att göra mer data till bättre beslut.</h2>
          <p class="founder-lead" data-i18n="founder.lead">Vexmera föddes ur ett enkelt problem: företag har tillgång till mer marknadsföringsdata än någonsin, men det är fortfarande svårt att veta vad som faktiskt förtjänar uppmärksamhet härnäst.</p>
          <p class="founder-quote" data-i18n="founder.quote">“Målet är inte att ge företag ännu en dashboard. Målet är att göra vägen från signal till handling tydligare.”</p>
          <div class="founder-meta"><span class="founder-meta-mark">V</span><div><strong data-i18n="founder.name">Erol Bekir</strong><small data-i18n="founder.role">Grundare, Vexmera</small></div></div>
        </div>
      </div>`;
    pricing.parentNode.insertBefore(section,pricing);
  }

  function applyLanguage(lang) {
    currentLanguage = lang === 'en' ? 'en' : 'sv';
    localStorage.setItem('vexmera-language',currentLanguage);
    root.lang = currentLanguage;
    const dict = copy[currentLanguage];
    document.querySelectorAll('[data-i18n]').forEach((element) => {
      const text = dict[element.dataset.i18n];
      if (typeof text === 'string') element.textContent = text;
    });
    if (languageButton) languageButton.textContent = currentLanguage.toUpperCase();
    if (footerLanguage) footerLanguage.textContent = currentLanguage === 'sv' ? 'SV / EN' : 'EN / SV';
    document.title = 'Vexmera — AI Marketing Officer';
    const description = document.querySelector('meta[name="description"]');
    if (description) description.content = currentLanguage === 'sv'
      ? 'Vexmera är din AI Marketing Officer. Förstå din marknadsföring, se vad som driver resultat och vet vad du ska göra härnäst.'
      : 'Vexmera is your AI Marketing Officer. Understand your marketing, see what drives results, and know what to do next.';
    const founderPortrait = document.querySelector('.founder-portrait');
    if (founderPortrait) founderPortrait.setAttribute('aria-label',currentLanguage === 'sv' ? 'Erol Bekir, grundare av Vexmera' : 'Erol Bekir, founder of Vexmera');
    updateBillingLabels();
  }

  function resolvedTheme(preference) {
    if (preference === 'system') return prefersDark.matches ? 'dark' : 'light';
    return preference === 'dark' ? 'dark' : 'light';
  }

  function applyTheme(preference) {
    themePreference = ['light','dark','system'].includes(preference) ? preference : 'light';
    localStorage.setItem('vexmera-theme',themePreference);
    const theme = resolvedTheme(themePreference);
    root.dataset.theme = theme;
    const themeMeta = document.querySelector('meta[name="theme-color"]');
    if (themeMeta) themeMeta.setAttribute('content',theme === 'dark' ? '#0d1117' : '#f7f5f0');
    if (themeButton) {
      const icon = themeButton.querySelector('.theme-icon');
      if (icon) icon.textContent = themePreference === 'light' ? '☼' : themePreference === 'dark' ? '◐' : '◒';
      themeButton.title = themePreference === 'system' ? 'System' : themePreference === 'dark' ? 'Dark' : 'Light';
    }
  }

  function cycleTheme() {
    const order = ['light','dark','system'];
    applyTheme(order[(order.indexOf(themePreference)+1)%order.length]);
  }

  function updateSoundUI() {
    if (!soundButton) return;
    soundButton.classList.toggle('enabled',soundEnabled);
    soundButton.setAttribute('aria-label',soundEnabled ? 'Ljud på' : 'Ljud av');
    soundButton.title = soundEnabled ? 'Sound on' : 'Sound off';
  }

  function toggleSound() {
    soundEnabled = !soundEnabled;
    localStorage.setItem('vexmera-sound',soundEnabled ? 'on' : 'off');
    updateSoundUI();
    if (soundEnabled) playTone('enable');
  }

  function playTone(type='insight') {
    if (!soundEnabled) return;
    try {
      audioContext ||= new (window.AudioContext || window.webkitAudioContext)();
      if (audioContext.state === 'suspended') audioContext.resume();
      const now = audioContext.currentTime;
      const master = audioContext.createGain();
      master.gain.setValueAtTime(.0001,now);
      master.gain.exponentialRampToValueAtTime(type === 'enable' ? .035 : .045,now+.025);
      master.gain.exponentialRampToValueAtTime(.0001,now+.55);
      master.connect(audioContext.destination);
      const notes = type === 'enable' ? [392,523.25] : [440,554.37,659.25];
      notes.forEach((frequency,index) => {
        const osc = audioContext.createOscillator();
        const gain = audioContext.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(frequency,now);
        gain.gain.setValueAtTime(.0001,now+index*.055);
        gain.gain.exponentialRampToValueAtTime(.32/notes.length,now+.04+index*.055);
        gain.gain.exponentialRampToValueAtTime(.0001,now+.42+index*.055);
        osc.connect(gain); gain.connect(master);
        osc.start(now+index*.055); osc.stop(now+.62);
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

  function toggleMenu(force) {
    if (!mobileMenu) return;
    const open = typeof force === 'boolean' ? force : !mobileMenu.classList.contains('open');
    mobileMenu.classList.toggle('open',open);
    body.classList.toggle('menu-open',open);
    menuButton?.setAttribute('aria-expanded',String(open));
  }

  enhanceProductPreview();
  enhanceModuleVisuals();
  injectFounderSection();

  document.querySelectorAll('[data-billing]').forEach((button) => {
    button.addEventListener('click',() => {
      billingMode = button.dataset.billing;
      document.querySelectorAll('[data-billing]').forEach((item) => item.classList.toggle('active',item === button));
      updateBillingLabels();
    });
  });

  languageButton?.addEventListener('click',() => applyLanguage(currentLanguage === 'sv' ? 'en' : 'sv'));
  footerLanguage?.addEventListener('click',() => applyLanguage(currentLanguage === 'sv' ? 'en' : 'sv'));
  themeButton?.addEventListener('click',cycleTheme);
  footerTheme?.addEventListener('click',cycleTheme);
  soundButton?.addEventListener('click',toggleSound);
  menuButton?.addEventListener('click',() => toggleMenu());
  mobileMenu?.querySelectorAll('a').forEach((link) => link.addEventListener('click',() => toggleMenu(false)));
  document.querySelectorAll('[data-sound="insight"]').forEach((button) => button.addEventListener('click',() => playTone('insight')));

  prefersDark.addEventListener?.('change',() => { if (themePreference === 'system') applyTheme('system'); });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('in-view');
      entry.target.closest('.section,.hero,.section-wrap')?.classList.add('in-view');
      observer.unobserve(entry.target);
    });
  },{threshold:.14,rootMargin:'0px 0px -7% 0px'});
  document.querySelectorAll('.reveal,.pulse-chart-card').forEach((element) => observer.observe(element));

  window.addEventListener('scroll',() => header?.classList.toggle('scrolled',window.scrollY>18),{passive:true});

  if (!prefersReducedMotion.matches && window.matchMedia('(pointer:fine)').matches) {
    let targetX=window.innerWidth/2,targetY=window.innerHeight/2,currentX=targetX,currentY=targetY;
    window.addEventListener('pointermove',(event) => { targetX=event.clientX; targetY=event.clientY; },{passive:true});
    const follow = () => {
      currentX += (targetX-currentX)*.065;
      currentY += (targetY-currentY)*.065;
      root.style.setProperty('--px',`${currentX}px`);
      root.style.setProperty('--py',`${currentY}px`);
      requestAnimationFrame(follow);
    };
    requestAnimationFrame(follow);
  }

  applyTheme(themePreference);
  updateSoundUI();
  applyLanguage(currentLanguage);
})();
