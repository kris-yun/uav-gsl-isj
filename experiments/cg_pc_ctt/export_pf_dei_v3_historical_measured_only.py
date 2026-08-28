#!/usr/bin/env python3
"""Export the 30 historical measured streams without copying truth fields.

This tool may be executed only after PF-DEI V3 weights are frozen.  It retains
the runtime directory layout expected by the future-predictive qualifier and
writes sensor_trace.csv files containing only t_sim_s and measured_gas_ppm.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for house_number in (1, 2, 3):
        house = f"House{house_number:02d}"
        for seed in range(10):
            relative = (
                Path(house) / f"seed{seed}" / "off" / "runtime"
                / f"{house}_seed{seed}_off_off" / "sensor_trace.csv"
            )
            source_path = args.archive_root / relative
            output_path = args.output_root / relative
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with source_path.open(newline="", encoding="utf-8-sig") as source:
                reader = csv.reader(source)
                header = next(reader)
                index = {name: offset for offset, name in enumerate(header)}
                for required in ("t_sim_s", "measured_gas_ppm"):
                    if required not in index:
                        raise ValueError(f"PF_DEI_V3_MEASURED_EXPORT_MISSING_FIELD:{required}:{source_path}")
                count = 0
                with output_path.open("w", newline="", encoding="utf-8") as sink:
                    writer = csv.writer(sink)
                    writer.writerow(("t_sim_s", "measured_gas_ppm"))
                    for source_row in reader:
                        writer.writerow((
                            source_row[index["t_sim_s"]],
                            source_row[index["measured_gas_ppm"]],
                        ))
                        count += 1
            if count < 20:
                raise ValueError(f"PF_DEI_V3_MEASURED_EXPORT_TOO_SHORT:{source_path}")
            rows.append({
                "house": house, "seed": seed, "row_count": count,
                "source_sensor_trace_sha256": sha256_file(source_path),
                "sanitized_sensor_trace_sha256": sha256_file(output_path),
                "relative_path": relative.as_posix(),
                "exported_fields": ["t_sim_s", "measured_gas_ppm"],
                "truth_fields_exported": False,
            })
    manifest = {
        "contract": "PF_DEI_V3_HISTORICAL_MEASURED_ONLY_V1",
        "run_count": len(rows), "truth_fields_exported": False, "runs": rows,
    }
    manifest_path = args.output_root / "measured_only_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PF_DEI_V3_HISTORICAL_MEASURED_ONLY=PASS runs={len(rows)} manifest_sha256={sha256_file(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
