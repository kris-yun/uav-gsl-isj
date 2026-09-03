# Codex resume — CTPI M2 TSDC fresh confirmation

This file supersedes any in-progress local selector/manifest edits from the paused Codex session.
Do not redesign M2 and do not write a new selector, manifest builder, materializer, pregen auditor, or evaluator.

Authoritative repository: `kris-yun/uav-gsl-isj`

Authoritative branch: `research/ctpi-m2-tsdc-committor-20260903`

Minimum handoff anchor that MUST be in ancestry: `7675c1a3c5af5be89a596aa44a1a35e3de33d933`

The user/ChatGPT handoff has already completed the non-VM engineering. Codex's remaining role is VM-native execution only.

## 1. Enter the correct repository and freeze the worktree

The project has more than one Git repository. Do not use the root `cp-sbd-gsl` origin.
Use the worktree whose origin is `uav-gsl-isj`, fetch the authoritative branch, and create a fresh isolated worktree at the exact current remote HEAD.

Before execution require:

```bash
git merge-base --is-ancestor 7675c1a3c5af5be89a596aa44a1a35e3de33d933 HEAD
git status --porcelain
```

The second command must be empty before any generated run artifact is created.

Verify frozen M2:

```bash
test "$(sha256sum experiments/cg_pc_ctt/ctpi_m2_tsdc_frozen_v0.py | awk '{print $1}')" = \
  854a2fc8513201cdb2ae497a62c0cd3c5fa09fdae2f1bc309ad594a8b1aaacf7
python experiments/cg_pc_ctt/ctpi_m2_tsdc_frozen_v0.py
```

Required: `CTPI_M2_TSDC_FROZEN_V0_SELFTEST=PASS`.

The paused session already reproduced the full 900-event/60-world DEV audit. If its saved Phase-A audit is still present and reports the frozen hashes plus beta delta `4.44e-16`, preserve it and do NOT waste time rerunning the full DEV analysis. If that evidence is unavailable, rerun the committed DEV audit once. Old 60 worlds remain `DEV_SPENT` either way.

## 2. Fixed VM inputs

```bash
STAGE1=/home/zyc/CPIR_FACTORIAL_ROUTE_DIAGNOSTIC_20260901_e2bb4a0_R3/01_STAGE1
PLACEMENT=/home/zyc/PF_DEI_V3_REGION_SUPPORT_20260828/frozen_region_placement_manifest.json
BANK=/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1
REGISTRY=docs/CTPI_M2_TSDC_USED_ASSET_REGISTRY_V0.json
FROZEN=experiments/cg_pc_ctt/ctpi_m2_tsdc_frozen_v0.py
```

Hard hashes:

- H01 Stage1 NPZ: `1552b799aa808d84a83a9375d7fed82b4495e2ee1ac6bd8f9fdda1424d21c1b5`
- H02 Stage1 NPZ: `8cafbd2ff8e190ce63a2b9bcb69e47449131d64cd5ef0f8de4be1310fb6b6310`
- H03 Stage1 NPZ: `7c55a6c6976aeec0d40e1a66ada290c51361ca4f2c631a331c3cf479a2cac91a`
- frozen PF-DEI V3 placement manifest: `2dfe8bf70cc5dd191db8659cfc66ed9934927b69d0b6798b9a6b5062e1dd959f`

Do not substitute `source_region_3d_support_manifest.csv` or a quadtree center for physical source XYZ.

## 3. Runtime identity

Use exactly:

```bash
export OMP_NUM_THREADS=4
export OMP_DYNAMIC=FALSE
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export PYTHONHASHSEED=0
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
export LD_LIBRARY_PATH="/opt/ros/humble/lib:/home/zyc/PF_DEI_V3_GADEN_BUILD/install/lib:/home/zyc/PF_DEI_V3_GADEN_BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}"
```

Create a fresh run root and run:

```bash
python tools/ctpi_m2_runtime_preflight.py \
  --bank-root "$BANK" \
  --output "$RUN_ROOT/00_PREGEN/RUNTIME_IDENTITY.json"
```

Required: `CTPI_M2_GENERATOR_RUNTIME=PASS`.

## 4. Reproduce the already-frozen fresh source selection

Do NOT edit the selector.

```bash
python tools/ctpi_m2_tsdc_select_fresh_sources.py \
  --stage1-root "$STAGE1" \
  --used-asset-registry "$REGISTRY" \
  --output "$RUN_ROOT/00_PREGEN/FRESH_SELECTION.json"
```

Required terminal:

`CTPI_M2_TSDC_FRESH_SOURCE_SELECTION=PASS`

Required output SHA-256, exactly:

`0d4e6162863ca2a07bf93ef74f178b1d4ad5d058ab787345d291362fd8e9f431`

If it differs, STOP. Do not choose another carrier set.

The expected human-readable carrier/route/U summary is frozen in:

`docs/CTPI_M2_TSDC_FRESH_SOURCE_SELECTION_EXPECTED_V0.json`

The pooled expected K histogram is `[185,31,18,16,22,17,24,27,110]`; every House covers K=0..8 and uses routes 0..9 exactly once.

## 5. Freeze physical placements and fresh RNG BEFORE any outcome

First verify:

```bash
test "$(sha256sum "$PLACEMENT" | awk '{print $1}')" = \
  2dfe8bf70cc5dd191db8659cfc66ed9934927b69d0b6798b9a6b5062e1dd959f
```

Then:

