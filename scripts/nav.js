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

  function ensureRepositoryFooterLink() {
    const repositoryUrl = 'https://github.com/IUENNA/IUENNA.github.io';

    document.querySelectorAll('footer').forEach(function (footer) {
      if (footer.querySelector('a[href="' + repositoryUrl + '"]')) return;

      const projectLink = Array.from(footer.querySelectorAll('a')).find(function (link) {
        return link.textContent.trim() === 'IUENNA Project';
      });

      if (!projectLink) return;

      const repositoryLink = document.createElement('a');
      repositoryLink.href = repositoryUrl;
      repositoryLink.target = '_blank';
      repositoryLink.rel = 'noopener noreferrer';
      repositoryLink.textContent = 'GitHub Repository';

      projectLink.insertAdjacentText('afterend', ' | ');
      projectLink.nextSibling.after(repositoryLink);
    });
  }

  function enhanceProjectOverview() {
    const overviewHeading = Array.from(document.querySelectorAll('.card h2')).find(function (heading) {
      return heading.textContent.trim() === 'Project Overview';
    });

    if (!overviewHeading) return;

    const overviewCard = overviewHeading.closest('.card');
    if (!overviewCard || overviewCard.querySelector('.project-focus-callout')) return;

    const paragraphs = overviewCard.querySelectorAll(':scope > p');
    if (paragraphs.length < 2) return;

    const originalFocusParagraph = paragraphs[1];
    const callout = document.createElement('div');
    callout.className = 'project-focus-callout';
    callout.setAttribute('aria-label', 'Project focus and funding');
    callout.style.cssText = [
      'margin-top: 1.65rem',
      'padding: 1.35rem 1.4rem',
      'border: 1px solid rgba(168, 68, 46, 0.22)',
      'border-left: 4px solid var(--primary)',
      'border-radius: var(--radius-md)',
      'background: linear-gradient(135deg, rgba(168, 68, 46, 0.085), rgba(184, 142, 62, 0.045))',
      'box-shadow: var(--shadow-sm)'
    ].join(';');

    callout.innerHTML = `
      <div style="display:grid;grid-template-columns:1.6rem minmax(0,1fr);gap:0.9rem;align-items:start;">
        <i class="fa-solid fa-location-dot" aria-hidden="true" style="color:var(--primary);font-size:1.25rem;line-height:1.5;"></i>
        <p style="margin:0;color:var(--text-dark);font-size:1.04rem;line-height:1.65;">
          At the heart of IUENNA was the archaeological micro-region of the
          <strong style="color:var(--primary);font-weight:800;">Jauntal/Podjuna Valley</strong>
          in Carinthia, Austria.
        </p>
      </div>
      <div style="display:grid;grid-template-columns:1.6rem minmax(0,1fr);gap:0.9rem;align-items:start;margin-top:1rem;padding-top:1rem;border-top:1px solid rgba(168, 68, 46, 0.18);">
        <i class="fa-solid fa-landmark" aria-hidden="true" style="color:var(--primary);font-size:1.1rem;line-height:1.6;"></i>
        <div>
          <div style="margin-bottom:0.25rem;color:var(--text-muted);font-size:0.76rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;">Funded by</div>
          <div style="color:var(--primary);font-weight:800;line-height:1.45;">Austrian Academy of Sciences (ÖAW)</div>
          <a href="https://www.oeaw.ac.at/foerderungen/godigital/godigital-30" target="_blank" rel="noopener noreferrer" style="display:inline-block;margin-top:0.15rem;color:var(--primary);font-weight:800;text-decoration:none;line-height:1.45;">
            Go!Digital 3.0 programme <i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true" style="font-size:0.72em;margin-left:0.2rem;"></i>
          </a>
        </div>
      </div>
    `;

    originalFocusParagraph.replaceWith(callout);
  }

  function init() {
    initNav();
    ensureRepositoryFooterLink();
    enhanceProjectOverview();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
