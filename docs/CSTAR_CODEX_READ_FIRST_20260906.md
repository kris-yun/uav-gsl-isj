# CSTAR — Codex READ FIRST: theory, code status, and execution gates

Date: 2026-09-06
Branch: `g3-cstar-causal-redesign-20260906`
Base scientific snapshot: `2387668ec6345d273a8d630af069d65af710850f`

## 0. Read this before touching code

The paper-level main innovation is **causal**, and the method is **CSTAR — Causal Source–Transport Active Resolution**.

Do **not** reinterpret this branch as a generic PMFS tuning exercise, a Bayesian-marginalization variant, a GMRF-repair project, or a one-step active-learning planner.

The causal experiment loop is:

`fixed source S -> stochastic transport C -> sensor memory M -> observation Y -> M1 causal source belief pi(S) -> do(route) -> M2 future observation law -> M3 source-resolution route -> new observation`.

The three modules are load-bearing parts of this one loop:

1. **M1 PICR — Perturbation-Invariant Causal Representation**
   - mother field: single-cell perturbation biology / functional genomics;
   - role: recover source identity that is stable under transport, amplitude and sensor-context interventions.
2. **M2 CPO — Committor / First-Passage Predictive Operator**
   - mother field: chemical physics / rare-event and transition-path theory;
   - role: predict the route-conditioned future encounter law, not only mean concentration.
3. **M3 PHS — Prospective Hypothesis Sweeps**
   - mother field: systems neuroscience / hippocampal prospective sweeps and information symmetry;
   - role: prospectively evaluate feasible future routes and select the intervention that best separates currently competing source hypotheses.

## 1. Mandatory reading order

Read these files in this order:

1. `docs/CTPI_CSTAR_CAUSAL_THREE_MODULE_THEORY_20260906.md`
2. `docs/CTPI_CSTAR_COMPOSITION_THEORY_20260906.md`
3. `docs/CTPI_CSTAR_CURRENT_CODE_ALIGNMENT_20260906.md`
4. `docs/CTPI_CSTAR_M2_SPARSE_WIND_CONTRACT_20260906.md`
5. `docs/CTPI_CSTAR_2026_DISTANT_FIELD_LITERATURE_LEDGER.md`
6. `docs/CTPI_CSTAR_TERMINOLOGY_AND_LOADBEARING_CORRECTION_20260906.md`
7. `experiments/ctpi_cstar/CSTAR_INTERFACE_CONTRACT.json`
8. `docs/CODEX_CSTAR_IMPLEMENTATION_CONTRACT_20260906.md`
9. `docs/CSTAR_CODEX_HANDOFF_V2_20260906.json`

Then inspect the executable references:

- `experiments/ctpi_cstar/cstar_reference.py`
- `experiments/ctpi_cstar/m1_picr/model.py`
- `experiments/ctpi_cstar/m2_cpo/model.py`
- `experiments/ctpi_cstar/m3_phs/phs.py`
- `experiments/ctpi_cstar/selftest_cstar_reference.py`
- `experiments/ctpi_cstar/selftest_models.py`
- `experiments/ctpi_cstar/m3_phs/selftest_phs.py`

## 2. Current code-review status

### Reviewed and accepted as infrastructure / baseline

At base `2387668` the following paths were audited and may be retained:

- `CPIR.cpp::recordCPIRRawSample()` causal timestamp-to-pose binding and future-pose rejection;
- `CTPIOnlineCoreV2.hpp::Transport` conservative shared-face advection/diffusion, CFL substeps and mass-balance checks;
- `CTPIOnlineCoreV2.hpp::Fopdt` causal sensor-memory propagation;
- `CTPIOnlineCoreV2.hpp::ObservationStream` predict-before-observe ordering and no-future-wind contract;
- `MovingStatePMFS.cpp` feasible/open move-set construction, navigation validity checks and audit plumbing;
- corrected wind-observation semantics and navigation-height geometry alignment from the preceding V2 engineering work.

These are **infrastructure**, not scientific contributions.

### Reviewed and explicitly rejected as the new scientific path

Do not promote these legacy formulas into CSTAR:

- `CPIR.cpp::applyCPIRPosterior()` peak-normalized Gaussian-plume SSE and `-100*SSE/N` posterior;
- per-cell historical-peak compression as the primary M1 statistic;
- M1 MAP-chase and posterior-guidance coefficients;
- `CTPI.cpp::evaluateCTPIActionInformation()` carrier-centroid collapse;
- latest-wind one-point Gaussian-plume future model;
- one-step binary mutual information as the complete M3;
- `(1 + 20 * posteriorMass)` exploitation multiplier;
- GMRF as a paper contribution or mandatory full-wind-field provider.

### New research code already present

- PICR research model with explicit `zS`, `zN`, amplitude state, arbitrary-map candidate scoring and intervention-pair losses;
- CPO residual operator with hazard -> first-passage -> encounter-CDF / route-committor probability algebra;
- PHS route scorer with posterior-weighted pairwise Bhattacharyya confusion and region-source placement marginalization;
- CPU mathematical reference and self-tests.

Important correction already made: the PICR source posterior must be load-bearing through `zS`; the scorer must not bypass the causal source representation through an unconstrained hidden state.

## 3. Is the branch ready for formal closed-loop science?

**NO.**

This branch is ready for **implementation completion + offline falsification**, not for a formal House closed-loop campaign.

The following are still missing before formal closed loop is scientifically interpretable:

