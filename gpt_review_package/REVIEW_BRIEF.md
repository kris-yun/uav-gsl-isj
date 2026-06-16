# UAV GSL ISJ Paper - Review Package for GPT Pro
## Date: 2026-06-16

---

## 1. Scientific Problem

UAV gas source localization (GSL) in low-wind indoor environments using PMFS algorithm.
The PMFS algorithm from MAPIRlab is the state-of-the-art, but it suffers from:
- Systematic convergence to incorrect local optima due to GMRF wind estimation errors
- Zero gas hits in sparse environments → probability map has no evidence to work with
- Premature declaration (exploration stops after 3-7 iterations on hard scenarios)

Target journal: IEEE Sensors Journal (ISJ)

## 2. Dataset

VGR public dataset (MAPIRlab):
- House01: source=(-0.4, -2.9), config=2,4-1_fast, 87x114 grid
- House02: source=(0.0, -1.0), config=3,5-1_fast
- House03: source=(8.2, 5.0), config=1-2,5_fast (HARD - source far from start)

## 3. Proposed Innovation Modules

### Module 1: SDR (Spatial Deconvolution Refinement)
- Origin: Medical imaging (Richardson-Lucy deconvolution)
- Idea: Deconvolve the hit probability map to recover source peak from wind-smeared observations
- Uses directional PSF aligned with average wind direction
- Implementation: PMFS_utils.cpp, lines ~460-595

### Module 2: ITS (Inertia Tensor Selection)
- Origin: Astronomical image analysis (second moment tensor)
- Idea: Compute eccentricity of gas hit spatial distribution to adaptively blend baseline and SDR
- High eccentricity (elongated plume) -> more SDR weight
- Low eccentricity (circular hits) -> more baseline weight
- Implementation: PMFS_utils.cpp, lines ~563-595

### Module 3: (NOT YET FOUND)
- Needs to be from non-atmospheric domain (medical/bio/CV preferred)
- Must work independently and show >10% improvement
- Must be robust across datasets

## 4. Experimental Results (Ablation Study)

### House01 - Original Source (-0.4, -2.9), 3 seeds
| Condition | s0 | s1 | s2 | Mean | vs Baseline |
|-----------|------|------|------|------|-------------|
| baseline | 3.589 | 3.366 | 3.589 | 3.515 | - |
| SDR | 3.105 | 3.105 | 3.105 | 3.105 | -11.7% |
| TDC (v1) | 4.476 | 3.270 | 3.127 | 3.624 | +3.1% |
| TDC (v2, EMA) | 3.270 | 4.355 | - | 3.812 | +8.4% |
| MHC | 3.270 | 2.879* | 2.879* | 3.009 | -14.4% |
| MTI | 3.589 | - | - | 3.589 | +2.1% |
| DQA(SDR+TDC+MHC) | 3.149 | 2.879* | 2.879* | 2.969 | -15.5% |
* = timed out (300s), may be unreliable

### House01 - Multi-Source Test (SDR only, seed 0)
| Source | Baseline | SDR | Change |
|--------|----------|-----|--------|
| (-0.4,-2.9) | 3.589 | 3.105 | -13.5% GOOD |
| (1.0,-1.5) | 5.116 | 4.725 | -7.6% GOOD |
| (-2.0,-4.0) | 2.278 | 2.550 | +11.9% BAD |

### House02 - (0.0, -1.0), 3 seeds
| Condition | s0 | s1 | s2 | Mean | vs Baseline |
|-----------|------|------|------|------|-------------|
| baseline | 3.781 | 2.139 | 3.955 | 3.292 | - |
| SDR | 3.333 | 2.990 | 3.333 | 3.219 | -2.2% |

### House03 - (8.2, 5.0), 3 seeds
| Condition | Mean | vs Baseline |
|-----------|------|-------------|
| baseline | 11.183 | - |
| SDR | 11.183 | 0% (no gas hits, SDR cannot activate) |

### ITS Blend Results (House01, seed 0)
| Source | Baseline | SDR | ITS Blend | ecc | Improvement |
|--------|----------|-----|-----------|-----|-------------|
| (-0.4,-2.9) | 3.589 | 3.105 | 3.174 | 0.367 | -11.6% |
| (1.0,-1.5) | 5.116 | 4.725 | 4.948 | 0.661 | -3.3% |
| (-2.0,-4.0) | 2.278 | 2.550 | 2.386 | 0.661 | +4.7% |

ITS Blend reduces SDR's harmful effect on alt2 from +15% to +4.7%, but also weakens SDR's benefit on alt1 from -12% to -3.3%.

