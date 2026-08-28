# Codex execution contract — V4 science closure -> C++ parity -> smoke -> fixed development

## Mandatory branch

`research/cg-pc-ctt-v4-residual-assimilation`

Do not begin by editing C++. The revised Python scientific contract is upstream and must be verified first.

Normative files:

- `docs/CG_PC_CTT_V4_FINAL_THREE_MODULE_FREEZE_20260828.md`
- `docs/CG_PC_CTT_V4_PREIMPLEMENTATION_VALIDATION_20260828.md`
- `docs/CODEX_V4_SCIENCE_CONTRACT_CLOSURE_20260828.md`
- `experiments/cg_pc_ctt/v4_final_reference.py`
- `experiments/cg_pc_ctt/selftest_v4_final_reference.py`
- `experiments/cg_pc_ctt/v4_truthblind_coverage.py`

## Stage 0 — do not translate the superseded reference

The previous HEAD contract that said "direct C++ translation now" is superseded.

First run:

`python3 experiments/cg_pc_ctt/selftest_v4_final_reference.py`

Required stdout:

`V4_FINAL_REFERENCE_SCIENCE_CONTRACT PASS`

If it fails: stop and repair Python/reference parity only. Do not change scientific thresholds and do not inspect localization error.

## Stage 1 — archived three-House truth-blind coverage

Using already-revealed development OFF trajectories, materialize every usable source-update window from H01/H02/H03 seeds 0..9 into NPZ contexts accepted by `v4_truthblind_coverage.py`.

Required arrays:

- `stop_probability [S,M,J]`, keeping the same keyed member identity across physical stops;
- `stop_r [J]`, one hit fraction per physical stop;
- `rectangles [S,4]`;
- `geometry_prior [S]`;
- optional metadata `house`, `seed`, `update_id`, `context_id`, `timesteps`.

Do not put truth coordinates, final localization error, ON performance, route id, plume seed, or any post-hoc success label into the materializer or audit.

Run the coverage audit and produce:

- `artifacts/v4_truthblind_coverage/v4_truthblind_coverage.csv`
- `artifacts/v4_truthblind_coverage/v4_truthblind_coverage.json`
- `docs/V4_TRUTHBLIND_COVERAGE_REPORT_20260828.md`
- the archive-to-NPZ materialization script(s), committed.

The report must include per House: context count, ACCEPT count/fraction, each ABSTAIN reason, component-count distribution, min absolute-null gain distribution where defined, min rival-margin distribution where defined, and data-contract failures.

Do not use truth to characterize an ACCEPT as right/wrong in this stage.

Mechanical stop conditions:

- `STOP_ZERO_ACTIONABILITY`: total ACCEPT = 0 across H01/H02/H03;
- `STOP_SINGLE_HOUSE_ACTIONABILITY`: only one of the three Houses has any ACCEPT.

If either occurs: stop before C++; commit the evidence package and report the failure mechanism. Do not weaken the frozen rule.

Otherwise continue. Coverage is feasibility evidence only, not a performance claim.

## Stage 2 — direct C++ translation after coverage

Implement `pfdi_mode=v4_ocsla` as a direct translation of the now-frozen reference. Do not redesign the method.

### M1 binding details

- explicit monotone `physical_stop_id`;
- repeated completed blocks at one stop collapse to one stop outcome;
- within-stop forward-prediction drift is a hard failure;
- calibration members 0..3 build observation-resolved components;
- scoring members 4..7 never enter component construction;
- `C_y=(1/4+eps_T^2)I`, `eps_T=0.5/(iterationsToRecord+1)`;
- exact geometric aliases are unresolved;
- stable complement gets finite precision; no Moore-Penrose deletion.

### M2 binding details

- training evidence: sum physical stops inside each scoring member, then marginalize members;
- held-out score: conditional posterior prediction under the training-updated joint `(source, member)` distribution;
- no stopwise re-uniformization of members;
- absolute null: Jeffreys-Beta `Beta(1/2,1/2)` trained on the other physical stops only;
- selected component must beat the absolute null and not lose a rival on every held-out stop;
- at least two strictly rival-informative heldouts;
- scoring-member LOO cannot reverse the selected component;
- any failure => ABSTAIN.

### M3 binding details

ABSTAIN returns current native PMFS posterior exactly.

ACCEPT updates the independent causal region-vs-complement state and applies only the KL/I-projection mass floor. If native mass `beta >= alpha`, return native PMFS exactly. No blend, temperature, posterior reset, or House/seed threshold.

Each raw window is consumed exactly once.

## Stage 3 — Python/C++ parity

Create deterministic C++ parity fixtures for every Python selftest family, including:

- common-bias absolute-null counterexample;
- fixed member-identity-switch counterexample;
- component construction and exact alias;
- calibration/scoring member permutations;
- candidate permutation;
- inactive and active I-projection;
- duplicate-window rejection.

Python and C++ must agree on: component labels, ACCEPT/ABSTAIN reason, selected mask, held-out absolute gains, rival margins, alpha/beta, projection-active flag, and final posterior within numerical tolerance.

Do not proceed to ROS smoke on a parity mismatch.

## Stage 4 — infrastructure smoke

Use one non-development seed not in 0..19, recommended `314159`, on House02.

Smoke checks infrastructure only:

- correct `v4_ocsla` dispatch;
- no V3/EC-ECDL fallthrough;
- physical-stop grouping and drift audit;
- no forbidden truth field in runtime decision;
- exact native on ABSTAIN/inactive projection;
- finite mass-conserving posterior;
- accepted state persistence and consumed-window ledger;
- 300 s stop;
- complete audit output.

Do not tune from smoke localization error.

## Stage 5 — fixed development closed loop

After smoke PASS, freeze git SHA / binary SHA / launch SHA and run exactly:

`H01,H02,H03 × seeds 0..9 × OFF/ON = 60 arms`.

- OFF = frozen Classic PMFS;
- ON = revised V4;
- `TIMEOUT_SEC=300`;
- `STEPS_SOURCE_UPDATE=3`;
- same deterministic paired environment;
- no House/seed-specific edits;
- no mid-matrix changes;
- no 2/3/5-seed pilot.

Aggregate only after all 60 arms finish.

Development GO remains:

- 30/30 valid pairs;
- pooled top-5 expected-location error reduction >=10%;
- >=20/30 pairs improve;
- no House pooled degradation >5%;
- ON introduces 0 new false-confident collapses;
- all runtime contracts pass.

If GO: freeze again and run fresh confirmatory seeds 10..19.
If NOT-GO: stop and return the full evidence/failure package. Do not retune seeds 0..9.
