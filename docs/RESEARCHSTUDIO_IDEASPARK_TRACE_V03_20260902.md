# ResearchStudio IdeaSpark trace — CTPI full-law V0.3

Date: 2026-09-02

This trace applies the public `microsoft/ResearchStudio` `ResearchStudio-Idea/skills/idea_spark` process to the current robotic gas-source-localization direction. It is a development/falsification trace, not independent confirmation.

## Phase 0 — literature grounding

| ID | year | work | what it closes | residue relevant here |
|---|---:|---|---|---|
| G1 | 2024 | Ojeda et al., *Robotic Gas Source Localization with Probabilistic Mapping and Online Dispersion Simulation* (IEEE T-RO) | probabilistic gas-hit mapping + online filament dispersion + source posterior | repeated candidate simulation; count-only F00 later shown to carry strong coarse source evidence, but the final inference still totally orders source hypotheses |
| G2 | 2024 | Jin & Martinoli, *Sense in Motion with Belief Clustering* (ICRA) | continuous sensing while moving and sensor-dynamics-aware operation | does not formulate source inference as partial identification of stochastic transport laws |
| G3 | 2025 | Tian et al., *Deep Learning Based Topography Aware Gas Source Localization with Mobile Robot* (ICRA) | learning-based topology-aware source localization | direct source prediction; no source-intervention identifiability geometry |
| G4 | 2025 | Jin et al., *Cumulative Informative Path Planning for Efficient Gas Source Localization* (IROS) | cumulative information planning | consumes a source belief; does not question whether the current observation supports a total source ordering |
| G5 | 2025 | pre-calculated air-contaminant distribution database source-localization method (Building and Environment) | fast source localization using precomputed distributions | environment-specific bank; not unknown-site partial identification |
| G6 | 2026 | Jin et al., *Calibration-Free Gas Source Localization... Measurement Ranking* | source inference without sensor calibration by rank features | still produces a probabilistic source-location distribution; removes calibration, not transport-law non-identifiability |
| G7 | 2026 | Kim et al., *Deep Probabilistic Indoor Gas Source Localization via Physical Dependency-Guided Sequential Inference* | fast probabilistic indoor GSL with explicit wind/concentration dependency chain | source is explicitly a categorical distribution over grid cells; uncertainty is modeled but every update still produces a total posterior over source cells |
| G8 | 2026 | Jin et al., *Probabilistic Multi-Robot Gas Source Localization with Uncalibrated Sensors* | distributed calibration-free local beliefs + product-of-experts fusion | belief fusion still assumes a source probability ordering is the appropriate inferential object |
| C1 | 2026 | Andreou et al., *Assimilative Causal Inference* (Nature Communications) | inverse causal reasoning via data assimilation | theoretical support for backward cause inference, not a GSL partial-identification solution |
| C2 | 2026 | Chen & Darwiche, *On the Granularity of Causal Effect Identifiability* (UAI) | state-level causal effects can be identifiable when variable-level effects are not, with context knowledge | supports changing causal resolution; does not define route-conditioned source laws for GSL |
| C3 | 2026 | *Partially Observed Structural Causal Models* (UAI) | causal identifiability under partial observation/context | supports the partially observed causal setting; not a GSL mechanism |
| C4 | 2026 | Lin et al., *Causal Partial Identification via Conditional Optimal Transport* (AISTATS) | set-valued causal identification when point identification is impossible | supports identified sets as legitimate outputs; does not supply the GSL response object |

### Closest adjacent / anchor

**G7 is the anchor.** It is the closest recent direct GSL paper because it explicitly represents indoor physical dependencies and outputs a probabilistic source posterior under sparse measurements. Its remaining assumption is exactly the one audited here: source inference is formulated as categorical classification over cells, so uncertainty changes probability mass but not the inferential granularity itself.

## Phase 1 — bottleneck identification

### Method lineage

1. **Root (>16y): Bayesian/Infotaxis source search.** Maintain a probability law over candidate source locations and plan from uncertainty/information gain.
2. **8–16y: model-based probabilistic GSL.** Add physical dispersion uncertainty while retaining source-location posterior inference.
3. **2–4y: PMFS.** Improve indoor physical realism through probabilistic gas-hit maps and online stochastic dispersion, still collapsing candidate evidence into a scalar source update.
4. **0–2y frontier leaves:** continuous-sensing GSL, topology-aware deep GSL, cumulative informative planning, calibration-free ranking, physical-dependency deep probabilistic GSL. They modify sensing, representation, computation, or planning but continue to output a totally ordered/probabilistic source field.

### Bottleneck statement

In sparse, stochastic indoor plume transport, different source interventions can induce response laws that are distinct as distributions while becoming identical after the scalar compression used by the source likelihood. The current probabilistic-GSL lineage therefore cannot express the observation-conditioned resolution limit of the source space: it must assign a total probability ordering even when the retained statistic does not identify that ordering. The frozen CPIR evidence makes this operational rather than philosophical: coarse intervention reachability moved the true source forward while retaining a broad belief, whereas persistent-sensor and stop-resolved refinements failed. The missing quantity is not another sharper posterior but a source-intervention response geometry that determines what the current route can identify before source attribution is permitted.

