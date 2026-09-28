#!/usr/bin/env python3
"""Bundle the train/dev inputs and stopped AOD v1 calibration for independent review."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


def sha(blob: bytes):
    return hashlib.sha256(blob).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--archives", type=Path, required=True)
    p.add_argument("--bank-dir", type=Path, required=True)
    p.add_argument("--h02-raw", type=Path, required=True)
    p.add_argument("--supplied-review", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    here = Path(__file__).resolve().parent
    old = here.parent / "aod_conditional_filter_v0"
    result = json.loads((here / "DEV_SCREEN_RESULT.json").read_text(encoding="utf-8"))
    assert result["status"] == "AOD_V1_DEV_SCREEN_FAIL_STOP_BEFORE_PLANNER"
    freeze = json.loads((here / "PREFIT_CONTRACT_20260928.json").read_text(encoding="utf-8"))
    assert sha(args.supplied_review.read_bytes()) == freeze["review_zip_sha256"]
    records = {}
    for name in ("PREFIT_CONTRACT_20260928.json", "TRAIN_ONLY_JOINT_CALIBRATION.json",
                 "DEV_SCREEN_RESULT.json", "H02_POSTSCREEN_EXPLANATION.json",
                 "AOD_V1_DEVELOPMENT_RESULT_20260928.md", "fit_joint_calibration.py",
                 "evaluate_joint_dev.py", "explain_joint_h02.py", "package_dev_review.py"):
        records[f"new/{name}"] = (here / name).read_bytes()
    for name in ("bank.py", "episode_io.py", "gain_innovation_bank.py",
                 "TRAIN_ONLY_CALIBRATION.json", "OPEN_DEV_CHECK.json"):
        records[f"old_reference/{name}"] = (old / name).read_bytes()
    with zipfile.ZipFile(args.supplied_review) as supplied:
        for name in ("code/evidence_decision_core.py", "code/test_core.py",
                     "README.md", "NEXT_ACTION.txt"):
            records[f"supplied_review/{name}"] = supplied.read(name)
    selected = []
    for case_file in sorted(args.cases.glob("*.json")):
        case = json.loads(case_file.read_text(encoding="utf-8"))
        if case["split"] not in ("train", "dev"):
            continue
        records[f"cases/{case_file.name}"] = case_file.read_bytes()
        name = f'native_{case["ordinal"]:03d}_{case["case_id"]}.tar.zst'
        archive = args.archives / name
        if not archive.is_file():
            raise FileNotFoundError(archive)
        records[f"native_archives/{name}"] = archive.read_bytes()
        selected.append({"case_id": case["case_id"], "split": case["split"],
                         "archive_sha256": sha(records[f"native_archives/{name}"])})
    assert len(selected) == 48 and sum(x["split"] == "train" for x in selected) == 40
    for env in (0, 1, 2):
        bank = args.bank_dir / f"env_{env}_bank.npz"
        blob = bank.read_bytes()
        assert sha(blob) == freeze["bank_sha256"][str(env)]
        records[f"banks/env_{env}_bank.npz"] = blob
    for name in ("sim_pose_trace.csv", "sensor_trace.csv", "measurement_blocks.csv",
                 "measurement_samples.csv"):
        records[f"h02_same_path/{name}"] = (args.h02_raw / name).read_bytes()
    records["INPUTS.json"] = (json.dumps({
        "status": "AOD_V1_DEV_STOP_REVIEW_INPUTS",
        "supplied_review_sha256": freeze["review_zip_sha256"],
        "frozen_train_dev_archives": selected,
        "note": "48 archived Native VGR episodes are original OPEN train/dev data. No House03 data, new plume, or new closed-loop run is included."
    }, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    records["SHA256SUMS"] = "".join(f"{sha(blob)}  {name}\n" for name, blob in sorted(records.items())).encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w") as out:
        for name, blob in sorted(records.items()):
            compression = zipfile.ZIP_STORED if name.endswith((".zst", ".npz")) else zipfile.ZIP_DEFLATED
            out.writestr(name, blob, compress_type=compression, compresslevel=6)
    with zipfile.ZipFile(args.output) as check:
        assert check.testzip() is None
        for name, blob in records.items():
            assert check.read(name) == blob
    print(json.dumps({"path": str(args.output), "bytes": args.output.stat().st_size,
                      "sha256": sha(args.output.read_bytes()), "files": len(records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
