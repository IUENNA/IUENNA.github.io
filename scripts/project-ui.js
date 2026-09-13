(function () {
  'use strict';

  function normalizeInstitutionLabel(value) {
    if (!value) return value;
    return value
      .replace(/Austrian Center for Digital Humanities and Cultural Heritage/g, 'Austrian Centre for Digital Humanities')
      .replace(/Austrian Centre for Digital Humanities and Cultural Heritage/g, 'Austrian Centre for Digital Humanities')
      .replace(/\bACDH-CH\b/g, 'ACDH')
      .replace(/\bÖAI\b/g, 'OeAI')
      .replace(/\bÖAW\b/g, 'OeAW');
  }

  function normalizeInstitutionNames(root) {
    const scope = root || document.body;
    if (!scope) return;

    if (scope.nodeType === Node.TEXT_NODE) {
      const replacement = normalizeInstitutionLabel(scope.nodeValue);
      if (replacement !== scope.nodeValue) scope.nodeValue = replacement;
      return;
    }

    const walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_ACCEPT;
        if (parent.closest('script, style, code, pre, textarea, noscript, [data-preserve-institution-names]')) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });

    const nodes = [];
    let node;
    while ((node = walker.nextNode())) nodes.push(node);
    nodes.forEach(function (textNode) {
      const replacement = normalizeInstitutionLabel(textNode.nodeValue);
      if (replacement !== textNode.nodeValue) textNode.nodeValue = replacement;
    });
  }

  function compactLeadershipAndAddFunding() {
    const leadershipHeading = Array.from(document.querySelectorAll('.card h2')).find(function (heading) {
      return heading.textContent.trim() === 'Project Leadership';
    });
    if (!leadershipHeading) return;

    const leadershipCard = leadershipHeading.closest('.card');
    if (!leadershipCard) return;

    const intro = leadershipCard.querySelector(':scope > p');
    if (intro) {
      intro.textContent = 'The IUENNA project was jointly coordinated.';
      intro.style.marginBottom = '1rem';
    }

    const profileCards = leadershipCard.querySelectorAll('.profile-card');
    if (profileCards.length >= 2) {
      profileCards.forEach(function (profileCard) {
        profileCard.style.flex = '1 1 auto';
        profileCard.style.minHeight = '0';
        profileCard.style.padding = '1rem 1.1rem';
        profileCard.style.gap = '0.9rem';
      });

      const dominikInfo = profileCards[0].querySelector('.profile-info');
      if (dominikInfo) {
        dominikInfo.innerHTML = '<strong><a href="https://orcid.org/0000-0002-4481-6234" target="_blank" rel="noopener noreferrer">Dominik Hagmann</a></strong>' +
          '<span class="profile-role" style="font-size:0.83rem;line-height:1.35;color:var(--text-muted);">Project Coordinator · Principal Investigator</span>' +
          '<span class="profile-org"><a href="https://landesmuseum.ktn.gv.at" target="_blank" rel="noopener noreferrer">kärnten.museum</a></span>';
      }

      const franziskaInfo = profileCards[1].querySelector('.profile-info');
      if (franziskaInfo) {
        franziskaInfo.innerHTML = '<strong>Franziska Waldhart</strong>' +
          '<span class="profile-role" style="font-size:0.83rem;line-height:1.35;color:var(--text-muted);">Principal Investigator</span>' +
          '<span class="profile-org"><a href="https://www.oeaw.ac.at/oeai" target="_blank" rel="noopener noreferrer">OeAI</a> / <a href="https://www.oeaw.ac.at/" target="_blank" rel="noopener noreferrer">OeAW</a></span>';
      }
    }

    leadershipCard.querySelectorAll('.project-funding-card').forEach(function (card) {
      card.remove();
    });

    const curationSection = document.getElementById('project-curation');
    const curationGrid = curationSection ? curationSection.closest('.grid-container') : null;
    if (curationGrid && !document.getElementById('project-funding')) {
      const fundingWrapper = document.createElement('div');
      fundingWrapper.className = 'grid-container';
      fundingWrapper.style.marginBottom = '3rem';
      fundingWrapper.innerHTML = '<section class="card" id="project-funding" style="grid-column:1 / -1;padding:1.8rem 2rem;border:2px solid rgba(168,68,46,0.42);background:linear-gradient(135deg,rgba(168,68,46,0.13),rgba(184,142,62,0.07));box-shadow:var(--shadow-md);">' +
        '<div style="display:flex;align-items:center;gap:1.25rem;flex-wrap:wrap;">' +
        '<div aria-hidden="true" style="display:flex;align-items:center;justify-content:center;flex:0 0 3.5rem;width:3.5rem;height:3.5rem;border-radius:50%;background:rgba(168,68,46,0.12);color:var(--primary);font-size:1.45rem;"><i class="fa-solid fa-landmark"></i></div>' +
        '<div style="flex:1 1 420px;min-width:0;">' +
        '<h2 style="margin:0 0 0.65rem;color:var(--primary);">Funding</h2>' +
        '<p style="margin:0 0 0.55rem;font-size:1.12rem;line-height:1.55;color:var(--text-dark);">Funded by the <strong style="color:var(--primary);">Austrian Academy of Sciences (OeAW)</strong> through the <a href="https://www.oeaw.ac.at/foerderungen/godigital/godigital-30" target="_blank" rel="noopener noreferrer" style="font-weight:800;color:var(--primary);text-decoration:none;">Go!Digital 3.0 programme <i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true" style="font-size:0.72em;"></i></a>.</p>' +
        '<p style="margin:0;color:var(--text-muted);font-size:0.94rem;line-height:1.55;">Project <strong>GD3.0_2021-24_IUENNA</strong> · Host institutions: <a href="https://landesmuseum.ktn.gv.at" target="_blank" rel="noopener noreferrer"><strong>kärnten.museum</strong></a> and the <a href="https://www.oeaw.ac.at/oeai" target="_blank" rel="noopener noreferrer"><strong>Austrian Archaeological Institute (OeAI)</strong></a> at the <a href="https://www.oeaw.ac.at/" target="_blank" rel="noopener noreferrer"><strong>OeAW</strong></a>.</p>' +
        '</div></div></section>';
      curationGrid.parentNode.insertBefore(fundingWrapper, curationGrid);
    }
  }

  function balanceOverview() {
    const overviewHeading = Array.from(document.querySelectorAll('.card h2')).find(function (heading) {
      return heading.textContent.trim() === 'Project Overview';
    });
    if (!overviewHeading) return;
    const overviewCard = overviewHeading.closest('.card');
    const areaBlock = overviewCard ? overviewCard.querySelector('.area-of-interest-block') : null;
    if (areaBlock) {
      areaBlock.style.marginTop = '2.1rem';
      areaBlock.style.paddingBottom = '0.35rem';
    }
  }

  function init() {
    compactLeadershipAndAddFunding();
    balanceOverview();
    normalizeInstitutionNames(document.body);

    const observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType === Node.TEXT_NODE || node.nodeType === Node.ELEMENT_NODE) normalizeInstitutionNames(node);
        });
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();