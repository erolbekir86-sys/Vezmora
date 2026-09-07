(() => {
  'use strict';

  const build = window.__VEXMERA_BUILD__ || 'local';
  const href = `/static/landing-premium.css?build=${encodeURIComponent(build)}`;

  if (!document.querySelector('link[data-vexmera-premium]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    link.dataset.vexmeraPremium = 'true';
    document.head.appendChild(link);
  }

  // Final one-shot portrait guard. No observers or animation loops: stability first.
  const portrait = document.querySelector('.founder-portrait');
  if (portrait) {
    const expected = `/static/vexmera-founder.jpg?build=${encodeURIComponent(build)}`;
    if (portrait.tagName === 'IMG') {
      if (!portrait.getAttribute('src') || !portrait.src.includes('vexmera-founder.jpg')) {
        portrait.src = expected;
      }
      portrait.loading = 'eager';
      portrait.decoding = 'async';
      portrait.fetchPriority = 'high';
      portrait.style.display = 'block';
      portrait.style.visibility = 'visible';
      portrait.style.opacity = '1';
    }
  }

  document.documentElement.classList.add('vexmera-premium-ready');
})();
