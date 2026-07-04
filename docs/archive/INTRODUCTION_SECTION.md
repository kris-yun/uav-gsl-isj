# Introduction Section (Draft)

## 1. Introduction

### 1.1 Background and Motivation

Unmanned aerial vehicles (UAVs) equipped with gas sensors have emerged as promising platforms for autonomous gas source localization (GSL), with applications ranging from industrial leak detection to environmental monitoring and disaster response [1,2]. In these scenarios, a UAV must navigate through an environment to locate the source of a gas emission, often under time pressure and with limited prior knowledge of the source location.

The fundamental challenge in UAV GSL is that gas dispersion in indoor or complex outdoor environments is driven by turbulent transport, resulting in intermittent, filamentary plume structures [3,4]. Unlike the smooth concentration gradients assumed by classical diffusion models, real gas plumes exhibit sharp spatial boundaries and temporal intermittency—a sensor may read high concentrations at one moment and near-zero readings seconds later, even without the UAV moving [5].

### 1.2 Limitations of Existing Methods

Current GSL methods can be broadly categorized into three families, each with distinct failure modes:

**Upwind-tracking methods** (e.g., SurgeCast [6]) track the gas plume upwind toward the source. These methods achieve excellent performance when the UAV starts within a strong plume (mean distance 0.4m in favorable conditions), but degrade dramatically when the initial gas signal is weak or intermittent. In our experiments, SurgeCast's localization error increases by 8× (from 0.4m to 3.3m) when the starting position has weak plume contact—a common scenario in real deployments where the UAV's initial position is arbitrary.

**Plume-model methods** (e.g., PMFS [7], GrGSL [8]) fit parametric dispersion models (typically Gaussian plumes) to observed concentrations and use the fitted model to infer source location. However, when the actual dispersion mechanism deviates from the model assumptions—as is the case with filament-based transport in indoor environments—these methods systematically fail (3–8m error across all tested conditions).

**Information-theoretic methods** (e.g., Infotaxis [9]) select actions to maximize expected information gain about the source location. While theoretically elegant, standard Infotaxis lacks a principled stopping criterion: the algorithm has no mechanism to declare "the source has been found" with any confidence guarantee.

### 1.3 The Stopping Problem

A critical and under-studied challenge in GSL is deciding *when to stop searching*. Existing methods either:
- Run for a fixed number of steps or until timeout (wasting energy if the source is found early), or
- Use ad-hoc convergence criteria (e.g., "MAP hasn't moved for K steps") without formal guarantees

In safety-critical applications such as hazardous material leaks, premature termination can lead to false source declarations and misdirected emergency response. Conversely, unnecessarily prolonged searches waste time and battery life. Neither failure mode is acceptable, yet no existing GSL method provides formal guarantees on false termination probability.

### 1.4 Our Approach

We address these challenges through a unified framework based on two recent advances in sequential statistical inference:

**Anytime-Valid Inference (AVI)** [10,11] provides a framework for sequential hypothesis testing where the stopping time need not be pre-specified. At its core are *e-processes*—products of non-negative random variables (e-values) that maintain validity under arbitrary stopping rules, without requiring exchangeability assumptions. This makes AVI particularly suited for GSL, where the posterior distribution changes at each step (violating the exchangeability assumption required by conformal prediction methods [12]).

**Blackwell Approachability** [13,14] provides a game-theoretic framework for characterizing achievable objectives in sequential decision problems. By modeling the UAV-environment interaction as a repeated vector-valued game, we can jointly optimize search efficiency, stopping decisions, and risk sensitivity within a single theoretical framework.

### 1.5 Contributions

Our contributions are as follows:

1. **Unified Framework.** We formulate UAV GSL as a sequential decision problem and prove that the coverage-efficiency target set is approachable under mild identifiability conditions (Proposition 0), providing a theoretical foundation for joint search-stopping optimization.

2. **Anytime-Valid Stopping.** We construct an e-process from posterior convergence indicators (MAP residuals) and prove that the resulting stopping rule satisfies $\mathbb{P}(\text{false positive}) \leq \delta$ at any stopping time, without exchangeability assumptions (Theorem 1). This is, to our knowledge, the first application of anytime-valid inference to robotic source localization.

3. **Risk-Adjusted Search.** We employ a risk-adjusted information-directed sampling strategy that balances exploration and exploitation, and prove that this strategy accelerates the e-process convergence (Proposition 2).

4. **Experimental Validation.** We validate our approach on three indoor environments with varying signal strengths using the VGR filament-based simulator. Our method achieves consistent localization performance (1.2–2.1m mean distance) across all environments, with 2× lower cross-environment variance than SurgeCast, while the e-process stopping criterion fires in 85% of runs (compared to 0% for previous conformal prediction-based approaches).

### 1.6 Paper Organization

Section 2 formalizes the problem. Section 3 presents our method. Section 4 provides the theoretical analysis. Section 5 reports experimental results. Section 6 discusses implications and limitations.