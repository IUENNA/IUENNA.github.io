#!/usr/bin/env python3
"""Small corrective pass for the progressive graph migration.

Keeps the migration compatible with the now-English graph UI and ensures that
resource-shard bookkeeping stays correct when structural depth is reduced.
"""
from pathlib import Path

DATA = Path("graph/data-source.js")
INJECT = Path("scripts/inject_graph_layout_module.py")


def patch_data_source() -> None:
    text = DATA.read_text(encoding="utf-8")
    old = '''        c.batch(() => {
            // Resource shards whose parent disappears are removed with that
            // branch so depth changes never leave orphaned resource clouds.
            c.nodes().filter(node => node.data("lod_collection_id") && !desiredIds.has(String(node.data("lod_collection_id")))).remove();

            c.edges().filter(edge => edge.data("lod_macro") === true && !desiredEdgeIds.has(edge.id())).remove();'''
    new = '''        // Resource shards whose parent disappears must be removed from both
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
            c.edges().filter(edge => edge.data("lod_macro") === true && !desiredEdgeIds.has(edge.id())).remove();'''
    if old in text:
        text = text.replace(old, new, 1)
    elif "Otherwise a later re-expansion" not in text:
        raise RuntimeError("Could not find progressive shard-cleanup anchor")
    DATA.write_text(text, encoding="utf-8")


def patch_injector() -> None:
    text = INJECT.read_text(encoding="utf-8")
    # The graph UI was translated to English after the original LOD injector
    # was written. Support both historical and current button strings.
    text = text.replace(
        '''    text = text.replace(
        '<span id="btnToggleEdgeLabelsText">Kantentexte verbergen</span>',
        '<span id="btnToggleEdgeLabelsText">Kantentexte einblenden</span>',
        1,
    )''',
        '''    text = text.replace(
        '<span id="btnToggleEdgeLabelsText">Kantentexte verbergen</span>',
        '<span id="btnToggleEdgeLabelsText">Kantentexte einblenden</span>',
        1,
    )
    text = text.replace(
        '<span id="btnToggleEdgeLabelsText">Hide Edge Labels</span>',
        '<span id="btnToggleEdgeLabelsText">Show Edge Labels</span>',
        1,
    )''',
        1,
    )
    text = text.replace(
        '''    if '<span id="btnToggleEdgeLabelsText">Kantentexte einblenden</span>' not in text:
        raise RuntimeError("Edge-label button does not reflect the hidden default")''',
        '''    if ('<span id="btnToggleEdgeLabelsText">Show Edge Labels</span>' not in text
            and '<span id="btnToggleEdgeLabelsText">Kantentexte einblenden</span>' not in text):
        raise RuntimeError("Edge-label button does not reflect the hidden default")''',
        1,
    )
    INJECT.write_text(text, encoding="utf-8")


def main() -> None:
    patch_data_source()
    patch_injector()
    print("[✓] Progressive graph migration compatibility fixes applied")


if __name__ == "__main__":
    main()
