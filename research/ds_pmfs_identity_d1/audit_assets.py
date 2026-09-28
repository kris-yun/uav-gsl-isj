"""Freeze the existing Native trajectories and amplitude products before D1 scoring.

This script reads names and hashes only. It never opens concentration values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
INVENTORY = REPO / "research/brg_deployment_matched_v1/recovery/NATIVE_OPEN_EPISODE_INVENTORY_FROZEN.json"
F1 = REPO / "research/aod_house03_f1_full624_20260927/templates"
HOST = Path(r"C:\Users\50176\Desktop\vm数据")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    native_dir = HOST / "BRG_V1_VGR_NATIVE_20260928"
    episodes = []
    for item in inventory["episodes"]:
        ordinal = int(item["ordinal"])
        matches = sorted(native_dir.glob(f"native_{ordinal:03d}_{item['case_id']}.tar.zst"))
        if len(matches) != 1:
            raise RuntimeError(f"missing or ambiguous original Native archive: {ordinal} {item['case_id']}")
        archive = matches[0]
        digest = sha(archive)
        if digest != item["package_sha256"]:
            raise RuntimeError(f"archive hash mismatch: {archive}")
        meta = HOST / "BRG_V1_EPISODES_20260928" / f"{ordinal:03d}_{item['case_id']}_native_pmfs.json"
        if not meta.is_file():
            raise RuntimeError(f"missing episode metadata: {meta}")
        m = json.loads(meta.read_text(encoding="utf-8"))
        env = int({("House01", "1,3-2,4_fast"): 0,
                   ("House02", "3,5-1_slow"): 1,
                   ("House02", "4,5-3_slow"): 2}[(m["house"], m["wind"])])
        episodes.append(dict(case_id=item["case_id"], house=m["house"], wind=m["wind"],
                             source_id=m["source_group"].split("/")[-1], env=env,
                             archive=str(archive), archive_sha256=digest,
                             episode_metadata=str(meta), episode_metadata_sha256=sha(meta),
                             event_count=int(item["events"]), support="native_legal",
                             recorded_policy="native_pmfs", split=item["split"]))
    cross = HOST / "AOD_FILTER_HOUSE123_3CASE_20260928"
    for tag, env, house, wind in [
        ("crosshouse_native_pmfs_H02_seed20702800", 2, "House02", "4,5-3_slow"),
        ("crosshouse_native_pmfs_H03_seed869241781_retry1", 3, "House03", "1-2,5_fast"),
    ]:
        meta = cross / f"{tag}.json"
        raw = cross / f"{tag}_raw"
        if not meta.is_file() or not raw.is_dir():
            raise RuntimeError(f"missing crosshouse Native trajectory: {tag}")
        m = json.loads(meta.read_text(encoding="utf-8"))
        if m.get("arm") != "native_pmfs" or m.get("case_id") is None:
            raise RuntimeError(f"not a verified Native case: {tag}")
        files = {name: sha(raw / name) for name in
                 ("measurement_events.csv", "measurement_blocks.csv", "measurement_samples.csv",
                  "source_update_complete.txt")}
        episodes.append(dict(case_id=m["case_id"], house=house, wind=wind,
                             source_id=m["source_id"], env=env, raw_dir=str(raw),
                             raw_files_sha256=files, episode_metadata=str(meta),
                             episode_metadata_sha256=sha(meta),
                             support="f1_full624_shadow_only" if env == 3 else "native_legal",
                             recorded_policy="native_pmfs", split="historical_open"))
    files = {}
    for env in range(3):
        for name in (f"env_{env}_bank.npz", f"env_{env}_occupancy.u8"):
            files[name] = sha(args.inputs / name)
    for name in ("h03_bank.npz", "h03_occupancy.u8", "h03_f1_occupancy.u8", "h03_f1_meta.csv"):
        files[name] = sha(args.inputs / name)
    for name in ("nominal_u_full_maps.npy", "nominal_rawu_full_maps.npy", "CANDIDATE_SUPPORT.csv"):
        files["f1/" + name] = sha(F1 / name)
    out = dict(protocol="DS_PMFS_IDENTITY_D1_ASSET_FREEZE", trajectory_count=len(episodes),
               environment_count=4, episodes=episodes, input_sha256=files,
               score="archived B2 nonnegative gain-profile SSE; EPS=1e-9; lower is better",
               prefixes="Native completed source-update stops: event 20,35,50,65 when present",
               sensor="each logged deployed measurement event once; all prior events up to prefix",
               projection="0.20 x 0.20 m area average, reject outside map",
               primary_unit="trajectory; then source and House aggregates, never update as independent replicate",
               h03_caveat="one Native H03 case has truth outside Native615; compare u/rawu on frozen F1 624 shadow support; do not call it Native615 exact-cell rank",
               no_new_simulation=True, no_planner_or_probability_change=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(trajectory_count=len(episodes), manifest_sha256=sha(args.output))))


if __name__ == "__main__":
    main()
