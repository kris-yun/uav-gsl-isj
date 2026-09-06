"""Fingerprint frozen transport inputs only; no gas records or route outcomes.

Decode documented legacy component-major doubles / modern interleaved float32,
then hash float32 vectors as consumed by the archived GADEN decoder. File-format
differences alone must never qualify as a physical transport intervention.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def wind_identity(path, cells):
    raw = path.read_bytes()
    if len(raw) == cells*24:
        values = np.frombuffer(raw, dtype="<f8").reshape(3, cells).T.astype("<f4")
        kind = "legacy_component_major_double_to_float32"
    elif len(raw) == cells*12+8 and 2 <= struct.unpack_from("<i", raw)[0] <= 3:
        values = np.frombuffer(raw, dtype="<f4", offset=8).reshape(cells, 3)
        kind = "modern_interleaved_float32"
    else:
        raise ValueError(f"UNSUPPORTED_WIND_LAYOUT:{path}:{len(raw)}")
    if not np.isfinite(values).all() or np.max(np.abs(values)) > 1e4:
        raise ValueError(f"INVALID_WIND_VECTOR:{path}")
    values = values.copy()
    values[values == 0] = 0  # canonical positive zero
    return {"path": str(path), "name": path.name, "file_sha256": hashlib.sha256(raw).hexdigest(),
        "normalized_vector_sha256": hashlib.sha256(values.tobytes(order="C")).hexdigest(),
        "bytes": len(raw), "cells": cells, "layout": kind}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--metadata", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    out = {"contract": "CSTAR_WIND_INPUT_IDENTITY_V1", "gas_payload_reads": 0, "entries": []}
    for row in json.loads(args.metadata.read_text())["entries"]:
        sim = Path(row["resolved_realization_path"])
        cells = int(np.prod(row["simulation_header"]["dimensions"]))
        files = sorted((sim / "wind").glob("wind_iteration_*"), key=lambda p: int(p.name.rsplit("_", 1)[1]))
        item = {"realization_id": row["realization_id"], "config_id": row["config_id"],
                "files": [], "errors": []}
        for path in files:
            try:
                item["files"].append(wind_identity(path, cells))
            except Exception as exc:
                item["errors"].append(str(exc))
        out["entries"].append(item)
        print(row["house"], row["config_id"], len(item["files"]), item["errors"], flush=True)
    args.output.write_text(json.dumps(out, indent=2)+"\n")


if __name__ == "__main__":
    main()
