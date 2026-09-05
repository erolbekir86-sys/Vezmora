(() => {
  const PHOTO_SRC = '/static/vexmera-founder.jpg?v=20260905-2';

  function installFounderPhoto() {
    const current = document.querySelector('.founder-portrait');
    if (!current || current.tagName === 'IMG') return Boolean(current);

    const image = document.createElement('img');
    image.className = current.className;
    image.src = PHOTO_SRC;
    image.alt = 'Erol Bekir, grundare av Vexmera';
    image.width = 300;
    image.height = 375;
    image.loading = 'lazy';
    image.decoding = 'async';
    image.style.display = 'block';
    image.style.objectFit = 'cover';
    image.style.objectPosition = 'center 39%';
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
    window.setTimeout(() => observer.disconnect(), 15000);
  }
})();
