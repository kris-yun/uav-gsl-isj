# CSTAR — environment-first Codex handoff after VM review

Date: 2026-09-06  
Branch: `g3-cstar-revise-before-exec-20260906`  
Status: **IMPLEMENTATION_REGRESSION_PASS_ENVIRONMENT_NOT_PRODUCTION_ALIGNED**

This file is the active next-step handoff. It supersedes any older instruction
that starts formal M1/M2 training before the three-House input environment is
aligned, and it does not authorize the 12-run closed-loop matrix.

## 0. Decision

Keep CSTAR/PICR/CPO/PHS. Do not reopen innovation search and do not tune GMRF.
The next gate is the shared input environment:

`geometry + coordinate frame + local wind direction/position/time + gas/pose clock + route frame/free-space`.

Only after all H01/H02/H03 pass the environment alignment audit may formal
controlled M1/M2/M3 assets be accepted.

## 1. Locate the real VM checkout; do not assume the obsolete path

The previously documented `/home/zyc/gsl_ws/src/GasSourceLocalization` does not
exist on the reviewed VM. First locate a real checkout:

```bash
set -euo pipefail
BRANCH=g3-cstar-revise-before-exec-20260906

# If already inside any checkout, this command may find it. Otherwise the
# reviewed old checkout /home/zyc/CTPI_G2_M12_SEED12_20260905/repo is one
# candidate, but do not overwrite it if it contains unrelated work.
LOCATOR=/tmp/cstar_locate_vm_repo.sh
# obtain tools/cstar_locate_vm_repo.sh from the branch or use an already fetched copy
REPO=$(bash "$LOCATOR")
echo "REPO=$REPO"
git -C "$REPO" remote get-url origin
git -C "$REPO" rev-parse HEAD
```

Preferred implementation: create a clean worktree or clean clone from the
revision branch rather than changing the archived old experiment checkout in
place.

After the branch is available locally:

```bash
cd "$REPO"
git fetch origin
git checkout g3-cstar-revise-before-exec-20260906
git pull --ff-only origin g3-cstar-revise-before-exec-20260906
git status --short
git rev-parse HEAD
```

If the checkout is not clean, preserve it and make a separate worktree.

## 2. Re-run all tests because the environment gate was added after ce3a0dd

The earlier VM regression at `ce3a0dd` is valid implementation evidence for that
snapshot. The branch now also contains an environment validator/selftest, so run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
python3 experiments/ctpi_cstar/run_reference_selftests.py
```

Required final line:

`CSTAR_ALL_REFERENCE_ENVIRONMENT_AND_REVIEW_SELFTESTS PASS`

Record Python/Torch versions and final git SHA.

Do not continue if the new environment selftest fails.

## 3. Freeze one common environment contract

Read:

- `experiments/ctpi_cstar/CSTAR_ENVIRONMENT_ALIGNMENT_CONTRACT_V1.json`
- `experiments/ctpi_cstar/validate_environment_alignment.py`
- `closed_loop/ctpi/cstar_local_wind.py`
- `closed_loop/ctpi/cstar_environment_runtime_probe.py`
- `closed_loop/ctpi/ctpi_v2_ingress.py`

Runtime CSTAR wind semantics are frozen:

- frame = `map`;
- direction = VGR-published **downwind** direction;
- vector = `(u,v)=speed*(cos(theta),sin(theta))` in m/s;
- observation position = robot pose at the **same timestamp**;
- cadence = 0.2 s / 200000000 ns;
- no `+pi` conversion;
- no later TF lookup to infer wind position;
- no full wind field required;
- GMRF is not required.

The old `gmrf_node.cpp` semantics and old launch subscription may remain in the
legacy tree, but they must not be the CSTAR shared input path.

## 4. H01 geometry: preserve the diagnostic reference but re-prove actual loading

Known review reference only:

- navigation height: z=0.3 m;
- reviewed image SHA-256:
  `7a0eb65e47428b898be7e24ac7f3519c4afdb7a6cdc861e59896955236ac49b4`;
- resolution: 0.1 m;
- origin: `(-7.55,-7.88)`;
- historical diagnostic had 1200 wind positions all legal.

These facts do **not** prove the new loader uses that map.

For H01, freeze the actual YAML/image pair and run the new runtime input probe.
The resulting audit's map hashes must match the frozen H01 geometry manifest.

## 5. H02/H03 geometry: perform the same navigation-height derivation and validation

Do not reuse an arbitrary `occupancy.yaml` merely because an old launch file
points to it.

For each H02 and H03:

1. identify the authoritative 3-D/house occupancy source and navigation height;
2. derive/export the navigation-height 2-D occupancy slice using the same
   coordinate convention used for H01;
3. freeze YAML + PGM path, SHA-256, resolution, origin, width, height and
   `geometry_identity`;
4. verify YAML relative `image:` resolves to the exact PGM being frozen;
5. create candidate/free-space probe coordinates from the actual candidate
   generator;
6. create route probe coordinates from the actual navigation route interface;
7. obtain wind-observation positions from the runtime input probe below;
8. do not proceed until all three coordinate classes map to free cells.

If the authoritative H02/H03 geometry source is ambiguous, stop as
`BLOCKED_ENVIRONMENT_GEOMETRY_IDENTITY` rather than selecting a convenient map.

## 6. Run the direct environment runtime probe for each House

Run a short infrastructure-only House session. No PICR/CPO/PHS model is loaded
and no GMRF prediction is required.

Example shape:

```bash
HOUSE=H01
GEOM_ID=<frozen_geometry_identity>
MAP_YAML=<exact_navigation_height_yaml>
MAP_IMAGE=<exact_navigation_height_pgm>
OUT=<fresh evidence directory>/$HOUSE
mkdir -p "$OUT"

