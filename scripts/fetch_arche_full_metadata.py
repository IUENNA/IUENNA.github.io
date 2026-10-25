#!/usr/bin/env python3
"""Fetch the authoritative IUENNA ARCHE metadata graph as Turtle.

The script downloads the complete metadata graph reachable from the IUENNA top
collection (ARCHE ID 1792170) using ARCHE's documented `relatives` read mode.
The resulting snapshot is written atomically to `data/arche_full_metadata.ttl`.
"""
from __future__ import annotations

import argparse
import os
import re
import tempfile
import urllib.parse
import urllib.request

ARCHE_API_BASE = "https://arche.acdh.oeaw.ac.at/api"
TOP_COLLECTION_ID = "1792170"
DEFAULT_OUTPUT = os.path.join("data", "arche_full_metadata.ttl")
MIN_EXPECTED_BYTES = 1_000_000

# Entities referenced by IUENNA resources/publications/affiliations located outside the collection tree:
REFERENCED_EXTERNAL_ENTITIES = [
    "1756785",  # Dr. Georg Tiefengraber (Person, Author of 1756783)
    "46220",    # Mag. Dr. Alice Waldner (Person, Author of 1756890)
    "48505",    # Austrian Centre for Digital Humanities and Cultural Heritage (Organisation)
    "41760",    # Universität Wien (Organisation)
    "504765",   # Ludwig Boltzmann Gesellschaft (Organisation)
]

SCHEMA_NS = "https://vocabs.acdh.oeaw.ac.at/schema#"

CURATED_EXTERNAL_SUPPLEMENTS: dict[str, dict[str, object]] = {
    "1756785": {
        "type": "Person",
        "leading_statements": [
            'n2:hasFirstName "Georg"@und;',
            'n2:hasLastName "Tiefengraber"@und;',
            'n2:hasPersonalTitle "Dr.";',
            'n2:hasTitle "Georg Tiefengraber"@und;',
        ],
        "identifiers": [
            "<https://orcid.org/0000-0002-1800-6684>",
            "<https://arche.acdh.oeaw.ac.at/api/1756785>",
        ],
    },
    "46220": {
        "type": "Person",
        "leading_statements": [
            'n2:hasFirstName "Alice"@und;',
            'n2:hasLastName "Waldner"@und;',
            'n2:hasPersonalTitle "Mag. Dr.";',
            'n2:hasTitle "Alice Waldner"@und;',
            'n2:hasEmail "alice.waldner@oeai.at";',
            "n2:isMemberOf <https://arche.acdh.oeaw.ac.at/api/37483>;",
        ],
        "identifiers": [
            "<https://id.acdh.oeaw.ac.at/awaldner>",
            "<http://viaf.org/viaf/317123161>",
            "<https://orcid.org/0000-0002-6749-4493>",
            "<https://arche.acdh.oeaw.ac.at/api/46220>",
        ],
    },
    "48505": {
        "type": "Organisation",
        "leading_statements": [
            'n2:hasTitle "Austrian Centre for Digital Humanities and Cultural Heritage"@en;',
            'n2:hasAlternativeTitle "ACDH-CH";',
            'n2:hasCity "Wien"@de;',
            'n2:hasCountry "Österreich"@de;',
            'n2:hasUrl "https://www.oeaw.ac.at/acdh";',
            "n2:isMemberOf <https://arche.acdh.oeaw.ac.at/api/21003>;",
        ],
        "identifiers": [
            "<https://arche.acdh.oeaw.ac.at/api/48505>",
            "<https://d-nb.info/gnd/1123037736>",
            "<https://id.acdh.oeaw.ac.at/acdh>",
            "<http://viaf.org/viaf/6515148451584915970000>",
            "<https://ror.org/054w9k714>",
        ],
    },
    "41760": {
        "type": "Organisation",
        "leading_statements": [
            'n2:hasTitle "Universität Wien"@de;',
            'n2:hasAlternativeTitle "Uni Wien";',
            'n2:hasCity "Wien"@de;',
            'n2:hasCountry "Österreich"@de;',
            'n2:hasUrl "https://www.univie.ac.at";',
        ],
        "identifiers": [
            "<https://arche.acdh.oeaw.ac.at/api/41760>",
            "<https://d-nb.info/gnd/2024703-5>",
            "<http://www.wikidata.org/entity/Q165980>",
            "<https://ror.org/03prydq77>",
        ],
    },
    "504765": {
        "type": "Organisation",
        "leading_statements": [
            'n2:hasTitle "Ludwig Boltzmann Gesellschaft"@de;',
            'n2:hasAlternativeTitle "LBG";',
            'n2:hasCity "Wien"@de;',
            'n2:hasCountry "Österreich"@de;',
            'n2:hasUrl "https://lbg.ac.at";',
        ],
        "identifiers": [
            "<https://arche.acdh.oeaw.ac.at/api/504765>",
            "<https://d-nb.info/gnd/1024204324>",
            "<http://www.wikidata.org/entity/Q1874246>",
            "<https://ror.org/01y0m6940>",
        ],
    },
}


