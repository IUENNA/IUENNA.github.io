/* IUENNA Knowledge Graph LOD data loader
 *
 * data/arche_graph.json remains the complete authoritative graph for BYOAI,
 * MCP and reproducibility. The browser renders a performance projection:
 * arche_graph_macro.json at startup plus collection-scoped resource shards on
 * demand. graph/index.html therefore never materializes all >20k resources and
 * >280k relations in Cytoscape at once.
 */
(function () {
    "use strict";

    const MACRO_URL = "../data/arche_graph_macro.json";
    const MANIFEST_URL = "../data/arche_graph_lod_manifest.json";
    const DATA_PREFIX = "../data/";
    const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

    let manifestPromise = null;
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

            c.batch(() => {
                c.elements().remove();
                c.add({ nodes: validated.nodes, edges: validated.edges });
            });

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
            updateMetadata(data.metadata || {}, validated.nodes.length);
            try { if (typeof updateVisibleNodesCount === "function") updateVisibleNodesCount(); } catch (_) {}

            const lod = (data.metadata && data.metadata.lod) || {};
            window.IUENNACanonicalGraphReady = true;
            window.IUENNACanonicalGraph = {
                url: "../data/arche_graph.json",
                visualizationUrl: MACRO_URL,
                mode: "macro-plus-resource-shards",
                nodes: validated.nodes.length,
                edges: validated.edges.length,
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
                `Performance-Modus: ${validated.nodes.length.toLocaleString("de-DE")} Strukturknoten geladen; ` +
                `${Number(manifest.lazy_resource_nodes || 0).toLocaleString("de-DE")} Ressourcen werden collectionweise nachgeladen.`,
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
        loadedCollections: () => Array.from(loadedShards.keys())
    };

    loadMacroGraph();
})();
