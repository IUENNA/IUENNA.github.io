/**
 * Ask IUENNA
 * ----------
 * Site-wide, client-side conversational discovery assistant for IUENNA.
 *
 * Provenance policy:
 * - Entity discovery uses data/arche_search_index.json, generated directly from
 *   the ARCHE RDF export.
 * - File-level discovery uses data/arche_corpus_browser_index.json, a compact
 *   non-authoritative browser projection of the authoritative arche_corpus.json.
 * - Natural-language processing is deterministic and client-side: bilingual
 *   stopwords, light stemming, intent detection, synonym expansion and a small
 *   dialogue state are used only to improve retrieval.
 * - The assistant does not generate archaeological interpretations or factual
 *   syntheses. It presents indexed metadata and links back to ARCHE, the IUENNA
 *   Knowledge Graph, Web Mapping, and BYOAI/Remote MCP.
 */
(function () {
  'use strict';

  if (typeof window === 'undefined' || typeof document === 'undefined') return;
  if (document.getElementById('iuenna-chat-trigger')) return;

  const currentScript = document.currentScript || document.querySelector('script[src*="iuenna-chat.js"]');
  let basePath = '';
  if (currentScript && currentScript.getAttribute('src')) {
    const src = currentScript.getAttribute('src');
    if (src.startsWith('../')) basePath = '../';
    else if (src.startsWith('/')) basePath = '/';
  }
  if (!basePath) {
    const path = window.location.pathname.toLowerCase();
    if (path.includes('/graph/') || path.includes('/wma/')) basePath = '../';
  }

  const SEARCH_INDEX_URL = basePath + 'data/arche_search_index.json';
  const CORPUS_INDEX_URL = basePath + 'data/arche_corpus_browser_index.json';
  const BYOAI_URL = basePath + 'byoai.html';
  const GRAPH_URL = basePath + 'graph/index.html';
  const WMA_URL = basePath + 'wma/wma.html';
  const ARCHE_ROOT = 'https://id.acdh.oeaw.ac.at/iuenna';
  const ARCHE_BROWSER = 'https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/';
  const STORAGE_KEY_OPEN = 'iuenna_chat_open';
  const STORAGE_KEY_HISTORY = 'iuenna_chat_history';
  const STORAGE_KEY_DIALOGUE = 'iuenna_chat_dialogue_v31';

  let searchIndex = null;
  let searchIndexPromise = null;
  let corpusIndex = null;
  let corpusIndexPromise = null;

  const dialogueState = {
    lastQuery: '',
    lastResolvedQuery: '',
    lastEntityLabel: '',
    lastPlace: '',
    lastCategory: '',
    lastIntent: '',
    lastResultKind: '',
    lastArcheUrl: '',
    lastLat: null,
    lastLon: null,
    lastCreators: []
  };

  const STOPWORDS = new Set([
    'a','an','and','any','are','as','at','be','by','can','could','do','does','for','from','give','how','i','in','is','it','me','of','on','or','please','show','tell','the','there','to','us','was','were','what','where','which','who','with','would','you',
    'aber','als','am','an','auch','auf','aus','bei','bitte','da','das','dass','dem','den','der','des','die','dort','du','ein','eine','einem','einen','einer','eines','er','es','für','gib','gibt','haben','hat','hier','ich','im','in','ist','kann','können','man','mehr','mir','mit','nach','noch','oder','sag','sie','sind','so','über','um','und','uns','von','vom','war','was','welche','welcher','welches','wer','wie','wir','wo','zu','zum','zur'
  ]);

  const FOLLOWUP_WORDS = new Set([
    'also','and','auch','dazu','davon','diese','diesem','diesen','dort','mehr','more','other','related','them','there','these','those','weitere','weiteres','whatabout'
  ]);

  const FILE_HINTS = new Set([
    'archive','archived','bild','bilder','datei','dateien','document','documents','file','files','foto','fotos','image','images','plan','plans','photo','photograph','photographs','scan','scans','tif','tiff','jpg','jpeg','pdf','geopackage','gpkg','dxf','xlsx','csv','txt'
  ]);

  const SYNONYM_GROUPS = [
    ['foto','fotos','photo','photos','photograph','photographs','image','images','bild','bilder'],
    ['plan','plans','planzeichnung','zeichnung','drawings','drawing'],
    ['grab','gräber','graeber','grave','graves','burial','burials','bestattung','bestattungen'],
    ['publikation','publikationen','publication','publications','paper','papers','article','articles','literatur','literature'],
    ['person','personen','people','researcher','researchers','author','authors','creator','creators'],
    ['ort','orte','place','places','site','sites','fundort','fundorte'],
    ['geodaten','geodata','gis','geopackage','gpkg','spatial'],
    ['karte','karten','map','maps','mapping','webgis','wma']
  ];

  const SYNONYM_MAP = (() => {
    const map = new Map();
    SYNONYM_GROUPS.forEach(group => {
      group.forEach(term => map.set(term, group));
    });
    return map;
  })();

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function normalize(value) {
    return String(value == null ? '' : value)
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/ß/g, 'ss')
      .replace(/[^a-z0-9]+/g, ' ')
      .trim();
  }

  function lightStem(token) {
    let word = normalize(token);
    if (word.length < 5) return word;
    const suffixes = [
      'ierungen','ierung','schaften','schaft','ungen','innen','ischen','ischer','isches','ische','keiten','keit','heiten','heit',
      'ments','ment','ations','ation','ographs','ograph','ies','ing','ers','er','en','em','es','e','s','n'
    ];
    for (const suffix of suffixes) {
      if (word.endsWith(suffix) && word.length - suffix.length >= 4) {
        word = word.slice(0, -suffix.length);
        break;
      }
    }
    return word;
  }

  function baseQueryTokens(query) {
    const raw = normalize(query).split(/\s+/).filter(Boolean);
    const filtered = raw.filter(token => !STOPWORDS.has(token));
    return filtered.length ? filtered : raw;
  }

  function expandedTokens(query) {
    const base = baseQueryTokens(query);
    const out = [];
    const seen = new Set();
    for (const token of base) {
      const variants = SYNONYM_MAP.get(token) || [token];
      for (const variant of variants) {
        const normalized = normalize(variant);
        if (!normalized || seen.has(normalized)) continue;
        seen.add(normalized);
        out.push({ raw: normalized, stem: lightStem(normalized), primary: normalized === token });
      }
    }
    return out;
  }

  function detectIntent(query) {
    const nq = normalize(query);
    const tokens = new Set(nq.split(/\s+/).filter(Boolean));
    if (/\b(who created|who made|creator|creators|created by|wer hat|erstellt|urheber|autor|autoren)\b/.test(nq)) return 'creator';
    if (/\b(show|open|zeige|offne|oeffne)\b.*\b(map|karte|webgis|wma)\b/.test(nq) || /\b(map|karte|webgis|wma)\b/.test(nq)) return 'show_map';
    if (/\b(publication|publications|paper|papers|article|articles|literature|publikation|publikationen|literatur)\b/.test(nq)) return 'find_publications';
    if (/\b(person|people|researcher|researchers|author|authors|personen|wer)\b/.test(nq)) return 'find_people';
    if (/\b(related|relations|connections|connected|zusammenhang|verknupft|verknuepft|beziehungen)\b/.test(nq)) return 'related';
    if (/\b(count|how many|wieviele|wie viele|anzahl)\b/.test(nq)) return 'count';
    for (const token of tokens) if (FILE_HINTS.has(token)) return 'find_files';
    return 'discover';
  }

  function looksLikeFollowUp(query) {
    const nq = normalize(query);
    const tokens = nq.split(/\s+/).filter(Boolean);
    if (!tokens.length) return false;
    if (tokens.length <= 4 && tokens.some(token => FOLLOWUP_WORDS.has(token))) return true;
    if (/^(and|also|what about|und|auch|dazu|davon|dort|mehr|weitere|other|more)\b/.test(nq)) return true;
    if (tokens.length <= 3 && dialogueState.lastEntityLabel && !containsKnownContext(nq)) return true;
    return false;
  }

  function containsKnownContext(normalizedQuery) {
    const contexts = [dialogueState.lastEntityLabel, dialogueState.lastPlace].map(normalize).filter(Boolean);
    return contexts.some(context => normalizedQuery.includes(context));
  }

  function resolveQuery(query, intent) {
    const nq = normalize(query);
    let context = '';
    if (dialogueState.lastPlace) context = dialogueState.lastPlace;
    else if (dialogueState.lastEntityLabel) context = dialogueState.lastEntityLabel;
    if (!context || containsKnownContext(nq)) return query;
    const explicitContextualIntent = ['find_files','find_publications','find_people','creator','show_map','related','count'].includes(intent);
    if (looksLikeFollowUp(query) || explicitContextualIntent) return `${query} ${context}`.trim();
    return query;
  }

  function extractDecade(query) {
    const match = normalize(query).match(/\b((?:18|19|20)\d)0s\b/);
    if (!match) return null;
    const start = Number(match[1] + '0');
    return { start, end: start + 9 };
  }

  function matchesDecade(item, query) {
    const decade = extractDecade(query);
    if (!decade) return true;
    const values = [item.date, item.title, item.filename, item.folder, Array.isArray(item.path) ? item.path.join(' ') : item.path]
      .filter(Boolean).join(' ');
    const years = String(values).match(/\b(?:18|19|20)\d{2}\b/g) || [];
    if (!years.length) return false;
    return years.some(year => Number(year) >= decade.start && Number(year) <= decade.end);
  }

  async function fetchJson(url) {
    const response = await fetch(url, { credentials: 'same-origin' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  function loadSearchIndex() {
    if (searchIndex) return Promise.resolve(searchIndex);
    if (!searchIndexPromise) {
      searchIndexPromise = fetchJson(SEARCH_INDEX_URL).then(data => {
        searchIndex = Array.isArray(data) ? data : [];
        return searchIndex;
      }).catch(error => {
        searchIndexPromise = null;
        throw error;
      });
    }
    return searchIndexPromise;
  }

  function loadCorpusIndex() {
    if (corpusIndex) return Promise.resolve(corpusIndex);
    if (!corpusIndexPromise) {
      corpusIndexPromise = fetchJson(CORPUS_INDEX_URL).then(data => {
        corpusIndex = data && Array.isArray(data.resources) ? data.resources : [];
        return corpusIndex;
      }).catch(error => {
        corpusIndexPromise = null;
        throw error;
      });
    }
    return corpusIndexPromise;
  }

  function tokenMatchScore(text, token) {
    if (!text || !token) return 0;
    if (text === token.raw) return token.primary ? 20 : 8;
    if (text.startsWith(token.raw)) return token.primary ? 12 : 5;
    if (text.includes(token.raw)) return token.primary ? 8 : 3;
    if (token.stem && token.stem.length >= 4 && text.includes(token.stem)) return token.primary ? 5 : 2;
    return 0;
  }

  function categoryBoost(item, intent) {
    const category = normalize([item.type, item.category, item.sublabel].filter(Boolean).join(' '));
    if (intent === 'find_publications' && /publication|publikation|literature|article|paper/.test(category)) return 55;
    if (intent === 'find_people' && /person|people|creator|author|researcher/.test(category)) return 55;
    if (intent === 'show_map' && /place|site|ort|location/.test(category)) return 25;
    return 0;
  }

  function scoreEntity(item, tokens, rawQuery, intent) {
    const label = normalize(item.label || '');
    const sublabel = normalize(item.sublabel || '');
    const category = normalize(item.category || '');
    const code = normalize(item.code || '');
    const tokenText = normalize((item.tokens || []).join(' '));
    const archeId = normalize(item.arche_id || '');
    const fields = [label, sublabel, category, code, tokenText, archeId];
    let score = categoryBoost(item, intent);
    let matchedPrimary = 0;
    const primaryTokens = tokens.filter(t => t.primary);
    for (const token of tokens) {
      let best = 0;
      for (const field of fields) best = Math.max(best, tokenMatchScore(field, token));
      if (best) {
        score += best;
        if (token.primary) matchedPrimary += 1;
      }
      if (label === token.raw || code === token.raw || archeId === token.raw) score += token.primary ? 45 : 10;
      else if (label.startsWith(token.raw) || code.startsWith(token.raw)) score += token.primary ? 25 : 6;
    }
    if (!matchedPrimary && primaryTokens.length) return 0;
    if (primaryTokens.length > 1 && matchedPrimary === primaryTokens.length) score += 40;
    const nq = normalize(rawQuery);
    if (nq && label === nq) score += 80;
    else if (nq && label.includes(nq)) score += 35;
    return score;
  }

  function searchEntities(query, limit = 8, intent = 'discover') {
    const tokens = expandedTokens(query);
    if (!tokens.length || !searchIndex) return [];
    return searchIndex
      .map(item => ({ item, score: scoreEntity(item, tokens, query, intent) }))
      .filter(entry => entry.score > 0)
      .sort((a, b) => b.score - a.score || String(a.item.label || '').localeCompare(String(b.item.label || '')))
      .slice(0, limit)
      .map(entry => entry.item);
  }

  function scoreResource(item, tokens, rawQuery) {
    const subjects = Array.isArray(item.subjs) ? item.subjs.join(' ') : (item.subjs || '');
    const path = Array.isArray(item.path) ? item.path.join(' ') : (item.path || '');
    const title = normalize(item.title || item.filename || '');
    const fields = [item.title, item.filename, item.place, item.folder, item.col, item.type, item.ftype, item.date, subjects, path, item.arche_id]
      .filter(Boolean).map(normalize);
    let score = 0;
    let matchedPrimary = 0;
    const primaryTokens = tokens.filter(t => t.primary && !/^\d{4}$/.test(t.raw) && !/^\d{4}s$/.test(t.raw));
    for (const token of tokens) {
      if (/^\d{4}s$/.test(token.raw)) continue;
      let best = 0;
      for (const field of fields) best = Math.max(best, tokenMatchScore(field, token));
      if (best) {
        score += best;
        if (token.primary && !/^\d{4}$/.test(token.raw)) matchedPrimary += 1;
      }
      if (title === token.raw) score += token.primary ? 40 : 8;
      else if (title.startsWith(token.raw)) score += token.primary ? 25 : 5;
      else if (title.includes(token.raw)) score += token.primary ? 16 : 3;
    }
    if (primaryTokens.length && !matchedPrimary) return 0;
    if (primaryTokens.length > 1 && matchedPrimary === primaryTokens.length) score += 30;
    const nq = normalize(rawQuery);
    if (nq && title === nq) score += 60;
    else if (nq && title.includes(nq)) score += 25;
    return score;
  }

  function searchResources(query, limit = 8) {
    const tokens = expandedTokens(query);
    if (!tokens.length || !corpusIndex) return [];
    return corpusIndex
      .filter(item => matchesDecade(item, query))
      .map(item => ({ item, score: scoreResource(item, tokens, query) }))
      .filter(entry => entry.score > 0)
      .sort((a, b) => b.score - a.score || String(a.item.title || '').localeCompare(String(b.item.title || '')))
      .slice(0, limit)
      .map(entry => entry.item);
  }

  function archeUrlForEntity(item) {
    if (item && item.meta && item.meta.pid) return item.meta.pid;
    const id = String(item && item.arche_id || '').replace(/^.*\//, '');
    if (/^\d+$/.test(id)) return ARCHE_BROWSER + encodeURIComponent(id);
    return ARCHE_ROOT;
  }

  function archeUrlForResource(item) {
    if (item && item.pid) return item.pid;
    const id = String(item && item.arche_id || '').replace(/^.*\//, '');
    if (/^\d+$/.test(id)) return ARCHE_BROWSER + encodeURIComponent(id);
    return ARCHE_ROOT;
  }

  function valueRow(label, value) {
    if (value == null || value === '' || (Array.isArray(value) && !value.length)) return '';
    const shown = Array.isArray(value) ? value.join(', ') : value;
    return `<div style="margin-top:3px;"><strong>${escapeHtml(label)}:</strong> ${escapeHtml(shown)}</div>`;
  }

  function renderEntity(item) {
    const meta = item.meta || {};
    const label = item.label || item.arche_id || 'ARCHE entity';
    const graphHref = `${GRAPH_URL}?search=${encodeURIComponent(label)}`;
    const archeHref = archeUrlForEntity(item);
    const rows = [
      valueRow('Type', item.type || item.category), valueRow('Items', meta.items), valueRow('Size', meta.size),
      valueRow('Years', meta.years || meta.year), valueRow('Creators', meta.creators), valueRow('Authors', meta.authors),
      valueRow('Publisher', meta.publisher), valueRow('Citation', meta.citation), valueRow('ARCHE ID', item.arche_id)
    ].join('');
    let mapButton = '';
    if (Number.isFinite(Number(meta.lat)) && Number.isFinite(Number(meta.lon))) {
      mapButton = `<a class="btn btn-outline" style="padding:5px 9px;font-size:.72rem;" href="${WMA_URL}?lat=${encodeURIComponent(meta.lat)}&lng=${encodeURIComponent(meta.lon)}&zoom=16"><i class="fa-solid fa-map-location-dot"></i> Web Mapping</a>`;
    }
    return `
      <article style="border:1px solid var(--border-color);border-radius:8px;padding:10px 12px;margin:8px 0;background:var(--bg-card);">
        <div style="font-weight:700;line-height:1.3;">${escapeHtml(label)}</div>
        <div style="font-size:.76rem;color:var(--text-muted);line-height:1.45;margin-top:5px;">${rows}</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;">
          <a class="btn btn-secondary" style="padding:5px 9px;font-size:.72rem;" href="${escapeHtml(archeHref)}" target="_blank" rel="noopener"><i class="fa-solid fa-database"></i> ARCHE</a>
          <a class="btn btn-outline" style="padding:5px 9px;font-size:.72rem;" href="${graphHref}"><i class="fa-solid fa-circle-nodes"></i> Knowledge Graph</a>
          ${mapButton}
        </div>
      </article>`;
  }

  function renderResource(item) {
    const label = item.title || item.filename || item.id || 'Archived resource';
    const archeHref = archeUrlForResource(item);
    const graphHref = `${GRAPH_URL}?search=${encodeURIComponent(label)}`;
    const rows = [
      valueRow('File', item.filename), valueRow('Type', item.type || item.ftype), valueRow('Place', item.place),
      valueRow('Collection', item.col), valueRow('Folder', item.folder), valueRow('Date', item.date),
      valueRow('Size', item.formatted_size), valueRow('ARCHE ID', item.arche_id)
    ].join('');
    return `
      <article style="border:1px solid var(--border-color);border-radius:8px;padding:10px 12px;margin:8px 0;background:var(--bg-card);">
        <div style="font-weight:700;line-height:1.3;">${escapeHtml(label)}</div>
        <div style="font-size:.76rem;color:var(--text-muted);line-height:1.45;margin-top:5px;">${rows}</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;">
          <a class="btn btn-secondary" style="padding:5px 9px;font-size:.72rem;" href="${escapeHtml(archeHref)}" target="_blank" rel="noopener"><i class="fa-solid fa-database"></i> ARCHE</a>
          <a class="btn btn-outline" style="padding:5px 9px;font-size:.72rem;" href="${graphHref}"><i class="fa-solid fa-circle-nodes"></i> Knowledge Graph</a>
        </div>
      </article>`;
  }

  function inferPlaceFromEntity(item) {
    const meta = item && item.meta || {};
    const candidates = [meta.place, meta.location, item && item.sublabel, item && item.label].filter(Boolean);
    const knownPlaces = ['Hemmaberg','Globasnitz','Iuenna','Jaunstein','Sankt Stefan','St. Stefan','Jauntal','Podjuna'];
    const joined = candidates.join(' ');
    const found = knownPlaces.find(place => normalize(joined).includes(normalize(place)));
    return found || meta.place || '';
  }

  function updateStateFromEntity(item, query, resolvedQuery, intent) {
    if (!item) return;
    const meta = item.meta || {};
    dialogueState.lastQuery = query;
    dialogueState.lastResolvedQuery = resolvedQuery;
    dialogueState.lastEntityLabel = item.label || dialogueState.lastEntityLabel;
    dialogueState.lastPlace = inferPlaceFromEntity(item) || dialogueState.lastPlace;
    dialogueState.lastCategory = item.type || item.category || '';
    dialogueState.lastIntent = intent;
    dialogueState.lastResultKind = 'entity';
    dialogueState.lastArcheUrl = archeUrlForEntity(item);
    dialogueState.lastLat = Number.isFinite(Number(meta.lat)) ? Number(meta.lat) : null;
    dialogueState.lastLon = Number.isFinite(Number(meta.lon)) ? Number(meta.lon) : null;
    const creators = meta.creators || meta.authors || [];
    dialogueState.lastCreators = Array.isArray(creators) ? creators : (creators ? [creators] : []);
    persistDialogueState();
  }

  function updateStateFromResource(item, query, resolvedQuery, intent) {
    if (!item) return;
    dialogueState.lastQuery = query;
    dialogueState.lastResolvedQuery = resolvedQuery;
    dialogueState.lastPlace = item.place || dialogueState.lastPlace;
    dialogueState.lastCategory = item.type || item.ftype || '';
    dialogueState.lastIntent = intent;
    dialogueState.lastResultKind = 'resource';
    dialogueState.lastArcheUrl = archeUrlForResource(item);
    dialogueState.lastCreators = [];
    dialogueState.lastLat = null;
    dialogueState.lastLon = null;
    persistDialogueState();
  }

  function persistDialogueState() {
    try { sessionStorage.setItem(STORAGE_KEY_DIALOGUE, JSON.stringify(dialogueState)); } catch (_) {}
  }

  function restoreDialogueState() {
    try {
      const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY_DIALOGUE) || '{}');
      Object.keys(dialogueState).forEach(key => {
        if (Object.prototype.hasOwnProperty.call(saved, key)) dialogueState[key] = saved[key];
      });
    } catch (_) {}
  }

  function resetDialogueState() {
    Object.assign(dialogueState, {
      lastQuery: '', lastResolvedQuery: '', lastEntityLabel: '', lastPlace: '', lastCategory: '',
      lastIntent: '', lastResultKind: '', lastArcheUrl: '', lastLat: null, lastLon: null, lastCreators: []
    });
    try { sessionStorage.removeItem(STORAGE_KEY_DIALOGUE); } catch (_) {}
  }

  function contextLabel() {
    return dialogueState.lastPlace || dialogueState.lastEntityLabel || '';
  }

  function followUpHtml(item, kind) {
    const meta = item && item.meta || {};
    const label = kind === 'entity'
      ? (item.label || contextLabel())
      : (item.place || dialogueState.lastPlace || item.col || dialogueState.lastEntityLabel || '');
    if (!label) return '';
    const chips = [];
    chips.push(`<button type="button" class="chat-chip" data-query="photos ${escapeHtml(label)}"><i class="fa-solid fa-image"></i> Photos</button>`);
    chips.push(`<button type="button" class="chat-chip" data-query="plans ${escapeHtml(label)}"><i class="fa-solid fa-map"></i> Plans</button>`);
    chips.push(`<button type="button" class="chat-chip" data-query="publications ${escapeHtml(label)}"><i class="fa-solid fa-book"></i> Publications</button>`);
    chips.push(`<button type="button" class="chat-chip" data-query="people ${escapeHtml(label)}"><i class="fa-solid fa-user-group"></i> People</button>`);
    const lat = kind === 'entity' ? meta.lat : dialogueState.lastLat;
    const lon = kind === 'entity' ? meta.lon : dialogueState.lastLon;
    if (Number.isFinite(Number(lat)) && Number.isFinite(Number(lon))) {
      chips.push(`<button type="button" class="chat-chip" data-query="show ${escapeHtml(label)} on map"><i class="fa-solid fa-map-location-dot"></i> Map</button>`);
    }
    return `<div class="chat-chips-container" style="margin-top:10px;">${chips.join('')}</div>`;
  }

  function messagesEl() { return document.getElementById('chat-messages'); }

  function appendMessage(html, who) {
    const area = messagesEl();
    if (!area) return;
    const wrapper = document.createElement('div');
    wrapper.className = `chat-msg ${who === 'user' ? 'user' : 'bot'}`;
    wrapper.innerHTML = `<div class="chat-msg-bubble">${html}</div><span class="chat-msg-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>`;
    area.appendChild(wrapper);
    area.scrollTop = area.scrollHeight;
    bindChipEvents();
    saveChatState();
  }

  function showTyping(text) {
    removeTyping();
    const area = messagesEl();
    if (!area) return;
    const el = document.createElement('div');
    el.id = 'chat-typing-indicator-el';
    el.className = 'chat-typing-indicator';
    el.innerHTML = `<span style="font-size:.74rem;margin-right:5px;">${escapeHtml(text || 'Searching metadata')}</span><span class="chat-typing-dot"></span><span class="chat-typing-dot"></span><span class="chat-typing-dot"></span>`;
    area.appendChild(el);
    area.scrollTop = area.scrollHeight;
  }

  function removeTyping() {
    const el = document.getElementById('chat-typing-indicator-el');
    if (el) el.remove();
  }

  function saveChatState() {
    try {
      const win = document.getElementById('iuenna-chat-window');
      sessionStorage.setItem(STORAGE_KEY_OPEN, win && win.classList.contains('chat-open') ? 'true' : 'false');
      const area = messagesEl();
      if (area) {
        const clone = area.cloneNode(true);
        const typing = clone.querySelector('#chat-typing-indicator-el');
        if (typing) typing.remove();
        sessionStorage.setItem(STORAGE_KEY_HISTORY, clone.innerHTML);
      }
      persistDialogueState();
    } catch (_) {}
  }

  function restoreChatState() {
    restoreDialogueState();
    try {
      const area = messagesEl();
      const history = sessionStorage.getItem(STORAGE_KEY_HISTORY);
      if (history && area) area.innerHTML = history;
      if (sessionStorage.getItem(STORAGE_KEY_OPEN) === 'true') {
        const win = document.getElementById('iuenna-chat-window');
        if (win) win.classList.add('chat-open');
      }
    } catch (_) {}
  }

  function welcomeHtml() {
    return `
      <p><strong>Ask IUENNA</strong></p>
      <p style="margin-top:6px;font-size:.84rem;line-height:1.45;">Search ARCHE-derived IUENNA metadata conversationally. You can ask follow-up questions such as <em>“Any photographs?”</em>, <em>“And from the 1980s?”</em> or <em>“Who created them?”</em>. Archaeological interpretations are not generated here; results link back to their source records.</p>
      <div class="chat-chips-container" style="margin-top:10px;">
        <button type="button" class="chat-chip" data-query="Hemmaberg"><i class="fa-solid fa-location-dot"></i> Hemmaberg</button>
        <button type="button" class="chat-chip" data-query="Globasnitz"><i class="fa-solid fa-location-dot"></i> Globasnitz</button>
        <button type="button" class="chat-chip" data-query="Jaunstein"><i class="fa-solid fa-location-dot"></i> Jaunstein</button>
        <button type="button" class="chat-chip" data-query="photos Hemmaberg"><i class="fa-solid fa-image"></i> Photos</button>
        <button type="button" class="chat-chip chat-chip-byoai" data-query="__byoai"><i class="fa-solid fa-microchip"></i> BYOAI / Remote MCP</button>
      </div>`;
  }

  function injectUi() {
    const trigger = document.createElement('button');
    trigger.id = 'iuenna-chat-trigger';
    trigger.type = 'button';
    trigger.setAttribute('aria-label', 'Open Ask IUENNA');
    trigger.innerHTML = `<span class="chat-trigger-icon">🏺</span><span>Ask IUENNA</span><span class="chat-trigger-badge">Conversational</span>`;
    document.body.appendChild(trigger);

    const win = document.createElement('div');
    win.id = 'iuenna-chat-window';
    win.setAttribute('role', 'dialog');
    win.setAttribute('aria-label', 'Ask IUENNA conversational metadata assistant');
    win.innerHTML = `
      <div class="chat-header">
        <div class="chat-header-info">
          <div class="chat-header-avatar">🏺</div>
          <div>
            <h3 class="chat-header-title">Ask IUENNA</h3>
            <p class="chat-header-sub">Conversational ARCHE metadata discovery</p>
            <div style="display:flex;align-items:center;gap:6px;margin-top:3px;flex-wrap:wrap;">
              <span style="display:inline-flex;align-items:center;gap:4px;font-size:.67rem;padding:1px 6px;border-radius:3px;background:rgba(255,255,255,.16);"><i class="fa-solid fa-shield-halved" style="color:#9fe3b1;"></i> grounded metadata only</span>
              <a href="${BYOAI_URL}" class="chat-header-byoai-badge" title="Connect your own AI through IUENNA Remote MCP"><i class="fa-solid fa-microchip"></i> BYOAI ↗</a>
            </div>
          </div>
        </div>
        <div class="chat-header-actions" style="display:flex;align-items:center;gap:6px;">
          <button class="chat-header-action-btn" id="chat-reset-btn" aria-label="Reset Ask IUENNA" title="Clear this tab's session" style="background:none;border:none;color:rgba(255,255,255,.78);cursor:pointer;padding:4px 6px;font-size:.85rem;"><i class="fa-solid fa-arrow-rotate-left"></i></button>
          <button class="chat-close-btn" id="chat-close-btn" aria-label="Close Ask IUENNA" title="Close"><i class="fa-solid fa-xmark"></i></button>
        </div>
      </div>
      <div class="chat-messages" id="chat-messages">
        <div class="chat-msg bot"><div class="chat-msg-bubble">${welcomeHtml()}</div><span class="chat-msg-time">Now</span></div>
      </div>
      <div class="chat-input-area">
        <div class="chat-input-row">
          <input type="text" id="chat-input-field" class="chat-input-field" placeholder="Ask about IUENNA metadata…" autocomplete="off" aria-label="Ask IUENNA">
          <button id="chat-send-btn" class="chat-send-btn" type="button" aria-label="Search"><i class="fa-solid fa-paper-plane"></i></button>
        </div>
        <div class="chat-privacy-footer" style="padding:5px 10px;text-align:center;display:flex;flex-direction:column;gap:2px;">
          <span style="font-size:.67rem;line-height:1.35;">Client-side NLP + metadata search · session context stored only in this tab · <a href="${BYOAI_URL}" style="font-weight:600;">Remote MCP / BYOAI</a></span>
        </div>
      </div>`;
    document.body.appendChild(win);

    restoreChatState();
    bindEvents();
    loadSearchIndex().catch(() => {});
  }

  function bindEvents() {
    const trigger = document.getElementById('iuenna-chat-trigger');
    const win = document.getElementById('iuenna-chat-window');
    const close = document.getElementById('chat-close-btn');
    const reset = document.getElementById('chat-reset-btn');
    const send = document.getElementById('chat-send-btn');
    const input = document.getElementById('chat-input-field');
    trigger.addEventListener('click', () => {
      win.classList.add('chat-open'); saveChatState(); setTimeout(() => input.focus(), 50);
    });
    close.addEventListener('click', () => { win.classList.remove('chat-open'); saveChatState(); });
    reset.addEventListener('click', () => {
      const area = messagesEl();
      area.innerHTML = `<div class="chat-msg bot"><div class="chat-msg-bubble">${welcomeHtml()}</div><span class="chat-msg-time">Now</span></div>`;
      try { sessionStorage.removeItem(STORAGE_KEY_HISTORY); } catch (_) {}
      resetDialogueState(); bindChipEvents(); saveChatState();
    });
    send.addEventListener('click', submitQuery);
    input.addEventListener('keydown', event => {
      if (event.key === 'Enter') submitQuery();
      if (event.key === 'Escape') { win.classList.remove('chat-open'); saveChatState(); }
    });
    bindChipEvents();
  }

  function bindChipEvents() {
    document.querySelectorAll('#iuenna-chat-window .chat-chip').forEach(button => {
      if (button.dataset.bound === '1') return;
      button.dataset.bound = '1';
      button.addEventListener('click', () => {
        const query = button.dataset.query || '';
        if (query === '__byoai') { window.location.href = BYOAI_URL; return; }
        const input = document.getElementById('chat-input-field');
        input.value = query; submitQuery();
      });
    });
  }

  function renderContextNotice(query, resolvedQuery) {
    if (normalize(query) === normalize(resolvedQuery)) return '';
    const context = contextLabel();
    if (!context) return '';
    return `<p style="font-size:.72rem;color:var(--text-muted);margin-top:4px;"><i class="fa-solid fa-link"></i> Follow-up resolved in the context of <strong>${escapeHtml(context)}</strong>.</p>`;
  }

  function handleContextAction(intent, query, resolvedQuery) {
    if (intent === 'show_map' && Number.isFinite(Number(dialogueState.lastLat)) && Number.isFinite(Number(dialogueState.lastLon))) {
      const label = contextLabel() || 'current result';
      const href = `${WMA_URL}?lat=${encodeURIComponent(dialogueState.lastLat)}&lng=${encodeURIComponent(dialogueState.lastLon)}&zoom=16`;
      appendMessage(`<p><strong>${escapeHtml(label)}</strong> can be opened directly in IUENNA Web Mapping.</p>${renderContextNotice(query, resolvedQuery)}<p style="margin-top:8px;"><a class="btn btn-secondary" style="padding:6px 10px;font-size:.75rem;" href="${href}"><i class="fa-solid fa-map-location-dot"></i> Open Web Mapping</a></p>`, 'bot');
      return true;
    }
    if (intent === 'creator' && dialogueState.lastResultKind === 'entity' && dialogueState.lastCreators && dialogueState.lastCreators.length) {
      const label = contextLabel() || dialogueState.lastEntityLabel || 'current record';
      appendMessage(`<p><strong>Creator / author metadata for ${escapeHtml(label)}</strong></p><p style="margin-top:6px;">${escapeHtml(dialogueState.lastCreators.join(', '))}</p>${renderContextNotice(query, resolvedQuery)}<p style="font-size:.7rem;color:var(--text-muted);margin-top:8px;">This is metadata from the previously matched ARCHE-derived record, not an inferred attribution.</p>`, 'bot');
      return true;
    }
    return false;
  }

  async function submitQuery() {
    const input = document.getElementById('chat-input-field');
    const query = (input.value || '').trim();
    if (!query) return;
    const intent = detectIntent(query);
    const resolvedQuery = resolveQuery(query, intent);
    appendMessage(`<p>${escapeHtml(query)}</p>`, 'user');
    input.value = '';
    if (handleContextAction(intent, query, resolvedQuery)) return;
    if (intent === 'find_files') {
      await searchFiles(resolvedQuery, query, intent);
      return;
    }
    showTyping('Resolving query against ARCHE-derived metadata');
    try {
      await loadSearchIndex();
      const results = searchEntities(resolvedQuery, 8, intent);
      removeTyping();
      if (!results.length) {
        await searchFiles(resolvedQuery, query, intent);
        return;
      }
      const top = results[0];
      updateStateFromEntity(top, query, resolvedQuery, intent);
      const cards = results.map(renderEntity).join('');
      const totalText = intent === 'count'
        ? `<p style="font-size:.78rem;margin-top:4px;">The discovery index returned <strong>${results.length}</strong> top matches. This is a ranked discovery result, not a corpus-wide scholarly count.</p>` : '';
      appendMessage(`
        <p><strong>Metadata matches</strong></p>
        ${renderContextNotice(query, resolvedQuery)}
        ${totalText}
        <p style="font-size:.78rem;color:var(--text-muted);margin-top:4px;">These records are derived from the ARCHE metadata export. No archaeological interpretation has been generated.</p>
        ${cards}
        <button type="button" class="chat-chip" data-query="files ${escapeHtml(contextLabel() || query)}" style="margin-top:8px;"><i class="fa-solid fa-file"></i> Search archived files</button>
        ${followUpHtml(top, 'entity')}
        <p style="font-size:.7rem;color:var(--text-muted);margin-top:8px;">For scholarly reuse, follow the ARCHE record and check its citation, rights statement and access conditions.</p>
      `, 'bot');
    } catch (error) {
      removeTyping();
      appendMessage(`<p><strong>Metadata search is temporarily unavailable.</strong></p><p style="font-size:.78rem;margin-top:5px;">You can still use the <a href="${BYOAI_URL}">BYOAI / Remote MCP</a> interface or open <a href="${ARCHE_ROOT}" target="_blank" rel="noopener">ARCHE</a>.</p>`, 'bot');
    }
  }

  async function searchFiles(resolvedQuery, originalQuery, intent) {
    showTyping('Searching the archived-file discovery index');
    try {
      await loadCorpusIndex();
      const resources = searchResources(resolvedQuery, 8);
      removeTyping();
      if (!resources.length) {
        appendMessage(`<p>No matching record was found in the archived-file discovery index for <strong>${escapeHtml(originalQuery)}</strong>.</p>${renderContextNotice(originalQuery, resolvedQuery)}<p style="font-size:.78rem;margin-top:5px;">Try a place name, collection title, person, dataset, publication, filename or ARCHE identifier. For advanced queries, use <a href="${BYOAI_URL}">IUENNA Remote MCP / BYOAI</a>.</p>`, 'bot');
        return;
      }
      const top = resources[0];
      updateStateFromResource(top, originalQuery, resolvedQuery, intent);
      appendMessage(`
        <p><strong>Archived-file matches</strong></p>
        ${renderContextNotice(originalQuery, resolvedQuery)}
        <p style="font-size:.78rem;color:var(--text-muted);margin-top:4px;">File results come from the compact browser projection of the authoritative ${corpusIndex.length.toLocaleString()}-resource corpus. Use the linked ARCHE record as the source of record.</p>
        ${resources.map(renderResource).join('')}
        ${followUpHtml(top, 'resource')}
        <p style="font-size:.7rem;color:var(--text-muted);margin-top:8px;">Rights and access conditions can differ by record; verify them in ARCHE before reuse.</p>
      `, 'bot');
    } catch (error) {
      removeTyping();
      appendMessage(`<p>The file-level index could not be loaded. Entity search remains available; advanced file retrieval is also exposed through <a href="${BYOAI_URL}">Remote MCP / BYOAI</a>.</p>`, 'bot');
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', injectUi);
  else injectUi();
})();