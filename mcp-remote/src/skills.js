export const IUENNA_RESEARCH_SKILL_TEXT = `---
name: iuenna-research
description: Authoritative archaeological research workflow for the IUENNA micro-region (Jauntal/Podjuna, Carinthia, Austria). Enforces source priority (ARCHE PIDs first), findspot lookup, GeoPackage exploration, knowledge graph traversal, and Zotero bibliography resolution.
license: CC-BY-4.0
metadata:
  version: "1.0.0"
  author: "IUENNA Project (Dominik Hagmann, Franziska Waldhart)"
  arche_collection_pid: "https://hdl.handle.net/21.11115/0000-0016-7B39-F"
  zotero_group: "4910727"
---

# IUENNA Archaeological Research Skill

This skill provides normative instructions and orchestration logic for AI agents researching the archaeological corpus of the **IUENNA** project (*openIng the soUthErn jauNtal as a micro-regioN for future Archaeology*).

The IUENNA project investigates the micro-region of Jauntal/Podjuna in Carinthia, Austria. The long-term archived corpus is deposited in **ARCHE** (Austrian Centre for Digital Humanities and Cultural Heritage, Austrian Academy of Sciences) under PID [21.11115/0000-0016-7B39-F](https://hdl.handle.net/21.11115/0000-0016-7B39-F).

---

## 1. Corpus Metrics & Terminology

When analyzing or reporting IUENNA data, you must strictly distinguish between these metrics:

* **Primary Resource Corpus:** Exactly **20,355 primary archived files** (find documentation, plans, field reports, photos, scans, 3D models).
* **Knowledge Graph:** **21,071 nodes** and **281,851 directed edges** (comprising 21,061 ARCHE-backed entities + 10 curated helper nodes).
* **Archaeological Findspots:** **219 georeferenced findspots** across the Jauntal micro-region.
* **Archival Collections:** **434 collections** within ARCHE, organized around key top-level clusters:
  - \`HB\`: Hemmaberg
  - \`GLO\`: Globasnitz
  - \`JAU\`: Jaunstein
  - \`STE\`: Sankt Stefan
  - \`TAL\`: Jauntal regional surveys
  - \`RET\`: Retrodigitalisate (digitized legacy publications)
* **GIS Datasets:** **9 curated GeoPackages** with authoritative spatial features and layer descriptions.
* **Important Notice:** The ARCHE repository statistic \`total_items\` reflects total system entities/metadata records. It is **not** the count of primary files.

---

## 2. Source Priority for AI Systems

Always prioritize sources in the following strict hierarchy:

1. **ARCHE Persistent Identifiers (PIDs):**  
   Persistent Handles (\`https://hdl.handle.net/21.11115/...\`) are the authoritative scientific source for long-term data preservation.
2. **IUENNA Machine-Readable Endpoints:**  
   Optimized discovery layer on GitHub Pages (\`https://iuenna.github.io/data/\`).
3. **IUENNA Knowledge Graph:**  
   Semantic relationships and CIDOC-CRM/ARCHE property paths (\`get_graph_neighborhood\`).
4. **IUENNA Web Mapping & Research Blog:**  
   Contextual documentation, historical narratives, and ongoing excavation notes ([https://iuenna.hypotheses.org/](https://iuenna.hypotheses.org/)).

---

## 3. Tool Orchestration Workflow

When answering user queries, follow this systematic multi-step workflow:

### Step A: Identify Places and Findspots
* For queries about a specific site, location, church, or Roman villa (e.g. *Hemmaberg*, *Globasnitz*, *Jaunstein*, *St. Stefan*):
  1. Call \`get_findspot_details\` using the site name or findspot ID.
  2. Examine coordinates, descriptions, and linked curated datasets.
  3. If findspot metadata indicates broader relationships, proceed to Step B.

### Step B: Retrieve Primary Files and Archival Resources
* For retrieving documents, excavation diaries, plans, or images:
  1. Call \`get_related_resources\` to find files associated with a place, collection, or topic.
  2. Call \`search_iuenna_corpus\` for specific keyword searches across filenames, titles, descriptions, and archival paths.
  3. Always extract the \`pid\` or \`arche_id\` of matching primary files for citation.

### Step C: Traverse Semantic Graph Relationships
* For queries about people, excavation directors, dating periods, or interconnected collections:
  1. Call \`get_graph_neighborhood\` on the node ID or label.
  2. Filter by \`direction\` (\`incoming\` / \`outgoing\`) and \`predicate\` (e.g. \`hasContributor\`, \`hasSpatialCoverage\`, \`isPartOf\`) to avoid noise.
  3. Resolve neighbors back to ARCHE entities and PIDs.

### Step D: Cross-Reference Spatial Geodata
* For queries about GIS, vector boundaries, surveys, or LiDAR:
  1. Call \`get_geodata_catalog\` to inspect the 9 curated GeoPackages.
  2. Note the specific file name and the ARCHE download link or PID for GIS analysts.

### Step E: Verify Scientific Literature & Bibliography
* For queries about academic publications, excavation reports, or authors:
  1. Call \`get_project_bibliography\` (queries Zotero Group \`4910727\`).
  2. Cross-reference DOIs, publication years, and author names.

---

## 4. Citation and Attribution Rules

* **Mandatory PID Citation:** When referencing a specific dataset, document, plan, or photo, cite its individual persistent handle (e.g. \`https://hdl.handle.net/21.11115/0000-0016-...\`). Do not cite only the generic website URL.
* **Access and Rights Awareness:** Open discovery metadata does not imply public domain for all binaries. Distinguish between open metadata (CC BY 4.0) and individual resource access restrictions recorded in ARCHE.
* **Zero Hallucination:** Never fabricate excavation dates, stratigraphic unit numbers, find numbers, or institutional attributions. If an artifact or findspot has no documented record in the corpus, state clearly that it is not recorded in the IUENNA archive.
`;

