(() => {
  'use strict';

  const byId = (id) => document.getElementById(id);

  function setLiveRegions() {
    ['authError', 'onboardingError'].forEach((id) => {
      const node = byId(id);
      if (!node) return;
      node.setAttribute('role', 'alert');
      node.setAttribute('aria-live', 'assertive');
      node.setAttribute('aria-atomic', 'true');
    });

    ['status', 'profileState', 'inviteResult', 'feedbackState', 'resetState'].forEach((id) => {
      const node = byId(id);
      if (!node) return;
      node.setAttribute('role', 'status');
      node.setAttribute('aria-live', 'polite');
      node.setAttribute('aria-atomic', 'true');
    });
  }

  function installAuthTabSemantics() {
    const loginTab = byId('showLogin');
    const registerTab = byId('showRegister');
    const loginPanel = byId('loginForm');
    const registerPanel = byId('registerForm');
    const tabList = loginTab?.parentElement;
    if (!loginTab || !registerTab || !loginPanel || !registerPanel || !tabList) return;

    tabList.setAttribute('role', 'tablist');
    tabList.setAttribute('aria-label', 'Kontoåtkomst');

    const pairs = [
      [loginTab, loginPanel],
      [registerTab, registerPanel],
    ];
    pairs.forEach(([tab, panel]) => {
      tab.setAttribute('role', 'tab');
      tab.setAttribute('aria-controls', panel.id);
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', tab.id);
    });

    function syncTabs() {
      pairs.forEach(([tab, panel]) => {
        const selected = !panel.classList.contains('hidden');
        tab.setAttribute('aria-selected', selected ? 'true' : 'false');
        tab.setAttribute('tabindex', selected ? '0' : '-1');
        panel.setAttribute('aria-hidden', selected ? 'false' : 'true');
      });
    }

    function selectAdjacent(current, direction) {
      const tabs = [loginTab, registerTab];
      const index = tabs.indexOf(current);
      const next = tabs[(index + direction + tabs.length) % tabs.length];
      next.click();
      next.focus();
    }

    pairs.forEach(([tab]) => {
      tab.addEventListener('click', () => queueMicrotask(syncTabs));
      tab.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowRight') {
          event.preventDefault();
          selectAdjacent(tab, 1);
        } else if (event.key === 'ArrowLeft') {
          event.preventDefault();
          selectAdjacent(tab, -1);
        } else if (event.key === 'Home') {
          event.preventDefault();
          loginTab.click();
          loginTab.focus();
        } else if (event.key === 'End') {
          event.preventDefault();
          registerTab.click();
          registerTab.focus();
        }
      });
    });

    syncTabs();
  }

  function installNavigationSemantics() {
    const nav = byId('appNavigation');
    if (!nav) return;
    const buttons = [...nav.querySelectorAll('button[data-view]')];

    function syncCurrentView() {
      buttons.forEach((button) => {
        if (button.classList.contains('active')) {
          button.setAttribute('aria-current', 'page');
        } else {
          button.removeAttribute('aria-current');
        }
      });
    }

    buttons.forEach((button) => button.addEventListener('click', () => queueMicrotask(syncCurrentView)));
    syncCurrentView();
  }

  function installOnboardingDialogAccessibility() {
    const modal = byId('onboardingModal');
    const card = modal?.querySelector('.modal-card');
    const stepLabel = byId('onboardingStepLabel');
    const progress = byId('onboardingProgress')?.parentElement;
    if (!modal || !card) return;

    modal.setAttribute('aria-describedby', 'onboardingError');
    if (progress) {
      progress.setAttribute('role', 'progressbar');
      progress.setAttribute('aria-valuemin', '1');
      progress.setAttribute('aria-valuemax', '3');
      progress.setAttribute('aria-label', 'Onboardingsteg');
    }

    let previousFocus = null;

    function isOpen() {
      return !modal.classList.contains('hidden');
    }

    function focusables() {
      return [...card.querySelectorAll('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])')]
        .filter((element) => !element.closest('.hidden') && element.offsetParent !== null);
    }

    function updateProgress() {
      if (!progress || !stepLabel) return;
      const match = stepLabel.textContent.match(/(\d+)\s*(?:av|of)\s*3/i);
      if (match) progress.setAttribute('aria-valuenow', match[1]);
    }

    function onVisibilityChange() {
      updateProgress();
      if (isOpen()) {
        previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        queueMicrotask(() => {
          const first = focusables()[0];
          if (first) first.focus();
          else {
            card.setAttribute('tabindex', '-1');
            card.focus();
          }
        });
      } else if (previousFocus?.isConnected) {
        previousFocus.focus();
        previousFocus = null;
      }
    }

    modal.addEventListener('keydown', (event) => {
      if (event.key !== 'Tab' || !isOpen()) return;
      const items = focusables();
      if (!items.length) {
        event.preventDefault();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });

    new MutationObserver(onVisibilityChange).observe(modal, {attributes: true, attributeFilter: ['class']});
    if (stepLabel) {
      new MutationObserver(updateProgress).observe(stepLabel, {childList: true, characterData: true, subtree: true});
    }
    updateProgress();
  }

  setLiveRegions();
  installAuthTabSemantics();
  installNavigationSemantics();
  installOnboardingDialogAccessibility();
})();
