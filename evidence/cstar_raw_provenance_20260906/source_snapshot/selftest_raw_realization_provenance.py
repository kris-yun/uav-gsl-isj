"""Synthetic regressions only, never House scientific evidence."""
import hashlib, json, struct, subprocess, sys, tempfile, zlib
from pathlib import Path
import xml.etree.ElementTree as ET
from provenance_physical_binding import RELEASE_FIELDS, TRANSPORT_FIELDS, derive_claims
from cstar_inspect_wind_provenance import wind_identity

HERE = Path(__file__).resolve().parent

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, obj):
    p.write_text(json.dumps(obj, sort_keys=True)+"\n")

def main():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        inv, records, entries, winds, env = [], [], [], [], {}
        wp = root / "wind.json"
        for house in ("H01", "H02", "H03"):
            scenario = root / "dataset/scenarios" / ("House"+house[1:])
            scenario.mkdir(parents=True)
            occ = scenario / "OccupancyGrid3D.csv"
            occ.write_text("#env_min(m) 0 0 0\n#env_max(m) 1 1 1\n#num_cells 1 1 1\n#cell_size(m) 1\n0\n")
            geom = f"{house}:occupancy-{sha(occ)}:z0.3:full-slice"
            env[house] = {"pass": True, "geometry_identity": geom}
            for source in (0, 1):
                xyz = [0.1+source*0.5, 0.2, 0.3]
                for speed in (1, 2):
                    rid = f"{house}_{source}_{speed}"
                    sim = scenario / "gas_simulations" / rid / "simulation"
                    (sim / "wind").mkdir(parents=True)
                    wf = sim / "wind/wind_iteration_0"
                    wf.write_bytes(struct.pack("<3d", speed, 0, 0))
                    windfiles = [wind_identity(wf, 1)]
                    winds.append({"realization_id": rid, "files": windfiles, "errors": []})
                    raw = bytearray(136)
                    struct.pack_into("<i6d3i3d3di2di", raw, 0, 1, 0, 0, 0, 1, 1, 1,
                                     1, 1, 1, 1, 1, 1, *xyz, 10, 1, 1, 0)
                    (sim / "iteration_0").write_bytes(zlib.compress(bytes(raw)+b"BODY_MUST_NOT_BE_DECODED"))
                    xml = ET.Element("launch")
                    node = ET.SubElement(xml, "node", pkg="gaden_filament_simulator")
                    params = {k: "1.0" for k in RELEASE_FIELDS+TRANSPORT_FIELDS}
                    params.update(variable_rate="true", writeConcentrations="false", allow_looping="true",
                                  results_location=str(sim), gas_type="10")
                    params.update({"source_position_"+a: str(v) for a, v in zip("xyz", xyz)})
                    for k, v in params.items():
                        ET.SubElement(node, "param", name=k, value=v)
                    generator = sim.parent / "generator.launch"
                    generator.write_bytes(ET.tostring(xml))
                    claims = derive_claims(generator, sim, windfiles)
                    records.append({"realization_id": rid, "house": house, "config_id": rid, "resolved_realization_path": str(sim)})
                    inv.append({"house": "House"+house[1:], "config": rid, "resolved_realization_path": str(sim), "payload_read": False})
                    entries.append({"realization_id": rid, "house": house, "config_id": rid,
                        "simulation_dir_path": str(sim), "geometry_identity": geom,
                        **{k: claims[k] for k in ("source_xyz_m", "gas_type_id", "release_fingerprint", "transport_fingerprint", "sensor_mechanism_fingerprint")},
                        "source_authority": "generator_config", "physical_binding": {"generator_evidence_index": 0,
                            "wind_evidence_index": 1, "header_sha256": hashlib.sha256(raw).hexdigest()},
                        "provenance_evidence": [{"kind": "generator_config", "path": str(generator), "sha256": sha(generator),
                            "required_literals": ["source_position_x"]}, {"kind": "transport_config", "path": str(wp), "required_literals": [rid]}]})
        write(wp, {"entries": winds})
        for e in entries:
            e["provenance_evidence"][1]["sha256"] = sha(wp)
        write(root / "inv.json", {"contract": "CSTAR_CONTROLLED_PREREQUISITE_INVENTORY_V1", "entries": inv})
        write(root / "env.json", {"contract": "CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1", "pass": True, "houses": env})
        split = {"contract": "CSTAR_RAW_REALIZATION_SPLITS_V1", "status": "FROZEN_BEFORE_PAYLOAD_READ",
            "frozen_from_inventory_sha256": sha(root / "inv.json"), "records": records,
            "outer_folds": {h: {"heldout_realization_ids": [r["realization_id"] for r in records if r["house"] == h],
                "train_realization_ids": [r["realization_id"] for r in records if r["house"] != h]} for h in env}}
        write(root / "split.json", split)
        manifest = {"contract": "CSTAR_RAW_REALIZATION_PROVENANCE_V1", "created_git_sha": "synthetic", "entries": entries}
        for label, name in (("prerequisite_inventory", "inv"), ("environment_alignment_audit", "env"), ("frozen_split_manifest", "split")):
            manifest[label+"_path"] = name+".json"
            manifest[label+"_sha256"] = sha(root / (name+".json"))
        def run(data, name, expected):
            path, output = root / (name+".json"), root / (name+"_out.json")
            write(path, data)
            p = subprocess.run([sys.executable, str(HERE / "audit_raw_realization_provenance.py"), "--manifest", str(path), "--output", str(output)], capture_output=True, text=True)
            assert (p.returncode == 0) == expected, (name, p.stdout, p.stderr)
            return json.loads(output.read_text()) if output.exists() else None
        good = run(manifest, "valid", True)
        assert good["entry_provenance_pass_count"] == 12 and good["qualified_m1_transport_pair_count"] == 6
        assert good["qualified_m2_route_case_count"] == 0
        for key, value in (("source_authority", "directory_name_only"), ("transport_fingerprint", "fake"),
                           ("sensor_mechanism_fingerprint", "fake"), ("physical_binding", {})):
            bad = json.loads(json.dumps(manifest))
            bad["entries"][0][key] = value
            out = run(bad, "bad_"+key, False)
            assert out["blocked_entries"] and not out["raw_realizations_eligible_for_future_truth_blind_route_extraction"]
        split["outer_folds"]["H01"]["train_realization_ids"].append(records[0]["realization_id"])
        write(root / "split.json", split)
        manifest["frozen_split_manifest_sha256"] = sha(root / "split.json")
        run(manifest, "leaky_fold", False)
        split["records"] = records[:4]
        write(root / "split.json", split)
        manifest["frozen_split_manifest_sha256"] = sha(root / "split.json")
        run(manifest, "one_house", False)
    print("CSTAR_RAW_REALIZATION_PROVENANCE_SELFTEST PASS")

if __name__ == "__main__":
    main()
