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
    const EDGE_BUNDLE_DISTANCE_SCALE = 0.36;
    const EDGE_BUNDLE_MAX_RATIO = 0.16;
    const EDGE_BUNDLE_MAX_PX = 90;
    const ROOT_CORRIDOR_PULL = 0.22;

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
        if (!c) return;
        if (!presetPositions) presetPositions = new Map();
        c.nodes().forEach(node => {
            if (presetPositions.has(node.id())) return;
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
        scheduleEdgeBundling();
        hideLoading();
        notify("Precomputed cluster layout restored.", "success", 1800);
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

    function nodeLevel(node) {
        const value = Number(node && node.data ? node.data("level") : NaN);
        return Number.isFinite(value) ? value : null;
    }

    function coseNodeRepulsion(node) {
        const type = node.data("type");
        const level = nodeLevel(node);
        if (type === "root" || level === 0 || node.id() === "iuenna_root") return 2600000;
        if (type === "subcollection" || level === 1) return 1700000;
        if (level === 2) return 900000;
        if (["dataset", "person", "organization", "place", "publication"].includes(type)) return 650000;
        return 420000;
    }

    function coseIdealEdgeLength(edge) {
        if (edge.data("label") !== "isPartOf") return 165;
        const source = edge.source();
        const target = edge.target();
        if (target.id() === "iuenna_root" || target.data("type") === "root") return 235;
        const level = nodeLevel(source);
        if (level === null) return 105;
        if (level <= 1) return 205;
        if (level === 2) return 130;
        if (level === 3) return 102;
        if (level === 4) return 86;
        return 74;
    }

    function coseEdgeElasticity(edge) {
        if (edge.data("label") !== "isPartOf") return 58;
        const source = edge.source();
        const target = edge.target();
        if (target.id() === "iuenna_root" || target.data("type") === "root") return 85;
        const level = nodeLevel(source);
        if (level === null || level <= 1) return 110;
        if (level === 2) return 145;
        return 185;
    }

    function routingCorridor(sourceHub, targetHub, rootPos) {
        const mid = {
            x: (sourceHub.x + targetHub.x) / 2,
            y: (sourceHub.y + targetHub.y) / 2
        };
        if (!rootPos) return mid;
        return {
            x: mid.x * (1 - ROOT_CORRIDOR_PULL) + rootPos.x * ROOT_CORRIDOR_PULL,
            y: mid.y * (1 - ROOT_CORRIDOR_PULL) + rootPos.y * ROOT_CORRIDOR_PULL
        };
    }

    function installHomepagePalette() {
        const c = graph();
        if (!c) return;
        const cyEl = document.getElementById("cy");
        if (cyEl) {
            cyEl.style.backgroundColor = "#FAF8F5";
            cyEl.style.backgroundImage = "radial-gradient(#E6E2DB 1px, transparent 1px)";
            cyEl.style.backgroundSize = "24px 24px";
        }
        c.style()
            .selector("edge")
            .style({
                "line-color": "#BDB6AC",
                "target-arrow-color": "#BDB6AC",
                "opacity": 0.16,
                "width": 1.0,
                "target-arrow-shape": "none"
            })
            .selector("edge[label = 'isPartOf']")
            .style({
                "line-color": "#CFC7BC",
                "opacity": 0.24,
                "width": 1.15
            })
            .selector("edge.highlighted")
            .style({
                "line-color": "#A8442E",
                "target-arrow-color": "#A8442E",
                "opacity": 0.92,
                "width": 2.4,
                "z-index": 999
            })
            .selector("node:selected")
            .style({
                "border-color": "#A8442E",
                "border-width": 4
            })
            .update();
    }

    function parentMap() {
        const c = graph();
        const map = new Map();
        if (!c) return map;
        c.edges("[label = 'isPartOf']").forEach(edge => map.set(edge.source().id(), edge.target().id()));
        return map;
    }

    function topHub(id, parents) {
        let current = id;
        let previous = id;
        const seen = new Set();
        while (parents.has(current) && !seen.has(current)) {
            seen.add(current);
            previous = current;
            current = parents.get(current);
            if (current === "iuenna_root") return previous;
        }
        return previous;
    }

    function controlPoint(edge, point) {
        const source = edge.source().position();
        const target = edge.target().position();
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const len2 = dx * dx + dy * dy;
        if (!len2) return null;
        const len = Math.sqrt(len2);
        const px = point.x - source.x;
        const py = point.y - source.y;
        const rawDistance = (px * (-dy) + py * dx) / len;
        const maxOffset = Math.min(EDGE_BUNDLE_MAX_PX, len * EDGE_BUNDLE_MAX_RATIO);
        return {
            weight: Math.max(0.15, Math.min(0.85, (px * dx + py * dy) / len2)),
            distance: Math.max(-maxOffset, Math.min(maxOffset, rawDistance * EDGE_BUNDLE_DISTANCE_SCALE))
        };
    }

    function applyHierarchicalEdgeBundling() {
        const c = graph();
        if (!c) return;
        installHomepagePalette();
        const parents = parentMap();
        const root = c.$id("iuenna_root");
        const rootPos = root.length ? root.position() : null;

        c.edges().forEach(edge => {
            if (edge.data("label") === "isPartOf") {
                edge.removeStyle("control-point-weights control-point-distances");
                edge.style("curve-style", "straight");
                return;
            }
            const sHubId = topHub(edge.source().id(), parents);
            const tHubId = topHub(edge.target().id(), parents);
            const sHub = c.$id(sHubId);
            const tHub = c.$id(tHubId);

            // Relations inside the same top-level collection remain nearly direct.
            // Bundling is reserved for cross-collection relations where it improves
            // readability instead of artificially bending local links.
            if (sHubId === tHubId) {
                edge.removeStyle("control-point-weights control-point-distances");
                edge.style("curve-style", "bezier");
                return;
            }

            const points = [];
            if (sHub.length && sHubId !== edge.source().id()) points.push(sHub.position());
            if (sHub.length && tHub.length) {
                points.push(routingCorridor(sHub.position(), tHub.position(), rootPos));
            }
            if (tHub.length && tHubId !== edge.target().id()) points.push(tHub.position());

            const controls = points.map(point => controlPoint(edge, point)).filter(Boolean);
            if (!controls.length) {
                edge.removeStyle("control-point-weights control-point-distances");
                edge.style("curve-style", "bezier");
                return;
            }
            edge.style("curve-style", "unbundled-bezier");
            edge.style("control-point-weights", controls.map(c => c.weight).join(" "));
            edge.style("control-point-distances", controls.map(c => c.distance).join(" "));
        });
    }

    function scheduleEdgeBundling() {
        window.clearTimeout(scheduleEdgeBundling.timer);
        scheduleEdgeBundling.timer = window.setTimeout(applyHierarchicalEdgeBundling, 40);
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
                componentSpacing: 170,
                nodeRepulsion: coseNodeRepulsion,
                idealEdgeLength: coseIdealEdgeLength,
                edgeElasticity: coseEdgeElasticity,
                nestingFactor: 1.30,
                gravity: 0.22,
                numIter: 1600,
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
                minNodeSpacing: 52,
                avoidOverlap: true,
                concentric: hierarchyValue,
                levelWidth: () => 4
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
                spacingFactor: 1.35,
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
                spacingFactor: 1.18,
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
            showLoading("Loading cluster layout...", "Restoring precomputed coordinates...");
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
            notify("No visible nodes are available for this layout.", "warning");
            return;
        }

        const labels = {
            cose: "Force-Directed (COSE)",
            concentric: "Concentric",
            breadthfirst: "Hierarchy",
            circle: "Circular"
        };
        const label = labels[name] || name;
        const edgeCount = elements.edges().length;
        showLoading(`Layout: ${label}`, `Computing ${workingNodes.length.toLocaleString()} nodes with ${edgeCount.toLocaleString()} relations...`);

        // Let the loading overlay paint before the synchronous layout starts.
        window.setTimeout(() => {
            try {
                const config = layoutConfig(name, workingNodes);
                activeLayout = elements.layout(config);
                activeLayout.one("layoutstop", () => {
                    if (macroMode) anchorVisibleResources();
                    c.fit(c.elements(":visible"), 45);
                    scheduleEdgeBundling();
                    activeLayout = null;
                    hideLoading();
                    if (macroMode && options.notify !== false) {
                        notify(`${label}: topology computed for ${workingNodes.length.toLocaleString()} structural nodes; resources anchored to parent collections.`, "success", 3500);
                    }
                });
                activeLayout.run();
            } catch (error) {
                console.error("IUENNA layout error:", error);
                activeLayout = null;
                hideLoading();
                notify(`Layout could not be computed: ${error.message || error}`, "warning", 5000);
            }
        }, 30);
    }

    function applyDepthFilterFixed(depth) {
        const c = graph();
        if (!c) return;
        const value = depth === "all" ? 6 : Math.max(1, Math.min(6, parseInt(depth, 10) || 2));
        if (window.IUENNAGraphDataSource && typeof window.IUENNAGraphDataSource.setMacroDepth === "function") {
            window.IUENNAGraphDataSource.setMacroDepth(value, { fit: false });
            capturePresetPositions();
            scheduleEdgeBundling();
        } else {
            c.batch(() => {
                c.nodes().forEach(node => {
                    const level = Number(node.data("level"));
                    if (!Number.isFinite(level) || level <= value) node.show();
                    else node.hide();
                });
            });
        }
        try { if (typeof updateVisibleNodesCount === "function") updateVisibleNodesCount(); } catch (_) {}
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
            slider.value = "2";
            const initialBadge = document.getElementById("lodLevelBadge");
            if (initialBadge) initialBadge.textContent = "L1–L2 · overview";
            slider.addEventListener("input", event => {
                event.stopImmediatePropagation();
                const value = Math.max(1, Math.min(6, parseInt(slider.value, 10) || 2));
                const labels = {
                    1: "L1 · 6 subcollections",
                    2: "L1–L2 · overview",
                    3: "L1–L3 · places + subject folders",
                    4: "L1–L4 · detailed collections",
                    5: "L1–L5 · near-complete structure",
                    6: "L1–L6 · all 434 folders"
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
            resetPresetPositions,
            bundleEdges: applyHierarchicalEdgeBundling
        };

        // Clarify the force implementation in the UI.
        const forceOption = select.querySelector('option[value="cose"]');
        if (forceOption) forceOption.textContent = "Force-directed (COSE)";
    }

    window.addEventListener("iuenna:canonical-graph-loaded", () => {
        resetPresetPositions();
        scheduleEdgeBundling();
    });
    window.addEventListener("iuenna:macro-depth-changed", scheduleEdgeBundling);
    window.addEventListener("iuenna:lod-shard-loaded", scheduleEdgeBundling);
    window.addEventListener("iuenna:lod-shard-unloaded", scheduleEdgeBundling);

    install();
})();
