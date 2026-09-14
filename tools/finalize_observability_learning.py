#!/usr/bin/env python3
"""Finalize the observability-learning falsification package and hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--result-note", type=Path, required=True)
    args = parser.parse_args()
    gate = json.loads((args.out_dir / "FINAL_GATE.json").read_text(encoding="utf-8"))
    results = json.loads((args.out_dir / "FALSIFICATION_RESULTS.json").read_text(encoding="utf-8"))
    gate["falsification_results_sha256"] = sha256_file(args.out_dir / "FALSIFICATION_RESULTS.json")
    gate["finalization_status"] = "PASS"
    (args.out_dir / "FINAL_GATE.json").write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    required = [
        args.out_dir / name for name in (
            "LEARNING_POLICY_FREEZE.json", "DATASET_INTEGRITY.json", "LABEL_DISTRIBUTION.json", "FALSIFICATION_RESULTS.json", "FINAL_GATE.json", "PRE_MODEL_SHA256SUMS", "dataset.npz",
        )
    ]
    required += [args.result_note, args.repo / "tools/build_observability_learning_dataset.py", args.repo / "tools/create_observability_learning_policy.py", args.repo / "tools/run_observability_learning_falsification.py"]
    lines = [f"{sha256_file(path)}  {path.relative_to(args.repo.resolve()).as_posix()}" for path in sorted({path.resolve() for path in required}, key=lambda path: str(path).lower())]
    (args.out_dir / "FINAL_SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"falsification": results["OBSERVABILITY_AWARE_LEARNING_FALSIFICATION"], "hash_entries": len(lines)}))


if __name__ == "__main__":
    main()
