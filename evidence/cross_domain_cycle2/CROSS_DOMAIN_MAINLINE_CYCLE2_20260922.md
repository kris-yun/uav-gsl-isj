# Cross-domain mainline cycle 2 — failure-informed screening on old + independent plume data

Date: 2026-09-22  
Base data commit: `c5271515d565c343d2fd2a63c77bf0484f45772a`  
Status: **NO NEW MAIN LINE PROMOTED; SHADOWING RETAINED AS DATA-INELIGIBLE HIGH-PRIORITY ROUTE**

## 0. Data contract and the lesson from HCMC

This cycle explicitly incorporates the HCMC independent-plume failure.

Development corpus used here:

- old R2 discovery: House01/02/03 × seed0/1;
- six now-unblinded TRUE_INDEPENDENT_PLUME_VALIDATION runs;
- endpoint comparisons are development diagnostics only, never a new holdout.

Critical raw-data correction:

> Each independent-plume accepted run contains exactly one recorded `source_update_0001`, not five source updates.

The direct uploaded archive is byte-identical to the verified GitHub package:

- `ACCEPTED_RAW_CONTEXT.tar.gz`
- SHA-256: `bbed3eaa45442e539843f8f45bab5fa0f796623417fa4c6320089cf47ed54957`

Each new case nevertheless contains a full 1500-step sensor/pose/wind trace. Therefore this cycle only promotes methods that can honestly work from a single candidate bank plus the recorded trajectory.

Native PMFS gas-presence semantics were audited in source:
`thresholdGas = getParam<double>("th_gas_present", 0.1)`.
All trajectory hit-based tests after that audit use **measured_gas_ppm > 0.1 ppm**.

Any earlier exploratory HCCE result based on `gas > 0` is invalid as scientific evidence.

## 1. Promotion rule used in this cycle

A main-line candidate is rejected if any of the following occurs:

1. undefined on a valid independent-plume case;
2. independent-plume subset collapses;
3. principal destructive-null fraction as-good-or-better is materially above 5%;
4. candidate scores do not reproduce across the two independent realizations of the same House;
5. a source-blind geometry baseline explains the endpoint;
6. the implementation requires information not actually present in the recorded data.

This is intentionally stricter than the pre-HCMC discovery process.

---

## 2. Causal emergence / dynamical reversibility — NO-GO

Mother ideas:

- Zhang, Tao, Yang, *Dynamical reversibility and a new theory of causal emergence based on SVD*, npj Complexity (2025), DOI `10.1038/s44260-025-00028-0`.
- *Causal Emergence 2.0: Quantifying emergent complexity* (2025), DOI `10.48550/arxiv.2503.13395`.
- public CE2 implementation inspected: https://github.com/jessescool/Causal-Emergence-2.0

Secondary transfer:
construct a source-conditioned joint candidate/sensor transition process, measure macro causal-power gain, and subtract a geometry-only candidate-distance process.

Important falsification:
the first exploratory implementation used `measured_gas_ppm > 0` and produced about 54.6% / 12-of-12 with very strong null separation. Source audit showed this hit definition was not PMFS-native. **Those numbers are invalidated.**

Under native `>0.1 ppm`:

- fixed equal-quartile version: about **21.8%**, 7/12;
- final-leaf permutation 1000: **55.8%** as good/better;
- temporal shift 30: **50%** as good/better.

A calibration-free empirical-rank state version:

- about **22.1%**, 7/12;
- leaf null: **56.2%** as good/better;
- temporal-shift null: **30%**;
- block-shuffle null: **23.3%**;
- H01 cross-realization candidate-score Spearman only about **0.08**.

Decision: **NO-GO main**. Do not rescue the post-hoc low-tail discretization that happened to score well after the native-threshold result was visible.

---

## 3. Transfer-operator / Ruelle–Pollicott resonance conformance — NO-GO

Mother idea:
Perron–Frobenius / Koopman transfer operators characterize density evolution and dynamical resonances rather than pointwise states.

