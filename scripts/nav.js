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
      if (navMenu.classList.contains('is-active')) closeMenu();
      else openMenu();
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
      </div>`;
    originalFocusParagraph.replaceWith(callout);
  }

  function shuffled(items) {
    const copy = items.slice();
    for (let i = copy.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      const tmp = copy[i]; copy[i] = copy[j]; copy[j] = tmp;
    }
    return copy;
  }

  function rotatingAssistantChipsHtml() {
    const people = [
      { query: 'Dominik Hagmann', label: 'Dominik Hagmann' },
      { query: 'Franziska Reiner', label: 'Franziska Reiner' },
      { query: 'Sabine Ladstätter', label: 'Sabine Ladstätter' },
      { query: 'Michaela Binder', label: 'Michaela Binder' },
      { query: 'Magdalena Srienc', label: 'Magdalena Srienc' },
      { query: 'Hans Winkler', label: 'Hans Winkler' }
    ];
    const topics = [
      { query: 'Hemmaberg', label: 'Hemmaberg', icon: 'fa-location-dot' },
      { query: 'Globasnitz', label: 'Globasnitz', icon: 'fa-location-dot' },
      { query: 'Jaunstein', label: 'Jaunstein', icon: 'fa-location-dot' },
      { query: 'Sankt Stefan', label: 'Sankt Stefan', icon: 'fa-location-dot' },
      { query: 'photos Hemmaberg', label: 'Photographs', icon: 'fa-image' },
      { query: 'plans Hemmaberg', label: 'Excavation plans', icon: 'fa-map' },
      { query: 'GeoPackage', label: 'GeoPackages', icon: 'fa-database' },
      { query: 'publications Hemmaberg', label: 'Publications', icon: 'fa-book' }
    ];
    const peopleCount = Math.random() < 0.5 ? 1 : 2;
    const topicCount = Math.random() < 0.5 ? 2 : 3;
    const personChips = shuffled(people).slice(0, peopleCount).map(function (item) {
      return `<button type="button" class="chat-chip" data-query="${item.query}"><i class="fa-solid fa-user"></i> ${item.label}</button>`;
    });
    const topicChips = shuffled(topics).slice(0, topicCount).map(function (item) {
      return `<button type="button" class="chat-chip" data-query="${item.query}"><i class="fa-solid ${item.icon}"></i> ${item.label}</button>`;
    });
    return personChips.concat(topicChips).join('') +
      '<button type="button" class="chat-chip chat-chip-byoai" data-query="__byoai"><i class="fa-solid fa-microchip"></i> BYOAI / Remote MCP</button>';
  }

  function bindRotatingAssistantChips(container) {
    if (!container) return;
    container.querySelectorAll('.chat-chip').forEach(function (button) {
      button.addEventListener('click', function () {
        const query = button.dataset.query || '';
        if (query === '__byoai') {
          const byoaiLink = document.querySelector('#iuenna-chat-window .chat-header-byoai-badge');
          if (byoaiLink && byoaiLink.href) window.location.href = byoaiLink.href;
          return;
        }
        const input = document.getElementById('chat-input-field');
        const send = document.getElementById('chat-send-btn');
        if (!input || !send) return;
        input.value = query;
        send.click();
      });
    });
  }

  function rotateAssistantWelcomeChips(root) {
    const scope = root || document;
    scope.querySelectorAll('#iuenna-chat-window .chat-msg.bot .chat-msg-bubble').forEach(function (bubble) {
      if (bubble.dataset.rotatingSuggestions === '1') return;
      const firstStrong = bubble.querySelector('p strong');
      if (!firstStrong || firstStrong.textContent.trim() !== 'Ask IUENNA') return;
      const container = bubble.querySelector('.chat-chips-container');
      if (!container) return;
      container.innerHTML = rotatingAssistantChipsHtml();
      bindRotatingAssistantChips(container);
      bubble.dataset.rotatingSuggestions = '1';
    });
  }

  function metadataRows(card) {
    const rows = {};
    if (!card) return rows;
    card.querySelectorAll('div > strong').forEach(function (strong) {
      const label = strong.textContent.replace(/:$/, '').trim();
      const parent = strong.parentElement;
      if (!label || !parent) return;
      const clone = parent.cloneNode(true);
      const clonedStrong = clone.querySelector('strong');
      if (clonedStrong) clonedStrong.remove();
      rows[label] = clone.textContent.trim();
    });
    return rows;
  }

  function addGroundedAssistantSummary(bubble) {
    if (!bubble || bubble.dataset.groundedSummary === '1') return;
    const heading = bubble.querySelector('p strong');
    if (!heading) return;
    const headingText = heading.textContent.trim();
    if (headingText !== 'Metadata matches' && headingText !== 'Archived-file matches') return;
    const cards = Array.from(bubble.querySelectorAll('article'));
    if (!cards.length) return;
    const firstCard = cards[0];
    const titleEl = firstCard.querySelector(':scope > div');
    const title = titleEl ? titleEl.textContent.trim() : '';
    const rows = metadataRows(firstCard);
    const summary = document.createElement('p');
    summary.className = 'chat-grounded-summary';
    summary.style.cssText = 'margin:0 0 9px 0;font-size:.84rem;line-height:1.5;';
    if (headingText === 'Metadata matches') {
      const details = [];
      if (rows.Type) details.push(rows.Type);
      if (rows.Items) details.push(rows.Items);
      if (rows.Years) details.push(rows.Years);
      const extra = cards.length > 1 ? ` I also found ${cards.length - 1} further ranked match${cards.length > 2 ? 'es' : ''} below.` : '';
      summary.innerHTML = `The closest ARCHE-derived match is <strong>${title || 'the first record shown below'}</strong>${details.length ? ` (${details.join(' · ')})` : ''}.${extra}`;
    } else {
      const details = [];
      if (rows.Type) details.push(rows.Type);
      if (rows.Place) details.push(rows.Place);
      if (rows.Date) details.push(rows.Date);
      const extra = cards.length > 1 ? ` ${cards.length} top matching archived resources are shown below.` : ' The matching archived resource is shown below.';
      summary.innerHTML = `The archived-file search points first to <strong>${title || 'the first resource shown below'}</strong>${details.length ? ` (${details.join(' · ')})` : ''}.${extra}`;
    }
    const firstParagraph = bubble.querySelector('p');
    if (firstParagraph) bubble.insertBefore(summary, firstParagraph);
    else bubble.prepend(summary);
    bubble.dataset.groundedSummary = '1';
  }

  function ensureAssistantContrastStyles() {
    if (document.getElementById('iuenna-assistant-contrast-styles')) return;
    const style = document.createElement('style');
    style.id = 'iuenna-assistant-contrast-styles';
    style.textContent = `
      #iuenna-chat-trigger,
      #iuenna-chat-trigger * {
        color: #FFFFFF !important;
      }

      #iuenna-chat-window .chat-header,
      #iuenna-chat-window .chat-header .chat-header-title,
      #iuenna-chat-window .chat-header .chat-header-sub,
      #iuenna-chat-window .chat-header p,
      #iuenna-chat-window .chat-header strong,
      #iuenna-chat-window .chat-header span,
      #iuenna-chat-window .chat-header i,
      #iuenna-chat-window .chat-header button,
      #iuenna-chat-window .chat-header button i {
        color: #FFFFFF !important;
      }

      #iuenna-chat-window .chat-header-sub {
        color: rgba(255, 255, 255, 0.88) !important;
      }

      #iuenna-chat-window .chat-header-byoai-badge,
      #iuenna-chat-window .chat-header-byoai-badge * {
        color: #FFFFFF !important;
      }

      #iuenna-chat-window .chat-msg.user .chat-msg-bubble,
      #iuenna-chat-window .chat-msg.user .chat-msg-bubble p,
      #iuenna-chat-window .chat-msg.user .chat-msg-bubble strong,
      #iuenna-chat-window .chat-msg.user .chat-msg-bubble span,
      #iuenna-chat-window .chat-msg.user .chat-msg-bubble a,
      #iuenna-chat-window .chat-msg.user .chat-msg-bubble i {
        color: #FFFFFF !important;
      }
    `;
    document.head.appendChild(style);
  }

  function addAssistantMinimizeButton() {
    const win = document.getElementById('iuenna-chat-window');
    if (!win) return;
    const actions = win.querySelector('.chat-header-actions');
    if (!actions || actions.querySelector('#chat-minimize-btn')) return;
    const button = document.createElement('button');
    button.id = 'chat-minimize-btn';
    button.type = 'button';
    button.className = 'chat-header-action-btn';
    button.setAttribute('aria-label', 'Minimize Ask IUENNA');
    button.title = 'Minimize';
    button.style.cssText = 'background:none;border:none;color:rgba(255,255,255,.78);cursor:pointer;padding:4px 6px;font-size:.85rem;';
    button.innerHTML = '<i class="fa-solid fa-minus"></i>';
    button.addEventListener('click', function () {
      win.classList.remove('chat-open');
      try { sessionStorage.setItem('iuenna_chat_open', 'false'); } catch (_) {}
      const trigger = document.getElementById('iuenna-chat-trigger');
      if (trigger) trigger.focus();
    });
    const close = actions.querySelector('#chat-close-btn');
    if (close) actions.insertBefore(button, close);
    else actions.appendChild(button);
  }

  function enhanceAssistant(root) {
    ensureAssistantContrastStyles();
    addAssistantMinimizeButton();
    rotateAssistantWelcomeChips(root);
    const scope = root || document;
    scope.querySelectorAll('#iuenna-chat-window .chat-msg.bot .chat-msg-bubble').forEach(addGroundedAssistantSummary);
  }

  function initAssistantEnhancements() {
    enhanceAssistant(document);
    const observer = new MutationObserver(function (mutations) {
      let assistantTouched = false;
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (!(node instanceof Element)) return;
          if (node.id === 'iuenna-chat-window' || node.closest('#iuenna-chat-window') || node.querySelector('#iuenna-chat-window')) assistantTouched = true;
        });
      });
      if (assistantTouched) enhanceAssistant(document);
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  function init() {
    initNav();
    ensureRepositoryFooterLink();
    enhanceProjectOverview();
    initAssistantEnhancements();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
