#!/usr/bin/env python3
"""Keep Ask IUENNA available on all public top-level IUENNA pages.

Embedded map documents are intentionally excluded: their parent WMA page already
contains the assistant, and injecting it into the iframe would create a duplicate UI.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
VERSION = "3.0.0"

ROOT_PAGES = [
    "index.html",
    "byoai.html",
    "impressum-datenschutz.html",
]
SUB_PAGES = [
    "wma/wma.html",
    "wma/genai-wma-home.html",
    "wma/qgis2web-home.html",
    "graph/index.html",
    "graph/graph.html",
]


def read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def write(rel: str, text: str) -> None:
    p = ROOT / rel
    if p.exists():
        p.write_text(text, encoding="utf-8")


def ensure_assistant(rel: str, prefix: str) -> None:
    text = read(rel)
    if not text:
        return
    text = re.sub(
        r'\n\s*<!--\s*IUENNA Interactive Search & Research Assistant\s*-->\s*\n\s*<script src="(?:\.\./)?scripts/iuenna-chat\.js\?v=[^"]+" defer></script>',
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        r'\n\s*<!--\s*Ask IUENNA.*?-->\s*\n\s*<script src="(?:\.\./)?scripts/iuenna-chat\.js\?v=[^"]+" defer></script>',
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        r'\n\s*<script src="(?:\.\./)?scripts/iuenna-chat\.js\?v=[^"]+" defer></script>',
        "",
        text,
        flags=re.I,
    )
    tag = f'\n    <!-- Ask IUENNA: ARCHE-derived client-side metadata discovery -->\n    <script src="{prefix}scripts/iuenna-chat.js?v={VERSION}" defer></script>\n'
    if "</body>" not in text:
        raise SystemExit(f"No </body> found in {rel}")
    text = text.replace("</body>", tag + "</body>", 1)
    write(rel, text)


for rel in ROOT_PAGES:
    ensure_assistant(rel, "")
for rel in SUB_PAGES:
    ensure_assistant(rel, "../")

# BYOAI: use the current shared stylesheet and give the top-level collection the
# same project-level citation already exposed in llms.txt.
rel = "byoai.html"
text = read(rel)
text = re.sub(r'styles\.css\?v=[0-9.]+', 'styles.css?v=2.5.0', text)
old = re.compile(
    r'<section class="byoai-section">\s*'
    r'<h2><span class="byoai-section-icon"><i class="fa-solid fa-landmark"></i></span>Provenance, citation and rights</h2>.*?'
    r'</section>',
    re.S,
)
new = '''<section class="byoai-section">
        <h2><span class="byoai-section-icon"><i class="fa-solid fa-landmark"></i></span>Provenance, citation and rights</h2>
        <p>ARCHE is the authoritative long-term repository for the archived IUENNA research collection. Cite the top-level collection as:</p>
        <div class="notice" style="border-left-color:var(--secondary);">
            <strong>Project-level citation</strong><br>
            Hagmann, D., &amp; Waldhart, F. (Eds.). (2025). <em>IUENNA – openIng the soUthErn jauNtal as a micro-regioN for future Archaeology</em>. ARCHE – Austrian Research Culture Heritage Extended. <a href="https://hdl.handle.net/21.11115/0000-0016-7B39-F" target="_blank" rel="noopener">https://hdl.handle.net/21.11115/0000-0016-7B39-F</a>
        </div>
        <p><strong>Persistent collection identifier:</strong> <a href="https://hdl.handle.net/21.11115/0000-0016-7B39-F" target="_blank" rel="noopener">21.11115/0000-0016-7B39-F</a>. The corresponding ARCHE top-level collection is <a href="https://id.acdh.oeaw.ac.at/iuenna" target="_blank" rel="noopener">https://id.acdh.oeaw.ac.at/iuenna</a>.</p>
        <div class="notice"><strong>Access and reuse:</strong> open discovery metadata does not mean that every archived binary resource is openly downloadable or licensed identically. Inspect the citation, rights statement and access conditions of the specific ARCHE record before reuse.</div>
        <p>When using a specific dataset, document, image, GeoPackage, or other archived resource, cite its <strong>individual ARCHE record, PID and record-level metadata</strong> in addition to any relevant project-level citation.</p>
    </section>'''
text, count = old.subn(new, text, count=1)
if count != 1:
    raise SystemExit("Could not replace BYOAI provenance/citation section")
write(rel, text)

# Keep the legal/privacy wording aligned with the public assistant name.
for rel in ("impressum-datenschutz.html", "impressum-datenschutz.md"):
    text = read(rel)
    text = text.replace('»Frag IUENNA«', '»Ask IUENNA«')
    text = text.replace('„Frag IUENNA“', '„Ask IUENNA“')
    write(rel, text)

# The generated graph must keep Ask IUENNA after every rebuild.
rel = "scripts/generate_graph_html.py"
text = read(rel)
text = re.sub(
    r'(<!-- Responsive Navigation Burger Menu -->\s*\n\s*<script src="\.\./scripts/nav\.js\?v=[^"]+" defer></script>)'
    r'(?:\s*\n\s*<!-- Ask IUENNA.*?-->\s*\n\s*<script src="\.\./scripts/iuenna-chat\.js\?v=[^"]+" defer></script>)?',
    r'\1\n    <!-- Ask IUENNA: ARCHE-derived client-side metadata discovery -->\n    <script src="../scripts/iuenna-chat.js?v=3.0.0" defer></script>',
    text,
    count=1,
    flags=re.S,
)
write(rel, text)

# Update the misleading CSS section label; styles themselves remain shared.
rel = "styles.css"
text = read(rel)
text = text.replace(
    'IUENNA Client-Side Interactive AI Chat Widget (2-Stufen Hybrid)',
    'Ask IUENNA — client-side ARCHE metadata discovery assistant',
)
write(rel, text)

print("[OK] Ask IUENNA enabled sitewide; BYOAI collection citation synchronized.")
