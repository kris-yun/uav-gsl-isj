"""Normalize the fixed 12 realizations from physical metadata, without gas outcomes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/ctpi_cstar"))
from provenance_physical_binding import derive_claims


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path, required=True)
    args = p.parse_args()
    evid = args.evidence.resolve()
    metadata_path = evid / "metadata/METADATA_INSPECTION.json"
    wind_path = evid / "WIND_INPUT_IDENTITY.json"
    metadata = json.loads(metadata_path.read_text())
    wind = {r["realization_id"]: r for r in json.loads(wind_path.read_text())["entries"]}
    env_root = ROOT / "evidence/cstar_environment_20260906"
    env_path = env_root / "CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1.json"
    env = json.loads(env_path.read_text())
    split = ROOT / "experiments/ctpi_cstar/CSTAR_RAW_REALIZATION_SPLITS_FROZEN_20260906.json"
    rows = []
    for record in metadata["entries"]:
        rid = record["realization_id"]
        generator = next(f for f in record["generator_files"] if f["original_path"].endswith("GADEN_ros2.launch"))
        claims = derive_claims(generator["archive_path"], record["resolved_realization_path"], wind[rid]["files"])
        row = {"realization_id": rid, "house": record["house"], "config_id": record["config_id"],
            "geometry_identity": env["houses"][record["house"]]["geometry_identity"],
            "simulation_dir_path": record["resolved_realization_path"],
            **{k: claims[k] for k in ("source_xyz_m", "gas_type_id", "release_fingerprint", "transport_fingerprint", "sensor_mechanism_fingerprint")},
            "source_authority": "generator_config",
            "physical_binding": {"generator_evidence_index": 0, "wind_evidence_index": 1,
                                 "header_sha256": record["simulation_header"]["header_sha256"]},
            "provenance_evidence": [
                {"kind": "generator_config", "path": generator["archive_path"], "sha256": generator["sha256"],
                 "required_literals": [record["config_id"], "source_location_x", "gas_type", "num_filaments_sec", "wind_data"]},
                {"kind": "transport_config", "path": str(wind_path), "sha256": sha(wind_path), "required_literals": [rid]},
                {"kind": "simulation_metadata", "path": str(metadata_path), "sha256": sha(metadata_path),
                 "required_literals": [rid, record["simulation_header"]["header_sha256"]]}]}
        rows.append(row)
    manifest = {"contract": "CSTAR_RAW_REALIZATION_PROVENANCE_V1",
        "created_git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=ROOT).strip(),
        "environment_alignment_audit_path": str(env_path), "environment_alignment_audit_sha256": sha(env_path),
        "prerequisite_inventory_path": str(env_root / "CONTROLLED_PREREQUISITE_INVENTORY.json"),
        "prerequisite_inventory_sha256": sha(env_root / "CONTROLLED_PREREQUISITE_INVENTORY.json"),
        "frozen_split_manifest_path": str(split), "frozen_split_manifest_sha256": sha(split), "entries": rows,
        "scope": "raw-field generator-mechanism provenance, not matched random release draws or scientific module utility",
        "historical_exposure_note": "Inventory payload_read=false describes directory listing only. Historical closed-loop runs and environment probes read some of these realizations before this split. No virgin-confirmation claim.",
        "gas_body_reads_this_qualification": 0, "training_started": False, "route_extraction_started": False}
    path = evid / "CSTAR_RAW_REALIZATION_PROVENANCE_V1.json"
    path.write_text(json.dumps(manifest, indent=2)+"\n")
    proc = subprocess.run([sys.executable, str(ROOT / "experiments/ctpi_cstar/audit_raw_realization_provenance.py"),
        "--manifest", str(path), "--output", str(evid / "CSTAR_RAW_REALIZATION_PROVENANCE_AUDIT_V1.json")])
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
