#!/usr/bin/env python3
"""One-shot source-conditioned M2 evaluation on the sealed CONFIRM set."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np


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
        raise RuntimeError("CTPI_M2_CONFIRM_FORECAST_IMPORT")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-root", type=Path, required=True)
    parser.add_argument("--world-manifest", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--stage1-root", type=Path, required=True)
    parser.add_argument("--forecast-code", type=Path, required=True)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"CTPI_M2_CONFIRM_REFUSE_STALE_OUTPUT:{args.output}")
    if (args.confirm_root / "CONFIRM_BATCH_PASS").read_text(encoding="utf-8").strip() != "CTPI_M2_CONFIRM_BATCH=PASS worlds=30":
        raise RuntimeError("CTPI_M2_CONFIRM_BATCH_NOT_PASS")
    authorization = json.loads(args.authorization.read_text(encoding="utf-8"))
    if authorization.get("CTPI_M2_SOURCE_INTERVENTION_PREGEN") != "PASS" or authorization.get("M2_CAL_FREEZE") != "PASS":
        raise RuntimeError("CTPI_M2_CONFIRM_AUTHORIZATION")
    manifest = json.loads(args.world_manifest.read_text(encoding="utf-8"))
    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    table_payload = json.loads(args.table.read_text(encoding="utf-8"))
    if table_payload.get("contract") != "CTPI_M2_SOURCE_INTERVENTION_TABLE_FREEZE_V1":
        raise RuntimeError("CTPI_M2_CONFIRM_TABLE_CONTRACT")
    if sha256_file(args.table) != authorization.get("m2_table_sha256"):
        raise RuntimeError("CTPI_M2_CONFIRM_TABLE_HASH")
    if sha256_file(args.forecast_code) != table_payload.get("forecast_code_sha256"):
        raise RuntimeError("CTPI_M2_CONFIRM_FORECAST_CODE_HASH")
    if sha256_file(args.world_manifest) != table_payload.get("world_manifest_sha256"):
        raise RuntimeError("CTPI_M2_CONFIRM_WORLD_MANIFEST_HASH")
    forecast = load_forecast(args.forecast_code)

    records: list[dict[str, Any]] = []
    world_hashes: dict[str, str] = {}
    for house in HOUSES:
        stage_path = args.stage1_root / f"{house}_FACTORIAL.npz"
        with np.load(stage_path, allow_pickle=False) as archive:
            carrier_ids = np.asarray(archive["carrier_ids"]).astype(str)
            q_raw = np.asarray(archive["q_raw"], dtype=np.float64)
        carrier_to_index = {value: index for index, value in enumerate(carrier_ids)}
        house_worlds = [row for row in manifest["formal_worlds"]
                        if row["set"] == "M2_CONFIRM" and row["house"] == house]
        if len(house_worlds) != 10:
            raise RuntimeError(f"CTPI_M2_CONFIRM_WORLD_COUNT:{house}")
        for world in house_worlds:
            world_id = world["world_id"]
            world_dir = args.confirm_root / world_id
            if not (world_dir / "PASS").is_file() or (world_dir / "FAIL").exists():
                raise RuntimeError(f"CTPI_M2_CONFIRM_WORLD_NOT_PASS:{world_id}")
            audit_path = world_dir / "WORLD_AUDIT.json"
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            if not audit.get("pass") or audit.get("world_id") != world_id:
                raise RuntimeError(f"CTPI_M2_CONFIRM_WORLD_AUDIT:{world_id}")
            world_hashes[world_id] = sha256_file(audit_path)
            carrier = str(world["controlled_carrier_id"])
            route = int(world["route_index"])
            source_index = carrier_to_index.get(carrier)
            if source_index is None:
                raise RuntimeError(f"CTPI_M2_CONFIRM_CARRIER:{world_id}")
            raw = q_raw[route, source_index]
            counts = np.rint(raw * 9.0 - 0.5).astype(np.int64)
            if np.max(np.abs(raw * 9.0 - 0.5 - counts)) > 1.0e-9:
                raise RuntimeError(f"CTPI_M2_CONFIRM_QRAW_NOT_COUNT:{world_id}")
            with (world_dir / "stop_events.csv").open(newline="", encoding="utf-8") as source:
                events = list(csv.DictReader(source))
            if len(events) != 15:
                raise RuntimeError(f"CTPI_M2_CONFIRM_EVENT_COUNT:{world_id}")
            for index, (count, event) in enumerate(zip(counts, events), 1):
                expected_action = f"{house}_route{route:02d}_stop{index:02d}"
                if event["action_id"] != expected_action:
                    raise RuntimeError(f"CTPI_M2_CONFIRM_ACTION_ID:{world_id}:{index}")
                records.append({
                    "world_id": world_id, "house": house,
                    "controlled_carrier_id": carrier, "route_index": route,
                    "stop_id": index, "action_id": expected_action,
                    "member_hit_count": int(count), "observed_event": int(event["observed_hit"]),
                    "world_audit_sha256": world_hashes[world_id],
                })

    if len(records) != 450:
        raise RuntimeError(f"CTPI_M2_CONFIRM_RECORD_COUNT:{len(records)}")
    k = np.asarray([row["member_hit_count"] for row in records], dtype=np.int64)
    y = np.asarray([row["observed_event"] for row in records], dtype=np.int8)
    for house in HOUSES:
        observed_hist = np.bincount(
            np.asarray([row["member_hit_count"] for row in records if row["house"] == house]),
            minlength=9,
        )
        expected_hist = np.asarray(selection["houses"][house]["sets"]["M2_CONFIRM"]["expected_k_histogram"])
        if not np.array_equal(observed_hist, expected_hist):
            raise RuntimeError(f"CTPI_M2_CONFIRM_K_HISTOGRAM:{house}")
    report = forecast.evaluate_source_intervention_gate(
        k, y,
        [row["world_id"] for row in records],
        [row["house"] for row in records],
        [row["controlled_carrier_id"] for row in records],
        [row["action_id"] for row in records],
        table_payload["fit"]["table"],
    )
    report.update({
        "table_sha256": sha256_file(args.table),
        "forecast_code_sha256": sha256_file(args.forecast_code),
        "world_manifest_sha256": sha256_file(args.world_manifest),
        "authorization_sha256": sha256_file(args.authorization),
        "world_audit_sha256": world_hashes,
        "confirm_opened_once": True,
        "formula_tuned_on_confirm": False,
    })
    args.output.mkdir(parents=True, exist_ok=False)
    csv_path = args.output / "CONFIRM_RECORDS.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(records[0]))
        writer.writeheader(); writer.writerows(records)
    report_path = args.output / "M2_CONFIRM_GATE_REPORT.json"
    report_path.write_bytes(canonical_bytes(report))
    (args.output / ("PASS" if report["pass"] else "NO_GO")).write_text(
        report["verdict"] + "\n", encoding="ascii"
    )
    print(report["verdict"])
    print(f"CTPI_M2_CONFIRM_REPORT_SHA256={sha256_file(report_path)}")
    return 0 if report["pass"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
