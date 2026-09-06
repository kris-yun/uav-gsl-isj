from __future__ import annotations
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDITOR = HERE / "audit_raw_realization_provenance.py"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_json(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, sort_keys=True) + "\n", encoding="utf-8")


def main():
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        specs = [
            ("a", "s1_fast", [-1, 2, 0.3], "Tfast"),
            ("b", "s1_slow", [-1, 2, 0.3], "Tslow"),
            ("c", "s2_fast", [2, -1, 0.3], "Tfast"),
            ("d", "s2_slow", [2, -1, 0.3], "Tslow"),
        ]
        inv_entries = []; split_records = []; entries = []
        for rid, cfg, xyz, transport in specs:
            sim = r / f"sim_{rid}"; sim.mkdir()
            ev = r / f"{rid}.txt"
            src = ','.join(str(x) for x in xyz)
            ev.write_text(f"source={src} gas=10 release=R1 transport={transport}\n")
            inv_entries.append({"house": "House01", "config": cfg,
                                "resolved_realization_path": str(sim), "payload_read": False})
            split_records.append({"realization_id": rid, "house": "H01", "config_id": cfg,
                                  "resolved_realization_path": str(sim)})
            entries.append({"realization_id": rid, "house": "H01", "geometry_identity": "G1",
                            "config_id": cfg, "simulation_dir_path": str(sim),
                            "source_xyz_m": xyz, "gas_type_id": "10",
                            "source_authority": "generator_config", "release_fingerprint": "R1",
                            "transport_fingerprint": transport, "sensor_mechanism_fingerprint": "S1",
                            "provenance_evidence": [{"kind": "generator_config", "path": ev.name,
                                "sha256": sha(ev), "required_literals": [f"source={src}", "gas=10",
                                "release=R1", f"transport={transport}"]}]})
        inv = {"contract": "CSTAR_CONTROLLED_PREREQUISITE_INVENTORY_V1", "entries": inv_entries}
        write_json(r / "inv.json", inv)
        env = {"contract": "CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1", "pass": True,
               "houses": {"H01": {"pass": True, "geometry_identity": "G1"}}}
        write_json(r / "env.json", env)
        split = {"contract": "CSTAR_RAW_REALIZATION_SPLITS_V1",
                 "status": "FROZEN_BEFORE_PAYLOAD_READ",
                 "frozen_from_inventory_sha256": sha(r / "inv.json"), "records": split_records}
        write_json(r / "split.json", split)
        prov = {"contract": "CSTAR_RAW_REALIZATION_PROVENANCE_V1", "created_git_sha": "test",
                "prerequisite_inventory_path": "inv.json", "prerequisite_inventory_sha256": sha(r / "inv.json"),
                "environment_alignment_audit_path": "env.json", "environment_alignment_audit_sha256": sha(r / "env.json"),
                "frozen_split_manifest_path": "split.json", "frozen_split_manifest_sha256": sha(r / "split.json"),
                "entries": entries}
        write_json(r / "prov.json", prov)
        p = subprocess.run([sys.executable, str(AUDITOR), "--manifest", str(r / "prov.json"),
                            "--output", str(r / "out.json")])
        assert p.returncode == 0
        out = json.loads((r / "out.json").read_text())
        assert out["qualified_m1_transport_pair_count"] == 2
        assert out["source_groups_per_house"] == {"H01": 2}
        assert out["qualified_groups_per_house"] == {"H01": 2}
        assert out["qualified_m2_route_case_count"] == 0
        prov["entries"][0]["source_authority"] = "directory_name_only"
        write_json(r / "bad.json", prov)
        q = subprocess.run([sys.executable, str(AUDITOR), "--manifest", str(r / "bad.json"),
                            "--output", str(r / "bad_out.json")])
        assert q.returncode != 0 or json.loads((r / "bad_out.json").read_text())["pass"] is False
    print("CSTAR_RAW_REALIZATION_PROVENANCE_SELFTEST PASS")

if __name__ == "__main__":
    main()
