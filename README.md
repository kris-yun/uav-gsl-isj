# CP-SBD-GSL

**Conformal Prediction-terminated, Self-regulating Bayesian Decision for UAV Gas Source Localization**

> Target: IEEE Sensors Journal (ISJ)

## Method

CP-SBD-GSL is a 3D adaptive-altitude UAV gas source localization framework with three cross-domain innovation pillars:

1. **DDM-Stopping** — Drift-Diffusion Model for search termination (neuroscience-inspired)
2. **W-RAIG** — Wasserstein Risk-Aware Information Gain (optimal transport theory)
3. **CP-Stopping** — Conformal Prediction convergence detection (distribution-free guarantee)

### Unified Objective Function

$$\max_{\pi} \mathbb{E}\left[\sum_{t=1}^{T} \gamma^{t-1} I_t^{W\text{-}RAIG} - \lambda \sum c(s_t, s_{t+1}) + \eta \mathcal{E}_t\right]$$

## Repository Structure

```
├── src/                    # C++ source code (ROS2 Humble)
│   ├── OPGSL.cpp          # Main algorithm (~1500 lines)
│   ├── OPGSL.hpp          # Header with all module declarations
│   ├── WATS_GSL.hpp       # Field estimator + W-RAIG
│   ├── DDM_Stopping.hpp   # DDM stopping criterion
│   └── CP_Stopping.hpp    # CP stopping criterion
├── launch/                 # ROS2 launch files
│   └── vgr_ablation.launch.py  # Ablation experiment launcher
├── scripts/                # Experiment automation
│   ├── ablation_batch.sh  # Ablation: Full/NoDDM/NoWRAIG/Baseline
│   ├── baselines_batch.sh # Classic baselines: PMFS/GrGSL/SurgeCast
│   ├── analyze_ablation.py # Statistical analysis
│   └── full_analysis.py   # Full analysis with Cliff's delta
├── docs/                   # Documentation
│   ├── CP_SBD_GSL_FRAMEWORK_CN.md  # Framework theory
│   ├── experiment_results_v5.md     # Experiment report
│   └── ISJ_SENIOR_EDITOR_EVALUATION.md # Editor review
└── results/                # Experiment data
    └── ablation_summary.csv
```

## Ablation Results

| Method | Median(m) | Mean(m) | Std(m) | vs Full |
|--------|-----------|---------|--------|---------|
| **Full** | **1.333** | **1.431** | 0.307 | — |
| NoDDM | 1.635 | 1.757 | 0.725 | +22.7% |
| NoWRAIG | 1.610 | 1.688 | 0.585 | +20.8% |
| Baseline | 1.646 | 1.639 | 0.758 | +23.5% |

- Dataset: VGR (3 Houses, CFD filament simulation)
- Start: (-0.9, 0.15), Flight height: 0.3m
- 3 seeds per configuration, 300s timeout

## Dependencies

- ROS2 Humble
- VGR Dataset (https://github.com/MAPIRlab/GSL-dataset)
- Eigen3
- GADEN (for CFD simulation)

## Citation

```bibtex
@article{yan2026cpsbdgsl,
  title={CP-SBD-GSL: Conformal Prediction-terminated Self-regulating Bayesian Decision for UAV Gas Source Localization},
  author={Yan, Z.Y.C.},
  journal={IEEE Sensors Journal},
  year={2026}
}
```

## License

To be determined. Code will be made public upon paper acceptance.