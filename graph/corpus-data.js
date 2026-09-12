/* IUENNA graph explorer: lazy corpus discovery loader.
 *
 * The authoritative data/arche_corpus.json is intentionally NOT fetched by the
 * browser. The explorer loads a compact discovery projection only when corpus
 * functionality is first used. BYOAI/MCP continue to use the complete corpus.
 */
(function () {
    "use strict";

    const INDEX_URL = "../data/arche_corpus_browser_index.json";
    let indexPromise = null;
    let ready = false;

    function notify(message, type = "info", duration = 3000) {
        try {
            if (typeof showNotification === "function") showNotification(message, type, duration);
        } catch (_) {}
    }

    function setPill(mode, count) {
        const pill = document.getElementById("pillCorpusStatus");
        const countEl = document.getElementById("corpusStatusCount");
        if (countEl && Number.isFinite(count)) countEl.textContent = count.toLocaleString("de-DE");
        if (!pill) return;

        if (mode === "idle") {
            pill.title = "Der kompakte Korpusindex wird erst bei Bedarf geladen.";
            pill.style.background = "#F7F5F0";
            pill.style.borderColor = "#D8D1C7";
            pill.style.color = "#655F57";
        } else if (mode === "loading") {
            pill.title = "Der kompakte Korpusindex wird geladen …";
            pill.style.background = "#F7F5F0";
            pill.style.borderColor = "#D8D1C7";
            pill.style.color = "#655F57";
        } else if (mode === "ready") {
            pill.title = "Kompakter Browserindex geladen; der vollständige autoritative Korpus bleibt serverseitig verfügbar.";
            pill.style.background = "#EBF3ED";
            pill.style.borderColor = "#B5D5BD";
            pill.style.color = "#2E6038";
        } else if (mode === "error") {
            pill.title = "Der Browserindex konnte nicht geladen werden.";
            pill.style.background = "#FFF3CD";
            pill.style.borderColor = "#E6D59A";
            pill.style.color = "#856404";
        }
    }

    function validate(data) {
        if (!data || !Array.isArray(data.resources)) {
            throw new Error("Ungültiger Korpus-Browserindex");
        }
        const ids = new Set();
        for (const item of data.resources) {
            if (!item || !item.id) throw new Error("Korpusindex enthält Ressource ohne ID");
            if (ids.has(item.id)) throw new Error(`Doppelte Ressourcen-ID im Korpusindex: ${item.id}`);
            ids.add(item.id);
        }
        return data;
    }

    function applyIndex(data) {
        try { corpusData = data; } catch (_) {}
        try { corpusResources = data.resources; } catch (_) {}

        try { if (typeof populateCorpusFilters === "function") populateCorpusFilters(); } catch (_) {}
        const count = data.resources.length;
        const countEl = document.getElementById("corpusStatusCount");
        if (countEl) countEl.textContent = count.toLocaleString("de-DE");
        try { if (typeof selectedNode !== "undefined" && selectedNode && typeof openInspector === "function") openInspector(selectedNode); } catch (_) {}

        ready = true;
        setPill("ready", count);
        window.dispatchEvent(new CustomEvent("iuenna:corpus-index-loaded", {
            detail: {
                url: INDEX_URL,
                resources: count,
                mode: "lazy-browser-discovery-index",
                authoritativeSource: "../data/arche_corpus.json"
            }
        }));
        return data;
    }

    async function loadIndex(reason = "user") {
        if (ready) {
            try { return corpusData; } catch (_) { return null; }
        }
        if (!indexPromise) {
            setPill("loading");
            indexPromise = fetch(INDEX_URL, { cache: "no-cache" })
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    return response.json();
                })
                .then(validate)
                .then(applyIndex)
                .catch(error => {
                    indexPromise = null;
                    setPill("error");
                    console.error("IUENNA corpus browser index load failed:", error);
                    notify(`Korpusindex konnte nicht geladen werden: ${error.message || error}`, "warning", 6000);
                    throw error;
                });
        }
        const data = await indexPromise;
        if (reason !== "search") {
            console.debug(`IUENNA corpus index ready (${reason}).`);
        }
        return data;
    }

    // Guard every direct corpus entry point, including buttons created later by
    // the tree view. This prevents an empty catalogue even when an entry point
    // bypasses the persistent toolbar button below.
    const originalOpenCorpusModal = typeof window.openCorpusModal === "function"
        ? window.openCorpusModal
        : null;
    if (originalOpenCorpusModal) {
        window.openCorpusModal = function (...args) {
            if (ready) return originalOpenCorpusModal.apply(this, args);
            return loadIndex("catalogue")
                .then(() => originalOpenCorpusModal.apply(this, args))
                .catch(() => undefined);
        };
    }

    // The generated explorer binds the main button before this runtime is
    // injected. Capture the click first so even a stored direct function
    // reference cannot open the catalogue before the index is ready.
    const btnOpenCorpus = document.getElementById("btnOpenCorpus");
    if (btnOpenCorpus) {
        btnOpenCorpus.addEventListener("click", async event => {
            if (ready) return;
            event.preventDefault();
            event.stopImmediatePropagation();
            try {
                await loadIndex("catalogue");
                if (originalOpenCorpusModal) originalOpenCorpusModal();
            } catch (_) {}
        }, true);
    }

    // Global autocomplete only pays for the corpus index after the user has
    // entered a meaningful resource query. Re-dispatch once after loading so
    // the existing search UI can add corpus matches without being rewritten.
    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            const query = searchInput.value.trim();
            if (ready || query.length < 2) return;
            loadIndex("search").then(() => {
                if (searchInput.value.trim() === query) {
                    searchInput.dispatchEvent(new Event("input", { bubbles: true }));
                }
            }).catch(() => {});
        });
    }

    // Deep links formerly depended on the eager 29+ MiB corpus fetch.
    const params = new URLSearchParams(window.location.search);
    if (params.get("open") === "corpus" || params.get("q") || params.get("res")) {
        loadIndex("deep-link").then(() => {
            const q = params.get("q");
            if (q) {
                const input = document.getElementById("corpusSearchInput");
                if (input) input.value = q;
            }
            if (params.get("open") === "corpus") {
                if (originalOpenCorpusModal) originalOpenCorpusModal();
            } else if (q && typeof filterCorpus === "function") {
                filterCorpus();
            }
            if (params.get("res") && typeof focusResourceInGraph === "function") {
                focusResourceInGraph(params.get("res"));
            }
        }).catch(() => {});
    }

    setPill("idle");

    window.IUENNACorpusDataSource = {
        url: INDEX_URL,
        authoritativeUrl: "../data/arche_corpus.json",
        mode: "lazy-browser-discovery-index",
        load: loadIndex,
        isReady: () => ready
    };
})();
