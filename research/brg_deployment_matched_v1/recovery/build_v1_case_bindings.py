"""Freeze V1 ROS case bindings from the source-blind 72-run manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
ACTIVE = PurePosixPath("/home/zyc/brg_v1_active_case_20260928")
SCENARIOS = PurePosixPath("/mnt/hgfs/workspace/GADEN_files/scenarios")
ENV = {
    ("House01", "1,3-2,4_fast"): (0, (-3.17, -1.75), 596,
        "ce18a95c7bb44cda91395c6febf19b967ebf477e6bd174c7f5e2ed7e048509b7"),
    ("House02", "3,5-1_slow"): (1, (-.5, -2.5), 630,
        "9c77674d7ebaff306b81b2f5c36e893bbb57099b661afe6e030a2eb57b04adeb"),
    ("House02", "4,5-3_slow"): (2, (-.5, -2.5), 630,
        "3974e8c9b24ad8ae46afe68cf828d319a08228522acdf2e8e926d3458cff73c0"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = ROOT / "FROZEN_RUN_MANIFEST.json"
    if sha(manifest) != "891a01d580ebc8ddbfa20b4ec2e3e0462cbe54b49232d65c1a36d4982ff4b2fe":
        raise RuntimeError("frozen source/seed contract changed")
    rows = json.loads(manifest.read_text())["runs"]
    out = ROOT / "v1_cases"
    out.mkdir(exist_ok=True)
    checksums = []
    for run in rows:
        key = (run["house"], run["wind"])
        index, start, support, fingerprint = ENV[key]
        run_id = run["run_id"]
        case = {
            "case_id": run_id, "ordinal": run["ordinal"], "house": run["house"],
            "wind": run["wind"], "source_id": run["source_id"],
            "plume_id": run_id, "historical_seed": run["historical_seed"],
            "split": run["split"], "truth_xy": run["xyz"][:2],
            "truth_z_m": run["xyz"][2], "start_xy": list(start),
            "initial_pose_id": f"frozen_{run['house']}_native_start",
            "observation_contract_id": "VGR_FOPDT_300S_PHYSICAL_FRAME_V1",
            "environment_index": index, "candidate_support_count": support,
            "candidate_support_id": fingerprint, "truth_in_support": True,
            "reporting_stratum": "in_support",
            "scenario_root": str(SCENARIOS / run["house"]),
            "realization": str(ACTIVE / run_id / "realization"),
            "frozen_writer_time_map_sha256": sha(ROOT / "RESULT_TIME_MAP_300S.tsv"),
        }
        path = out / f"{run['ordinal']:03d}_{run_id}.json"
        path.write_text(json.dumps(case, indent=2) + "\n")
        checksums.append({"ordinal": run["ordinal"], "case_file": path.name,
                          "sha256": sha(path), "split": run["split"]})
    (ROOT / "V1_CASE_BINDINGS.json").write_text(json.dumps({"cases": checksums,
        "manifest_sha256": sha(manifest), "time_map_sha256": sha(ROOT / "RESULT_TIME_MAP_300S.tsv"),
        "sources_grouped_before_concentration": True}, indent=2) + "\n")
    print(json.dumps({"status": "V1_72_CASE_BINDINGS_FROZEN", "cases": len(checksums),
                      "bindings_sha256": sha(ROOT / "V1_CASE_BINDINGS.json")}))


if __name__ == "__main__":
    main()
