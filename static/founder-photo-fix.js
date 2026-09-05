(() => {
  const PHOTO_SRC = '/static/vexmera-founder.jpg?v=20260905-5';

  function installFounderPhoto() {
    const current = document.querySelector('.founder-portrait');
    if (!current) return false;

    if (current.tagName === 'IMG') {
      if (!current.src.includes('20260905-5')) current.src = PHOTO_SRC;
      current.loading = 'eager';
      current.decoding = 'async';
      current.fetchPriority = 'high';
      return true;
    }

    const image = document.createElement('img');
    image.className = current.className;
    image.src = PHOTO_SRC;
    image.alt = 'Erol Bekir, grundare av Vexmera';
    image.width = 300;
    image.height = 375;
    image.loading = 'eager';
    image.decoding = 'async';
    image.fetchPriority = 'high';
    image.style.display = 'block';
    image.style.objectFit = 'cover';
    image.style.objectPosition = 'center 38%';
    image.style.aspectRatio = '4 / 5';
    image.style.minHeight = '0';
    image.style.background = 'var(--paper-2, #f2efe8)';

    current.replaceWith(image);
    return true;
  }

  if (!installFounderPhoto()) {
    const observer = new MutationObserver(() => {
      if (installFounderPhoto()) observer.disconnect();
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
    window.setTimeout(() => observer.disconnect(), 20000);
  }
})();
