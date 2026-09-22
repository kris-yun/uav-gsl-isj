# Dynamical large-deviation / trajectory-thermodynamics transfer — NO-GO

Date: 2026-09-22  
Status: **NO-GO AS MAIN LINE**

## Mother idea

Cross-domain source: nonequilibrium statistical physics.

Scite anchors:
- Lin & Tang, *Dynamical Partition Functions of Stochastic Dynamics via Variational Flows* (2026), DOI `10.48550/arxiv.2606.10757`.
- Valov & Meerson, *Dynamical large deviations of the fractional Ornstein-Uhlenbeck process*, J. Phys. A (2025), DOI `10.1088/1751-8121/adb8ae`.
- Pamulaparthy & Harris, *Towards neural reinforcement learning for large deviations in non-equilibrium systems with memory*, J. Stat. Mech. (2025), DOI `10.1088/1742-5468/adea65`.

The physical idea is to characterize an entire stochastic history through finite-time dynamical partition functions / scaled cumulant generating functions of time-integrated path observables rather than by an instantaneous state.

## GSL transfer tested

For every source candidate:
1. sample its simulated hit-probability field along the actual robot trajectory;
2. rank-normalize the measured gas trace and candidate trace to suppress marginal-amplitude calibration;
3. partition the history into fixed time blocks;
4. compute finite-time trajectory free-energy / SCGF spectra
   [
   \psi_B(\lambda)=B^{-1}\log\langle e^{\lambda S_B}\rangle
   ]
   for symmetric fixed tilts `lambda = {-4,-2,-1,1,2,4}`;
5. rank source hypotheses by measured-vs-candidate SCGF-spectrum mismatch.

A principled multiscale member used block lengths 10, 25, and 50 samples (2, 5, 10 s).

## Joint old+new development result

- Native mean over 12 = **5.7843 m**
- trajectory-free-energy candidate mean = **4.4264 m**
- pooled reduction = **23.48%**
- non-worse = **9/12**

Split:
- old six: **10.49%**, 4/6
- new six: **35.47%**, 5/6

The result is therefore not an old-only HCMC-style collapse, but this is not sufficient.

## Destructive controls

### Final-leaf score permutation, 500 repetitions
- null mean = **4.4398 m**
- fraction null as good as/better than real = **0.48**

### Candidate temporal-correlation destruction, 20 repetitions
Independently shuffle each candidate sequence in time while preserving its marginal distribution.
- null mean = **4.5691 m**
- fraction null as good as/better than real = **0.35**

### Candidate-identity mismatch, 50 repetitions
Reassign source scores to different candidate identities.
- null mean = **4.4474 m**
- fraction null as good as/better than real = **0.52**

These controls fail the failure-informed mechanism criterion.

## Geometry-only control

Apply the identical trajectory-free-energy construction to a source-blind geometry channel based only on robot-to-candidate distance.

- geometry-only mean = **4.2534 m**
- apparent gain = **26.47%**
- non-worse = **9/12**

Geometry-only is numerically better than the plume-based large-deviation transfer.

## Candidate-level truth audit

The nearest-to-truth candidate receives very low score percentiles in most cases.

Examples:
- new H01 realization 1: ~21.1 percentile
- new H01 realization 2: ~21.5 percentile
- new H02 realization 1: ~10.8 percentile
- new H02 realization 2: ~11.5 percentile

The candidate with the single largest score is frequently several metres from truth.

High cross-realization score reproducibility (~0.97–0.99) therefore reflects a stable trajectory/geometry signature, not reliable source identity.

## Decision

The large-deviation mother theory is scientifically legitimate, but the present source-inference transfer is not.

The apparent endpoint gain is not source-specific:
- leaf null is not separated;
- candidate identity is not load-bearing;
- geometry-only is stronger;
- truth-candidate ranking is poor.

Final verdict:

`DYNAMICAL_LARGE_DEVIATION_GSL_TRANSFER_NO_GO_20260922`

Do not tune lambda grids, block lengths, or alternative rate-function transforms on the same 12 cases.