export const SKILL_DIGEST = "sha256:da0e7b776d8f252132d5fbbfdec43197fbe0e149f4bb81ab4d6208cb7aa94264";
export const SKILL_SIZE = 5527;

export const SKILLS_CATALOG = [
  {
    uri: "skill://iuenna-research/SKILL.md",
    frontmatter: {
      name: "iuenna-research",
      description: "Authoritative archaeological research workflow for the IUENNA micro-region (Jauntal/Podjuna, Carinthia, Austria). Enforces source priority (ARCHE PIDs first), findspot lookup, GeoPackage exploration, knowledge graph traversal, and Zotero bibliography resolution.",
      license: "CC-BY-4.0",
      metadata: {
        version: "1.0.0",
        author: "IUENNA Project (Dominik Hagmann, Franziska Waldhart)",
        arche_collection_pid: "https://hdl.handle.net/21.11115/0000-0016-7B39-F",
        zotero_group: "4910727"
      }
    },
    resources: [
      {
        uri: "skill://iuenna-research/SKILL.md",
        digest: SKILL_DIGEST,
        size: SKILL_SIZE
      }
    ]
  }
];

export function getSkillsList() {
  return {
    resultType: "complete",
    skills: SKILLS_CATALOG
  };
}

export function getSkillByUri(uri) {
  const norm = String(uri || "").trim();
  const found = SKILLS_CATALOG.find(s => s.uri === norm || s.uri === `${norm}/SKILL.md` || norm.includes(s.frontmatter.name));
  return found || null;
}

export function getSkillResource(uri) {
  const norm = String(uri || "").trim();
  if (norm === "skill://iuenna-research/SKILL.md" || norm === "skill://iuenna-research" || norm.includes("iuenna-research")) {
    return {
      contents: [
        {
          uri: "skill://iuenna-research/SKILL.md",
          mimeType: "text/markdown",
          text: IUENNA_RESEARCH_SKILL_TEXT
        }
      ]
    };
  }
  return null;
}
