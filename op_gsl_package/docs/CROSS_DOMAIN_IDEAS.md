# Cross-Domain Transferable Ideas for GSL

> 7 far-field domains searched (NOT GSL-specific). Each includes mathematical formulation, transfer rationale, and adaptation notes.

---

## 1. Backward Lagrangian Tracking (Oceanography)

**Source**: GRIPP method — Souza et al., 2025; Reijnders et al., 2025 (stability-aware tracking)

**Core Math**:
Instead of solving forward dispersion (source → concentration), trace particles BACKWARD from observation points through the wind/current field:

```
dx/dt = -u(x, t) + noise     (backward in time)
```

where u is the wind velocity field. The source probability at grid cell (i,j) is:

```
P(source at (i,j)) ∝ Σ_k δ(x_k(T) ∈ cell(i,j))
```

where x_k is the k-th backward particle released from observation point, and T is the trace-back time.

**Why it transfers to GSL**:
- No forward model needed — no Green function, no PDE solver, no kernel mismatch
- Naturally handles non-Gaussian dispersion (particles follow actual wind)
- Works with any wind field (spatially varying, turbulent, with obstacles)
- GRIPP achieves 0.019 degree mean error in ocean currents

**Transfer to UAV GSL**:
```
At each observation (rx, ry, z):
  1. Release N=1000 virtual particles
  2. Trace backward: x_{t-1} = x_t - wind(x_t) * dt + sqrt(2*kappa*dt) * noise
  3. Accumulate particle endpoints in grid → source probability map
  4. P(source at cell) = count(particles ending in cell) / N
```

**Advantages over current approach**:
- No Green function bias (particles spread naturally)
- No PDE discretization error
- Handles obstacles (particles bounce off walls)
- Wind-aware by construction

**Risk**: Requires accurate wind field. VGR provides per-cell wind data.

---

## 2. Sparse Bayesian Learning for Matched-Field Processing (Acoustics)

**Source**: Wang et al., Applied Acoustics 2024 (Fast SBL-MFP); Wang et al., JASA 2024 (ST-SBL-MFP)

**Core Math**:
Build a dictionary A where each column A[:,i] = predicted sensor readings if source were at position i:

```
y = A * x + noise
```

where y = observed concentration vector, x = source indicator (sparse — only 1 source).

Type-II Maximum Likelihood:

```
L(x) = -log|Σ| - y^T Σ^{-1} y
Σ = σ² I + A diag(α) A^T
```

where α are hyperparameters controlling sparsity. Optimize α → sparse x → source location.

**Why it transfers**:
- Does NOT need a perfect forward model (dictionary can be approximate)
- Sparsity prior: there is ONE source (or few), not many
- Spatio-temporal variant exploits: source is FIXED, sensor MOVES (each row of A corresponds to a different time step with different sensor position)
- Handles multi-modal posteriors naturally

**Transfer to UAV GSL**:
```python
# For each candidate source position s:
#   A[:, s] = predicted_concentration_at_all_observation_positions(source=s)
# Solve: min ||y - A*x||² + λ||x||₁
# Source = argmax(x)
```

**Key insight**: The dictionary A encodes the forward model, but the SBL solver is robust to dictionary errors. Even an approximate forward model gives good localization.

---

## 3. BOED for Sensor Placement (Active Learning / Seismology)

**Source**: Huan et al., Acta Numerica 2024; Callahan et al., GJI 2025 (seismic monitoring)

**Core Math**:
Expected Information Gain for choosing next observation position ξ:

```
EIG(ξ) = H[p(θ)] - E_y[H[p(θ | y, ξ)]]
       = H[p(θ)] - Σ_{y∈{0,1}} p(y|ξ) H[p(θ | y, ξ)]
```

where θ = source position, y = binary observation (hit/miss), ξ = candidate sensor position.

Submodular greedy selection guarantees 63% optimality:

```
ξ* = argmax_ξ EIG(ξ)
```

**Why it transfers**:
- Already partially implemented in our EIG height selection
- Can extend to full 3D path planning (position + height)
- Provides theoretical guarantee on exploration quality
- Directly applicable to "where should the UAV fly next?"

**Transfer to UAV GSL**:
```
For each candidate (x, y, z):
  1. Compute p(hit) at (x, y, z) from current posterior
  2. Simulate: if hit → update posterior, compute entropy
  3. Simulate: if miss → update posterior, compute entropy
  4. EIG = H_prior - (p_hit * H_hit + (1-p_hit) * H_miss)
Choose (x, y, z) with max EIG
```

