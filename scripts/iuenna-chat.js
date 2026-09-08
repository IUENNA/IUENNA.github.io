/**
 * iuenna-chat.js
 * --------------
 * Client-side 2-Stage Hybrid AI & Search Assistant for the IUENNA project.
 * 
 * - Stage 1 (Default): Instant client-side search across data/iuenna_kb.json (0 MB download, < 10ms).
 * - Stage 2 (Optional Opt-in): In-browser Small Language Model (SLM) using Transformers.js v3
 *   (SmolLM2-135M-Instruct via WebGPU/WASM) for local narrative synthesis.
 * 
 * 100% Client-Side. No personal data transmission. Zero server cost.
 */

(function() {
  'use strict';

  // Configuration
  const KB_URL = 'data/iuenna_kb.json';
  const SLM_MODEL_ID = 'onnx-community/Qwen2.5-0.5B-Instruct';
  
  let kbData = null;
  let slmPipeline = null;
  let isSlmLoading = false;
  let isSlmActive = false;

  // Sound/Vibration feedback helper (optional, subtle)
  function triggerHaptic() {
    if (navigator.vibrate) navigator.vibrate(10);
  }

  // 1. Build and Inject DOM elements
  function injectChatUI() {
    // Check if already injected
    if (document.getElementById('iuenna-chat-trigger')) return;

    // Trigger button
    const triggerBtn = document.createElement('button');
    triggerBtn.id = 'iuenna-chat-trigger';
    triggerBtn.setAttribute('aria-label', 'IUENNA Assistent öffnen');
    triggerBtn.innerHTML = `
      <span class="chat-trigger-icon">🏺</span>
      <span>Frag IUENNA</span>
      <span class="chat-trigger-badge">Assistent</span>
    `;
    document.body.appendChild(triggerBtn);

    // Chat Window
    const chatWindow = document.createElement('div');
    chatWindow.id = 'iuenna-chat-window';
    chatWindow.innerHTML = `
      <!-- Header -->
      <div class="chat-header">
        <div class="chat-header-info">
          <div class="chat-header-avatar">🏺</div>
          <div>
            <h3 class="chat-header-title">IUENNA Assistent</h3>
            <p class="chat-header-sub">Forschungs- &amp; Sammlungs-Explorer</p>
          </div>
        </div>
        <div class="chat-header-actions">
          <button class="chat-close-btn" id="chat-close-btn" aria-label="Schließen" title="Schließen (ESC)">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
      </div>

      <!-- Mode & Status Bar -->
      <div class="chat-mode-bar" style="background-color: var(--bg-card); padding: 8px 16px; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
        <span style="font-size: 0.78rem; color: var(--primary); font-weight: 700; display: flex; align-items: center; gap: 6px;">
          <i class="fa-solid fa-bolt" style="color: var(--secondary);"></i> Schnelle Fachauskunft
        </span>
        <span style="font-size: 0.70rem; color: var(--text-muted); display: flex; align-items: center; gap: 4px;">
          <i class="fa-solid fa-triangle-exclamation" style="color: #b88e3e; font-size: 0.72rem;"></i> Automatisiert • System kann Fehler machen
        </span>
      </div>

      <!-- Messages Area -->
      <div class="chat-messages" id="chat-messages">
        <!-- Welcome Message -->
        <div class="chat-msg bot">
          <div class="chat-msg-bubble">
            <p><strong>Willkommen beim IUENNA Sammlungs-Assistenten!</strong> 🏺</p>
            <p style="margin-top: 6px; font-size: 0.84rem;">
              Ich helfe Ihnen beim Erkunden der über <strong>20.000 archäologischen Objekte</strong>, Grabungspläne und Fotos aus dem Jauntal in <em>ARCHE</em>.
            </p>
            <p style="margin-top: 6px; font-size: 0.8rem; color: var(--text-muted);">
              Wählen Sie ein Thema oder stellen Sie eine freie Frage (z. B. nach Fundorten oder Personen wie <em>Franz Glaser</em>):
            </p>
            <div class="chat-chips-container">
              <button class="chat-chip" data-query="Wer ist Franz Glaser?">👤 Franz Glaser</button>
              <button class="chat-chip" data-query="Ist Globasnitz wirklich die römische Straßenstation Iuenna?">🏛️ Tscherberg vs. Globasnitz</button>
              <button class="chat-chip" data-query="Was ist die Villenanlage von St. Stefan?">🏡 Villenanlage St. Stefan</button>
              <button class="chat-chip" data-query="Warum gibt es auf dem Hemmaberg Doppelkirchen?">⛪ Hemmaberg Doppelkirchen</button>
              <button class="chat-chip" data-query="Wie viele Gräber wurden im Gräberfeld von Globasnitz ausgegraben?">💀 Gräberfeld Globasnitz (440 Gräber)</button>
              <button class="chat-chip" data-query="Wer ist Marianne Pollak?">👤 Marianne Pollak</button>
              <button class="chat-chip" data-query="Wer war L. Barbius Vercaius?">📜 Wer war L. Barbius Vercaius?</button>
              <button class="chat-chip" data-query="Welche Rolle spielten die historischen Skizzen von Hans Winkler?">🎨 Hans Winkler Skizzen</button>
              <button class="chat-chip" data-query="Wie kann ich die Geodaten des Projekts direkt in QGIS nutzen?">🗺️ QGIS GeoPackage (.gpkg)</button>
            </div>
          </div>
          <span class="chat-msg-time">Jetzt</span>
        </div>
      </div>

      <!-- Input Area -->
      <div class="chat-input-area">
        <div class="chat-input-row">
          <input type="text" id="chat-input-field" class="chat-input-field" placeholder="Frage stellen (z.B. 'Wer ist Franz Glaser?', 'Pläne Hemmaberg')..." autocomplete="off">
          <button id="chat-send-btn" class="chat-send-btn" aria-label="Senden" title="Senden">
            <i class="fa-solid fa-paper-plane"></i>
          </button>
        </div>
        <div class="chat-privacy-footer" style="padding: 6px 14px; text-align: center; border-top: 1px solid var(--border-color); background: var(--bg-card); display: flex; flex-direction: column; gap: 2px;">
          <span style="font-size: 0.67rem; color: var(--text-muted); line-height: 1.35;">
            <i class="fa-solid fa-circle-exclamation" style="color: #b88e3e;"></i> <strong>Hinweis:</strong> Dies ist ein automatisierter Recherche-Assistent. Antworten können Fehler enthalten – bitte bei wissenschaftlicher Nutzung Primärquellen in ARCHE &amp; Fachliteratur konsultieren.
          </span>
          <span style="font-size: 0.63rem; color: #2e7d32; margin-top: 2px;">
            <i class="fa-solid fa-shield-halved"></i> 100% Client-Side In-Browser • Keine Datenübertragung an Dritte
          </span>
        </div>
      </div>
    `;
    document.body.appendChild(chatWindow);

    bindEvents();
  }

  // 2. Load Knowledge Base
  async function loadKnowledgeBase() {
    try {
      const response = await fetch(KB_URL);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      kbData = await response.json();
      console.log('✓ IUENNA Knowledge Base loaded successfully:', kbData.meta);
    } catch (err) {
      console.warn('Could not load IUENNA Knowledge Base from file, using fallback data:', err);
    }
  }

  // German Stopwords to prevent generic words like 'was', 'ist', 'der' from skewing results
  const GERMAN_STOPWORDS = new Set([
    'was', 'ist', 'sind', 'war', 'waren', 'hat', 'hatte', 'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einer', 'einem',
    'eines', 'einen', 'und', 'oder', 'in', 'im', 'zu', 'zum', 'zur', 'von', 'vom', 'mit', 'auf',
    'für', 'wo', 'wie', 'wer', 'welche', 'welcher', 'welches', 'gibt', 'es', 'kann', 'man',
    'finde', 'ich', 'zeig', 'mir', 'bitte', 'über', 'nach', 'an', 'bei'
  ]);

  // 3. Stage 1: Fast Token-based Relevance Matcher
  function searchKnowledgeBase(query) {
    if (!kbData) return null;

    const cleanQuery = query.toLowerCase().trim();
    const rawTokens = cleanQuery.split(/[\s,;.?!]+/).filter(t => t.length > 1);
    
    // Filter stopwords, but keep them if the query consisted ONLY of stopwords
    const contentTokens = rawTokens.filter(t => !GERMAN_STOPWORDS.has(t));
    const tokens = contentTokens.length > 0 ? contentTokens : rawTokens;

    if (tokens.length === 0) return null;

    const scoredResults = [];

    // Helper to score an item
    const scoreItem = (item, type, title, text, keywords = [], meta = {}) => {
      let score = 0;
      const combined = `${title} ${text} ${keywords.join(' ')}`.toLowerCase();

      tokens.forEach(tok => {
        if (combined.includes(tok)) score += 3;
        // Exact keyword match gets high bonus
        if (keywords.some(kw => kw.toLowerCase() === tok)) score += 8;
        // Title match gets high bonus
        if (title.toLowerCase().includes(tok)) score += 10;
        // Exact token equality in title or keyword
        if (title.toLowerCase() === tok || keywords.some(kw => kw.toLowerCase() === tok)) score += 15;
      });

      // Exact query phrase matching
      if (combined.includes(cleanQuery)) score += 12;

      // Type-specific relevance boosts: Synthetic Q&A, Foundations, sites and subcollections
      if (type === 'synthetic_qa') score += 14;
      if (type === 'foundation') score += 8;
      if (type === 'site' || type === 'subcollection') score += 5;

      if (score > 0) {
        scoredResults.push({
          score,
          type,
          title,
          text,
          keywords,
          meta,
          raw: item
        });
      }
    };

    // 0. Score Synthetic Q&A Knowledge Bank (Highest Precision Matching)
    (kbData.synthetic_qa || []).forEach(qa => {
      const title = qa.question;
      const text = qa.answer;
      const variations = qa.variations || [];
      const allKeywords = [...(qa.keywords || []), ...variations];
      
      scoreItem(qa, 'synthetic_qa', title, text, allKeywords, {
        id: qa.graph_node_id,
        category: qa.category,
        citations: qa.citations,
        lang: qa.lang || 'de',
        variations: variations
      });
    });

    // 1. Score Authoritative Foundations (Mikroregion, Iuenna/Globasnitz, Hemmaberg, St. Stefan, IUENNA-Projekt, Literatur)
    (kbData.foundations || []).forEach(f => {
      const title = f.title;
      const text = f.summary || f.content;
      scoreItem(f, 'foundation', title, text, f.keywords || [], {
        id: f.graph_node_id,
        category: f.category,
        citations: f.citations,
        full_text: f.content
      });
    });

    // 1. Score Archaeological Sites (Hemmaberg, Jaunstein, Globasnitz, St. Stefan)
    (kbData.sites || []).forEach(s => {
      const title = `Fundstelle: ${s.name}`;
      const text = `Epoche: ${s.period}. Highlights: ${s.highlights}. Objekte: ca. ${s.items_count}.`;
      scoreItem(s, 'site', title, text, s.keywords || [], {
        id: s.name === 'Hemmaberg' ? 'col_1792212' : (s.name.includes('Jaunstein') ? 'col_1792303' : (s.name.includes('Globasnitz') ? 'col_1792169' : 'col_1792411')),
        geonames: s.geonames,
        period: s.period,
        items: s.items_count,
        subcollection: s.subcollection
      });
    });

    // 2. Score Subcollections (HB, GLO, JAU, RET, STE, TAL)
    (kbData.subcollections || []).forEach(col => {
      const title = `${col.title} (${col.code})`;
      const text = `${col.description} Objekte: ${col.items}. Speichergröße: ${col.size}.`;
      scoreItem(col, 'subcollection', title, text, col.keywords || [], {
        id: col.code === 'HB' ? 'col_1792212' : (col.code === 'JAU' ? 'col_1792303' : (col.code === 'GLO' ? 'col_1792169' : (col.code === 'RET' ? 'col_1792572' : (col.code === 'TAL' ? 'col_1792417' : 'col_1792411')))),
        code: col.code,
        items: col.items,
        size: col.size,
        pid: col.pid,
        url: col.arche_url
      });
    });

    // 3. Score Knowledge Graph Entities (folders, diaries, plans from ARCHE)
    (kbData.graph_entities || []).forEach(g => {
      const title = `${g.label}`;
      const text = g.description ? `${g.description}` : `ARCHE Bestand (${g.type_label || g.type})`;
      scoreItem(g, 'graph_node', title, text, [g.id, g.label, g.type, g.type_label || ''], {
        id: g.id,
        type: g.type,
        type_label: g.type_label,
        items: g.items,
        size: g.size,
        arche_url: g.arche_url,
        color: g.color
      });
    });

    // 4. Score Document Types
    (kbData.doc_types || []).forEach(d => {
      const title = d.name;
      const text = `${d.description} Anzahl: ${d.count}. Formate: ${d.formats}.`;
      scoreItem(d, 'doc_type', title, text, d.keywords || [], {
        count: d.count,
        formats: d.formats
      });
    });

    // 5. Score FAQs (only if specific question matches)
    (kbData.faq || []).forEach(f => {
      scoreItem(f, 'faq', f.question, f.answer, f.keywords || [], { links: f.links });
    });

    // 6. Score Project Info
    if (kbData.project) {
      const p = kbData.project;
      const partnersList = p.partners.map(x => x.name).join(', ');
      const leadershipList = p.leadership.map(x => `${x.name} (${x.institution})`).join(', ');
      scoreItem(p, 'project', p.title, `${p.subtitle}. Fördergeber: ${p.funding}. Leitung: ${leadershipList}. Partner: ${partnersList}. Curation-Workflow: ${p.curation_workflow.join(' ')}.`, [
        'projekt', 'ziel', 'leitung', 'partner', 'workflow', 'team', 'hagmann', 'waldhart', 'curation'
      ], {
        links: [
          { text: 'ARCHE Repositorium', url: p.links.arche },
          { text: 'Web-Mapping Portal', url: p.links.wma },
          { text: 'Projekt-Blog', url: p.links.blog }
        ]
      });
    }

    scoredResults.sort((a, b) => b.score - a.score);
    return scoredResults.slice(0, 3);
  }

  // Format inline markdown (bold/italic/linebreaks)
  function formatMarkdownMini(str) {
    if (!str) return '';
    return str
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
  }

  // Format Stage 1 Search Results into HTML
  function renderSearchResultCard(results) {
    if (!results || results.length === 0) {
      return `
        <div class="chat-msg-bubble">
          <p>Dazu konnte ich in der IUENNA-Wissensbasis leider keine direkten Treffer finden.</p>
          <p style="margin-top: 6px; font-size: 0.82rem; color: var(--text-muted);">
            Tipp: Versuchen Sie Begriffe wie <em>Hemmaberg</em>, <em>Jaunstein</em>, <em>Globasnitz</em>, <em>Grabungspläne</em>, <em>QGIS</em> oder <em>Leitung</em>.
          </p>
        </div>
      `;
    }

    const top = results[0];
    let metaTagsHtml = '';
    let linksHtml = '';

    if (top.type === 'synthetic_qa') {
      metaTagsHtml = `
        <span class="chat-card-tag"><i class="fa-solid fa-circle-question" style="color: var(--secondary);"></i> ${top.meta.category || 'Archäologischer Befund'}</span>
        ${top.meta.citations && top.meta.citations.length > 0 ? `<span class="chat-card-tag"><i class="fa-solid fa-feather-pointed"></i> Lit.: ${top.meta.citations.slice(0, 2).join('; ')}</span>` : ''}
      `;
      if (top.meta.id) {
        linksHtml += `<button type="button" class="chat-card-btn secondary" onclick="if(window.focusGraphNode){window.focusGraphNode('${top.meta.id}');}"><i class="fa-solid fa-circle-nodes" style="color: var(--secondary);"></i> Im Wissensgraphen zeigen 🕸️</button>`;
      }
      linksHtml += `<a href="wma/wma.html" class="chat-card-btn primary"><i class="fa-solid fa-map-location-dot"></i> In Web-GIS ansehen</a>`;
      linksHtml += `<a href="https://id.acdh.oeaw.ac.at/iuenna" target="_blank" rel="noopener noreferrer" class="chat-card-btn secondary"><i class="fa-solid fa-database"></i> ARCHE Repositorium</a>`;
    } else if (top.type === 'foundation') {
      metaTagsHtml = `
        <span class="chat-card-tag"><i class="fa-solid fa-book-open"></i> ${top.meta.category || 'Wissenschaftliche Grundlagen'}</span>
        ${top.meta.citations && top.meta.citations.length > 0 ? `<span class="chat-card-tag"><i class="fa-solid fa-feather-pointed"></i> Lit.: ${top.meta.citations.slice(0, 2).join('; ')}</span>` : ''}
      `;
      if (top.meta.id) {
        linksHtml += `<button type="button" class="chat-card-btn secondary" onclick="if(window.focusGraphNode){window.focusGraphNode('${top.meta.id}');}"><i class="fa-solid fa-circle-nodes" style="color: var(--secondary);"></i> Im Wissensgraphen zeigen 🕸️</button>`;
      }
      linksHtml += `<a href="wma/wma.html" class="chat-card-btn primary"><i class="fa-solid fa-map-location-dot"></i> In Web-GIS ansehen</a>`;
      linksHtml += `<a href="https://id.acdh.oeaw.ac.at/iuenna" target="_blank" rel="noopener noreferrer" class="chat-card-btn secondary"><i class="fa-solid fa-database"></i> ARCHE Repositorium</a>`;
    } else if (top.type === 'subcollection') {
      metaTagsHtml = `
        <span class="chat-card-tag"><i class="fa-solid fa-folder"></i> Code: ${top.meta.code}</span>
        <span class="chat-card-tag"><i class="fa-solid fa-layer-group"></i> ${top.meta.items.toLocaleString()} Objekte</span>
        <span class="chat-card-tag"><i class="fa-solid fa-hard-drive"></i> ${top.meta.size}</span>
      `;
      if (top.meta.pid) {
        linksHtml += `<a href="${top.meta.pid}" target="_blank" rel="noopener noreferrer" class="chat-card-btn primary"><i class="fa-solid fa-arrow-up-right-from-square"></i> In ARCHE öffnen</a>`;
      }
      if (top.meta.id) {
        linksHtml += `<button type="button" class="chat-card-btn secondary" onclick="if(window.focusGraphNode){window.focusGraphNode('${top.meta.id}');}"><i class="fa-solid fa-circle-nodes" style="color: var(--secondary);"></i> Im Wissensgraphen zeigen 🕸️</button>`;
      }
      linksHtml += `<a href="wma/wma.html" class="chat-card-btn secondary"><i class="fa-solid fa-map-location-dot"></i> Auf Karte suchen</a>`;
    } else if (top.type === 'site') {
      metaTagsHtml = `
        <span class="chat-card-tag"><i class="fa-solid fa-landmark"></i> ${top.meta.period}</span>
        <span class="chat-card-tag"><i class="fa-solid fa-cubes"></i> ca. ${top.meta.items.toLocaleString()} Einträge</span>
        <span class="chat-card-tag"><i class="fa-solid fa-archive"></i> Sammlung: ${top.meta.subcollection}</span>
      `;
      if (top.meta.id) {
        linksHtml += `<button type="button" class="chat-card-btn secondary" onclick="if(window.focusGraphNode){window.focusGraphNode('${top.meta.id}');}"><i class="fa-solid fa-circle-nodes" style="color: var(--secondary);"></i> Im Wissensgraphen zeigen 🕸️</button>`;
      }
      linksHtml += `<a href="wma/wma.html" class="chat-card-btn primary"><i class="fa-solid fa-map"></i> In Web-GIS ansehen</a>`;
      if (top.meta.geonames) {
        linksHtml += `<a href="${top.meta.geonames}" target="_blank" rel="noopener noreferrer" class="chat-card-btn secondary"><i class="fa-solid fa-earth-europe"></i> GeoNames</a>`;
      }
    } else if (top.type === 'graph_node') {
      metaTagsHtml = `
        <span class="chat-card-tag"><i class="fa-solid fa-circle-nodes" style="color: var(--secondary);"></i> Typ: ${top.meta.type_label || top.meta.type}</span>
        ${top.meta.items ? `<span class="chat-card-tag"><i class="fa-solid fa-layer-group"></i> ${top.meta.items.toLocaleString()} Items</span>` : ''}
        ${top.meta.size ? `<span class="chat-card-tag"><i class="fa-solid fa-hard-drive"></i> ${top.meta.size}</span>` : ''}
      `;
      if (top.meta.arche_url) {
        linksHtml += `<a href="${top.meta.arche_url}" target="_blank" rel="noopener noreferrer" class="chat-card-btn primary"><i class="fa-solid fa-arrow-up-right-from-square"></i> In ARCHE öffnen ↗</a>`;
      }
      if (top.meta.id) {
        linksHtml += `<button type="button" class="chat-card-btn secondary" onclick="if(window.focusGraphNode){window.focusGraphNode('${top.meta.id}');}"><i class="fa-solid fa-circle-nodes" style="color: var(--secondary);"></i> Im Wissensgraphen zeigen 🕸️</button>`;
      }
    } else if (top.type === 'doc_type') {
      metaTagsHtml = `
        <span class="chat-card-tag"><i class="fa-solid fa-file"></i> ${top.meta.count}</span>
        <span class="chat-card-tag"><i class="fa-solid fa-code"></i> Formate: ${top.meta.formats}</span>
      `;
      linksHtml += `<a href="https://id.acdh.oeaw.ac.at/iuenna" target="_blank" rel="noopener noreferrer" class="chat-card-btn primary"><i class="fa-solid fa-database"></i> ARCHE Repositorium</a>`;
    } else if (top.type === 'faq' || top.type === 'project') {
      if (top.meta.links && top.meta.links.length > 0) {
        top.meta.links.forEach(l => {
          linksHtml += `<a href="${l.url}" target="_blank" rel="noopener noreferrer" class="chat-card-btn primary"><i class="fa-solid fa-link"></i> ${l.text}</a>`;
        });
      }
    }

    // Additional related matches
    let secondaryHtml = '';
    if (results.length > 1) {
      secondaryHtml = `
        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border-color); font-size: 0.78rem;">
          <span style="color: var(--text-muted); font-weight: 600;">Weitere relevante Treffer im Wissensgraphen:</span>
          <ul style="margin: 4px 0 0 16px; padding: 0; color: var(--text-dark);">
            ${results.slice(1).map(r => `
              <li style="margin-bottom: 2px;">
                <strong>${r.title}</strong>
                ${r.meta.id ? ` <a href="javascript:void(0)" onclick="if(window.focusGraphNode){window.focusGraphNode('${r.meta.id}');}" style="color: var(--secondary); text-decoration: underline; margin-left: 4px;">[Im Graph 🕸️]</a>` : ''}
              </li>
            `).join('')}
          </ul>
        </div>
      `;
    }

    // Dynamic contextual follow-up suggestions
    const followUpHtml = generateFollowUpChips(top);

    const categoryBadge = top.type === 'synthetic_qa' ? 'Archäologische Fachantwort' :
      (top.type === 'foundation' ? 'Wissenschaftliche Grundlagen' :
      (top.type === 'subcollection' ? 'ARCHE-Subcollection' :
      (top.type === 'graph_node' ? 'ARCHE-Wissensgraph' :
      (top.type === 'site' ? 'Archäologische Fundstelle' : 'Projekt-Fakt'))));

    return `
      <div class="chat-msg-bubble">
        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
          <span style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--primary); letter-spacing: 0.04em;">
            ${categoryBadge}
          </span>
        </div>
        <h4 style="margin: 0 0 6px 0; font-size: 0.95rem; font-family: var(--font-header);">${top.title}</h4>
        <p style="margin: 0 0 6px 0; font-size: 0.84rem; line-height: 1.5;">${formatMarkdownMini(top.text)}</p>
        
        ${metaTagsHtml ? `<div class="chat-card-meta">${metaTagsHtml}</div>` : ''}
        ${linksHtml ? `<div class="chat-card-links">${linksHtml}</div>` : ''}
        ${secondaryHtml}
        ${followUpHtml}
        <div style="font-size: 0.67rem; color: var(--text-muted); margin-top: 8px; font-style: italic; border-top: 1px dashed var(--border-color); padding-top: 6px; display: flex; align-items: center; gap: 4px;">
          <i class="fa-solid fa-triangle-exclamation" style="font-size: 0.65rem; color: #b88e3e;"></i> Automatische Projekt-Auskunft (kann Fehler enthalten) • Für Zitate bitte Fachpublikationen prüfen.
        </div>
      </div>
    `;
  }

  function generateFollowUpChips(top) {
    if (!top) return '';
    const text = ((top.title || '') + ' ' + (top.text || '')).toLowerCase();
    const chips = [];

    if (text.includes('glaser')) {
      chips.push({ query: 'Warum gibt es auf dem Hemmaberg Doppelkirchen?', label: '⛪ Doppelkirchen Hemmaberg' });
      chips.push({ query: 'Gibt es Grabungspläne zum Hemmaberg?', label: '🗺️ Grabungspläne in ARCHE' });
      chips.push({ query: 'Wer ist Marianne Pollak?', label: '👤 Marianne Pollak' });
    } else if (text.includes('pollak')) {
      chips.push({ query: 'Wie viele Gräber wurden im Gräberfeld von Globasnitz ausgegraben?', label: '💀 440 Gräber' });
      chips.push({ query: 'Wer ist Franz Glaser?', label: '👤 Franz Glaser' });
      chips.push({ query: 'Was wurde in Jaunstein gefunden?', label: '🏺 Gräberfeld Jaunstein' });
    } else if (text.includes('hemmaberg')) {
      chips.push({ query: 'Wer ist Franz Glaser?', label: '👤 Franz Glaser' });
      chips.push({ query: 'Gibt es Grabungspläne zum Hemmaberg?', label: '🗺️ Grabungspläne Hemmaberg' });
      chips.push({ query: 'Warum gibt es auf dem Hemmaberg Doppelkirchen?', label: '⛪ Doppelkirchen' });
      chips.push({ query: 'Was ist die Rosaliengrotte?', label: '💧 Rosaliengrotte' });
    } else if (text.includes('globasnitz') || text.includes('tscherberg') || text.includes('ostgräberfeld')) {
      chips.push({ query: 'Ist Globasnitz wirklich die römische Straßenstation Iuenna?', label: '🏛️ Tscherberg vs. Globasnitz' });
      chips.push({ query: 'Wie viele Gräber wurden im Gräberfeld von Globasnitz ausgegraben?', label: '💀 440 Gräber' });
      chips.push({ query: 'Wer ist Marianne Pollak?', label: '👤 Marianne Pollak' });
      chips.push({ query: 'Was ist die Villenanlage von St. Stefan?', label: '🏡 Villa St. Stefan' });
    } else if (text.includes('st. stefan') || text.includes('barbius') || text.includes('winkler')) {
      chips.push({ query: 'Wer war L. Barbius Vercaius?', label: '📜 L. Barbius Vercaius' });
      chips.push({ query: 'Welche Rolle spielten die historischen Skizzen von Hans Winkler?', label: '🎨 Hans Winkler Skizzen' });
      chips.push({ query: 'Gibt es Pläne zur Villa St. Stefan?', label: '🗺️ Pläne St. Stefan' });
    } else if (text.includes('jaunstein')) {
      chips.push({ query: 'Was wurde in Jaunstein gefunden?', label: '🏺 Funde in Jaunstein' });
      chips.push({ query: 'Zeige mir die Subcollection JAU in ARCHE', label: '📁 ARCHE Subcollection JAU' });
    } else {
      chips.push({ query: 'Wer ist Franz Glaser?', label: '👤 Franz Glaser' });
      chips.push({ query: 'Ist Globasnitz wirklich die römische Straßenstation Iuenna?', label: '🏛️ Iuenna & Tscherberg' });
      chips.push({ query: 'Warum gibt es auf dem Hemmaberg Doppelkirchen?', label: '⛪ Hemmaberg' });
      chips.push({ query: 'Wie kann ich die Geodaten des Projekts direkt in QGIS nutzen?', label: '🗺️ QGIS Geodaten' });
    }

    if (chips.length === 0) return '';
    return `
      <div style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border-color);">
        <span style="font-size: 0.74rem; color: var(--text-muted); font-weight: 600; display: block; margin-bottom: 4px;">Weiterführende Fragen zum Thema:</span>
        <div class="chat-chips-container" style="margin-top: 4px;">
          ${chips.map(c => `<button type="button" class="chat-chip" data-query="${escapeHtml(c.query)}">${c.label}</button>`).join('')}
        </div>
      </div>
    `;
  }

  // 4. Stage 2: In-Browser SLM (Transformers.js)
  async function initStage2SLM() {
    if (slmPipeline || isSlmLoading) return;

    isSlmLoading = true;
    const progressContainer = document.getElementById('chat-dl-progress');
    const progressFill = document.getElementById('chat-dl-fill');
    const progressPct = document.getElementById('chat-dl-pct');
    const statusText = document.getElementById('chat-dl-status');
    const badge = document.getElementById('chat-stage-badge');

    if (progressContainer) progressContainer.style.display = 'flex';
    if (badge) {
      badge.textContent = 'Lade lokale KI...';
      badge.className = 'chat-badge-stage';
    }

    try {
      console.log('[*] Initializing Transformers.js for in-browser SLM inference...');
      
      // Dynamic import from CDN
      const { pipeline, env } = await import('https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.0.2');
      
      env.allowLocalModels = false;
      env.useBrowserCache = true;

      // Test WebGPU availability safely
      let targetDevice = 'wasm';
      if (typeof navigator !== 'undefined' && navigator.gpu) {
        try {
          const adapter = await navigator.gpu.requestAdapter();
          if (adapter) {
            targetDevice = 'webgpu';
          }
        } catch (gpuErr) {
          console.warn('WebGPU check threw error, using WASM:', gpuErr);
        }
      }
      console.log(`[*] Target device for SLM: ${targetDevice}`);

      const progressCallback = (progressData) => {
        if (progressData.status === 'progress' && progressData.progress !== undefined) {
          const pct = Math.round(progressData.progress);
          if (progressFill) progressFill.style.width = `${pct}%`;
          if (progressPct) progressPct.textContent = `${pct}%`;
          const fileName = progressData.file ? ` (${progressData.file.split('/').pop()})` : '';
          if (statusText) statusText.textContent = `Lade Modell: ${pct}%${fileName}`;
        } else if (progressData.status === 'ready' || progressData.status === 'done') {
          if (progressFill) progressFill.style.width = '100%';
          if (progressPct) progressPct.textContent = '100%';
        }
      };

      try {
        slmPipeline = await pipeline('text-generation', SLM_MODEL_ID, {
          dtype: 'q4',
          device: targetDevice,
          progress_callback: progressCallback
        });
      } catch (pipeErr) {
        if (targetDevice === 'webgpu') {
          console.warn('WebGPU pipeline failed, retrying with WASM fallback...', pipeErr);
          targetDevice = 'wasm';
          slmPipeline = await pipeline('text-generation', SLM_MODEL_ID, {
            dtype: 'q4',
            device: 'wasm',
            progress_callback: progressCallback
          });
        } else {
          throw pipeErr;
        }
      }

      isSlmActive = true;
      if (progressContainer) progressContainer.style.display = 'none';
      if (badge) {
        badge.textContent = targetDevice === 'webgpu' ? 'Stufe 2: Lokale KI aktiv (WebGPU)' : 'Stufe 2: Lokale KI aktiv (WASM)';
        badge.className = 'chat-badge-stage stage2';
      }
      console.log(`[+] In-browser SLM initialized successfully on ${targetDevice}.`);

      appendBotMessage(`
        <div class="chat-msg-bubble" style="background: rgba(168, 68, 46, 0.05); border: 1px solid rgba(168, 68, 46, 0.2);">
          <p><strong>Qwen 2.5 (0.5B) aktiviert!</strong> 🚀 (${targetDevice.toUpperCase()})</p>
          <p style="font-size: 0.82rem; margin-top: 4px;">
            Das Modell <em>Qwen2.5-0.5B-Instruct</em> (Alibaba) rechnet nun zu 100 % lokal auf Ihrem Gerät (${targetDevice === 'webgpu' ? 'Grafikkarte / WebGPU' : 'CPU / WebAssembly'}). Es beherrscht Deutsch hervorragend und fasst die ARCHE-Fakten sprachlich flüssig zusammen.
          </p>
        </div>
      `);

    } catch (err) {
      console.error('Failed to load in-browser SLM:', err);
      isSlmActive = false;
      if (progressContainer) progressContainer.style.display = 'none';
      if (badge) {
        badge.textContent = 'Stufe 1: Blitz-Suche (0 MB)';
        badge.className = 'chat-badge-stage';
      }
      const toggle = document.getElementById('chat-ai-toggle');
      if (toggle) toggle.checked = false;

      appendBotMessage(`
        <div class="chat-msg-bubble" style="border-left: 3px solid var(--primary);">
          <p><strong>Hinweis zum KI-Modus:</strong></p>
          <p style="font-size: 0.82rem; margin-top: 4px;">
            Die lokale WebGPU-Beschleunigung konnte in diesem Browser nicht initialisiert werden (${err.message || 'Nicht unterstützt'}). Die blitzschnelle Stufe 1 (Such- &amp; ARCHE-Katalogmodus) bleibt uneingeschränkt aktiv!
          </p>
        </div>
      `);
    } finally {
      isSlmLoading = false;
    }
  }

  // Synthesize answer with SLM
  async function generateSlmAnswer(userQuery, searchResults) {
    if (!slmPipeline) return null;

    let contextSnippet = '';
    if (searchResults && searchResults.length > 0) {
      contextSnippet = searchResults.slice(0, 2).map(r => {
        if (r.type === 'synthetic_qa') {
          const citStr = r.meta && r.meta.citations && r.meta.citations.length > 0 ? ` (Quellen: ${r.meta.citations.join('; ')})` : '';
          return `【Archäologische Fachfrage & verifizierter Befund: ${r.title}】\n${r.text}${citStr}`;
        } else if (r.type === 'foundation') {
          const citStr = r.meta && r.meta.citations && r.meta.citations.length > 0 ? ` (Quellen: ${r.meta.citations.join('; ')})` : '';
          return `【Wissenschaftliche Grundlagen: ${r.title}】\n${r.meta.full_text || r.text}${citStr}`;
        } else if (r.type === 'site') {
          return `【Archäologische Fundstelle: ${r.title}】\n${r.text}`;
        } else if (r.type === 'subcollection') {
          return `【ARCHE-Subcollection: ${r.title}】\n${r.text}`;
        } else {
          return `【IUENNA-Fakt: ${r.title}】\n${r.text}`;
        }
      }).join('\n\n');
    } else {
      contextSnippet = 'Keine spezifischen Sammlungsfakten gefunden.';
    }

    const messages = [
      {
        role: 'system',
        content: `Du bist der wissenschaftliche KI-Assistent für das archäologische Forschungsprojekt IUENNA (ÖAW / ÖAI / kärnten.museum).
Beantworte die Frage des Nutzers auf Deutsch auf Basis des folgenden verifizierten Forschungskontexts.
Antworte präzise, sachlich und fundiert in 2 bis maximal 4 vollständigen Sätzen. Nenne wenn passend historische Autoren (wie Glaser, Pollak, Hagmann & Reiner). Erfinde keine Fakten.

Forschungskontext:
${contextSnippet}`
      },
      {
        role: 'user',
        content: userQuery
      }
    ];

    const output = await slmPipeline(messages, {
      max_new_tokens: 160,
      temperature: 0.1,
      repetition_penalty: 1.15,
      do_sample: false
    });

    if (output && output[0] && output[0].generated_text) {
      const generated = output[0].generated_text;
      let rawText = '';
      if (Array.isArray(generated)) {
        const lastMsg = generated[generated.length - 1];
        rawText = (lastMsg && lastMsg.content) ? lastMsg.content : '';
      } else if (typeof generated === 'string') {
        rawText = generated;
      }
      
      if (rawText) {
        // Clean out prompt echoes and repeated loops
        const sentences = rawText.split(/(?<=[.?!])\s+/);
        const unique = [];
        sentences.forEach(s => {
          const trimmed = s.trim();
          if (trimmed && !unique.includes(trimmed) && trimmed.toLowerCase() !== userQuery.toLowerCase()) {
            unique.push(trimmed);
          }
        });
        return unique.join(' ') || rawText;
      }
    }
    return null;
  }

  // 5. Chat UI Helpers
  function appendUserMessage(text) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-msg user';
    msgDiv.innerHTML = `
      <div class="chat-msg-bubble">${escapeHtml(text)}</div>
      <span class="chat-msg-time">Gerade eben</span>
    `;
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function appendBotMessage(htmlContent) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-msg bot';
    msgDiv.innerHTML = `
      ${htmlContent}
      <span class="chat-msg-time">Gerade eben</span>
    `;
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return null;

    const indicator = document.createElement('div');
    indicator.className = 'chat-msg bot';
    indicator.id = 'chat-typing-indicator-el';
    indicator.innerHTML = `
      <div class="chat-typing-indicator">
        <div class="chat-typing-dot"></div>
        <div class="chat-typing-dot"></div>
        <div class="chat-typing-dot"></div>
      </div>
    `;
    messagesContainer.appendChild(indicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return indicator;
  }

  function removeTypingIndicator() {
    const el = document.getElementById('chat-typing-indicator-el');
    if (el) el.remove();
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // 6. Conversational Dialogue State & Main Handler
  const dialogueState = {
    lastTopic: null,
    lastSite: null
  };

  async function handleUserSubmit(userQuery) {
    if (!userQuery || !userQuery.trim()) return;
    const query = userQuery.trim();

    // 1. Render User Message
    appendUserMessage(query);

    // 2. Show Typing Indicator
    showTypingIndicator();

    const cleanQ = query.toLowerCase().replace(/[?!.,;:]/g, '').trim();

    // Dialog Intent A: Greetings
    if (/^(hallo|hi|guten (tag|morgen|abend)|servus|grüß gott|moin|hey)$/i.test(cleanQ)) {
      setTimeout(() => {
        removeTypingIndicator();
        appendBotMessage(`
          <div class="chat-msg-bubble">
            <p><strong>Grüß Gott!</strong> 🏛️</p>
            <p style="margin-top: 6px; font-size: 0.85rem; line-height: 1.5;">
              Ich bin Ihr interaktiver Sammlungs-Assistent für das <strong>IUENNA-Projekt</strong> (ÖAW / ÖAI / kärnten.museum).
              Ich helfe Ihnen beim Erkunden von über 20.000 archäologischen Objekten und Plänen in ARCHE sowie den neuesten Forschungsergebnissen zum Hemmaberg, zu Globasnitz und zur Villa St. Stefan.
            </p>
            <p style="margin-top: 6px; font-size: 0.82rem; color: var(--text-muted);">
              Wählen Sie ein Thema oder stellen Sie eine freie Frage:
            </p>
            <div class="chat-chips-container" style="margin-top: 8px;">
              <button type="button" class="chat-chip" data-query="Erzähl mir vom Hemmaberg">⛪ Hemmaberg</button>
              <button type="button" class="chat-chip" data-query="Ist Globasnitz die Straßenstation Iuenna?">🏛️ Tscherberg vs. Globasnitz</button>
              <button type="button" class="chat-chip" data-query="Was ist die Villenanlage von St. Stefan?">🏡 Villa St. Stefan</button>
              <button type="button" class="chat-chip" data-query="Wie viele Gräber wurden im Gräberfeld von Globasnitz ausgegraben?">💀 440 Gräber</button>
            </div>
          </div>
        `);
      }, 120);
      return;
    }

    // Dialog Intent B: Thanks / Feedback
    if (/^(danke|vielen dank|dankeschön|super|toll|klasse|prima|danke dir|perfekt|danke schön)$/i.test(cleanQ)) {
      setTimeout(() => {
        removeTypingIndicator();
        appendBotMessage(`
          <div class="chat-msg-bubble">
            <p><strong>Sehr gerne!</strong> 😊</p>
            <p style="margin-top: 6px; font-size: 0.85rem; line-height: 1.5;">
              Haben Sie noch weitere Fragen zu den Fundstellen, den Grabungsplänen in ARCHE oder den Inschriften? Ich stehe Ihnen jederzeit zur Verfügung.
            </p>
            ${dialogueState.lastTopic ? `
              <p style="margin-top: 6px; font-size: 0.8rem; color: var(--text-muted);">
                Möchten Sie noch mehr zu <strong>${escapeHtml(dialogueState.lastTopic)}</strong> erfahren?
              </p>
            ` : ''}
          </div>
        `);
      }, 120);
      return;
    }

    // Dialog Intent C: Help / Overview
    if (/^(hilfe|help|was kannst du|wer bist du|funktionen)$/i.test(cleanQ)) {
      setTimeout(() => {
        removeTypingIndicator();
        appendBotMessage(`
          <div class="chat-msg-bubble">
            <p><strong>So kann ich Ihnen helfen:</strong> 🔍</p>
            <ul style="margin: 6px 0 0 16px; padding: 0; font-size: 0.84rem; line-height: 1.5;">
              <li><strong>Archäologische Fakten:</strong> Fragen Sie nach Bauphasen, Datierungen oder Ausgräbern (z. B. <em>„Doppelkirchen Hemmaberg“</em>, <em>„Villa St. Stefan“</em>).</li>
              <li><strong>ARCHE Sammlungen:</strong> Finden Sie Grabungspläne, Fundtagebücher und Fotos im Repositorium.</li>
              <li><strong>Wissensgraph &amp; GIS:</strong> Klicken Sie in den Antwortkarten auf <em>„Im Wissensgraphen zeigen“</em> oder <em>„In Web-GIS ansehen“</em>.</li>
            </ul>
          </div>
        `);
      }, 120);
      return;
    }

    // Multi-turn Pronoun & Topic Expansion (e.g. "Gibt es dazu Pläne?" -> append lastTopic)
    let effectiveQuery = query;
    if (dialogueState.lastTopic && /\b(dazu|dort|davon|mehr|weitere|auch|pläne|fotos|bilder|gräber)\b/i.test(query) && !query.toLowerCase().includes(dialogueState.lastTopic.toLowerCase())) {
      effectiveQuery = `${query} ${dialogueState.lastTopic}`;
    }

    // 3. Search Knowledge Base
    const results = searchKnowledgeBase(effectiveQuery);

    // Update conversation topic state
    if (results && results.length > 0) {
      const top = results[0];
      const txt = ((top.title || '') + ' ' + (top.text || '')).toLowerCase();
      if (txt.includes('hemmaberg')) dialogueState.lastTopic = 'Hemmaberg';
      else if (txt.includes('globasnitz')) dialogueState.lastTopic = 'Globasnitz';
      else if (txt.includes('st. stefan') || txt.includes('barbius') || txt.includes('winkler')) dialogueState.lastTopic = 'St. Stefan';
      else if (txt.includes('jaunstein')) dialogueState.lastTopic = 'Jaunstein';
      else if (txt.includes('qgis') || txt.includes('geodaten')) dialogueState.lastTopic = 'Geodaten';
    }

    // 4. Return instant verified academic research card
    setTimeout(() => {
      removeTypingIndicator();
      const cardHtml = renderSearchResultCard(results);
      appendBotMessage(cardHtml);
    }, 150); // Natural micro-delay for smooth UX
  }

  // 7. Event Binding
  function bindEvents() {
    const triggerBtn = document.getElementById('iuenna-chat-trigger');
    const chatWindow = document.getElementById('iuenna-chat-window');
    const closeBtn = document.getElementById('chat-close-btn');
    const inputField = document.getElementById('chat-input-field');
    const sendBtn = document.getElementById('chat-send-btn');

    // Toggle Chat Window
    const toggleWindow = () => {
      triggerHaptic();
      const isOpen = chatWindow.classList.contains('chat-open');
      if (isOpen) {
        chatWindow.classList.remove('chat-open');
      } else {
        chatWindow.classList.add('chat-open');
        setTimeout(() => inputField.focus(), 200);
      }
    };

    triggerBtn.addEventListener('click', toggleWindow);
    closeBtn.addEventListener('click', () => {
      chatWindow.classList.remove('chat-open');
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && chatWindow.classList.contains('chat-open')) {
        chatWindow.classList.remove('chat-open');
      }
    });

    // Send Message
    const submitInput = () => {
      const val = inputField.value;
      if (val.trim()) {
        inputField.value = '';
        handleUserSubmit(val);
      }
    };

    sendBtn.addEventListener('click', submitInput);
    inputField.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        submitInput();
      }
    });

    // Suggestion Chips Click
    document.addEventListener('click', (e) => {
      const chip = e.target.closest('.chat-chip');
      if (chip) {
        const query = chip.getAttribute('data-query');
        if (query) {
          handleUserSubmit(query);
        }
      }
    });
  }

  // 8. Initialization on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      injectChatUI();
      loadKnowledgeBase();
    });
  } else {
    injectChatUI();
    loadKnowledgeBase();
  }

})();
