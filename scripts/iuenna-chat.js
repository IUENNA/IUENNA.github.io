/**
 * iuenna-chat.js
 * --------------
 * Intuitiver Sammlungs- & Recherche-Assistent für das IUENNA-Projekt.
 * 
 * Sucht in Echtzeit in der Graphendatenbank (21.071 Knoten), im Web-GIS
 * und in den ARCHE-Sammlungen nach Metadaten.
 * 
 * - Bei Treffern: Ein kleines In-Browser-Sprachmodell (Qwen 2.5 0.5B via WebGPU/WASM)
 *   formuliert aus den konkreten Metadaten eine kurze 1-2 Satz-Zusammenfassung.
 * - Bei 0 Treffern: Keine Spekulation oder Fachauskunft, sondern direkte Rückmeldung
 *   ("Die Anfrage lieferte leider keine Ergebnisse in den Beständen").
 * - Klare Aktions-Buttons: Direkte Verlinkung in den Wissensgraphen, ins Web-GIS & nach ARCHE.
 * 
 * 100% Client-Side. Keine API-Keys auf GitHub.
 */

(function(global) {
  'use strict';

  const root = typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : global);

  // Dynamic base path resolution (supports root level pages and subfolder pages like graph/ or wma/)
  let basePath = '';
  const currentScript = document.currentScript || document.querySelector('script[src*="iuenna-chat.js"]');
  if (currentScript && currentScript.getAttribute('src')) {
    const srcAttr = currentScript.getAttribute('src');
    if (srcAttr.startsWith('../')) {
      basePath = '../';
    } else if (srcAttr.startsWith('/')) {
      basePath = '/';
    }
  }
  if (!basePath) {
    const p = window.location.pathname.toLowerCase();
    if (p.includes('/graph/') || p.endsWith('/graph') || p.endsWith('/graph.html') || p.includes('/wma/')) {
      basePath = '../';
    }
  }

  const isGraphPage = window.location.pathname.includes('/graph/') || 
                      window.location.pathname.endsWith('/graph') ||
                      window.location.pathname.endsWith('graph.html') ||
                      (document.getElementById('cy') !== null && document.getElementById('lodSlider') !== null);

  // Configuration
  const KB_URL = basePath + 'data/iuenna_kb.json';
  const STORAGE_KEY_OPEN = 'iuenna_chat_open';
  const STORAGE_KEY_HISTORY = 'iuenna_chat_history';
  
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

  // Session Storage Helpers for Cross-Page State Persistence
  function saveChatState() {
    try {
      const chatWin = document.getElementById('iuenna-chat-window');
      const isOpen = chatWin && chatWin.classList.contains('chat-open');
      sessionStorage.setItem(STORAGE_KEY_OPEN, isOpen ? 'true' : 'false');

      const messagesContainer = document.getElementById('chat-messages');
      if (messagesContainer) {
        const clone = messagesContainer.cloneNode(true);
        const typingEl = clone.querySelector('#chat-typing-indicator-el');
        if (typingEl) typingEl.remove();
        sessionStorage.setItem(STORAGE_KEY_HISTORY, clone.innerHTML);
      }
    } catch (e) {}
  }

  function restoreChatState() {
    try {
      const savedHistory = sessionStorage.getItem(STORAGE_KEY_HISTORY);
      const messagesContainer = document.getElementById('chat-messages');
      if (savedHistory && messagesContainer && savedHistory.trim().length > 0) {
        messagesContainer.innerHTML = savedHistory;
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }

      const wasOpen = sessionStorage.getItem(STORAGE_KEY_OPEN) === 'true';
      if (wasOpen) {
        const chatWin = document.getElementById('iuenna-chat-window');
        if (chatWin) {
          chatWin.classList.add('chat-open');
        }
      }
    } catch (e) {}
  }

  function showChatToast(msg) {
    const msgArea = document.getElementById('chat-messages');
    if (!msgArea) return;
    const toast = document.createElement('div');
    toast.style.cssText = 'align-self: center; margin: 6px 0; font-size: 0.74rem; background: rgba(30, 58, 138, 0.08); color: #1e3a8a; border: 1px solid rgba(30, 58, 138, 0.2); border-radius: 12px; padding: 4px 12px; animation: fadeIn 0.2s ease; display: flex; align-items: center; gap: 6px;';
    toast.innerHTML = `<i class="fa-solid fa-circle-check" style="color: #1e3a8a;"></i> <em>${msg}</em>`;
    msgArea.appendChild(toast);
    msgArea.scrollTop = msgArea.scrollHeight;
    setTimeout(() => { toast.remove(); }, 3500);
  }

  function getWelcomeMessageHtml() {
    return `
      <!-- Welcome Message -->
      <div class="chat-msg bot">
        <div class="chat-msg-bubble">
          <p><strong>Willkommen beim IUENNA Sammlungs-Assistenten!</strong> 🏺</p>
          <p style="margin-top: 6px; font-size: 0.84rem; line-height: 1.45;">
            Stellen Sie eine Frage oder suchen Sie nach Objekten, Fundstellen und Plänen. Die Treffer führen Sie direkt zu den Daten im <strong>Wissensgraphen</strong>, im <strong>Web-GIS</strong> und in <strong>ARCHE</strong>.
          </p>
          <div class="chat-byoai-welcome-box" style="margin-top: 8px; padding: 7px 10px; background: rgba(106, 27, 154, 0.06); border: 1px solid rgba(106, 27, 154, 0.2); border-radius: 4px; font-size: 0.79rem; line-height: 1.4; color: #4a148c;">
            <i class="fa-solid fa-microchip" style="color: #6a1b9a;"></i> <strong>Bring Your Own AI (BYOAI):</strong> Sie möchten lieber Ihre eigene KI (Claude, ChatGPT, Ollama etc.) nutzen? Alle Bestände stehen offen über unser <a href="${basePath}byoai.html" target="_blank" rel="noopener noreferrer" style="color: #6a1b9a; font-weight: 700; text-decoration: underline;">Model Context Protocol (MCP) &amp; OpenAPI</a> bereit.
          </div>
          <div class="chat-chips-container" style="margin-top: 8px;">
            <button type="button" class="chat-chip chat-chip-byoai" data-query="Was ist BYOAI?"><i class="fa-solid fa-microchip"></i> Was ist BYOAI?</button>
            <button type="button" class="chat-chip" data-query="Welche Literatur gibt es?" style="background: rgba(192, 57, 43, 0.07); border-color: rgba(192, 57, 43, 0.25); color: #c0392b; font-weight: 600;"><i class="fa-solid fa-book-bookmark"></i> 📚 Literatur (Zotero)</button>
            <button type="button" class="chat-chip" data-query="Wer war Sabine Ladstätter?">👤 Sabine Ladstätter</button>
            <button type="button" class="chat-chip" data-query="Wer ist Michaela Binder?">👤 Michaela Binder</button>
            <button type="button" class="chat-chip" data-query="Wer ist Elke Profant?">👤 Elke Profant</button>
            <button type="button" class="chat-chip" data-query="Wer ist Magdalena Srienc?">👤 Magdalena Srienc</button>
            <button type="button" class="chat-chip" data-query="Welche Münzen gibt es?">🪙 Münzschatz Globasnitz</button>
            <button type="button" class="chat-chip" data-query="Wer war Hans Winkler?">👤 Hans Winkler</button>
            <button type="button" class="chat-chip" data-query="Doppelkirchen Hemmaberg">⛪ Hemmaberg Doppelkirchen</button>
            <button type="button" class="chat-chip" data-query="Ostgotisches Gräberfeld Globasnitz">💀 Ostgotisches Gräberfeld</button>
            <button type="button" class="chat-chip" data-query="Villenanlage St. Stefan">🏡 Villa St. Stefan</button>
            <button type="button" class="chat-chip" data-query="QGIS Geodaten">🗺️ QGIS GeoPackage</button>
          </div>
        </div>
        <span class="chat-msg-time">Jetzt</span>
      </div>
    `;
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
            <div style="display: flex; align-items: center; gap: 6px; margin-top: 3px; flex-wrap: wrap;">
              <span id="chat-model-status" style="display: inline-flex; align-items: center; gap: 4px; font-size: 0.67rem; padding: 1px 6px; border-radius: 3px; background: rgba(255,255,255,0.16);">
                <i class="fa-solid fa-bolt" style="color: #4fc3f7;"></i> Schnellsuche &bull; Metadaten
              </span>
              <a href="${basePath}byoai.html" target="_blank" rel="noopener noreferrer" class="chat-header-byoai-badge" title="Bring Your Own AI – Eigene KI anbinden">
                <i class="fa-solid fa-microchip"></i> BYOAI Hub ↗
              </a>
            </div>
          </div>
        </div>
        <div class="chat-header-actions" style="display: flex; align-items: center; gap: 6px;">
          <button class="chat-header-action-btn" id="chat-reset-btn" aria-label="Chat zurücksetzen" title="Verlauf leeren &amp; neu starten" style="background: none; border: none; color: rgba(255,255,255,0.75); cursor: pointer; padding: 4px 6px; font-size: 0.85rem; border-radius: 4px; transition: color 0.15s ease;">
            <i class="fa-solid fa-arrow-rotate-left"></i>
          </button>
          <button class="chat-close-btn" id="chat-close-btn" aria-label="Schließen" title="Schließen (ESC)">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
      </div>

      <!-- Messages Area -->
      <div class="chat-messages" id="chat-messages">
        ${getWelcomeMessageHtml()}
      </div>

      <!-- Input Area -->
      <div class="chat-input-area">
        <div class="chat-input-row">
          <input type="text" id="chat-input-field" class="chat-input-field" placeholder="Suchbegriff eingeben (z.B. 'Münzen', 'Sabine Ladstätter', 'Michaela Binder', 'Hans Winkler')..." autocomplete="off">
          <button id="chat-send-btn" class="chat-send-btn" aria-label="Senden" title="Senden">
            <i class="fa-solid fa-paper-plane"></i>
          </button>
        </div>
        <div class="chat-privacy-footer" style="padding: 6px 14px; text-align: center; border-top: 1px solid var(--border-color); background: var(--bg-card); display: flex; flex-direction: column; gap: 2px;">
          <span style="font-size: 0.67rem; color: var(--text-muted); line-height: 1.35;">
            <i class="fa-solid fa-circle-check" style="color: #2e7d32;"></i> 100% Client-Side Metadaten-Recherche &bull; DSGVO-konform &bull; <a href="${basePath}byoai.html" target="_blank" rel="noopener noreferrer" style="color: #6a1b9a; font-weight: 600; text-decoration: underline;"><i class="fa-solid fa-microchip"></i> BYOAI: Eigene KI anbinden ↗</a>
          </span>
        </div>
      </div>
    `;
    document.body.appendChild(chatWindow);

    restoreChatState();
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
    'für', 'wo', 'wie', 'wer', 'welche', 'welcher', 'welches', 'welchem', 'welchen', 'gibt', 'gibts', 'gab', 'gaben', 'gäbe', 'es', 'kann', 'können', 'konnte', 'konnten', 'man',
    'soll', 'sollte', 'sollten', 'muss', 'musste', 'müssen', 'finde', 'ich', 'du', 'er', 'sie', 'wir', 'ihr', 'zeig', 'mir', 'uns', 'bitte',
    'über', 'nach', 'an', 'am', 'als', 'so', 'da', 'dann', 'auch', 'noch', 'nur', 'sehr', 'viel', 'viele', 'mehr', 'hier', 'dort',
    'wenn', 'dass', 'daß', 'ob', 'um', 'durch', 'vor', 'hinter', 'unter', 'neben', 'zwischen',
    'etwas', 'erzähl', 'erzähle', 'erzählen', 'bericht', 'berichte', 'berichten'
  ]);

  // Regex escape helper
  function escapeRegExp(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // Morphological stemmer for German inflections
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

  // 4. Token-based Relevance Matcher across Graph Entities & Metadata
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
    const scoreItem = (rawItem, type, title, meta = {}, keywords = []) => {
      const combined = `${title} ${keywords.join(' ')} ${meta.place || ''} ${meta.period || ''} ${meta.type_label || ''}`.toLowerCase();
      const titleLower = title.toLowerCase();

      let matchScore = 0;
      let strongMatch = false;
      let matchedTokensCount = 0;

      tokens.forEach(tok => {
        const stem = getGermanStem(tok);
        const wordRegex = new RegExp(`(^|[^a-z0-9äöüß])${escapeRegExp(tok)}($|[^a-z0-9äöüß])`, 'i');
        const stemRegex = new RegExp(`(^|[^a-z0-9äöüß])${escapeRegExp(stem)}[a-z0-9äöüß]*($|[^a-z0-9äöüß])`, 'i');

        let tokenScore = 0;
        let tokenMatched = false;

        // Combined text match
        if (wordRegex.test(combined)) {
          tokenScore += 6;
          tokenMatched = true;
        } else if (stemRegex.test(combined)) {
          tokenScore += 4;
          tokenMatched = true;
        } else if (stem && stem.length >= 4 && combined.includes(stem)) {
          tokenScore += 2;
          tokenMatched = true;
        }

        // Title match (high value)
        if (wordRegex.test(titleLower)) {
          tokenScore += 18;
          strongMatch = true;
          tokenMatched = true;
        } else if (stem && (titleLower.includes(stem) || stemRegex.test(titleLower))) {
          tokenScore += 12;
          strongMatch = true;
          tokenMatched = true;
        }

        // Keyword match - CAP score per token so repeating the same keyword doesn't inflate!
        let bestKwScore = 0;
        for (let i = 0; i < keywords.length; i++) {
          const kwLower = (keywords[i] || '').toLowerCase();
          if (kwLower === tok) {
            bestKwScore = Math.max(bestKwScore, 18);
            strongMatch = true;
            tokenMatched = true;
          } else if (wordRegex.test(kwLower)) {
            bestKwScore = Math.max(bestKwScore, 15);
            strongMatch = true;
            tokenMatched = true;
          } else if (stem && (kwLower.includes(stem) || stemRegex.test(kwLower))) {
            bestKwScore = Math.max(bestKwScore, 10);
            strongMatch = true;
            tokenMatched = true;
          }
        }
        tokenScore += bestKwScore;

        if (tokenMatched) {
          matchedTokensCount++;
          matchScore += tokenScore;
        }
      });

      // Multi-token query bonus & penalty: strongly favor items matching ALL query terms
      if (tokens.length > 1) {
        const coverageRatio = matchedTokensCount / tokens.length;
        if (coverageRatio === 1.0) {
          // 100% token coverage bonus
          matchScore += 60;
        } else if (matchedTokensCount > 1) {
          matchScore += matchedTokensCount * 20;
        } else if (coverageRatio < 0.6) {
          // If user queried multiple distinct terms and this item only matched 1 of them
          matchScore = Math.floor(matchScore * 0.45);
        }
      }

      if (titleLower === cleanQuery) {
        matchScore += 40;
        strongMatch = true;
      } else if (titleLower.includes(cleanQuery)) {
        matchScore += 25;
        strongMatch = true;
      } else if (combined.includes(cleanQuery)) {
        matchScore += 15;
      }

      // Overlap guard (strictly requires token or stem boundary match in title or keywords)
      let tokenOverlap = false;
      tokens.forEach(tok => {
        const stem = getGermanStem(tok);
        const tokRegex = new RegExp(`(^|[^a-z0-9äöüß])${escapeRegExp(tok)}`, 'i');
        const stemRegex = (stem && stem.length >= 4) ? new RegExp(`(^|[^a-z0-9äöüß])${escapeRegExp(stem)}`, 'i') : null;
        if (tokRegex.test(titleLower) || (stemRegex && stemRegex.test(titleLower))) {
          tokenOverlap = true;
        }
        for (let i = 0; i < keywords.length; i++) {
          const kw = (keywords[i] || '').toLowerCase();
          if (tokRegex.test(kw) || (stemRegex && stemRegex.test(kw))) {
            tokenOverlap = true;
          }
        }
      });

      if (!tokenOverlap || matchScore < 10) return;

      if (type === 'find_complex') matchScore += 35;
      if (type === 'synthetic_qa' || type === 'faq') matchScore += 25;
      if (type === 'doc_type') matchScore += 20;
      if (type === 'subcollection') matchScore += 16;
      if (type === 'site') matchScore += 14;
      if (type === 'folder') {
        matchScore += 4;
        if (rawItem && rawItem.type === 'folder_l2') matchScore += 4;
        else if (rawItem && rawItem.type === 'folder_l3') matchScore += 2;
        if (rawItem && rawItem.items && rawItem.items > 100) matchScore += 3;
        // Demote raw secondary container titles
        if (/^(klarsichthülle|hülle|ordner|mischordner|kopie|scan|cd)\b/i.test(title)) {
          matchScore -= 12;
        }
      }

      if (matchScore > 8) {
        scoredResults.push({
          rawItem,
          type,
          title,
          meta,
          score: matchScore,
          strongMatch
        });
      }
    };

    // 1. Authoritative Archaeological Find Complexes
    const findComplexes = [
      {
        title: 'Münzschatzfund von Globasnitz',
        type_label: 'Archäologischer Fundkomplex',
        place: 'Globasnitz',
        period: 'Spätantike (4. Jh. n. Chr.)',
        items: '322 römische Münzen',
        pid: 'https://hdl.handle.net/21.11115/0000-0016-7B30-8',
        arche_url: 'https://hdl.handle.net/21.11115/0000-0016-7B30-8',
        id: 'col_1792169',
        category: 'coins',
        lat: 46.55694,
        lng: 14.70278,
        keywords: ['münzen', 'münzschatz', 'hortfund', 'globasnitz', '322', 'bronzemünzen', 'geld', 'numismatik', 'münzfund']
      },
      {
        title: 'Ostgotisches Gräberfeld Globasnitz',
        type_label: 'Archäologischer Befund',
        place: 'Globasnitz',
        period: 'Spätantike / Ostgotenzeit (5.–6. Jh. n. Chr.)',
        items: '440 dokumentierte Gräber',
        pid: 'https://hdl.handle.net/21.11115/0000-0016-7B30-8',
        arche_url: 'https://hdl.handle.net/21.11115/0000-0016-7B30-8',
        id: 'col_1792186',
        category: 'graves',
        lat: 46.55694,
        lng: 14.70278,
        keywords: ['ostgotisches gräberfeld', 'ostgoten', 'ostgotisch', 'gräberfeld', 'gräber', 'bestattungen', 'skelette', 'globasnitz', 'ostgräberfeld', 'binder', 'srienc', 'turmschädel', 'schädeldeformation']
      },
      {
        title: 'Doppelkirchenanlage & Pilgerheiligtum Hemmaberg',
        type_label: 'Archäologischer Befund',
        place: 'Hemmaberg',
        period: 'Spätantike (5.–6. Jh. n. Chr.)',
        items: '5 Kirchenbauten & Mosaiken',
        pid: 'https://hdl.handle.net/21.11115/0000-0016-7B3B-D',
        arche_url: 'https://hdl.handle.net/21.11115/0000-0016-7B3B-D',
        id: 'col_1792212',
        category: 'architecture',
        lat: 46.55269,
        lng: 14.66768,
        keywords: ['doppelkirchen', 'doppelkirche', 'hemmaberg', 'kirchen', 'mosaik', 'mosaiken', 'ladstätter', 'binder', 'pilgerzentrum', 'pilgerheiligtum', 'baptisterium']
      },
      {
        title: 'Römische Großvilla & Badeanlage St. Stefan',
        type_label: 'Archäologischer Befund',
        place: 'Sankt Stefan im Jauntal',
        period: 'Römische Kaiserzeit (1.–4. Jh. n. Chr.)',
        items: '2 ha Villenkomplex & Therme',
        pid: 'https://hdl.handle.net/21.11115/0000-0016-7B53-1',
        arche_url: 'https://hdl.handle.net/21.11115/0000-0016-7B53-1',
        id: 'col_1792411',
        category: 'architecture',
        lat: 46.59100,
        lng: 14.77300,
        keywords: ['villa', 'villenanlage', 'st. stefan', 'stefan', 'badeanlage', 'hypokaust', 'therme', 'šteben', 'großvilla', 'barbius']
      },
      {
        title: 'Frühmittelalterliches Reihengräberfeld Jaunstein',
        type_label: 'Archäologischer Befund',
        place: 'Jaunstein',
        period: 'Frühmittelalter (8.–10. Jh. n. Chr.)',
        items: 'Reihengräber mit Korbgehängen & Schmuck',
        pid: 'https://hdl.handle.net/21.11115/0000-0016-7B4B-B',
        arche_url: 'https://hdl.handle.net/21.11115/0000-0016-7B4B-B',
        id: 'col_1792303',
        category: 'graves',
        lat: 46.55936,
        lng: 14.67102,
        keywords: ['jaunstein', 'gräberfeld', 'reihengräber', 'köttlach', 'korbgehänge', 'frühmittelalter', 'karantanen', 'trachtschmuck']
      },
      {
        title: 'Archivalien & Nachlass Dr. Hans Winkler',
        type_label: 'Historischer Forschungsnachlass',
        place: 'St. Stefan / Jauntal',
        period: 'Forschungsgeschichte (frühes 20. Jh.)',
        items: '475 Archivalien, Skizzen & Tagebücher',
        pid: 'https://hdl.handle.net/21.11115/0000-0016-7B59-B',
        arche_url: 'https://hdl.handle.net/21.11115/0000-0016-7B59-B',
        id: 'col_1792752',
        category: 'persons',
        lat: 46.59100,
        lng: 14.77300,
        keywords: ['winkler', 'hans winkler', 'notar', 'eberndorf', 'skizzen', 'tagebuch', 'tagebücher', 'nachlass', 'skizzenbuch', 'pionier']
      }
    ];

    findComplexes.forEach(fc => {
      scoreItem(fc, 'find_complex', fc.title, fc, fc.keywords);
    });

    // 2. Score ARCHE Subcollections (authoritative collections)
    const siteCoordsMap = {
      'HB': { lat: 46.55269, lng: 14.66768, place: 'Hemmaberg' },
      'GLO': { lat: 46.55694, lng: 14.70278, place: 'Globasnitz' },
      'JAU': { lat: 46.55936, lng: 14.67102, place: 'Jaunstein' },
      'STEF': { lat: 46.59100, lng: 14.77300, place: 'Sankt Stefan im Jauntal' },
      'RET': { lat: 46.59100, lng: 14.77300, place: 'St. Stefan / Hemmaberg' },
      'BIO': { lat: 46.55694, lng: 14.70278, place: 'Jauntal' }
    };

    (kbData.subcollections || []).forEach(sc => {
      const geo = siteCoordsMap[sc.code] || { place: 'Jauntal' };
      const kw = [...(sc.keywords || [])];
      if (sc.code === 'RET') {
        kw.push('winkler', 'hans winkler', 'notar', 'skizzen', 'tagebücher', 'nachlass');
      }
      scoreItem(sc, 'subcollection', sc.title || `${sc.code} - Sammlung`, {
        title: sc.title || `${sc.code} - Sammlung`,
        type_label: 'ARCHE-Subcollection',
        place: geo.place,
        lat: geo.lat,
        lng: geo.lng,
        items: sc.items ? `${sc.items} Objekte` : null,
        size: sc.size || '',
        pid: sc.pid,
        arche_url: sc.pid,
        id: sc.id
      }, kw);
    });

    // 3. Score Archaeological Sites (with precise coordinates and ARCHE collection nodes)
    const siteGeoDetails = {
      'site_hemmaberg': { node_id: 'col_1792212', lat: 46.55269, lng: 14.66768, pid: 'https://hdl.handle.net/21.11115/0000-0016-7B3B-D' },
      'site_globasnitz': { node_id: 'col_1792169', lat: 46.55694, lng: 14.70278, pid: 'https://hdl.handle.net/21.11115/0000-0016-7B30-8' },
      'site_sankt_stefan': { node_id: 'col_1792411', lat: 46.59100, lng: 14.77300, pid: 'https://hdl.handle.net/21.11115/0000-0016-7B53-1' },
      'site_jaunstein': { node_id: 'col_1792303', lat: 46.55936, lng: 14.67102, pid: 'https://hdl.handle.net/21.11115/0000-0016-7B4B-B' }
    };

    (kbData.sites || []).forEach(st => {
      const geo = siteGeoDetails[st.id] || {};
      scoreItem(st, 'site', `${st.name} (Kärnten)`, {
        title: `${st.name} (Kärnten)`,
        type_label: 'Archäologische Fundstelle',
        place: st.name,
        lat: geo.lat,
        lng: geo.lng,
        period: st.period || '',
        items: st.items_count ? `${st.items_count} Ressourcen` : null,
        id: geo.node_id || st.id || 'iuenna_root',
        pid: geo.pid || 'https://id.acdh.oeaw.ac.at/iuenna',
        arche_url: geo.pid || 'https://id.acdh.oeaw.ac.at/iuenna',
        geonames: st.geonames
      }, st.keywords || []);
    });

    // 4. Score Graph Entities (All 21,071 nodes, prioritizing collections & primary archival folders)
    (kbData.graph_entities || []).forEach(g => {
      const label = g.label || g.name || g.id;
      if (!label) return;
      const isCol = (g.id && g.id.startsWith('col_')) || (g.type && g.type.includes('folder'));
      const kw = [g.type, g.type_label, g.id].filter(Boolean);
      const lLower = label.toLowerCase();
      if (lLower.includes('winkler')) {
        kw.push('winkler', 'hans winkler', 'notar', 'eberndorf', 'skizzen');
      }
      if (lLower.includes('münz')) {
        kw.push('münzen', 'münzschatz', 'hortfund');
      }

      let extraType = isCol ? 'folder' : 'graph_node';
      let place = null;
      let lat = null;
      let lng = null;
      if (lLower.includes('hemmaberg')) { place = 'Hemmaberg'; lat = 46.55269; lng = 14.66768; }
      else if (lLower.includes('globasnitz')) { place = 'Globasnitz'; lat = 46.55694; lng = 14.70278; }
      else if (lLower.includes('stefan') || lLower.includes('winkler')) { place = 'St. Stefan / Jauntal'; lat = 46.59100; lng = 14.77300; }
      else if (lLower.includes('jaunstein')) { place = 'Jaunstein'; lat = 46.55936; lng = 14.67102; }

      scoreItem(g, extraType, label, {
        title: label,
        type_label: g.type_label || (isCol ? 'ARCHE-Sammlung' : 'Knoten im Wissensgraph'),
        place: place,
        lat: lat,
        lng: lng,
        items: g.items ? `${g.items} Items` : null,
        size: g.size || null,
        arche_url: g.arche_url,
        pid: g.arche_url || 'https://id.acdh.oeaw.ac.at/iuenna',
        id: g.id
      }, kw);
    });

    // 5. Score Document Types (Pläne, Fotos, GeoPackages etc.)
    (kbData.doc_types || []).forEach(d => {
      const extraKw = ['hemmaberg', 'jaunstein', 'globasnitz', 'st. stefan', 'jauntal'];
      let dNodeId = 'iuenna_root';
      let dPid = 'https://hdl.handle.net/21.11115/0000-0016-7B39-F';
      if (d.id === 'doc_plans') {
        extraKw.push('grabungsplan', 'grabungspläne', 'grabungsdokumentation', 'profilschnitt', 'steinpläne', 'aufmaßplan');
        dNodeId = 'col_1792211';
        dPid = 'https://hdl.handle.net/21.11115/0000-0016-7B3A-E';
      } else if (d.id === 'doc_photos') {
        extraKw.push('foto', 'fotos', 'fotografien', 'aufnahme');
        dNodeId = 'col_1792167';
        dPid = 'https://hdl.handle.net/21.11115/0000-0016-7B2F-B';
      } else if (d.id === 'doc_geodata') {
        extraKw.push('qgis', 'arcgis', 'vektordaten', 'layer');
        dNodeId = 'col_1792211';
        dPid = 'https://hdl.handle.net/21.11115/0000-0016-7B3A-E';
      }
      scoreItem(d, 'doc_type', d.name, {
        title: d.name,
        type_label: 'Materialgruppe',
        items: d.count ? `${d.count} Dokumente` : null,
        size: d.formats ? `Formate: ${d.formats}` : null,
        id: dNodeId,
        pid: dPid,
        arche_url: dPid
      }, [...(d.keywords || []), ...extraKw]);
    });

    // 6. Score Synthetic Q&A pairs (curated expert scientific syntheses)
    (kbData.synthetic_qa || []).forEach(qa => {
      const qText = qa.question || '';
      const variations = qa.variations || [];
      const keywords = qa.keywords || [];
      const citations = qa.citations || [];
      const ans = qa.answer || '';
      const allKeywords = [...keywords, ...variations, ...(citations || [])];

      let place = 'Jauntal';
      let lat = 46.55694;
      let lng = 14.70278;
      const qLower = (qText + ' ' + allKeywords.join(' ')).toLowerCase();
      if (qLower.includes('hemmaberg')) { place = 'Hemmaberg'; lat = 46.55269; lng = 14.66768; }
      else if (qLower.includes('globasnitz')) { place = 'Globasnitz'; lat = 46.55694; lng = 14.70278; }
      else if (qLower.includes('st. stefan') || qLower.includes('stefan')) { place = 'Sankt Stefan im Jauntal'; lat = 46.59100; lng = 14.77300; }
      else if (qLower.includes('jaunstein')) { place = 'Jaunstein'; lat = 46.55936; lng = 14.67102; }
      else if (qLower.includes('tscherberg') || qLower.includes('katharinakogel')) { place = 'Tscherberg / St. Stefan'; lat = 46.59100; lng = 14.77300; }

      let archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B39-F';
      if (qa.graph_node_id === 'col_1792169') archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B30-8';
      else if (qa.graph_node_id === 'col_1792186') archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B30-8';
      else if (qa.graph_node_id === 'col_1792212') archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B3B-D';
      else if (qa.graph_node_id === 'col_1792303') archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B4B-B';
      else if (qa.graph_node_id === 'col_1792411') archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B53-1';
      else if (qa.graph_node_id === 'col_1792572' || qa.graph_node_id === 'col_1792752') archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B59-B';

      scoreItem(qa, 'synthetic_qa', qText, {
        title: qText,
        type_label: 'Forschungssynthese',
        place: place,
        lat: lat,
        lng: lng,
        qa_answer: ans,
        citations: citations,
        id: qa.graph_node_id || 'iuenna_root',
        pid: archePid,
        arche_url: archePid
      }, allKeywords);
    });

    // 7. Score FAQs (official project & research answers)
    (kbData.faq || []).forEach(f => {
      const qText = f.question || '';
      const keywords = f.keywords || [];
      const ans = f.answer || '';
      const allKeywords = [...keywords];

      let place = 'Jauntal';
      let lat = 46.55694;
      let lng = 14.70278;
      const qLower = (qText + ' ' + allKeywords.join(' ')).toLowerCase();
      if (qLower.includes('hemmaberg')) { place = 'Hemmaberg'; lat = 46.55269; lng = 14.66768; }
      else if (qLower.includes('globasnitz')) { place = 'Globasnitz'; lat = 46.55694; lng = 14.70278; }
      else if (qLower.includes('st. stefan') || qLower.includes('stefan')) { place = 'Sankt Stefan im Jauntal'; lat = 46.59100; lng = 14.77300; }
      else if (qLower.includes('jaunstein')) { place = 'Jaunstein'; lat = 46.55936; lng = 14.67102; }

      let archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B39-F';
      let nodeId = 'iuenna_root';
      if (qLower.includes('hemmaberg')) { archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B3B-D'; nodeId = 'col_1792212'; }
      else if (qLower.includes('gräber') || qLower.includes('graeber') || qLower.includes('ostgot')) { archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B30-8'; nodeId = 'col_1792186'; }
      else if (qLower.includes('globasnitz') || qLower.includes('münz')) { archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B30-8'; nodeId = 'col_1792169'; }
      else if (qLower.includes('stefan')) { archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B53-1'; nodeId = 'col_1792411'; }
      else if (qLower.includes('jaunstein')) { archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B4B-B'; nodeId = 'col_1792303'; }
      else if (qLower.includes('winkler')) { archePid = 'https://hdl.handle.net/21.11115/0000-0016-7B59-B'; nodeId = 'col_1792752'; }

      scoreItem(f, 'synthetic_qa', qText, {
        title: qText,
        type_label: 'FAQ & Projektwissen',
        place: place,
        lat: lat,
        lng: lng,
        qa_answer: ans,
        links: f.links || [],
        id: nodeId,
        pid: archePid,
        arche_url: archePid
      }, allKeywords);
    });

    scoredResults.sort((a, b) => b.score - a.score);
    const finalResults = scoredResults.slice(0, 3);
    finalResults.tokens = tokens;
    return finalResults;
  }

  // Clean technical prefixes, duplicate count parentheses, and raw metadata noise
  function cleanArchaeologicalText(str) {
    if (!str && str !== 0) return '';
    return String(str)
      // Strip file extensions
      .replace(/\.(pdf|tif|tiff|jpg|jpeg|png|dwg|dxf|gpkg|geojson|shp|csv|xlsx|zip)$/gi, '')
      // Strip technical collection / numbering prefixes
      .replace(/^(\d{2}_)+/g, '')
      .replace(/^(HB|GLO|JAU|STEF|RET|BIO)[-_]/gi, '')
      // Strip raw folder/container designations at the beginning
      .replace(/^(Klarsichthülle|Mischordner|Ordner|Kopie|Scan|CD)\s*\d*[:\-_\s]*/gi, '')
      // Strip duplicate count parentheses (e.g. "(322 römische Münzen)", "(440 Gräber)")
      .replace(/\s*\(\d+\s*(?:römische\s*)?(?:münzen|gräber|bestattungen|objekte|items|ressourcen|dokumente|aufnahmen|funde)[^)]*\)/gi, '')
      // Strip hierarchy level indicators (L1) - (L6)
      .replace(/\s*\(L[1-6]\)/g, '')
      // Normalise vicus annotation
      .replace(/\s*\(vicus\)/gi, ' (Bereich des antiken vicus)')
      // Strip empty parentheses
      .replace(/\(\s*\)/g, '')
      // Strip markdown link syntax, keeping text: [Some Label](url) -> Some Label
      .replace(/\[([^\]]+)\]\((?:https?|zotero):\/\/[^\)]+\)/g, '$1')
      // Strip raw desktop zotero or beaver protocol tokens
      .replace(/zotero:\/\/[^\s\)\"\']+/gi, '')
      // Strip dangling double commas or periods
      .replace(/,\s*,/g, ',')
      .replace(/\.\s*\./g, '.')
      // Replace underscores with spaces
      .replace(/_/g, ' ')
      // Clean multiple spaces
      .replace(/\s{2,}/g, ' ')
      .trim();
  }

  // Resolve exact Graph Node ID with intelligent subcollection mapping
  function resolveGraphNodeId(meta, title, cleanPlace) {
    if (meta && meta.id && meta.id !== 'none' && meta.id !== 'iuenna_root') return meta.id;
    if (meta && meta.graph_node_id && meta.graph_node_id !== 'none' && meta.graph_node_id !== 'iuenna_root') return meta.graph_node_id;

    const text = `${title || ''} ${cleanPlace || ''} ${(meta && meta.place) || ''}`.toLowerCase();
    if (text.includes('hemmaberg')) return 'col_1792212';
    if (text.includes('gräber') || text.includes('graeber') || text.includes('ostgot')) return 'col_1792186';
    if (text.includes('münz') || text.includes('hortfund')) return 'col_1792169';
    if (text.includes('winkler')) return 'col_1792752';
    if (text.includes('st. stefan') || text.includes('sankt stefan') || text.includes('stefan') || text.includes('villa') || text.includes('šteben')) return 'col_1792411';
    if (text.includes('jaunstein')) return 'col_1792303';
    if (text.includes('globasnitz')) return 'col_1792169';

    return 'iuenna_root';
  }

  // Resolve authoritative ARCHE Handle URL mapped to specific subcollections
  function resolveArcheUrl(meta, title, cleanPlace) {
    if (meta && meta.pid && !meta.pid.includes('0000-0016-7B39-F')) return meta.pid;
    if (meta && meta.arche_url && !meta.arche_url.includes('0000-0016-7B39-F')) return meta.arche_url;

    const text = `${title || ''} ${cleanPlace || ''} ${(meta && meta.place) || ''} ${((meta && meta.keywords) || []).join(' ')}`.toLowerCase();
    if (text.includes('hemmaberg')) return 'https://hdl.handle.net/21.11115/0000-0016-7B3B-D';
    if (text.includes('jaunstein')) return 'https://hdl.handle.net/21.11115/0000-0016-7B4B-B';
    if (text.includes('st. stefan') || text.includes('sankt stefan') || text.includes('stefan') || text.includes('šteben')) return 'https://hdl.handle.net/21.11115/0000-0016-7B53-1';
    if (text.includes('winkler') || text.includes('retro') || text.includes('skizzenbuch') || text.includes('tagebuch')) return 'https://hdl.handle.net/21.11115/0000-0016-7B59-B';
    if (text.includes('globasnitz') || text.includes('münz') || text.includes('ostgot')) return 'https://hdl.handle.net/21.11115/0000-0016-7B30-8';

    return (meta && (meta.pid || meta.arche_url)) || 'https://hdl.handle.net/21.11115/0000-0016-7B39-F';
  }

  // Detect entity category for specialized archaeological phrasing and contextual actions
  function detectEntityCategory(meta, title, query) {
    if (meta && meta.category) return meta.category;
    const combined = `${title || ''} ${(meta && meta.type_label) || ''} ${(meta && meta.items) || ''} ${query || ''}`.toLowerCase();
    if (/\b(zotero|literatur|publikation|publikationen|aufsatz|artikel|buch|monographie|bibliographie)\b/i.test(combined) || (meta && (meta.type === 'Publication' || meta.type === 'publication'))) return 'publications';
    if (/\b(münz|muenz|hortfund|numismat|denar|antoninian|follis|nominal|geld|präg)/i.test(combined)) return 'coins';
    if (/\b(grab|gräber|graeber|bestattung|skelett|gräberfeld|graeberfeld|nekropol|ostgot|turmschädel|schädeldeform|anthropolog)/i.test(combined)) return 'graves';
    if (/\b(plan|pläne|plaene|aufmaß|aufmass|zeichnung|profil|schnitt|grundriss|steinplan|bauaufnahme|vektor|cad|dwg|dxf)/i.test(combined)) return 'plans';
    if (/\b(person|forscher|forscherin|nachlass|winkler|ladstätter|ladstaetter|binder|profant|srienc|reiner|hagmann|waldhart|gugl|barbius|notar)/i.test(combined)) return 'persons';
    if (/\b(kirche|doppelkirche|pilger|villa|therme|badeanlage|hypokaust|mosaik|sakral|baptisterium|basilika|mauer)/i.test(combined)) return 'architecture';
    return 'default';
  }

  // Fluent, natural, scholarly German summary generator
  function formatArchaeologicalSummary(meta, topTitle, query) {
    if (!meta) return '';

    // Direct match with curated Q&A research synthesis
    if (meta.qa_answer) {
      return cleanArchaeologicalText(meta.qa_answer.trim());
    }

    const title = topTitle || meta.title || '';
    const cleanTitle = cleanArchaeologicalText(title);
    const cleanPlace = cleanArchaeologicalText(meta.place || '');
    const cleanPeriod = cleanArchaeologicalText(meta.period || '');
    const cleanItems = cleanArchaeologicalText(meta.items || '');

    // Avoid repeating place if already part of title or referring to identical locality
    let placeClause = '';
    if (cleanPlace) {
      const pLower = cleanPlace.toLowerCase();
      const tLower = cleanTitle.toLowerCase();
      const samePlace = (
        (pLower.includes('globasnitz') && tLower.includes('globasnitz')) ||
        (pLower.includes('hemmaberg') && tLower.includes('hemmaberg')) ||
        (pLower.includes('stefan') && tLower.includes('stefan')) ||
        (pLower.includes('jaunstein') && tLower.includes('jaunstein')) ||
        tLower.includes(pLower)
      );
      if (!samePlace) {
        placeClause = ` in ${cleanPlace}`;
      }
    }

    // Format period naturally
    let periodClause = '';
    if (cleanPeriod) {
      if (/^(aus|der|in|spätantike|römerzeit|frühmittelalter)/i.test(cleanPeriod)) {
        periodClause = ` (${cleanPeriod})`;
      } else {
        periodClause = ` aus der Epoche ${cleanPeriod}`;
      }
    }

    const itemsClause = cleanItems ? cleanItems : 'archäologische Primärdaten';
    const cat = detectEntityCategory(meta, title, query);
    const comb = `${cleanTitle} ${(meta.type_label || '')} ${(meta.items || '')}`.toLowerCase();

    // Deterministic selection based on title/query hash
    const seed = (title.length + (query ? query.length : 0)) % 3;

    // 1. Gräber / Bestattungen (Graves & Burials)
    if (cat === 'graves') {
      if (comb.includes('globasnitz')) {
        return 'Das ostgotische Gräberfeld von Globasnitz (5.–6. Jh. n. Chr.) zählt mit rund 425 Gräbern und circa 440 Bestattungen zu den bedeutendsten Bestattungsplätzen des Ostalpenraums. Neben herausragenden Trachtbeigaben und zwei Friedhofskirchen wurden bei mindestens zehn Individuen künstliche Schädeldeformationen (Turmschädel) nachgewiesen.';
      }
      if (comb.includes('jaunstein')) {
        return 'Das frühmittelalterliche Reihengräberfeld von Jaunstein (8.–10. Jh. n. Chr.) gehört zur slawisch-karantanischen Köttlach-Kultur. Die Gräber zeichnen sich durch reichen Trachtschmuck aus, insbesondere die charakteristischen mehrgliedrigen Korbgehänge und Emailfibeln.';
      }
      const graveTemplates = [
        `Zum Bestattungskomplex **${cleanTitle}**${placeClause}: Die Forschungsdaten umfassen ${itemsClause}${periodClause}. Die Dokumentation erschließt detaillierte Grabungsberichte, Gräberfeldpläne und anthropologische Befunde.`,
        `Der Bestattungsplatz **${cleanTitle}**${placeClause} umfasst ${itemsClause}${periodClause}. Der Befund liefert grundlegende Erkenntnisse zu Bestattungsbräuchen, Grabausstattungen und der spätantik-frühmittelalterlichen Bevölkerung des Jauntals.`,
        `Im Gräberfeldareal von **${cleanTitle}**${placeClause} wurden ${itemsClause}${periodClause} freigelegt und wissenschaftlich inventarisiert.`
      ];
      return graveTemplates[seed % graveTemplates.length];
    }

    // 2. Münzen / Hortfunde (Coins & Hoards)
    if (cat === 'coins') {
      if (comb.includes('globasnitz')) {
        return '1946 wurde im Ortszentrum von Globasnitz ein bedeutender Hortfund von 322 römischen Bronzemünzen (3.–4. Jh. n. Chr.) geborgen. Der Fundkomplex belegt den regen Geldumlauf und die florierende spätantike Wirtschaft im Bereich der Straßensiedlung an der norischen Fernstraße.';
      }
      const coinTemplates = [
        `Der numismatische Fundbestand zu **${cleanTitle}**${placeClause} umfasst ${itemsClause}${periodClause}. Die Fundmünzen dokumentieren Geldumlauf, Handelsnetzwerke und Verbergungshorizonte in der Mikroregion.`,
        `Zu den Münzfunden aus **${cleanTitle}**${placeClause} verzeichnet die Sammlung ${itemsClause}${periodClause}. Die Stücke sind mit genauer Fundlage und numismatischer Bestimmung katalogisiert.`,
        `In den IUENNA-Beständen ist der Münzbestand **${cleanTitle}**${placeClause} mit einem Umfang von ${itemsClause}${periodClause} erschlossen und digital zugänglich.`
      ];
      return coinTemplates[seed % coinTemplates.length];
    }

    // 3. Pläne / Aufmaßzeichnungen (Plans & Architectural Drawings)
    if (cat === 'plans') {
      const planTemplates = [
        `Die planimetrische Dokumentation zu **${cleanTitle}**${placeClause} umfasst ${itemsClause}. Die Bestände enthalten hochauflösende Bauaufnahmen, Profilschnitte, Steinpläne und georeferenzierte Vektorgeodaten.`,
        `Für **${cleanTitle}**${placeClause} verzeichnet das Repositorium ${itemsClause}. Die Pläne dokumentieren Grabungsschnitte, Mauerzüge und Schichtbefunde aus über einem Jahrhundert Forschungsgeschichte.`,
        `Zu **${cleanTitle}**${placeClause} liegen ${itemsClause}${periodClause} vor. Die Vermessungs- und CAD-Zeichnungen bilden die Befundstrukturen präzise ab und stehen als Rasterscans sowie Vektordaten bereit.`
      ];
      return planTemplates[seed % planTemplates.length];
    }

    // 4. Personen & Nachlässe (Persons & Researchers)
    if (cat === 'persons') {
      if (comb.includes('winkler')) {
        return 'Dr. Hans Winkler (1882–1964), Notar in Eberndorf, war ein zentraler autodidaktischer Pionier der Jauntaler Archäologie. Sein im IUENNA-Projekt aufbereiteter Nachlass umfasst 475 Archivalien – darunter detailreiche Skizzenbücher, Fundprotokolle und Feldtagebücher zu Ausgrabungen in St. Stefan und am Hemmaberg.';
      }
      if (comb.includes('ladstätter') || comb.includes('ladstaetter')) {
        return 'Dr. Sabine Ladstätter (1967–2024, ÖAI / ÖAW) erforschte grundlegend die materielle Kultur der Spätantike auf dem Hemmaberg und leitete die Ausgrabungen an der Wallanlage. Ihre Monografie bildet das chronologische und funktionale Fundament der Erforschung des Pilgerheiligtums.';
      }
      if (comb.includes('binder')) {
        return 'Dr. Michaela Binder (ÖAI / ÖAW) leitet die bioarchäologischen und anthropologischen Untersuchungen im Gräberfeld auf dem Hemmaberg. Zu ihren international beachteten Entdeckungen zählt der Nachweis einer frühmittelalterlichen Fußprothese aus dem 6. Jahrhundert n. Chr.';
      }
      if (comb.includes('profant')) {
        return 'Elke Profant (ÖAI / ÖAW) führt großflächige geophysikalische Prospektionen und Geomagnetik-Messungen im Jauntal durch, die verborgene römische Straßen, Großbauten und Gräber in Globasnitz und St. Stefan zerstörungsfrei sichtbar machen.';
      }
      if (comb.includes('srienc')) {
        return 'Dr. Magdalena Srienc erforscht als Archäologin die spätantike und frühmittelalterliche Siedlungslandschaft sowie materielle Kulturzeugnisse im südlichen Jauntal.';
      }
      if (comb.includes('hagmann') || comb.includes('reiner')) {
        return 'Dr. Dominik Hagmann (kärnten.museum) und Franziska Reiner (ÖAI / ÖAW) leiten das Projekt IUENNA. Ihre Publikationen und Datenkurationen verbinden archäologische Feldforschung, Langzeitarchivierung in ARCHE und moderne Web-GIS-Infrastrukturen.';
      }
      const personTemplates = [
        `**${cleanTitle}** ist als zentrale Persönlichkeit der archäologischen Erforschung des Jauntals verzeichnet. Das Archiv bewahrt zugehörige Dokumente, Forschungsberichte und Nachlassakten.`,
        `Im Rahmen der Forschungsgeschichte zu ${cleanPlace || 'Jauntal'} dokumentieren die IUENNA-Bestände das Wirken von **${cleanTitle}** mit archivalischen Zeugnissen und Fundberichten.`
      ];
      return personTemplates[seed % personTemplates.length];
    }

    // 5. Bauten / Villen / Kirchen (Architecture)
    if (cat === 'architecture') {
      if (comb.includes('hemmaberg')) {
        return 'Die frühchristliche Doppelkirchenanlage auf dem Hemmaberg bildete im 5. und 6. Jahrhundert n. Chr. ein weithin berühmtes spätantikes Pilgerheiligtum. Das Areal umfasst fünf Sakralbauten, Baptisterien und aufwendige Mosaikböden samt umfassender archäologischer Dokumentation.';
      }
      if (comb.includes('stefan') || comb.includes('šteben')) {
        return 'Die römische Großvilla von St. Stefan im Jauntal erstreckt sich über rund zwei Hektar aus der Kaiserzeit (1.–4. Jh. n. Chr.). Die Erfassung dokumentiert herrschaftliche Wohnbereiche mit Fußbodenheizung (Hypokaust) und eine monumentale Badeanlage (Therme).';
      }
      const archTemplates = [
        `Der architektonische Befund **${cleanTitle}**${placeClause} umfasst ${itemsClause}${periodClause}. Die baulichen Strukturen sind durch Mauerwerksanalysen, Profilschnitte und Fotodokumentationen erschlossen.`,
        `Zu **${cleanTitle}**${placeClause} dokumentieren die Bestände ${itemsClause}. Die Anlage${periodClause} stellt ein herausragendes Denkmal der Siedlungs- und Baugeschichte des Jauntals dar.`
      ];
      return archTemplates[seed % archTemplates.length];
    }

    // 6. Publikationen & Literatur
    if (cat === 'publications') {
      const pubTemplates = [
        `Die Fachpublikation **${cleanTitle}**${placeClause} dokumentiert wissenschaftliche Ergebnisse zu den archäologischen Befunden im Jauntal. Der Titel ist in der Zotero-Projektbibliothek (ID: 4910727) erfasst.`,
        `Zu **${cleanTitle}** liegt ein wissenschaftlicher Forschungsbeitrag vor${periodClause}. Die Publikation erschließt die Grabungsergebnisse und Fundkomplexe für die internationale Forschung.`
      ];
      return pubTemplates[seed % pubTemplates.length];
    }

    // 7. Default Fallback for General Collections / Documents
    if (meta.description && meta.description.length > 20) {
      return `Zu **${cleanTitle}**${placeClause}: ${cleanArchaeologicalText(meta.description)}`;
    }
    const defaultTemplates = [
      `Der Sammlungsbestand **${cleanTitle}**${placeClause} umfasst ${itemsClause}${periodClause}. Alle zugehörigen Ressourcen sind im Repositorium ARCHE sowie im IUENNA-Wissensgraphen erschlossen.`,
      `In den IUENNA-Beständen ist **${cleanTitle}**${placeClause} mit ${itemsClause}${periodClause} verzeichnet und digital zugänglich.`
    ];
    return defaultTemplates[seed % defaultTemplates.length];
  }

  // Dynamic contextual follow-up suggestions
  function generateFollowUpChips(top) {
    if (!top || !top.meta) return '';
    const text = ((top.title || '') + ' ' + (top.meta.place || '')).toLowerCase();
    const chips = [];

    if (text.includes('münz') || text.includes('322')) {
      chips.push({ query: 'Was ist über den Münzschatzfund von Globasnitz bekannt?', label: '🪙 Münzschatz (322 Münzen)' });
      chips.push({ query: 'Welche geophysikalischen Prospektionsmethoden wurden in Globasnitz und St. Stefan eingesetzt?', label: '📡 Geophysik & Prospektion' });
      chips.push({ query: 'Ist Globasnitz wirklich die römische Straßenstation Iuenna?', label: '🏛️ Tscherberg vs. Globasnitz' });
    } else if (text.includes('winkler')) {
      chips.push({ query: 'Wer war Hans Winkler?', label: '👤 Hans Winkler' });
      chips.push({ query: 'Welche Rolle spielten die historischen Skizzen von Hans Winkler?', label: '🎨 Hans Winkler Skizzen' });
      chips.push({ query: 'Gibt es Pläne zur Villa St. Stefan?', label: '🗺️ Pläne St. Stefan' });
    } else if (text.includes('hemmaberg')) {
      chips.push({ query: 'Warum gibt es auf dem Hemmaberg Doppelkirchen?', label: '⛪ Doppelkirchen' });
      chips.push({ query: 'Gibt es Grabungspläne zum Hemmaberg?', label: '🗺️ Grabungspläne' });
      chips.push({ query: 'Was ist über die frühmittelalterliche Fußprothese vom Hemmaberg bekannt?', label: '🦴 Fußprothese (6. Jh.)' });
    } else if (text.includes('globasnitz') || text.includes('ostgot') || text.includes('grab') || text.includes('gräber')) {
      chips.push({ query: 'Wie viele Gräber wurden im ostgotischen Gräberfeld von Globasnitz ausgegraben?', label: '⚰️ 425 Gräber' });
      chips.push({ query: 'Wurden im ostgotischen Gräberfeld von Globasnitz künstliche Schädeldeformationen nachgewiesen?', label: '💀 Schädeldeformationen' });
      chips.push({ query: 'Gab es frühchristliche Kirchen im Gräberfeld von Globasnitz?', label: '⛪ Kirchen im Gräberfeld' });
      chips.push({ query: 'Was zeichnet das frühmittelalterliche Gräberfeld von Jaunstein aus?', label: '🦴 Jaunstein Reihengräber' });
    } else if (text.includes('jaunstein')) {
      chips.push({ query: 'Was zeichnet das frühmittelalterliche Gräberfeld von Jaunstein aus?', label: '🦴 Köttlach-Kultur' });
      chips.push({ query: 'Grabungspläne Jaunstein', label: '🗺️ Pläne Jaunstein' });
    } else {
      chips.push({ query: 'Wer war Hans Winkler?', label: '👤 Hans Winkler' });
      chips.push({ query: 'Welche Münzen gibt es?', label: '🪙 Münzschatz Globasnitz' });
      chips.push({ query: 'Warum gibt es auf dem Hemmaberg Doppelkirchen?', label: '⛪ Hemmaberg' });
    }

    if (chips.length === 0) return '';
    return `
      <div style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border-color);">
        <span style="font-size: 0.74rem; color: var(--text-muted); font-weight: 600; display: block; margin-bottom: 4px;">Weiterführende Vorschläge:</span>
        <div class="chat-chips-container" style="margin-top: 4px;">
          ${chips.map(c => `<button type="button" class="chat-chip" data-query="${escapeHtml(c.query)}">${c.label}</button>`).join('')}
        </div>
      </div>
    `;
  }

  // Format Search Results into Clean, Clickable Cards
  function renderSearchResultCard(results, summaryText, query = '') {
    // Case A: 0 Results Found (Pure notice with varying friendly phrasing - no lectures, no fake info)
    if (!results || results.length === 0) {
      const zeroVariations = [
        "Die Anfrage lieferte leider keine Ergebnisse in den Beständen.",
        "Zu diesem Suchbegriff konnten in der Sammlungsdatenbank leider keine Treffer ermittelt werden.",
        "Für diese Anfrage liegen in den Sammlungs- und Geodaten derzeit keine passenden Einträge vor.",
        "In den digitalisierten Beständen wurden dazu leider keine passenden Objekte oder Dokumente gefunden."
      ];
      const randomMsg = zeroVariations[Math.floor(Math.random() * zeroVariations.length)];

      return `
        <div class="chat-msg-bubble">
          <p style="margin: 0 0 6px 0; font-size: 0.88rem; font-weight: 600; color: var(--text-dark);">
            ${randomMsg} 🔍
          </p>
          <p style="margin: 0 0 10px 0; font-size: 0.82rem; color: var(--text-muted); line-height: 1.45;">
            Versuchen Sie es mit einem anderen Begriff oder wählen Sie eines dieser Themen:
          </p>
          <div class="chat-chips-container">
            <button type="button" class="chat-chip chat-chip-byoai" data-query="Was ist BYOAI?"><i class="fa-solid fa-microchip"></i> Was ist BYOAI?</button>
            <button type="button" class="chat-chip" data-query="Welche Literatur gibt es?" style="background: rgba(192, 57, 43, 0.07); border-color: rgba(192, 57, 43, 0.25); color: #c0392b; font-weight: 600;"><i class="fa-solid fa-book-bookmark"></i> 📚 Literatur (Zotero)</button>
            <button type="button" class="chat-chip" data-query="Welche Münzen gibt es?">🪙 Münzschatz Globasnitz</button>
            <button type="button" class="chat-chip" data-query="Doppelkirchen Hemmaberg">⛪ Hemmaberg</button>
            <button type="button" class="chat-chip" data-query="Ostgotisches Gräberfeld Globasnitz">💀 Ostgotisches Gräberfeld</button>
            <button type="button" class="chat-chip" data-query="Wer war Hans Winkler?">👤 Hans Winkler</button>
            <button type="button" class="chat-chip" data-query="Villenanlage St. Stefan">🏡 Villa St. Stefan</button>
            <button type="button" class="chat-chip" data-query="Grabungspläne Hemmaberg">🗺️ Grabungspläne</button>
            <button type="button" class="chat-chip" data-query="Inschriften">📜 Inschriften</button>
          </div>
          <div style="margin-top: 10px; padding: 7px 10px; background: rgba(106, 27, 154, 0.06); border: 1px solid rgba(106, 27, 154, 0.2); border-radius: var(--radius-sm, 4px); font-size: 0.77rem; color: #4a148c; line-height: 1.4;">
            <i class="fa-solid fa-microchip" style="color: #6a1b9a;"></i> <strong>BYOAI-Tipp:</strong> Für tiefere Abfragen oder semantische Analysen können Sie Ihre eigene KI über unser <strong>Model Context Protocol (MCP)</strong> oder offene Schnittstellen anbinden: <a href="byoai.html" target="_blank" rel="noopener noreferrer" style="color: #6a1b9a; font-weight: 700; text-decoration: underline;">Zum BYOAI Hub &rarr;</a>
          </div>
        </div>
      `;
    }

    // Case B: Results Found (Structured metadata summary + Action Buttons)
    const top = results[0];
    const meta = top.meta || {};
    const cleanTitle = cleanArchaeologicalText(top.title || '');
    const cleanPlace = cleanArchaeologicalText(meta.place || '');
    const cleanPeriod = cleanArchaeologicalText(meta.period || '');
    const cleanItems = cleanArchaeologicalText(meta.items || '');

    // Action Buttons - Smart, Context-Sensitive Generation
    let linksHtml = '';
    const cat = detectEntityCategory(meta, cleanTitle, query);

    // Resolve exact Graph Node ID and ARCHE URL
    const graphNodeId = resolveGraphNodeId(meta, cleanTitle, cleanPlace);
    const graphHref = isGraphPage
      ? `?col=${encodeURIComponent(graphNodeId)}`
      : `${basePath}graph/index.html?col=${encodeURIComponent(graphNodeId)}`;

    const archeUrl = resolveArcheUrl(meta, cleanTitle, cleanPlace);

    // 1. PERSONEN & FORSCHERINNEN: Ladstätter, Binder, Profant, Srienc, Winkler, Hagmann/Reiner etc.
    if (cat === 'persons') {
      // Graph link to person / archive node
      linksHtml += `<a href="${graphHref}" class="chat-card-btn graph-btn" data-node-id="${escapeHtml(graphNodeId)}" title="Nachlass im Wissensgraphen fokussieren"><i class="fa-solid fa-circle-nodes"></i> Nachlass im Wissensgraphen 🕸️</a>`;

      // ARCHE link directly to personal archive collection
      linksHtml += `<a href="${archeUrl}" target="_blank" rel="noopener noreferrer" class="chat-card-btn arche-btn"><i class="fa-solid fa-box-archive"></i> Archivalien in ARCHE ↗</a>`;

      // Zotero bibliography search for this researcher
      const authorLastName = cleanTitle.replace(/^(Dr\.|Mag\.|Prof\.)\s*/i, '').split(' ').pop() || 'Winkler';
      const zoteroPersonUrl = `https://www.zotero.org/groups/4910727/iuenna/library?q=${encodeURIComponent(authorLastName)}`;
      linksHtml += `<a href="${zoteroPersonUrl}" target="_blank" rel="noopener noreferrer" class="chat-card-btn zotero-btn"><i class="fa-solid fa-book-bookmark"></i> Publikationen (Zotero) 📚</a>`;

      // Secondary: if Winkler, add clear context-specific excavation map link
      if (cleanTitle.toLowerCase().includes('winkler')) {
        const winklerGisUrl = `${basePath}wma/wma.html?lat=46.59100&lng=14.77300&zoom=16`;
        linksHtml += `<a href="${winklerGisUrl}" target="_blank" rel="noopener noreferrer" class="chat-card-btn gis-btn" title="Grabungsort von Winkler in St. Stefan im Web-GIS ansehen"><i class="fa-solid fa-map-location-dot"></i> Grabungsort St. Stefan (GIS) 🗺️</a>`;
      }
    }
    // 2. PUBLIKATIONEN & LITERATUR
    else if (cat === 'publications') {
      // Direct Zotero link or DOI
      let pubUrl = meta.url || meta.uri;
      if (!pubUrl || pubUrl.includes('arche.acdh.oeaw.ac.at')) {
        pubUrl = `https://www.zotero.org/groups/4910727/iuenna/library?q=${encodeURIComponent(cleanTitle.slice(0, 35))}`;
      }
      linksHtml += `<a href="${pubUrl}" target="_blank" rel="noopener noreferrer" class="chat-card-btn zotero-btn"><i class="fa-solid fa-book-bookmark"></i> In Zotero öffnen 📚</a>`;

      // If direct PDF available
      if (meta.url && meta.url.toLowerCase().endsWith('.pdf')) {
        linksHtml += `<a href="${meta.url}" target="_blank" rel="noopener noreferrer" class="chat-card-btn pdf-btn"><i class="fa-solid fa-file-pdf"></i> Volltext (PDF) 📄</a>`;
      }

      // Graph link to publication node
      linksHtml += `<a href="${graphHref}" class="chat-card-btn graph-btn" data-node-id="${escapeHtml(graphNodeId)}" title="Publikation im Wissensgraphen zeigen"><i class="fa-solid fa-circle-nodes"></i> Im Wissensgraphen zeigen 🕸️</a>`;

      // ARCHE link if available
      if (archeUrl) {
        linksHtml += `<a href="${archeUrl}" target="_blank" rel="noopener noreferrer" class="chat-card-btn arche-btn"><i class="fa-solid fa-arrow-up-right-from-square"></i> In ARCHE öffnen ↗</a>`;
      }
    }
    // 3. ARCHÄOLOGISCHE BEFUNDE, FUNDKOMPLEXE, GEODATEN, PLÄNE
    else {
      // Graph Link
      linksHtml += `<a href="${graphHref}" class="chat-card-btn graph-btn" data-node-id="${escapeHtml(graphNodeId)}" title="Im Wissensgraphen fokussieren"><i class="fa-solid fa-circle-nodes"></i> Im Wissensgraphen zeigen 🕸️</a>`;

      // Web-GIS Link: Only show if coordinates exist or can be resolved
      let gisLat = meta.lat;
      let gisLng = meta.lng;
      if (!gisLat || !gisLng) {
        const siteKey = `${cleanTitle} ${cleanPlace} ${(meta.place || '')}`.toLowerCase();
        if (siteKey.includes('hemmaberg')) { gisLat = 46.55269; gisLng = 14.66768; }
        else if (siteKey.includes('globasnitz')) { gisLat = 46.55694; gisLng = 14.70278; }
        else if (siteKey.includes('stefan') || siteKey.includes('šteben')) { gisLat = 46.59100; gisLng = 14.77300; }
        else if (siteKey.includes('jaunstein')) { gisLat = 46.55936; gisLng = 14.67102; }
      }

      if (gisLat && gisLng) {
        const gisUrl = `${basePath}wma/wma.html?lat=${gisLat}&lng=${gisLng}&zoom=16`;
        linksHtml += `<a href="${gisUrl}" target="_blank" rel="noopener noreferrer" class="chat-card-btn gis-btn"><i class="fa-solid fa-map-location-dot"></i> In Web-GIS ansehen 🗺️</a>`;
      }

      // ARCHE Link: Real persistent identifier
      linksHtml += `<a href="${archeUrl}" target="_blank" rel="noopener noreferrer" class="chat-card-btn arche-btn"><i class="fa-solid fa-arrow-up-right-from-square"></i> In ARCHE öffnen ↗</a>`;
    }

    // Weitere relevante Treffer im Wissensgraphen
    let secondaryHtml = '';
    if (results.length > 1) {
      secondaryHtml = `
        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border-color); font-size: 0.78rem;">
          <span style="color: var(--text-muted); font-weight: 600;">Weitere relevante Treffer im Wissensgraphen:</span>
          <ul style="margin: 4px 0 0 16px; padding: 0; color: var(--text-dark);">
            ${results.slice(1, 4).map(r => {
              const rTitle = cleanArchaeologicalText(r.title || '');
              const rPlace = cleanArchaeologicalText(r.meta ? r.meta.place : '');
              const rId = resolveGraphNodeId(r.meta || {}, rTitle, rPlace);
              let rGraphHref = isGraphPage
                ? `?col=${encodeURIComponent(rId)}`
                : `${basePath}graph/index.html?col=${encodeURIComponent(rId)}`;
              return `
                <li style="margin-bottom: 3px;">
                  <strong>${escapeHtml(rTitle)}</strong>
                  <a href="${rGraphHref}" class="chat-secondary-graph-link" data-node-id="${escapeHtml(rId)}" style="color: var(--secondary); text-decoration: underline; margin-left: 4px; font-weight: 600;">[Im Wissensgraphen 🕸️]</a>
                </li>
              `;
            }).join('')}
          </ul>
        </div>
      `;
    }

    // Dynamic contextual follow-up suggestions
    const followUpHtml = generateFollowUpChips(top);

    // Natural varied lead-in phrase
    const introVariations = [
      "Zu Ihrer Recherche in den Sammlungsbeständen:",
      "In der archäologischen Dokumentation liegt dazu Folgendes vor:",
      "Die Sammlungsdatenbank verzeichnet dazu folgenden Befund:",
      "Zu diesem Thema finden sich in den Beständen folgende Nachweise:",
      "Aus den archäologischen Erfassungen im Jauntal:",
      "Die Dokumentation liefert zu dieser Anfrage folgenden Eintrag:"
    ];
    const introText = introVariations[Math.floor(Math.random() * introVariations.length)];

    const cardBadge = top.type === 'synthetic_qa'
      ? 'Archäologische Forschungssynthese'
      : cleanArchaeologicalText(meta.type_label || 'Sammlungsbestand');

    return `
      <div class="chat-msg-bubble">
        <!-- 1. Conversational Intro -->
        <p class="chat-intro-line" style="margin: 0 0 8px 0; font-size: 0.88rem; font-weight: 600; color: var(--text-dark); display: flex; align-items: center; gap: 6px;">
          <i class="fa-solid fa-magnifying-glass" style="color: var(--secondary); font-size: 0.85rem;"></i>
          <span>${escapeHtml(introText)}</span>
        </p>

        <!-- 2. Crisp result card based on verified archaeological metadata & research -->
        <div class="chat-result-card" style="background: rgba(184, 142, 62, 0.05); border-left: 3px solid var(--secondary); padding: 9px 12px; border-radius: var(--radius-sm, 4px); margin-bottom: 8px;">
          <div style="font-size: 0.68rem; font-weight: 700; text-transform: uppercase; color: var(--secondary); letter-spacing: 0.04em; margin-bottom: 2px;">
            ${escapeHtml(cardBadge)}
          </div>
          <h4 style="margin: 0 0 4px 0; font-size: 0.93rem; font-family: var(--font-header); color: var(--primary);">
            ${escapeHtml(cleanTitle)}
          </h4>
          <p style="margin: 0; font-size: 0.84rem; line-height: 1.48; color: var(--text-dark);">
            ${summaryText}
          </p>

          <!-- Metadata Tags -->
          <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;">
            ${cleanPlace ? `<span class="chat-card-tag"><i class="fa-solid fa-location-dot"></i> ${escapeHtml(cleanPlace)}</span>` : ''}
            ${cleanPeriod ? `<span class="chat-card-tag"><i class="fa-solid fa-clock"></i> ${escapeHtml(cleanPeriod)}</span>` : ''}
            ${cleanItems ? `<span class="chat-card-tag"><i class="fa-solid fa-layer-group"></i> ${escapeHtml(cleanItems)}</span>` : ''}
            ${meta.size ? `<span class="chat-card-tag"><i class="fa-solid fa-hard-drive"></i> ${escapeHtml(meta.size)}</span>` : ''}
          </div>

          <!-- Citation Reference if available (with clickable links to Zotero / DOI) -->
          ${(() => {
            const qStr = (query || '').toLowerCase();
            const allowGlaser = qStr.includes('glaser');
            const allowPollak = qStr.includes('pollak');
            const safeCits = (meta.citations || []).filter(c => {
              const lower = c.toLowerCase();
              if (lower.includes('glaser') && !allowGlaser) return false;
              if (lower.includes('pollak') && !allowPollak) return false;
              return true;
            });
            if (safeCits.length === 0) return '';

            const citLinks = safeCits.map(cit => {
              const cleanCit = cit.replace(/\[|\]/g, '').trim();
              const doiMatch = cleanCit.match(/10\.\d{4,9}\/[-._;()/:A-Z0-9]+/i);
              let citHref = '';
              if (doiMatch) {
                citHref = `https://doi.org/${doiMatch[0]}`;
              } else {
                const searchQ = cleanCit.replace(/p\.\s*\d+/g, '').replace(/[()]/g, '').trim();
                citHref = `https://www.zotero.org/groups/4910727/iuenna/library?q=${encodeURIComponent(searchQ)}`;
              }
              return `<a href="${citHref}" target="_blank" rel="noopener noreferrer" style="color: var(--secondary); text-decoration: underline; font-weight: 500;" title="Zotero / DOI Referenz öffnen">${escapeHtml(cleanCit)}</a>`;
            });

            return `
            <div style="margin-top: 6px; font-size: 0.75rem; color: var(--text-muted); line-height: 1.4;">
              <i class="fa-solid fa-book-bookmark" style="color: #c0392b; margin-right: 3px;"></i> <strong>Referenz:</strong> ${citLinks.join(' • ')}
            </div>
          `;
          })()}
        </div>

        <!-- 3. Prominent Action Buttons -->
        <div class="chat-card-links">
          ${linksHtml}
        </div>

        <!-- 4. BYOAI Integration Mention in Answers -->
        <div class="chat-byoai-answer-hint">
          <span style="color: #512da8; line-height: 1.35;">
            <i class="fa-solid fa-microchip"></i> <strong>BYOAI:</strong> Diesen Datensatz mit eigener KI (Claude, GPT, Ollama) auswerten?
          </span>
          <a href="${basePath}byoai.html" target="_blank" rel="noopener noreferrer" style="color: #512da8; font-weight: 700; text-decoration: underline; white-space: nowrap;">
            BYOAI &amp; MCP &rarr;
          </a>
        </div>

        <!-- 5. Related Hits & Follow-ups -->
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
    saveChatState();
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
    saveChatState();
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

  // 6. Conversational Handler
  async function handleUserSubmit(userQuery) {
    if (!userQuery || !userQuery.trim()) return;
    const query = userQuery.trim();
    const thisRequestId = ++currentRequestId;

    // 1. Render User Message & Typing indicator
    appendUserMessage(query);
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

    // Dialog Intent C: BYOAI / AI / MCP / Schnittstellen
    if (/\b(byoai|ki|ai|mcp|ollama|chatgpt|claude|agent|agenten|api|openapi|llm|llms|schnittstelle|schnittstellen|bring your own ai)\b/i.test(cleanQ)) {
      setTimeout(() => {
        if (thisRequestId !== currentRequestId) return;
        removeTypingIndicator();
        appendBotMessage(`
          <div class="chat-msg-bubble">
            <p style="margin: 0 0 6px 0; font-weight: 700; font-size: 0.92rem; color: #4a148c; display: flex; align-items: center; gap: 6px;">
              <i class="fa-solid fa-microchip"></i> Bring Your Own AI (BYOAI) in IUENNA
            </p>
            <p style="margin: 0 0 8px 0; font-size: 0.84rem; line-height: 1.45; color: var(--text-dark);">
              IUENNA verfolgt das <strong>BYOAI-Prinzip (Bring Your Own AI)</strong>: Statt Sie an ein vorgegebenes Modell oder eine proprietäre Plattform zu binden, stellen wir offene, standardisierte Schnittstellen bereit. Sie können Ihre <strong>eigene bevorzugte KI</strong> (z.&nbsp;B. Claude Desktop, ChatGPT, Ollama lokal oder Google Antigravity) direkt an die archäologischen Forschungsdaten anbinden!
            </p>
            <div style="background: rgba(106, 27, 154, 0.05); border: 1px solid rgba(106, 27, 154, 0.18); border-radius: 4px; padding: 8px 10px; font-size: 0.78rem; line-height: 1.45; color: #4a148c; margin-bottom: 8px;">
              <ul style="margin: 0; padding-left: 16px;">
                <li><strong>Model Context Protocol (MCP):</strong> Vorkonfigurierter Server (Python &amp; Node.js) für automatisierte Werkzeug- &amp; Fundstellenabfragen.</li>
                <li><strong>OpenAPI &amp; llms.txt:</strong> Maschinenlesbare API-Spezifikation und hierarchischer KI-Kontext.</li>
                <li><strong>ARCHE Langzeitarchiv:</strong> Verlässliche Zitation und Zugriff auf 20.788 Primärressourcen via Persistent Identifiers (PIDs).</li>
              </ul>
            </div>
            <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
              <a href="${basePath}byoai.html" target="_blank" rel="noopener noreferrer" class="chat-card-btn" style="background: #6a1b9a; color: #fff; text-decoration: none; font-weight: 600; font-size: 0.78rem; padding: 6px 12px; border-radius: 4px; display: inline-flex; align-items: center; gap: 5px;">
                <i class="fa-solid fa-microchip"></i> Zum BYOAI Hub (Setup &amp; MCP) ↗
              </a>
              <a href="${basePath}data/openapi.json" target="_blank" rel="noopener noreferrer" class="chat-card-btn" style="background: var(--bg-card); color: var(--text-dark); border: 1px solid var(--border-color); text-decoration: none; font-size: 0.78rem; padding: 6px 10px; border-radius: 4px; display: inline-flex; align-items: center; gap: 5px;">
                <i class="fa-solid fa-code"></i> OpenAPI JSON
              </a>
              <a href="${basePath}llms.txt" target="_blank" rel="noopener noreferrer" class="chat-card-btn" style="background: var(--bg-card); color: var(--text-dark); border: 1px solid var(--border-color); text-decoration: none; font-size: 0.78rem; padding: 6px 10px; border-radius: 4px; display: inline-flex; align-items: center; gap: 5px;">
                <i class="fa-solid fa-file-lines"></i> llms.txt
              </a>
            </div>
          </div>
        `);
      }, 150);
      return;
    }

    // Dialog Intent D: Literature / Publications / Zotero / Bibliography (general project queries)
    if (/\b(zotero|literatur|publikation|publikationen|bibliographie|quellen|literaturverzeichnis|aufsatz|aufsätze|artikel|fachliteratur)\b/i.test(cleanQ)) {
      setTimeout(() => {
        if (thisRequestId !== currentRequestId) return;
        removeTypingIndicator();
        appendBotMessage(`
          <div class="chat-msg-bubble">
            <p style="margin: 0 0 6px 0; font-weight: 700; font-size: 0.92rem; color: #b88e3e; display: flex; align-items: center; gap: 6px;">
              <i class="fa-solid fa-book-bookmark" style="color: #c0392b;"></i> IUENNA Literatur &amp; Zotero-Bibliothek
            </p>
            <p style="margin: 0 0 8px 0; font-size: 0.84rem; line-height: 1.45; color: var(--text-dark);">
              Die gesamte wissenschaftliche Literatur des IUENNA-Projekts sowie Publikationen zu den Fundstellen im Jauntal (Hemmaberg, Globasnitz, St. Stefan) und zu digitaler Archäologie ist in unserer <strong>öffentlichen Zotero-Gruppe (ID: 4910727)</strong> mit über <strong>420 Titeln</strong> erfasst.
            </p>
            <div style="background: rgba(184, 142, 62, 0.06); border: 1px solid rgba(184, 142, 62, 0.2); border-radius: 4px; padding: 8px 10px; font-size: 0.79rem; line-height: 1.45; margin-bottom: 8px;">
              <p style="margin: 0 0 4px 0; font-weight: 600; color: var(--primary);">Wichtige Referenztitel:</p>
              <ul style="margin: 0; padding-left: 16px;">
                <li><strong>Hagmann &amp; Reiner (geb. Waldhart) (2025):</strong> <em>Das go!digital-3.0-Projekt IUENNA</em> (Rudolfinum).</li>
                <li><strong>Hagmann, Reiner &amp; Gugl (2025):</strong> <em>No End of History Yet! Long-Term Archiving in Roman Archaeology</em>.</li>
                <li><strong>Reiner &amp; Profant (2025):</strong> <em>Iuenna und Umgebung – Geophysikalische Prospektion</em>.</li>
                <li><strong>Hagmann &amp; Reiner (2023):</strong> <em>IUENNA – A ‘para-description’</em> (Peer Community Journal).</li>
                <li><strong>Hagmann &amp; Waldhart (Hrsg.) (2025):</strong> <em>IUENNA</em> (ARCHE-Forschungsdateninfrastruktur).</li>
              </ul>
            </div>
            <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px;">
              <a href="https://www.zotero.org/groups/4910727/iuenna/library" target="_blank" rel="noopener noreferrer" class="chat-card-btn" style="background: #c0392b; color: #fff; text-decoration: none; font-weight: 600; font-size: 0.78rem; padding: 6px 12px; border-radius: 4px; display: inline-flex; align-items: center; gap: 5px;">
                <i class="fa-solid fa-arrow-up-right-from-square"></i> Zotero-Bibliothek öffnen ↗
              </a>
              <a href="https://api.zotero.org/groups/4910727/items?format=json&limit=20" target="_blank" rel="noopener noreferrer" class="chat-card-btn" style="background: var(--bg-card); color: var(--text-dark); border: 1px solid var(--border-color); text-decoration: none; font-size: 0.78rem; padding: 6px 10px; border-radius: 4px; display: inline-flex; align-items: center; gap: 5px;">
                <i class="fa-solid fa-code"></i> Zotero API (JSON)
              </a>
              <a href="https://api.zotero.org/groups/4910727/items?format=bib" target="_blank" rel="noopener noreferrer" class="chat-card-btn" style="background: var(--bg-card); color: var(--text-dark); border: 1px solid var(--border-color); text-decoration: none; font-size: 0.78rem; padding: 6px 10px; border-radius: 4px; display: inline-flex; align-items: center; gap: 5px;">
                <i class="fa-solid fa-file-lines"></i> BibTeX Export
              </a>
            </div>
          </div>
        `);
      }, 150);
      return;
    }

    // Multi-turn Pronoun & Topic Expansion
    let effectiveQuery = query;
    if (dialogueState.lastTopic && /\b(dazu|dort|davon|mehr|weitere|auch|pläne|fotos|bilder|gräber)\b/i.test(query) && !query.toLowerCase().includes(dialogueState.lastTopic.toLowerCase())) {
      effectiveQuery = `${query} ${dialogueState.lastTopic}`;
    }

    // 2. Search Knowledge Base
    const results = searchKnowledgeBase(effectiveQuery);

    // If 0 results: immediate polite variation
    if (!results || results.length === 0) {
      setTimeout(() => {
        if (thisRequestId !== currentRequestId) return;
        removeTypingIndicator();
        const cardHtml = renderSearchResultCard([]);
        appendBotMessage(cardHtml);
      }, 150);
      return;
    }

    // Update conversation topic state from top match
    const top = results[0];
    const txt = ((top.title || '') + ' ' + (top.meta.place || '')).toLowerCase();
    if (txt.includes('hemmaberg')) dialogueState.lastTopic = 'Hemmaberg';
    else if (txt.includes('globasnitz')) dialogueState.lastTopic = 'Globasnitz';
    else if (txt.includes('st. stefan') || txt.includes('barbius') || txt.includes('winkler')) dialogueState.lastTopic = 'St. Stefan';
    else if (txt.includes('jaunstein')) dialogueState.lastTopic = 'Jaunstein';

    // 3. Synthesize summary from metadata (instant, deterministic, factual)
    setTimeout(() => {
      if (thisRequestId !== currentRequestId) return;
      removeTypingIndicator();
      const summaryText = formatArchaeologicalSummary(top.meta, top.title, effectiveQuery);
      const cardHtml = renderSearchResultCard(results, summaryText, effectiveQuery);
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
        setTimeout(() => inputField && inputField.focus(), 200);
      }
      saveChatState();
    };

    const openChat = () => {
      if (chatWindow && !chatWindow.classList.contains('chat-open')) {
        chatWindow.classList.add('chat-open');
        saveChatState();
        setTimeout(() => inputField && inputField.focus(), 200);
      }
    };

    const closeChat = () => {
      if (chatWindow && chatWindow.classList.contains('chat-open')) {
        chatWindow.classList.remove('chat-open');
        saveChatState();
      }
    };

    if (triggerBtn) triggerBtn.addEventListener('click', toggleWindow);
    if (closeBtn) closeBtn.addEventListener('click', closeChat);

    const resetBtn = document.getElementById('chat-reset-btn');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        try {
          sessionStorage.removeItem(STORAGE_KEY_HISTORY);
        } catch (e) {}
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
          messagesContainer.innerHTML = getWelcomeMessageHtml();
          messagesContainer.scrollTop = 0;
        }
      });
    }

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && chatWindow && chatWindow.classList.contains('chat-open')) {
        closeChat();
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
        return;
      }

      // Graph Button & Inline Link Click (delegated)
      const graphBtn = e.target.closest('.graph-btn, .chat-secondary-graph-link');
      if (graphBtn) {
        if (e.ctrlKey || e.metaKey || e.shiftKey) return;

        const nodeId = graphBtn.getAttribute('data-node-id');
        if (!nodeId) return;

        if (isGraphPage) {
          // On the dedicated Knowledge Graph page: focus in-canvas without page reload!
          if (typeof window.focusGraphNode === 'function') {
            const focused = window.focusGraphNode(nodeId);
            if (focused !== false) {
              e.preventDefault();
              if (window.history && window.history.replaceState) {
                const newUrl = new URL(window.location.href);
                newUrl.searchParams.set('col', nodeId);
                window.history.replaceState({}, '', newUrl.toString());
              }
              showChatToast('Fundkomplex im Wissensgraphen fokussiert! 🕸️');
            }
          }
        } else {
          // Not on the graph page (e.g. index.html):
          // Save chat state so the assistant opens on the graph page with the conversation intact!
          saveChatState();
          // Allow normal link navigation to graphHref (graph/index.html?col=...)
        }
      }
    });

    // Check if on graph page with col/node deep-link parameter and active session
    if (isGraphPage) {
      const urlParams = new URLSearchParams(window.location.search);
      const colParam = urlParams.get('col') || urlParams.get('node');
      if (colParam && sessionStorage.getItem(STORAGE_KEY_OPEN) === 'true') {
        setTimeout(() => {
          showChatToast('Fundkomplex im Wissensgraphen fokussiert! 🕸️');
        }, 600);
      }
    }
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
  root.iuennaChat = {
    search: searchKnowledgeBase,
    submit: handleUserSubmit,
    renderCard: renderSearchResultCard,
    formatSummary: formatArchaeologicalSummary,
    cleanText: cleanArchaeologicalText,
    detectCategory: detectEntityCategory,
    toggle: () => {
      const trigger = document.getElementById('iuenna-chat-trigger');
      if (trigger) trigger.click();
    },
    open: () => {
      const chatWin = document.getElementById('iuenna-chat-window');
      if (chatWin && !chatWin.classList.contains('chat-open')) {
        const trigger = document.getElementById('iuenna-chat-trigger');
        if (trigger) trigger.click();
      }
    },
    close: () => {
      const closeBtn = document.getElementById('chat-close-btn');
      if (closeBtn) closeBtn.click();
    },
    showToast: showChatToast,
    getKbData: () => kbData,
    setKbData: (d) => { kbData = d; }
  };

})(typeof window !== 'undefined' ? window : this);
