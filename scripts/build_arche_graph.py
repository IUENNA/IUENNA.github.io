#!/usr/bin/env python3
"""Compatibility entry point for the canonical IUENNA ARCHE graph builder.

The implementation lives in `build_complete_arche_graph.py`. Keeping this file
as a thin wrapper prevents the two graph builders from diverging semantically.
"""

from build_complete_arche_graph import build_graph


if __name__ == "__main__":
    build_graph()