### Gaps left open

1. **Mean-projection aliasing:** candidate stochastic response laws can collapse to the same scalar F00 physical likelihood even when their full laws differ. — stakes: the localizer can be forced to break a physically unsupported tie using prior/model artifacts.
2. **Resolution is not an output:** current GSL posteriors encode uncertainty but not the distinction between “low probability” and “not identifiable under this observation operator.” — stakes: a sharp but wrong posterior can look more decisive than a broad but physically correct source set.
3. **Finite-ensemble evidence has no intrinsic robustness scale:** a source ordering can depend on one transport realization. — stakes: a nominal source ranking can be a Monte-Carlo accident rather than a transport-supported distinction.

## Phase 2.1 — gap × pattern selection

One anchor story is sufficient; no parallel sibling machinery is admitted.

### Pattern chain

1. `assumption_audit_and_pivot` — audit the inherited assumption that every update must totally order source candidates using scalar evidence.
2. `characterize_limit_then_surpass` — characterize exactly what F00 loses under its mean projection and construct a full-law operator that strictly separates some mean aliases.
3. `reframe_as_solvable_object` — use the resulting source-law geometry to formulate GSL as set-valued causal partial identification rather than mandatory categorical classification.

All three pairings are listed as attested companion combinations by ResearchStudio. None of the three reject-favored `heterogeneous_decomposition` compositions is used.

## Phase 2.2 — candidate

### Candidate title

**CTPI-FL: Causal Transport Partial Identification from Full Route-Encounter Laws**

### M1 — CREL: Causal Route-Encounter Law

Input:

`do(S=s)` source query + `do(X_1:t=x_obs)` clamp of the already executed sensing trajectory + map/wind context + frozen/deployable transport mechanism.

Oracle output:

\[
\widehat P_{s,t}(K)=\frac1M\sum_{m=1}^M\delta_{K_{sm,t}},
\qquad
K_{sm,t}=\sum_{j\in V_t}E_{smj}.
\]

M1 does **not** read measured gas. It asks what encounter-count law the source intervention can cause along the already executed route.

### M2 — CDIG: Causal Distributional Identifiability Geometry

F00 count-only physical evidence factors through

\[
T_s=\sum_m K_{sm,t}.
\]

Indeed, for `N` visible stops and `M` members,

\[
\bar q_s=\frac{T_s+N/2}{N(M+1)}.
\]

Therefore `T_i=T_j` implies identical F00 physical likelihood for every observed hit count `H`.

CDIG retains the complete empirical histogram and CDF. Its theorem-linked separation is

\[
G_{ij}=\sum_{k=0}^{N-1}\left(C_i(k)-C_j(k)\right)^2,
\]

where `C_i(k)` is the empirical cumulative count. `G=0` iff the empirical laws are identical.

For physical interpretability it also reports

\[
R^T_{ij}=\frac12\sum_k|n_i(k)-n_j(k)|,
\]

the number of member outcomes outside the two empirical histograms' maximal common overlap (equivalently, the minimum number of member outcomes that must be changed in one empirical law to transform it into the other).

M2 reads only M1 outputs; measured gas and source truth are forbidden.

### M3 — APRS: Adaptive Proper-Score Resolution

With actual observed route hit count `H`, candidate law `P_s` is evaluated by the discrete Ranked Probability Score:

\[
RPS(P_s,H)=\sum_{k=0}^{N-1}\left(F_s(k)-\mathbf 1[H\le k]\right)^2.
\]

The load-bearing correspondence theorem is

\[
\mathbb E_{H\sim P}\left[RPS(Q,H)-RPS(P,H)\right]
=
\sum_{k=0}^{N-1}\left(F_Q(k)-F_P(k)\right)^2.
\]

Hence if two sources have the same F00 mean projection but different laws, F00 ties their physical likelihood while full-law RPS strictly distinguishes the true law in expectation.

No fixed robustness parameter is selected. For every deletion level `q=0,...,M-1`, dynamic programming computes the exact minimum and maximum RPS obtainable after deleting any `q` transport members. Source `a` robustly out-scores `b` at level `q` only if

\[
\max RPS_a(q)<\min RPS_b(q).
\]

The method outputs the entire two-axis survivor surface

\[
\mathcal S_t(r_T,r_O),\qquad r_T,r_O=1,\ldots,M,
\]

where `r_T` is physical-law separation strength and `r_O` is observation-score robustness. No scalar `alpha`, deletion depth, margin, temperature, or bandwidth is chosen.

A robustness-persistence map may be used as a descriptive source support score, but it is **not** called a calibrated Bayesian posterior.

## Phase 2.3 — coherence / correspondence checks

