/* IUENNA Knowledge Graph canonical data loader
 *
 * data/arche_graph.json is the single authoritative graph payload used by the
 * browser. graph/index.html contains only the Cytoscape/UI shell; no full graph
 * snapshot is embedded in the generated HTML.
 */
(function () {
    "use strict";

    const GRAPH_URL = "../data/arche_graph.json";

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

    function updateMetadata(metadata, nodeCount) {
        if (!metadata) metadata = {};
        const setText = (id, value) => {
            const el = document.getElementById(id);
            if (el && value !== undefined && value !== null) {
                el.textContent = typeof value === "number" ? value.toLocaleString("de-DE") : String(value);
            }
        };
        setText("pillItems", metadata.total_items || metadata.total_arche_entities || nodeCount);
        setText("pillResources", metadata.total_resources);
        setText("pillCollections", metadata.total_collections);
        setText("pillSize", metadata.total_size);
        setText("pillVisibleNodes", nodeCount);
    }

    function validatePayload(data) {
        if (!data || !data.elements || !Array.isArray(data.elements.nodes) || !Array.isArray(data.elements.edges)) {
            throw new Error("arche_graph.json besitzt keine gültige Cytoscape-elements-Struktur");
        }
        const ids = new Set();
        for (const node of data.elements.nodes) {
            const id = node && node.data && node.data.id;
            if (!id) throw new Error("Graph enthält einen Knoten ohne data.id");
            if (ids.has(id)) throw new Error(`Doppelte Knoten-ID im publizierten Graphen: ${id}`);
            ids.add(id);
        }
        const safeEdges = [];
        for (const edge of data.elements.edges) {
            const d = edge && edge.data;
            if (!d || !ids.has(d.source) || !ids.has(d.target)) continue;
            safeEdges.push(edge);
        }
        return {
            nodes: data.elements.nodes,
            edges: safeEdges,
            droppedEdges: data.elements.edges.length - safeEdges.length
        };
    }

    function applyVisibilityState(c) {
        try {
            if (typeof nodeLabelsVisible !== "undefined" && !nodeLabelsVisible) c.nodes().addClass("no-label");
            if (typeof edgeLabelsVisible !== "undefined" && !edgeLabelsVisible) c.edges().addClass("no-label");
            if (typeof edgesVisible !== "undefined" && !edgesVisible) c.edges().hide();
        } catch (_) {}
    }

    async function loadCanonicalGraph() {
        const c = getGraph();
        if (!c) {
            window.setTimeout(loadCanonicalGraph, 40);
            return;
        }

        showLoading("Lade autoritativen Knowledge Graph...", "arche_graph.json wird als kanonische Graphquelle geladen...");

        try {
            const response = await fetch(GRAPH_URL, { cache: "no-cache" });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            const validated = validatePayload(data);

            // Keep the existing Cytoscape instance: styles, delegated handlers and
            // inspector/search integrations remain intact while the data is swapped.
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
            try { selectedNode = null; } catch (_) {}
            try { if (typeof closeInspector === "function") closeInspector(); } catch (_) {}

            applyVisibilityState(c);
            updateMetadata(data.metadata || {}, validated.nodes.length);
            try { if (typeof updateVisibleNodesCount === "function") updateVisibleNodesCount(); } catch (_) {}

            window.IUENNACanonicalGraphReady = true;
            window.IUENNACanonicalGraph = {
                url: GRAPH_URL,
                nodes: validated.nodes.length,
                edges: validated.edges.length,
                droppedEdges: validated.droppedEdges,
                metadata: data.metadata || {}
            };

            window.dispatchEvent(new CustomEvent("iuenna:canonical-graph-loaded", {
                detail: window.IUENNACanonicalGraph
            }));

            // Preserve the server-computed coordinates as the initial view.
            c.layout({ name: "preset", fit: true, padding: 40 }).run();
            hideLoading();

            if (validated.droppedEdges > 0) {
                notify(`${validated.droppedEdges.toLocaleString("de-DE")} ungültige Kanten wurden beim Laden verworfen.`, "warning", 5000);
            }
        } catch (error) {
            console.error("IUENNA canonical graph load failed:", error);
            hideLoading();
            const status = document.getElementById("graphLoadingStatus");
            if (status) status.textContent = "Der kanonische Graph konnte nicht geladen werden.";
            notify(`Knowledge Graph konnte nicht aus arche_graph.json geladen werden: ${error.message || error}`, "warning", 7000);
        }
    }

    window.IUENNAGraphDataSource = {
        url: GRAPH_URL,
        reload: loadCanonicalGraph
    };

    loadCanonicalGraph();
})();
