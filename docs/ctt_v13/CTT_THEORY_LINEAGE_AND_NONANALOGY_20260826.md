# CTT theory lineage, transfer boundary and second-order innovation

Date: 2026-08-26  
Status: literature-to-method alignment draft.

## Main scientific question

PMFS treats each measurement largely through a misspecified candidate response family. The previous V10/V11/V12 mechanisms could improve some trajectories while still assigning cumulative evidence to false carriers. CTT changes the estimand before Bayesian accumulation: it tests which candidate can causally generate the observed sequence of arrivals and non-arrivals under transport physics.

## Three distant-domain transfers

### 1. Seismic travel-time tomography and phase association

Recent high-rate seismic phase association represents source-to-receiver travel times by a continuous neural field and compares unordered observed/predicted arrival distributions with optimal transport. The load-bearing ideas transferred to CTT are:

- propagation time is a field conditioned on source, receiver and medium, not Euclidean distance;
- multiple observed arrivals must be associated globally to physically admissible paths;
- missing/spurious arrivals require an unbalanced/background-aware association rather than forced matching.

CTT's second-order innovation is to replace wave eikonal travel time by an advection-diffusion first-passage distribution in an obstacle/wind field, and replace a fixed receiver array by one moving gas sensor. M1 produces stochastic delay/hazard components; M2 performs capacity-constrained burst-to-path association.

### 2. Astronomical reverberation mapping

Reverberation mapping extracts spatial structure from temporal response lags when direct spatial resolution is unavailable. CTT borrows only the principle that a distributed delay/transfer response can encode hidden geometry.

The analogy is not exact. Astronomy normally observes a varying driver and its delayed response. A continuously emitting gas source does not provide an observed release light curve. CTT therefore must not claim to recover a classical transfer function. It uses route- and wind-conditioned transport opportunities as predicted response components and tests observed burst timing against them. Any implementation that assumes a known emission onset violates the problem physics.

### 3. Assimilative causal inference in intermittent stochastic systems

Assimilative causal inference treats causality as an inverse problem: trace backward from an observed effect using a stochastic dynamical model and data assimilation, especially when only one intermittent realization is observed. CTT transfers that inverse-causal orientation to plume sensing:

- M1 traces an observed sensor event backward through wind, diffusion and obstacles to candidate source regions;
- M2 asks whether the full event sequence admits a coherent causal assignment;
- M3 uses prequential non-arrival as falsification of a candidate's predicted cause-effect channel.

CTT does not claim intervention-based causality. Its causal statement is mechanistic and conditional: under the frozen transport model family and nuisance prior, a candidate receives evidence only through a physically admissible source-to-observation path with the correct temporal support.

## Why a neural component is optional, not the novelty by itself

A neural field/operator may accelerate or approximate the M1 first-passage PDE. Its admissible target is \(S_s(x,t,\ell)\), \(f_s(\ell)\), or a low-dimensional physical discrepancy. It may not consume source truth, final localization error, PMFS entropy or seed success. It is retained only if it beats the numerical/analytical field on held-out transport prediction without changing causal ordering or violating PDE/boundary contracts.

Therefore the paper's novelty is not “a calibrated neural network.” It is the factorized causal transport likelihood:

\[
\text{physical arrival field}\rightarrow
\text{global burst-phase association}\rightarrow
\text{prequential miss survival},
\]

with disjoint evidence ownership and explicit before-Bayes source ordering.

## Identification assumptions that must be tested

1. **Carrier coverage:** the frozen candidate support contains a carrier close enough to the true source for the claimed resolution.
2. **Transport distinguishability:** at least some candidates have different first-passage/delay fields on the executed route.
3. **Temporal excitation:** the route, wind changes or plume intermittency create enough observable timing structure; constant identical hazards cannot identify M2.
4. **Nuisance restriction:** source strength/background cannot be separately profiled on the same miss interval, or any candidate can explain silence.
5. **Blockwise non-reuse:** a measurement block is scored once, by either the native PMFS update or the CTT update, never both.
6. **Feedback survivability:** pre-Bayes evidence improvements must remain useful after the planner changes the subsequent trajectory; this is tested only in frozen closed loop.

Failure of assumptions 1-3 is an invalid/diagnostic result, not negative performance. Failure of assumptions 4-5 is a method-contract error. Failure of assumption 6 after all earlier gates is a genuine closed-loop scientific NO-GO.

## Paper-level contribution shape

1. **Causal transport tomography:** formulate single-UAV gas-source localization as inverse recovery from stochastic first-passage arrival and survival evidence.
2. **Physics-constrained phase field:** learn/solve a continuous source-to-moving-sensor first-passage field under wind, diffusion and obstacles.
3. **Intermittent phase association and survival factorization:** combine unbalanced global burst assignment with disjoint prequential no-arrival likelihood.
4. **Mechanism-first validation:** require direct positive and conditional incremental information for every module before cross-House closed-loop qualification.

The contribution is credible only if M1, M2 and M3 pass their direct gates and the frozen A3 method improves the original PMFS metric in held-out 300-second House123 feedback loops.

