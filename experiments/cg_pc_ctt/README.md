# CG-PC-CTT V3 research entrypoint — direct closed-loop path

Current branch: `research/cg-pc-ctt-v3-observation-quotient-theory`  
Status: **RESEARCH / V3-ORR direct closed-loop integration authorized / no paper-level GO yet**.

## 0. Current execution path — read this first

The verified House02 reconstructed bank is now a completed development/diagnostic asset. Do **not** wait for more H02 data before the next performance experiment.

Frozen state:

- `H02_RECONSTRUCTED_CHALLENGE_V1_BANK_VERIFY_PASS`;
- 51 outcome-blind House02 contexts;
- 201 unique physical source carriers;
- 8 keyed transport members;
- 82,008 verified CTT V13 traces;
- historical hard-28 remains `LEGACY_HARD28_PROVENANCE_LOST` and is not reconstructed.

The current ON-arm engineering contract is **V3 Observation-Resolved Reversible Update (V3-ORR)**.

Read and execute:

`docs/CODEX_V3_ORR_INTEGRATE_AND_RUN_20260827.md`

Binding next steps:

1. run `bash experiments/cg_pc_ctt/run_v3_selftests.sh`;
2. integrate `ObservationResolvedV3.hpp` into `Simulations.cpp` at the existing `rawProbabilities[source][member][completed_event]` branch point, before historical EC-ECDL Hellinger/eigenchannel processing;
3. add explicit `pfdiMode=v3_orr`;
4. build an isolated binary;
5. run infrastructure smoke only on House02 seed `314159`; do not tune using localization outcome;
6. freeze git SHA, binary SHA and launch SHA;
7. launch `House01/House02/House03 x seeds 0..9 x OFF/ON = 60 arms`, `TIMEOUT_SEC=300`, `STEPS_SOURCE_UPDATE=3`;
8. aggregate with `closed_loop/cg_pc_ctt/aggregate_multiseed.py`.

Do **not** insert another hard-28 recovery, bridge panel, post-bank pre-outcome sweep, or small-seed method-selection stage before this matrix.

`run_h02_reconstructed_postbank_preoutcome.sh` is retained only as an optional archival diagnostic and now refuses to run unless `ALLOW_LEGACY_PREOUTCOME_DIAGNOSTIC=1` is explicitly set.

## 1. Frozen scientific status

### CONFIRMED

- CTT M1 wind-conditioned first-passage transport is the positive transport premise.
- Gate V2 repaired V1 finite-member self-noise and passed the real H03 bank `phi[10,206,8,626]` in all 10 contexts.
- Gate V2 is interpreted as a **model-side replicated-identifiability/completeness premise**, not a runtime reliability selector.
- Sparse actual observation support causes local source-information rank loss in both H03 CTT first-passage responses and the recovered H02 PMFS hit-probability response family.
- Full-covariance V3 mathematics removes the earlier feature-duplication sensitivity of diagonal whitening and aligns local information with the 2-D physical source parameter `(x,y)`.
- Existing PMFS `applyEnsembleEcEdcl()` already materializes candidate × keyed-member predictive probabilities at the actual completed-event positions before historical Hellinger normalization. V3-ORR reuses this runtime object rather than introducing a second simulator.

### LEGACY / NOT A CURRENT BLOCKER

- Gate V1: `INVALID_PROTOCOL`.
- Historical H02 hard-28 primary provenance: `LEGACY_HARD28_PROVENANCE_LOST`.
- `h02_hard28_fast_eval.py`, `bridge_fasttrack_verdict.py`, and `run_h02_reconstructed_postbank_preoutcome.sh` are not current closed-loop prerequisites.
- The proximal/host-aware bridge remains a mechanistic analysis and possible later extension; it is **not** a prerequisite for the direct V3-ORR closed-loop matrix.

## 2. V3-ORR runtime contract

Use only causally available quantities:

- `rawProbabilities[source][keyed_member][completed_event]`;
- completed-event hit/miss;
- stable `block_id`;
- geometry-only persistent-carrier rectangles;
- fixed geometry/design prior.

