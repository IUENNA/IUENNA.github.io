#!/usr/bin/env python3
"""Upgrade the public graph explorer to progressive macro materialisation.

This migration keeps the authoritative graph and resource shards unchanged. It
only changes the browser runtime: a shallow structural overview is materialised
first; deeper collection levels are added on demand. It also installs a
hierarchy-aware edge-routing layer in the existing layout runtime.
"""
from pathlib import Path

DATA = Path("graph/data-source.js")
LAYOUTS = Path("graph/layouts.js")
INJECT = Path("scripts/inject_graph_layout_module.py")
WORKFLOW = Path(".github/workflows/graph_frontend.yml")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Missing patch anchor: {label}")
    return text.replace(old, new, 1)


def patch_data_source() -> None:
    text = DATA.read_text(encoding="utf-8")
    if "INITIAL_MACRO_DEPTH = 2" in text:
        return

    text = replace_once(
        text,
        '    const DATA_PREFIX = "../data/";\n    const GOLDEN_ANGLE',
        '    const DATA_PREFIX = "../data/";\n    const INITIAL_MACRO_DEPTH = 2;\n    const GOLDEN_ANGLE',
        "data constants",
    )
    text = replace_once(
        text,
        '    let manifestPromise = null;\n    const loadedShards = new Map();',
        '    let manifestPromise = null;\n    let macroPayload = null;\n    let macroDepth = INITIAL_MACRO_DEPTH;\n    const loadedShards = new Map();',
        "data state",
    )

    marker = '    async function getManifest() {'
    block = r'''    function macroNodeDepth(node) {
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

        c.batch(() => {
            // Resource shards whose parent disappears are removed with that
            // branch so depth changes never leave orphaned resource clouds.
            c.nodes().filter(node => node.data("lod_collection_id") && !desiredIds.has(String(node.data("lod_collection_id")))).remove();

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

'''
    text = replace_once(text, marker, block + marker, "progressive macro helpers")

    old = '''            c.batch(() => {
                c.elements().remove();
                c.add({ nodes: validated.nodes, edges: validated.edges });
            });

            try { graphData = data; } catch (_) {}'''
    new = '''            c.batch(() => c.elements().remove());
            macroPayload = { nodes: validated.nodes, edges: validated.edges, raw: data };
            setMacroDepth(INITIAL_MACRO_DEPTH, { fit: false });

            try { graphData = data; } catch (_) {}'''
    text = replace_once(text, old, new, "initial macro materialisation")

    text = replace_once(
        text,
        '            updateMetadata(data.metadata || {}, validated.nodes.length);',
        '            updateMetadata(data.metadata || {}, c.nodes().length);',
        "metadata visible count",
    )
    text = replace_once(
        text,
        '                nodes: validated.nodes.length,\n                edges: validated.edges.length,',
        '                nodes: c.nodes().length,\n                edges: c.edges().length,\n                macroNodes: validated.nodes.length,\n                macroEdges: validated.edges.length,\n                initialDepth: INITIAL_MACRO_DEPTH,',
        "canonical graph metadata",
    )
    text = replace_once(
        text,
        '                `Performance-Modus: ${validated.nodes.length.toLocaleString("de-DE")} Strukturknoten geladen; ` +',
        '                `Progressive mode: ${c.nodes().length.toLocaleString("en-US")} overview nodes materialised; ` +',
        "startup notification",
    )
    text = replace_once(
        text,
        '                `${Number(manifest.lazy_resource_nodes || 0).toLocaleString("de-DE")} Ressourcen werden collectionweise nachgeladen.`,',
        '                `${Number(manifest.lazy_resource_nodes || 0).toLocaleString("en-US")} resources remain collection-scoped and load on demand.`,',
        "startup notification resources",
    )
    text = replace_once(
        text,
        '        getManifest,\n        loadedCollections:',
        '        getManifest,\n        setMacroDepth,\n        getMacroDepth: () => macroDepth,\n        loadedCollections:',
        "public data API",
    )

    DATA.write_text(text, encoding="utf-8")


