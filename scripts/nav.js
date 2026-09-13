(function () {
  'use strict';

  function loadScript(src, onload) {
    const script = document.createElement('script');
    script.src = src;
    script.defer = true;
    if (onload) script.addEventListener('load', onload, { once: true });
    document.head.appendChild(script);
  }

  loadScript('/scripts/nav-base.js?v=2.5.0', function () {
    loadScript('/scripts/project-ui.js?v=2.6.0');
  });
})();