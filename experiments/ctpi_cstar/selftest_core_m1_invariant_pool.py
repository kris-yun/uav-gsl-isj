"""Algebraic checks for M1G transport-context log pooling."""

import json
import math
from pathlib import Path


# Rows are source candidates; columns are transport contexts.
likelihoods = [
    [0.30, 0.60, 0.45],
    [0.20, 0.50, 0.40],
    [0.10, 0.25, 0.20],
]


def normalize(values):
    total = sum(values)
    return [value / total for value in values]


def geometric_scores(table):
    return [math.exp(sum(map(math.log, row)) / len(row)) for row in table]


def arithmetic_scores(table):
    return [sum(row) / len(row) for row in table]


base = normalize(geometric_scores(likelihoods))
permuted = normalize(geometric_scores([list(reversed(row)) for row in likelihoods]))

# A member-specific scale is nuisance: it multiplies every candidate in that
# context.  Log pooling turns it into one common posterior normalization factor.
member_scales = [0.2, 3.0, 1.7]
scaled = [[value * member_scales[j] for j, value in enumerate(row)] for row in likelihoods]
scaled_geometric = normalize(geometric_scores(scaled))
scaled_arithmetic = normalize(arithmetic_scores(scaled))

repo = Path(__file__).resolve().parents[2]
pmfs = (repo / "ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp").read_text(
    encoding="utf-8"
)
simulations = (
    repo / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp"
).read_text(encoding="utf-8")
launch = (repo / "closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py").read_text(
    encoding="utf-8"
)
runner = (repo / "closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh").read_text(
    encoding="utf-8"
)

implementation_checks = {
    "mode_sets_transport_log_pool":
        'eventEvidenceTransportLogPool = pfdiMode == "cer_core_invariant_m1"' in pmfs,
    "log_pool_uses_mean_log_likelihood":
        "mixtureLikelihood = std::exp(meanLogLikelihood);" in simulations,
    "launch_identity_is_explicit": "'cer_core_invariant_m1': 'M1G'" in launch,
    "runner_identity_is_explicit": 'M1G) PFDI_MODE="cer_core_invariant_m1"' in runner,
}

report = {
    "contract": "CSTAR_CORE_M1_INVARIANT_LOG_POOL_V1",
    "base_posterior": base,
    "member_permutation_max_error": max(abs(a - b) for a, b in zip(base, permuted)),
    "member_scale_geometric_max_error": max(
        abs(a - b) for a, b in zip(base, scaled_geometric)
    ),
    "member_scale_arithmetic_max_error": max(
        abs(a - b)
        for a, b in zip(normalize(arithmetic_scores(likelihoods)), scaled_arithmetic)
    ),
    "geometric_not_above_arithmetic": all(
        geometric <= arithmetic + 1.0e-15
        for geometric, arithmetic in zip(
            geometric_scores(likelihoods), arithmetic_scores(likelihoods)
        )
    ),
    "implementation_checks": implementation_checks,
}
report["pass"] = (
    report["member_permutation_max_error"] < 1.0e-15
    and report["member_scale_geometric_max_error"] < 1.0e-15
    and report["member_scale_arithmetic_max_error"] > 1.0e-3
    and report["geometric_not_above_arithmetic"]
    and all(implementation_checks.values())
)
report["limits"] = [
    "finite algebraic test only",
    "transport contexts are three native stochastic replicas, not observed interventions",
    "closed-loop utility requires paired execution",
]

print(json.dumps(report, indent=2))
if not report["pass"]:
    raise SystemExit(1)
