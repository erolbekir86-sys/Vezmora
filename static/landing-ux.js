(() => {
  const SVG = (body) => `<svg class="ux-icon" viewBox="0 0 24 24" aria-hidden="true">${body}</svg>`;
  const icons = {
    home: SVG('<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>'),
    growth: SVG('<path d="M4 18V6"/><path d="M4 18h16"/><path d="m7 14 4-4 3 2 5-6"/><path d="M16 6h3v3"/>'),
    spark: SVG('<path d="M12 3l1.35 4.15L17.5 8.5l-4.15 1.35L12 14l-1.35-4.15L6.5 8.5l4.15-1.35L12 3Z"/><path d="M18.5 14.5l.75 2.25 2.25.75-2.25.75-.75 2.25-.75-2.25-2.25-.75 2.25-.75.75-2.25Z"/>'),
    shield: SVG('<path d="M12 3 20 6v5c0 5-3.4 8.6-8 10-4.6-1.4-8-5-8-10V6l8-3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/>'),
    layers: SVG('<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 16 9 5 9-5"/>'),
    arrow: SVG('<path d="M4 12h15"/><path d="m14 7 5 5-5 5"/>'),
    target: SVG('<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 4V2M20 12h2M12 20v2M4 12H2"/>'),
    core: SVG('<path d="m12 3 7 9-7 9-7-9 7-9Z"/><path d="M9.5 12h5"/><path d="M12 9.5v5"/>'),
    pulse: SVG('<path d="M3 12h4l2-5 4 10 2-5h6"/>'),
    launch: SVG('<path d="M14 5c2.4-1.4 4.7-1.8 6.5-1.5.3 1.8-.1 4.1-1.5 6.5l-5.5 5.5-5-5L14 5Z"/><path d="m9 15-3 1-2 4 4-2 1-3Z"/><circle cx="16.5" cy="7.5" r="1.5"/>'),
    autopilot: SVG('<path d="M4 15a8 8 0 1 1 16 0"/><path d="m12 15 4-5"/><circle cx="12" cy="15" r="1.5"/><path d="M6 19h12"/>'),
    settings: SVG('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.83 2.83-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1.03 1.56V21h-4v-.08A1.7 1.7 0 0 0 9 19.37a1.7 1.7 0 0 0-1.88.34l-.06.06-2.83-2.83.06-.06A1.7 1.7 0 0 0 4.63 15 1.7 1.7 0 0 0 3.08 14H3v-4h.08A1.7 1.7 0 0 0 4.63 9a1.7 1.7 0 0 0-.34-1.88l-.06-.06 2.83-2.83.06.06A1.7 1.7 0 0 0 9 4.63 1.7 1.7 0 0 0 10 3.08V3h4v.08A1.7 1.7 0 0 0 15 4.63a1.7 1.7 0 0 0 1.88-.34l.06-.06 2.83 2.83-.06.06A1.7 1.7 0 0 0 19.37 9 1.7 1.7 0 0 0 20.92 10H21v4h-.08A1.7 1.7 0 0 0 19.4 15Z"/>'),
    users: SVG('<circle cx="9" cy="8" r="3"/><path d="M3.5 19c.5-3.2 2.4-5 5.5-5s5 1.8 5.5 5"/><path d="M15 6.2a3 3 0 0 1 0 5.6"/><path d="M16 14.5c2.5.5 4 2 4.5 4.5"/>'),
    link: SVG('<path d="M10 13a4 4 0 0 0 5.7 0l2.3-2.3A4 4 0 1 0 12.3 5L11 6.3"/><path d="M14 11a4 4 0 0 0-5.7 0L6 13.3A4 4 0 0 0 11.7 19l1.3-1.3"/>'),
    chart: SVG('<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M22 20H2"/>'),
    check: SVG('<circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/>'),
    speaker: SVG('<path d="M4 10v4h4l5 4V6l-5 4H4Z"/><path d="M16 9a4 4 0 0 1 0 6"/><path d="M18.5 6.5a8 8 0 0 1 0 11"/>'),
    speakerOff: SVG('<path d="M4 10v4h4l5 4V6l-5 4H4Z"/><path d="m17 10 4 4M21 10l-4 4"/>'),
    ads: SVG('<circle cx="11" cy="12" r="7"/><path d="m16 7 5-3-3 5"/><path d="m14.5 9.5 4-4"/>'),
    analytics: SVG('<path d="M4 19V9M10 19V5M16 19v-7M22 19H2"/>'),
    network: SVG('<circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="7" r="2.5"/><circle cx="18" cy="17" r="2.5"/><path d="m8.3 11 7.3-3M8.3 13l7.3 3"/>'),
    briefcase: SVG('<rect x="3" y="7" width="18" height="12" rx="2"/><path d="M8 7V5h8v2M3 12h18"/>'),
    play: SVG('<rect x="4" y="3" width="16" height="18" rx="4"/><path d="m10 9 6 3-6 3V9Z"/>'),
    bag: SVG('<path d="M5 8h14l-1 13H6L5 8Z"/><path d="M9 9V6a3 3 0 0 1 6 0v3"/>')
  };

  function setIcon(element, name) {
    if (!element || !icons[name]) return;
    element.innerHTML = icons[name];
  }

  function enhanceIcons() {
    document.querySelectorAll('.trust-icon').forEach((el, i) => setIcon(el, ['growth','spark','shield'][i] || 'check'));
    document.querySelectorAll('.value-card .icon-box').forEach((el, i) => setIcon(el, ['layers','arrow','target'][i] || 'spark'));

    document.querySelectorAll('.dash-nav').forEach((nav) => {
      const text = (nav.textContent || '').trim().toLowerCase();
      let name = 'home';
      if (text.includes('core')) name = 'core';
      else if (text.includes('pulse')) name = 'pulse';
      else if (text.includes('launch')) name = 'launch';
      else if (text.includes('autopilot')) name = 'autopilot';
      else if (text.includes('inställ') || text.includes('setting')) name = 'settings';
      else if (text.includes('konkurrent') || text.includes('competitor')) name = 'users';
      else if (text.includes('anslut') || text.includes('connection')) name = 'link';
      else if (text.includes('insikt') || text.includes('insight')) name = 'chart';
      else if (text.includes('godkänn') || text.includes('approval')) name = 'check';
      const old = nav.querySelector('b');
      if (old) old.outerHTML = icons[name];
      else if (!nav.querySelector('.ux-icon')) nav.insertAdjacentHTML('afterbegin', icons[name]);
    });

    document.querySelectorAll('.module-card').forEach((card) => {
      const letter = card.querySelector('.module-letter');
      if (!letter) return;
      const text = (card.textContent || '').toLowerCase();
      const name = text.includes('pulse') ? 'pulse' : text.includes('launch') ? 'launch' : text.includes('autopilot') ? 'autopilot' : 'core';
      letter.classList.add('ux-symbol');
      setIcon(letter, name);
    });

    document.querySelectorAll('.integration-card').forEach((card) => {
      const logo = card.querySelector('.source-logo');
      if (!logo) return;
      const text = (card.textContent || '').toLowerCase();
      let name = 'link';
      if (text.includes('google ads')) name = 'ads';
      else if (text.includes('meta')) name = 'network';
      else if (text.includes('analytics')) name = 'analytics';
      else if (text.includes('linkedin')) name = 'briefcase';
      else if (text.includes('tiktok')) name = 'play';
      else if (text.includes('shopify')) name = 'bag';
      logo.classList.add('ux-source');
      setIcon(logo, name);
    });
  }

  function installHoverFlow() {
    if (!window.matchMedia('(hover:hover) and (pointer:fine)').matches || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const selector = '.trust-strip article,.value-card,.step,.module-card,.integration-card,.outcome-grid article,.plan-card';
    document.querySelectorAll(selector).forEach((el) => {
      if (el.dataset.uxHover === '1') return;
      el.dataset.uxHover = '1';
      el.classList.add('ux-hover');
      el.addEventListener('pointermove', (event) => {
        const rect = el.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width - .5) * 3.2;
        const y = ((event.clientY - rect.top) / rect.height - .5) * 2.6;
        el.style.setProperty('--ux-x', `${x.toFixed(2)}px`);
        el.style.setProperty('--ux-y', `${y.toFixed(2)}px`);
      }, {passive:true});
      el.addEventListener('pointerleave', () => {
        el.style.setProperty('--ux-x', '0px');
        el.style.setProperty('--ux-y', '0px');
      }, {passive:true});
    });
  }

  let audioContext = null;
  let soundEnabled = localStorage.getItem('vexmera-sound') !== 'off';

  function audio() {
    audioContext ||= new (window.AudioContext || window.webkitAudioContext)();
    if (audioContext.state === 'suspended') audioContext.resume();
    return audioContext;
  }

  function tone(kind = 'click') {
    if (!soundEnabled) return;
    try {
      const ctx = audio();
      const now = ctx.currentTime;
      const master = ctx.createGain();
      master.gain.setValueAtTime(.0001, now);
      master.gain.exponentialRampToValueAtTime(kind === 'enable' ? .028 : .018, now + .008);
      master.gain.exponentialRampToValueAtTime(.0001, now + (kind === 'enable' ? .18 : .09));
      master.connect(ctx.destination);
      const notes = kind === 'enable' ? [520, 680] : kind === 'insight' ? [620, 830] : [720];
      notes.forEach((frequency, index) => {
        const oscillator = ctx.createOscillator();
        const gain = ctx.createGain();
        oscillator.type = index ? 'sine' : 'triangle';
        oscillator.frequency.setValueAtTime(frequency, now + index * .035);
        gain.gain.setValueAtTime(.0001, now + index * .035);
        gain.gain.exponentialRampToValueAtTime(.42 / notes.length, now + .012 + index * .035);
        gain.gain.exponentialRampToValueAtTime(.0001, now + .075 + index * .045);
        oscillator.connect(gain); gain.connect(master);
        oscillator.start(now + index * .035);
        oscillator.stop(now + .14 + index * .04);
      });
    } catch (_) {}
  }

  function updateSoundControl() {
    const button = document.getElementById('soundToggle');
    if (!button) return;
    button.classList.toggle('enabled', soundEnabled);
    button.setAttribute('aria-label', soundEnabled ? 'Ljud på' : 'Ljud av');
    button.title = soundEnabled ? 'Klickljud på' : 'Klickljud av';
    button.innerHTML = `${soundEnabled ? icons.speaker : icons.speakerOff}<i aria-hidden="true"></i>`;
  }

  function installSound() {
    const button = document.getElementById('soundToggle');
    if (button && button.dataset.uxSound !== '1') {
      button.dataset.uxSound = '1';
      updateSoundControl();
      button.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopImmediatePropagation();
        soundEnabled = !soundEnabled;
        localStorage.setItem('vexmera-sound', soundEnabled ? 'on' : 'off');
        updateSoundControl();
        if (soundEnabled) tone('enable');
      }, true);
    }

    if (document.documentElement.dataset.uxClickSound !== '1') {
      document.documentElement.dataset.uxClickSound = '1';
      document.addEventListener('click', (event) => {
        const control = event.target.closest('a,button,[role="button"],.faq-question');
        if (!control || control.id === 'soundToggle' || control.hasAttribute('disabled')) return;
        tone(control.matches('[data-sound="insight"],.mini-action') ? 'insight' : 'click');
      }, false);
    }
  }

  function ensureFounderPhoto() {
    const current = document.querySelector('.founder-portrait');
    if (!current) return false;
    if (current.tagName === 'IMG') {
      current.loading = 'eager';
      current.fetchPriority = 'high';
      current.classList.add(current.complete && current.naturalWidth ? 'ux-photo-ready' : 'ux-photo-loading');
      current.addEventListener('load', () => current.classList.remove('ux-photo-loading'), {once:true});
      current.addEventListener('load', () => current.classList.add('ux-photo-ready'), {once:true});
      return true;
    }
    const image = document.createElement('img');
    image.className = `${current.className} ux-photo-loading`;
    image.src = '/static/vexmera-founder.jpg?v=20260905-ux3';
    image.alt = document.documentElement.lang === 'en' ? 'Erol Bekir, founder of Vexmera' : 'Erol Bekir, grundare av Vexmera';
    image.width = 600;
    image.height = 750;
    image.loading = 'eager';
    image.decoding = 'async';
    image.fetchPriority = 'high';
    image.addEventListener('load', () => {
      image.classList.remove('ux-photo-loading');
      image.classList.add('ux-photo-ready');
    }, {once:true});
    image.addEventListener('error', () => {
      image.classList.remove('ux-photo-loading');
      image.style.backgroundImage = "url('/static/vexmera-founder.jpg?v=20260905-ux3')";
      image.style.backgroundSize = 'cover';
      image.style.backgroundPosition = 'center 38%';
    }, {once:true});
    current.replaceWith(image);
    return true;
  }

  function runEnhancements() {
    enhanceIcons();
    installHoverFlow();
    installSound();
    ensureFounderPhoto();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', runEnhancements, {once:true});
  else runEnhancements();

  const observer = new MutationObserver(() => runEnhancements());
  observer.observe(document.documentElement, {childList:true, subtree:true});
  window.setTimeout(() => observer.disconnect(), 12000);
})();