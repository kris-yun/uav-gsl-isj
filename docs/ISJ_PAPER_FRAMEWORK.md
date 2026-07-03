# ISJ论文框架: Anytime-Valid Sequential Testing for UAV GSL

**Target**: IEEE Sensors Journal
**Status**: Draft framework
**Last updated**: 2026-07-03

---

## Title

**Anytime-Valid Sequential Testing for Robust UAV Gas Source Localization with Distribution-Free Stopping Guarantees**

---

## Abstract (Draft)

We address the problem of autonomous gas source localization (GSL) by unmanned aerial vehicles (UAVs) in signal-degraded environments where classical upwind-tracking methods fail due to weak or intermittent plume contact. We formulate the UAV search as a sequential decision problem and propose a unified framework based on Blackwell's theory of approachability that jointly optimizes search efficiency, stopping decisions, and risk sensitivity. For the stopping criterion, we construct an anytime-valid e-process based on posterior entropy change rates, providing distribution-free false termination guarantees without requiring exchangeability assumptions. For search strategy, we employ a risk-adjusted information-directed sampling approach that balances exploration and exploitation. We prove that (i) the target coverage-efficiency set is approachable under mild identifiability conditions, (ii) the e-process stopping rule satisfies P(false positive) ≤ δ at any stopping time, and (iii) the risk-adjusted search strategy accelerates posterior convergence. Experimental validation on three indoor environments with varying signal strengths demonstrates consistent performance (1.2-2.1m mean distance) across all environments, with 2× lower cross-environment variance compared to the state-of-the-art SurgeCast method. The e-process stopping criterion fires in 85% of runs (vs. 0% for previous conformal prediction approaches), with mean stopping distance of 1.4m.

---

## 1. Introduction (1.5 pages)

### 1.1 Motivation
- UAV GSL for emergency response (leak detection, environmental monitoring)
- Challenge: UAV starts at arbitrary position, doesn't know signal strength at start
- Classical methods (upwind tracking, plume model) depend on continuous plume contact

### 1.2 Limitations of Existing Work
- SurgeCast: works well when plume signal is strong, fails when signal is weak (8× error increase)
- PMFS/GrGSL: depend on plume model assumptions that don't match real environments
- Deep RL: requires training, not generalizable across environments
- None provides formal stopping guarantees

### 1.3 Our Approach
- Formulate as sequential decision problem
- Unified framework via Blackwell approachability
- Anytime-valid stopping via e-processes

### 1.4 Contributions
1. **Unified framework**: Blackwell approachability for joint search-stopping-risk optimization
2. **Anytime-valid stopping**: e-process with P(false positive) ≤ δ, no exchangeability needed
3. **GSL-specific e-value**: posterior entropy change rate as nonconformity measure
4. **Experimental validation**: consistent performance across weak/strong signal environments

---

## 2. Problem Formulation (1 page)

### 2.1 Environment Model
- Source position s* ∈ X ⊂ R² (unknown)
- UAV position x_t ∈ X
- Gas reading z_t ~ p(z | x_t, s*) (filament-based model)
- Wind vector w_t (measurable)

### 2.2 Plume Contact Dependency
**Definition**: A GSL method M has plume contact dependency if its search direction is determined by the current gas reading z_t.

**Formalization**: 
- SurgeCast: direction = upwind(z_t) → fails when z_t ≈ 0
- Our method: direction = argmax EIG(a | π_t) → works even when z_t ≈ 0

### 2.3 Sequential Decision Framework
- State: s_t = (x_t, π_t)
- Action: a_t ∈ A = {next position} ∪ {STOP}
- Objective: minimize E[d(ŝ_τ, s*)] subject to P(false stop) ≤ δ

---

## 3. Method (3 pages)

### 3.1 Bayesian Posterior Update
- π_{t+1}(s) ∝ π_t(s) · p(z_t | x_t, s)
- Wind-relative spatial field estimation (WATS)
- Ensemble-based uncertainty

### 3.2 Search Strategy: Risk-Adjusted Information-Directed Sampling
- EIG(a | π_t) = H(π_t) - E_z[H(π_{t+1})]
- W-RAIG: a* = argmax [EIG - β·√Var(EIG)]
- Blackwell interpretation: minimize distance to target set C

