#!/usr/bin/env python3
"""Persist the raw multi-source 2026 literature search, including abstracts.

The installed paper-search CLI in this workspace predates its documented
``--json`` flag.  This wrapper calls the same public ``search_papers`` function
and serializes its return value so the relevance decisions remain auditable.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


QUERIES = [
    "spatial dither lock-in detection gradient estimation mobile robot odor plume",
    "extremum seeking coded excitation sensor latency active sensing",
    "phase-sensitive detection moving sensor source localization",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--search-script", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.search_script.parent))
    spec = importlib.util.spec_from_file_location("paper_search_runtime", args.search_script)
    if spec is None or spec.loader is None:
        raise ImportError("PAPER_SEARCH_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    results = module.search_papers(
        query=QUERIES,
        start_year=2026,
        end_year=2026,
        max_results=12,
        sources=["arxiv", "open_alex", "dblp"],
    )
    payload = {
        "queries": QUERIES,
        "year_range": [2026, 2026],
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({source: len(papers) for source, papers in results.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
