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
  let isKbLoading = true;
  let kbLoadError = false;
  let slmPipeline = null;
  let isSlmLoading = false;
  let isSlmActive = false;
  let currentRequestId = 0;

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
      <div class="chat-mode-bar">
        <div class="chat-mode-toggle-row">
          <div class="chat-mode-label">
            <i class="fa-solid fa-bolt" style="color: var(--secondary);"></i>
            <span>Optionale KI-Zusammenfassung</span>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span id="chat-stage-badge" class="chat-badge-stage">Katalogmodus</span>
            <label class="switch" title="Lokale KI-Sprachfassung (Qwen 2.5) aktivieren/deaktivieren">
              <input type="checkbox" id="chat-ai-toggle">
              <span class="slider"></span>
            </label>
          </div>
        </div>
        <!-- Progress Bar for Model Download -->
        <div class="chat-download-progress" id="chat-dl-progress">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span id="chat-dl-status">Lade lokales Modell...</span>
            <span id="chat-dl-pct">0%</span>
          </div>
          <div class="chat-progress-bar-bg">
            <div class="chat-progress-bar-fill" id="chat-dl-fill"></div>
          </div>
        </div>
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
              Wählen Sie ein Thema oder stellen Sie eine freie Frage (z. B. nach Fundorten oder Personen wie <em>Hans Winkler</em>):
            </p>
            <div class="chat-chips-container">
              <button class="chat-chip" data-query="Wer war Hans Winkler?">👤 Hans Winkler</button>
              <button class="chat-chip" data-query="Ist Globasnitz wirklich die römische Straßenstation Iuenna?">🏛️ Tscherberg vs. Globasnitz</button>
              <button class="chat-chip" data-query="Was ist über die frühmittelalterliche Fußprothese vom Hemmaberg bekannt?">🦴 Fußprothese Hemmaberg</button>
              <button class="chat-chip" data-query="Wurden im Gräberfeld von Globasnitz künstliche Schädeldeformationen nachgewiesen?">💀 Schädeldeformationen</button>
              <button class="chat-chip" data-query="Was ist die Villenanlage von St. Stefan?">🏡 Villenanlage St. Stefan</button>
              <button class="chat-chip" data-query="Warum gibt es auf dem Hemmaberg Doppelkirchen?">⛪ Hemmaberg Doppelkirchen</button>
              <button class="chat-chip" data-query="Wie viele Gräber wurden im Gräberfeld von Globasnitz ausgegraben?">⚰️ Gräberfeld Globasnitz (425 Gräber)</button>
              <button class="chat-chip" data-query="Wer ist Marianne Pollak?">👤 Marianne Pollak</button>
              <button class="chat-chip" data-query="Was ist über den Münzschatzfund von Globasnitz bekannt?">🪙 Münzschatz (322 Münzen)</button>
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
          <input type="text" id="chat-input-field" class="chat-input-field" placeholder="Frage stellen (z.B. 'Wer war Hans Winkler?', 'Pläne Hemmaberg')..." autocomplete="off">
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
    isKbLoading = true;
    kbLoadError = false;
    try {
      const response = await fetch(KB_URL);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      kbData = await response.json();
      isKbLoading = false;
      console.log('✓ IUENNA Knowledge Base loaded successfully:', kbData.meta);
    } catch (err) {
      isKbLoading = false;
      kbLoadError = true;
      console.warn('Could not load IUENNA Knowledge Base from file:', err);
    }
  }

  // German Stopwords to prevent generic words from skewing relevance results
  const GERMAN_STOPWORDS = new Set([
    'was', 'ist', 'sind', 'war', 'waren', 'wird', 'werden', 'wurde', 'wurden', 'hat', 'hatte', 'hatten', 'habe', 'haben',
    'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einer', 'einem', 'eines', 'einen',
    'und', 'oder', 'aber', 'in', 'im', 'ins', 'zu', 'zum', 'zur', 'von', 'vom', 'mit', 'auf', 'aus', 'bei',
    'für', 'wo', 'wie', 'wer', 'welche', 'welcher', 'welches', 'welchem', 'gibt', 'es', 'kann', 'können', 'konnte', 'konnten', 'man',
    'soll', 'sollte', 'sollten', 'muss', 'musste', 'müssen', 'finde', 'ich', 'du', 'er', 'sie', 'wir', 'ihr', 'zeig', 'mir', 'uns', 'bitte',
    'über', 'nach', 'an', 'am', 'als', 'so', 'da', 'dann', 'auch', 'noch', 'nur', 'sehr', 'viel', 'viele', 'mehr', 'hier', 'dort',
    'wenn', 'dass', 'daß', 'ob', 'um', 'durch', 'vor', 'hinter', 'unter', 'neben', 'zwischen'
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
      const combined = `${title} ${text} ${keywords.join(' ')}`.toLowerCase();
      const titleLower = title.toLowerCase();

      let matchScore = 0;
      let strongMatch = false;

      tokens.forEach(tok => {
        // Whole word or boundary matching gets higher precision
        const wordRegex = new RegExp(`(^|[^a-z0-9äöüß])${tok.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}($|[^a-z0-9äöüß])`, 'i');
        if (wordRegex.test(combined)) {
          matchScore += 4;
        } else if (combined.includes(tok)) {
          matchScore += 2;
        }

        // Exact keyword match gets high bonus
        if (keywords.some(kw => kw.toLowerCase() === tok)) {
          matchScore += 10;
          strongMatch = true;
        }
        // Title match gets high bonus
        if (titleLower.includes(tok)) {
          matchScore += 12;
          strongMatch = true;
        }
        // Exact token equality in title or keyword
        if (titleLower === tok || keywords.some(kw => kw.toLowerCase() === tok)) {
          matchScore += 15;
          strongMatch = true;
        }
      });

      // Exact query phrase matching
      if (combined.includes(cleanQuery)) {
        matchScore += 14;
        strongMatch = true;
      }

      // Relevance threshold: require strong match (title/keyword/phrase) or at least 2 distinct token matches
      const minThreshold = tokens.length > 1 ? 7 : 6;
      if (matchScore >= minThreshold || (matchScore > 0 && strongMatch)) {
        let totalScore = matchScore;
        if (type === 'synthetic_qa') totalScore += 14;
        if (type === 'foundation') totalScore += 8;
        if (type === 'site' || type === 'subcollection') totalScore += 5;

        scoredResults.push({
          score: totalScore,
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

  // Format Stage 1 Search Results into HTML (with optional SLM summary)
  function renderSearchResultCard(results, slmSummary = null) {
    if (!results || results.length === 0) {
      return `
        <div class="chat-msg-bubble">
          <p><strong>Keine passenden Informationen im Bestand gefunden.</strong></p>
          <p style="margin-top: 6px; font-size: 0.82rem; color: var(--text-muted);">
            Zu Ihrer Anfrage konnten keine passenden archäologischen Objekte, Fundstellen oder Grundlagen in der IUENNA-Wissensbasis ermittelt werden.
          </p>
          <p style="margin-top: 6px; font-size: 0.82rem; color: var(--text-muted);">
            Tipp: Versuchen Sie Schlagworte wie <em>Hemmaberg</em>, <em>Jaunstein</em>, <em>Globasnitz</em>, <em>Grabungspläne</em>, <em>Hans Winkler</em> oder <em>QGIS</em>.
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

    let slmSummaryHtml = '';
    if (slmSummary) {
      slmSummaryHtml = `
        <div class="chat-slm-summary-box" style="margin-bottom: 12px; padding: 10px 14px; background: rgba(184, 142, 62, 0.09); border-left: 3px solid var(--secondary); border-radius: var(--radius-sm, 4px);">
          <div style="font-size: 0.72rem; font-weight: 700; color: var(--secondary); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
            <i class="fa-solid fa-brain"></i> Zusammenfassung der gefundenen Einträge (lokales Modell)
          </div>
          <p style="margin: 0; font-size: 0.85rem; line-height: 1.55; color: var(--text-dark);">${escapeHtml(slmSummary)}</p>
        </div>
      `;
    }

    return `
      <div class="chat-msg-bubble">
        ${slmSummaryHtml}
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

    if (text.includes('prothese') || text.includes('amputation') || text.includes('binder')) {
      chips.push({ query: 'Was ist über die frühmittelalterliche Fußprothese vom Hemmaberg bekannt?', label: '🦴 Fußprothese Hemmaberg' });
      chips.push({ query: 'Wurden im Gräberfeld von Globasnitz künstliche Schädeldeformationen nachgewiesen?', label: '💀 Schädeldeformationen' });
      chips.push({ query: 'Welche demografischen Unterschiede zeigen die Bestattungen in Globasnitz und auf dem Hemmaberg?', label: '📊 Demografie & Bestattungen' });
    } else if (text.includes('schädel') || text.includes('deformation') || text.includes('turmschädel')) {
      chips.push({ query: 'Wurden im Gräberfeld von Globasnitz künstliche Schädeldeformationen nachgewiesen?', label: '💀 Schädeldeformationen' });
      chips.push({ query: 'Was ist über die frühmittelalterliche Fußprothese vom Hemmaberg bekannt?', label: '🦴 Fußprothese Hemmaberg' });
      chips.push({ query: 'Warum wird das Gräberfeld von Globasnitz als Zeugnis einer \'Kontaktregion\' bezeichnet?', label: '🌍 Ostgoten & Kontaktregion' });
    } else if (text.includes('münz') || text.includes('schatz') || text.includes('322')) {
      chips.push({ query: 'Was ist über den Münzschatzfund von Globasnitz bekannt?', label: '🪙 Münzschatz (322 Münzen)' });
      chips.push({ query: 'Welche geophysikalischen Prospektionsmethoden wurden in Globasnitz und St. Stefan eingesetzt?', label: '📡 Geophysik & Prospektion' });
      chips.push({ query: 'Ist Globasnitz wirklich die römische Straßenstation Iuenna?', label: '🏛️ Tscherberg vs. Globasnitz' });
    } else if (text.includes('glaser')) {
      chips.push({ query: 'Warum gibt es auf dem Hemmaberg Doppelkirchen?', label: '⛪ Doppelkirchen Hemmaberg' });
      chips.push({ query: 'Gibt es Grabungspläne zum Hemmaberg?', label: '🗺️ Grabungspläne in ARCHE' });
      chips.push({ query: 'Wer ist Marianne Pollak?', label: '👤 Marianne Pollak' });
    } else if (text.includes('pollak')) {
      chips.push({ query: 'Wie viele Gräber wurden im Gräberfeld von Globasnitz ausgegraben?', label: '💀 425 Gräber' });
      chips.push({ query: 'Wurden im Gräberfeld von Globasnitz künstliche Schädeldeformationen nachgewiesen?', label: '💀 Schädeldeformationen' });
      chips.push({ query: 'Wer ist Franz Glaser?', label: '👤 Franz Glaser' });
    } else if (text.includes('hemmaberg')) {
      chips.push({ query: 'Was ist über die frühmittelalterliche Fußprothese vom Hemmaberg bekannt?', label: '🦴 Fußprothese (6. Jh.)' });
      chips.push({ query: 'Was verraten die archäologischen Funde über Alltag, Ernährung und Wirtschaft auf dem Hemmaberg?', label: '🥣 Alltag & Ernährung' });
      chips.push({ query: 'Warum gibt es auf dem Hemmaberg Doppelkirchen?', label: '⛪ Doppelkirchen' });
      chips.push({ query: 'Wer ist Franz Glaser?', label: '👤 Franz Glaser' });
    } else if (text.includes('globasnitz') || text.includes('tscherberg') || text.includes('ostgräberfeld')) {
      chips.push({ query: 'Ist Globasnitz wirklich die römische Straßenstation Iuenna?', label: '🏛️ Tscherberg vs. Globasnitz' });
      chips.push({ query: 'Was ist über den Münzschatzfund von Globasnitz bekannt?', label: '🪙 Münzschatz (322 Münzen)' });
      chips.push({ query: 'Wie viele Gräber wurden im Gräberfeld von Globasnitz ausgegraben?', label: '⚰️ 425 Gräber' });
      chips.push({ query: 'Was ist die Villenanlage von St. Stefan?', label: '🏡 Villa St. Stefan' });
    } else if (text.includes('st. stefan') || text.includes('barbius') || text.includes('winkler')) {
      chips.push({ query: 'Wer war L. Barbius Vercaius?', label: '📜 L. Barbius Vercaius' });
      chips.push({ query: 'Welche Rolle spielten die historischen Skizzen von Hans Winkler?', label: '🎨 Hans Winkler Skizzen' });
      chips.push({ query: 'Gibt es Pläne zur Villa St. Stefan?', label: '🗺️ Pläne St. Stefan' });
    } else if (text.includes('jaunstein')) {
      chips.push({ query: 'Was wurde in Jaunstein gefunden?', label: '🏺 Funde in Jaunstein' });
      chips.push({ query: 'Zeige mir die Subcollection JAU in ARCHE', label: '📁 ARCHE Subcollection JAU' });
    } else {
      chips.push({ query: 'Wer war Hans Winkler?', label: '👤 Hans Winkler' });
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
        badge.textContent = targetDevice === 'webgpu' ? 'Modell aktiv (WebGPU)' : 'Modell aktiv (WASM)';
        badge.className = 'chat-badge-stage stage2';
      }
      console.log(`[+] In-browser SLM initialized successfully on ${targetDevice}.`);

      appendBotMessage(`
        <div class="chat-msg-bubble" style="background: rgba(184, 142, 62, 0.08); border-left: 3px solid var(--secondary);">
          <p><strong>Lokale Sprachfassung aktiviert</strong> 🧠 (${targetDevice.toUpperCase()})</p>
          <p style="font-size: 0.82rem; margin-top: 4px; line-height: 1.45;">
            Das Modell <em>Qwen2.5-0.5B-Instruct</em> rechnet nun direkt in Ihrem Browser. Es formuliert kurze Zusammenfassungen der gefundenen Sammlungs- und Forschungseinträge. Unveränderte Primärquellen und Aktionsbuttons bleiben stets erhalten.
          </p>
        </div>
      `);

    } catch (err) {
      console.error('Failed to load in-browser SLM:', err);
      isSlmActive = false;
      if (progressContainer) progressContainer.style.display = 'none';
      if (badge) {
        badge.textContent = 'Katalogmodus';
        badge.className = 'chat-badge-stage';
      }
      const toggle = document.getElementById('chat-ai-toggle');
      if (toggle) toggle.checked = false;

      appendBotMessage(`
        <div class="chat-msg-bubble" style="border-left: 3px solid var(--primary);">
          <p><strong>Hinweis zur Modellinitialisierung:</strong></p>
          <p style="font-size: 0.82rem; margin-top: 4px;">
            Das lokale Modell konnte in diesem Browser nicht geladen werden (${err.message || 'Nicht unterstützt'}). Die reguläre Suche in den geprüften Projekt- und ARCHE-Daten bleibt uneingeschränkt aktiv.
          </p>
        </div>
      `);
    } finally {
      isSlmLoading = false;
    }
  }

  // Helper to clip text at sentence boundary preserving datings and qualifiers
  function clipToSentenceBoundary(str, maxLength = 500) {
    if (!str) return '';
    const clean = str.replace(/\s+/g, ' ').trim();
    if (clean.length <= maxLength) return clean;
    const truncated = clean.substring(0, maxLength);
    const lastPunct = Math.max(
      truncated.lastIndexOf('. '),
      truncated.lastIndexOf('? '),
      truncated.lastIndexOf('! ')
    );
    if (lastPunct > 120) {
      return truncated.substring(0, lastPunct + 1).trim();
    }
    const lastSpace = truncated.lastIndexOf(' ');
    if (lastSpace > 120) {
      return truncated.substring(0, lastSpace).trim() + ' ...';
    }
    return truncated.trim() + ' ...';
  }

  // Synthesize answer with SLM (strict summarization only)
  async function generateSlmAnswer(userQuery, searchResults) {
    if (!slmPipeline) return null;

    let contextSnippet = '';
    if (searchResults && searchResults.length > 0) {
      contextSnippet = searchResults.slice(0, 2).map((r, idx) => {
        const rawText = (r.type === 'foundation' && r.meta && r.meta.full_text) ? r.meta.full_text : r.text;
        const bounded = clipToSentenceBoundary(rawText, 450);
        return `[Ausschnitt ${idx + 1}: ${r.title}]\n${bounded}`;
      }).join('\n\n');
    } else {
      contextSnippet = 'Keine passenden Textausschnitte vorhanden.';
    }

    const INFERENCE_TIMEOUT_MS = 10000;

    const inferencePromise = (async () => {
      try {
        const messages = [
          {
            role: 'system',
            content: 'Formuliere aus den bereitgestellten Textausschnitten eine kurze Antwort auf Deutsch. Verwende ausschließlich die enthaltenen Informationen. Bewahre Namen, Datierungen, Zahlen, Verneinungen und Unsicherheitsangaben. Ergänze keine Personen, Quellen oder Zusammenhänge aus deinem Modellwissen. Wenn die Ausschnitte die Frage nicht beantworten, benenne die Informationslücke. Schreibe höchstens zwei bis vier Sätze. Erzeuge keine Links oder HTML-Auszeichnung.'
          },
          {
            role: 'user',
            content: `Bereitgestellte Textausschnitte:\n${contextSnippet}\n\nFrage: ${userQuery}`
          }
        ];

        const output = await slmPipeline(messages, {
          max_new_tokens: 140,
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
      } catch (err) {
        console.warn('SLM generation exception:', err);
        return null;
      }
    })();

    const timeoutPromise = new Promise((resolve) => {
      setTimeout(() => {
        console.warn(`[!] SLM inference exceeded ${INFERENCE_TIMEOUT_MS}ms timeout.`);
        resolve(null);
      }, INFERENCE_TIMEOUT_MS);
    });

    return await Promise.race([inferencePromise, timeoutPromise]);
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
    const thisRequestId = ++currentRequestId;

    // 1. Render User Message
    appendUserMessage(query);

    // 2. Show Typing Indicator
    showTypingIndicator();

    // Check if Knowledge Base is still loading
    if (isKbLoading) {
      setTimeout(() => {
        if (thisRequestId !== currentRequestId) return;
        removeTypingIndicator();
        appendBotMessage(`
          <div class="chat-msg-bubble">
            <p><i class="fa-solid fa-spinner fa-spin" style="color: var(--secondary);"></i> Die Sammlungs-Wissensbasis wird noch geladen. Bitte einen kurzen Moment Geduld...</p>
          </div>
        `);
      }, 100);
      return;
    }

    if (kbLoadError || !kbData) {
      setTimeout(() => {
        if (thisRequestId !== currentRequestId) return;
        removeTypingIndicator();
        appendBotMessage(`
          <div class="chat-msg-bubble">
            <p><i class="fa-solid fa-triangle-exclamation" style="color: #b88e3e;"></i> Die Sammlungs-Wissensbasis konnte nicht geladen werden. Bitte prüfen Sie Ihre Netzwerkverbindung oder laden Sie die Seite neu.</p>
          </div>
        `);
      }, 100);
      return;
    }

    const cleanQ = query.toLowerCase().replace(/[?!.,;:]/g, '').trim();

    // Dialog Intent A: Greetings
    if (/^(hallo|hi|guten (tag|morgen|abend)|servus|grüß gott|moin|hey)$/i.test(cleanQ)) {
      setTimeout(() => {
        if (thisRequestId !== currentRequestId) return;
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
      }, 100);
      return;
    }

    // Dialog Intent B: Thanks / Feedback
    if (/^(danke|vielen dank|dankeschön|super|toll|klasse|prima|danke dir|perfekt|danke schön)$/i.test(cleanQ)) {
      setTimeout(() => {
        if (thisRequestId !== currentRequestId) return;
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
      }, 100);
      return;
    }

    // Dialog Intent C: Help / Overview
    if (/^(hilfe|help|was kannst du|wer bist du|funktionen)$/i.test(cleanQ)) {
      setTimeout(() => {
        if (thisRequestId !== currentRequestId) return;
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
      }, 100);
      return;
    }

    // Multi-turn Pronoun & Topic Expansion (e.g. "Gibt es dazu Pläne?" -> append lastTopic)
    let effectiveQuery = query;
    if (dialogueState.lastTopic && /\b(dazu|dort|davon|mehr|weitere|auch|pläne|fotos|bilder|gräber)\b/i.test(query) && !query.toLowerCase().includes(dialogueState.lastTopic.toLowerCase())) {
      effectiveQuery = `${query} ${dialogueState.lastTopic}`;
    }

    // 3. Search Knowledge Base (with fixed token matching requirement)
    const results = searchKnowledgeBase(effectiveQuery);

    // If no results found in knowledge base
    if (!results || results.length === 0) {
      setTimeout(() => {
        if (thisRequestId !== currentRequestId) return;
        removeTypingIndicator();
        const cardHtml = renderSearchResultCard([]);
        appendBotMessage(cardHtml);
      }, 100);
      return;
    }

    // Update conversation topic state from actual top match
    const top = results[0];
    const txt = ((top.title || '') + ' ' + (top.text || '')).toLowerCase();
    if (txt.includes('hemmaberg')) dialogueState.lastTopic = 'Hemmaberg';
    else if (txt.includes('globasnitz')) dialogueState.lastTopic = 'Globasnitz';
    else if (txt.includes('st. stefan') || txt.includes('barbius') || txt.includes('winkler')) dialogueState.lastTopic = 'St. Stefan';
    else if (txt.includes('jaunstein')) dialogueState.lastTopic = 'Jaunstein';
    else if (txt.includes('qgis') || txt.includes('geodaten')) dialogueState.lastTopic = 'Geodaten';

    // 4. Check if SLM summarization is active
    if (isSlmActive && slmPipeline) {
      try {
        const summary = await generateSlmAnswer(query, results);
        if (thisRequestId !== currentRequestId) return; // Discard outdated response
        removeTypingIndicator();
        const cardHtml = renderSearchResultCard(results, summary);
        appendBotMessage(cardHtml);
      } catch (err) {
        console.warn('SLM generation failed, falling back to direct search results:', err);
        if (thisRequestId !== currentRequestId) return;
        removeTypingIndicator();
        const cardHtml = renderSearchResultCard(results);
        appendBotMessage(cardHtml);
      }
    } else {
      // Instant Catalog Output (Stage 1)
      setTimeout(() => {
        if (thisRequestId !== currentRequestId) return;
        removeTypingIndicator();
        const cardHtml = renderSearchResultCard(results);
        appendBotMessage(cardHtml);
      }, 100);
    }
  }

  // 7. Event Binding
  function bindEvents() {
    const triggerBtn = document.getElementById('iuenna-chat-trigger');
    const chatWindow = document.getElementById('iuenna-chat-window');
    const closeBtn = document.getElementById('chat-close-btn');
    const inputField = document.getElementById('chat-input-field');
    const sendBtn = document.getElementById('chat-send-btn');
    const aiToggle = document.getElementById('chat-ai-toggle');

    // Toggle AI Model Mode
    if (aiToggle) {
      aiToggle.addEventListener('change', async (e) => {
        if (e.target.checked) {
          await initStage2SLM();
        } else {
          isSlmActive = false;
          const badge = document.getElementById('chat-stage-badge');
          if (badge) {
            badge.textContent = 'Katalogmodus';
            badge.className = 'chat-badge-stage';
          }
          appendBotMessage(`
            <div class="chat-msg-bubble" style="border-left: 3px solid var(--secondary);">
              <p><strong>Katalogmodus aktiv.</strong></p>
              <p style="font-size: 0.82rem; margin-top: 4px;">
                Antworten werden wieder direkt aus der geprüften IUENNA-Wissensbasis ohne lokale Modellzusammenfassung ausgegeben.
              </p>
            </div>
          `);
        }
      });
    }

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

    if (triggerBtn) triggerBtn.addEventListener('click', toggleWindow);
    if (closeBtn) closeBtn.addEventListener('click', () => {
      if (chatWindow) chatWindow.classList.remove('chat-open');
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && chatWindow && chatWindow.classList.contains('chat-open')) {
        chatWindow.classList.remove('chat-open');
      }
    });

    // Send Message
    const submitInput = () => {
      if (!inputField) return;
      const val = inputField.value;
      if (val.trim()) {
        inputField.value = '';
        handleUserSubmit(val);
      }
    };

    if (sendBtn) sendBtn.addEventListener('click', submitInput);
    if (inputField) {
      inputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          submitInput();
        }
      });
    }

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

  // Expose global controller for testing and deep-linking
  window.iuennaChat = {
    search: searchKnowledgeBase,
    submit: handleUserSubmit,
    getKbData: () => kbData,
    setKbData: (d) => { kbData = d; }
  };

})();
