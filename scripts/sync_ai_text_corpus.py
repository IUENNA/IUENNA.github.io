#!/usr/bin/env python3
"""Normalize stale quantitative claims in IUENNA AI-facing text artifacts.

This is intentionally narrow: it replaces known legacy claims that conflated
repository entities with primary resources. Quantitative values come from the
validated graph audit so future rebuilds keep BYOAI, synthetic QA, finetuning
exports and the chat knowledge base aligned.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "arche_graph_audit.json"

TEXT_TARGETS = [
    ROOT / "byoai.html",
    ROOT / "scripts" / "generate_synthetic_qa.py",
    ROOT / "data" / "iuenna_synthetic_qa.json",
    ROOT / "data" / "iuenna_finetune_alpaca.json",
    ROOT / "data" / "iuenna_finetune_chatml.jsonl",
    ROOT / "data" / "iuenna_finetune_sharegpt.json",
]


def main() -> None:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    if audit.get("status") != "pass":
        raise SystemExit("Refusing to synchronize AI text corpus from a non-passing audit")

    nodes = int(audit["graph"]["nodes"])
    arche_backed = int(audit["graph"]["arche_backed_nodes"])
    resources = int(audit["inputs"]["resources"])

    en_nodes = f"{nodes:,}"
    en_arche = f"{arche_backed:,}"
    en_resources = f"{resources:,}"

    legacy_sentence = "The ARCHE repository houses 20,788 digital resources and over 356 GB"
    replacement_sentence = (
        f"The authoritative IUENNA primary-resource corpus contains {en_resources} archived files, "
        f"while the validated knowledge graph contains {en_nodes} nodes ({en_arche} ARCHE-backed entities); "
        "the archived holdings comprise over 356 GB"
    )

    changed = []
    for path in TEXT_TARGETS:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        text = text.replace(legacy_sentence, replacement_sentence)

        if path.name == "byoai.html":
            notice = (
                f'<div class="notice"><strong>Why the distinction matters:</strong> '
                f'<code>arche_corpus.json</code> contains {en_resources} primary resources/files, while the validated '
                f'Knowledge Graph contains {en_nodes} nodes, including {en_arche} ARCHE-backed entities. '
                f'MCP full-text retrieval operates on the primary-resource corpus, whereas semantic traversal uses '
                f'<code>arche_graph.json</code>; these are related but intentionally different quantitative layers.</div>'
            )
            text = re.sub(
                r'<div class="notice"><strong>Why the distinction matters:</strong>.*?</div>',
                notice,
                text,
                count=1,
                flags=re.DOTALL,
            )

        if text != original:
            path.write_text(text, encoding="utf-8")
            changed.append(str(path.relative_to(ROOT)))

    # This stage only guards the legacy claims it owns. Broader BYOAI/llms/OpenAPI
    # wording is normalized immediately afterwards by sync_graph_metadata.py and
    # validated again by build_ai_stack.py.
    forbidden = (
        "20,788 digital resources",
        "20,788 repository records",
    )
    for path in TEXT_TARGETS:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        hits = [token for token in forbidden if token in text]
        if hits:
            raise SystemExit(f"Stale quantitative AI claim remains in {path.relative_to(ROOT)}: {hits}")

    print(
        f"[✓] AI text corpus synchronized: {en_resources} primary resources; "
        f"{en_nodes} graph nodes; {en_arche} ARCHE-backed graph entities"
    )
    if changed:
        print("[✓] Updated: " + ", ".join(changed))
    else:
        print("[✓] AI text corpus already synchronized")


if __name__ == "__main__":
    main()