1. **Exact F00 limit:** same `T_s` means exactly same F00 physical likelihood; no approximation is used.
2. **Strict surpassing example:** `[0,0,0,0,4,4,4,4]` and `[2,2,2,2,2,2,2,2]` have the same mean/`T_s` but different CDFs. F00 ties them; expected RPS under the first law strictly favors the first law.
3. **M2→M3 same object:** M2's squared empirical CDF separation is exactly the expected RPS regret geometry used by M3.
4. **No shared-member counterfactual assumption:** member labels are exchangeable within each source; no source-A/member-3 to source-B/member-3 pairing is used.
5. **No rescued old modules:** persistent sensor memory and precise stop identity remain NO-GO and are not reintroduced.
6. **Causal boundary:** the oracle estimates `P(K | do(S=s), do(X=x_observed), context)`; it does not claim a counterfactual in which the robot replans under each source.

## Phase 3.2 — audit and verdict

### Gap-closure reject check

**Risk:** a sophisticated framework could still be a bundle of existing parts.  
**Mitigation:** the contribution is pinned to one exact limit/remedy theorem: F00 factors through the mean projection; full-law CDF geometry is invisible to that projection; RPS regret is exactly the CDF distance. The three modules are stages of this one construction, not independent add-ons.

### Recipe-application check

- `assumption_audit_and_pivot`: applied — a specific inherited assumption (mandatory total source ordering from scalar evidence) is explicitly isolated.
- `characterize_limit_then_surpass`: applied — there is an exact equivalence class and a strict-separation construction.
- `reframe_as_solvable_object`: applied conditionally — set-valued output is justified only if the oracle data contain real mean-alias/distinct-law pairs and the full-law method improves downstream evidence without losing truth coverage.

### Anti-pattern check

No ResearchStudio reject-favored pair involving `heterogeneous_decomposition` is present.

### Paper-pointed threats

1. **Kim et al. 2026 deep probabilistic indoor GSL:** subsumes broad claims about probabilistic physical-dependency GSL. CTPI-FL must claim the change in *identification object/granularity*, not “physics-guided probabilistic GSL.”
2. **Assimilative Causal Inference 2026:** subsumes broad claims about inverse causal inference. It is theory support, not novelty.
3. **UAI 2026 state-level identifiability / POSCM and AISTATS 2026 partial identification:** subsume broad claims that state-level or set-valued causal identification is new. The novelty must be the GSL-specific route-encounter law, exact F00 mean-projection limit, and its source-resolution construction.
4. **Calibration-Free GSL 2026:** prevents any untested claim of calibration-free robustness.
5. **Classical inverse-source identifiability:** older parabolic/PDE source-localization theory already allows set-valued source solutions and asks what observations make a source identifiable. CTPI-FL therefore does **not** claim that set-valued source localization or identifiability itself is new; the contribution must remain tied to the robotic-GSL route-encounter law and the exact PMFS/F00 mean-projection limit.
6. **PDSL 2026 (Propagation Dynamics Aware Framework for Source Localization):** explicitly models stochastic propagation dynamics in a different network-diffusion source-localization domain. It blocks any broad claim that “using the full stochastic propagation distribution for source localization” is new in general. CTPI-FL's claim must be GSL-specific and mechanism-specific: route-conditioned gas-encounter laws, the exact F00 compression theorem, and partial-identification output under sparse robotic observations.

### Falsification structure check

Minimal existing-data experiment:

1. On the frozen 4936-world route bank, count pairs with equal F00 mean numerator `T_i=T_j` but nonzero full-law CDF separation `G_ij>0`.
2. Verify exact F00 parity against the frozen F00 artifact.
3. Evaluate CTPI-FL on all H01/H02/H03 × 10 tapes × 5 updates.
4. Compare the full-law survivor surface/support against area-matched F00 on `J`, source-label tail mass, true-source rank, and report localization error/AUC as secondary outcomes.
5. Reassign complete `P(K|S)` laws to wrong source identities. The downstream `J` must deteriorate as the amount of physical-law association destroyed increases.

Load-bearing variable: **full-law CDF separation `G_ij` / complete `P(K|do(S=s),C)` rather than its mean projection**.

No invented effect-size threshold is used. Direction and Pareto dominance against the frozen comparator decide the development Gate.

### Verdict

**REVISE → ADVANCE TO ORACLE FALSIFICATION.**

The previous FOSD + absolute-count-residual CTPI-A should be retired as the main formulation because it did not establish strict expressivity beyond F00's mean statistic. The V0.3 full-law formulation repairs that structural issue and has a concrete existing-data falsification test. It is not yet a paper-level GO until the frozen oracle Gate is run.

### Post-audit refinement — theorem relevance is separately falsified

The ResearchStudio "characterize a limit, then surpass it" pattern requires more than an abstract counterexample. V0.3 therefore distinguishes (a) **capacity evidence**: each House contains at least one `T_i=T_j, G_ij>0` pair, from (b) **load-bearing task evidence**: the truth source itself enters such an F00-physical-likelihood equivalence class in at least one evaluated context. For every House where that happens, CTPI's unweighted robustness-surface persistence must not favor the alias competitors on average; pooled over all such contexts, the truth-minus-alias persistence margin must be positive. If the development data never put truth in a hard alias class, the theorem remains valid but its direct localization relevance is `NOT_IDENTIFIED` and the Oracle Gate cannot claim the strict-expressivity mechanism is empirically load-bearing.
