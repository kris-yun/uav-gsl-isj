# UAV-GSL ISJ Experiment Results (Final 2026-06-17)

## Three Innovation Modules

### Module 1: SDR ? Spatial Deconvolution Refinement
- **Domain**: Medical imaging (Richardson-Lucy deconvolution, 1974)
- **Concept**: Gas hit distribution = source signal convolved with plume PSF. Deconvolution recovers source.
- **Implementation**: Anisotropic upwind PSF, RL iteration, ITS-G gate (astronomical inertia tensor)
- **Effect**: Improves final estimate quality regardless of PMFS convergence status

### Module 2: CFAR ? Constant False Alarm Rate Detection
- **Domain**: Radar signal processing (Neyman-Pearson, 1943)
- **Concept**: Replace fixed thresholdGas=0.1 with adaptive threshold based on local noise floor
- **Implementation**: Sliding window of recent concentrations, Q25 as noise floor, threshold = Q25 * guard_factor
- **Effect**: Improves PMFS convergence success rate by adapting to varying signal conditions

### Module 3: ITS-G ? Inertia Tensor Gating
- **Domain**: Astronomical image analysis (shape classification)
- **Concept**: Compute eccentricity of gas hit distribution to decide when SDR should apply
- **Implementation**: Inertia tensor eigenvalue decomposition, hard gate (ecc >= 0.3)
- **Effect**: Prevents SDR from degrading estimates when hits are circular (near source)

## House01 Results (10 seeds, paired)

| Method | Mean Error | Improvement | Success@3m | Notes |
|--------|-----------|-------------|------------|-------|
| Baseline | 3.099m | - | 40% (4/10) | PMFS original |
| CFAR | 3.241m | +4.6% | **70% (7/10)** | Helps convergence |
| SDR | **2.762m** | **-10.9%** | **70% (7/10)** | Improves accuracy |
| CFAR+SDR | 3.051m | -1.6% | **80% (8/10)** | Best success rate |

## House02 Results (5 seeds)

| Method | Mean Error | Improvement |
|--------|-----------|-------------|
| Baseline | 5.712m | - |
| SDR | 5.424m | -5.0% |

## House03 Results (5 seeds)

All methods: 3.448m (PMFS converges in 4 iterations, no room for improvement)

## Statistical Summary (House01)

- SDR vs Baseline: -10.9% mean error, +30% success rate
- CFAR vs Baseline: +4.6% mean error, +30% success rate
- CFAR+SDR vs Baseline: -1.6% mean error, +40% success rate
- SDR's best single improvement: s1 from 2.879m to 0.486m (-83.1%)

## Key Insights

1. SDR is the primary accuracy improvement module (-10.9% mean error)
2. CFAR improves convergence but can worsen accuracy on already-converged seeds
3. CFAR+SDR combination achieves highest success rate (80%) 
4. ITS-G gate prevents SDR degradation on near-source hits
5. Cross-dataset: SDR helps House01 (-10.9%) and House02 (-5.0%), not House03

## Comparison with Official Baselines (from VGR dataset)

| Algorithm | Mean min_distance | Source |
|-----------|-------------------|--------|
| PMFS | 2.41m | Official |
| GrGSL | 4.20m | Official |
| surge_cast | 4.47m | Official |
| **PMFS+SDR** | **2.762m** | This work |

Note: Official baselines use different metrics (min_distance_to_source over full run).
Our error metric is final declared source position, not minimum distance during search.

## Pending
- [ ] Cross-dataset validation on House02/03 with CFAR+SDR
- [ ] Statistical significance tests (Wilcoxon paired test)
- [ ] Bootstrap 95% CI
- [ ] Official baseline comparison (run PMFS/GrGSL/surge_cast with same seeds)
- [ ] Paper writing
