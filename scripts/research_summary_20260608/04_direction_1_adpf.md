# 04 Direction 1: AD-PF (Advection-Diffusion Particle Filter)

## Status: ABANDONED (improvement too small: 3.3%)

## Method
Replace isotropic diffusion in particle filter state transition with
Lagrangian advection-diffusion dynamics from atmospheric science (HYSPLIT).

Standard PF: particles += np.random.normal(0, sigma)  # isotropic
AD-PF: particles += advection + anisotropic_diffusion   # wind-aligned

Where:
- advection = -wind_hat * wind_speed * dt (upwind drift)
- diffusion_along = sigma_0 + alpha * |wind| (along-wind)
- diffusion_cross = sigma_0 + beta * |wind| (cross-wind, beta < alpha)

## Cross-Domain Source
- Atmospheric science: HYSPLIT / FLEXPART Lagrangian particle models
- S2 search: "Lagrangian particle" + "source localization" + gas = 0 papers
- Novelty confirmed: 8/10

## Experiment Results

### MATRIX Real Data (9 clean trials)
| Method | Mean Error | vs Std PF |
|--------|-----------|-----------|
| Standard PF | 232.6m | baseline |
| AD-PF | 224.8m | +3.3% |
| Win/Loss | | 6W/3L |

### Synthetic Data (5 scenarios × 10 seeds)
| Scenario | Std PF | AD-PF | Improvement | W/L |
|----------|--------|-------|-------------|-----|
| Weak wind (1 m/s) | 83.9m | 66.8m | **+20.3%** | 8W/2L |
| Far source | 140.5m | 133.9m | +4.7% | 9W/1L |
| Noisy | 106.8m | 102.2m | +4.3% | 5W/5L |
| Strong wind (6 m/s) | 145.2m | 141.1m | +2.8% | 6W/4L |
| Close source | 88.2m | 87.4m | +0.9% | 5W/5L |

## Why Abandoned
1. Improvement too small (3.3% on real data)
2. Only works well in weak-wind scenarios (20%), which is too narrow
3. Absolute errors still large (200m+)
4. Root cause: the LIKELIHOOD MODEL is too weak, not the state transition
5. The grid-based posterior approach is fundamentally limited

## Code Location
- `workspace/scripts/run_adpf_pilot.py` (v1)
- `workspace/scripts/run_adpf_synthetic.py` (synthetic test)
