"""Run all current CSTAR reference/model/offline-interface tests from one command.

Usage from repository root:
    python experiments/ctpi_cstar/run_reference_selftests.py
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import selftest_cstar_reference
import selftest_models
import selftest_offline_contracts
from m3_phs import selftest_phs


def main():
    selftest_cstar_reference.main()
    selftest_phs.main()
    selftest_models.main()
    selftest_offline_contracts.main()
    print("CSTAR_ALL_REFERENCE_SELFTESTS PASS")


if __name__ == "__main__":
    main()
