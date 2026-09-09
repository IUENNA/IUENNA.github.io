/**
 * iuenna-chat.js
 * --------------
 * Intuitiver Sammlungs- & Recherche-Assistent für das IUENNA-Projekt.
 * 
 * Durchsucht in Echtzeit die archäologische Wissensbasis (data/iuenna_kb.json)
 * nach Objekten, Fundstellen, Plänen und Befunden.
 * 
 * Präsentiert Treffer kurz und prägnant ("Ich habe dazu Folgendes gefunden:")
 * und leitet direkt zu den interaktiven Aktionen weiter:
 * - Im Wissensgraphen zeigen (Cytoscape Graph Highlight)
 * - In Web-GIS ansehen (Web-Mapping Karte)
 * - In ARCHE öffnen (Repositorium)
 * 
 * 100% Client-Side. Keine externen API-Abhängigkeiten. Sofortige Ausführung.
 */

(function() {
  'use strict';

  // Configuration
  const KB_URL = 'data/iuenna_kb.json';
  
  let kbData = null;
  let isKbLoading = true;
  let kbLoadError = false;
  let currentRequestId = 0;

  // Conversational Dialogue State
  const dialogueState = {
    lastTopic: null,
    lastSite: null
  };

  // Sound/Vibration feedback helper (subtle)
  function triggerHaptic() {
    if (navigator.vibrate) navigator.vibrate(10);
  }

  // 1. Build and Inject DOM elements
  function injectChatUI() {
    if (document.getElementById('iuenna-chat-trigger')) return;

    // Floating Trigger button
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
            <p class="chat-header-sub">Suche in 20.000+ Objekten &amp; Quellen</p>
          </div>
        </div>
        <div class="chat-header-actions">
          <button class="chat-close-btn" id="chat-close-btn" aria-label="Schließen" title="Schließen (ESC)">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
      </div>

      <!-- Messages Area -->
      <div class="chat-messages" id="chat-messages">
        <!-- Welcome Message -->
        <div class="chat-msg bot">
          <div class="chat-msg-bubble">
            <p><strong>Willkommen beim IUENNA Sammlungs-Assistenten!</strong> 🏺</p>
            <p style="margin-top: 6px; font-size: 0.84rem; line-height: 1.45;">
              Stellen Sie eine kurze Frage oder wählen Sie ein Thema. Die Buttons in den Treffern führen Sie direkt zu den Funden im <strong>Wissensgraphen</strong>, im <strong>Web-GIS</strong> oder im <strong>ARCHE-Repositorium</strong>:
            </p>
            <div class="chat-chips-container" style="margin-top: 8px;">
              <button type="button" class="chat-chip" data-query="Welche Münzen gibt es?">🪙 Münzschatz Globasnitz</button>
              <button type="button" class="chat-chip" data-query="Wer war Hans Winkler?">👤 Hans Winkler</button>
              <button type="button" class="chat-chip" data-query="Doppelkirchen Hemmaberg">⛪ Hemmaberg Doppelkirchen</button>
              <button type="button" class="chat-chip" data-query="Gräberfeld Globasnitz">💀 Gräberfeld Globasnitz</button>
              <button type="button" class="chat-chip" data-query="Villenanlage St. Stefan">🏡 Villa St. Stefan</button>
              <button type="button" class="chat-chip" data-query="Grabungspläne Hemmaberg">🗺️ Grabungspläne</button>
              <button type="button" class="chat-chip" data-query="QGIS Geodaten">🗺️ QGIS GeoPackage</button>
            </div>
          </div>
          <span class="chat-msg-time">Jetzt</span>
        </div>
      </div>

      <!-- Input Area -->
      <div class="chat-input-area">
        <div class="chat-input-row">
          <input type="text" id="chat-input-field" class="chat-input-field" placeholder="Suchbegriff oder Frage eingeben (z.B. 'Münzen', 'Hans Winkler', 'Hemmaberg')..." autocomplete="off">
          <button id="chat-send-btn" class="chat-send-btn" aria-label="Senden" title="Senden">
            <i class="fa-solid fa-paper-plane"></i>
          </button>
        </div>
        <div class="chat-privacy-footer" style="padding: 6px 14px; text-align: center; border-top: 1px solid var(--border-color); background: var(--bg-card); display: flex; flex-direction: column; gap: 2px;">
          <span style="font-size: 0.67rem; color: var(--text-muted); line-height: 1.35;">
            <i class="fa-solid fa-circle-check" style="color: #2e7d32;"></i> Schnelle, geprüfte Auskunft aus der IUENNA-Wissensbasis &bull; 100% Client-Side
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

  // German Stopwords
  const GERMAN_STOPWORDS = new Set([
    'was', 'ist', 'sind', 'war', 'waren', 'wird', 'werden', 'wurde', 'wurden', 'hat', 'hatte', 'hatten', 'habe', 'haben',
    'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einer', 'einem', 'eines', 'einen',
    'und', 'oder', 'aber', 'in', 'im', 'ins', 'zu', 'zum', 'zur', 'von', 'vom', 'mit', 'auf', 'aus', 'bei',
    'für', 'wo', 'wie', 'wer', 'welche', 'welcher', 'welches', 'welchem', 'gibt', 'es', 'kann', 'können', 'konnte', 'konnten', 'man',
    'soll', 'sollte', 'sollten', 'muss', 'musste', 'müssen', 'finde', 'ich', 'du', 'er', 'sie', 'wir', 'ihr', 'zeig', 'mir', 'uns', 'bitte',
    'über', 'nach', 'an', 'am', 'als', 'so', 'da', 'dann', 'auch', 'noch', 'nur', 'sehr', 'viel', 'viele', 'mehr', 'hier', 'dort',
    'wenn', 'dass', 'daß', 'ob', 'um', 'durch', 'vor', 'hinter', 'unter', 'neben', 'zwischen'
  ]);

  // Regex escape helper
  function escapeRegExp(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // Morphological stemmer for German inflections and compound words (e.g. Münzen -> Münz)
  function getGermanStem(word) {
    if (!word || typeof word !== 'string') return '';
    const w = word.toLowerCase();
    const suffixes = ['ungen', 'innen', 'ische', 'ischen', 'ischer', 'isches', 'heit', 'keit', 'schaft', 'lich', 'isch', 'ung', 'bar', 'ern', 'est', 'en', 'er', 'es', 'em', 'te', 'st', 'e', 's', 'n'];
    for (let i = 0; i < suffixes.length; i++) {
      const s = suffixes[i];
      if (w.length - s.length >= 3 && w.endsWith(s)) {
        return w.substring(0, w.length - s.length);
      }
    }
    return w;
  }

  // 3. Fast Token-based Relevance Matcher
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
        const stem = getGermanStem(tok);
        const wordRegex = new RegExp(`(^|[^a-z0-9äöüß])${escapeRegExp(tok)}($|[^a-z0-9äöüß])`, 'i');
        const stemRegex = new RegExp(`(^|[^a-z0-9äöüß])${escapeRegExp(stem)}[a-z0-9äöüß]*($|[^a-z0-9äöüß])`, 'i');

        // Boundary match on whole word or stem
        if (wordRegex.test(combined)) {
          matchScore += 6;
        } else if (stemRegex.test(combined)) {
          matchScore += 4;
        } else if (stem && combined.includes(stem)) {
          matchScore += 2;
        }

        // Title match (exact or stem)
        if (wordRegex.test(titleLower)) {
          matchScore += 16;
          strongMatch = true;
        } else if (stem && (titleLower.includes(stem) || stemRegex.test(titleLower))) {
          matchScore += 12;
          strongMatch = true;
        }

        // Keyword matches (exact, compound substring, or stem)
        for (let i = 0; i < keywords.length; i++) {
          const kwLower = (keywords[i] || '').toLowerCase();
          if (kwLower === tok) {
            matchScore += 16;
            strongMatch = true;
          } else if (wordRegex.test(kwLower)) {
            matchScore += 14;
            strongMatch = true;
          } else if (stem && (kwLower.includes(stem) || stemRegex.test(kwLower))) {
            matchScore += 10;
            strongMatch = true;
          }
        }
      });

      // Exact query phrase matching
      if (combined.includes(cleanQuery)) {
        matchScore += 15;
        strongMatch = true;
      }

      // Strong requirement: must contain at least one token or stem in title/keywords
      let tokenOverlap = false;
      tokens.forEach(tok => {
        const stem = getGermanStem(tok);
        if (titleLower.includes(tok) || (stem && titleLower.includes(stem))) {
          tokenOverlap = true;
        }
        for (let i = 0; i < keywords.length; i++) {
          const kw = (keywords[i] || '').toLowerCase();
          if (kw.includes(tok) || (stem && kw.includes(stem))) {
            tokenOverlap = true;
          }
        }
      });

      if (!tokenOverlap && matchScore < 10) return;

      // Type-specific relevance boosts
      if (type === 'synthetic_qa') matchScore += 12;
      if (type === 'foundation') matchScore += 6;
      if (type === 'subcollection') matchScore += 4;
      if (type === 'site') matchScore += 5;

      if (matchScore > 8) {
        scoredResults.push({
          item,
          type,
          title,
          text,
          score: matchScore,
          meta
        });
      }
    };

    // 1. Score Precomputed Synthetic Q&A
    (kbData.synthetic_qa || []).forEach(qa => {
      scoreItem(qa, 'synthetic_qa', qa.question, qa.answer, qa.keywords || [], {
        id: qa.id,
        category: qa.category,
        citations: qa.citations
      });
    });

    // 2. Score Scientific Foundations
    (kbData.foundations || []).forEach(f => {
      scoreItem(f, 'foundation', f.title, f.summary, f.keywords || [], {
        id: f.id,
        full_text: f.content || f.summary,
        category: f.category,
        citations: f.citations
      });
    });

    // 3. Score ARCHE Subcollections
    (kbData.subcollections || []).forEach(sc => {
      const title = sc.title || `${sc.code} - Sammlung`;
      const text = `${sc.description || ''} Enthält ca. ${sc.items || ''} Ressourcen (${sc.size || ''}).`;
      scoreItem(sc, 'subcollection', title, text, sc.keywords || [], {
        code: sc.code,
        items: sc.items,
        size: sc.size,
        pid: sc.pid,
        id: sc.id
      });
    });

    // 4. Score Archaeological Sites
    (kbData.sites || []).forEach(st => {
      const title = `${st.name} (Kärnten)`;
      const hl = Array.isArray(st.highlights) ? st.highlights.join(', ') : (st.highlights || '');
      const text = `Datierung: ${st.period || ''}. Highlights: ${hl}. Zugehörige Sammlung: ${st.subcollection || ''}.`;
      scoreItem(st, 'site', title, text, st.keywords || [], {
        name: st.name,
        period: st.period,
        items: st.items_count,
        subcollection: st.subcollection,
        id: st.id,
        geonames: st.geonames
      });
    });

    // 5. Score Graph Entities
    (kbData.graph_entities || []).slice(0, 1500).forEach(g => {
      const title = g.label || g.name || g.id;
      const text = `${g.type_label || g.type || 'Knoten'} im Wissensgraphen. ${g.parent_label ? 'Zugeordnet: ' + g.parent_label : ''} ${g.size ? 'Größe: ' + g.size : ''}`;
      scoreItem(g, 'graph_node', title, text, [g.type, g.type_label, g.id].filter(Boolean), {
        id: g.id,
        type: g.type,
        type_label: g.type_label,
        arche_url: g.arche_url,
        items: g.items,
        size: g.size,
        color: g.color
      });
    });

    // 6. Score Document Types
    (kbData.doc_types || []).forEach(d => {
      const title = d.name;
      const text = `${d.description} Anzahl: ${d.count}. Formate: ${d.formats}.`;
      scoreItem(d, 'doc_type', title, text, d.keywords || [], {
        count: d.count,
        formats: d.formats
      });
    });

    // 7. Score FAQs
    (kbData.faq || []).forEach(f => {
      scoreItem(f, 'faq', f.question, f.answer, f.keywords || [], { links: f.links });
    });

    // 8. Score Project Info
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
    const finalResults = scoredResults.slice(0, 3);
    finalResults.tokens = tokens;
    return finalResults;
  }

  // Format inline markdown
  function formatMarkdownMini(str) {
    if (!str) return '';
    return str
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
  }

  // Clip text to sentence boundary without cutting at ordinals (e.g. 3. Jh.) or abbreviations
  function clipToSentenceBoundary(text, maxLength = 260) {
    if (!text) return '';
    let cleaned = text.replace(/\s+/g, ' ').trim();
    if (cleaned.length <= maxLength) return cleaned;

    const truncated = cleaned.substring(0, maxLength);
    const regex = /([.!?]\)?)\s+[A-ZÄÖÜ0-9]/g;
    let match;
    let bestCut = -1;
    while ((match = regex.exec(truncated)) !== null) {
      const before = truncated.substring(0, match.index);
      if (!/\b\d+$/.test(before) && !/\b(z\.?\s*B|ca|vgl|bzw|u\.?\s*a|Jh|Jhs|Nr)$/i.test(before)) {
        bestCut = match.index + match[1].length;
      }
    }

    if (bestCut > 60) {
      return truncated.substring(0, bestCut).trim();
    }

    const lastSpace = truncated.lastIndexOf(' ');
    if (lastSpace > 60) {
      return truncated.substring(0, lastSpace).trim() + ' ...';
    }
    return truncated.trim() + ' ...';
  }

  // Keyword-In-Context Snippet Extractor for longer texts
  function extractRelevantContextSnippet(fullText, queryTokens, maxLength = 240) {
    queryTokens = queryTokens || [];
    if (!fullText) return '';
    let cleaned = fullText.replace(/\(\[[^\]]+\]\([^\)]+\)\)/g, '');
    cleaned = cleaned.replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1');
    cleaned = cleaned.replace(/\s+/g, ' ').trim();

    const sentences = cleaned.split(/(?<=[.?!])\s+/).map(s => s.trim()).filter(s => s.length > 8);
    if (!sentences.length) return clipToSentenceBoundary(cleaned, maxLength);

    const stems = [];
    queryTokens.forEach(t => {
      stems.push(t.toLowerCase());
      const s = getGermanStem(t);
      if (s && s.length >= 3) stems.push(s);
    });

    let bestIdx = -1;
    let bestScore = 0;
    sentences.forEach((s, idx) => {
      const sLower = s.toLowerCase();
      let score = 0;
      stems.forEach(st => {
        if (sLower.includes(st)) score += 10;
      });
      if (score > bestScore) {
        bestScore = score;
        bestIdx = idx;
      }
    });

    if (bestIdx >= 0) {
      const chosen = sentences[bestIdx];
      if (chosen.length > maxLength) {
        return clipToSentenceBoundary(chosen, maxLength);
      }
      return chosen;
    }

    return clipToSentenceBoundary(cleaned, maxLength);
  }

  // Dynamic contextual follow-up suggestions
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
      chips.push({ query: 'Warum gibt es auf dem Hemmaberg Doppelkirchen?', label: '⛪ Doppelkirchen' });
      chips.push({ query: 'Gibt es Grabungspläne zum Hemmaberg?', label: '🗺️ Grabungspläne' });
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

  // 4. Format Search Results into Clean, Clickable Cards
  function renderSearchResultCard(results) {
    // Case A: No Results Found ("Es tut mir leid, dazu habe ich leider nichts gefunden...")
    if (!results || results.length === 0) {
      return `
        <div class="chat-msg-bubble">
          <p style="margin: 0 0 6px 0; font-size: 0.88rem; font-weight: 600; color: var(--text-dark);">
            Es tut mir leid, dazu habe ich leider nichts gefunden. 🔍
          </p>
          <p style="margin: 0 0 10px 0; font-size: 0.82rem; color: var(--text-muted); line-height: 1.45;">
            Schauen Sie doch nach einem anderen Thema oder wählen Sie einen dieser Begriffe:
          </p>
          <div class="chat-chips-container">
            <button type="button" class="chat-chip" data-query="Welche Münzen gibt es?">🪙 Münzschatz Globasnitz</button>
            <button type="button" class="chat-chip" data-query="Doppelkirchen Hemmaberg">⛪ Hemmaberg</button>
            <button type="button" class="chat-chip" data-query="Gräberfeld Globasnitz">💀 Globasnitz Gräber</button>
            <button type="button" class="chat-chip" data-query="Wer war Hans Winkler?">👤 Hans Winkler</button>
            <button type="button" class="chat-chip" data-query="Villenanlage St. Stefan">🏡 Villa St. Stefan</button>
            <button type="button" class="chat-chip" data-query="Grabungspläne Hemmaberg">🗺️ Grabungspläne</button>
          </div>
        </div>
      `;
    }

    // Case B: Results Found ("Ich habe dazu Folgendes gefunden:")
    const top = results[0];
    const tokens = results.tokens || [];

    // Category Label
    const categoryBadge = top.type === 'synthetic_qa' ? 'Archäologischer Befund' :
      (top.type === 'foundation' ? 'Wissenschaftliche Grundlagen' :
      (top.type === 'subcollection' ? 'ARCHE-Sammlung' :
      (top.type === 'graph_node' ? 'ARCHE-Wissensgraph' :
      (top.type === 'site' ? 'Archäologische Fundstelle' : 'Projekt-Fakt'))));

    // Concise, focused text snippet (1-2 sentences max, no lecturing)
    let shortText = '';
    if (top.type === 'synthetic_qa') {
      shortText = clipToSentenceBoundary(top.text, 220);
    } else if (top.type === 'foundation' && top.meta && top.meta.full_text) {
      shortText = extractRelevantContextSnippet(top.meta.full_text, tokens, 220);
    } else {
      shortText = clipToSentenceBoundary(top.text, 200);
    }

    // Action Buttons ("denn die leute sollen ja auf die buttons klicken")
    let linksHtml = '';
    if (top.meta && top.meta.id) {
      linksHtml += `<button type="button" class="chat-card-btn graph-btn" onclick="if(window.focusGraphNode){window.focusGraphNode('${top.meta.id}');}"><i class="fa-solid fa-circle-nodes"></i> Im Wissensgraphen zeigen 🕸️</button>`;
    }
    linksHtml += `<a href="wma/wma.html" class="chat-card-btn gis-btn"><i class="fa-solid fa-map-location-dot"></i> In Web-GIS ansehen 🗺️</a>`;
    
    let archeUrl = 'https://id.acdh.oeaw.ac.at/iuenna';
    if (top.meta && top.meta.pid) {
      archeUrl = top.meta.pid;
    } else if (top.meta && top.meta.arche_url) {
      archeUrl = top.meta.arche_url;
    } else if (top.meta && top.meta.links && top.meta.links.length > 0) {
      const archeLink = top.meta.links.find(l => l.url && l.url.includes('acdh.oeaw.ac.at'));
      if (archeLink) archeUrl = archeLink.url;
    }
    linksHtml += `<a href="${archeUrl}" target="_blank" rel="noopener noreferrer" class="chat-card-btn arche-btn"><i class="fa-solid fa-arrow-up-right-from-square"></i> In ARCHE öffnen ↗</a>`;

    // Weitere relevante Treffer im Wissensgraphen
    let secondaryHtml = '';
    if (results.length > 1) {
      secondaryHtml = `
        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border-color); font-size: 0.78rem;">
          <span style="color: var(--text-muted); font-weight: 600;">Weitere relevante Treffer im Wissensgraphen:</span>
          <ul style="margin: 4px 0 0 16px; padding: 0; color: var(--text-dark);">
            ${results.slice(1, 4).map(r => `
              <li style="margin-bottom: 3px;">
                <strong>${escapeHtml(r.title)}</strong>
                ${r.meta && r.meta.id ? ` <a href="javascript:void(0)" onclick="if(window.focusGraphNode){window.focusGraphNode('${r.meta.id}');}" style="color: var(--secondary); text-decoration: underline; margin-left: 4px; font-weight: 600;">[Im Graph 🕸️]</a>` : ''}
              </li>
            `).join('')}
          </ul>
        </div>
      `;
    }

    // Dynamic contextual follow-up suggestions
    const followUpHtml = generateFollowUpChips(top);

    return `
      <div class="chat-msg-bubble">
        <!-- 1. Conversational Intro -->
        <p class="chat-intro-line" style="margin: 0 0 8px 0; font-size: 0.88rem; font-weight: 600; color: var(--text-dark); display: flex; align-items: center; gap: 6px;">
          <i class="fa-solid fa-magnifying-glass" style="color: var(--secondary); font-size: 0.85rem;"></i>
          <span>Ich habe dazu Folgendes gefunden:</span>
        </p>

        <!-- 2. Crisp, short result card -->
        <div class="chat-result-card" style="background: rgba(184, 142, 62, 0.05); border-left: 3px solid var(--secondary); padding: 9px 12px; border-radius: var(--radius-sm, 4px); margin-bottom: 8px;">
          <div style="font-size: 0.68rem; font-weight: 700; text-transform: uppercase; color: var(--secondary); letter-spacing: 0.04em; margin-bottom: 2px;">
            ${categoryBadge}
          </div>
          <h4 style="margin: 0 0 4px 0; font-size: 0.93rem; font-family: var(--font-header); color: var(--primary);">
            ${escapeHtml(top.title)}
          </h4>
          <p style="margin: 0; font-size: 0.84rem; line-height: 1.45; color: var(--text-dark);">
            ${formatMarkdownMini(shortText)}
          </p>
          ${top.meta && top.meta.citations && top.meta.citations.length > 0 ? `
            <div style="margin-top: 5px; font-size: 0.72rem; color: var(--text-muted);">
              <i class="fa-solid fa-feather-pointed"></i> Lit.: ${escapeHtml(top.meta.citations.slice(0, 2).join('; '))}
            </div>
          ` : ''}
        </div>

        <!-- 3. Prominent Action Buttons -->
        <div class="chat-card-links">
          ${linksHtml}
        </div>

        <!-- 4. Related Hits & Follow-ups -->
        ${secondaryHtml}
        ${followUpHtml}
      </div>
    `;
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
    if (!str && str !== 0) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // 6. Conversational Handler (Instant, deterministic, zero-lag)
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
            <p><i class="fa-solid fa-triangle-exclamation" style="color: #b88e3e;"></i> Die Sammlungs-Wissensbasis konnte nicht geladen werden. Bitte prüfen Sie Ihre Verbindung oder laden Sie die Seite neu.</p>
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
              Ich helfe Ihnen beim schnellen Auffinden von archäologischen Fundstellen, Grabungsplänen und Fotos aus dem Jauntal.
            </p>
            <p style="margin-top: 6px; font-size: 0.82rem; color: var(--text-muted);">
              Wonach suchen Sie? Sie können z.&nbsp;B. nach <em>„Münzen“</em>, <em>„Hemmaberg Pläne“</em>, <em>„Hans Winkler“</em> oder <em>„Globasnitz Gräber“</em> fragen.
            </p>
          </div>
        `);
      }, 150);
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
              Klicken Sie gerne auf die Buttons in den Treffern, um die Funde direkt im Wissensgraphen, im Web-GIS oder im ARCHE-Repositorium zu erkunden!
            </p>
          </div>
        `);
      }, 150);
      return;
    }

    // Dialog Intent C: Help / Overview
    if (/^(hilfe|help|was kannst du|wer bist du|funktionen)$/i.test(cleanQ)) {
      setTimeout(() => {
        if (thisRequestId !== currentRequestId) return;
        removeTypingIndicator();
        appendBotMessage(`
          <div class="chat-msg-bubble">
            <p><strong>So funktioniert die Suche:</strong> 🔍</p>
            <ul style="margin: 6px 0 0 16px; padding: 0; font-size: 0.84rem; line-height: 1.5;">
              <li><strong>Suchbegriff oder Frage eingeben:</strong> z.&nbsp;B. <em>„Welche Münzen gibt es?“</em> oder <em>„Pläne Hemmaberg“</em>.</li>
              <li><strong>Auf die Buttons klicken:</strong> Jeder Treffer führt Sie direkt zu den Daten:
                <ul style="margin: 4px 0 0 16px;">
                  <li>🕸️ <em>Im Wissensgraphen zeigen</em> &ndash; zentriert und markiert das Objekt im Graphen.</li>
                  <li>🗺️ <em>In Web-GIS ansehen</em> &ndash; öffnet die Fundstelle auf der interaktiven Karte.</li>
                  <li>↗️ <em>In ARCHE öffnen</em> &ndash; zeigt Originaldokumente &amp; Pläne im Repositorium.</li>
                </ul>
              </li>
            </ul>
          </div>
        `);
      }, 150);
      return;
    }

    // Multi-turn Pronoun & Topic Expansion (e.g. "Gibt es dazu Pläne?" -> append lastTopic)
    let effectiveQuery = query;
    if (dialogueState.lastTopic && /\b(dazu|dort|davon|mehr|weitere|auch|pläne|fotos|bilder|gräber)\b/i.test(query) && !query.toLowerCase().includes(dialogueState.lastTopic.toLowerCase())) {
      effectiveQuery = `${query} ${dialogueState.lastTopic}`;
    }

    // 3. Search Knowledge Base (with stemmed token matching)
    const results = searchKnowledgeBase(effectiveQuery);

    // Update conversation topic state from top match
    if (results && results.length > 0) {
      const top = results[0];
      const txt = ((top.title || '') + ' ' + (top.text || '')).toLowerCase();
      if (txt.includes('hemmaberg')) dialogueState.lastTopic = 'Hemmaberg';
      else if (txt.includes('globasnitz')) dialogueState.lastTopic = 'Globasnitz';
      else if (txt.includes('st. stefan') || txt.includes('barbius') || txt.includes('winkler')) dialogueState.lastTopic = 'St. Stefan';
      else if (txt.includes('jaunstein')) dialogueState.lastTopic = 'Jaunstein';
      else if (txt.includes('qgis') || txt.includes('geodaten')) dialogueState.lastTopic = 'Geodaten';
    }

    // Fast, natural delay (180ms) for smooth responsive feel
    setTimeout(() => {
      if (thisRequestId !== currentRequestId) return;
      removeTypingIndicator();
      const cardHtml = renderSearchResultCard(results);
      appendBotMessage(cardHtml);
    }, 180);
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

    // Suggestion Chips Click (delegated)
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
    renderCard: renderSearchResultCard,
    getKbData: () => kbData,
    setKbData: (d) => { kbData = d; }
  };

})();
