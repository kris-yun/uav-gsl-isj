"""Run all CSTAR reference/model/offline/environment/provenance/review tests.

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
import selftest_environment_alignment
import selftest_raw_realization_provenance
import review_regression_tests
import replay_m1_phic_attribution
from m3_phs import selftest_phs


def main():
    selftest_cstar_reference.main()
    selftest_phs.main()
    selftest_models.main()
    selftest_offline_contracts.main()
    selftest_environment_alignment.main()
    selftest_raw_realization_provenance.main()
    review_regression_tests.main()
    replay_report = replay_m1_phic_attribution.selftest()
    if not replay_report["pass"]:
        raise SystemExit("CSTAR_M1_PHIC_ATTRIBUTION_REPLAY_SELFTEST FAIL")
    print("CSTAR_M1_PHIC_ATTRIBUTION_REPLAY_SELFTEST PASS")
    print("CSTAR_ALL_REFERENCE_ENVIRONMENT_PROVENANCE_AND_REVIEW_SELFTESTS PASS")


if __name__ == "__main__":
    main()
