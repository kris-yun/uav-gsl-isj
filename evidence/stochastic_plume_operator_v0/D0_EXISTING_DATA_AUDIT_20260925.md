# SPOI/DLL D0 Existing-Data Audit — 2026-09-25

Working route: **Sparse-Observation Stochastic Plume Operator Inversion (SPOI)**

Mother theory: Park et al., ICML 2026, *Generative Neural Operators through Diffusion Last Layer* (DLL), arXiv:2602.04139.

Status: **D0_HOLD_NEEDS_EXISTING_WIND_GEOMETRY_CONTEXT**

No new GADEN simulation is authorized.

## 1. Scientific object

Instead of learning only a deterministic plume mean or directly classifying the source, model a conditional random plume function:

p(C | S, W, O),

where S is candidate source context, W is wind context and O is geometry/occupancy context.

For sparse UAV observations y = H C + sensor noise, source inference uses the explicit observation likelihood:

p(y | S,W,O,H) = integral p(y | C,H) p(C | S,W,O) dC,

followed by a Bayesian update on the original PMFS source grid.

The paper-level innovation, if it survives, is the inversion of a source-conditioned stochastic function operator under sparse partial observations, not merely applying DLL to plume prediction.

## 2. Why DLL is relevant

DLL learns an input-conditioned low-rank functional basis and a conditional distribution of its coefficients. It is designed for stochastic systems whose output distributions are smooth/low-dimensional.

D1R independently established both ingredients:
- source-conditioned expected plume/encounter structure is strongly low-dimensional;
- plume realization spread is strongly source-dependent.

## 3. Prior-art boundary

### 2026 Deep Probabilistic Indoor GSL

Kim et al., arXiv:2608.16221, already perform deep probabilistic indoor GSL from sparse gas/wind/map observations and output a source posterior.

They also predict wind and concentration-field uncertainty, but use per-cell independent heteroscedastic diagonal Gaussian field models and inverse sequential inference.

Therefore SPOI must not claim novelty for:
- deep probabilistic GSL;
- source posterior maps;
- using wind/map context;
- predicting concentration uncertainty;
- sparse-observation inference.

Candidate distinction:
- learn a forward correlated stochastic plume law p(C|S,W,O);
- preserve low-rank spatial/temporal correlations in the random plume function;
- apply a sparse observation operator H to obtain candidate-source likelihoods;
- invert the learned stochastic operator explicitly into the PMFS posterior.

### 2023 learned plume surrogate + STE

Jin et al., ICRA 2023, already learn a deterministic/data-driven plume surrogate and integrate it with probabilistic Source Term Estimation.

Therefore SPOI must beat a deterministic surrogate/mean-field likelihood under the same observation budget. A stochastic operator that merely predicts fields better is insufficient.

## 4. Existing-D1R linearized stochastic-operator signal

Input data:
- 168 sources x16 realizations x300 log(1+ppm) observations;
- checkerboard 84/84 source holdout;
- one 8-realization half used for training, opposite half for evaluation;
- all 168 source hypotheses remain in the posterior support.

### Shared low-rank basis, global stochastic spectrum

A Gaussian low-rank plume law uses one residual basis/spectrum learned from outer-train sources.

### Shared low-rank basis, source-conditioned spectrum

The same basis is used, but per-source latent variances are estimated on training sources and spatially predicted for all candidate sources.

With a fixed rank-10 diagnostic and the same candidate mean model, source-conditioned stochastic spectrum improves source-heldout proper score in all four directions relative to the global-spectrum version.

This is a mechanism signal that source-dependent plume spread matters.

## 5. Strict nested-CV result on the full 300-query observation

When stochastic rank and posterior temperature are selected only by inner train-source CV:

- all four outer source-heldout scenarios select rank 0.

Thus, without richer operator context, a full input-dependent low-rank stochastic law is not justified by the 300-query D1R observation contract.

Target-ceiling nonzero-rank results are explicitly rejected.

## 6. Sparse-observation diagnostic

Using deterministic sparse query masks and train-source-only rank/temperature selection:

- 20-query settings select nonzero rank in all four outer scenarios;
- 100-query settings select nonzero rank in all four;
- 10-query settings are mixed;
- 50-query and full-300 settings collapse to rank 0.

However, nonzero-rank selection does not yield a source-heldout proper-score win in every outer direction.

Therefore stochastic covariance appears more relevant under sparse observation, but the result is not yet sufficiently stable for ADVANCE.

## 7. Neural conditional KL lower bound

A small neural context-to-mean/input-dependent-low-rank Gaussian model was tested with source x-y context.

Although target-ceiling nonzero ranks looked promising, nested train-source CV selected rank 0 in all four scenarios.

Adding simple planar free-space geometry features from the packaged 630-cell source mask still selected rank 0 in three of four outer scenarios.

Therefore coordinate-only and simple free-space context are insufficient.

## 8. Missing existing input

The scientifically relevant missing context is the already-frozen House02 W2 transport/geometry input:

- canonical W2 `3,5-1_slow` wind iterations 0..10;
- House02 OccupancyGrid3D.csv;
- no new plume realizations are needed.

These assets already existed on the VM in earlier Gate1A/M4 work and have frozen hashes/provenance, but their bytes are not present in the D1R review package or current file library.

## 9. Current decision

`D0_HOLD_NEEDS_EXISTING_WIND_GEOMETRY_CONTEXT`

Do not:
- run new GADEN plume simulations;
- train full DLL diffusion;
- run PMFS closed loop;
- claim stochastic neural operator as the main innovation yet.

Next gate may use only existing wind/occupancy assets plus the completed D1R bank.

STOP if adding true transport context does not make a stochastic operator consistently outperform deterministic/source-mean baselines on source-heldout sparse-observation proper score.