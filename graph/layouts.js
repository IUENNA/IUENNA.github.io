/* IUENNA Knowledge Graph layout runtime
 *
 * The graph contains >20k resource nodes. Running browser-side layouts over the
 * full graph is neither useful nor tractable. Alternate layouts therefore run
 * on the visible structural graph (collections, datasets, places, actors,
 * publications, helper nodes) while retaining the connecting edges. Visible
 * resource nodes are then deterministically re-anchored around their parent
 * collection. The original server-computed coordinates are cached so the
 * "preset" option actually restores the authoritative cluster layout.
 */
(function () {
    "use strict";

    const LARGE_GRAPH_THRESHOLD = 1500;
    const RESOURCE_THRESHOLD = 500;
    const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

    let presetPositions = null;
    let activeLayout = null;
    let rerunTimer = null;

    function graph() {
        try {
            return (typeof cy !== "undefined" && cy && typeof cy.nodes === "function") ? cy : null;
        } catch (_) {
            return null;
        }
    }

    function notify(message, type = "info", duration = 2600) {
        try {
            if (typeof showNotification === "function") {
                showNotification(message, type, duration);
            }
        } catch (_) {
            // Layouts must remain usable even if the toast helper changes.
        }
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

    function capturePresetPositions() {
        const c = graph();
        if (!c || presetPositions) return;
        presetPositions = new Map();
        c.nodes().forEach(node => {
            const p = node.position();
            presetPositions.set(node.id(), { x: p.x, y: p.y });
        });
    }

    function resetPresetPositions() {
        presetPositions = null;
        capturePresetPositions();
    }

    function restorePreset() {
        const c = graph();
        if (!c) return;
        capturePresetPositions();
        if (activeLayout && typeof activeLayout.stop === "function") {
            try { activeLayout.stop(); } catch (_) {}
        }
        activeLayout = null;
        c.batch(() => {
            c.nodes().positions(node => presetPositions.get(node.id()) || node.position());
        });
        c.fit(c.elements(":visible"), 40);
        hideLoading();
        notify("Vorberechnetes Cluster-Layout wiederhergestellt.", "success", 1800);
    }

    function nodesAndConnectingEdges(nodes) {
        const c = graph();
        const ids = new Set();
        nodes.forEach(n => ids.add(n.id()));
        const edges = c.edges().filter(edge => ids.has(edge.source().id()) && ids.has(edge.target().id()));
        return nodes.union(edges);
    }

    function structuralNodes(visibleNodes) {
        return visibleNodes.filter(node => node.data("type") !== "resource");
    }

    function hierarchyValue(node) {
        const type = node.data("type");
        const levelRaw = node.data("level");
        const level = Number.isFinite(Number(levelRaw)) ? Number(levelRaw) : null;
        if (type === "root" || level === 0) return 100;
        if (type === "subcollection" || level === 1) return 90;
        if (level === 2) return 80;
        if (level === 3) return 70;
        if (level === 4) return 60;
        if (level === 5) return 50;
        if (level !== null && level >= 6) return 40;
        if (type === "dataset") return 78;
        if (type === "person" || type === "organization") return 68;
        if (type === "place") return 58;
        if (type === "publication") return 48;
        return 30;
    }

    function layoutConfig(name, workingNodes) {
        const c = graph();
        const root = c.getElementById("iuenna_root");

        if (name === "cose") {
            return {
                name: "cose",
                animate: false,
                fit: false,
                padding: 60,
                randomize: true,
                componentSpacing: 120,
                nodeRepulsion: node => {
                    const hierarchyEdges = node.connectedEdges("[label = 'isPartOf']").length;
                    return 350000 + Math.min(3200000, hierarchyEdges * 450);
                },
                idealEdgeLength: edge => edge.data("label") === "isPartOf" ? 115 : 175,
                edgeElasticity: edge => edge.data("label") === "isPartOf" ? 140 : 70,
                nestingFactor: 1.15,
                gravity: 0.35,
                numIter: 1400,
                initialTemp: 1000,
                coolingFactor: 0.98,
                minTemp: 1.0
            };
        }

        if (name === "concentric") {
            return {
                name: "concentric",
                fit: false,
                padding: 60,
                animate: false,
                startAngle: 1.5 * Math.PI,
                clockwise: true,
                equidistant: false,
                minNodeSpacing: 45,
                avoidOverlap: true,
                concentric: hierarchyValue,
                levelWidth: () => 5
            };
        }

        if (name === "breadthfirst") {
            return {
                name: "breadthfirst",
                fit: false,
                padding: 60,
                animate: false,
                directed: false,
                circle: false,
                grid: false,
                spacingFactor: 1.45,
                maximal: false,
                roots: root && root.length ? root : undefined
            };
        }

        if (name === "circle") {
            return {
                name: "circle",
                fit: false,
                padding: 60,
                animate: false,
                avoidOverlap: true,
                spacingFactor: 1.25,
                sort: (a, b) => {
                    const av = hierarchyValue(a);
                    const bv = hierarchyValue(b);
                    if (av !== bv) return bv - av;
                    return String(a.data("label") || a.id()).localeCompare(String(b.data("label") || b.id()));
                }
            };
        }

        return { name: "preset", fit: false };
    }

    function anchorVisibleResources() {
        const c = graph();
        if (!c) return;

        const buckets = new Map();
        const resources = c.nodes(":visible").filter(node => node.data("type") === "resource");
        if (!resources.length) return;

        const visibleResourceIds = new Set();
        resources.forEach(node => visibleResourceIds.add(node.id()));

        // `isPartOf` points from child/resource to parent in the IUENNA graph.
        c.edges("[label = 'isPartOf']").forEach(edge => {
            const source = edge.source();
            if (!visibleResourceIds.has(source.id())) return;
            const parent = edge.target();
            if (!parent || !parent.length || !parent.visible()) return;
            if (!buckets.has(parent.id())) buckets.set(parent.id(), []);
            buckets.get(parent.id()).push(source);
        });

        c.batch(() => {
            buckets.forEach((nodes, parentId) => {
                const parent = c.getElementById(parentId);
                if (!parent || !parent.length) return;
                const center = parent.position();
                nodes.sort((a, b) => String(a.id()).localeCompare(String(b.id())));
                nodes.forEach((node, index) => {
                    const angle = index * GOLDEN_ANGLE;
                    const radius = 34 + 6.0 * Math.sqrt(index + 1);
                    node.position({
                        x: center.x + Math.cos(angle) * radius,
                        y: center.y + Math.sin(angle) * radius
                    });
                });
            });
        });
    }

    function runLayout(name, options = {}) {
        const c = graph();
        if (!c) return;
        capturePresetPositions();

        if (!name || name === "preset") {
            showLoading("Cluster-Layout laden...", "Vorberechnete Koordinaten werden wiederhergestellt...");
            window.setTimeout(restorePreset, 20);
            return;
        }

        if (activeLayout && typeof activeLayout.stop === "function") {
            try { activeLayout.stop(); } catch (_) {}
        }

        const visibleNodes = c.nodes(":visible");
        const visibleResources = visibleNodes.filter(node => node.data("type") === "resource");
        const macroMode = visibleNodes.length > LARGE_GRAPH_THRESHOLD || visibleResources.length > RESOURCE_THRESHOLD;
        const workingNodes = macroMode ? structuralNodes(visibleNodes) : visibleNodes;
        const elements = nodesAndConnectingEdges(workingNodes);

        if (!workingNodes.length) {
            notify("Für das gewählte Layout sind keine sichtbaren Knoten vorhanden.", "warning");
            return;
        }

        const labels = {
            cose: "Force-Directed (COSE)",
            concentric: "Konzentrisch",
            breadthfirst: "Baum-Hierarchie",
            circle: "Zirkulär"
        };
        const label = labels[name] || name;
        const edgeCount = elements.edges().length;
        showLoading(`Layout: ${label}`, `Berechne ${workingNodes.length.toLocaleString()} Knoten mit ${edgeCount.toLocaleString()} Relationen...`);

        // Let the loading overlay paint before the synchronous layout starts.
        window.setTimeout(() => {
            try {
                const config = layoutConfig(name, workingNodes);
                activeLayout = elements.layout(config);
                activeLayout.one("layoutstop", () => {
                    if (macroMode) anchorVisibleResources();
                    c.fit(c.elements(":visible"), 45);
                    activeLayout = null;
                    hideLoading();
                    if (macroMode && options.notify !== false) {
                        notify(`${label}: Topologie auf ${workingNodes.length.toLocaleString()} Strukturknoten berechnet; Ressourcen an Elternsammlungen verankert.`, "success", 3500);
                    }
                });
                activeLayout.run();
            } catch (error) {
                console.error("IUENNA layout error:", error);
                activeLayout = null;
                hideLoading();
                notify(`Layout konnte nicht berechnet werden: ${error.message || error}`, "warning", 5000);
            }
        }, 30);
    }

    function applyDepthFilterFixed(depth) {
        const c = graph();
        if (!c) return;
        const maxLevel = depth === "all" ? 99 : parseInt(depth, 10);
        c.batch(() => {
            c.nodes().forEach(node => {
                const level = node.data("level");
                if (level !== undefined && level !== null) {
                    if (Number(level) <= maxLevel) node.show();
                    else node.hide();
                } else {
                    node.show();
                }
            });
            c.edges().forEach(edge => {
                const endpointsVisible = edge.source().visible() && edge.target().visible();
                let shouldShow = endpointsVisible;
                try {
                    if (typeof edgesVisible !== "undefined" && !edgesVisible) shouldShow = false;
                } catch (_) {}
                if (shouldShow) edge.show();
                else edge.hide();
            });
        });
        try {
            if (typeof updateVisibleNodesCount === "function") updateVisibleNodesCount();
        } catch (_) {}
        const select = document.getElementById("layoutSelect");
        runLayout(select ? select.value : "preset", { notify: false });
    }

    function install() {
        const c = graph();
        const select = document.getElementById("layoutSelect");
        if (!c || !select) {
            window.setTimeout(install, 50);
            return;
        }

        capturePresetPositions();

        // Capture phase deliberately runs before the legacy listener embedded in
        // graph/index.html. stopImmediatePropagation() prevents the old node-only
        // layout call from running.
        select.addEventListener("change", event => {
            event.stopImmediatePropagation();
            runLayout(select.value);
        }, true);

        const slider = document.getElementById("lodSlider");
        if (slider) {
            slider.addEventListener("input", event => {
                event.stopImmediatePropagation();
                const value = Math.max(1, Math.min(6, parseInt(slider.value, 10) || 6));
                const labels = {
                    1: "L1 (6 Subcollections)",
                    2: "L1–L2 (74 Hauptbestände)",
                    3: "L1–L3 (274 Fachordner)",
                    4: "L1–L4 (312 Teilsammlungen)",
                    5: "L1–L5 (432 Befundordner)",
                    6: "L1–L6 (Alle 434 Ordner)"
                };
                const badge = document.getElementById("lodLevelBadge");
                if (badge) badge.textContent = labels[value];
                window.clearTimeout(rerunTimer);
                rerunTimer = window.setTimeout(() => applyDepthFilterFixed(value === 6 ? "all" : String(value)), 20);
            }, true);
        }

        // Make the repaired runner available for debugging and future UI hooks.
        window.IUENNAGraphLayouts = {
            run: runLayout,
            restorePreset,
            capturePresetPositions,
            resetPresetPositions
        };

        // Clarify the force implementation in the UI.
        const forceOption = select.querySelector('option[value="cose"]');
        if (forceOption) forceOption.textContent = "Force-Directed (COSE, Topologie)";
    }

    window.addEventListener("iuenna:canonical-graph-loaded", () => {
        resetPresetPositions();
    });

    install();
})();
