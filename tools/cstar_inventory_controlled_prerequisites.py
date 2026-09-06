"""Read-only directory/metadata inventory. Never read protected bank payloads."""
import argparse
import json
from pathlib import Path
import re


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    entries = []
    for house in ("House01", "House02", "House03"):
        for realization in sorted((args.scenario_root / house / "gas_simulations").glob("*/FilamentSimulation*")):
            files = list(realization.iterdir())
            iterations = [f for f in files if f.name.startswith("iteration_") and f.is_file()]
            wind = realization / "wind"
            entries.append({"house": house, "config": realization.parent.name,
                "realization_path": str(realization), "resolved_realization_path": str(realization.resolve()),
                "source_xyz_from_name_only": realization.name.split("sourcePosition_")[-1],
                "iteration_file_count": len(iterations),
                "wind_file_count": len(list(wind.glob("wind_iteration_*"))) if wind.is_dir() else 0,
                "top_level_metadata_filenames": [f.name for f in files if f.is_file()
                    and not f.name.startswith("iteration_")],
                "payload_read": False})
    report = {"contract": "CSTAR_CONTROLLED_PREREQUISITE_INVENTORY_V1",
        "scope": "names and file counts only, not provenance certification or controlled-asset PASS",
        "entries": entries}
    args.out.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