1. a real dataset adapter that builds PICR intervention pairs from the existing spent/frozen data without outcome leakage;
2. actual PICR training/checkpoint selection under the frozen M1 causal gate;
3. a named causal sparse-wind baseline/prior feeding CPO without requiring oracle full-field wind;
4. actual CPO training and held-out first-passage/encounter calibration;
5. production-quality route representation: use the real navigation path if available; otherwise use a frozen endpoint+dwell contract. Never draw a straight line through obstacles;
6. M3 held-out offline prospective-sweep falsification with a baseline provider before substituting learned CPO;
7. F00 posterior-to-native-planner adapter that introduces no fitted guidance coefficient and has exact parity when weights equal native weights;
8. production adapters/mode isolation only after the three offline scientific gates pass.

## 4. Mandatory execution order

### Phase A — static/reference verification

Run all pure-CPU/reference self-tests first. Fix only correctness/interface defects. Do not change scientific objectives to make later gates pass.

Expected references include:

- probability normalization;
- hazard -> first-passage identities;
- monotone encounter CDF;
- route committor equals `1 - P(no hit by horizon)`;
- Bhattacharyya coefficient extrema;
- PHS identical-law resolution = 0 and disjoint-law resolution = 1;
- region-valued source marginalization;
- PICR arbitrary-candidate posterior normalization;
- no direct `zN`/raw hidden-state bypass into source posterior.

### Phase B — M1 PICR offline causal falsification

Use existing data first. Do not launch new GADEN House campaigns.

Construct and freeze intervention pairs:

- same source, different transport/wind realization;
- same source, different source strength/release realization where available/licensed;
- same source, different sensor-memory context where available/licensed;
- different source, matched nuisance/context;
- leave-one-House-out evaluation.

M1 passes only if all are directionally supported:

- proper source score/error improves over peak-SSE M1 and a matched unconstrained temporal encoder;
- same-source nuisance interventions move `zS` less than the unconstrained encoder;
- different-source separation does not collapse;
- source-strength interventions no longer recreate the fixed-amplitude failure;
- source-label permutation destroys gain;
- removing the intervention constraint removes a measurable part of the gain;
- House ID is absent and held-out-House direction remains valid.

If task accuracy improves but causal intervention tests fail, M1 is **NO-GO as a causal contribution**.

### Phase C — M2 CPO offline predictive falsification

Inputs at deployment must remain only geometry + causal local-wind history + source hypothesis + sensor/current history + `do(route)`.

Primary future object is the first-passage categorical law:

`P(T=1),...,P(T=H),P(T>H)`.

Report encounter CDF and the terminal route committor separately and use the terminology exactly.

M2 passes only if held-out predictive distribution/calibration improves over:

- current causal plume/FOPDT baseline;
- uncorrected physics prior;

while preserving cross-House/source-strength/wind perturbation validity and never querying a held-out-House predictive bank at runtime.

### Phase D — M3 PHS offline falsification

Freeze a baseline route-law provider first so M3 is tested independently of learned CPO.

PHS uses:

`B(tau)=sum_{i<j} sqrt(pi_i*pi_j) * BC(P_i^tau,P_j^tau)`

and selects minimum confusion / maximum normalized resolution.

No `20x` term, no fitted explore/exploit coefficient, no carrier centroid as physical truth.

The native PMFS feasible route must be included in the candidate set whenever feasible so model-space comparison is auditable.

M3 passes only if it improves the preregistered temporal source-risk/error measure on held-out outcome realizations and route/source-law shuffle destroys the gain.

### Phase E — production integration and smoke

Only after A-D pass:

- add an isolated `cstar_v1` production mode;
- preserve legacy CPIR/CTPI/V3-ORR scientific formulas unchanged for reproducibility;
- connect full causal history -> PICR -> posterior;
- connect source x feasible route -> CPO route law;
- connect PICR posterior + CPO laws -> PHS chosen route;
- run infrastructure smoke for message timing, action legality, output normalization, runtime and audit integrity only.

Smoke outcome is not a scientific PASS.

### Phase F — closed-loop incremental science

Freeze before outcome inspection:

- `A0`: Classic PMFS;
- `F00`: PICR + native PMFS information planner through coefficient-free adapter;
- `F10`: PICR + PHS + frozen baseline route-law provider;
- `F11`: PICR + PHS + full CPO.

Interpret only:

- M1 increment = `F00 - A0`;
- M3 increment = `F10 - F00`;
- M2 increment = `F11 - F10`;
- full CSTAR = `F11 - A0`.

Each module must be directionally beneficial. A strong M1 cannot carry decorative M2/M3.

## 5. Hard stop rules

Stop and report instead of tuning if:

- M1 causal invariance/source-separation gate fails;
- M2 first-passage/encounter law does not beat simple causal baselines;
- M3 prospective resolution does not improve held-out source-risk/error;
- a required input is unavailable and would have to be replaced by source truth, future state, House ID or held-out predictive bank;
- the real navigation path is unavailable and somebody proposes a fake straight-line path through obstacles;
- production integration changes a frozen baseline scientific formula instead of adding an isolated mode.

Environment/build/ROS/overlay defects may be fixed and tested without changing the scientific equations.

## 6. What Codex should report back

Before any formal closed-loop campaign, return one evidence bundle containing:

- exact git SHA;
- all self-test commands/results;
- M1 gate metrics and destructive controls;
- M2 first-passage/encounter calibration and held-out tests;
- M3 held-out policy comparison and destructive controls;
- explicit PASS/NO-GO for M1, M2 and M3 separately;
- exact production integration diff and mode isolation;
- smoke audit if and only if all three modules pass offline.

Only after that evidence bundle should a formal closed-loop matrix be authorized.
