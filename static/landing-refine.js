(() => {
  const root = document.documentElement;
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const BUILD = window.__VEXMERA_BUILD__ || 'local';
  const PORTRAIT_SRC = `/static/vexmera-founder.jpg?build=${encodeURIComponent(BUILD)}`;

  const icon = (body) => `<svg class="ux-icon" viewBox="0 0 24 24" aria-hidden="true">${body}</svg>`;
  const themeIcons = {
    light: icon('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
    dark: icon('<path d="M20 15.2A8 8 0 0 1 8.8 4a8.5 8.5 0 1 0 11.2 11.2Z"/>'),
    system: icon('<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>')
  };

  function applyLanguageCleanup() {
    const lang = root.lang === 'en' ? 'en' : 'sv';
    const replacements = {
      sv: {
        'dash.approvalsMeta': 'Att granska',
        'dash.sourcesMeta': 'Aktiv synk'
      },
      en: {
        'dash.approvalsMeta': 'To review',
        'dash.sourcesMeta': 'Active sync'
      }
    }[lang];

    Object.entries(replacements).forEach(([key, value]) => {
      document.querySelectorAll(`[data-i18n="${key}"]`).forEach((el) => {
        if (el.textContent !== value) el.textContent = value;
      });
    });

    const founder = document.querySelector('.founder-meta strong');
    if (founder && founder.textContent !== 'Erol Bekir') founder.textContent = 'Erol Bekir';
  }

  function ensurePortrait() {
    const existing = document.querySelector('.founder-portrait');
    if (!existing) return false;

    let image = existing;
    if (existing.tagName !== 'IMG') {
      image = document.createElement('img');
      image.className = existing.className;
      existing.replaceWith(image);
    }

    const alt = root.lang === 'en' ? 'Erol Bekir, founder of Vexmera' : 'Erol Bekir, grundare av Vexmera';
    if (image.alt !== alt) image.alt = alt;
    image.width = 300;
    image.height = 375;
    image.loading = 'eager';
    image.decoding = 'async';
    image.fetchPriority = 'high';
    image.style.display = 'block';
    image.style.objectFit = 'cover';
    image.style.objectPosition = 'center 38%';
    image.style.aspectRatio = '4 / 5';

    const expectedBuild = `build=${encodeURIComponent(BUILD)}`;
    const currentSrc = image.getAttribute('src') || '';
    if (!currentSrc.includes(expectedBuild) && image.dataset.refineRetried !== '1') image.src = PORTRAIT_SRC;

    if (image.dataset.refinePhotoBound !== '1') {
      image.dataset.refinePhotoBound = '1';
      image.addEventListener('load', () => {
        image.classList.remove('ux-photo-loading');
        image.classList.add('ux-photo-ready');
      });
      image.addEventListener('error', () => {
        if (image.dataset.refineRetried !== '1') {
          image.dataset.refineRetried = '1';
          image.src = `/static/vexmera-founder.jpg?build=${encodeURIComponent(BUILD)}&retry=1`;
          return;
        }
        const fallback = document.createElement('div');
        fallback.className = 'founder-photo-fallback';
        fallback.textContent = root.lang === 'en' ? 'Founder portrait could not be loaded.' : 'Grundarbilden kunde inte laddas.';
        image.replaceWith(fallback);
      });
    }
    return true;
  }

  function installThemeIcon() {
    const button = document.getElementById('themeToggle');
    if (!button) return;
    const preference = localStorage.getItem('vexmera-theme') || 'light';
    const key = ['light','dark','system'].includes(preference) ? preference : 'light';
    const slot = button.querySelector('.theme-icon') || button;
    if (slot.dataset.refineThemeIcon === key) return;
    slot.innerHTML = themeIcons[key];
    slot.dataset.refineThemeIcon = key;
  }

  function installActiveNavigation() {
    const links = [...document.querySelectorAll('.desktop-nav a[href^="#"],.mobile-menu a[href^="#"]')];
    const sections = links
      .map((link) => document.querySelector(link.getAttribute('href')))
      .filter((section, index, all) => section && all.indexOf(section) === index);
    if (!sections.length) return;

    const update = (id) => {
      links.forEach((link) => {
        const active = link.getAttribute('href') === `#${id}`;
        if (active && link.getAttribute('aria-current') !== 'location') link.setAttribute('aria-current','location');
        if (!active && link.hasAttribute('aria-current')) link.removeAttribute('aria-current');
      });
    };

    const observer = new IntersectionObserver((entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a,b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible?.target?.id) update(visible.target.id);
    }, {rootMargin:'-28% 0px -56% 0px', threshold:[.05,.18,.35]});
    sections.forEach((section) => observer.observe(section));
  }

  function installPointerHighlights() {
    if (prefersReducedMotion.matches || !window.matchMedia('(hover:hover) and (pointer:fine)').matches) return;
    const cards = document.querySelectorAll('.value-card,.step,.module-card,.integration-card,.outcome-grid article,.plan-card');
    cards.forEach((card) => {
      if (card.dataset.refinePointer === '1') return;
      card.dataset.refinePointer = '1';
      card.addEventListener('pointermove', (event) => {
        const rect = card.getBoundingClientRect();
        card.style.setProperty('--refine-mx', `${((event.clientX - rect.left) / rect.width * 100).toFixed(1)}%`);
        card.style.setProperty('--refine-my', `${((event.clientY - rect.top) / rect.height * 100).toFixed(1)}%`);
      }, {passive:true});
    });
  }

  function installScrollProgress() {
    const update = () => {
      const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      root.style.setProperty('--page-progress', Math.min(1, Math.max(0, window.scrollY / max)).toFixed(4));
    };
    update();
    window.addEventListener('scroll', update, {passive:true});
    window.addEventListener('resize', update, {passive:true});
  }

  function refresh() {
    applyLanguageCleanup();
    ensurePortrait();
    installThemeIcon();
    installPointerHighlights();
  }

  refresh();
  installActiveNavigation();
  installScrollProgress();

  let refreshQueued = false;
  const queueRefresh = () => {
    if (refreshQueued) return;
    refreshQueued = true;
    window.requestAnimationFrame(() => {
      refreshQueued = false;
      refresh();
    });
  };

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type === 'attributes' && mutation.target === root && (mutation.attributeName === 'lang' || mutation.attributeName === 'data-theme')) {
        queueRefresh();
        return;
      }
      if (mutation.type === 'childList') {
        queueRefresh();
        return;
      }
    }
  });
  observer.observe(document.documentElement, {subtree:true, childList:true, attributes:true, attributeFilter:['lang','data-theme']});
})();
