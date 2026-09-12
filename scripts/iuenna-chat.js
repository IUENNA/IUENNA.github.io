/**
 * Ask IUENNA
 * ----------
 * Site-wide, client-side discovery assistant for IUENNA.
 *
 * Provenance policy:
 * - Entity discovery uses data/arche_search_index.json, generated directly from
 *   the ARCHE RDF export.
 * - File-level discovery uses data/arche_corpus_browser_index.json, a compact
 *   non-authoritative browser projection of the authoritative arche_corpus.json.
 * - The assistant does not generate archaeological interpretations or factual
 *   syntheses. It only presents indexed metadata and links back to ARCHE,
 *   the IUENNA Knowledge Graph, Web Mapping, and BYOAI/Remote MCP.
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

  let searchIndex = null;
  let searchIndexPromise = null;
  let corpusIndex = null;
  let corpusIndexPromise = null;
  let currentQuery = '';

  const EN_STOPWORDS = new Set([
    'a','an','and','are','as','at','be','by','for','from','how','in','is','it','of','on','or','the','to','what','where','which','who','with','show','find','me','please'
  ]);

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
      .replace(/[^a-z0-9äöüß]+/g, ' ')
      .trim();
  }

  function queryTokens(query) {
    const tokens = normalize(query).split(/\s+/).filter(Boolean);
    const filtered = tokens.filter(t => !EN_STOPWORDS.has(t));
    return filtered.length ? filtered : tokens;
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

  function scoreEntity(item, tokens, rawQuery) {
    const label = normalize(item.label || '');
    const sublabel = normalize(item.sublabel || '');
    const category = normalize(item.category || '');
    const code = normalize(item.code || '');
    const tokenText = normalize((item.tokens || []).join(' '));
    const archeId = normalize(item.arche_id || '');
    const haystack = [label, sublabel, category, code, tokenText, archeId].join(' ');
    let score = 0;
    let matched = 0;

    for (const token of tokens) {
      if (!haystack.includes(token)) continue;
      matched += 1;
      if (label === token || code === token || archeId === token) score += 60;
      else if (label.startsWith(token) || code.startsWith(token)) score += 35;
      else if (label.includes(token)) score += 24;
      else if (tokenText.includes(token)) score += 12;
      else score += 7;
    }

    if (!matched) return 0;
    if (tokens.length > 1 && matched === tokens.length) score += 35;
    const nq = normalize(rawQuery);
    if (nq && label === nq) score += 80;
    else if (nq && label.includes(nq)) score += 35;
    return score;
  }

  function searchEntities(query, limit = 8) {
    const tokens = queryTokens(query);
    if (!tokens.length || !searchIndex) return [];
    return searchIndex
      .map(item => ({ item, score: scoreEntity(item, tokens, query) }))
      .filter(entry => entry.score > 0)
      .sort((a, b) => b.score - a.score || String(a.item.label || '').localeCompare(String(b.item.label || '')))
      .slice(0, limit)
      .map(entry => entry.item);
  }

  function scoreResource(item, tokens, rawQuery) {
    const subjects = Array.isArray(item.subjs) ? item.subjs.join(' ') : (item.subjs || '');
    const path = Array.isArray(item.path) ? item.path.join(' ') : (item.path || '');
    const title = normalize(item.title || item.filename || '');
    const haystack = normalize([
      item.title, item.filename, item.place, item.folder, item.col, item.type,
      item.ftype, item.date, subjects, path, item.arche_id
    ].filter(Boolean).join(' '));
    let score = 0;
    let matched = 0;
    for (const token of tokens) {
      if (!haystack.includes(token)) continue;
      matched += 1;
      if (title === token) score += 50;
      else if (title.startsWith(token)) score += 30;
      else if (title.includes(token)) score += 20;
      else score += 7;
    }
    if (!matched) return 0;
    if (tokens.length > 1 && matched === tokens.length) score += 25;
    const nq = normalize(rawQuery);
    if (nq && title === nq) score += 60;
    else if (nq && title.includes(nq)) score += 25;
    return score;
  }

  function searchResources(query, limit = 8) {
    const tokens = queryTokens(query);
    if (!tokens.length || !corpusIndex) return [];
    return corpusIndex
      .map(item => ({ item, score: scoreResource(item, tokens, query) }))
      .filter(entry => entry.score > 0)
      .sort((a, b) => b.score - a.score || String(a.item.title || '').localeCompare(String(b.item.title || '')))
      .slice(0, limit)
      .map(entry => entry.item);
  }

  function archeUrlForEntity(item) {
    if (item && item.meta && item.meta.pid) return item.meta.pid;
    if (item && item.meta && item.meta.url && /^https?:\/\//.test(item.meta.url)) return item.meta.url;
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
      valueRow('Type', item.type || item.category),
      valueRow('Context', item.sublabel),
      valueRow('Items', meta.items),
      valueRow('Size', meta.size),
      valueRow('Years', meta.years || meta.year),
      valueRow('Creators', meta.creators),
      valueRow('Authors', meta.authors),
      valueRow('Publisher', meta.publisher),
      valueRow('Citation', meta.citation),
      valueRow('ARCHE ID', item.arche_id)
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
      valueRow('File', item.filename),
      valueRow('Type', item.type || item.ftype),
      valueRow('Place', item.place),
      valueRow('Collection', item.col),
      valueRow('Folder', item.folder),
      valueRow('Date', item.date),
      valueRow('Size', item.formatted_size),
      valueRow('ARCHE ID', item.arche_id)
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

  function messagesEl() { return document.getElementById('chat-messages'); }

  function appendMessage(html, who) {
    const area = messagesEl();
    if (!area) return;
    const wrapper = document.createElement('div');
    wrapper.className = `chat-msg ${who === 'user' ? 'user' : 'bot'}`;
    wrapper.innerHTML = `<div class="chat-msg-bubble">${html}</div><span class="chat-msg-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>`;
    area.appendChild(wrapper);
    area.scrollTop = area.scrollHeight;
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
    } catch (_) {}
  }

  function restoreChatState() {
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
      <p style="margin-top:6px;font-size:.84rem;line-height:1.45;">Search ARCHE-derived IUENNA metadata for collections, places, people, publications and datasets. Archaeological interpretations are not generated here; results link back to their source records.</p>
      <div class="chat-chips-container" style="margin-top:10px;">
        <button type="button" class="chat-chip" data-query="Hemmaberg"><i class="fa-solid fa-location-dot"></i> Hemmaberg</button>
        <button type="button" class="chat-chip" data-query="Globasnitz"><i class="fa-solid fa-location-dot"></i> Globasnitz</button>
        <button type="button" class="chat-chip" data-query="Jaunstein"><i class="fa-solid fa-location-dot"></i> Jaunstein</button>
        <button type="button" class="chat-chip" data-query="GeoPackage"><i class="fa-solid fa-database"></i> GeoPackages</button>
        <button type="button" class="chat-chip chat-chip-byoai" data-query="__byoai"><i class="fa-solid fa-microchip"></i> BYOAI / Remote MCP</button>
      </div>`;
  }

  function injectUi() {
    const trigger = document.createElement('button');
    trigger.id = 'iuenna-chat-trigger';
    trigger.type = 'button';
    trigger.setAttribute('aria-label', 'Open Ask IUENNA');
    trigger.innerHTML = `<span class="chat-trigger-icon">🏺</span><span>Ask IUENNA</span><span class="chat-trigger-badge">Metadata</span>`;
    document.body.appendChild(trigger);

    const win = document.createElement('div');
    win.id = 'iuenna-chat-window';
    win.setAttribute('role', 'dialog');
    win.setAttribute('aria-label', 'Ask IUENNA metadata assistant');
    win.innerHTML = `
      <div class="chat-header">
        <div class="chat-header-info">
          <div class="chat-header-avatar">🏺</div>
          <div>
            <h3 class="chat-header-title">Ask IUENNA</h3>
            <p class="chat-header-sub">ARCHE-derived metadata discovery</p>
            <div style="display:flex;align-items:center;gap:6px;margin-top:3px;flex-wrap:wrap;">
              <span style="display:inline-flex;align-items:center;gap:4px;font-size:.67rem;padding:1px 6px;border-radius:3px;background:rgba(255,255,255,.16);"><i class="fa-solid fa-shield-halved" style="color:#9fe3b1;"></i> metadata only</span>
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
          <input type="text" id="chat-input-field" class="chat-input-field" placeholder="Search IUENNA metadata…" autocomplete="off" aria-label="Search IUENNA metadata">
          <button id="chat-send-btn" class="chat-send-btn" type="button" aria-label="Search"><i class="fa-solid fa-magnifying-glass"></i></button>
        </div>
        <div class="chat-privacy-footer" style="padding:5px 10px;text-align:center;display:flex;flex-direction:column;gap:2px;">
          <span style="font-size:.67rem;line-height:1.35;">Client-side metadata search · session stored only in this tab · <a href="${BYOAI_URL}" style="font-weight:600;">Remote MCP / BYOAI</a></span>
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
      win.classList.add('chat-open');
      saveChatState();
      setTimeout(() => input.focus(), 50);
    });
    close.addEventListener('click', () => {
      win.classList.remove('chat-open');
      saveChatState();
    });
    reset.addEventListener('click', () => {
      const area = messagesEl();
      area.innerHTML = `<div class="chat-msg bot"><div class="chat-msg-bubble">${welcomeHtml()}</div><span class="chat-msg-time">Now</span></div>`;
      try { sessionStorage.removeItem(STORAGE_KEY_HISTORY); } catch (_) {}
      bindChipEvents();
      saveChatState();
    });
    send.addEventListener('click', submitQuery);
    input.addEventListener('keydown', event => {
      if (event.key === 'Enter') submitQuery();
      if (event.key === 'Escape') {
        win.classList.remove('chat-open');
        saveChatState();
      }
    });
    bindChipEvents();
  }

  function bindChipEvents() {
    document.querySelectorAll('#iuenna-chat-window .chat-chip').forEach(button => {
      if (button.dataset.bound === '1') return;
      button.dataset.bound = '1';
      button.addEventListener('click', () => {
        const query = button.dataset.query || '';
        if (query === '__byoai') {
          window.location.href = BYOAI_URL;
          return;
        }
        const input = document.getElementById('chat-input-field');
        input.value = query;
        submitQuery();
      });
    });
  }

  async function submitQuery() {
    const input = document.getElementById('chat-input-field');
    const query = (input.value || '').trim();
    if (!query) return;
    currentQuery = query;
    appendMessage(`<p>${escapeHtml(query)}</p>`, 'user');
    input.value = '';
    showTyping('Searching ARCHE-derived metadata');

    try {
      await loadSearchIndex();
      const results = searchEntities(query);
      removeTyping();
      if (!results.length) {
        await searchFiles(query, true);
        return;
      }
      const cards = results.map(renderEntity).join('');
      appendMessage(`
        <p><strong>Metadata matches</strong></p>
        <p style="font-size:.78rem;color:var(--text-muted);margin-top:4px;">These are discovery records derived from the ARCHE metadata export. No archaeological interpretation has been generated.</p>
        ${cards}
        <button type="button" class="chat-chip" id="ask-iuenna-search-files" style="margin-top:8px;"><i class="fa-solid fa-file"></i> Search archived files for “${escapeHtml(query)}”</button>
        <p style="font-size:.7rem;color:var(--text-muted);margin-top:8px;">For scholarly reuse, follow the ARCHE record and check its citation, rights statement and access conditions.</p>
      `, 'bot');
      const fileButton = document.getElementById('ask-iuenna-search-files');
      if (fileButton) fileButton.addEventListener('click', () => searchFiles(query, false), { once: true });
    } catch (error) {
      removeTyping();
      appendMessage(`<p><strong>Metadata search is temporarily unavailable.</strong></p><p style="font-size:.78rem;margin-top:5px;">You can still use the <a href="${BYOAI_URL}">BYOAI / Remote MCP</a> interface or open <a href="${ARCHE_ROOT}" target="_blank" rel="noopener">ARCHE</a>.</p>`, 'bot');
    }
  }

  async function searchFiles(query, fromNoEntityResult) {
    showTyping('Loading the archived-file discovery index');
    try {
      await loadCorpusIndex();
      const resources = searchResources(query);
      removeTyping();
      if (!resources.length) {
        appendMessage(`<p>No matching record was found in the entity index or the archived-file discovery index for <strong>${escapeHtml(query)}</strong>.</p><p style="font-size:.78rem;margin-top:5px;">Try a place name, collection title, person, dataset, publication, filename or ARCHE identifier. For advanced queries, use <a href="${BYOAI_URL}">IUENNA Remote MCP / BYOAI</a>.</p>`, 'bot');
        return;
      }
      appendMessage(`
        <p><strong>Archived-file matches</strong></p>
        <p style="font-size:.78rem;color:var(--text-muted);margin-top:4px;">File results come from the compact browser projection of the authoritative 20,355-resource corpus. Use the linked ARCHE record as the source of record.</p>
        ${resources.map(renderResource).join('')}
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
