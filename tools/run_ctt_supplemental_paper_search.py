#!/usr/bin/env python3
"""Run the installed paper-search API and preserve abstracts as JSON."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


SEARCH_MODULE = Path(
    r"D:\ZYC\UAV\.codex\skills\paper_search\scripts\search_papers.py"
)
OUTPUT = Path(
    "docs/ctt_scoop_check_20260830/supplemental_search_20260831.json"
)
QUERIES = [
    "persistent latent state repeated observations source transport inversion",
    "dynamic tomography latent motion consistency sparse observations",
    "robotic gas source localization multiple dispersion models persistent model identity sequential observations",
]


def main() -> int:
    sys.path.insert(0, str(SEARCH_MODULE.parent))
    spec = importlib.util.spec_from_file_location("ctt_paper_search", SEARCH_MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load paper-search module: {SEARCH_MODULE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.search_papers(
        query=QUERIES,
        start_year=2022,
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
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {"queries": QUERIES, "start_year": 2022, "end_year": 2026, "results": result},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    counts = {source: len(papers) for source, papers in result.items()}
    print(json.dumps({"output": str(OUTPUT), "counts": counts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
