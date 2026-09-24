# CODEX HANDOFF — Bi-Green Gate 1A Exact-Physics Validation

Date: 2026-09-24  
Branch: `research/causal-biorthogonal-green-v1`  
Status: **EXECUTE FROZEN GATE ONLY — DO NOT MODIFY SCIENTIFIC CONTRACT**

## Mission

Run the already-frozen Gate 1A exact-physics identifiability experiment on the VM.

The scientific question is only:

> Across >=143 arbitrary source hypotheses, can the exact frozen House02 W2 transport physics recover the true source from source-blind observations?

Do **not** implement Neural Green, adjoint, biorthogonal compression, ROS, PMFS closed loop, or any new rescue model in this task.

## Hard no-change rules

Do not change any of the following after reading results:

- source bank;
- source truth;
- W2 wind;
- target realizations;
- target seeds;
- prediction seeds;
- probe locations;
- snapshot indices;
- score definition;
- PASS/FAIL thresholds;
- GADEN parameters;
- source grid resolution.

If execution reveals an infrastructure bug, fix only the bug, document it, and rerun under the same scientific contract.

Do not tune on S2_W2_A/B.

## Frozen branch and code

```bash
cd /path/to/uav-gsl-isj
git fetch origin
git checkout research/causal-biorthogonal-green-v1
git pull --ff-only
git status --short
```

Require a clean worktree before execution.

Record:

```bash
git rev-parse HEAD
git branch --show-current
```

Expected branch:

`research/causal-biorthogonal-green-v1`

## Required VM assets

The runner expects these defaults:

- GADEN binary:
  `/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator`
- target W2 bank:
  `/home/zyc/c0_5_real_gaden_bank_20260923`
- canonical scenario:
  `/mnt/hgfs/workspace/GADEN_files/scenarios`
- spatial extractor:
  `/home/zyc/rmfe_filament_extractor_omp`

Do not substitute another binary, target bank, wind, occupancy, or extractor unless the runner itself reports the frozen path is unavailable. If anything is missing, STOP and report the missing asset rather than silently replacing it.

## Mandatory wind-alignment audit

This Gate must not mix the historical HCMC W1 trajectory wind with the W2 target/predictor contract.

The historical HCMC replay files are used **only** for the geometry-only PMFS candidate manifest. Their W1 (`3,5-1_fast`) wind/plume traces are excluded from every Gate-1A score.

Before launching the batch, verify and record that:

- target `S2_W2_A` provenance is W2 `3,5-1_slow`;
- target `S2_W2_B` provenance is W2 `3,5-1_slow`;
- the forward runner uses exactly:
  `House02/gas_simulations/3,5-1_slow/.../wind`;
- wind iterations 1..10 exist and their SHA-256 values are recorded.

Run:

```bash
W2="/mnt/hgfs/workspace/GADEN_files/scenarios/House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"

for i in $(seq 1 10); do
  test -f "$W2/wind_iteration_$i" || { echo "MISSING W2 iteration $i"; exit 41; }
done

{
  echo "W2_PATH=$W2"
  sha256sum "$W2"/wind_iteration_{1..10}
  echo "--- S2_W2_A manifest ---"
  cat /home/zyc/c0_5_real_gaden_bank_20260923/S2_W2_A/manifest.tsv
  echo "--- S2_W2_B manifest ---"
  cat /home/zyc/c0_5_real_gaden_bank_20260923/S2_W2_B/manifest.tsv
} | tee evidence/causal_biorthogonal_green_v1/GATE1A_WIND_ALIGNMENT_20260924.txt
```

If either target manifest indicates `3,5-1_fast` / W1, or a different wind contract, **STOP before simulation** and report:

`GATE1A_INFRA_STOP_WIND_CONTRACT_MISMATCH`

Do not substitute another target or wind field.

## Preflight-only check

Before launching the full batch, inspect:

```bash
sed -n '1,260p' evidence/causal_biorthogonal_green_v1/GATE1A_EXACT_PHYSICS_FREEZE_20260924.md
sed -n '1,260p' evidence/causal_biorthogonal_green_v1/GATE1A_PREFLIGHT_20260924.md
sed -n '1,260p' evidence/causal_biorthogonal_green_v1/NOVELTY_BOUNDARY_20260924.md
```

Then syntax-check only:

```bash
python3 -m py_compile   research/causal_biorthogonal_green_v1/prepare_gate1a_bank.py   research/causal_biorthogonal_green_v1/extract_gate1a_probe_vector.py   research/causal_biorthogonal_green_v1/rank_gate1a_exact_forward.py
bash -n research/causal_biorthogonal_green_v1/run_gate1a_exact_forward_vm.sh
```