def patch_layouts() -> None:
    text = LAYOUTS.read_text(encoding="utf-8")
    if "applyHierarchicalEdgeBundling" in text:
        return

    text = replace_once(
        text,
        '        if (!c || presetPositions) return;\n        presetPositions = new Map();\n        c.nodes().forEach(node => {\n            const p = node.position();\n            presetPositions.set(node.id(), { x: p.x, y: p.y });\n        });',
        '        if (!c) return;\n        if (!presetPositions) presetPositions = new Map();\n        c.nodes().forEach(node => {\n            if (presetPositions.has(node.id())) return;\n            const p = node.position();\n            presetPositions.set(node.id(), { x: p.x, y: p.y });\n        });',
        "incremental preset positions",
    )

    marker = '    function layoutConfig(name, workingNodes) {'
    block = r'''    function installHomepagePalette() {
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
        return {
            weight: Math.max(0.08, Math.min(0.92, (px * dx + py * dy) / len2)),
            distance: (px * (-dy) + py * dx) / len
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
                edge.style("curve-style", "bezier");
                return;
            }
            const sHubId = topHub(edge.source().id(), parents);
            const tHubId = topHub(edge.target().id(), parents);
            const sHub = c.$id(sHubId);
            const tHub = c.$id(tHubId);
            const points = [];
            if (sHub.length && sHubId !== edge.source().id()) points.push(sHub.position());
            if (sHubId !== tHubId && rootPos) points.push(rootPos);
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

'''
    text = replace_once(text, marker, block + marker, "edge bundling helpers")

    # Use the data-source's real progressive materialisation instead of merely hiding nodes.
    start = text.index('    function applyDepthFilterFixed(depth) {')
    end = text.index('\n    function install() {', start)
    new_depth = r'''    function applyDepthFilterFixed(depth) {
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
'''
    text = text[:start] + new_depth + text[end:]

    text = text.replace('"Vorberechnetes Cluster-Layout wiederhergestellt."', '"Precomputed cluster layout restored."')
    text = text.replace('"Für das gewählte Layout sind keine sichtbaren Knoten vorhanden."', '"No visible nodes are available for this layout."')
    text = text.replace('c.fit(c.elements(":visible"), 40);\n        hideLoading();', 'c.fit(c.elements(":visible"), 40);\n        scheduleEdgeBundling();\n        hideLoading();', 1)
    text = text.replace('                    c.fit(c.elements(":visible"), 45);\n                    activeLayout = null;', '                    c.fit(c.elements(":visible"), 45);\n                    scheduleEdgeBundling();\n                    activeLayout = null;', 1)

    # Replace slider labels/default and make the current UI English.
    text = text.replace('            slider.addEventListener("input", event => {', '            slider.value = "2";\n            const initialBadge = document.getElementById("lodLevelBadge");\n            if (initialBadge) initialBadge.textContent = "L1–L2 · overview";\n            slider.addEventListener("input", event => {', 1)
    text = text.replace('const value = Math.max(1, Math.min(6, parseInt(slider.value, 10) || 6));', 'const value = Math.max(1, Math.min(6, parseInt(slider.value, 10) || 2));')
    replacements = {
        '"L1 (6 Subcollections)"': '"L1 · 6 subcollections"',
        '"L1–L2 (74 Hauptbestände)"': '"L1–L2 · overview"',
        '"L1–L3 (274 Fachordner)"': '"L1–L3 · places + subject folders"',
        '"L1–L4 (312 Teilsammlungen)"': '"L1–L4 · detailed collections"',
        '"L1–L5 (432 Befundordner)"': '"L1–L5 · near-complete structure"',
        '"L1–L6 (Alle 434 Ordner)"': '"L1–L6 · all 434 folders"',
        '"Force-Directed (COSE, Topologie)"': '"Force-directed (COSE)"',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Add bundling refresh hooks and export.
    text = replace_once(
        text,
        '            resetPresetPositions\n        };',
        '            resetPresetPositions,\n            bundleEdges: applyHierarchicalEdgeBundling\n        };',
        "layout export",
    )
    text = replace_once(
        text,
        '    window.addEventListener("iuenna:canonical-graph-loaded", () => {\n        resetPresetPositions();\n    });',
        '    window.addEventListener("iuenna:canonical-graph-loaded", () => {\n        resetPresetPositions();\n        scheduleEdgeBundling();\n    });\n    window.addEventListener("iuenna:macro-depth-changed", scheduleEdgeBundling);\n    window.addEventListener("iuenna:lod-shard-loaded", scheduleEdgeBundling);\n    window.addEventListener("iuenna:lod-shard-unloaded", scheduleEdgeBundling);',
        "bundling events",
    )

    LAYOUTS.write_text(text, encoding="utf-8")


def patch_injector_and_workflow() -> None:
    text = INJECT.read_text(encoding="utf-8")
    text = text.replace('data-source.js?v=20260912-3', 'data-source.js?v=20260912-4')
    text = text.replace('layouts.js?v=20260912-2', 'layouts.js?v=20260912-3')
    text = text.replace('if \'./data-source.js?v=20260912-3\' not in text:', 'if \'./data-source.js?v=20260912-4\' not in text:')
    text = text.replace('if \'./layouts.js?v=20260912-2\' not in text:', 'if \'./layouts.js?v=20260912-3\' not in text:')
    INJECT.write_text(text, encoding="utf-8")

    wf = WORKFLOW.read_text(encoding="utf-8")
    wf = wf.replace('data-source.js?v=20260912-3', 'data-source.js?v=20260912-4')
    wf = wf.replace('layouts.js?v=20260912-2', 'layouts.js?v=20260912-3')
    # Old generated UI string was German; progressive runtime now owns this UX.
    wf = wf.replace("          grep -q 'Kantentexte einblenden' graph/index.html\n", "")
    wf = wf.replace(
        "          grep -q 'arche_graph_lod_manifest.json' graph/data-source.js\n",
        "          grep -q 'arche_graph_lod_manifest.json' graph/data-source.js\n          grep -q 'INITIAL_MACRO_DEPTH = 2' graph/data-source.js\n          grep -q 'setMacroDepth' graph/data-source.js\n          grep -q 'applyHierarchicalEdgeBundling' graph/layouts.js\n          grep -q 'unbundled-bezier' graph/layouts.js\n",
    )
    WORKFLOW.write_text(wf, encoding="utf-8")


def main() -> None:
    patch_data_source()
    patch_layouts()
    patch_injector_and_workflow()
    print("[✓] Progressive graph LOD + hierarchy-aware edge bundling installed")


if __name__ == "__main__":
    main()
