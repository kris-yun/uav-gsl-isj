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
        (r / "sim_a").mkdir(); (r / "sim_b").mkdir()
        (r / "a.txt").write_text("source=-1,2,0.3 gas=10 release=R1 transport=Tfast\n")
        (r / "b.txt").write_text("source=-1,2,0.3 gas=10 release=R1 transport=Tslow\n")
        inv = {"contract": "CSTAR_CONTROLLED_PREREQUISITE_INVENTORY_V1", "entries": [
            {"house": "House01", "config": "fast", "resolved_realization_path": str(r / "sim_a"), "payload_read": False},
            {"house": "House01", "config": "slow", "resolved_realization_path": str(r / "sim_b"), "payload_read": False}]}
        write_json(r / "inv.json", inv)
        env = {"contract": "CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1", "pass": True,
               "houses": {"H01": {"pass": True, "geometry_identity": "G1"}}}
        write_json(r / "env.json", env)
        split = {"contract": "CSTAR_RAW_REALIZATION_SPLITS_V1", "status": "FROZEN_BEFORE_PAYLOAD_READ",
                 "frozen_from_inventory_sha256": sha(r / "inv.json"), "records": [
                     {"realization_id": "a", "house": "H01", "config_id": "fast", "resolved_realization_path": str(r / "sim_a")},
                     {"realization_id": "b", "house": "H01", "config_id": "slow", "resolved_realization_path": str(r / "sim_b")} ]}
        write_json(r / "split.json", split)
        def entry(rid, cfg, sim, ev, transport):
            return {"realization_id": rid, "house": "H01", "geometry_identity": "G1", "config_id": cfg,
                    "simulation_dir_path": str(sim), "source_xyz_m": [-1, 2, 0.3], "gas_type_id": "10",
                    "source_authority": "generator_config", "release_fingerprint": "R1",
                    "transport_fingerprint": transport, "sensor_mechanism_fingerprint": "S1",
                    "provenance_evidence": [{"kind": "generator_config", "path": ev.name, "sha256": sha(ev),
                    "required_literals": ["source=-1,2,0.3", "gas=10", "release=R1", f"transport={transport}"]}]}
        prov = {"contract": "CSTAR_RAW_REALIZATION_PROVENANCE_V1", "created_git_sha": "test",
                "prerequisite_inventory_path": "inv.json", "prerequisite_inventory_sha256": sha(r / "inv.json"),
                "environment_alignment_audit_path": "env.json", "environment_alignment_audit_sha256": sha(r / "env.json"),
                "frozen_split_manifest_path": "split.json", "frozen_split_manifest_sha256": sha(r / "split.json"),
                "entries": [entry("a", "fast", r / "sim_a", r / "a.txt", "Tfast"),
                            entry("b", "slow", r / "sim_b", r / "b.txt", "Tslow")]}
        write_json(r / "prov.json", prov)
        p = subprocess.run([sys.executable, str(AUDITOR), "--manifest", str(r / "prov.json"), "--output", str(r / "out.json")])
        assert p.returncode == 0
        out = json.loads((r / "out.json").read_text())
        assert out["qualified_m1_transport_pair_count"] == 1
        assert out["qualified_m2_route_case_count"] == 0
        prov["entries"][0]["source_authority"] = "directory_name_only"
        write_json(r / "bad.json", prov)
        q = subprocess.run([sys.executable, str(AUDITOR), "--manifest", str(r / "bad.json"), "--output", str(r / "bad_out.json")])
        assert q.returncode != 0 or json.loads((r / "bad_out.json").read_text())["pass"] is False
    print("CSTAR_RAW_REALIZATION_PROVENANCE_SELFTEST PASS")

if __name__ == "__main__":
    main()