Do not run ad-hoc experimental variants.

## Execute Gate 1A

Run exactly:

```bash
bash research/causal_biorthogonal_green_v1/run_gate1a_exact_forward_vm.sh
```

The runner is resume-safe. If interrupted, rerun the exact same command.

Do not delete:

`/home/zyc/bigreen_gate1a_exact_20260924`

until the review package has been created and hashed.

## Frozen scientific contract

The source bank is constructed from the frozen House02 PMFS quadtree manifest.

Expected preflight:

- 164 quadtree leaves;
- 631 deduplicated PMFS support cells;
- 630 free arbitrary source positions after occupancy filtering;
- exact truth support cell: `pmfs_3_34`;
- exact truth coordinate approximately:
  `(-4.34273, 2.89912, 0.20)`.

Targets:

- `S2_W2_A`, target seed `2026092301`;
- `S2_W2_B`, target seed `2026092302`.

Prediction RNG seeds:

- `2026092401`;
- `2026092402`.

Observations:

- 30 source-blind geometry probes on the frozen **2x2 pooled grid**;
- each probe value is the mean of its corresponding 2x2 native 83x119 concentration block;
- 10 frozen W2 snapshot times;
- 300 observations per target.

Important: `points_xy` in the frozen M4 diagnostic are pooled-grid coordinates, not raw 83x119 indices. Do not reinterpret them as raw cells. The committed scripts already enforce the correct pooled observation operator.

Primary score:

[
E(s)=\frac{\|\bar c_s-y\|_2^2}{\|y\|_2^2+10^{-12}},
\qquad
\bar c_s=\tfrac12(c_s^{2026092401}+c_s^{2026092402}).
]

No amplitude fit.
No offset fit.
No source-dependent fit.

## Frozen PASS/STOP rule

PASS requires **both** S2_W2_A and S2_W2_B to satisfy:

- mean(C,D) true-source rank <= 3;
- prediction-seed C true-source rank <= 10;
- prediction-seed D true-source rank <= 10.

If any condition fails:

`GATE1A_FAIL_STOP_SOURCE_TO_SENSOR_GREEN_FAMILY`

Do not attempt rescue experiments.

If PASS:

`GATE1A_PASS_EXACT_PHYSICS_SOURCE_IDENTIFIABLE`

Still do not start Gate 1B until the result package is reviewed.

## Required integrity checks after execution

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path

p=Path("evidence/causal_biorthogonal_green_v1/GATE1A_EXACT_FORWARD_RESULT_20260924.json")
j=json.loads(p.read_text())
print(json.dumps({
    "decision": j["decision"],
    "source_count": j["source_count"],
    "truth_source_id": j["truth_source_id"],
    "targets": {
        k: {
            "truth_primary_rank": v["truth_primary_rank"],
            "truth_per_prediction_seed_rank": v["truth_per_prediction_seed_rank"],
            "gate_pass": v["gate_pass"],
        }
        for k,v in j["targets"].items()
    }
}, indent=2))
PY
```

Also verify prediction count:

```bash
for s in 2026092401 2026092402; do
  echo -n "seed $s: "
  find /home/zyc/bigreen_gate1a_exact_20260924/predictions/seed_$s     -maxdepth 1 -type f -name 'pmfs_*.npy' | wc -l
done
```

Expected: 630 for each seed.

## Commit exact evidence before packaging

Do not edit result JSON/CSV/log files manually.

```bash
git add evidence/causal_biorthogonal_green_v1/
git status --short
git commit -m "evidence: record Bi-Green Gate 1A exact-physics result"
git push origin research/causal-biorthogonal-green-v1
```

If there was a necessary infrastructure-only patch, commit that patch separately **before** the evidence commit, with an explicit explanation.

## Build review package for ChatGPT

After the evidence commit, run:

```bash
bash research/causal_biorthogonal_green_v1/package_gate1a_review.sh
```

The script prints:

- review ZIP/TAR path;
- byte size;
- SHA-256.

Upload that generated review package to ChatGPT.

## What to report back in chat

Report only:

1. branch;
2. final commit SHA;
3. Gate 1A decision;
4. source count;
5. truth rank for A mean/C/D;
6. truth rank for B mean/C/D;
7. review-package path;
8. review-package SHA-256;
9. any infrastructure-only deviation from the frozen runner.

Do not interpret the mechanism or start Gate 1B yourself. The next scientific decision is made only after independent review of the package.
