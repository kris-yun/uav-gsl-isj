"""Assemble verified three-House input evidence and inspect raw asset names only."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/ctpi_cstar"))
from validate_environment_alignment_v2 import sha256_file as sha, require


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path, required=True)
    args = p.parse_args()
    out = args.evidence.resolve()
    houses = json.loads((out / "maps_v1/geometry_manifest.json").read_text())
    contract = json.loads((ROOT / "experiments/ctpi_cstar/CSTAR_ENVIRONMENT_ALIGNMENT_CONTRACT_V1.json").read_text())
    git_shas, crosschecks = set(), {}
    for h, row in houses.items():
        d = out / "probes_v1" / h
        audit = d / "runtime_audit.json"
        a = json.loads(audit.read_text())
        require(a["pass"] is True, f"RUNTIME_NOT_PASS:{h}")
        git_shas.add(a["git_sha"])
        wind = d / "wind_observation_positions.csv"
        row["free_space_probe_csvs"].append({"kind": "wind_observation", "path": str(wind), "sha256": sha(wind)})
        row.update(runtime_load_audit_path=str(audit), runtime_load_audit_sha256=sha(audit))
        # Independently compare producer's pre-ROS downwind vector and pose
        # to the received/decoded stamped stream (trace writes 6 decimals).
        with wind.open() as f:
            observed = list(csv.DictReader(f))
        with (d / "bridge_wind.csv").open() as f:
            truthblind_bridge = list(csv.DictReader(f))
        require(len(observed) == len(truthblind_bridge) == 8, f"BRIDGE_COUNT:{h}")
        worst = 0.0
        for got, sent in zip(observed, truthblind_bridge):
            require(int(got["stamp_ns"]) == round(float(sent["t_sim_s"])*1e9), f"BRIDGE_STAMP:{h}")
            for key in ("x", "y", "wind_u", "wind_v"):
                error = abs(float(got[key])-float(sent[key]))
                require(error <= 1e-6, f"BRIDGE_VECTOR_OR_POSE:{h}:{key}:{error}")
                worst = max(worst, error)
            require(abs(float(sent["z"])-row["navigation_height_m"]) <= 1e-8, f"BRIDGE_HEIGHT:{h}")
        crosschecks[h] = {"pass": True, "rows": 8, "max_trace_rounding_difference": worst,
            "bridge_wind_sha256": sha(d / "bridge_wind.csv"), "received_wind_sha256": sha(wind),
            "navigation_height_m": row["navigation_height_m"]}
    require(len(git_shas) == 1, "RUNTIME_CODE_NOT_SHARED")
    code = {}
    for stem, filename in [("ingress", "ctpi_v2_ingress.py"), ("wind_adapter", "cstar_local_wind.py")]:
        path = ROOT / "closed_loop/ctpi" / filename
        code[stem+"_code_path"], code[stem+"_code_sha256"] = str(path), sha(path)
    shared = hashlib.sha256(json.dumps({"houses": houses, "code": code,
        "common": contract["common_runtime_contract"]}, sort_keys=True).encode()).hexdigest()
    manifest = {"contract": "CSTAR_ENVIRONMENT_ALIGNMENT_V1", "git_sha": next(iter(git_shas)),
        "repo_root": str(ROOT), "common_runtime_contract": contract["common_runtime_contract"],
        "runtime_code_identity": code, "houses": houses,
        "shared_arm_input_identity": {arm: shared for arm in ("A0", "F00", "F10", "F11")},
        "shared_arm_identity_scope": "binding contract for future arms, NOT four-arm execution evidence"}
    path = out / "CSTAR_ENVIRONMENT_ALIGNMENT_V1.json"
    path.write_text(json.dumps(manifest, indent=2)+"\n")
    (out / "BRIDGE_TO_INGRESS_CROSSCHECK.json").write_text(json.dumps(crosschecks, indent=2)+"\n")
    subprocess.run([sys.executable, str(ROOT / "experiments/ctpi_cstar/validate_environment_alignment.py"),
        "--manifest", str(path), "--output", str(out / "CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1.json")], check=True)


if __name__ == "__main__":
    main()
