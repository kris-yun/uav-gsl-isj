# Codex direct instructions — RCEC V13 v2 audited candidate

Repository: `kris-yun/uav-gsl-isj`
Branch: `codex/rcec-v13-materialized-20260826`

## STOP / READ FIRST

The earlier RCEC draft used a feedback-coupled native log increment. It is rejected. Do not run parity, regression or new seeds until the **native-absolute v2 correction** and the build-closure patch have both been materialized and verified.

Read in this order:

1. `RCEC_V13_AUDIT_READ_FIRST.md`
2. `docs/RCEC_V13_FROZEN_METHOD_20260826.md`
3. `RCEC_V13_BUILD_CLOSURE_READ_FIRST.md`
4. this file

## 1. Reset to the latest remote branch

```bash
git fetch origin
git checkout codex/rcec-v13-materialized-20260826
git reset --hard origin/codex/rcec-v13-materialized-20260826
git status --short
```

The worktree must be clean before materialization.

## 2. Materialize the audited scientific correction first

```bash
python3 tools/fix_rcec_v13_native_absolute.py
```

Expected:

```text
RCEC_V13_NATIVE_ABSOLUTE_PATCH=PASS
native_view=current_post_native_absolute_rank
previous_injected_state_used_by_CREI=false
```

Scientific contract after this step:

```text
z_native,t(s) = NormalRank(M_native,t(s))
c_t(s) = min(z_native,t(s), z_even,t(s), z_odd,t(s))
m_t(s) = candidate-wise median of identifiable c_u(s)
q_t(s) proportional q0(s) exp(m_t(s))
```

`M_native,t` is the current PMFS candidate mass after the native source update and before RCEC injection. Do not subtract the previous source state.

## 3. Close the incomplete dormant V12-M build path

```bash
python3 tools/close_rcec_v13_build_dependency.py
```

Do not copy `RCSDTFEIV12.hpp` or `V12ResponseBank.hpp` from any workstation. RCEC does not use that legacy method.

Expected:

```text
RCEC_V13_BUILD_CLOSURE=PASS
legacy_v12_runtime=FAIL_CLOSED
rcec_method_equations_changed=false
```

## 4. Run hard source contracts

```bash
python3 reference/verify_rcec_v13_build_closure.py
python3 reference/verify_rcec_v13_source.py
```

Required:

```text
RCEC_V13_BUILD_CLOSURE_CONTRACT=PASS
RCEC_V13_SOURCE_CONTRACT=PASS
RCEC_V13_NATIVE_VIEW=ABSOLUTE_CURRENT_NATIVE_RANK
RCEC_V13_PREVIOUS_INJECTED_STATE_IN_CREI=false
RCEC_V13_CORE=PASS
```

If any command fails, STOP. Return the exact first failure. Do not hand-edit the algorithm to make a verifier pass.

## 5. Inspect diff before build

```bash
git diff -- \
  ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp \
  ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp \
  ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp
```

Allowed semantic changes relative to the current checkpoint are only:

- RCEC A1/A2/A3 arm plumbing;
- native-absolute CREI rather than rejected native increment;
- TMEM candidate history and explicit map-init reset;
- audit logging;
- fail-closed compile isolation of the incomplete dormant V12-M path.

Frozen/no-change areas:

- ACIT 54-member family;
- V11 even/odd temporal scoring;
- >=2 spatial-hit-site identifiability gate;
- PMFS OFF algorithm;
- planner parameters;
- runtime seed selection;
- no truth/error use.

## 6. Isolated ROS build

Build using the same ROS2 Humble/GADEN overlay provenance as the frozen V11 experiments. Do not overwrite the frozen V10/V11 binary artifact.

If build fails, STOP on the **first compiler/linker error** and report it exactly. Do not copy missing untracked files or change scientific code.

After successful build record:

- materialized Git commit SHA;
- `Simulations.cpp` SHA-256;
- `Simulations.hpp` SHA-256;
- `PMFS.cpp` SHA-256;
- final executable SHA-256;
- linked GADEN/ROS provenance.

