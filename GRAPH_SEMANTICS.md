# IUENNA ARCHE Knowledge Graph – Semantic Model and Audit

## Scope

The IUENNA Knowledge Graph is a **provenance-aware graph projection of ARCHE metadata for discovery and exploration**. It is not intended to be a lossless replacement for the complete ARCHE RDF graph. The authoritative source remains the ARCHE repository and its RDF metadata.

Accordingly, claims such as „vollständige semantische Repräsentation des ARCHE-Bestands“ or „lückenlose Prädikaten-Extraktion“ should only be used if a build-specific audit demonstrates the relevant completeness criterion. For publication, the preferred description is:

> „eine provenance-erhaltende graphbasierte Projektion der für IUENNA relevanten ARCHE-Metadaten und -Relationen“.

## Canonical entity model

A single ARCHE identifier represents a single graph entity. The graph builder therefore enforces the invariant:

**one ARCHE ID = one graph node**

Curated classifications are represented as roles or additional node metadata rather than duplicate entities. In particular, the nine curated GeoPackage datasets are ARCHE Resources and are therefore represented by the same node as their corresponding resource record. A GeoPackage such as ARCHE `1798920` is consequently represented as one canonical node (normally `res_1798920`) with roles such as:

```json
{
  "arche_id": "1798920",
  "type": "dataset",
  "roles": ["resource", "dataset"]
}
```

The previous parallel representation as `dts_1798920` and `res_1798920` is no longer generated when both records refer to the same ARCHE ID.

## Two-pass graph construction

Graph construction is explicitly separated into two passes.

### Pass 1 – Nodes

All ARCHE-backed graph nodes are created first:

- collections and the top collection;
- resources;
- persons;
- organisations;
- publications;
- places;
- curated dataset roles.

Only after all nodes exist is the global ARCHE-ID-to-node-ID mapping considered complete.

### Pass 2 – Relations

Semantic relations are then resolved against the complete node map. This prevents Resource-level relations from being silently lost because the corresponding `res_*` node does not yet exist.

The configured ARCHE object predicates currently include:

- `isPartOf`
- `hasHosting`
- `hasOwner`
- `hasLicensor`
- `hasRightsHolder`
- `hasCurator`
- `hasDepositor`
- `hasMetadataCreator`
- `hasCreator`
- `hasContributor`
- `hasAuthor`
- `documents`
- `hasDigitisingAgent`
- `hasSpatialCoverage`
- `isMemberOf`

## Relation provenance

Every graph edge records its origin and semantic status. The principal statuses are:

| `relation_status` | Meaning |
|---|---|
| `asserted` | Relation explicitly asserted in ARCHE metadata or the authoritative Resource corpus |
| `inherited` | Relation inferred from the parent collection |
| `aggregated` | Relation aggregated from child resources for discovery/navigation |
| `curated` | Relation supplied by a curated IUENNA index derived from ARCHE metadata |
| `synthetic` | Non-semantic relation created exclusively for graph navigation/layout |

An inherited spatial relation may therefore be represented as:

```json
{
  "label": "hasSpatialCoverage",
  "provenance": "IUENNA-derived",
  "relation_status": "inherited",
  "derivations": [
    {
      "method": "inherited-from-parent",
      "inherited_from": "1792273"
    }
  ]
}
```

A direct ARCHE relation is represented as `provenance: "ARCHE-direct"` and `relation_status: "asserted"`.

## Spatial coverage

`build_authoritative_corpus.py` retains spatial provenance explicitly:

- `spatial_ids_direct` – `hasSpatialCoverage` directly asserted on the Resource;
- `spatial_ids_inherited` – spatial coverage inherited from its parent Collection;
- `spatial_ids` – effective values used for discovery;
- `spatial_relation_status` – `asserted`, `inherited`, or `none`;
- `spatial_inherited_from` – ARCHE ID of the parent from which the spatial relation was inherited.

Resources without a direct or inherited place no longer receive a synthetic default place such as „Jauntal“.

For graph connectivity, a previously unconnected Place may receive a `connectedForNavigation` edge. This edge is explicitly marked `semantic: false` and must not be interpreted as an ARCHE `hasSpatialCoverage` assertion.

## Curated Subject, Epoch, and License nodes

The current Subject, Epoch, and License helper nodes are deliberately curated graph projections. They do **not** constitute complete reproductions of the corresponding ARCHE vocabularies. The original values may continue to exist as attributes on ARCHE-backed nodes.

## Automatic graph audit

Every successful graph build writes:

`data/arche_graph_audit.json`

The audit records:

- number of source entities by role;
- source-role overlaps, especially Resource/Dataset overlaps;
- number of canonical ARCHE-backed graph nodes;
- duplicate ARCHE IDs remaining in the graph;
- dangling edges;
- edge counts by predicate, provenance, and relation status;
- unresolved ARCHE source and target IDs;
- ARCHE TTL triple counts for each configured predicate;
- number of resolvable ARCHE triples;
- number of corresponding asserted graph edges;
- predicate-level recall for resolvable triples.

For a predicate `P`, the principal completeness measure is:

```text
recall(P) = graph asserted edges reproduced from ARCHE(P)
            / resolvable ARCHE triples(P)
```

The builder fails when:

- duplicate ARCHE IDs remain;
- dangling edges are detected;
- a resolvable configured ARCHE TTL triple is not preserved in the graph.

The audit distinguishes repository completeness from graph-model completeness. An unresolved target is reported rather than silently interpreted as a missing graph relation.

## Reproducible build sequence

With `data/arche_full_metadata.ttl` available locally:

```bash
python3 scripts/parse_arche_full_ttl.py
python3 scripts/build_authoritative_corpus.py
python3 scripts/build_complete_arche_graph.py
python3 scripts/generate_graph_html.py
```

The complete TTL dump is intentionally excluded from Git with `*.ttl` / `data/*.ttl`; therefore generated graph artefacts should only be committed after rebuilding them from the authoritative local ARCHE dump and checking `data/arche_graph_audit.json`.

## Publication wording

Until a specific build has passed the graph audit, recommended wording is:

> „The IUENNA Knowledge Graph provides a provenance-aware graph projection of ARCHE metadata for discovery and exploration. It integrates the complete set of IUENNA entities represented by the build pipeline and selected ARCHE semantic relations, while explicitly distinguishing asserted, inherited, aggregated, curated, and synthetic relations.“

After a successful audit, completeness claims should be predicate-specific, for example:

> „For the configured ARCHE object predicates, the graph reproduces 100% of the ARCHE triples whose source and target entities are represented in the IUENNA graph; unresolved external or otherwise unmodelled targets are reported separately by the build audit.“
