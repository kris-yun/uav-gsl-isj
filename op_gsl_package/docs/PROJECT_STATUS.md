# OPGSL Project Status & Context

> Last updated: 2026-06-30 | Git: 75ad04d (adaptive_altitude_gsl)

## 1. Project Definition & Goal

**Title**: UAV-based Gas Source Localization with Adaptive Altitude and Physics-Informed Forward Model

**Core Problem**: Given a UAV with a single gas sensor and anemometer, localize an unknown gas source in a 3D indoor environment with obstacles. The source height is unknown and must be estimated jointly with the horizontal position.

**Key Innovation (Target)**:
- Advection-diffusion forward model for Bayesian source localization
- EIG-driven adaptive altitude selection (the UAV actively chooses flight height)
- Robust to model misspecification (works when the forward model doesn't perfectly match reality)

**Target Venue**: Top robotics journal (TRO / RA-L) or conference (ICRA / IROS)

---

## 2. Current Status (2026-06-30)

### What Works
- **Coordinate system**: Fixed. Grid [0,10] × [0,10], phys = grid_index × 0.1, no offset. Verified PASS.
- **Forward model on synthetic data**: 0.10m error on pre-computed GADEN Env A grid (sufficient sampling).
- **EIG height estimation on synthetic data**: 0.34m ErrZ, converges to near-source heights.
- **Two-phase exploration**: 50-step random + entropy/MAP hybrid achieves 0.45m on GADEN Env A.
- **C++ integration**: Forward model compiled and integrated into WC_RIF_GSL.cpp with grid origin support.
- **3D forward model**: Works on subsampled grid (30780 cells), 0.10m error.

### What's Broken
- **Forward model on real VGR data**: 5-7m error. The Green's function peaks at the observation position, creating a self-reinforcing bias (MAP converges to robot position, not source).
- **GrGSL/SurgeCast baselines had ground-truth leakage**: Navigation used true source position. Fixed, but fair comparison shows ALL methods at 3-7m.
- **VGR gas detection at flight height**: Source at z=-0.3, flight at z=0.3 → gas below 0.1 ppm threshold → zero hits for sensor-dependent methods.
- **ROS2 benchmark runner**: SAISC-PF specific, crashes for PMFS/GrGSL/SurgeCast.

### Key Numbers (VGR House01, fair comparison, no GT leakage)
| Algorithm | Error (m) | SR@1m | Hits |
|-----------|-----------|-------|------|
| PMFS | 5.65 | 27% | 143 |
| GrGSL | 3.94 | 13% | 35 |
| SurgeCast | 3.71 | 20% | 49 |
| Ours | 6.93 | 7% | 137 |

---

## 3. Experiment Configuration

### GADEN Env A (Primary Test Environment)
- Grid: 100×100×30, cell_size=0.1m, env_min=(0,0,0), env_max=(10,10,3)
- Source: (5.0, 6.2, 0.5) or (5.0, 6.2, 2.0) for elevated
- Wind: `wind_simulations/1,2,3-5,6_0.csv`
- Gas: `gas_simulations/A1/iteration_*` (GADEN v3 format, needs conversion)
- Occupancy: `OccupancyGrid3D.csv` (8183 free cells at z=0)

### VGR Dataset (Public Benchmark)
- 30 houses, CFD 3D gas dispersion
- Path: `/home/zyc/vgr_data_scenarios/`
- House01: 87×114×33, source (-0.4, -2.9, -0.3) [config 2,4-1] or (-0.6, 1.95, 0.4) [config 1,3-2,4]
- House02: 83×119×26, source (0.0, -1.0, 0.2)
- House03: 138×83×25, source (-0.45, 1.9, -0.1)
- Wind CSV format: U, V, W, x, y, z columns

### Forward Model Parameters (All universal defaults)
| Parameter | Value | Notes |
|-----------|-------|-------|
| kappa | 0.01 | Diffusion coefficient |
| delta | 0.1 | Decay rate |
| alpha | 10.0 | Hit sensitivity |
| Gas threshold | 0.1 ppm | Standard |
| Step size | 0.8m | Shared |
| Max steps | 200 | Shared |

---

## 4. Pitfalls & Lessons Learned (CRITICAL)

### Pitfall 1: Coordinate System Bug
- **What**: Scripts used `int((x+5.0)/0.1)` assuming grid covers [-5,5]. Actual grid covers [0,10].
- **Impact**: ALL previous Python results were in wrong coordinate system.
- **Fix**: `int(x/0.1)` with no offset. Verified with round-trip test.
- **Lesson**: Always verify coordinates with header data from OccupancyGrid3D.csv.

### Pitfall 2: GADEN v3 vs v1 Format
- **What**: PMFS Env A uses GADEN v3 format (`GADEN_RESULT` header + 8-byte size_t). gadentools only reads v1.
- **Impact**: Can't use gadentools to query PMFS Env A concentration.
- **Fix**: Custom v3→v1 converter (strip 22-byte header, parse v3 with 8-byte size_t, write v1 with zlib).
- **Lesson**: Always check file format compatibility before assuming data pipeline works.

### Pitfall 3: Ground-Truth Leakage in Baselines
- **What**: GrGSL/SurgeCast Python implementations used `source[0], source[1]` (true source position) in navigation.
- **Impact**: Reported 0.21m error was achieved by algorithms that KNEW the source location.
- **Fix**: Replace with MAP estimate + wind direction.
- **Lesson**: Never use ground truth in algorithm logic, even in simplified implementations.

### Pitfall 4: Forward Model Self-Reinforcing Bias
- **What**: Green's function `g = (L^T)^{-1} * delta_obs` peaks at observation position. Hit updates push posterior toward robot, not source.
- **Impact**: MAP converges to robot's start corner, not source.
- **Status**: UNRESOLVED. Attempted fixes (upwind bias, directional likelihood) didn't help.
- **Lesson**: The adjoint formulation is fundamentally biased for this problem. Need alternative (backward Lagrangian).

### Pitfall 5: Gas Concentration at Flight Height
- **What**: VGR sources at z≈-0.3, flight at z=0.3 → concentration <0.1 ppm threshold.
- **Impact**: All sensor-dependent algorithms get zero hits.
- **Lesson**: Always verify gas concentration at flight height BEFORE running experiments.

### Pitfall 6: Benchmark Runner Incompatibility
- **What**: SAISC-PF benchmark runner requires specific audit files, crashes for PMFS/GrGSL/SurgeCast.
- **Impact**: Can't use standard pipeline for fair comparison.
- **Fix**: Write standalone benchmark scripts or use `clean_benchmark.py`.

---

## 5. VM Information

- **IP**: 192.168.111.128
- **User**: zyc / Password: 123456
- **ROS2**: Humble
- **Workspace**: `/home/zyc/gsl_ws/`
- **GSL source**: `/home/zyc/gsl_ws/src/GasSourceLocalization/`
- **VGR data**: `/home/zyc/vgr_data_scenarios/`
- **PMFS Env A**: `/home/zyc/gsl_ws/install/pmfs_env/share/pmfs_env/scenarios/A/`
- **Python**: `/usr/bin/python3` (no conda on VM)
- **PyTorch**: CPU version installed
- **scipy/numpy**: available

---

## 6. Git History (adaptive_altitude_gsl)

```
75ad04d step2: directional likelihood test
1e5ba50 step1: fair comparison - removed GT leakage
d004598 v19-real: VGR real GADEN data
d99d52c v19: VGR multi-house comparison
b8eebe4 v17b: fixed EIG with hybrid height posterior
1658e00 v17: true EIG + off-grid source
2f1339b v16-baseline: method package
```

---

## 7. Code Structure

### C++ (on VM)
```
/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/
├── PMFS/           # PMFS algorithm (internal filament simulation)
├── GrGSL/          # Gradient-based GSL
├── OPGSL/          # Our algorithm (WC_RIF_GSL.cpp with forward model)
├── SensorAwareSurgeCastPF/  # SAISC-PF
├── Spiral/         # SurgeCast base
└── Common/         # Base classes, states, utilities
```

### Python (adaptive_altitude_gsl on VM)
```
/home/zyc/adaptive_altitude_gsl/
├── src/
│   ├── core.py              # Forward model, algorithms, grid loading
│   ├── v17_eig_experiment.py # EIG altitude experiment
│   ├── v19_real_gas.py      # VGR comparison with real gas data
│   ├── step1_fair.py        # Fair comparison (no GT leakage)
│   └── step2_upwind.py      # Upwind bias / directional likelihood test
├── data/
│   └── conc_3d.pkl          # Pre-computed 3D concentration field
├── results/                 # CSV results
└── REPRODUCE.md             # Reproduction guide
```

### Key Files on VM
- `fair_validation.py` — 3-way wind comparison (FIXED coordinates)
- `analysis_by_synthesis_test.py` — Offline forward model test (FIXED coordinates)
- `v10_sampling_diagnosis.py` — Sampling geometry diagnostic
- `v10_closed_loop_sim.py` — Closed-loop simulation
- `convert_v3_to_v1.py` — GADEN v3→v1 format converter
- `convert_mismatch.py` — Mismatch scenario converter

---

## 8. What the Advisor Wants

1. **Fair comparison on public benchmark** (VGR dataset) with official baselines
2. **Robustness to model misspecification** (when forward model doesn't match reality)
3. **3D height estimation** as the key differentiator
4. **No per-scenario hand-tuning** — all parameters should be universal defaults
5. **Reproducibility** — everything must be reproducible with git hash + seeds
