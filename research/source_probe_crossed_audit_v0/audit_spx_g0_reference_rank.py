#!/usr/bin/env python3
"""Reference-only identifiability audit for frozen pairwise PCA2 blocks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from score_spx_g0 import EVIDENCE_REL, FOLDS, PROTOCOLS, pair_table, tensor_paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    paths = tensor_paths(repo / EVIDENCE_REL)
    tensors = {key: np.load(path, mmap_mode="r", allow_pickle=False) for key, path in paths.items()}
    records = []
    for pair in pair_table(repo):
        indices = [int(pair["source0_index"]), int(pair["source1_index"])]
        for protocol in PROTOCOLS:
            data = tensors[(pair["panel"], protocol)][indices]
            for fold, held in enumerate(FOLDS):
                reference = [i for i in range(16) if i not in held]
                for block in range(5):
                    raw = data[:, reference, 2 * block:2 * block + 2].reshape(24, 60)
                    varying = int(np.count_nonzero(np.var(raw, axis=0) > 0))
                    if varying < 2:
                        records.append({"panel": pair["panel"], "pair_index": pair["pair_index"],
                                        "protocol": protocol, "fold": fold, "block": block,
                                        "varying_raw_dimensions": varying,
                                        "reference_all_zero": bool(np.all(raw == 0))})
    summary = {"stage": "REFERENCE_ONLY_PCA2_RANK_AUDIT", "pair_count": 87,
               "pair_protocol_fold_block_total": 87 * 2 * 4 * 5,
               "insufficient_two_dimension_cases": len(records),
               "all_zero_cases": sum(row["reference_all_zero"] for row in records),
               "affected_pair_protocols": len({(row["panel"], row["pair_index"], row["protocol"]) for row in records}),
               "affected_pairs": len({(row["panel"], row["pair_index"]) for row in records}),
               "cases": records, "audit_uses_targets": False,
               "note": "Only the 12 reference realizations per frozen fold are inspected; no pair utility or held-out score is calculated."}
    output = repo / EVIDENCE_REL / "SPX_G0_REFERENCE_PCA_RANK_AUDIT.json"
    output.write_bytes((json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps({key: value for key, value in summary.items() if key != "cases"}))


if __name__ == "__main__":
    main()
