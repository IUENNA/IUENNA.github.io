#!/usr/bin/env python3
"""Fetch the authoritative IUENNA ARCHE metadata graph as Turtle.

The script downloads the complete metadata graph reachable from the IUENNA top
collection (ARCHE ID 1792170) using ARCHE's documented `relatives` read mode.
The resulting snapshot is written atomically to `data/arche_full_metadata.ttl`.
"""
from __future__ import annotations

import argparse
import os
import tempfile
import urllib.parse
import urllib.request

ARCHE_API_BASE = "https://arche.acdh.oeaw.ac.at/api"
TOP_COLLECTION_ID = "1792170"
DEFAULT_OUTPUT = os.path.join("data", "arche_full_metadata.ttl")
MIN_EXPECTED_BYTES = 1_000_000


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
