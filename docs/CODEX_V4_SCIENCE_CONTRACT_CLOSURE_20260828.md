# Codex task — close V4 scientific contract before C++

Date: 2026-08-28
Branch: `research/cg-pc-ctt-v4-residual-assimilation`

## Objective

Do the environment-dependent work that cannot be completed from the static repository alone: reconstruct truth-free OFF source-update contexts for H01/H02/H03, measure the revised V4 M1/M2 activation coverage, and only then decide whether C++ translation is justified.

The mathematics is already frozen in `v4_final_reference.py`. Do not invent another method.

## Required order

1. Pull the branch and record HEAD.
2. Run `selftest_v4_final_reference.py`; require `V4_FINAL_REFERENCE_SCIENCE_CONTRACT PASS`.
3. Inventory archived OFF development artifacts for H01/H02/H03 seeds 0..9.
4. Write the smallest deterministic adapter needed to export one NPZ per usable source-update context.
5. Run `v4_truthblind_coverage.py`.
6. Commit the adapter, CSV, JSON, and `V4_TRUTHBLIND_COVERAGE_REPORT_20260828.md`.
7. Apply the mechanical actionability stop conditions.
8. Only if not stopped, begin C++ translation/parity.

## Data reconstruction rules

A context is valid only if the archive can establish:

- one explicit source-update window;
- actual physical-stop grouping, not block-as-stop pseudo-replication;
- all 8 keyed transport members with identity preserved across the stops;
- persistent carrier rectangles/order;
- geometry prior corresponding to those carriers;
- `T=iterationsToRecord`.

If an archive contains 8 repeated blocks at each stop, collapse to `r_j` and one prediction coordinate per physical stop. If member identity or physical-stop identity cannot be recovered unambiguously, mark the context invalid rather than guessing.

Do not silently substitute reconstructed full-field cells for unobserved actual stops.

## Forbidden data in the activation decision

Do not load or reference:

- true source coordinates or truth-near carrier;
- final localization error;
- OFF-vs-ON improvement;
- final estimate;
- route id as a success proxy;
- plume seed as a success proxy.

Those fields may be used only after the truth-blind coverage report is frozen, in a separately labeled retrospective analysis.

## Required falsification checks on the materialized contexts

Before accepting the coverage report:

- candidate permutation leaves the decision invariant after unpermuting;
- calibration-member permutation leaves components invariant;
- scoring-member permutation leaves the decision invariant;
- scoring-member identity destruction is able to alter at least some non-degenerate synthetic fixture, proving the identity check is live;
- duplicating blocks within a stop cannot increase physical-stop count;
- source truth is absent from the NPZ key set;
- no localization-error column enters the audit;
- every finite covariance eigenvalue is positive under the frozen sensor floor.

## Deliverables

Commit:

- archive-to-context adapter(s);
- `artifacts/v4_truthblind_coverage/*.npz` only if repository size policy permits, otherwise a manifest with hashes and VM paths;
- `artifacts/v4_truthblind_coverage/v4_truthblind_coverage.csv`;
- `artifacts/v4_truthblind_coverage/v4_truthblind_coverage.json`;
- `docs/V4_TRUTHBLIND_COVERAGE_REPORT_20260828.md`.

The report must state exact invalid/missing context counts. Never silently drop failed contexts.

## Stop / continue rule

If total revised ACCEPT across all three Houses is zero:
`STOP_ZERO_ACTIONABILITY`.

If only one House has any ACCEPT:
`STOP_SINGLE_HOUSE_ACTIONABILITY`.

In either case, do not change the Jeffreys-Beta null, numerical-zero rule, component construction, number of members, or LOSO rule after seeing outcomes. Return the evidence and stop.

Otherwise:
`V4_TRUTHBLIND_COVERAGE_ACTIONABLE_FOR_CPP`.

That verdict authorizes implementation engineering only; it is not a localization-performance claim.
