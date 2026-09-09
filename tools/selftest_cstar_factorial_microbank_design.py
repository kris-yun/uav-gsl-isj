"""Static guard for the source-by-wind M1 microbank generator.

The guard prevents a cosmetic SA/SB ``fast`` label from silently selecting two
different wind directories.  It does not generate a gas field or qualify an
output; those remain separate VM evidence steps.
"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/cstar_generate_current_runtime_dataset.sh"


def main():
    rows = re.findall(
        r"^run_case\s+(H0[123])_S([AB])_(fast|slow)\s+(House0[123])\s+'([^']+)'\s+(.+)$",
        SCRIPT.read_text(encoding="utf-8"), re.MULTILINE,
    )
    if len(rows) != 12:
        raise RuntimeError(f"EXPECTED_12_CASES_GOT_{len(rows)}")
    selected = {}
    for house_id, source_arm, regime, runtime_house, wind_config, source_xyz in rows:
        if house_id[-1] != runtime_house[-1]:
            raise RuntimeError(f"HOUSE_LABEL_MISMATCH:{house_id}:{runtime_house}")
        selected.setdefault((house_id, regime), {})[source_arm] = wind_config
        if len(source_xyz.split()) != 3:
            raise RuntimeError(f"SOURCE_XYZ_ARITY:{house_id}:{source_arm}:{regime}")
    for key, arms in selected.items():
        if set(arms) != {"A", "B"}:
            raise RuntimeError(f"MISSING_SOURCE_ARM:{key}")
        if arms["A"] != arms["B"]:
            raise RuntimeError(f"SOURCE_WIND_NOT_FIXED:{key}:{arms}")
    print("CSTAR_M1_FACTORIAL_MICROBANK_DESIGN=PASS")


if __name__ == "__main__":
    main()
