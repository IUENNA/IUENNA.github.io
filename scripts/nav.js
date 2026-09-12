/**
 * IUENNA Navigation & Burger Menu
 *
 * The burger control is intentionally used at every viewport width so the
 * header remains compact and consistent across all public IUENNA pages.
 */
(function () {
  'use strict';

  function initNav() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');

    if (!navToggle || !navMenu) return;

    function openMenu() {
      navToggle.classList.add('is-active');
      navMenu.classList.add('is-active');
      navToggle.setAttribute('aria-expanded', 'true');
      const icon = navToggle.querySelector('i');
      if (icon) {
        icon.classList.remove('fa-bars');
        icon.classList.add('fa-xmark');
      }
    }

    function closeMenu() {
      navToggle.classList.remove('is-active');
      navMenu.classList.remove('is-active');
      navToggle.setAttribute('aria-expanded', 'false');
      const icon = navToggle.querySelector('i');
      if (icon) {
        icon.classList.remove('fa-xmark');
        icon.classList.add('fa-bars');
      }
    }

    navToggle.addEventListener('click', function (event) {
      event.stopPropagation();
      if (navMenu.classList.contains('is-active')) {
        closeMenu();
      } else {
        openMenu();
      }
    });

    navMenu.querySelectorAll('.nav-link').forEach(function (link) {
      link.addEventListener('click', closeMenu);
    });

    document.addEventListener('click', function (event) {
      if (!navMenu.classList.contains('is-active')) return;
      const header = document.querySelector('.nav-header');
      if (header && !header.contains(event.target)) closeMenu();
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && navMenu.classList.contains('is-active')) {
        closeMenu();
        navToggle.focus();
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNav);
  } else {
    initNav();
  }
})();
