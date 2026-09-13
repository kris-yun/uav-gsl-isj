# 03 — Nuisance Perturbation Contract (M2)

Atoms: `b_{s,j} = g(s, ξ_j+) − g(s, ξ_j−)`, fixed candidate s, nuisance j.
Generated with the verified PMFS filament kernel (snapshot copy, behavior-neutral
per M1), CRN = same frozen engine + Gaussian stream per candidate for the
physical nuisances; the stochastic-realization nuisance uses two fixed streams.

## Frozen magnitudes (from config/calibration, NOT from H01/H03 results)

| nuisance | + / − | basis |
|---|---|---|
| wind direction | ±15° | GMRF angular-error assumption |
| wind speed scale | ±20% | GMRF magnitude-error assumption |
| velocity noise | noiseSTDev 0.5 ± 0.1 | frozen run config |
| filament realization | two fixed streams (+500 / +1200 Gaussian draws) | CRN design |
| MOX rise/recovery | τ = 0.5 ± 0.1 on `g(1−exp(−g/τ))` | VGR fopdt sensor config |

CRN: per candidate c, engine = base + c·7919, Gaussian index = c·251 + offset,
using the frozen post-update Gaussian table; same stream for + and − of the
physical nuisances (candidate/stochastic differences do not mix).

Outputs: `atoms.f32` (J×N float32) + `nuisance_manifest.json`.
Atom counts: H01 U0 76 (19 candidates), U1 84 (21), U2 92 (23);
H03 U0 92 (23), U1 84 (21), U2 76 (19); plus C MOX atoms per update.