Commit the materialized source before examining any new-seed truth.

## 7. Same-binary arm contract

Keep:

```text
pfdi_mode=me_aci
```

Choose at process launch:

```bash
RCEC_V13_ARM=v11_stouffer   # A1 frozen V11 parity
RCEC_V13_ARM=crei_latest    # A2 ACIT + native-absolute CREI
RCEC_V13_ARM=rcec_full      # A3 ACIT + CREI + TMEM
```

No variable is equivalent to A1.

Never switch arms inside a run.

## 8. OFF parity

Before any performance test, run a matched PMFS OFF parity case against the frozen baseline environment.

RCEC must not affect OFF behavior. Compare at least:

- final PMFS metric;
- source update count/times;
- robot trajectory;
- native source posterior hashes where available.

Any unexplained OFF difference is `RCEC_OFF_PARITY_FAIL` and stops the protocol.

## 9. A1 V11 parity

Use a previously revealed V11 case. Run `RCEC_V13_ARM=v11_stouffer` and verify the source state/logs against frozen V11 within the established numeric tolerance.

The native-absolute correction is inside A2/A3 only; A1 must remain frozen V11 behavior.

Any mismatch is `RCEC_A1_PARITY_FAIL` and stops the protocol.

## 10. Revealed mechanism regression — H01 seed653959

This seed is development-visible and must never be counted as confirmation.

Run A1/A2/A3 using the same build/runtime contract. The purpose is not to tune by final error but to verify mechanism/log identities:

A2/A3 must export per identifiable update:

- `native_absolute_mass`;
- `native_normal_rank`;
- `even_normal_rank`;
- `odd_normal_rank`;
- `crei_score`;
- `temporal_median_score`;
- `history_count`;
- active arm;
- injected posterior hash.

Hard checks:

- `native_normal_rank` is recomputable from current `native_absolute_mass` alone;
- no previous injected posterior enters CREI;
- candidate IDs/order remain identical across TMEM history, otherwise fail closed;
- new map initialization starts with empty RCEC history;
- A2 equals current CREI; A3 equals candidate-wise median of recorded CREI history;
- no truth/final-error field exists in online decision logs.

Do not tune if the revealed final error is disappointing. A mismatch between runtime and audit formula is an implementation fail; a formula-consistent poor result is scientific evidence.

## 11. Freeze before unseen truth

Only after Sections 1–10 pass, freeze source and binary hashes. Do not change formulas, gates, weights, temperature, planner or memory rule after this point.

Formula marker must be:

`rcec_v13_acit_crei_native_absolute_tmem_v2`

## 12. Genuinely unseen 300 s qualification

Select seeds that have never appeared in V10/V11/V12/V13 method development or evidence inspection.

Initial minimum:

- H01 OFF vs A3 `rcec_full`, full 300 s;
- H02 OFF vs A3, full 300 s;
- H03 OFF vs A3, full 300 s.

Do not inspect ON truth before both arms for that pair are complete. No early stop at first accepted update.

Primary metric remains frozen PMFS `ExpectedValue(sourceProbability, 0.05)` final localization error.

Use the existing preregistered spirit for initial qualification:

- at least 2/3 Houses improve;
- pooled improvement >=10%;
- zero catastrophic regressions (>=1 m absolute regression and <=-25% relative improvement);
- no new false-confident wrong collapse.

If the 3-pair qualification passes, expand independent seeds for paired confidence intervals/statistical robustness. If it fails, archive it; do not tune the revealed seeds.

## Development evidence boundary

The corrected 15-pair native-absolute offline audit is **fixed-trajectory shadow evidence only**. It uses archived V11 trajectories and therefore cannot predict planner/trajectory feedback under RCEC. It exists to justify implementation and stress-test the formula, not to replace the unseen closed-loop qualification.

Do not cite the older native-increment audit as the active method; it is superseded/rejected.