A source-conditioned eigen/singular fingerprint was tested over multiple lags.

Representative old+new result:

- about **25.7%** pooled reduction;
- **10/12** non-worse.

But:

- final-leaf permutation: about **37%** of nulls as good/better;
- substantial candidate-score correlation with source geometry in several cases.

Decision: **NO-GO main**.

---

## 4. Resolvent / non-normal amplification — geometry-confounded, not promoted

Mother idea:
resolvent analysis treats turbulent dynamics as an input-output amplification operator and extracts non-normal forcing-response structure.

Graph advection-diffusion resolvent screens:

- zero-advection family: about **41.2%**, 10/12;
- physical-wind Pe≈1: about **46.7%**, 10/12;
- other Pe values remained positive.

However the same twelve cases still share the same House source positions. Source-blind geometry controls are stronger:

- rank by distance to coordinate origin: about **66.9%**, 12/12;
- rank by distance to start: about **53.5%**, 12/12.

Directional contrast intended to remove geometry:

- physical-wind minus zero-advection: weak/unstable;
- physical-wind minus reversed-wind: roughly 9–13% in the better predeclared range, not robust.

Decision: **NOT PROMOTED**. Any resolvent/non-normal route requires source-position-transfer data before further endpoint claims.

---

## 5. Non-Hermitian reciprocity breaking — NO-GO

Mother idea:
advection makes the transport generator non-self-adjoint, so forward and reverse Green responses exhibit directional reciprocity breaking.

A source score based on forward/reverse Green asymmetry was tested using native gas-hit semantics.

Natural hit-contrast form:

- Pe≈1: about **13.8%**, 10/12;
- Pe≈4: about **26.6%**, 9/12.

But for the natural Pe≈1 score:

- final-leaf permutation 300: approximately **89.7%** of nulls as good/better.

Some hit-only variants had larger endpoint numbers but were not promoted because they omit the no-hit trajectory and are strongly geometry/exposure-confounded.

Decision: **NO-GO main**.

---

## 6. Nonequilibrium entropy production / time-arrow — NO-GO

Mother ideas:
2025–2026 nonequilibrium statistical physics on coarse-grained irreversibility and entropy production.

A joint candidate-state / measured-hit process was used to estimate forward-vs-reverse transition-flux asymmetry, subtracting candidate-only and geometry counterparts.

Natural K=4, lag=1:

- about **28.1%**, 10/12.

But:

- final-leaf permutation: approximately **19.5%** as good/better.

Decision: **NO-GO main**.

---

## 7. Mori–Zwanzig projected memory — NO-GO current transfer

Mother ideas:

- *Data-driven Mori–Zwanzig modeling of Lagrangian particle dynamics in turbulent flows*, PNAS 2026, DOI `10.1073/pnas.2525390123`.
- *Learning turbulent transport via Mori--Zwanzig graph neural networks*, 2026, DOI `10.48550/arxiv.2606.14918`.

The scientific attraction is strong: unresolved turbulent degrees of freedom appear as non-Markovian memory plus orthogonal fluctuations.

Tested transfer:
candidate plume sequence sampled on the robot path is added as a resolved variable; source candidates are compared by finite-memory predictive closure and by whitening of the unresolved residual.

Results:

- current-only candidate forcing: about **20.2%**, 8/12;
- memory horizons were non-monotonic and no stable memory scale dominated;
- residual-whitening family: roughly **14–17%**, typically 9–10/12;
- representative white10: **16.5%**, 10/12.

Mechanism failure for white10:

- leaf permutation 300: **82%** as good/better;
- large temporal shifts and full candidate-sequence shuffles frequently match or improve the real result.

Decision: **NO-GO main**. The mother theory remains scientifically relevant, but the present source-conditioned transfer does not demonstrate load-bearing MZ memory.

---

## 8. Krylov complexity / operator growth — promising-looking but fails the null gate

Mother idea:
Krylov complexity measures how rapidly dynamical evolution spreads through the minimal Krylov subspace. Recent 2026 work establishes a classical–quantum correspondence (J. Phys. A; arXiv `2603.11034`).

