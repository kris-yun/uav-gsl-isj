"""Run all current pure-CPU CSTAR reference tests from one command.

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
from m3_phs import selftest_phs


def main():
    selftest_cstar_reference.main()
    selftest_phs.main()
    print("CSTAR_ALL_REFERENCE_SELFTESTS PASS")


if __name__ == "__main__":
    main()
