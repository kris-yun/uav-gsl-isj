#!/usr/bin/env python3
"""Assemble the 30 controlled-source CAL worlds and freeze the one M2 table."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np


CONTRACT = "CTPI_M2_SOURCE_INTERVENTION_CAL_FREEZE_V1"
HOUSES = ("H01", "H02", "H03")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_forecast(path: Path):
    spec = importlib.util.spec_from_file_location("ctpi_m2_source_intervention_forecast", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("CTPI_M2_CAL_FORECAST_IMPORT")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cal-root", type=Path, required=True)
    parser.add_argument("--world-manifest", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--stage1-root", type=Path, required=True)
    parser.add_argument("--forecast-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"CTPI_M2_CAL_REFUSE_STALE_OUTPUT:{args.output}")
    if (args.cal_root / "CAL_BATCH_PASS").read_text(encoding="utf-8").strip() != "CTPI_M2_CAL_BATCH=PASS worlds=30":
        raise RuntimeError("CTPI_M2_CAL_BATCH_NOT_PASS")
    manifest = json.loads(args.world_manifest.read_text(encoding="utf-8"))
    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    if manifest.get("contract") != "CTPI_M2_SOURCE_INTERVENTION_WORLD_MANIFEST_V1" or not manifest.get("pass"):
        raise RuntimeError("CTPI_M2_CAL_WORLD_MANIFEST")
    if selection.get("contract") != "CTPI_M2_SOURCE_SELECTION_V3" or not selection.get("pass"):
        raise RuntimeError("CTPI_M2_CAL_SELECTION")
    if sha256_file(args.selection) != manifest["selection_sha256"]:
        raise RuntimeError("CTPI_M2_CAL_SELECTION_HASH")
    forecast = load_forecast(args.forecast_code)

    records: list[dict[str, Any]] = []
    world_hashes: dict[str, str] = {}
    for house in HOUSES:
        stage_path = args.stage1_root / f"{house}_FACTORIAL.npz"
        with np.load(stage_path, allow_pickle=False) as archive:
            # Realized historical observations in this archive are deliberately
            # not accessed.  Only frozen predictive-bank features are read.
            carrier_ids = np.asarray(archive["carrier_ids"]).astype(str)
            q_raw = np.asarray(archive["q_raw"], dtype=np.float64)
        if q_raw.shape != (10, len(carrier_ids), 15):
            raise RuntimeError(f"CTPI_M2_CAL_QRAW_SHAPE:{house}:{q_raw.shape}")
        carrier_to_index = {value: index for index, value in enumerate(carrier_ids)}
        house_worlds = [row for row in manifest["formal_worlds"]
                        if row["set"] == "M2_CAL" and row["house"] == house]
        if len(house_worlds) != 10:
            raise RuntimeError(f"CTPI_M2_CAL_WORLD_COUNT:{house}")
        for world in house_worlds:
            world_id = world["world_id"]
            world_dir = args.cal_root / world_id
            if not (world_dir / "PASS").is_file() or (world_dir / "FAIL").exists():
                raise RuntimeError(f"CTPI_M2_CAL_WORLD_NOT_PASS:{world_id}")
            audit_path = world_dir / "WORLD_AUDIT.json"
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            if not audit.get("pass") or audit.get("world_id") != world_id:
                raise RuntimeError(f"CTPI_M2_CAL_WORLD_AUDIT:{world_id}")
            if audit["world_manifest_sha256"] != sha256_file(args.world_manifest):
                raise RuntimeError(f"CTPI_M2_CAL_WORLD_MANIFEST_LINK:{world_id}")
            world_hashes[world_id] = sha256_file(audit_path)
            carrier = str(world["controlled_carrier_id"])
            if carrier not in carrier_to_index:
                raise RuntimeError(f"CTPI_M2_CAL_CARRIER:{world_id}:{carrier}")
            source_index = carrier_to_index[carrier]
            route = int(world["route_index"])
            raw = q_raw[route, source_index]
            counts = np.rint(raw * 9.0 - 0.5).astype(np.int64)
            if np.max(np.abs(raw * 9.0 - 0.5 - counts)) > 1.0e-9:
                raise RuntimeError(f"CTPI_M2_CAL_QRAW_NOT_COUNT:{world_id}")
            with (world_dir / "stop_events.csv").open(newline="", encoding="utf-8") as source:
                events = list(csv.DictReader(source))
            if len(events) != 15:
                raise RuntimeError(f"CTPI_M2_CAL_EVENT_COUNT:{world_id}")
            for index, (count, event) in enumerate(zip(counts, events), 1):
                expected_action = f"{house}_route{route:02d}_stop{index:02d}"
                if event["action_id"] != expected_action or int(event["stop_id"]) != index:
                    raise RuntimeError(f"CTPI_M2_CAL_ACTION_ID:{world_id}:{index}")
                records.append({
                    "world_id": world_id, "house": house,
                    "controlled_carrier_id": carrier, "route_index": route,
                    "stop_id": index, "action_id": expected_action,
                    "member_hit_count": int(count),
                    "observed_event": int(event["observed_hit"]),
                    "world_audit_sha256": world_hashes[world_id],
                })

    if len(records) != 450:
        raise RuntimeError(f"CTPI_M2_CAL_RECORD_COUNT:{len(records)}")
    k = np.asarray([row["member_hit_count"] for row in records], dtype=np.int64)
    y = np.asarray([row["observed_event"] for row in records], dtype=np.int8)
    for house in HOUSES:
        observed_hist = np.bincount(
            np.asarray([row["member_hit_count"] for row in records if row["house"] == house]),
            minlength=9,
        )
        expected_hist = np.asarray(selection["houses"][house]["sets"]["M2_CAL"]["expected_k_histogram"])
        if not np.array_equal(observed_hist, expected_hist):
            raise RuntimeError(f"CTPI_M2_CAL_K_HISTOGRAM:{house}")
    fit = forecast.fit_source_intervention_table(k, y)
    table = np.asarray(fit["table"], dtype=np.float64)
    base = forecast.baseline_probability(k)
    m2 = forecast.calibrated_probability(k, table)
    base_nll, base_brier = forecast._loss(base, y)
    m2_nll, m2_brier = forecast._loss(m2, y)

    args.output.mkdir(parents=True, exist_ok=False)
    csv_path = args.output / "CAL_RECORDS.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(records[0]))
        writer.writeheader(); writer.writerows(records)
    npz_path = args.output / "CAL_RECORDS.npz"
    np.savez_compressed(
        npz_path, member_hit_count=k, observed_event=y,
        world_id=np.asarray([row["world_id"] for row in records]),
        house=np.asarray([row["house"] for row in records]),
        controlled_carrier_id=np.asarray([row["controlled_carrier_id"] for row in records]),
        action_id=np.asarray([row["action_id"] for row in records]),
    )
    table_payload = {
        "contract": "CTPI_M2_SOURCE_INTERVENTION_TABLE_FREEZE_V1",
        "fit": fit,
        "forecast_code_path": str(args.forecast_code),
        "forecast_code_sha256": sha256_file(args.forecast_code),
        "world_manifest_sha256": sha256_file(args.world_manifest),
        "selection_sha256": sha256_file(args.selection),
        "cal_records_csv_sha256": sha256_file(csv_path),
        "cal_records_npz_sha256": sha256_file(npz_path),
        "confirm_data_access": False,
        "localization_metric_access": False,
        "m1_posterior_access": False,
    }
    table_path = args.output / "M2_CALIBRATION_TABLE.json"
    table_path.write_bytes(canonical_bytes(table_payload))
    report = {
        "contract": CONTRACT,
        "world_count": 30, "record_count": 450,
        "world_audit_sha256": world_hashes,
        "k_histogram": np.bincount(k, minlength=9).tolist(),
        "hit_count": int(np.count_nonzero(y)),
        "cal_descriptive_only": {
            "baseline_nll": float(np.mean(base_nll)), "m2_nll": float(np.mean(m2_nll)),
            "baseline_brier": float(np.mean(base_brier)), "m2_brier": float(np.mean(m2_brier)),
            "baseline_ece_5bin": forecast._ece(base, y), "m2_ece_5bin": forecast._ece(m2, y),
        },
        "table_sha256": sha256_file(table_path),
        "forecast_code_sha256": sha256_file(args.forecast_code),
        "confirm_generated_or_opened": False,
        "pass": True,
        "verdict": "CTPI_M2_SOURCE_INTERVENTION_CAL_FREEZE=PASS",
    }
    report_path = args.output / "CAL_FIT_REPORT.json"
    report_path.write_bytes(canonical_bytes(report))
    manifest_rows = []
    for path in sorted(args.output.iterdir()):
        if path.is_file():
            manifest_rows.append(f"{path.name}\t{path.stat().st_size}\t{sha256_file(path)}")
    (args.output / "FILE_SHA256.tsv").write_text("\n".join(manifest_rows) + "\n", encoding="utf-8")
    print(report["verdict"])
    print(f"CTPI_M2_CAL_TABLE_SHA256={report['table_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