Transfer:
form source-conditioned delay-Krylov matrices from candidate plume sequence and measured sensor trajectory; measure shared effective dynamical dimension after subtracting a pure candidate-distance geometry process.

Eight-member family:
- spectral effective-rank / participation-rank;
- four fixed delay lengths.

Source-blind median family consensus:

- old+new: about **32.9%**, 10/12;
- old subset: about **22.8%**, 5/6;
- independent-plume subset: about **42.2%**, 5/6.

Cross-realization candidate-score Spearman:
- H01 ≈ **0.85**
- H02 ≈ **0.62**
- H03 ≈ **0.99**

But:

- final-leaf permutation 500: **9.6%** as good/better.

Decision: **NO-GO main under the current ≤5% destructive-null gate**.

---

## 9. Computational mechanics / epsilon-machine causal states — NO-GO

Mother idea:
computational mechanics reconstructs the minimal predictive architecture of a stochastic process as causal states / an epsilon-machine.

Current cross-domain anchors:
- 2026 MNRAS/arXiv work on epsilon-machine reconstruction of causal structure in repeating fast-radio-burst timing;
- current public implementation: https://github.com/johnazariah/emic

Transfer:
for every source candidate, construct a source-conditioned symbolic process and approximate predictive causal-state compression; compare predictive information per statistical complexity and subtract a geometry-only process.

Nine-member family over history length and sampling interval.

Family median consensus:

- about **36.5%**, 8/12;
- final-leaf permutation 500: only **3.0%** as good/better.

This would previously have been promoted. It is rejected now because the source-candidate mechanism does not reproduce across independent plume realizations:

- H01 score Spearman ≈ **-0.18**
- H02 ≈ **-0.09**
- H03 ≈ **0.01**

Decision: **NO-GO main**. Endpoint success with non-reproducible source ranking is treated as another benchmark/geometry artifact.

---

## 10. Generalized synchronization / recurrence structure — early NO-GO

Mother idea:
two chaotic systems can share a functional synchronization relation despite pointwise trajectory divergence.

A recurrence-neighborhood overlap between candidate plume trajectory and continuous sensor trajectory was tested after subtracting candidate-distance recurrence.

Best fixed family member reached roughly:

- **26.1%**, 9/12,

but the independent-plume subset was only **4/6** non-worse and H01 remained unstable.

Decision: **EARLY NO-GO**. Destructive-null budget was not spent after this failure.

---

## 11. Rough-path / path-signature directional interaction — early NO-GO

Mother idea:
rough-path signatures encode ordered interactions of irregular stochastic trajectories through iterated integrals.

2026 cross-domain anchor:
*Quickest Detection with Rough Path Signatures*, arXiv `2607.22958`.

A level-2 antisymmetric path-area transfer was tested between source-candidate trajectory and continuous sensor trajectory, subtracting geometry-only path area.

Family behavior was not stable:
- some windows produced 20–31% aggregate gains;
- the apparently strongest independent-plume result coincided with approximately zero/negative old-subset gain.

Decision: **EARLY NO-GO** due environment instability. No parameter selection by endpoint.

---

## 12. Reaction-coordinate / committor / Transition Path Theory — current data-domain failure

Mother idea:
in molecular rare-event dynamics the committor is the optimal reaction coordinate, and reactive current/transition paths reveal the mechanism.

2026 anchors include:
- *Following the Committor Flow: A Data-Driven Discovery of Transition Pathways*, JCTC 2026, DOI `10.1021/acs.jctc.6c00007`;
- *Reactive Flux Matching: Mechanism Discovery and Adaptive Sampling of Rare Events*, 2026 preprint.

Transfer:
treat each candidate source sequence as a proposed reaction coordinate for transitions between no-gas and gas states.

Failure:
at least the low-excitation H01 independent realization does not contain enough native-threshold reactive 0→1 events for a stable source-conditioned reactive-flux score. Some cases become undefined.

