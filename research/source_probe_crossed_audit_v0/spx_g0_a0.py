#!/usr/bin/env python3
"""Read-only SPX-G0 asset audit and exact crossed re-extraction on the VM."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

CENTRAL_ROOT = Path("/home/zyc/cess_d1r_168x16_reference_20260925")
E2_ROOT = Path("/home/zyc/JTD_E2_K12_180_RUNS_20260925")
E2_OLD_ROOT = Path("/home/zyc/E2_CROSS_ENVIRONMENT_168_RUNS_20260925/OPEN_DISCOVERY")
E1_ROOT = Path("/home/zyc/JTD_E1_FRESH_TARGETS_20260925")
WIND_DIR = Path("/mnt/hgfs/workspace/GADEN_files/scenarios/House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind")
OCC = Path("/mnt/hgfs/workspace/GADEN_files/scenarios/House02/OccupancyGrid3D.csv")
EXPECTED_CENTRAL = "b21a089cb015ace71a448db58bd7a2f1fee25e9a8431cbb56728f48ca39573d9"
EXPECTED_PANEL = "5df11712dd0e7dbef6e454c8d146427407644b9f27245c447479185ab2129d8e"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def table(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def write_json(path: Path, value: object) -> None:
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def descriptor(path: Path, values: np.ndarray | None = None) -> dict:
    record = {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}
    if values is not None:
        record.update({"numeric_shape": list(values.shape), "numeric_dtype": str(values.dtype),
                       "finite": bool(np.isfinite(values).all())})
    return record


def read_occupancy(path: Path) -> tuple[dict, np.ndarray]:
    header = {}
    payload = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("#"):
                key, *numbers = line[1:].split()
                header[key] = [float(v) for v in numbers]
            elif line.strip() != ";":
                payload.extend(int(v) for v in line.split())
    nx, ny, nz = map(int, header["num_cells"])
    values = np.asarray(payload, dtype=np.int8)
    if values.size != nx * ny * nz:
        raise ValueError("occupancy payload count mismatch")
    return header, values.reshape(nz, nx, ny)


def probes(assets: Path, occ_header: dict) -> tuple[list[dict], list[dict], dict]:
    gate = json.loads((assets / "gate1a_contract.json").read_text(encoding="utf-8"))
    initial = json.loads((assets / "e2_initial_lock.json").read_text(encoding="utf-8"))
    p_g1a = gate["probe_points"]
    p_e2 = sorted((row for row in table(assets / "e1_probe_contracts.tsv") if row["house"] == "House02"),
                  key=lambda row: int(row["probe_rank"]))
    if len(p_g1a) != 30 or len(p_e2) != 30:
        raise ValueError("probe count mismatch")
    min_x, min_y, _ = occ_header["env_min(m)"]
    cell = occ_header["cell_size(m)"][0]
    for source in (p_g1a, p_e2):
        for row in source:
            x0, x1 = int(row["native_x0"]), int(row["native_x1_exclusive"])
            y0, y1 = int(row["native_y0"]), int(row["native_y1_exclusive"])
            if x1 - x0 != 2 or y1 - y0 != 2 or not (0 <= x0 < x1 <= 83 and 0 <= y0 < y1 <= 119):
                raise ValueError("probe footprint incompatible with House02 cube")
            center_x = min_x + (x0 + x1) * cell / 2
            center_y = min_y + (y0 + y1) * cell / 2
            declared_x = float(row["center_x_m"])
            declared_y = float(row["center_y_m"])
            if abs(center_x - declared_x) > 1e-6 or abs(center_y - declared_y) > 1e-6 or abs(float(row["z_m"]) - .2) > 1e-9:
                raise ValueError("probe xyz/voxel transform incompatible")
    if gate["iteration_indices"] != list(range(100, 551, 50)) or gate["probe_operator"]["kernel"] != 2:
        raise ValueError("Gate1A time/pooling contract drift")
    if sha(assets / "gate1a_contract.json") != "68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334":
        raise ValueError("Gate1A contract SHA drift")
    if sha(assets / "e1_probe_contracts.tsv") != initial["probe_contract_sha256"]:
        raise ValueError("E2 probe contract SHA drift")
    return p_g1a, p_e2, gate


def all_cube_records(assets: Path) -> tuple[list[dict], list[dict]]:
    panel = table(assets / "central_panel.tsv")
    central_manifest = table(assets / "central_manifest.tsv")
    if sha(assets / "central_panel.tsv") != EXPECTED_PANEL or len(panel) != 168 or len(central_manifest) != 2688:
        raise ValueError("central panel/manifest incompatible")
    central = []
    keys = set()
    for row in central_manifest:
        index = int(row["panel_index"])
        replicate = int(row["replicate"])
        if not (0 <= index < 168 and 1 <= replicate <= 16):
            raise ValueError("central index out of range")
        source = panel[index]
        if row["source_id"] != source["source_id"] or int(row["rng_seed"]) != 2026105000 + 16 * index + replicate:
            raise ValueError("central seed/source mismatch")
        key = index, replicate - 1
        if key in keys:
            raise ValueError("duplicate central cube")
        keys.add(key)
        path = CENTRAL_ROOT / source["source_id"] / f"rep_{replicate:02d}_seed_{row['rng_seed']}" / "spatial/concentration.npy"
        central.append({"panel": "CENTRAL", "source_index": index, "replicate_index": replicate - 1,
                        "source_id": source["source_id"], "path": path, "expected_sha256": row["concentration_sha256"]})
    if len(keys) != 2688:
        raise ValueError("incomplete central grid")
    ref = table(assets / "e2_reference_manifest.tsv")
    target = table(assets / "e2_target_manifest.tsv")
    source_rows = [row for row in table(assets / "e1_source_panels.tsv") if row["house"] == "House02"]
    if len(source_rows) != 6:
        raise ValueError("offstrip source count mismatch")
    offstrip = []
    keys = set()
    for source, manifest in (("REFERENCE", ref), ("TARGET", target)):
        for row in manifest:
            if row["house"] != "House02" or row["wind"] != "3,5-1_slow":
                continue
            index = int(row["source_index"])
            replica = int(row["reference_index"] if source == "REFERENCE" else row["new_index"]) + (0 if source == "REFERENCE" else 12)
            if not (0 <= index < 6 and 0 <= replica < 16):
                raise ValueError("offstrip index out of range")
            if row["source_id"] != source_rows[index]["source_id"]:
                raise ValueError("offstrip source order mismatch")
            key = index, replica
            if key in keys:
                raise ValueError("duplicate offstrip cube")
            keys.add(key)
            path = Path(row["run_dir"]) / "concentration.npy"
            allowed = (E2_OLD_ROOT, E1_ROOT, E2_ROOT)
            if not any(path.is_relative_to(root) for root in allowed):
                raise ValueError("offstrip path outside OPEN roots")
            offstrip.append({"panel": "OFFSTRIP", "source_index": index, "replicate_index": replica,
                             "source_id": row["source_id"], "path": path, "expected_sha256": row["cube_sha256"]})
    if len(keys) != 96:
        raise ValueError("incomplete offstrip 6x16 grid")
    return central, offstrip


def audit(assets: Path, out: Path) -> bool:
    report = {"stage": "SPX_G0_A0", "house": "House02", "wind": "3,5-1_slow",
              "new_plume_runs": 0, "sealed_data_read": False,
              "required_assets": {}, "cube_inventory": [], "errors": []}
    try:
        for filename in ("central_bank.npy", "central_manifest.tsv", "central_panel.tsv", "gate1a_contract.json",
                         "e1_probe_contracts.tsv", "e1_source_panels.tsv", "e2_initial_lock.json",
                         "e2_reference_manifest.tsv", "e2_target_manifest.tsv",
                         "e2_reference_tensor.npy", "e2_target_tensor.npy"):
            path = assets / filename
            if not path.is_file():
                raise FileNotFoundError(path)
            report["required_assets"][filename] = descriptor(path)
        historical_central = np.load(assets / "central_bank.npy", mmap_mode="r", allow_pickle=False)
        historical_ref = np.load(assets / "e2_reference_tensor.npy", mmap_mode="r", allow_pickle=False)
        historical_target = np.load(assets / "e2_target_tensor.npy", mmap_mode="r", allow_pickle=False)
        if historical_central.shape != (168, 16, 10, 30) or sha(assets / "central_bank.npy") != EXPECTED_CENTRAL:
            raise ValueError("historical CENTRAL tensor incompatible")
        if historical_ref.shape != (3, 6, 12, 10, 30) or historical_target.shape != (3, 6, 4, 10, 30):
            raise ValueError("historical OFFSTRIP tensor incompatible")
        for name, tensor in (("central_bank.npy", historical_central), ("e2_reference_tensor.npy", historical_ref),
                             ("e2_target_tensor.npy", historical_target)):
            report["required_assets"][name].update({"numeric_shape": list(tensor.shape), "numeric_dtype": str(tensor.dtype),
                                                       "finite": bool(np.isfinite(tensor).all())})
        initial = json.loads((assets / "e2_initial_lock.json").read_text(encoding="utf-8"))
        header, occ = read_occupancy(OCC)
        if sha(OCC) != initial["occupancy_sha256"]["House02"] or occ.shape != (26, 83, 119):
            raise ValueError("occupancy SHA/shape mismatch")
        report["required_assets"]["occupancy"] = {**descriptor(OCC, occ), "header": header,
                                                     "unique_values": np.unique(occ).tolist(),
                                                     "sufficient_for_cross_extraction": True}
        wind_expected = initial["winds"][1]["iteration_hashes"]
        winds = []
        for iteration in range(11):
            file = WIND_DIR / f"wind_iteration_{iteration}"
            raw = np.fromfile(file, dtype="<f8")
            if raw.size != 3 * occ.size or sha(file) != wind_expected[file.name]:
                raise ValueError(f"wind iteration {iteration} SHA/shape mismatch")
            values = raw.reshape(3, *occ.shape)
            entry = descriptor(file, values)
            entry["mean_vector_mps"] = [float(values[c].mean()) for c in range(3)]
            if not entry["finite"]:
                raise ValueError("nonfinite wind values")
            winds.append(entry)
        report["required_assets"]["wind_sequence"] = winds
        p_g1a, p_e2, gate = probes(assets, header)
        report["required_assets"]["probe_contracts"] = {"P_G1A_count": len(p_g1a), "P_E2_count": len(p_e2),
                                                           "time_indices": gate["iteration_indices"],
                                                           "pooling": "native 2x2 average", "z_m": .2,
                                                           "numeric_voxel_footprints_verified": True}
        central, offstrip = all_cube_records(assets)
        for item in central + offstrip:
            path = item["path"]
            if not path.is_file():
                raise FileNotFoundError(path)
            cube = np.load(path, mmap_mode="r", allow_pickle=False)
            entry = descriptor(path, cube)
            if entry["sha256"] != item["expected_sha256"] or cube.shape != (10, 83, 119) or not entry["finite"] or np.any(cube < 0):
                raise ValueError(f"raw cube invalid: {path}")
            report["cube_inventory"].append({"panel": item["panel"], "source_index": item["source_index"],
                                             "replicate_index": item["replicate_index"], "source_id": item["source_id"],
                                             **entry})
        report["counts"] = {"CENTRAL": len(central), "OFFSTRIP": len(offstrip), "wind_iterations": len(winds),
                            "probe_protocols": 2, "occupancy_voxels": int(occ.size)}
        report["deployment_context"] = [
            {"variable": "candidate/source geometry", "availability": "AVAILABLE if map known"},
            {"variable": "probe/sensor geometry", "availability": "AVAILABLE"},
            {"variable": "local onboard wind observations", "availability": "POTENTIALLY AVAILABLE"},
            {"variable": "full simulator wind field", "availability": "ORACLE without a real estimator"},
            {"variable": "occupancy/building geometry", "availability": "AVAILABLE only if mapped"},
            {"variable": "target-environment dense source stochastic bank", "availability": "NOT ALLOWED as deployment context"},
        ]
        report["asset_usability"] = "ASSET_READY_FOR_CROSSED_EXTRACTION"
    except Exception as exc:
        report["asset_usability"] = "SPX_G0_DATA_CONTRACT_STOP"
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "SPX_G0_ASSET_AUDIT.json", report)
    print(report["asset_usability"], report["counts"] if "counts" in report else report["errors"], flush=True)
    return report["asset_usability"] == "ASSET_READY_FOR_CROSSED_EXTRACTION"


def pooled(cube: np.ndarray, probe_rows: list[dict]) -> np.ndarray:
    out = np.empty((10, 30), dtype=np.float64)
    for i, row in enumerate(probe_rows):
        x0, x1 = int(row["native_x0"]), int(row["native_x1_exclusive"])
        y0, y1 = int(row["native_y0"]), int(row["native_y1_exclusive"])
        out[:, i] = cube[:, x0:x1, y0:y1].mean(axis=(1, 2))
    return out


def extract(assets: Path, out: Path) -> bool:
    audit_report = json.loads((out / "SPX_G0_ASSET_AUDIT.json").read_text(encoding="utf-8"))
    if audit_report["asset_usability"] != "ASSET_READY_FOR_CROSSED_EXTRACTION":
        print("SPX_G0_DATA_CONTRACT_STOP asset audit incomplete")
        return False
    header, _ = read_occupancy(OCC)
    pg, pe, _ = probes(assets, header)
    central, offstrip = all_cube_records(assets)
    tensors = {
        "CENTRAL_P_G1A": np.empty((168, 16, 10, 30), dtype=np.float64),
        "CENTRAL_P_E2": np.empty((168, 16, 10, 30), dtype=np.float64),
        "OFFSTRIP_P_G1A": np.empty((6, 16, 10, 30), dtype=np.float64),
        "OFFSTRIP_P_E2": np.empty((6, 16, 10, 30), dtype=np.float64),
    }
    for item in central + offstrip:
        cube = np.load(item["path"], allow_pickle=False)
        prefix = item["panel"]
        index, replica = item["source_index"], item["replicate_index"]
        tensors[f"{prefix}_P_G1A"][index, replica] = pooled(cube, pg)
        tensors[f"{prefix}_P_E2"][index, replica] = pooled(cube, pe)
    historical_central = np.load(assets / "central_bank.npy", allow_pickle=False)
    historical_ref = np.load(assets / "e2_reference_tensor.npy", allow_pickle=False)[1]
    historical_target = np.load(assets / "e2_target_tensor.npy", allow_pickle=False)[1]
    historical_e2 = np.concatenate((historical_ref, historical_target), axis=1)
    delta_c = float(np.max(np.abs(tensors["CENTRAL_P_G1A"] - historical_central)))
    delta_e = float(np.max(np.abs(tensors["OFFSTRIP_P_E2"].astype(np.float32) - historical_e2)))
    report = {"stage": "SPX_G0_A0_CROSSED_EXTRACTION", "asset_audit_sha256": sha(out / "SPX_G0_ASSET_AUDIT.json"),
              "historical_reproduction": {"CENTRAL_P_G1A_max_abs": delta_c,
                                           "OFFSTRIP_P_E2_max_abs_after_float32_serialization": delta_e,
                                           "CENTRAL_values": int(historical_central.size),
                                           "OFFSTRIP_values": int(historical_e2.size)},
              "crossed_tensors": {}, "new_plume_runs": 0, "sealed_data_read": False}
    if delta_c > 1e-12 or delta_e > 1e-12:
        report["decision"] = "SPX_G0_DATA_CONTRACT_STOP"
        write_json(out / "SPX_G0_A0_COMPATIBILITY.json", report)
        print("SPX_G0_DATA_CONTRACT_STOP historical reproduction mismatch", delta_c, delta_e)
        return False
    for name, values in tensors.items():
        path = out / f"SPX_G0_{name}_10x30.npy"
        np.save(path, values)
        report["crossed_tensors"][name] = descriptor(path, values)
    report["decision"] = "SPX_G0_A0_COMPATIBLE"
    write_json(out / "SPX_G0_A0_COMPATIBILITY.json", report)
    print("SPX_G0_A0_COMPATIBLE", delta_c, delta_e, flush=True)
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["audit", "extract"])
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    assets, out = args.assets.resolve(), args.out.resolve()
    ready = audit(assets, out) if args.phase == "audit" else extract(assets, out)
    if not ready:
        raise SystemExit(30)


if __name__ == "__main__":
    main()
