# PF-DEI modular closed-loop freeze

Date: 2026-08-29
Status: MODULE/INTERFACE FREEZE BEFORE CLOSED-LOOP INTEGRATION

This document separates the reconstructed method into independent modules so the same implementation can support truth-blind qualification, full closed-loop ON inference, and later one-module-at-a-time ablation without rewriting formulas after outcomes are visible.

## 1. B0 — physical causal generator base (not an ablation switch)

The common base for every PF-DEI arm is the physically closed source definition and native predictive family:

`S -> U -> Z_t -> C_t -> R_t -> M_t`

- `S`: planar persistent source carrier region, the localization target;
- `U`: unresolved legal 3-D placement inside the carrier;
- `Z_t`: one stochastic native-GADEN transport realization;
- `C_t`: physical concentration at the robot;
- `R_t`: persistent sensor state;
- `M_t`: measured ppm.

All arms use the same candidate carriers, geometry prior, nuisance-member IDs, GADEN source/configuration, wind/map context, source-update cadence and planner. No House/seed/source-truth dependent parameter is allowed. B0 is the corrected problem definition and is common to all method/ablation arms, so it is not removed in the primary ablation matrix.

## 2. M1 — sensor-state canonicalization

FULL does not treat measured ppm as instantaneous physical concentration. With frozen `dt=0.2 s`, `tau=1.2 s`, and two-sample dead time, the exact deterministic inverse is

`C[k-2] = (M[k] - alpha M[k-1])/(1-alpha)`, `alpha=exp(-0.2/1.2)`.

The recovered physical prefix is aligned to the original physical pose/time indices and then compared with native physical predictions.

Ablation `pfdei_ablate_sensor` bypasses this inverse and compares the measured sequence directly with candidate physical predictions. This is intentionally a misspecified observation-operator ablation; nothing else changes.

## 3. M2 — physical nuisance-distribution marginalization

For source `s`, FULL retains the finite predictive distribution

`P_s={C_s,j[1:T]} j=1..M`.

FULL uses the finite-ensemble energy score including its ensemble-dispersion correction, so uncertainty over unresolved source placement/transport members is represented as a distribution rather than collapsed to one deterministic forecast.

Ablation `pfdei_ablate_nuisance` replaces the member distribution by the arithmetic-mean trajectory and scores only that mean field. This changes M2 only.

## 4. M3 — coherent nuisance trajectories

Inside the M2 ensemble, one nuisance member `j` must remain the same physical realization for the whole prefix:

`C_s,j[1] -> C_s,j[2] -> ... -> C_s,j[T]`.

Ablation `pfdei_ablate_coherence` deterministically remaps

`C'[s,m,t]=C[s,(m+t) mod M,t]`.

At each source/time the multiset over members is exactly unchanged, so instantaneous predictive distributions are identical; only cross-time member identity is destroyed. This isolates the scientific value of coherent stochastic trajectories from ordinary ensemble spread.

## 5. M4 — ordered temporal increment evidence

For a nonnegative physical concentration sequence `C`, define the dimensionless level channel

`a_t=log1p(C_t/thresholdGas)`.

The order-sensitive FULL path representation is

`Phi(C)=[a/sqrt(T), diff(a)/sqrt(T-1)]`.

This uses only the adjacent causal increment; there is no selected lag, attention window or outcome-tuned temporal scale. Distance is Euclidean in this path representation. Because `diff(a)` depends on adjacency, a common time permutation is no longer invisible as it is for a level-only Euclidean sequence score.

Ablation `pfdei_ablate_temporal` drops `diff(a)` and retains only the level channel. This changes M4 only while preserving B0, M1, M2 and M3.

M4 is claimable only if the independent offline order audit supports it. If that audit fails, final PF-DEI must omit M4 rather than rescue it with another architecture.

## 6. A0 — reversible source-mass adapter (integration operator, not a claimed innovation module)

For each source, the selected evidence backend computes a lower-is-better predictive score. Candidate scores are converted to fixed-scale Gaussian mid-rank evidence `z_s`; source mass is recomputed from the geometry-only prior on every prefix:

`q_t(s) proportional q0(s) exp(z_s)`.

This is intentionally reversible: the previous PF-DEI mass is never multiplied again, so the same historical evidence cannot compound repeatedly at later source updates.

This rank adapter is a deterministic source-mass map, not a calibrated physical likelihood. Until a separately qualified ratio/likelihood backend exists, paper wording must use `source mass` or `source belief`, not claim a calibrated Bayesian posterior. A0 is required to connect candidate evidence to PMFS and is therefore not a primary ablation switch.

## 7. Runtime provider boundary

`PFDEIPredictiveProvider.hpp` defines the required runtime physics provider. It must answer

`physicalPpm(source, member, arbitrary causally visited pose/time)`.

