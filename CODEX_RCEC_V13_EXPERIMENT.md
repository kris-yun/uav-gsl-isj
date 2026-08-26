# Codex direct execution — RCEC V13 frozen candidate

Repository: `kris-yun/uav-gsl-isj`  
Branch: `rcec-v13-frozen-candidate-20260826`  
Base checkpoint: `3f95e646dcfa2182fde60dcad11c8b0d8a7945d2`

## 0. Scientific boundary

Do not continue the rejected CTT M2/M3 HMM/count-survival route for this experiment. CTT files in the base checkpoint are diagnostic only.

RCEC V13 is an upgrade of frozen V11. Do not change the V11 54-member ACIT inverse-transport family, even/odd temporal folds, >=2 spatial hit-site identifiability rule, cumulative raw-event reservoir, PMFS planner, 300 s budget, frozen evaluation metric, or source-truth isolation. No adaptive weights, temperatures, House-specific parameters or truth gates.

## 1. Pull and materialize the frozen source patch

```bash
git fetch origin
git checkout rcec-v13-frozen-candidate-20260826
git reset --hard origin/rcec-v13-frozen-candidate-20260826

python3 tools/apply_rcec_v13_patch.py
python3 reference/verify_rcec_v13_source.py
git diff -- \
  ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp \
  ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp
```

The patch must report `RCEC_V13_SOURCE_PATCH=PASS`; the verifier must report `RCEC_V13_SOURCE_CONTRACT=PASS` and `RCEC_V13_CORE=PASS`.

Record SHA-256 for the materialized source files. Commit the materialized patch on a child branch before any new-seed truth is viewed, e.g.

```bash
git checkout -b codex/rcec-v13-materialized-20260826
git add ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp \
        ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp
git commit -m "feat: materialize frozen RCEC V13 source fusion"
git push -u origin codex/rcec-v13-materialized-20260826
```

## 2. Same-binary ablation modes

Keep `pfdi_mode=me_aci`. Select only the fusion arm with:

```bash
RCEC_V13_ARM=v11_stouffer   # A1 frozen V11 parity
RCEC_V13_ARM=crei_latest    # A2 ACIT + CREI
RCEC_V13_ARM=rcec_full      # A3 ACIT + CREI + TMEM
```

Absence of `RCEC_V13_ARM` must be parity-equivalent to `v11_stouffer`. Do not implement additional modes or weights.

## 3. Build and parity gates before any performance run

Build an isolated binary using the same ROS2/GADEN overlays as frozen V11. Record source SHA, binary SHA and linked `libgaden.so` provenance.

Required gates:

1. OFF parity: RCEC environment must not alter an OFF run.
2. A1 parity: `RCEC_V13_ARM=v11_stouffer` must reproduce frozen V11 on a revealed replay/mechanism case within numerical tolerance.
3. Missing environment variable must match A1.
4. Invalid `RCEC_V13_ARM` must fail hard.
5. No truth coordinate or final error may occur in `rcec_v13_scores_*` inputs.
6. Candidate ID/order drift must fail rather than silently remap TMEM history.

## 4. Revealed-seed mechanism regression only

Use revealed seeds only to verify mechanics; they are not qualification data. Preferred stress case: House01 seed653959 because V11 had the catastrophic regression there.

For A1/A2/A3 export at every identifiable update: candidate ID; native-before/after candidate mass; native log increment and normal rank; even/odd normal ranks; V11 Stouffer score; CREI score; TMEM score; history count; active score/posterior; trajectory and final external PMFS metric.

Structural expectations, not performance tuning:

- A1 reproduces V11;
- A2 can veto a candidate that is high in only one view;
- A3 median equals the median of archived CREI snapshots candidate-by-candidate;
- each new identifiable update appends exactly one TMEM snapshot;
- an abstained update appends none;
- no historical score is multiplied as a fresh likelihood.

If any invariant fails, stop. Fix implementation only; do not inspect new-seed performance.

## 5. Freeze before new seed

After parity/mechanism gates pass, freeze source commit SHA, binary SHA-256, `RCECV13.hpp` SHA-256, `RCEC_V13_ARM=rcec_full`, PMFS config/planner parameters, map/House configs, GADEN build/library provenance, 300 s timeout, evaluator SHA, and formula marker `rcec_v13_acit_crei_tmem_v1`.

No change after new-seed truth is read.

## 6. New-seed confirmatory qualification

Choose genuinely new seeds not present in any V10/V11/V12/V13 development archive. Do not pre-screen seeds by result.

First economical gate:

- one new House01 OFF/A3 pair;
- one new House02 OFF/A3 pair;
- one new House03 OFF/A3 pair;
- full 300 s, no early stopping.

If the three-pair gate has a catastrophic regression or pooled improvement <=0, stop and archive NO-GO. If direction is positive without catastrophe, extend to at least 3 new seeds per House (9 paired cases total).

Primary final metric remains frozen PMFS `ExpectedValue(sourceProbability, 0.05)` localization error.

Report pair table, pooled and House-wise improvement, positive-pair fraction, catastrophe count, paired bootstrap CI clustered by seed/pair, sign/permutation test as appropriate, posterior variance as secondary only, and trajectory divergence separately from inference improvement.

Do not require every seed to improve; do require no recurrence of the V11 catastrophic wrong-basin tail in the qualification set.

## 7. Offline evidence is development-only

`evidence/rcec_v13/rcec_v13_offline_15pairs_summary.json` documents the revealed 15-pair shadow audit. It is useful for mechanism and ablation justification, not for the confirmatory p-value or final generalization claim.