Decision: **NO-GO CURRENT IMPLEMENTATION** under the hard definability gate. Do not tune event windows to rescue it.

---

## 13. Fluctuation–Response / FDT closure — NO-GO

Mother ideas:
2026 nonequilibrium fluctuation-response theory, including:

- *Fluctuation-Response Theory for Nonequilibrium Langevin Dynamics*, arXiv `2601.16387`;
- *Nonequilibrium Fluctuation-Response Theory in the Frequency Domain*, arXiv `2605.05038`;
- Lucarini, *Interpretable and equation-free response theory for complex systems*, Phil. Trans. A 2026.

Transfer:
estimate local source-position susceptibility (partial q/partial s_x,partial q/partial s_y) from neighboring candidates and compare its frequency-domain response spectrum with the measured sensor fluctuation spectrum; subtract the same construction built from source-to-robot geometry.

Result:
- old subset often showed roughly 20–29% apparent gain;
- independent-plume subset was near zero or negative for most family members (typically only 2–3/6 non-worse).

Decision: **NO-GO** before spending additional null budget.

---

## 14. Least-squares shadowing — high-priority mother idea, but DATA-INELIGIBLE now

This is the most directly failure-informed route found in this cycle.

2026 JFM:
*Mitigating adjoint chaos in wall turbulence*, DOI `10.1017/jfm.2026.11822`.

The paper explicitly frames chaotic inverse/sensitivity problems as ill-conditioned when one tries to follow a single trajectory, and discusses least-squares shadowing as replacing the unstable initial-value trajectory by a nearby dynamically valid shadow trajectory.

Mature public prototype:
https://github.com/niangxiu/nis  
(`NILSS: Non-Intrusive Least Squares Shadowing`, accompanying Ni & Wang's JCP implementation.)

Why this fits the HCMC failure:
- different turbulent plume realizations are not required to match pointwise;
- a correct source is tested by whether a **dynamically admissible nearby trajectory** can shadow the observations;
- the object is trajectory-level dynamical consistency, not a realization-specific spatial invariant.

Why it is not tested here:
the current candidate bank stores a source-conditioned spatial hit field at one update. Sampling that static field along the robot path is **not** a full source-conditioned turbulent plume trajectory. Running NILSS on it would be a category error.

Required minimal new data, much smaller than a generative-model training corpus:

1. choose a modest frozen set of source candidates per House;
2. for each candidate, run/save synchronized counterfactual sensor-at-trajectory time series or a compact temporal plume state;
3. keep actual robot pose/wind trajectory fixed for the mechanism screen;
4. evaluate source-conditioned shadowing cost without truth-tuned hyperparameters;
5. destructive controls: time permutation, wrong-wind/reversed-wind, candidate identity permutation;
6. only if source ranking reproduces across independent plume realizations should a localization posterior be constructed.

Status: **HIGH-PRIORITY / DATA-INELIGIBLE / NOT PROMOTED**.

---

## 15. New process conclusion

This cycle intentionally produced many NO-GOs. That is the desired behavior after HCMC.

The main methodological lesson is:

> A large endpoint improvement on old+new cases is still insufficient if the candidate ranking is not realization-reproducible, if geometry explains it, or if destructive nulls can reproduce it.

The next main-line candidate must simultaneously survive:
- old + independent plume development data;
- source-blind definability;
- cross-realization candidate-score reproducibility;
- destructive nulls;
- source-position/geometry controls.

### Immediate next queue

1. **Shadowing / NILSS** — strongest failure-informed mother idea, requires a small new counterfactual temporal bank.
2. **Hodge/Helmholtz flow decomposition** — directly testable next; 2026 work applies Hodge decomposition to information/physical flows and separates gradient, curl, harmonic components.
3. **Macroscopic fluctuation theory / path action** — scientifically strong but current one-dimensional sensor path is insufficient for an honest spatial current-field implementation; do not fake it.
4. Continue Scite search only for genuinely orthogonal physics/math/complex-systems principles, not generic inference tools.
