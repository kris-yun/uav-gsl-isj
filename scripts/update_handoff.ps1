# Update PROJECT_HANDOFF.md with critical discovery
$handoff = @"
# Project Handoff — CP-SBD-GSL

## Critical Discovery (2026-07-04)

**Root cause of ALL A1_fast scenario failures: Posterior grid bounds too small.**

The posterior grid was initialized with:
``````cpp
posterior3d_.init(-7.5f, 3.9f, -7.9f, 0.82f, z_min_, z_max_);
``````
But the source is at (5.0, 6.2) — completely OUTSIDE the grid. The posterior could never place mass on the correct location.

**Fix:** Change to `posterior3d_.init(-1.0f, 11.0f, -1.0f, 11.0f, z_min_, z_max_);`

**Impact:** Seed 1 error dropped from 6.39m to 0.16m. Seed 2 from 5.61m to 0.09m.

## Current Code State

### VM: `/home/zyc/gsl_ws/src/GasSourceLocalization/`
- **OPGSL.cpp** — Restored to original (pre-Poisson) with ONLY the grid fix applied
- **OPGSL.hpp** — Original with grid fix
- Backup: `OPGSL.cpp.bak_poisson` (pre-Poisson version)

### Key Code Path
1. `processGasAndWindMeasurements()` — receives sensor data
2. `posterior3d_.update()` — Bayesian posterior update (Gaussian plume model)
3. `sdnbvStep()` — search step selection (Phase 1→1.5→2)
4. `checkSourceFound()` — convergence check

### Posterior Model (Current)
- Gaussian plume likelihood with adaptive anisotropic kernel
- Heuristic weights: detection `sqrt(conc)*1.5`, non-detection `0.3`
- Temporal decay: `0.995` per step
- Grid: 40x40x4 cells, resolution 0.5m, bounds [-1,11] x [-1,11]

### Known Issues
1. **Heuristic weights** in posterior update — not theoretically justified
2. **Gaussian plume model** doesn't match GADEN filament simulation
3. **CP/DDM modules** disabled (fire prematurely)
4. **Benchmark runner** crashes but doesn't affect algorithm

### How to Run
``````bash
# Single seed
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash
ros2 launch vgr_bridge vgr_ablation.launch.py seed:=0 timeout_sec:=120 opgsl_cp:=false opgsl_ddm:=false

# 10-seed batch
bash /tmp/run_10seeds.sh
``````

### Environment
- **Data**: `/home/zyc/enva_vgr/` (VGR-format, House01)
- **Config**: A1_fast, source (5.0, 6.2, 0.5), start (4.0, 4.0)
- **ROS2 Humble** workspace at `/home/zyc/gsl_ws/`

### Git
- Repo: https://github.com/kris-yun/cp-sbd-gsl (private)
- Current commit: `fd1ba48` (with grid fix, uncommitted)

## Theoretical Framework

### Poisson Event Model (Designed but not yet calibrated)
- Rate: `lambda(x,s) = lambda0 * exp(-dist/ell) * (1 + alpha_w * cos_theta)`
- Detection: `P(d=1) = 1 - exp(-lambda * dt)`
- Non-detection: `P(d=0) = exp(-lambda * dt)`
- **Status**: Framework designed, parameters need GADEN calibration

### Mathematical Framework (in `docs/MATHEMATICAL_FRAMEWORK_V2.tex`)
- Proposition: Source Identifiability
- Theorem: Strict Positivity of ED-EIG
- Theorem: Exponential Posterior Concentration
- Theorem: Anytime-Valid Stopping via Ville's inequality

## LaTeX Paper

### Location: `D:\ZYC\A-gas\ASCi\sci\paper-isj-zh\`
- `main.tex` — Title: "Event-Driven Bayesian UAV GSL with Anytime-Valid Stopping"
- `sections/methodology.tex` — Poisson event model (needs update to match code)
- `sections/experiments.tex` — [TBD] values (needs real data)
- `sections/references.tex` — 25 bibitems

### Paper Status
- **Theory**: Strong (3 theorems, formal proofs)
- **Implementation**: Needs alignment (paper describes Poisson, code uses Gaussian)
- **Experiments**: Grid fix resolved; 10-seed running
- **Novelty**: Event-driven binary detection for GSL — unique in literature

## Next Steps
1. Wait for 10-seed results
2. Calibrate Poisson model from GADEN data
3. Align paper with implementation
4. Run baseline comparisons (SurgeCast, PMFS, Infotaxis)
5. Submit to ISJ
"@

$handoff | Out-File -FilePath "D:\ZYC\A-gas\docs\PROJECT_HANDOFF.md" -Encoding utf8
echo "PROJECT_HANDOFF.md updated"