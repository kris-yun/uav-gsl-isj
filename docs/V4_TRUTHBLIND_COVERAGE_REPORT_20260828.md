# CG-PC-CTT V4 truth-blind coverage and power report

Date: 2026-08-28

Frozen upstream reference: `42e089f3dc7ced1b471e21d97ddaf3bbb92c1ce1`

Development archive: H01/H02/H03, seeds 0..9, OFF trajectories only

## Executive verdict

- `V4_FINAL_REFERENCE_SCIENCE_CONTRACT = PASS`
- `V4_INDEPENDENT_ADVERSARIAL_AUDIT = PASS`
- `V4_TRUTHBLIND_MATERIALIZATION = PASS` (30/30 runs, 150/150 contexts, 0 invalid)
- `UPSTREAM_MECHANICAL_ACTIONABILITY = PASS` (ACCEPT occurs in H01 and H02)
- `V4_DEVELOPMENT_20_OF_30_POWER_BOUND = FAIL`
- `RECOMMENDATION = STOP_BEFORE_CPP_AND_60_ARM_MATRIX`

The revised reference closes the earlier component-construction, coherent-member,
absolute-adequacy, and NumPy-axis defects. It is now a scientifically coherent
selective update rule. It does **not**, however, have enough activation coverage
to satisfy its own planned closed-loop GO criterion.

## Frozen truth-blind reconstruction

The adapter opened only the OFF runtime information needed to reconstruct the
causal source-update window:

- completed-block `GAS HIT` / `NOTHING` records from the PMFS action log;
- source-update wall-clock boundaries;
- explicit moving/stationary pose state;
- context-bank occupancy and estimated-wind snapshots;
- the frozen truth-free eight-member CTT builder.

Eight completed blocks at one stationary stop were collapsed to one fractional
hit outcome. The first source-update window contained four physical stops and
later windows contained three. Persistent 2x2 geometry carriers were rebuilt
from occupancy only and exactly covered every free cell once. Full trace banks
were streamed through a temporary directory and removed after extracting the
actual-stop probabilities.

No true-source coordinate, final estimate, localization error, ON outcome,
route identifier, or plume-seed success proxy was loaded or written to the NPZ
contexts. The NPZ schema contains only the four required arrays and allowed
House/seed/update metadata.

All 150 contexts passed:

- candidate permutation invariance;
- calibration-member permutation invariance;
- scoring-member permutation invariance;
- exact eight-block-to-one-stop grouping;
- positive finite effective-covariance spectrum;
- truth/performance-key exclusion.

The minimum effective-covariance eigenvalues stayed near 0.25, confirming that
the frozen sensor floor gives finite stable-complement precision.

## Coverage result

| House | Valid contexts | ACCEPT | Coverage | Runs with at least one ACCEPT | ACCEPT seeds |
|---|---:|---:|---:|---:|---|
| H01 | 50 | 6 | 12.0% | 5/10 | 0, 3, 5, 8, 9 |
| H02 | 50 | 1 | 2.0% | 1/10 | 0 |
| H03 | 50 | 0 | 0.0% | 0/10 | none |
| **Total** | **150** | **7** | **4.67%** | **6/30** | — |

Abstention reasons:

| House | LOSO component disagree | Held-out rival contradiction | Insufficient informative held-out | Scoring-member LOO fail |
|---|---:|---:|---:|---:|
| H01 | 27 | 9 | 5 | 3 |
| H02 | 43 | 6 | 0 | 0 |
| H03 | 47 | 2 | 1 | 0 |

Observation-resolved components were not absent. Median component counts were
47.5 (H01), 55.5 (H02), and 48.5 (H03). The dominant failure is therefore M2
cross-stop invariance, not M1 numerical rank or a missing source partition.

## Why the planned development GO is already impossible

The frozen method requires an ABSTAIN to return native PMFS exactly. Consider a
paired OFF/ON run before its first V4 ACCEPT:

1. posterior is identical;
2. planner input is identical;
3. the paired deterministic planner chooses the same trajectory;
4. the same physical observations and next source-update context follow.

By induction, if the complete archived OFF trajectory contains no ACCEPT, the
V4 ON arm cannot spontaneously reach a different future context. It remains
identical to PMFS for the full run. Such a pair cannot have a strictly improved
final error under the frozen contract.

Only 6 of the 30 development OFF runs contain any ACCEPT. Therefore the maximum
possible number of non-identical/improved pairs is 6, even under the optimistic
assumption that every activated pair improves. This is below the frozen GO
requirement of at least 20 improved pairs out of 30:

`max_possible_improved_pairs = 6 < 20`.

This bound uses neither truth nor localization error. Running 60 arms cannot
repair it. Any ON divergence in one of the 24 zero-ACCEPT runs would indicate a
parity, determinism, or infrastructure defect rather than V4 scientific gain.

## Scientific assessment

The update from the earlier draft is substantive:

- M1 now has an executable calibration-member quotient with finite precision;
- M2 preserves one source/member latent identity across stops and uses exact
  conditional posterior prediction;
- the Jeffreys-Beta prequential null blocks shared model misspecification;
- M3 is a defensible minimum-change KL/I-projection, not an arbitrary blend.

The remaining limitation is structural. With only three new physical stops in
most windows, leave-one-stop-out training has only two stops. H02 and H03 form
many observation-resolved spatial components, but different held-out stops do
not support one common component. The rule is safe because it abstains; it is
too rarely active to be the requested >=10% general closed-loop improvement.

The paper should also describe M2 as an invariant cross-predictive residual
unless an intervention/identification argument is added; the present evidence
does not by itself establish a causal effect in the strict Pearl/Rubin sense.

## Idea-quality score after falsification

| Axis | Score | Evidence |
|---|---:|---|
| A. Idea quality | 5/5 | Clear three-module mechanism; prior reference defects are genuinely repaired. |
| B. Reasoning quality | 4/5 | Coherent latent-member prediction, absolute null, and minimum-change assimilation are well aligned; strict causal naming remains ahead of identification. |
| C. Feasibility and validation | 2/5 | 150/150 contexts are auditable, but only 6/30 runs can ever differ from PMFS and H03 is fully inactive. |

Overall: **70/100 — promising scientific mechanism, but STOP for the frozen
performance objective**.

## Required next decision

Do not loosen the Jeffreys null, numerical zero, member count, or LOSO rule
after seeing this coverage. If the research continues, it must be a newly
frozen method version that increases observation information before the gate,
not a threshold rescue. The most direct hypothesis to test is whether an
anytime-valid accumulation over more unique physical stops (or a separately
falsified within-stop dynamical observation marker) can create reproducible
H02/H03 component support without block pseudo-replication.

## Evidence files

- `artifacts/v4_truthblind_coverage/archive_inventory.csv`
- `artifacts/v4_truthblind_coverage/materialization_manifest.csv`
- `artifacts/v4_truthblind_coverage/materialization_summary.json`
- `artifacts/v4_truthblind_coverage/v4_truthblind_coverage.csv`
- `artifacts/v4_truthblind_coverage/v4_truthblind_coverage.json`
- `artifacts/v4_truthblind_coverage/H01_persistent_carriers.csv`
- `artifacts/v4_truthblind_coverage/H02_persistent_carriers.csv`
- `artifacts/v4_truthblind_coverage/H03_persistent_carriers.csv`

The 150 compressed NPZ payloads remain on the VM at
`/home/zyc/V4_TRUTHBLIND_COVERAGE_20260828_R1/contexts`; their SHA-256 values and
paths are frozen in `materialization_manifest.csv`.