def normalize_external_entity_ttl(ext_id: str, ext_ttl: str) -> str:
    """Normalize a single-entity ARCHE Turtle snippet for inclusion in arche_full_metadata.ttl.

    Single-resource ARCHE Turtle responses define their own local `@prefix nX:`
    mappings where `n1:` or `n2:` may be the ACDH schema and `n4:`/`n9:` may be
    Wikidata, ORCID, or GND. This function resolves non-schema prefixed URIs to
    full `<URI>` references, maps the ACDH schema prefix to `n2:`, and merges
    curated authority identifiers (such as ROR and Wikidata) so downstream
    graph builds remain deterministic across live ARCHE refreshes.
    """
    prefixes: dict[str, str] = {}
    body_lines: list[str] = []
    for line in (ext_ttl or "").splitlines():
        m_pfx = re.match(r"^\s*@prefix\s+([A-Za-z0-9_-]+):\s*<([^>]+)>\s*\.\s*$", line)
        if m_pfx:
            prefixes[m_pfx.group(1)] = m_pfx.group(2)
        elif line.strip():
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    def replace_qname(match: re.Match[str]) -> str:
        pfx, local = match.group(1), match.group(2)
        ns = prefixes.get(pfx)
        if ns == SCHEMA_NS:
            return f"n2:{local}"
        if ns:
            return f"<{ns}{local}>"
        return f"n2:{local}"

    if body:
        body = re.sub(r"(?<![A-Za-z0-9_:/.-])(n\d+):([A-Za-z0-9_.-]+)", replace_qname, body)

    supplement = CURATED_EXTERNAL_SUPPLEMENTS.get(ext_id, {})
    m_type = re.search(r"\ba\s+n2:(\w+)\s*[;.]?", body)
    ent_type = str(supplement.get("type") or (m_type.group(1) if m_type else "Resource"))

    live_identifiers: list[str] = []
    for m_id in re.finditer(r"n2:hasIdentifier\s+(.*?)(?:;|\.\s*$)", body, re.MULTILINE):
        for token in m_id.group(1).split(","):
            tok = token.strip()
            if tok and tok not in live_identifiers:
                live_identifiers.append(tok)

    merged_identifiers: list[str] = []
    for tok in list(supplement.get("identifiers", [])) + live_identifiers:
        if tok and tok not in merged_identifiers:
            merged_identifiers.append(tok)

    cleaned_body = re.sub(r"\ba\s+n2:\w+\s*[;.]?", "", body)
    cleaned_body = re.sub(r"^\s*<https://arche\.acdh\.oeaw\.ac\.at/api/\d+>\s*", "", cleaned_body).strip()
    cleaned_body = re.sub(r"\bn2:hasIdentifier\s+.*?(?:;|\.\s*$)", "", cleaned_body, flags=re.MULTILINE).strip()

    statements: list[str] = list(supplement.get("leading_statements", []))
    if merged_identifiers:
        statements.append(f"n2:hasIdentifier {', '.join(merged_identifiers)};")
    if cleaned_body:
        if not cleaned_body.endswith("."):
            cleaned_body = cleaned_body.rstrip(";") + "."
        statements.append(cleaned_body)
    elif statements:
        statements[-1] = statements[-1].rstrip(";") + " ."

    joined = "\n    ".join(s for s in statements if s)
    return f"\n<https://arche.acdh.oeaw.ac.at/api/{ext_id}> a n2:{ent_type};\n    {joined}\n"


