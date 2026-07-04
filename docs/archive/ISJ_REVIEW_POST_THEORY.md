# ISJ Senior Associate Editor Review — Theory Improvement Assessment
**Date**: 2026-07-04
**Paper**: "Anytime-Valid Sequential Testing for Robust UAV Gas Source Localization"
**Previous Score**: 6.0-6.5/10
**Current Assessment**: Post-theory-improvement review

---

## 1. THEORY ASSESSMENT (Updated)

### 1.1 Proposition 1 (Identifiability): 7/10 ↑ (was 5/10)

**Improvements:**
- Formal Definition 1 (Source Identifiability) added
- Proposition 1 proves identifiability under filament-based dispersion with two explicit conditions
- Conditions are mild and physically meaningful: non-zero wind + non-empty interior
- Remark about degenerate cases strengthens the argument

**Remaining concerns:**
- The proof uses an informal argument ("filament trajectories differ") rather than a formal measure-theoretic argument
- A reviewer might ask for explicit computation of p(z|s1) vs p(z|s2) for a simple case

**Verdict: Acceptable for ISJ.** The identifiability proof is non-trivial and GSL-specific.

### 1.2 Proposition 2 (Approachability): 7/10 ↑ (was 5/10)

**Improvements:**
- Now properly builds on Proposition 1 (identifiability -> posterior consistency -> approachability)
- Explicitly states the two conditions: posterior consistency + action richness
- Action richness argument is clear: positive entropy -> exists informative action

**Remaining concerns:**
- Still relies on citing Blackwell 1956, but now with GSL-specific justification
- Posterior consistency reference (Ghosal & van der Vaart 2017) is appropriate

**Verdict: Good for ISJ.** Well-structured proof chain.

### 1.3 Theorem 1 (Anytime-Valid Stopping): 7.5/10 (unchanged)

**Improvements:**
- Lemma 1 (Super-Martingale Property) added with explicit proof
- Sub-exponential tail assumption is stated and used
- Parameter selection guidelines (η = θ^-1) provided
- Comparison with CP is clearer

**Remaining concerns:**
- The sub-exponential tail assumption for MAP residuals is not empirically verified
- A reviewer will ask: "Do MAP residuals actually have sub-exponential tails?"
- The proof has a subtle issue: the conclusion "for η sufficiently small" is vague

**Verdict: Acceptable with caveats.** Need empirical validation of tail assumption.

### 1.4 Conjecture 1 (Search-Stop Coupling): 5.5/10 ↑ (was 4/10)

**Improvements:**
- Honestly converted to Conjecture (not claimed as proven)
- Clear motivation provided
- Empirical evidence referenced

**Remaining concerns:**
- A conjecture in an ISJ paper is risky - reviewers may see it as incomplete work
- Need strong empirical support to justify including it

**Verdict: Marginal.** Consider either: (a) proving a weaker version, or (b) removing and replacing with empirical observation.

### 1.5 Overall Theory Score: 7.0/10 ↑ (was 6.0/10)

**Summary:** The theory has improved significantly. The main strengths are:
1. Formal identifiability proof specific to filament-based GSL
2. Super-martingale proof with explicit assumptions
3. Honest handling of the coupling result (conjecture vs unproven claim)

**Gap to 8/10:**
- Empirical validation of sub-exponential tail assumption (+0.3)
- Either prove coupling or remove it (+0.3)
- Computation of information gain lower bound under filament model (+0.4)

---

## 2. EXPERIMENT ASSESSMENT

### 2.1 Current State: 5.5/10

**VGR Data:**
- 31 runs completed (Full method seeds 0-9, NoDDM seed 0)
- map_dist not recorded by benchmark_runner (must extract from logs)
- All distances need manual computation

**PMFS Data:**
- 1 run completed, algorithm converged to wrong location (7m error)
- Wind field too weak for current parameters
- Need to investigate and fix

**Baselines:**
- SurgeCast/PMFS/GrGSL: n=3 (insufficient for ISJ)

### 2.2 Key Experiment Issues

1. **Distance extraction broken**: benchmark_runner does not record map_dist. Need Python script to extract from RESULT lines in logs.
2. **PMFS integration failing**: Algorithm converges to wrong location in PMFS environment.
3. **Baseline n too small**: n=3 gives no statistical power.

### 2.3 Recommendations

1. **Immediate**: Extract distances from ALL existing VGR logs (31 runs + old logs)
2. **This week**: Investigate PMFS wind data loading - check if wind is actually being published
3. **This week**: Run baselines with n=10

---

## 3. OVERALL READINESS

| Criterion | Before | After | Target |
|-----------|--------|-------|--------|
| Theory | 6.0 | 7.0 | 8.0 |
| Experiments | 5.5 | 5.5 | 7.0 |
| Presentation | 6.0 | 7.0 | 7.0 |
| **Overall** | **6.0** | **6.5** | **7.5** |

### Minimum to Submit to ISJ (7.0+):

1. [ ] Extract all VGR distances from logs (1-2 hours)
2. [ ] Fix PMFS integration (investigate wind loading)
3. [ ] Run baselines with n=10 (VM time)
4. [ ] Empirically validate sub-exponential tail assumption (1 Python script)
5. [ ] Either prove coupling or remove it (decision needed)

### Time Estimate: 1-2 weeks to reach 7.0

---

## 4. POSITIVE CHANGES

1. **Identifiability proof is genuinely new** - no prior work proves this for filament-based GSL
2. **Super-martingale proof is rigorous** - explicit assumptions, clear derivation
3. **Multi-dataset plan (PMFS)** - addresses single-dataset criticism
4. **Honest conjecture handling** - better than unproven claims

## 5. REMAINING RISKS

| Risk | Probability | Severity | Mitigation |
|------|-------------|----------|------------|
| PMFS integration fails | High | High | Use different wind config or fall back to VGR-only with more source positions |
| Sub-exponential tail doesn't hold | Medium | Medium | Add empirical validation figure |
| Reviewer rejects conjecture | Medium | Medium | Remove coupling claim, focus on empirical evidence |
| Baselines n=3 criticized | High | Medium | Increase to n=10 |