/* IUENNA Knowledge Graph LOD data loader
 *
 * data/arche_graph.json remains the complete authoritative graph for BYOAI and
 * reproducibility. The public Remote MCP uses its own reproducible query projection;
 * the browser renders a separate performance projection:
 * arche_graph_macro.json at startup plus collection-scoped resource shards on
 * demand. graph/index.html therefore never materializes all >20k resources and
 * >280k relations in Cytoscape at once.
 */
(function () {
    "use strict";

    const MACRO_URL = "../data/arche_graph_macro.json";
    const MANIFEST_URL = "../data/arche_graph_lod_manifest.json";
    const DATA_PREFIX = "../data/";
    const INITIAL_MACRO_DEPTH = 2;
    const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

    let manifestPromise = null;
    let macroPayload = null;
    let macroDepth = INITIAL_MACRO_DEPTH;
    const loadedShards = new Map();
    const pendingEdges = new Map();

    function getGraph() {
        try {
            return (typeof cy !== "undefined" && cy && typeof cy.add === "function") ? cy : null;
        } catch (_) {
            return null;
        }
    }

    function notify(message, type = "info", duration = 3500) {
        try {
            if (typeof showNotification === "function") showNotification(message, type, duration);
        } catch (_) {}
    }

    function showLoading(title, status) {
        try {
            if (typeof showGraphLoading === "function") showGraphLoading(title, status);
        } catch (_) {}
    }

    function hideLoading() {
        try {
            if (typeof hideGraphLoading === "function") hideGraphLoading();
        } catch (_) {}
    }

    function updateMetadata(metadata, visibleNodeCount) {
        if (!metadata) metadata = {};
        const lod = metadata.lod || {};
        const setText = (id, value) => {
            const el = document.getElementById(id);
            if (el && value !== undefined && value !== null) {
                el.textContent = typeof value === "number" ? value.toLocaleString("de-DE") : String(value);
            }
        };
        setText("pillItems", metadata.total_items || metadata.total_arche_entities || lod.full_nodes || visibleNodeCount);
        setText("pillResources", metadata.total_resources || lod.lazy_resource_nodes);
        setText("pillCollections", metadata.total_collections);
        setText("pillSize", metadata.total_size);
        setText("pillVisibleNodes", visibleNodeCount);
    }

    function validatePayload(data, label) {
        if (!data || !data.elements || !Array.isArray(data.elements.nodes) || !Array.isArray(data.elements.edges)) {
            throw new Error(`${label} besitzt keine gültige Cytoscape-elements-Struktur`);
        }
        const ids = new Set();
        for (const node of data.elements.nodes) {
            const id = node && node.data && node.data.id;
            if (!id) throw new Error(`${label} enthält einen Knoten ohne data.id`);
            if (ids.has(id)) throw new Error(`Doppelte Knoten-ID in ${label}: ${id}`);
            ids.add(id);
        }
        return { nodes: data.elements.nodes, edges: data.elements.edges };
    }

    function applyVisibilityState(c, elements) {
        const scope = elements || c.elements();
        try {
            if (typeof nodeLabelsVisible !== "undefined" && !nodeLabelsVisible) scope.nodes().addClass("no-label");
            if (typeof edgeLabelsVisible !== "undefined" && !edgeLabelsVisible) scope.edges().addClass("no-label");
            if (typeof edgesVisible !== "undefined" && !edgesVisible) scope.edges().hide();
        } catch (_) {}
    }

    function macroNodeDepth(node) {
        const d = (node && node.data) || {};
        const level = Number(d.level);
        if (Number.isFinite(level)) return level;
        if (d.type === "root") return 0;
        if (d.type === "subcollection") return 1;
        return null;
    }

    function keepMacroNode(node, depth) {
        const d = (node && node.data) || {};
        const level = macroNodeDepth(node);
        if (level !== null) return level <= depth;
        // Keep the small scholarly context layer in the overview, while places
        // join from L3 onwards to avoid a dense first paint.
        if (d.type === "place") return depth >= 3;
        if (["dataset", "person", "organization", "publication", "root"].includes(d.type)) return true;
        return depth >= 4;
    }

    function macroEdgeId(edge) {
        const d = (edge && edge.data) || {};
        return String(d.id || `${d.source}|${d.label || ""}|${d.target}`);
    }

    function setMacroDepth(depth, options = {}) {
        const c = getGraph();
        if (!c || !macroPayload) return null;
        const nextDepth = Math.max(1, Math.min(6, Number(depth) || INITIAL_MACRO_DEPTH));
        macroDepth = nextDepth;

        const desiredNodes = macroPayload.nodes.filter(node => keepMacroNode(node, nextDepth));
        const desiredIds = new Set(desiredNodes.map(node => String(node.data.id)));
        const desiredEdges = macroPayload.edges.filter(edge => {
            const d = edge.data || {};
            return desiredIds.has(String(d.source)) && desiredIds.has(String(d.target));
        });
        const desiredEdgeIds = new Set(desiredEdges.map(macroEdgeId));

        // Resource shards whose parent disappears must be removed from both
        // Cytoscape and the loader registry. Otherwise a later re-expansion
        // would incorrectly treat an absent shard as already loaded.
        for (const [collectionId, state] of Array.from(loadedShards.entries())) {
            if (desiredIds.has(String(collectionId))) continue;
            state.resourceIds.forEach(id => {
                const node = c.$id(String(id));
                if (node.length) c.remove(node);
            });
            loadedShards.delete(collectionId);
            try {
                if (typeof expandedNodesMap !== "undefined" && expandedNodesMap && typeof expandedNodesMap.delete === "function") {
                    expandedNodesMap.delete(collectionId);
                }
            } catch (_) {}
        }

        c.batch(() => {
            c.edges().filter(edge => edge.data("lod_macro") === true && !desiredEdgeIds.has(edge.id())).remove();
            c.nodes().filter(node => node.data("lod_macro") === true && !desiredIds.has(node.id())).remove();

            const newNodes = desiredNodes.filter(node => !c.$id(String(node.data.id)).length).map(node => {
                const clone = JSON.parse(JSON.stringify(node));
                clone.data.lod_macro = true;
                return clone;
            });
            if (newNodes.length) c.add({ nodes: newNodes });

            const newEdges = desiredEdges.filter(edge => !c.$id(macroEdgeId(edge)).length).map(edge => {
                const clone = JSON.parse(JSON.stringify(edge));
                clone.data.id = macroEdgeId(clone);
                clone.data.lod_macro = true;
                return clone;
            });
            if (newEdges.length) c.add({ edges: newEdges });
            flushPendingEdges(c);
        });

        applyVisibilityState(c);
        updateMetadata((macroPayload.raw && macroPayload.raw.metadata) || {}, c.nodes().length);
        try { if (typeof updateVisibleNodesCount === "function") updateVisibleNodesCount(); } catch (_) {}

        const detail = {
            depth: nextDepth,
            nodes: c.nodes().length,
            edges: c.edges().length,
            macroNodes: desiredNodes.length,
            macroEdges: desiredEdges.length
        };
        window.dispatchEvent(new CustomEvent("iuenna:macro-depth-changed", { detail }));
        if (options.fit !== false) c.fit(c.elements(":visible"), 45);
        return detail;
    }

    async function getManifest() {
        if (!manifestPromise) {
            manifestPromise = fetch(MANIFEST_URL, { cache: "no-cache" }).then(response => {
                if (!response.ok) throw new Error(`LOD manifest HTTP ${response.status}`);
                return response.json();
            }).then(data => {
                if (!data || !data.collections || !data.resource_to_collection) {
                    throw new Error("LOD manifest besitzt keine gültige Collections-/Resource-Zuordnung");
                }
                return data;
            });
        }
        return manifestPromise;
    }

    function edgeReady(c, edge) {
        const d = edge && edge.data;
        return d && c.$id(String(d.source)).length > 0 && c.$id(String(d.target)).length > 0;
    }

    function addReadyEdges(c, edges) {
        const ready = [];
        for (const edge of edges || []) {
            const d = edge && edge.data;
            if (!d) continue;
            const id = String(d.id || `${d.source}|${d.label || ""}|${d.target}`);
            if (c.$id(id).length > 0) continue;
            if (edgeReady(c, edge)) ready.push(edge);
            else pendingEdges.set(id, edge);
        }
        if (ready.length) c.add({ edges: ready });
    }

    function flushPendingEdges(c) {
        const ready = [];
        for (const [id, edge] of pendingEdges.entries()) {
            if (c.$id(id).length > 0) {
                pendingEdges.delete(id);
                continue;
            }
            if (edgeReady(c, edge)) {
                ready.push(edge);
                pendingEdges.delete(id);
            }
        }
        if (ready.length) c.add({ edges: ready });
    }

    function anchorResourceNodes(c, collectionId, nodeIds) {
        const parent = c.$id(collectionId);
        if (!parent || parent.length === 0) return;
        const center = parent.position();
        const ordered = Array.from(nodeIds).sort();
        c.batch(() => {
            ordered.forEach((id, index) => {
                const node = c.$id(id);
                if (!node || node.length === 0) return;
                const angle = index * GOLDEN_ANGLE;
                const radius = 38 + 6.5 * Math.sqrt(index + 1);
                node.position({
                    x: center.x + Math.cos(angle) * radius,
                    y: center.y + Math.sin(angle) * radius
                });
            });
        });
    }

    async function resolveCollectionId(ref) {
        const manifest = await getManifest();
        const c = getGraph();
        const raw = String(ref && ref.id ? ref.id() : ref || "");
        if (manifest.collections[raw]) return raw;

        if (c && c.$id(raw).length) {
            const node = c.$id(raw);
            const aid = String(node.data("arche_id") || "");
            for (const [cid, entry] of Object.entries(manifest.collections)) {
                if (String(entry.arche_id || "") === aid) return cid;
            }
        }
        for (const [cid, entry] of Object.entries(manifest.collections)) {
            if (String(entry.arche_id || "") === raw) return cid;
        }
        return null;
    }

    async function loadCollection(ref, options = {}) {
        const c = getGraph();
        if (!c) return null;
        const manifest = await getManifest();
        const collectionId = await resolveCollectionId(ref);
        if (!collectionId || !manifest.collections[collectionId]) return null;
        if (loadedShards.has(collectionId)) return loadedShards.get(collectionId);

        const entry = manifest.collections[collectionId];
        const parent = c.$id(collectionId);
        const label = entry.label || (parent.length ? parent.data("label") : collectionId);
        showLoading("Ressourcen laden...", `${entry.resource_count.toLocaleString("de-DE")} Ressourcen für ${label} werden nachgeladen...`);

        try {
            const response = await fetch(DATA_PREFIX + entry.url, { cache: "no-cache" });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const shard = await response.json();
            const validated = validatePayload(shard, entry.url);
            const addedIds = new Set();
            const newNodes = [];

            for (const node of validated.nodes) {
                const id = String(node.data.id);
                if (c.$id(id).length > 0) continue;
                node.data.lod_collection_id = collectionId;
                newNodes.push(node);
                addedIds.add(id);
            }

            let added = c.collection();
            c.batch(() => {
                if (newNodes.length) added = c.add({ nodes: newNodes });
                addReadyEdges(c, validated.edges);
                flushPendingEdges(c);
            });
            anchorResourceNodes(c, collectionId, addedIds);
            applyVisibilityState(c, added.union(added.connectedEdges()));

            const state = {
                collectionId,
                resourceIds: addedIds,
                resourceCount: validated.nodes.length,
                edgeCount: validated.edges.length,
                url: DATA_PREFIX + entry.url
            };
            loadedShards.set(collectionId, state);

            try {
                if (typeof expandedNodesMap !== "undefined" && expandedNodesMap && typeof expandedNodesMap.set === "function") {
                    expandedNodesMap.set(collectionId, addedIds);
                }
            } catch (_) {}
            try { if (typeof updateVisibleNodesCount === "function") updateVisibleNodesCount(); } catch (_) {}
            try { if (parent.length && typeof openInspector === "function") openInspector(parent); } catch (_) {}

            window.dispatchEvent(new CustomEvent("iuenna:lod-shard-loaded", { detail: state }));
            hideLoading();
            if (options.notify !== false) {
                notify(`${addedIds.size.toLocaleString("de-DE")} Ressourcen für ${label} geladen.`, "success", 2600);
            }
            return state;
        } catch (error) {
            hideLoading();
            console.error("IUENNA LOD shard load failed:", error);
            notify(`Ressourcen konnten nicht geladen werden: ${error.message || error}`, "warning", 6000);
            throw error;
        }
    }

    async function unloadCollection(ref) {
        const c = getGraph();
        if (!c) return;
        const collectionId = await resolveCollectionId(ref);
        const state = collectionId && loadedShards.get(collectionId);
        if (!state) return;

        c.batch(() => {
            state.resourceIds.forEach(id => {
                const node = c.$id(id);
                if (node.length) c.remove(node);
            });
        });
        loadedShards.delete(collectionId);
        try {
            if (typeof expandedNodesMap !== "undefined" && expandedNodesMap && typeof expandedNodesMap.delete === "function") {
                expandedNodesMap.delete(collectionId);
            }
        } catch (_) {}
        try { if (typeof updateVisibleNodesCount === "function") updateVisibleNodesCount(); } catch (_) {}
        window.dispatchEvent(new CustomEvent("iuenna:lod-shard-unloaded", { detail: { collectionId } }));
    }

    async function ensureResource(resourceId, options = {}) {
        const c = getGraph();
        if (!c) return null;
        const rid = String(resourceId || "");
        if (c.$id(rid).length) return c.$id(rid);
        const manifest = await getManifest();
        const collectionId = manifest.resource_to_collection[rid];
        if (!collectionId) return null;
        await loadCollection(collectionId, { notify: options.notify !== false });
        return c.$id(rid).length ? c.$id(rid) : null;
    }

    async function loadMacroGraph() {
        const c = getGraph();
        if (!c) {
            window.setTimeout(loadMacroGraph, 40);
            return;
        }

        window.IUENNA_LOD_ACTIVE = true;
        showLoading("Lade Knowledge Graph...", "Struktureller Macro-Graph wird geladen; Primärressourcen folgen bei Bedarf...");

        try {
            const [response, manifest] = await Promise.all([
                fetch(MACRO_URL, { cache: "no-cache" }),
                getManifest()
            ]);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            const validated = validatePayload(data, "arche_graph_macro.json");

            c.batch(() => c.elements().remove());
            macroPayload = { nodes: validated.nodes, edges: validated.edges, raw: data };
            setMacroDepth(INITIAL_MACRO_DEPTH, { fit: false });

            try { graphData = data; } catch (_) {}
            try {
                if (typeof expandedNodesMap !== "undefined" && expandedNodesMap && typeof expandedNodesMap.clear === "function") {
                    expandedNodesMap.clear();
                }
            } catch (_) {}
            loadedShards.clear();
            pendingEdges.clear();
            try { selectedNode = null; } catch (_) {}
            try { if (typeof closeInspector === "function") closeInspector(); } catch (_) {}

            applyVisibilityState(c);
            updateMetadata(data.metadata || {}, c.nodes().length);
            try { if (typeof updateVisibleNodesCount === "function") updateVisibleNodesCount(); } catch (_) {}

            const lod = (data.metadata && data.metadata.lod) || {};
            window.IUENNACanonicalGraphReady = true;
            window.IUENNACanonicalGraph = {
                url: "../data/arche_graph.json",
                visualizationUrl: MACRO_URL,
                mode: "macro-plus-resource-shards",
                nodes: c.nodes().length,
                edges: c.edges().length,
                macroNodes: validated.nodes.length,
                macroEdges: validated.edges.length,
                initialDepth: INITIAL_MACRO_DEPTH,
                fullNodes: manifest.full_nodes || lod.full_nodes,
                fullEdges: manifest.full_edges || lod.full_edges,
                lazyResources: manifest.lazy_resource_nodes || lod.lazy_resource_nodes,
                shards: manifest.shard_count || lod.shards,
                metadata: data.metadata || {}
            };

            window.dispatchEvent(new CustomEvent("iuenna:canonical-graph-loaded", {
                detail: window.IUENNACanonicalGraph
            }));

            c.layout({ name: "preset", fit: true, padding: 40 }).run();
            hideLoading();
            notify(
                `Progressive mode: ${c.nodes().length.toLocaleString("en-US")} overview nodes materialised; ` +
                `${Number(manifest.lazy_resource_nodes || 0).toLocaleString("en-US")} resources remain collection-scoped and load on demand.`,
                "success",
                4200
            );
        } catch (error) {
            console.error("IUENNA LOD graph load failed:", error);
            hideLoading();
            notify(`Knowledge Graph konnte nicht im Performance-Modus geladen werden: ${error.message || error}`, "warning", 7000);
        }
    }

    // Replace the historical corpus-derived resource expansion with the exact
    // graph shards. Existing click handlers can therefore remain unchanged.
    window.expandResourcesForNode = async function (nodeId) {
        return loadCollection(nodeId);
    };
    window.collapseResourcesForNode = async function (nodeId) {
        return unloadCollection(nodeId);
    };

    window.IUENNAGraphDataSource = {
        url: "../data/arche_graph.json",
        visualizationUrl: MACRO_URL,
        manifestUrl: MANIFEST_URL,
        mode: "macro-plus-resource-shards",
        reload: loadMacroGraph,
        loadCollection,
        unloadCollection,
        ensureResource,
        getManifest,
        setMacroDepth,
        getMacroDepth: () => macroDepth,
        loadedCollections: () => Array.from(loadedShards.keys())
    };

    loadMacroGraph();
})();