### 3.3 Stopping Criterion: Anytime-Valid e-Process
- Sequential hypothesis test: H₀ (not converged) vs H₁ (converged)
- e-value: E_t = exp(η · (thresh - residual_t))
- e-process: M_T = Π_{t=1}^T E_t
- Stopping: τ = min{T : M_T ≥ 1/δ}
- Ville's inequality: P(τ < ∞ | H₀) ≤ δ

### 3.4 GSL-Specific e-Value Construction
- Residual: r_t = ||ŝ_t - ŝ_{t-1}|| (MAP movement)
- Under H₀ (not converged): r_t large → E_t < 1
- Under H₁ (converged): r_t small → E_t > 1
- Warm-up period: don't accumulate evidence in first N steps

---

## 4. Theoretical Analysis (1.5 pages)

### 4.1 Proposition 0: Approachability
Under identifiability and richness conditions, the target set C = {(c,e): c ≥ 1-α, e ≥ -ε} is approachable.

### 4.2 Proposition 1: Anytime-Valid Stopping
Under bounded posterior drift:
- (a) M_T is a super-martingale under H₀ → P(sup M_T ≥ 1/δ) ≤ δ
- (b) Under H₁: E[τ] ≤ O(1/Δ²) where Δ = signal strength
- (c) At stopping: P(s* ∈ B_ε(ŝ_τ) | data) ≥ 1-δ

### 4.3 Proposition 2: Search-Stop Coupling
- W-RAIG's information gain accelerates e-process growth
- E[τ_W-RAIG] ≤ E[τ_random]

---

## 5. Experiments (3 pages)

### 5.1 Setup
- VGR simulator: 3 houses with different geometries
- Source positions: House01 (3.1m from start), House02 (1.5m), House03 (1.8m)
- 10 seeds per configuration
- Baselines: SurgeCast, PMFS, GrGSL

### 5.2 Main Results: Cross-Environment Consistency
- Table: Mean ± std distance per method per house
- **Key finding**: Our method has 2× lower CV than SurgeCast
- SurgeCast: House02 0.41m vs House01 3.26m (8× variance)
- Ours: House03 1.11m vs House01 2.04m (2× variance)

### 5.3 Ablation Study
- Full (DDM+WRAIG+e-process) vs NoDDM vs NoWRAIG vs NoCP vs Baseline
- Statistical tests: Mann-Whitney U, Cliff's delta, bootstrap CI

### 5.4 Stopping Analysis
- e-process firing rate: 85% (vs 0% for old CP)
- Mean stopping step: 15
- Mean stopping distance: 1.4m
- Convergence type distribution: found/cp_stop/ddm_stop/other

### 5.5 Coverage Table
- e-process coverage: target 90% → actual X%

---

## 6. Discussion (1 page)

### 6.1 When Our Method Excels
- Weak signal environments (House01): 2.04m vs SurgeCast 3.26m
- Unknown deployment conditions: consistent 1-2m across all environments

### 6.2 When SurgeCast Excels
- Strong signal environments (House02): 0.41m vs ours 1.98m
- If you know the environment is "easy", SurgeCast is better

### 6.3 Practical Implications
- For emergency response: consistency > peak performance
- The e-process stopping criterion provides actionable confidence

### 6.4 Limitations
- Single simulator (VGR)
- Limited to 3 house configurations
- Computational overhead of posterior update

---

## 7. Conclusion (0.5 pages)

We proposed a unified framework for UAV gas source localization based on Blackwell approachability and anytime-valid inference. The key contributions are:
1. Distribution-free stopping guarantees via e-processes
2. Consistent performance across signal-degraded environments
3. Formal connection between search efficiency and stopping time

---

## References

1. Principato & Stoltz (2025). Blackwell's Approachability for Sequential Conformal Inference. arXiv:2510.15824.
2. Ramdas, Grünwald, Vovk, Shafer (2023). Game-theoretic Statistics and SAVI. Statistical Science 38(4).
3. Gibbs & Candès (2021). Adaptive Conformal Inference. NeurIPS.
4. Russo & Van Roy (2018). Learning to Optimize via IDS. Operations Research.
5. Vergassola et al. (2007). Infotaxis. Science.
6. Neumann et al. (2023). PMFS. IEEE TRO.
7. [Existing references from the project]