```bash
python tools/ctpi_m2_tsdc_freeze_fresh_manifest.py \
  --selection "$RUN_ROOT/00_PREGEN/FRESH_SELECTION.json" \
  --placement-manifest "$PLACEMENT" \
  --used-asset-registry "$REGISTRY" \
  --output "$RUN_ROOT/00_PREGEN/FRESH_WORLD_MANIFEST.json"
```

Required: `CTPI_M2_TSDC_FRESH_WORLD_FREEZE=PASS`.

This manifest contains exactly 30 formal worlds plus ONE disposable H01 smoke. It must exist and be SHA-hashed before the smoke is generated. Predictive bank generation is forbidden.

## 6. TSDC one-world adapter selftest and deterministic smoke

```bash
python tools/ctpi_m2_tsdc_materialize_world.py --selftest
```

Required: `CTPI_M2_TSDC_ONE_WORLD_ADAPTER_SELFTEST=PASS`.

Read the smoke world id from `FRESH_WORLD_MANIFEST.json`. Materialize that exact disposable smoke twice into two fresh directories using `--allow-disposable-smoke`, the same world manifest, and the same runtime report. Do not use either smoke output in the formal 30-world dataset.

Both smoke runs must PASS and have identical `payload_sha256`.

## 7. Obtain pregen authorization

After the two smoke runs, and still before any formal fresh outcome, run:

```bash
python tools/ctpi_m2_tsdc_finalize_pregen.py \
  --selection "$RUN_ROOT/00_PREGEN/FRESH_SELECTION.json" \
  --world-manifest "$RUN_ROOT/00_PREGEN/FRESH_WORLD_MANIFEST.json" \
  --runtime-report "$RUN_ROOT/00_PREGEN/RUNTIME_IDENTITY.json" \
  --used-asset-registry "$REGISTRY" \
  --frozen-module "$FROZEN" \
  --materializer-code tools/ctpi_m2_tsdc_materialize_world.py \
  --smoke-a "$RUN_ROOT/00_PREGEN/SMOKE_A/WORLD_AUDIT.json" \
  --smoke-b "$RUN_ROOT/00_PREGEN/SMOKE_B/WORLD_AUDIT.json" \
  --implementation-commit "$(git rev-parse HEAD)" \
  --output "$RUN_ROOT/00_PREGEN/TSDC_PREGEN_AUDIT.json"
```

Required: `CTPI_M2_TSDC_PREGEN=PASS`.

No formal world may be generated without that marker.

## 8. Materialize exactly 30 formal worlds

For each `world_id` in `formal_worlds`, sequentially call:

```bash
python tools/ctpi_m2_tsdc_materialize_world.py \
  --world-manifest "$RUN_ROOT/00_PREGEN/FRESH_WORLD_MANIFEST.json" \
  --runtime-report "$RUN_ROOT/00_PREGEN/RUNTIME_IDENTITY.json" \
  --world-id "$WORLD_ID" \
  --authorization "$RUN_ROOT/00_PREGEN/TSDC_PREGEN_AUDIT.json" \
  --output "$RUN_ROOT/01_WORLDS/$WORLD_ID"
```

Rules:

- exactly 30/30 worlds;
- sequential execution is preferred; no hidden parallel plume generation;
- each world must have `CTPI_M2_TSDC_WORLD_MATERIALIZATION=PASS`;
- 1500 physical samples, 1502 measured samples, 15 events;
- bank before/after identity unchanged;
- no source metadata enters M1/planner runtime;
- no retries with a different seed after a scientifically valid completed world;
- no M3/C++/ROS/closed-loop.

## 9. One-shot evaluator — already written, do not edit after outcomes

After 30/30 materialization completes, run exactly once:

```bash
python tools/ctpi_m2_tsdc_evaluate_fresh_confirm.py \
  --world-root "$RUN_ROOT/01_WORLDS" \
  --world-manifest "$RUN_ROOT/00_PREGEN/FRESH_WORLD_MANIFEST.json" \
  --selection "$RUN_ROOT/00_PREGEN/FRESH_SELECTION.json" \
  --stage1-root "$STAGE1" \
  --frozen-module "$FROZEN" \
  --pregen-authorization "$RUN_ROOT/00_PREGEN/TSDC_PREGEN_AUDIT.json" \
  --output-dir "$RUN_ROOT/02_GATE"
```

The evaluator contains NO fitting routine. It implements the preregistered conjunctive Gate unchanged.

Terminal outcomes only:

- `CTPI_M2_TSDC_FRESH_CONFIRM=PASS`
- `CTPI_M2_TSDC_FRESH_CONFIRM=NO_GO`

On NO-GO: stop immediately and preserve evidence; do not tune from the fresh outcomes.

On PASS: authorize ONLY the M3 offline action Gate. C++/ROS/formal closed-loop remain forbidden.

## 10. Never do these on resume

Do not:

- recreate selector/manifest/evaluator code;
- change TSDC beta/features/state timing;
- use House ID, route ID, source ID embedding, truth, rank/error/reward;
- use transit/arrival/pre-stop future measured state as `M_decision`;
- reuse the old 60 `DEV_SPENT` worlds as confirmation;
- regenerate the predictive bank;
- start M3, C++, ROS or closed-loop before M2 fresh PASS.

If any frozen hash, exact selection SHA, placement SHA, runtime identity, smoke determinism, or pregen check fails, stop and report the blocker rather than repairing it from outcomes.
