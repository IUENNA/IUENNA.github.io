import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from build_authoritative_corpus import extract_arche_uris
from build_complete_arche_graph import NodeRegistry, parse_arche_relation_triples


class ArcheGraphSemanticsTest(unittest.TestCase):
    def test_dataset_resource_same_arche_id_merges_into_one_node(self):
        registry = NodeRegistry()
        registry.add(
            {
                "id": "res_1798920",
                "arche_id": "1798920",
                "type": "resource",
                "filename": "hb_geodaten_open.gpkg",
            },
            role="resource",
        )
        node_id = registry.add(
            {
                "id": "res_1798920",
                "arche_id": "1798920",
                "type": "dataset",
                "type_label": "Forschungsdatensatz / GeoPackage",
            },
            role="dataset",
            prefer_incoming=("type", "type_label"),
        )

        self.assertEqual(node_id, "res_1798920")
        self.assertEqual(len(registry.nodes_by_id), 1)
        self.assertEqual(registry.node_id_for_arche_id("1798920"), "res_1798920")
        self.assertEqual(registry.nodes_by_id[node_id]["type"], "dataset")
        self.assertEqual(registry.nodes_by_id[node_id]["roles"], ["dataset", "resource"])

    def test_spatial_extractor_does_not_break_on_dots_in_arche_url(self):
        block = """
        n2:hasSpatialCoverage <https://arche.acdh.oeaw.ac.at/api/1756734>,
            <https://arche.acdh.oeaw.ac.at/api/1757171>;
        n2:hasTitle "Example"@en .
        """
        self.assertEqual(
            extract_arche_uris("hasSpatialCoverage", block),
            ["1756734", "1757171"],
        )

    def test_ttl_parser_keeps_resource_level_multi_target_relations(self):
        ttl = """@prefix n2: <https://vocabs.acdh.oeaw.ac.at/schema#> .
<https://arche.acdh.oeaw.ac.at/api/9001> a n2:Resource;
    n2:hasCreator <https://arche.acdh.oeaw.ac.at/api/1001>,
        <https://arche.acdh.oeaw.ac.at/api/1002>;
    n2:hasRightsHolder <https://arche.acdh.oeaw.ac.at/api/2001>;
    n2:hasSpatialCoverage <https://arche.acdh.oeaw.ac.at/api/3001> .
<https://arche.acdh.oeaw.ac.at/api/1001> a n2:Person;
    n2:hasTitle "A" .
"""
        with tempfile.NamedTemporaryFile("w", suffix=".ttl", delete=False, encoding="utf-8") as handle:
            handle.write(ttl)
            path = handle.name
        try:
            triples = parse_arche_relation_triples(path)
        finally:
            os.unlink(path)

        self.assertIn(("9001", "hasCreator", "1001"), triples)
        self.assertIn(("9001", "hasCreator", "1002"), triples)
        self.assertIn(("9001", "hasRightsHolder", "2001"), triples)
        self.assertIn(("9001", "hasSpatialCoverage", "3001"), triples)


if __name__ == "__main__":
    unittest.main()