---

## 4. Generative Signal-Based Inference (Seismology)

**Source**: SIGVISA — Moore 2025

**Core Math**:
Instead of extracting features then inverting, model the FULL sensor time-series:

```
p(source | y_{1:T}) ∝ p(y_{1:T} | source) * p(source)
```

where y_{1:T} is the complete sensor time-series (not just hit/miss binary).

**Why it transfers**:
- The temporal pattern (whiff frequency, duration, intensity) carries information about source distance and direction
- Binary thresholding (hit/miss) destroys this information
- SIGVISA shows 4x improvement over extract-then-invert

**Transfer to UAV GSL**:
```
Instead of: z = 1 if conc > threshold else 0
Use: full concentration time-series c(t) at each position

Likelihood model:
  p(c(t) | source at s) = predicted_concentration_profile(s, wind, t)
  where the profile includes intermittency, duration, peak height
```

**Risk**: More complex likelihood model. But the information gain could be substantial.

---

## 5. Variational Sparse Source Imaging (EEG/MEG)

**Source**: VSSI-GGD — Liu et al., IEEE TNSRE 2024; XDL-ESI — Jiao et al., NeuroImage 2024

**Core Math**:
Spatial prior with wavelet decomposition:

```
min ||y - Ax||² + λ₁ ||Wx||₁ + λ₂ ||x||₂²
```

where W = wavelet transform matrix, λ₁ promotes sparsity in wavelet domain (multi-scale), λ₂ regularizes.

**Why it transfers**:
- Multi-scale spatial priors capture both localized and distributed source patterns
- Structural priors: source likely in open space (not inside walls), near outlets
- Algorithm unrolling (XDL-ESI) for fast inference

**Transfer to UAV GSL**:
```
Add spatial prior to posterior update:
  log_posterior += log_prior(x, y, z)
  
where log_prior encodes:
  - Source cannot be inside obstacles (hard constraint)
  - Source likely near walls/outlets (soft prior)
  - Source concentration decreases with distance from source (spatial smoothness)
```

---

## 6. L1 Sparse Plume Inversion (Atmospheric Science)

**Source**: Dooley et al., AMT 2024 (aerial methane attribution); Williams et al., ACP 2025

**Core Math**:
Multiple simultaneous sources with L1 sparsity:

```
min ||y - Ax||₂² + λ||x||₁
```

where x = source strength vector (sparse — few active sources), A = dispersion matrix.

**Why it transfers**:
- Handles multiple potential leak points naturally
- L1 regularization selects the most likely source(s)
- Validated on real aerial methane measurements

**Transfer to UAV GSL**:
```
Grid cells = candidate sources
A[i,j] = predicted concentration at observation j if source at cell i
Solve L1-regularized inverse → sparse source estimate
```

---

## 7. Lagrangian Coherent Structures (Fluid Dynamics)

**Source**: Rao et al., Nature Sci Rep 2024 (persistent LCS)

**Core Math**:
Finite-Time Lyapunov Exponent (FTLE):

```
FTLE(x₀, T) = (1/|T|) log ||∇Φ(x₀, T)||
```

where Φ is the flow map. LCS = ridges of FTLE field = transport barriers.

**Why it transfers**:
- Identifies GEOMETRIC BARRIERS in the flow that constrain where the source can be
- Source cannot be behind an LCS barrier relative to observations
- Provides hard bounds on feasible source regions BEFORE Bayesian inference

**Transfer to UAV GSL**:
```
1. Compute FTLE from wind field
2. Identify LCS ridges
3. Source must be on the same side of LCS as the observations
4. Use LCS as hard constraint in posterior: P(source | LCS) = 0 if behind barrier
```

---

## Combined Architecture (Proposed)

```
Wind Field + Occupancy Grid
         │
         ▼
    LCS Pre-filter (Domain 7)
    → Eliminate impossible source regions
         │
         ▼
    Backward Lagrangian (Domain 1)
    → Source probability from particle tracing
         │
         ▼
    SBL Sparse Recovery (Domain 2)
    → Robust source localization with approximate model
         │
         ▼
    BOED Path Planning (Domain 3)
    → Information-greedy UAV navigation
         │
         ▼
    Full Time-Series Inference (Domain 4)
    → Use raw concentration, not binary hit/miss
         │
         ▼
    3D EIG Height Selection (existing)
    → Adaptive altitude for unknown source height
```

**Key principle**: Each layer adds robustness. If one component fails, the others still provide useful constraints.
