#!/usr/bin/env python3
"""Audit source-blind final-leaf derivation against post-truth discovery records."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-root", type=Path, required=True)
    parser.add_argument("--pretruth-root", type=Path, required=True)
    args = parser.parse_args()
    failed = False
    for case_dir in sorted(path for path in args.native_root.iterdir() if path.is_dir()):
        evaluation_path = case_dir / "tnqc_fixed_trajectory_evaluation.json"
        if not evaluation_path.is_file():
            continue
        evaluation = json.loads(
            evaluation_path.read_text()
        )
        manifest = json.loads(
            (
                args.pretruth_root
                / case_dir.name
                / "source_blind_case_manifest.json"
            ).read_text()
        )
        authoritative = set(
            evaluation["tnqc_gate_scope_audit"]["final_leaf_candidate_ids"]
        )
        derived = set(manifest["final_leaf_candidate_ids"])
        missing = sorted(authoritative - derived)
        extra = sorted(derived - authoritative)
        print(
            case_dir.name,
            "authoritative=", len(authoritative),
            "derived=", len(derived),
            "missing=", missing[:10],
            "extra=", extra[:10],
        )
        failed = failed or bool(missing or extra)
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
