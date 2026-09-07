(() => {
  'use strict';
  const sections = [['.section-problem','data'],['.product-demo','decision'],['.how-section','how'],['.workflow-section','workflow'],['.security-section','security']];
  function install(){sections.forEach(([selector,art])=>{const section=document.querySelector(selector);if(!section||section.querySelector(':scope > .vex-section-art'))return;section.classList.add('vex-art-section');const layer=document.createElement('div');layer.className='vex-section-art';layer.dataset.vexArt=art;layer.setAttribute('aria-hidden','true');section.prepend(layer);});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
