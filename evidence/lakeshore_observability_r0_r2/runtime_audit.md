# GADEN runtime audit

Decision: **R1_HOLD_WEAK_OR_UNSTABLE**.

Primary fails because N0 and F1/F2 all have88.89pp height Top1 spread, so the negative-control contrast is absent. At mid release10, N0 is100% Top1 at10m and11.11% at30/60/100m; F1/F2 are100% at10/30m and11.11% at60/100m. Rank1 versus5 is shared by controls. The present data show an extension of the detectable height to30m, not a front-specific low-level false-negative blind zone. M1 upwind-cone capture is100% and M2 blind fraction0. M3 F1 front-peak fraction41.67% versus N033.33% at mid release is weak secondary evidence only; HOLD does not certify the primary mechanism. Threshold sensitivities do not rescue primary. R2 is not run.

R0_GO precedes N0 parity PASS, native RNG repeatability PASS, wind QC PASS and 12-realization smoke PASS. Then parameters, gas generation and scorer sources were frozen before the 864-realization matrix. No PMFS, learned model, closed loop or House rerun was involved.

Adapter: ros2_gaden family, minimal native C++ CLI against unchanged pre-existing GADEN core 3.0 in PF_DEI_V3_GADEN_BUILD. Python bindings absent. Main source commit17adaf650a4f11d29aa049cf0661e9f9ea2e636f, main core9e93c36ae1af74f6a62c42f1c9d7b813153222ed, historically modified. Isolated build's Git links are broken; source/binary hashes are authoritative, its original commit is not asserted.

Geometry is explicit native Environment occupancy: flat solid layer -5..0m; free interior0..150m; outer lateral/top cells are outlets. No shoreline wall. Native ParseOpenFoamVectorCloud preprocesses every regular CSV. Native RunningSimulation generates/query filaments, no replacement concentration field or postprocessing lift. No runtime package/kernel was installed, upgraded or edited.

N0 u=2m/s. L1 u=.4+1.6*f(z). F1/F2 divergence-free streamfunction: u=.4+A*s(x)*(f(z)-mean(f)), w=-A*sprime(x)*I(z), I(0)=I(150)=0. Compensating upper return flow preserves continuity. H=100m, widths15m vertical/35m horizontal. w maxima.5/1m/s. This is an ideal mechanism ablation, not fitted transient weather. N0 random100 query-point error0; finite-difference divergence maxima1.071e-4/2.142e-4s^-1.

Methane:5/10/20filaments/s, initial centre20ppm, sigma100cm, growth gamma10000cm²/s, native noise.02,298K/1atm. These are frozen synthetic dispersion settings, not inferred from public weather. Native buoyancy is unchanged across conditions. Eight explicit plume seeds30001..30008; OMP1, separate process per realization;120s warmup then300s fixed1Hz queries. Gas fields evolve in memory; exported C data are native trajectory observations, with replay defined by frozen seeds and binaries.

M4 removes the held-out seed from all9 source templates, Beta(1,1) smoothing and Brier ranking. Exact ties receive average rank/fractional Top1/Top3 credit; all misses remain chance-level. Heights10/30/60/100m share one2m/s XY ladder, period220s. Hit threshold.001ppm, sensitivity.0005/.002ppm. No per-environment thresholds.


Observed runtime sources/binaries in runtime_*.txt and runtime_binary_hashes.txt; actual parity and seed validations in N0_parity.json/seed_repeatability.json.
