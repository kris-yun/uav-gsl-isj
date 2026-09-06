"""Read generator XML and at most 136 decoded legacy header bytes, never gas records.

The header parser reports raw fields provisionally; it does not qualify provenance.
No filament/concentration body is decompressed or interpreted. No wind values,
routes or outcomes are inspected. Exact original XML/header bytes are archived.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET
import zlib

ROOT = Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def header_only(path):
    decoder = zlib.decompressobj()
    raw, compressed = b"", b""
    with path.open("rb") as f:
        while len(raw) < 136:
            chunk = f.read(16)
            if not chunk:
                break
            compressed += chunk
            raw += decoder.decompress(chunk, 136-len(raw))
            if len(compressed) > 4096:
                raise RuntimeError("HEADER_COMPRESSED_BOUND_EXCEEDED")
    info = {"path": str(path), "compressed_prefix_bytes_read": len(compressed),
            "decoded_header_bytes": len(raw), "compressed_prefix_sha256": sha(compressed),
            "header_sha256": sha(raw), "gas_body_decoded": False}
    if len(raw) == 136 and struct.unpack_from("<i", raw)[0] == 1:
        info.update(version=1,
            environment_slots_native_double=list(struct.unpack_from("<6d", raw, 4)),
            environment_slots_float_prefix=[struct.unpack_from("<f", raw, 4+8*i)[0] for i in range(6)],
            dimensions=list(struct.unpack_from("<3i", raw, 52)),
            cell_size=struct.unpack_from("<d", raw, 64)[0],
            five_metadata_slots_native_double=list(struct.unpack_from("<5d", raw, 72)),
            five_metadata_slots_float_prefix=[struct.unpack_from("<f", raw, 72+8*i)[0] for i in range(5)],
            gas_type_id=struct.unpack_from("<i", raw, 112)[0],
            initial_wind_index=struct.unpack_from("<i", raw, 132)[0])
    return info, raw, compressed


def parse_launch(raw, root):
    xml = ET.fromstring(raw)
    args = {e.attrib["name"]: e.attrib.get("default", "") for e in xml.findall("arg")}
    node = next(e for e in xml.findall("node") if e.attrib.get("pkg") == "gaden_filament_simulator")
    params = {}
    for e in node.findall("param"):
        value = e.attrib["value"]
        value = value.replace("$(find-pkg-share vgr_dataset)", str(root))
        value = re.sub(r"\$\(var ([^)]+)\)", lambda m: args[m[1]], value)
        value = value.replace("$(find vgr_dataset)", str(root))
        value = re.sub(r"\$\(arg ([^)]+)\)", lambda m: args[m[1]], value)
        params[e.attrib["name"]] = value
    return {"args": args, "simulator_params": params}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    split = ROOT / "experiments/ctpi_cstar/CSTAR_RAW_REALIZATION_SPLITS_FROZEN_20260906.json"
    rows = json.loads(split.read_text())["records"]
    result = []
    for row in rows:
        sim = Path(row["resolved_realization_path"])
        scenario = sim.parents[2]
        dataset = scenario.parents[1]
        target = args.out / row["realization_id"]
        target.mkdir()
        rec = {**row, "generator_files": [], "errors": []}
        for name in ("GADEN_ros1.launch", "GADEN_ros2.launch", "GADEN_preprocessing_ros2.launch"):
            path = scenario / "launch" / row["config_id"] / name
            if path.is_file():
                raw = path.read_bytes()
                (target / name).write_bytes(raw)
                ev = {"original_path": str(path), "archive_path": str(target / name), "sha256": sha(raw)}
                if "preprocessing" not in name:
                    try:
                        ev["parsed"] = parse_launch(raw, dataset)
                    except Exception as exc:
                        ev["parse_error"] = str(exc)
                rec["generator_files"].append(ev)
            else:
                rec["errors"].append(f"MISSING:{path}")
        try:
            info, raw, compressed = header_only(sim / "iteration_0")
            (target / "iteration_0.header.bin").write_bytes(raw)
            (target / "iteration_0.compressed_prefix.bin").write_bytes(compressed)
            rec["simulation_header"] = info
        except Exception as exc:
            rec["errors"].append(f"HEADER_UNVERIFIED:{exc}")
        result.append(rec)
    report = {"scope": "existing generator XML and bounded header metadata only; no scientific qualification",
              "frozen_split_sha256": sha(split.read_bytes()), "entries": result,
              "gas_body_reads": 0, "route_extraction_started": False}
    (args.out / "METADATA_INSPECTION.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    for rec in result:
        print(json.dumps({"id": rec["realization_id"], "house": rec["house"], "config": rec["config_id"],
            "header": rec.get("simulation_header"), "errors": rec["errors"]}))


if __name__ == "__main__":
    main()