python3 closed_loop/ctpi/cstar_environment_runtime_probe.py \
  --house "$HOUSE" \
  --geometry-identity "$GEOM_ID" \
  --git-sha "$(git rev-parse HEAD)" \
  --map-yaml "$MAP_YAML" \
  --map-image "$MAP_IMAGE" \
  --output "$OUT/CSTAR_RUNTIME_INPUT_LOAD_AUDIT_V1.json" \
  --wind-position-csv "$OUT/wind_observation_positions.csv" \
  --frame-jsonl "$OUT/aligned_input_frames.jsonl" \
  --required-aligned-frames 8
```

Use the actual topic names if they differ from defaults, but document them.

Repeat independently for H01/H02/H03.

Required:

- pose frame = map;
- gas units = ppm;
- wind frame = map;
- local wind decoder = downwind u,v with no +pi;
- strict stamped ingress accepts consecutive aligned frames;
- map YAML/image hashes are in the audit;
- `old_native_gmrf_anemometer_subscription_used=false` for this CSTAR path.

This is an environment probe only, not a model smoke or performance run.

## 7. Candidate and route probe files

For each House create CSV files with at least columns `x,y` for:

- `candidate`: the real candidate-source domain used by the planned formal data/model;
- `route`: actual navigation path points or preregistered endpoint+dwell points;
- `wind_observation`: use the probe-generated wind positions CSV (`x,y` columns are already present).

Do not invent straight current-to-goal lines through obstacles.

Hash every CSV before adding it to the environment manifest.

## 8. Build `CSTAR_ENVIRONMENT_ALIGNMENT_V1.json`

The realised manifest must contain:

- exact repo root and git SHA;
- frozen common runtime contract;
- code identities for:
  - `closed_loop/ctpi/ctpi_v2_ingress.py`;
  - `closed_loop/ctpi/cstar_local_wind.py`;
- H01/H02/H03 map YAML/image hashes and geometry metadata;
- the three free-space probe kinds per House;
- each House's runtime-load-audit path/hash;
- one identical non-empty `shared_arm_input_identity` token for A0/F00/F10/F11.

The shared identity means all later comparison arms receive the corrected same
geometry/wind/time interface. It is forbidden to fix inputs only for CSTAR while
leaving Classic PMFS on a known mismatched map/wind interface.

## 9. Run the environment validator

```bash
python3 experiments/ctpi_cstar/validate_environment_alignment.py \
  --manifest /path/to/CSTAR_ENVIRONMENT_ALIGNMENT_V1.json \
  --output /path/to/CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1.json
```

Required exact verdict:

`CSTAR_ENVIRONMENT_ALIGNMENT=PASS`

The validator checks actual file hashes, YAML->PGM identity, resolution/origin,
PGM dimensions, world->pixel conversion, free-space legality for candidate /
wind / route points, runtime loader identity, direct-downwind convention,
cadence and shared arm identity.

If any House fails, stop. Do not enter formal M1/M2 training.

## 10. Only after environment PASS: controlled asset audit

The controlled asset contract has been tightened. Read:

`experiments/ctpi_cstar/CSTAR_CONTROLLED_CAUSAL_ASSET_CONTRACT_V1.json`

Every controlled manifest must now reference the exact environment alignment
audit and its SHA-256.

Each row must include `geometry_identity` and `realization_id`.

The validator now prevents:

- source pairing across different Houses/geometries;
- same physical realization split across train/heldout under different prefix
  filenames;
- empty declared splits;
- M1/M2 rows whose geometry identity differs from the passed House environment;
- outcome-realization leakage across M2 splits.

Run:

```bash
python3 experiments/ctpi_cstar/validate_controlled_assets.py \
  --manifest /path/to/CSTAR_CONTROLLED_CAUSAL_ASSET_V1.json \
  --output /path/to/CSTAR_CONTROLLED_CAUSAL_ASSET_AUDIT_V1.json
```

Only an environment-bound controlled-asset PASS may feed the formal M1/M2
producer work.

## 11. Formal M1/M2 work remains limited validation, not 12-run

After Sections 2-10 pass, continue with the previously frozen limited-validation
requirements:

### M1

Implement the formal `CSTAR_M1_CONTROLLED_CAUSAL_GATE_V1` producer with a real
checkpoint and all destructive controls:

- matched unconstrained temporal encoder;
- context-only baseline;
- zS zero/mask;
- zS matched-context permutation;
- source-label permutation;
- no-intervention-loss ablation;
- low-information entropy/abstention diagnostics.

### M2

Implement `CSTAR_M2_SOURCE_DIVERSE_PREDICTIVE_GATE_V1` with real checkpoint and
three providers:

- causal Gaussian plume + audited FOPDT;
- verified conservative-physics prior;
- learned CPO.

Formal M2 routes must be decision-locked or controlled open-loop routes. A
retrospective adaptive path is not `do(route)`.

### M3

Use only genuine same-context multi-route counterfactual outcomes and retain the
destructive route-law shuffle.

## 12. Stop point

Even if environment and limited M1/M2/M3 gates are promising, stop before:

- production `cstar_v1` performance smoke;
- H01/H02/H03 x seed12 x A0/F00/F10/F11 12-run.

Push a finite validation bundle first.

Current advancement ladder is:

`IMPLEMENTATION_REGRESSION_PASS`
-> `ENVIRONMENT_ALIGNMENT_PASS`
-> `CONTROLLED_ASSET_PASS`
-> `LIMITED_SCIENTIFIC_VALIDATION_REVIEW`
-> only after review: `READY_FOR_PRODUCTION_SMOKE`
-> only after smoke review: `READY_FOR_12RUN`.

No stage may be skipped.