A tensor sampled only along historical OFF trajectories is sufficient for offline audits but is **not** sufficient for an adaptive ON closed loop, because the ON planner can visit different poses. The production provider must therefore be trajectory-independent, backed by retained native GADEN field outputs/frame-query semantics or an equivalent immutable queryable field bank.

Reserved nuisance members are qualification-only. Runtime FULL uses only the frozen training/predictive member set.

## 8. Runtime observation boundary

PF-DEI temporal inference requires the same raw measured-ppm cadence used by the qualified sequence model/audits. The existing `processGasAndWindMeasurements()` path may operate on a completed block average; Codex must locate the pre-average measured-gas sample callback/topic and append `PFDEIEngine::RawSample` there without changing the native PMFS measurement path.

If the deployed ROS path exposes only block averages, PF-DEI must be re-qualified offline at block resolution before closed-loop use. It is forbidden to silently train/audit at 0.2-s resolution and deploy at block resolution.

## 9. Source-mass to PMFS-grid adapter

Candidate source mass is region-valued. For a carrier `s` with its exact 2-D PMFS free-cell set `F_s`, distribute carrier mass uniformly over its constituent free cells:

`p(f)=q(s)/|F_s|` for `f in F_s`.

The persistent carriers form the geometry partition used by the source-support contract. After distribution, verify total free-cell mass is one to numerical tolerance. Do not blend with the same-window native PMFS posterior.

On a structural inference failure (insufficient prefix, provider error, invalid value), leave the current native/source grid unchanged and log the reason. This is not an outcome-based ACCEPT gate.

## 10. Runtime modes frozen for ablation

- `off`: untouched Classic PMFS;
- `pfdei_shadow`: compute/log FULL source mass but never mutate `sourceProbability`;
- `pfdei_full`: B0 + M1 + M2 + M3 + M4 + A0;
- `pfdei_ablate_sensor`: remove M1 only;
- `pfdei_ablate_nuisance`: remove M2 only by replacing the predictive distribution with its mean trajectory;
- `pfdei_ablate_coherence`: remove M3 only by destroying member trajectory identity while preserving every per-time member multiset;
- `pfdei_ablate_temporal`: remove M4 only by dropping adjacent temporal increments;

Every arm must share the same B0 source support/physics, raw observations, geometry prior, planner settings, source-update cadence, stopping logic and A0 adapter. Only the named scientific module changes.

## 11. Full closed-loop validation order

1. Existing-bank offline source/coherence/order audit; no training and no closed-loop outcomes.
2. Python/C++ modular parity and native field-provider parity on historical trajectories.
3. `pfdei_shadow` runtime smoke: same trajectory/posterior/planner as OFF; source-mass logs only.
4. Freeze FULL backend and binary before outcome comparison.
5. Development matrix: H01/H02/H03 x seeds 0..9 x OFF/FULL = 30 matched pairs / 60 arms. Frozen criteria remain pooled error reduction >=10%, >=20/30 improved, no House pooled degradation >5%, zero new false-confident collapses.
6. Only if FULL development is GO, run one-module-at-a-time ablations M1/M2/M3/M4 on the already-frozen development seeds. Reuse the 30 completed FULL runs; do not rerun them.
7. Confirmatory matrix: H01/H02/H03 x seeds 10..19 x OFF/FULL only. No ablation output may be used to modify FULL before this matrix.
8. Real-world deployment: new environment may regenerate/query a source-independent physics bank and perform source-independent sensor calibration, but no source-label neural retraining or outcome-based parameter fitting.

## 12. Current code boundaries

- `experiments/cg_pc_ctt/pf_dei_modular_core.py`: Python reference;
- `experiments/cg_pc_ctt/selftest_pf_dei_modular.py`: sensor/inference/module selftest;
- `ros2_package/.../PFDEIModularRuntime.hpp`: C++ M1/M2/M3/M4/A0 core;
- `ros2_package/.../PFDEIPredictiveProvider.hpp`: trajectory-independent B0 provider interface;
- `ros2_package/.../PFDEIEngine.hpp`: streaming raw-observation + provider engine;
- `closed_loop/pf_dei/run_pfdei_pair_matrix.sh`: development/confirmatory OFF/FULL pair runner;
- `closed_loop/pf_dei/aggregate_pfdei_pairs.py`: frozen paired GO/NO-GO aggregator;
- `closed_loop/pf_dei/run_pfdei_modular_ablation_matrix.sh`: later M1/M2/M3/M4 removal runner;
- `closed_loop/pf_dei/aggregate_pfdei_ablation.py`: paired ablation summary.

The module boundary is frozen before closed-loop outcome visibility. The exact final evidence backend is activated only after the ongoing truth-blind physical-information audit determines whether ordered/coherent path evidence is supported.
