"""Whitelist configuration metadata over SSH; never read gas/wind payloads.

Existing configurations are evidence of declared settings, not cryptographic
proof that historical snapshots were generated from these bytes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

PARAMS = {"sim_time", "time_step", "num_filaments_sec", "variable_rate",
          "wind_time_step", "allow_looping", "loop_from_step", "loop_to_step",
          "results_time_step", "results_min_time"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--r4-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    entries = {}
    for house, scenario in (("H01", "House01"), ("H02", "House02"), ("H03", "House03")):
        manifest = args.r4_root / f"{house}_seed12_A0" / "formal_runtime_manifest.json"
        raw = manifest.read_bytes()
        identity = json.loads(raw)
        config = identity["config_id"]
        if not re.fullmatch(r"[0-9,]+-[0-9,]+_(fast|slow)", config):
            raise ValueError("unsafe or unexpected config ID")
        remote = f"/mnt/hgfs/workspace/GADEN_files/scenarios/{scenario}/launch/{config}/GADEN_ros2.launch"
        result = subprocess.run(["ssh", "-i", "C:/Users/50176/.ssh/id_ed25519_vm",
                                 "zyc@192.168.111.128", f"cat -- '{remote}'"],
                                check=True, capture_output=True, timeout=30)
        root = ET.fromstring(result.stdout)
        selected = {}
        for param in root.iter("param"):
            name = param.get("name")
            if name in PARAMS:
                if name in selected:
                    raise ValueError(f"ambiguous repeated parameter: {name}")
                selected[name] = param.get("value")
        if set(selected) != PARAMS:
            raise ValueError(f"missing metadata: {PARAMS - set(selected)}")
        entries[house] = {
            "config_id": config, "config_path": remote,
            "config_sha256": hashlib.sha256(result.stdout).hexdigest(),
            "runtime_manifest_sha256": hashlib.sha256(raw).hexdigest(),
            "declared_parameters": selected,
            "native_to_sensor_time_ratio_if_config_bound": float(selected["results_time_step"]) / .2,
            "config_to_snapshot_generation_binding": "UNVERIFIED",
        }
    report = {"status": "DECLARED_GENERATION_METADATA_ONLY", "houses": entries,
              "limitations": ["No snapshot payloads or protected banks read.",
                              "No source coordinates or concentration observations exported.",
                              "Current launch files are not proof of historical generation identity.",
                              "Wind looping is not evidence that the gas state is periodic.",
                              "variable_rate=true is a declaration, not a verified stochastic release law."],
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(json.dumps({h: e["declared_parameters"] for h, e in entries.items()}))


if __name__ == "__main__":
    main()
