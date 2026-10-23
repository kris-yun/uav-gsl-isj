"""Source-blind readout audit of the actual, limited 20 s S2 CH4 archive.

The released, hash-pinned reader is the environment backend. Only current
position/time observations reach the exported history. No private source labels,
new simulation, warmed-stack qualification or localization gain is implied.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


READER_SHA256 = "8541825d24ed43450bbdf88a7430811eac00e2f7facb0a5c70d70214a9cc01e0"


def inspect_s2_t0(release_root: str | Path, out: str | Path) -> dict:
    root, out = Path(release_root), Path(out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("Refuse to overwrite an S2 qualification receipt")
    metadata_path = root / "DATASET.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    if metadata.get("version") != "FSR_S2_CH4_T0_20S_V1":
        raise ValueError("Different S2 lineage requires its own reader qualification")
    if metadata.get("formal_scientific_release_admitted") or metadata.get("warm_stack") or metadata.get("thermal_lake_breeze"):
        raise ValueError("Unexpected metadata claim: this adapter is limited T0 only")
    reader_path = root / "code/ch4_world.py"
    reader_sha = hashlib.sha256(reader_path.read_bytes()).hexdigest()
    if reader_sha != READER_SHA256:
        raise ValueError("Released reader changed; re-audit before execution")
    spec = importlib.util.spec_from_file_location("audited_s2_ch4_reader", reader_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    exported = []; checks = []
    permitted = {"valid", "reason", "time_s", "coordinate_ENU_m", "excess_CH4_ppm", "wind_m_s", "reference_T_K", "reference_P_Pa", "sensor", "thermal_lake_breeze", "warm_stack"}
    # Same pre-existing, qualified geometric query location as the original
    # package's verifier. Coordinates are not chosen from localization results.
    for role in ("DAY", "NIGHT"):
        world = module.CH4World(root, role)
        world.step(2.0)
        for step in range(3):
            position = [3441 + .05 * step, 4745, 35]
            observation = world.observe(position)
            if not observation.get("valid") or set(observation) - permitted:
                raise ValueError("Invalid query or unexpected privileged output")
            exported.append({"role": role, "observation": observation})
            world.step(.1)
        invalid = world.observe([0, 0, 0])
        if invalid["valid"] or invalid.get("excess_CH4_ppm") is not None:
            raise ValueError("Invalid-domain query was silently converted to gas zero")
        rejected = False
        try:
            world.observe([3441, 4745, 35], time_s=20.1)
        except ValueError:
            rejected = True
        if not rejected:
            raise ValueError("Reader accepted an unqualified future time")
        checks.append({"role": role, "actual_local_observations": 3, "invalid_distinct_from_zero": True, "outside_qualified_time_rejected": True})
    null = module.CH4World(root, "NULL_DAY")
    null_observation = null.observe([3441, 4745, 35], time_s=2.0)
    if not null_observation["valid"] or null_observation["excess_CH4_ppm"] != 0:
        raise ValueError("Frozen zero-release control failed")
    out.mkdir(parents=True, exist_ok=True)
    history = {"scope": "S2_T0_ACTUAL_READOUT_INTERFACE_ONLY", "time_is_physical_seconds": True, "observations": exported}
    (out / "local_history.json").write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n")
    receipt = {
        "status": "PASS_ACTUAL_S2_LOCAL_QUERY_INTERFACE", "role_checks": checks,
        "release_root": str(root.resolve()), "reader_sha256": reader_sha,
        "dataset_manifest_sha256": hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
        "null_control_passed": True, "private_labels_opened": False,
        "whole_field_exposed_to_student": False, "new_physical_simulation": False,
        "student_predictions_evaluated": False, "training_performed": False,
        "scientific_localization_gain_claim": False,
        "physical_scope": "single source; DAY/NIGHT static diagnostic wind; 20 s T0; ideal CH4 point readout",
        "thermal_lake_breeze": False, "warm_stack": False,
        "scientific_admission": "HOLD_FOR_WARM_AND_MULTISOURCE_LAKESHORE_BENCHMARK",
    }
    (out / "QUALIFICATION_RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_s2_t0(args.release_root, args.out), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
