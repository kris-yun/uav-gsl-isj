# Codex execution runbook — TNQC V5 300-s offline gate

## 0. Scope

You are executing a **frozen confirmatory/offline feasibility batch**. You are
not developing or tuning TNQC.

Repository:

`kris-yun/uav-gsl-isj`

Execution branch:

`codex/tnqc-v5-300s-offline-20260921`

Frozen method/source checkpoint:

`9d3d21e7a7fdea0946e29d313ea9073ce63d2bab`

The execution branch starts from that checkpoint and adds only Codex execution
instructions/scripts/results. Do **not** merge this branch into `main` during
the run.

The authoritative frozen contracts are already in the repository:

- `CODEX_START_HERE.md`
- `docs/TNQC_V5_LINKED_NATIVE_EXECUTION_FREEZE_20260921.md`
- `docs/TNQC_V5_SUPPORT_COVERAGE_GATE_20260921.md`
- `evidence/TNQC_V5_IMPLEMENTATION_MANIFEST_20260921.json`

## 1. Hard prohibitions

Do not edit, tune, or regenerate any manifest-locked source/method/evaluator
file before or after seeing House results.

In particular, do **not** change:

- TNQC equations;
- q_aff or q_ord;
- final-leaf candidate definition;
- free-cell hypothesis measure;
- support-coverage gate;
- evidence clipping or exponential tilt;
- 300-s budget;
- House01/02/03 or seeds 0/1;
- source truth coordinates;
- `stepsSourceUpdate=3`;
- native PMFS parameters;
- top-5% ExpectedValue endpoint;
- 10% pooled GO threshold;
- 4/6 improved-pair threshold;
- 25% worst-degradation threshold;
- false-confident-collapse rule;
- any manifest-locked file.

If the result is HOLD, **record HOLD and stop**. Do not tune and rerun V5.

If an integrity audit is INVALID, **record INVALID and diagnose the execution
problem only**. Do not modify the scientific method to make the audit pass.

Do not commit VM scenario data, ROS build directories, large binaries,
candidate map .f32 files, or the full context bank.

## 2. Do not trust memory; verify before running

Run exactly:

```bash
git fetch origin
git checkout codex/tnqc-v5-300s-offline-20260921
git reset --hard origin/codex/tnqc-v5-300s-offline-20260921
git status --short
git log -1 --oneline
```

The working tree must be clean before execution.

Then use the supplied recorder:

```bash
bash codex/run_tnqc_v5_300s_and_record.sh
```

Do not manually substitute another TNQC runner.

## 3. What the recorder must do

The recorder is intentionally strict. It must:

1. confirm the branch name;
2. confirm the frozen checkpoint is an ancestor;
3. record Git HEAD and working-tree status;
4. run the manifest verifier;
5. check the required VGR launch/scenario paths;
6. run the authoritative 300-s offline command with a fresh /dev/shm run root;
7. capture stdout/stderr and the real runner exit code;
8. preserve HOLD (exit 10) as a valid scientific outcome;
9. copy compact per-case evidence into
   `codex_results/tnqc_v5_300s_20260921/`;
10. generate a machine-readable summary and SHA256 list.

The authoritative runner itself performs the frozen VM preflight:

- manifest byte verification;
- complete `ros2_package` tree SHA check;
- clean source-tree requirement;
- Python syntax checks;
- full synthetic fixed-trajectory replay test;
- shell syntax checks;
- standalone TNQC C++ core compile/run;
- clean Release colcon build;
- algorithm/linked-native endpoint provenance;
- six House/seed native 300-s runs;
- V7 linked-native fixed-trajectory replay;
- V6 aggregate.

## 4. Exit-code interpretation

For `codex/run_tnqc_v5_300s_and_record.sh`:

- 0: aggregate GO.
- 10: aggregate HOLD. This is a valid scientific result; do not rerun with
  changed equations/thresholds.
- any other nonzero code: execution/infrastructure failure. Diagnose without
  changing the frozen method.

The recorder still writes the available audit files before returning.

## 5. Required post-run review

Before pushing results, inspect:

`codex_results/tnqc_v5_300s_20260921/RESULTS_SUMMARY.md`

and

`codex_results/tnqc_v5_300s_20260921/results_summary.json`.

For all six cases, verify that the summary reports:

- native posterior reconstruction audit;
- linked-native C++ endpoint audit;
- endpoint engine =
  `gsl_utils_expected_value_linked_native_v1`;
- replay contract =
  `TNQC_VGR_FIXED_TRAJECTORY_300S_REPLAY_V7_LINKED_NATIVE_ENDPOINT`;
- candidate scope =
  `final_partition_leaf_candidates_free_cell_measure_support_coverage_weighted`;
- native and TNQC fused 300-s top-5% errors;
- selected final source-update simulation time;
- final-leaf candidate count;
- support-coverage gate strength/coverage;
- Python-vs-linked-C++ tie diagnostic.

Also verify aggregate contract:

`TNQC_VGR_FIXED_TRAJECTORY_300S_GATE_V6_LINKED_NATIVE_ENDPOINT`.

If any field is absent, do not invent it. State that it is absent.

## 6. Upload only to this branch

After the run, do:

```bash
git status --short
git add codex_results/tnqc_v5_300s_20260921
git diff --cached --stat
git diff --cached --name-only
```

The staged paths must be only under:

`codex_results/tnqc_v5_300s_20260921/`

If any source, manifest, docs, workflow, or runner file is staged, unstage it
and investigate why.

Then:

```bash
git commit -m "evidence(tnqc): record frozen V5 300s Codex batch"
git push origin codex/tnqc-v5-300s-offline-20260921
```

Do not push to `main`.

## 7. What to report back

Report exactly:

- branch name and final commit SHA;
- recorder exit code;
- aggregate `valid`;
- aggregate `verdict`;
- `go_for_closed_loop`;
- pooled native error;
- pooled TNQC fused error;
- pooled improvement fraction;
- improved pairs count;
- worst pair degradation;
- false-confident-collapse cases;
- six paired native/fused errors;
- every failed integrity audit, if any;
- paths of uploaded evidence.

Do not state “TNQC works” from the 240-s concentration screen. The first
authoritative online-representation localization result is this 300-s gate.
