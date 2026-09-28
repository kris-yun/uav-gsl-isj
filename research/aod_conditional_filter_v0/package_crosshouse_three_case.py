#!/usr/bin/env python3
"""Package the frozen one-seed-per-House Native/AOD closed-loop comparison."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


STEMS = (
    "crosshouse_native_pmfs_H02_seed20702800",
    "crosshouse_aod_filter_H02_seed20702800",
    "crosshouse_native_pmfs_H03_seed869241781",
    "crosshouse_native_pmfs_H03_seed869241781_retry1",
    "crosshouse_aod_filter_H03_seed869241781",
)
CODE = (
    "bank.py",
    "bind_aod_case_vm.py",
    "bind_aod_crosshouse_vm.py",
    "calibrate_open.py",
    "check_open_dev.py",
    "episode_io.py",
    "gain_innovation_bank.py",
    "serve_aod_filter_vm.py",
    "TRAIN_ONLY_CALIBRATION.json",
    "OPEN_DEV_CHECK.json",
    "SYNTHETIC_SELFTEST.json",
    "TWO_ARM_FREEZE.json",
    "CROSSHOUSE_3CASE_FREEZE.json",
    "CROSSHOUSE_H03_TIMEBASE_INFRA_PATCH.json",
    "H03_F1_SOURCE0_REPLICA0_CASE.json",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--collected", type=Path, required=True)
    p.add_argument("--house01-zip", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    code_dir = Path(__file__).resolve().parent
    summary = {
        "scope": "VGR interactive closed-loop development comparison; one existing plume seed per House; no new plume or network",
        "budget_s": 300,
        "geometric_success_radius_m": 0.5,
        "source_estimate_definition": "final Native source-probability-map location estimate, not robot position",
        "cases": [],
        "infrastructure_note": "Initial House03 Native attempt stopped at paused t=0: its 986 recorded writer frames were incompatible with the House01/02 566-frame replay assertion. The same case was rerun with the signed House03 RESULT_TIME_MAP; failed attempt is preserved.",
        "interpretation": "Three individual development cases do not estimate cross-House success rates. House03 truth is outside the Native 615-candidate support; geometric error remains evaluable, exact-cell rank does not.",
    }
    h01 = json.loads((code_dir / "TWO_ARM_RESULT.json").read_text(encoding="utf-8"))
    summary["cases"].append({"house": "House01", "case_id": h01["case_id"], "native": h01["native"], "aod_filter": h01["aod_filter"]})
    for house, seed in (("House02", 20702800), ("House03", 869241781)):
        house_tag = "H02" if house == "House02" else "H03"
        native_suffix = "_retry1" if house == "House03" else ""
        n = json.loads((args.collected / f"crosshouse_native_pmfs_{house_tag}_seed{seed}{native_suffix}.json").read_text(encoding="utf-8"))
        a = json.loads((args.collected / f"crosshouse_aod_filter_{house_tag}_seed{seed}.json").read_text(encoding="utf-8"))
        assert n["case_id"] == a["case_id"] and n["truth_xy"] == a["truth_xy"]
        assert n["candidate_support_id"] == a["candidate_support_id"]
        assert n["budget_s"] == a["budget_s"] == 300
        assert n["arm"] == "native_pmfs" and a["arm"] == "aod_filter"
        assert n["navigation_failure_count"] == a["navigation_failure_count"] == 0
        assert n["callback_exception_count"] == a["callback_exception_count"] == 0
        summary["cases"].append({"house": house, "case_id": n["case_id"], "truth_in_support": n["truth_in_support"], "native": n, "aod_filter": a, "error_reduction_m": n["final_source_error_m"] - a["final_source_error_m"]})
    assert len(summary["cases"]) == 3

    records: dict[str, bytes] = {}
    with zipfile.ZipFile(args.house01_zip) as prior:
        for name in prior.namelist():
            records[f"house01_prior_review/{name}"] = prior.read(name)
    for stem in STEMS:
        result = args.collected / f"{stem}.json"
        assert result.is_file(), result
        records[f"house02_house03_runs/{result.name}"] = result.read_bytes()
        raw = args.collected / f"{stem}_raw"
        assert raw.is_dir(), raw
        for f in sorted(raw.rglob("*")):
            if f.is_file():
                records[f"house02_house03_runs/{raw.name}/{f.relative_to(raw).as_posix()}"] = f.read_bytes()
    for name in CODE:
        f = code_dir / name
        records[f"code_and_freeze/{name}"] = f.read_bytes()
    records["CROSSHOUSE_3CASE_RESULT.json"] = (json.dumps(summary, indent=2, ensure_ascii=False) + "\n").encode()
    records["SHA256SUMS"] = "".join(f"{sha256(value)}  {name}\n" for name, value in sorted(records.items())).encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as out:
        for name, value in sorted(records.items()):
            out.writestr(name, value)
    with zipfile.ZipFile(args.output) as check:
        assert check.testzip() is None
        for name, value in records.items():
            assert check.read(name) == value
    print(json.dumps({"path": str(args.output), "bytes": args.output.stat().st_size, "sha256": sha256(args.output.read_bytes()), "files": len(records), "summary": summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