def build_url(resource_id: str = TOP_COLLECTION_ID) -> str:
    query = urllib.parse.urlencode({
        "readMode": "relatives",
        "format": "text/turtle",
    })
    return f"{ARCHE_API_BASE}/{resource_id}/metadata?{query}"


def fetch(output_path: str, resource_id: str = TOP_COLLECTION_ID) -> str:
    url = build_url(resource_id)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/turtle",
            "User-Agent": "IUENNA-Knowledge-Graph/1.0 (+https://iuenna.github.io/)",
        },
    )

    target_dir = os.path.dirname(os.path.abspath(output_path))
    fd, tmp_path = tempfile.mkstemp(prefix="arche_full_metadata_", suffix=".ttl.tmp", dir=target_dir)
    os.close(fd)

    try:
        total = 0
        with urllib.request.urlopen(request, timeout=180) as response, open(tmp_path, "wb") as out:
            content_type = response.headers.get("Content-Type", "")
            if "turtle" not in content_type.lower() and "text/plain" not in content_type.lower():
                raise RuntimeError(f"Unexpected ARCHE response Content-Type: {content_type!r}")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                total += len(chunk)

        if total < MIN_EXPECTED_BYTES:
            raise RuntimeError(f"ARCHE metadata dump unexpectedly small: {total:,} bytes")

        with open(tmp_path, "r", encoding="utf-8", errors="ignore") as check:
            head = check.read(250_000)
        expected_uri = f"{ARCHE_API_BASE}/{resource_id}"
        if expected_uri not in head:
            raise RuntimeError(f"Downloaded Turtle does not contain expected top collection URI {expected_uri}")

        if REFERENCED_EXTERNAL_ENTITIES:
            print(f"[*] Appending {len(REFERENCED_EXTERNAL_ENTITIES)} external referenced ARCHE entities...")
            with open(tmp_path, "a", encoding="utf-8") as out:
                out.write("\n# --- IUENNA External Referenced Entities ---\n")
                for ext_id in REFERENCED_EXTERNAL_ENTITIES:
                    ext_url = f"{ARCHE_API_BASE}/{ext_id}/metadata?format=text/turtle"
                    ext_ttl = ""
                    try:
                        ext_req = urllib.request.Request(ext_url, headers={"Accept": "text/turtle"})
                        with urllib.request.urlopen(ext_req, timeout=30) as ext_resp:
                            ext_ttl = ext_resp.read().decode("utf-8")
                    except Exception as err:
                        print(f"  [!] Warning: could not fetch external entity {ext_id}, using curated fallback: {err}")
                    out.write(normalize_external_entity_ttl(ext_id, ext_ttl))

        os.replace(tmp_path, output_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    print(f"[✓] Downloaded authoritative ARCHE metadata: {output_path} ({total / 1024 / 1024:.2f} MB)")
    print(f"[✓] Source: {url}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Target Turtle file")
    parser.add_argument("--resource-id", default=TOP_COLLECTION_ID, help="ARCHE top collection ID")
    args = parser.parse_args()
    fetch(args.output, args.resource_id)


if __name__ == "__main__":
    main()
