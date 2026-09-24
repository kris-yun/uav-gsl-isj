# Gate 1A — VM execution handoff

Date: 2026-09-24

The scientific protocol is already frozen. Do not change candidate positions,
probe points, target realizations, prediction seeds, score, or thresholds after
running.

## One command

```bash
cd /path/to/uav-gsl-isj
git fetch origin
git checkout research/causal-biorthogonal-green-v1
git pull --ff-only
bash research/causal_biorthogonal_green_v1/run_gate1a_exact_forward_vm.sh
```

The runner is resume-safe. If interrupted, rerun the same command; valid
completed 300-value prediction vectors are skipped.

## Expected frozen inputs

- GADEN binary:
  `/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator`
- target W2 bank:
  `/home/zyc/c0_5_real_gaden_bank_20260923`
- W2:
  `/mnt/hgfs/workspace/GADEN_files/scenarios/House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind`
- extractor:
  `/home/zyc/rmfe_filament_extractor_omp`

The runner verifies their frozen hashes before doing work.

## What it will run

- 630 free arbitrary PMFS source-grid locations;
- prediction seeds `2026092401` and `2026092402`;
- exact 300 s W2 GADEN physics;
- 30 source-blind probes x 10 frozen times;
- targets `S2_W2_A` and `S2_W2_B`.

Temporary raw GADEN realizations are deleted after each successful probe-vector
extraction. Compact predictions/logs stay under
`/home/zyc/bigreen_gate1a_exact_20260924`.

## Result files that must be committed unchanged

- `evidence/causal_biorthogonal_green_v1/GATE1A_EXACT_FORWARD_RESULT_20260924.json`
- `evidence/causal_biorthogonal_green_v1/GATE1A_EXACT_FORWARD_20260924.log`
- `evidence/causal_biorthogonal_green_v1/GATE1A_SHA256_20260924.txt`
- `evidence/causal_biorthogonal_green_v1/S2_W2_A_all_source_scores.csv`
- `evidence/causal_biorthogonal_green_v1/S2_W2_B_all_source_scores.csv`

Commit command after the runner finishes:

```bash
git add evidence/causal_biorthogonal_green_v1/
git commit -m "evidence: record Bi-Green Gate 1A exact-physics result"
git push origin research/causal-biorthogonal-green-v1
```

## Frozen decision

PASS only if both targets have:

- mean(C,D) truth rank <= 3;
- C-only truth rank <= 10;
- D-only truth rank <= 10.

Otherwise the result is
`GATE1A_FAIL_STOP_SOURCE_TO_SENSOR_GREEN_FAMILY`.

Do not start Gate 1B, Gate 2, ROS, or closed-loop experiments unless Gate 1A is
a frozen PASS.
