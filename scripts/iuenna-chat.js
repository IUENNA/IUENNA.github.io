/**
 * iuenna-chat.js
 * --------------
 * Intuitiver Sammlungs- & Recherche-Assistent für das IUENNA-Projekt.
 * 
 * Sucht in Echtzeit in der Graphendatenbank (21.080 Knoten), im Web-GIS
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
            <div style="display: flex; align-items: center; gap: 6px; margin-top: 3px; flex-wrap: wrap;">
              <span id="chat-model-status" style="display: inline-flex; align-items: center; gap: 4px; font-size: 0.67rem; padding: 1px 6px; border-radius: 3px; background: rgba(255,255,255,0.16);">
                <i class="fa-solid fa-bolt" style="color: #4fc3f7;"></i> Schnellsuche &bull; Metadaten
              </span>
              <a href="byoai.html" target="_blank" rel="noopener noreferrer" class="chat-header-byoai-badge" title="Bring Your Own AI – Eigene KI anbinden">
                <i class="fa-solid fa-microchip"></i> BYOAI Hub ↗
              </a>
            </div>
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
              Stellen Sie eine Frage oder suchen Sie nach Objekten, Fundstellen und Plänen. Die Treffer führen Sie direkt zu den Daten im <strong>Wissensgraphen</strong>, im <strong>Web-GIS</strong> und in <strong>ARCHE</strong>.
            </p>
            <div class="chat-byoai-welcome-box" style="margin-top: 8px; padding: 7px 10px; background: rgba(106, 27, 154, 0.06); border: 1px solid rgba(106, 27, 154, 0.2); border-radius: 4px; font-size: 0.79rem; line-height: 1.4; color: #4a148c;">
              <i class="fa-solid fa-microchip" style="color: #6a1b9a;"></i> <strong>Bring Your Own AI (BYOAI):</strong> Sie möchten lieber Ihre eigene KI (Claude, ChatGPT, Ollama etc.) nutzen? Alle Bestände stehen offen über unser <a href="byoai.html" target="_blank" rel="noopener noreferrer" style="color: #6a1b9a; font-weight: 700; text-decoration: underline;">Model Context Protocol (MCP) &amp; OpenAPI</a> bereit.
            </div>
            <div class="chat-chips-container" style="margin-top: 8px;">
              <button type="button" class="chat-chip chat-chip-byoai" data-query="Was ist BYOAI?"><i class="fa-solid fa-microchip"></i> Was ist BYOAI?</button>
              <button type="button" class="chat-chip" data-query="Welche Literatur gibt es?" style="background: rgba(192, 57, 43, 0.07); border-color: rgba(192, 57, 43, 0.25); color: #c0392b; font-weight: 600;"><i class="fa-solid fa-book-bookmark"></i> 📚 Literatur (Zotero)</button>
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
          <input type="text" id="chat-input-field" class="chat-input-field" placeholder="Suchbegriff eingeben (z.B. 'Münzen', 'Hans Winkler', 'Inschriften')..." autocomplete="off">
          <button id="chat-send-btn" class="chat-send-btn" aria-label="Senden" title="Senden">
            <i class="fa-solid fa-paper-plane"></i>
          </button>
        </div>
        <div class="chat-privacy-footer" style="padding: 6px 14px; text-align: center; border-top: 1px solid var(--border-color); background: var(--bg-card); display: flex; flex-direction: column; gap: 2px;">
          <span style="font-size: 0.67rem; color: var(--text-muted); line-height: 1.35;">
            <i class="fa-solid fa-circle-check" style="color: #2e7d32;"></i> 100% Client-Side Metadaten-Recherche &bull; DSGVO-konform &bull; <a href="byoai.html" target="_blank" rel="noopener noreferrer" style="color: #6a1b9a; font-weight: 600; text-decoration: underline;"><i class="fa-solid fa-microchip"></i> BYOAI: Eigene KI anbinden ↗</a>
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

      tokens.forEach(tok => {
        const stem = getGermanStem(tok);
        const wordRegex = new RegExp(`(^|[^a-z0-9äöüß])${escapeRegExp(tok)}($|[^a-z0-9äöüß])`, 'i');
        const stemRegex = new RegExp(`(^|[^a-z0-9äöüß])${escapeRegExp(stem)}[a-z0-9äöüß]*($|[^a-z0-9äöüß])`, 'i');

        if (wordRegex.test(combined)) matchScore += 6;
        else if (stemRegex.test(combined)) matchScore += 4;
        else if (stem && stem.length >= 4 && combined.includes(stem)) matchScore += 2;

        if (wordRegex.test(titleLower)) {
          matchScore += 16;
          strongMatch = true;
        } else if (stem && (titleLower.includes(stem) || stemRegex.test(titleLower))) {
          matchScore += 12;
          strongMatch = true;
        }

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

      if (combined.includes(cleanQuery)) {
        matchScore += 15;
        strongMatch = true;
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

      if (type === 'find_complex') matchScore += 16;
      if (type === 'subcollection') matchScore += 14;
      if (type === 'site') matchScore += 10;
      if (type === 'folder') {
        matchScore += 8;
        if (rawItem && rawItem.type === 'folder_l2') matchScore += 6;
        else if (rawItem && rawItem.type === 'folder_l3') matchScore += 3;
        if (rawItem && rawItem.items && rawItem.items > 100) matchScore += 4;
      }

      if (matchScore > 8) {
        scoredResults.push({
          rawItem,
          type,
          title,
          score: matchScore,
          meta
        });
      }
    };

    // 1. Authoritative Archaeological Find Complexes
    const findComplexes = [
      {
        title: 'Münzschatzfund von Globasnitz (322 römische Münzen)',
        type_label: 'Archäologischer Fundkomplex',
        place: 'Globasnitz (vicus)',
        period: 'Spätantike (4. Jh. n. Chr.)',
        items: '322 römische Münzen',
        pid: 'https://hdl.handle.net/21.11115/0000-0016-7B3B-D',
        arche_url: 'https://hdl.handle.net/21.11115/0000-0016-7B3B-D',
        id: 'col_1792694',
        lat: 46.55694,
        lng: 14.70278,
        keywords: ['münzen', 'münzschatz', 'hortfund', 'globasnitz', '322', 'bronzemünzen', 'geld']
      },
      {
        title: 'Ostgräberfeld Globasnitz (440 spätantike Gräber)',
        type_label: 'Archäologischer Befund',
        place: 'Globasnitz',
        period: 'Spätantike (5.–6. Jh. n. Chr.)',
        items: '440 dokumentierte Gräber',
        pid: 'https://hdl.handle.net/21.11115/0000-0016-7B3B-D',
        arche_url: 'https://hdl.handle.net/21.11115/0000-0016-7B3B-D',
        id: 'col_1792694',
        lat: 46.55694,
        lng: 14.70278,
        keywords: ['gräberfeld', 'gräber', 'bestattungen', 'skelette', 'globasnitz', 'ostgräberfeld', 'pollak']
      },
      {
        title: 'Doppelkirchenanlage & Pilgerheiligtum Hemmaberg',
        type_label: 'Archäologischer Befund',
        place: 'Hemmaberg',
        period: 'Spätantike (5.–6. Jh. n. Chr.)',
        items: '5 Kirchenbauten & Mosaiken',
        pid: 'https://hdl.handle.net/21.11115/0000-0016-7B3A-E',
        arche_url: 'https://hdl.handle.net/21.11115/0000-0016-7B3A-E',
        id: 'col_1792693',
        lat: 46.55269,
        lng: 14.66768,
        keywords: ['doppelkirchen', 'doppelkirche', 'hemmaberg', 'kirchen', 'mosaik', 'mosaiken', 'glaser', 'pilgerzentrum']
      },
      {
        title: 'Römische Großvilla & Badeanlage St. Stefan',
        type_label: 'Archäologischer Befund',
        place: 'Sankt Stefan im Jauntal',
        period: 'Römische Kaiserzeit (1.–4. Jh. n. Chr.)',
        items: '2 ha Villenkomplex & Therme',
        pid: 'https://hdl.handle.net/21.11115/0000-0016-7B3E-A',
        arche_url: 'https://hdl.handle.net/21.11115/0000-0016-7B3E-A',
        id: 'col_1792697',
        lat: 46.59100,
        lng: 14.77300,
        keywords: ['villa', 'villenanlage', 'st. stefan', 'stefan', 'badeanlage', 'hypokaust', 'therme', 'šteben']
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

    // 3. Score Archaeological Sites (with precise coordinates)
    const siteGeoDetails = {
      'site_hemmaberg': { lat: 46.55269, lng: 14.66768, pid: 'https://hdl.handle.net/21.11115/0000-0016-7B3A-E' },
      'site_globasnitz': { lat: 46.55694, lng: 14.70278, pid: 'https://hdl.handle.net/21.11115/0000-0016-7B3B-D' },
      'site_sankt_stefan': { lat: 46.59100, lng: 14.77300, pid: 'https://hdl.handle.net/21.11115/0000-0016-7B3E-A' },
      'site_jaunstein': { lat: 46.55936, lng: 14.67102, pid: 'https://hdl.handle.net/21.11115/0000-0016-7B3C-C' }
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
        id: st.id,
        pid: geo.pid || 'https://id.acdh.oeaw.ac.at/iuenna',
        arche_url: geo.pid || 'https://id.acdh.oeaw.ac.at/iuenna',
        geonames: st.geonames
      }, st.keywords || []);
    });

    // 4. Score Graph Entities (All 21,080 nodes, prioritizing collections & primary archival folders)
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
      scoreItem(d, 'doc_type', d.name, {
        title: d.name,
        type_label: 'Materialgruppe',
        items: d.count ? `${d.count} Dokumente` : null,
        size: d.formats ? `Formate: ${d.formats}` : null,
        pid: 'https://id.acdh.oeaw.ac.at/iuenna',
        arche_url: 'https://id.acdh.oeaw.ac.at/iuenna'
      }, d.keywords || []);
    });

    scoredResults.sort((a, b) => b.score - a.score);
    const finalResults = scoredResults.slice(0, 3);
    finalResults.tokens = tokens;
    return finalResults;
  }

  // Deterministic metadata sentence generator (100% factual, 0ms latency, zero-overhead)
  function formatMetadataSummary(meta) {
    if (!meta) return '';
    const parts = [];
    if (meta.title) parts.push(`Zu **${meta.title}**`);
    if (meta.place) parts.push(`in ${meta.place}`);
    if (meta.items) {
      parts.push(`sind ${meta.items}`);
      if (meta.type_label) parts.push(`(${meta.type_label})`);
    } else if (meta.type_label) {
      parts.push(`(${meta.type_label})`);
    }
    if (meta.period) parts.push(`aus der Epoche *${meta.period}*`);
    parts.push(`in den IUENNA-Beständen dokumentiert.`);
    return parts.join(' ');
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
    } else if (text.includes('globasnitz')) {
      chips.push({ query: 'Wie viele Gräber wurden im Gräberfeld von Globasnitz ausgegraben?', label: '⚰️ 425 Gräber' });
      chips.push({ query: 'Wurden im Gräberfeld von Globasnitz künstliche Schädeldeformationen nachgewiesen?', label: '💀 Schädeldeformationen' });
      chips.push({ query: 'Was ist die Villenanlage von St. Stefan?', label: '🏡 Villa St. Stefan' });
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
  function renderSearchResultCard(results, summaryText) {
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
            <button type="button" class="chat-chip" data-query="Gräberfeld Globasnitz">💀 Globasnitz Gräber</button>
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

    // Action Buttons
    let linksHtml = '';
    
    // 1. Graph Link: Real anchor tag that opens the full Knowledge Graph Explorer at graph/index.html (with in-page canvas focus fallback)
    const graphNodeId = meta.id || '';
    const graphHref = `graph/index.html?col=${encodeURIComponent(graphNodeId)}&search=${encodeURIComponent(top.title || '')}`;
    linksHtml += `<a href="${graphHref}" target="_blank" rel="noopener noreferrer" class="chat-card-btn graph-btn" onclick="if(window.focusGraphNode && window.focusGraphNode('${graphNodeId}')){event.preventDefault();}"><i class="fa-solid fa-circle-nodes"></i> Im Wissensgraphen zeigen 🕸️</a>`;

    // 2. Web-GIS Link: Passes precise coordinates if available
    let gisUrl = 'wma/wma.html';
    const siteKey = ((meta.place || '') + ' ' + (top.title || '')).toLowerCase();
    if (meta.lat && meta.lng) {
      gisUrl += `?lat=${meta.lat}&lng=${meta.lng}&zoom=16`;
    } else if (siteKey.includes('hemmaberg')) {
      gisUrl += `?lat=46.55269&lng=14.66768&zoom=16`;
    } else if (siteKey.includes('globasnitz')) {
      gisUrl += `?lat=46.55694&lng=14.70278&zoom=16`;
    } else if (siteKey.includes('stefan') || siteKey.includes('winkler')) {
      gisUrl += `?lat=46.59100&lng=14.77300&zoom=16`;
    } else if (siteKey.includes('jaunstein')) {
      gisUrl += `?lat=46.55936&lng=14.67102&zoom=16`;
    }
    linksHtml += `<a href="${gisUrl}" target="_blank" rel="noopener noreferrer" class="chat-card-btn gis-btn"><i class="fa-solid fa-map-location-dot"></i> In Web-GIS ansehen 🗺️</a>`;
    
    // 3. ARCHE Link: Real persistent identifier
    let archeUrl = meta.pid || meta.arche_url || 'https://hdl.handle.net/21.11115/0000-0016-7B39-F';
    linksHtml += `<a href="${archeUrl}" target="_blank" rel="noopener noreferrer" class="chat-card-btn arche-btn"><i class="fa-solid fa-arrow-up-right-from-square"></i> In ARCHE öffnen ↗</a>`;

    // Weitere relevante Treffer im Wissensgraphen
    let secondaryHtml = '';
    if (results.length > 1) {
      secondaryHtml = `
        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border-color); font-size: 0.78rem;">
          <span style="color: var(--text-muted); font-weight: 600;">Weitere relevante Treffer im Wissensgraphen:</span>
          <ul style="margin: 4px 0 0 16px; padding: 0; color: var(--text-dark);">
            ${results.slice(1, 4).map(r => {
              const rId = (r.meta && r.meta.id) || '';
              const rGraphHref = `graph/index.html?col=${encodeURIComponent(rId)}&search=${encodeURIComponent(r.title || '')}`;
              return `
                <li style="margin-bottom: 3px;">
                  <strong>${escapeHtml(r.title)}</strong>
                  <a href="${rGraphHref}" target="_blank" rel="noopener noreferrer" style="color: var(--secondary); text-decoration: underline; margin-left: 4px; font-weight: 600;" onclick="if(window.focusGraphNode && window.focusGraphNode('${rId}')){event.preventDefault();}">[Im Graph 🕸️]</a>
                </li>
              `;
            }).join('')}
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

        <!-- 2. Crisp, short result card based purely on metadata -->
        <div class="chat-result-card" style="background: rgba(184, 142, 62, 0.05); border-left: 3px solid var(--secondary); padding: 9px 12px; border-radius: var(--radius-sm, 4px); margin-bottom: 8px;">
          <div style="font-size: 0.68rem; font-weight: 700; text-transform: uppercase; color: var(--secondary); letter-spacing: 0.04em; margin-bottom: 2px;">
            ${escapeHtml(meta.type_label || 'Sammlungsbestand')}
          </div>
          <h4 style="margin: 0 0 4px 0; font-size: 0.93rem; font-family: var(--font-header); color: var(--primary);">
            ${escapeHtml(top.title)}
          </h4>
          <p style="margin: 0; font-size: 0.84rem; line-height: 1.45; color: var(--text-dark);">
            ${summaryText}
          </p>

          <!-- Metadata Tags -->
          <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px;">
            ${meta.place ? `<span class="chat-card-tag"><i class="fa-solid fa-location-dot"></i> ${escapeHtml(meta.place)}</span>` : ''}
            ${meta.period ? `<span class="chat-card-tag"><i class="fa-solid fa-clock"></i> ${escapeHtml(meta.period)}</span>` : ''}
            ${meta.items ? `<span class="chat-card-tag"><i class="fa-solid fa-layer-group"></i> ${escapeHtml(meta.items)}</span>` : ''}
            ${meta.size ? `<span class="chat-card-tag"><i class="fa-solid fa-hard-drive"></i> ${escapeHtml(meta.size)}</span>` : ''}
          </div>
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
          <a href="byoai.html" target="_blank" rel="noopener noreferrer" style="color: #512da8; font-weight: 700; text-decoration: underline; white-space: nowrap;">
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
              <a href="byoai.html" target="_blank" rel="noopener noreferrer" class="chat-card-btn" style="background: #6a1b9a; color: #fff; text-decoration: none; font-weight: 600; font-size: 0.78rem; padding: 6px 12px; border-radius: 4px; display: inline-flex; align-items: center; gap: 5px;">
                <i class="fa-solid fa-microchip"></i> Zum BYOAI Hub (Setup &amp; MCP) ↗
              </a>
              <a href="data/openapi.json" target="_blank" rel="noopener noreferrer" class="chat-card-btn" style="background: var(--bg-card); color: var(--text-dark); border: 1px solid var(--border-color); text-decoration: none; font-size: 0.78rem; padding: 6px 10px; border-radius: 4px; display: inline-flex; align-items: center; gap: 5px;">
                <i class="fa-solid fa-code"></i> OpenAPI JSON
              </a>
              <a href="llms.txt" target="_blank" rel="noopener noreferrer" class="chat-card-btn" style="background: var(--bg-card); color: var(--text-dark); border: 1px solid var(--border-color); text-decoration: none; font-size: 0.78rem; padding: 6px 10px; border-radius: 4px; display: inline-flex; align-items: center; gap: 5px;">
                <i class="fa-solid fa-file-lines"></i> llms.txt
              </a>
            </div>
          </div>
        `);
      }, 150);
      return;
    }

    // Dialog Intent D: Literature / Publications / Zotero / Bibliography
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
                <li><strong>Hagmann &amp; Reiner (2025):</strong> <em>Das go!digital-3.0-Projekt IUENNA</em> (Rudolfinum).</li>
                <li><strong>Hagmann, Reiner &amp; Gugl (2025):</strong> <em>No End of History Yet! Long-Term Archiving in Roman Archaeology</em>.</li>
                <li><strong>Reiner &amp; Profant (2025):</strong> <em>Iuenna und Umgebung – Geophysikalische Prospektion</em>.</li>
                <li><strong>Glaser (2002 / 1991):</strong> <em>Die frühchristlichen Kirchen am Hemmaberg</em>.</li>
                <li><strong>Pollak (2023):</strong> <em>Der merowingerzeitliche Friedhof von Globasnitz</em>.</li>
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
      const summaryText = formatMetadataSummary(top.meta);
      const cardHtml = renderSearchResultCard(results, summaryText);
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
  root.iuennaChat = {
    search: searchKnowledgeBase,
    submit: handleUserSubmit,
    renderCard: renderSearchResultCard,
    formatSummary: formatMetadataSummary,
    getKbData: () => kbData,
    setKbData: (d) => { kbData = d; }
  };

})(typeof window !== 'undefined' ? window : this);
