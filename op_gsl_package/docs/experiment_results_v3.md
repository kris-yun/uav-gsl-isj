# SD-NBV v3 Experiment Results

> Date: 2026-07-01 | Dataset: VGR House01 | Source: (-0.4, -2.9, -0.3)

## Method: SD-NBV v3 (Spatial Deconvolution + Next-Best-View)

### Key Features
- 3D Bayesian posterior over source location (sx, sy, sz)
- FIM-based dimension selection
- GP-gated altitude calibration (only train after calibration)
- Temporal decay on posterior (0.995)
- Surge-to-MAP navigation (wind > 0.3 m/s)
- Isotropic diffusion model for low-wind fallback
- Distance-weighted plume likelihood
- NBV with wind-bias and map clipping

### Results (House01, start=(-0.9, 0.15))

| Seed | MAP (x,y,z) | x_err | y_err | z_err | 2D_err | 3D_err | Steps | Time |
|------|------------|-------|-------|-------|--------|--------|-------|------|
| 0    | (-0.95,-2.89,0.00) | 0.55 | 0.01 | 0.30 | **0.55** | 0.63 | 83 | 292s |
| 7    | (-3.22,-4.19,0.80) | 2.82 | 1.29 | 1.10 | **3.10** | 3.29 | 95 | 295s |
| 42   | (-0.38,-2.45,2.00) | 0.02 | 0.45 | 2.30 | **0.45** | 2.34 | 81 | 249s |
| **Mean** | | **1.13** | **0.58** | **1.23** | **1.37** | **2.09** | **86** | **279s** |

### Baseline Comparison (House01)

| Method | 2D Error | Notes |
|--------|----------|-------|
| PMFS   | 4.27m    | Converges fast (~25s) but to wrong location |
| **SD-NBV v3 mean** | **1.37m** | **68% better than PMFS** |
| **SD-NBV v3 best** | **0.45m** | **89% better than PMFS** |

### Analysis

**Strengths:**
- 2D localization significantly better than PMFS (1.37m vs 4.27m)
- y-direction nearly perfect in best case (0.01m)
- Altitude calibration works (gates GP training until after calibration)
- Posterior convergence improved with temporal decay

**Weaknesses:**
- z-direction unreliable (1.23m mean error)
- High seed-dependence (0.45m to 3.10m range)
- Slow convergence (~280s vs PMFS ~25s)
- Posterior MAP can lock to wrong location

### Root Causes Identified (by Expert Agents)

**Euler (Code Diagnosis):**
1. GP trained on pre-calibration data -> altitude stuck (FIXED in v2)
2. No distance attenuation in plume model -> MAP jumps (FIXED in v2)
3. NBV selects outside map -> wasted steps (FIXED in v2)
4. Wind not used for search direction -> inefficient (FIXED in v3)

**Darwin (Literature Analysis):**
1. Gaussian plume model invalid in low Péclet number (indoor) regime
2. FIM-based dimension selection blind to z in isotropic conditions
3. Need temporal-contrast (E. coli) z-exploration instead of FIM
4. Need diffusion-dominated plume model, not wind-advection model
5. Suggest reframing as "biomimetic chemotaxis with spatial deconvolution"

### Recommended Next Steps
1. Replace Gaussian plume with diffusion-dominated model (Loisy 2022)
2. Add temporal-contrast z-exploration (E. coli chemotaxis, Berg 1972)
3. Run GrGSL and SurgeCast baselines for comparison
4. Ablation experiment (6 configs x 3 seeds)
5. Run on House02 and House03 for generalization