### Official Baselines (round6_results, House01, 8 seeds, min_distance)
| Method | mean min_distance |
|--------|------------------|
| PMFS | 2.409 |
| GrGSL | 4.202 |
| surge_cast | 4.466 |

## 5. Failed Modules (Do Not Reuse)

| Module | Domain | Why Failed |
|--------|--------|------------|
| TDC (v1) | Signal processing (derivative) | Noise amplification: +3.1% avg |
| TDC (v2, EMA) | Signal processing (smoothed) | Still inconsistent: +8.4% avg |
| MHC | Image morphology | Unreliable (some timeout results) |
| MTI | Bio-inspired (MOX temporal) | No effect (no gas hits to accumulate) |
| ACG | Signal detection (Neyman-Pearson) | spread=0.80m for ALL sources, cannot discriminate |
| MAP Selection | Bayesian (sourceProbability) | Circular: PMFS's own peak always has highest prob |
| PSDE | Atmospheric (Gaussian plume) | Math formula errors |
| SPW | Signal processing (matched filter) | No improvement |
| BAPR | Medical (distance transform) | Blind penalty, pushes to worse locations |
| ASA | Statistics (temporal ensemble) | Reinforces wrong direction |

## 6. Current Key Problems

### Problem 1: SDR is not universally effective
- Helps ~11% for far sources, HURTS ~15% for near sources
- The directional PSF assumption (upstream wider) fails when source is close to gas hits
- No reliable observable feature to discriminate far vs near source scenarios

### Problem 2: House03 is completely unsolvable
- Source at (8.2,5.0), start at (-5,-5), distance ~14.6m
- PMFS explores only 3-7 iterations, never reaches source area
- 0 gas hits → SDR cannot activate
- Changing minExplorationIterations and explorationProbability does NOT help

### Problem 3: No second effective module
- All attempted modules (TDC, MHC, MTI, ACG, MAP, ITS blend) fail to show consistent improvement
- Root cause: VGR dataset has extremely sparse gas encounters
- Only post-processing of the probability map (SDR) can work when hits exist
- When hits don't exist, nothing can help

### Problem 4: ITS blend cannot reliably discriminate
- alt1 (far source) and alt2 (near source) have nearly identical eccentricity (~0.66)
- Total variance is also similar (~0.85)
- The hit distribution shape does not encode enough information about source distance

## 7. What We Need From GPT Pro

1. **A second/third innovation module** that:
   - Works on the probability map level (not dependent on gas hits)
   - Comes from non-atmospheric domain (medical/bio/CV/physics)
   - Shows consistent improvement across House01, House02, and ideally House03
   - Has theoretical backing

2. **A reliable discriminator** to determine when SDR should be used:
   - Current approaches (spread, eccentricity, probability comparison) all fail
   - Need an observable feature that correlates with "SDR helps vs hurts"

3. **A solution for House03 exploration failure**:
   - PMFS gives up after 3-7 iterations
   - No gas hits means no information to guide search
   - Need a fundamentally different approach for hard exploration scenarios

4. **ISJ paper strategy**:
   - Is a single-module paper (SDR only, ~11%) sufficient for ISJ?
   - How to frame the contribution when the module doesn't work universally?
   - What level of statistical validation is needed?

## 8. Code Structure

`
code/
├── src/
│   ├── PMFS.cpp          - Main algorithm, TDC/MTI logic, parameter declarations
│   ├── PMFS_utils.cpp    - SDR/ITS deconvolution, estimation logic
│   └── PMFS.hpp          - Member variables (raw_peak, TDC/MTI state)
├── include/
│   └── Settings.hpp      - All module settings (SDR, TDC, MHC, MTI params)
└── launch/
    └── vgr_gsl_unified_ablation.launch.py - Launch file with all parameters
`

Key code locations:
- ITS Blend: PMFS_utils.cpp ~line 563-595
- SDR block: PMFS_utils.cpp ~line 458-560
- TDC logic: PMFS.cpp ~line 299-330
- MTI logic: PMFS.cpp ~line 378-395
- Settings: Settings.hpp lines 67-91

## 9. VM Setup

- VM: 192.168.111.128, SSH user zyc/zyc
- ROS2 Humble at ~/ros2_ws/
- GSL code: ~/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/
- VGR data: /mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/
- Build: cd ~/ros2_ws && source /opt/ros/humble/setup.bash && colcon build --symlink-install --packages-select gsl_server

## 10. GitHub

- Repo: https://github.com/kris-yun/uav-gsl-isj (PRIVATE)
- Latest commit: 528cca3