Forbidden online inputs include source truth, future observations, same-window native PMFS posterior/rank as V3 evidence, legacy `native_score`, oracle wind/plume/config IDs, and House/seed-specific fitted parameters.

### Member split

Eight keyed members are fixed as:

- members `0..3`: observation-resolution calibration only;
- members `4..7`: outcome likelihood scoring only.

### Observation resolution

On actual completed-event support, calibration members define the full pair-difference nuisance covariance `Sigma_tr` and numerical Moore-Penrose inverse `Sigma_tr^+`.

For each adjacent physical source pair, replicated cross-member source separation and leave-one-member-out stability decide whether that local boundary is resolved. Ordinary repeated online sign-flip p-values are not used.

Unresolved local edges form connected components called **resolution cells**. This is a geometric resolution statement, not a claim that every candidate inside the component has an identical statistical distribution.

### Outcome evidence

Scoring members use the proper Bernoulli trajectory likelihood. Events split by stable `block_id % 2` into even/odd reproducibility folds. Each fold needs at least two events and at least one hit and one miss; otherwise V3-ORR abstains.

Candidate evidence is projected to resolution cells before tie-safe normal ranking.

### Reversible posterior

Fold scores combine as

`g(s) = [z_even(s) + z_odd(s)] / sqrt(2)`.

Project `g` again to the current resolution cells, then compute

`q(s) proportional q0(s) exp(g(s))`,

where `q0` is the fixed geometry/design prior.

The posterior is recomputed from the current completed-event set and fixed prior. It is not recursively multiplied by the previous V3 posterior, preventing stale-evidence double counting.

On ABSTAIN, do not inject the same-window Classic PMFS posterior as V3 evidence.

## 3. Authoritative code

Shared research mathematics:

- `v3_math.py`
- `v3_adequacy.py`
- `v3_bernoulli_adequacy.py`

Direct runtime reference/parity:

- `v3_direct_runtime_reference.py`
- `selftest_v3_direct_runtime.py`
- `ros2_package/src/gsl_server/algorithms/PMFS/internal/ObservationResolvedV3.hpp`

Posterior reference:

- `closed_loop/cg_pc_ctt/v3_quotient_rank_posterior.py`
- `closed_loop/cg_pc_ctt/selftest_v3_quotient_posterior.py`

CTT archive/diagnostic tools remain available, including the exact CTT bitset decoder and compact tensor materializer, but they are not gating the next closed-loop run.

## 4. Selftests

Run before integration/build:

```bash
cd experiments/cg_pc_ctt
bash run_v3_selftests.sh
```

Expected:

`CG_PC_CTT_V3_STATIC_AND_MATH_SELFTEST PASS`

## 5. Confirmatory closed-loop matrix

OFF: unmodified Classic PMFS.  
ON: V3-ORR.

Frozen matrix:

`3 Houses x 10 seeds x OFF/ON = 30 matched pairs / 60 arms`.

Frozen endpoint and success criteria remain:

1. 30/30 matched pairs valid;
2. pooled PMFS `ExpectedValue(sourceProbability,0.05)` error reduction >=10%;
3. one-sided paired sign test `p<=0.05`;
4. no House pooled mean degrades by >5%;
5. zero false-confident-collapse flags.

No House-specific, seed-specific, threshold, temperature, blend-weight or bridge-weight tuning after the matrix begins.

## 6. Theory / protocol documents

Primary current documents:

- `docs/CG_PC_CTT_V3_DIRECT_CLOSED_LOOP_FREEZE_20260827.md`
- `docs/CODEX_V3_ORR_INTEGRATE_AND_RUN_20260827.md`
- `docs/CG_PC_CTT_V3_OBSERVATION_QUOTIENT_DERIVATION_20260827.md`
- `docs/CG_PC_CTT_V3_ASSIMILATIVE_RESOLUTION_AND_SEQUENTIAL_VALIDITY_20260827.md`
- `docs/CG_PC_CTT_V3_FAILURE_PREMORTEM_20260827.md`

Binding rule: **resolution must be earned by causally available observations; no truth leakage, no unvisited forward-field support counted as current evidence, no outcome-fitted online threshold, and no repeated unadjusted online p-value release.**
