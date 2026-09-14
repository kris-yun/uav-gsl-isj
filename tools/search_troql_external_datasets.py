#!/usr/bin/env python3
"""Search primary scholarly indexes for TROQL confirmation datasets.

The bundled paper-search CLI in this workspace predates its documented JSON
flag.  This thin wrapper uses the documented programmatic API so abstracts and
raw connector provenance remain auditable.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


SEARCH_MODULE = Path(
    r"D:\ZYC\UAV\.codex\skills\paper_search\scripts\search_papers.py"
)
OUTPUT = Path("paper_search_troql_external_dataset_2010_2026.json")
QUERIES = [
    "gas source localization public dataset known source multiple wind conditions",
    "robot olfaction dataset gas dispersion source location repeated experiments",
    "turbulent gas source localization benchmark dataset wind tunnel",
]


def main() -> None:
    sys.path.insert(0, str(SEARCH_MODULE.parent))
    spec = importlib.util.spec_from_file_location("codex_paper_search", SEARCH_MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load paper-search module: {SEARCH_MODULE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    results = module.search_papers(
        query=QUERIES,
        start_year=2010,
        end_year=2026,
        max_results=8,
        sources=[
            "semantic_scholar",
            "open_alex",
            "arxiv",
            "openreview",
            "crossref",
            "dblp",
        ],
        parallel=True,
    )
    payload = {
        "query": QUERIES,
        "start_year": 2010,
        "end_year": 2026,
        "max_results_per_source_per_query": 8,
        "results": results,
    }
    OUTPUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: len(value) for key, value in results.items()}, sort_keys=True))
    print(OUTPUT.resolve())


if __name__ == "__main__":
    main()
