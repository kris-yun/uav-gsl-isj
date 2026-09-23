# Candidate M2 — Wind-Regime Invariant PMFS

Date: 2026-09-23  
Branch: \`research/wind-regime-invariance-v1\`  
Status: **KEEP FOR IMMEDIATE MECHANISM FALSIFICATION; NOT YET MAIN**

## 1. Scientific thesis

Do not treat wind non-stationarity only as noise to forget.

Treat distinct wind conditions as **multiple environments / natural soft interventions on gas transport**, while the physical source location remains invariant.

The proposed PMFS-level principle is:

> retain environment-specific gas evidence, explain each environment with its matching transport model, and identify the source candidate whose support is consistent across the different wind environments.

This is deliberately different from:
- a sliding window;
- recency weighting;
- a single current-wind forward model;
- averaging multiple plume models into one;
- generic causal scoring.

Working name:

**Wind-Regime Invariant PMFS (WRi-PMFS)**

---

## 2. Native PMFS temporal semantics — why this question exists

Official PMFS contains two pieces that are individually reasonable but can become semantically mismatched under large wind-regime changes.

### 2.1 The measured hit map accumulates all historical measurements

The PMFS paper explicitly states that the gas hit-probability map is recursively updated from **all accumulated measurements** using a binary Bayes filter:

\[
l(H_i|z^{1:t})
=
l(H_i|z^{1:t-1})
+
l(H_i|z^t)
-
l(H_i).
\]

Official \`PMFSLib::EstimateHitProbabilities()\` implements this with

\`\`\`cpp
cell.logOdds += cell.auxWeight - logOddsPrior;
\`\`\`

and does not reset the map when the wind field changes.

Each individual measurement uses its local measured wind direction/speed to shape the propagated kernel, so the accumulated map may contain evidence gathered under different transport conditions.

### 2.2 Candidate forward maps are regenerated using the current wind grid

At every measurement cycle, official PMFS calls \`EstimateWind(...)\`.

When a source update is due, \`simulations.updateSourceProbability(...)\` generates each candidate-source plume through the \`Simulations\` object, which references the current \`estimatedWindVectors\`.

Thus at source-update time, candidate \(s\) produces a hit map under the current transport state, while the measured hit map can encode historical observations gathered under multiple earlier transport states.

### 2.3 Structural hypothesis

Under quasi-stationary wind, this can be harmless or beneficial because accumulating measurements suppresses turbulent fluctuations.

Under a genuine regime change, however, the comparison can become:

\[
\text{historical multi-regime evidence}
\quad\text{vs}\quad
\text{single current-regime candidate plume}.
\]

This is a PMFS-specific falsifiable hypothesis, not yet a demonstrated failure.

---

## 3. Remote-field parent idea — invariance across environments

Yao, Rancati, Cadei, Fumero & Locatello,

**Unifying Causal Representation Learning with the Invariance Principle**, ICLR 2025.

Key transferable lesson:

- identifiability in multi-environment data can be driven by known **invariances / symmetries** across data pockets;
- the relevant structure need not rely on claiming a full causal hierarchy;
- different environments can change variant mechanisms while preserving the latent object one wants to identify.

For WRi-PMFS:

- invariant latent object = source location \(S\);
- environment = wind/transport regime \(E\);
- variant mechanism = plume geometry / hit-probability field;
- observable evidence = regime-specific gas measurements / hit maps.

This is the scientific parent, not a direct algorithm transfer and not a claim that PMFS becomes a causal-representation-learning model.

Reference:
- ICLR 2025 proceedings: *Unifying Causal Representation Learning with the Invariance Principle*
- arXiv: 2409.02772

---

## 4. Important prior-art boundaries

### 4.1 Time-dependent gas mapping already exists

Asadi, Fan, Hernandez Bennetts & Lilienthal,

*Time-dependent gas distribution modelling*, Robotics and Autonomous Systems 96 (2017), 157–170.

DOI: 10.1016/j.robot.2017.05.012

They:
- explicitly address changing gas distributions;
- use temporal sub-sampling and recency weighting;
- show that recent measurements can better estimate the current gas distribution.

Therefore we cannot claim:
- first time-aware gas map;
- first forgetting/sliding-window gas mapping;
- first method for changing environmental conditions.

**Difference sought here:** old regimes are not merely discarded or down-weighted. They are retained as separate environments because they can contribute complementary source-identification evidence.

### 4.2 Time-varying-wind GSL itself is not new

Many GSL / mapping methods have been evaluated under varying wind. Existing work also models temporally varying advection and may forget old measurements.

Therefore:
- “works under dynamic wind” is not a novelty claim.

### 4.3 Non-stationary gas inverse problems already exploit wind variation

Vänskä, Weidmann & Ursin,

*Greenhouse gas emission mapping and quantification based on 3D transport modeling and Bayesian state estimation*, Inverse Problems 41 (2025) 095001.

DOI: 10.1088/1361-6420/adfb29

They explicitly formulate non-stationary 3-D gas-source reconstruction with temporally evolving concentration and wind data, and demonstrate source reconstruction under multiple wind conditions.

Therefore we cannot claim:
- first inverse gas-source method to exploit non-stationary wind;
- first multi-wind source reconstruction.

Remaining target distinction:
- mobile robotic GSL;
- PMFS candidate-source probability map;
- online filament simulations;
- retaining multiple transport environments as separate PMFS evidence channels;
- invariant-source aggregation across those channels.

---

## 5. Core representation

Instead of one measured map

\[
M_t
\]

maintain an environment-indexed collection

\[
\{M^{(e)}_t\}_{e=1}^{E_t}.
\]

Each actual gas/wind observation is assigned to one environment \(e_t\).

For first falsification, environments are **given**, not learned:
- use known wind-regime labels in toy data;
- later use predeclared clustering/change detection source-blind.

For every active environment \(e\), preserve:
- regime-specific hit-probability map \(M^{(e)}\);
- confidence map \(\alpha^{(e)}\);
- representative / regime-specific wind field \(W^{(e)}\);
- measurement count / timestamps.

No source truth is used in environment construction.

---

## 6. Regime-matched candidate simulation

For candidate source \(s\), generate

\[
H^{(s,e)}
=
\operatorname{PMFSForward}(s,W^{(e)}).
\]

Then compute the **native PMFS map-comparison score within each environment**:

\[
L_e(s)
=
S_{\rm PMFS}
\left(
M^{(e)},
H^{(s,e)}
\right).
\]

The first implementation should reuse the official PMFS score rather than invent another likelihood.

---

## 7. Invariant-source aggregation

The same source candidate \(s\) must explain all environments.

A parameter-free first aggregation is the product of environment evidence:

\[
\boxed{
P(s|D_{1:E})
\propto
P_0(s)
\prod_{e=1}^{E}
L_e(s).
}
\]

For numerical implementation use log scores.

The scientific meaning is a **product of environment-specific constraints**:
- a wrong candidate can be plausible in one wind regime because its plume alias overlaps the observations;
- under a different wind intervention, that alias should move differently;
- only source candidates whose position remains compatible across environments receive persistent support.

### Warning

Before implementation, verify that the native \(L_e\) scale is comparable across regimes with different amounts of evidence.

Do not add arbitrary environment weights.

Possible source-blind normalization, only if required:
- use native confidence / number of effective measurements;
- use per-environment average log compatibility instead of raw product;
- predeclare the rule before truth reveal.

---

## 8. Why this is not a model ensemble

The source index is shared; the transport environment changes.

This is not:

\[
\sum_m p(m)\,p(s|D,m)
\]

over competing plume models.

It is:

\[
\prod_e p(D_e|s,e)
\]

where each environment is an observed/estimated physical condition and the same source must survive all of them.

The environments are complementary evidence, not alternative explanations to be averaged away.

---

## 9. Why this can be stronger than recency weighting

A recency method asks:

> Which old measurements should I forget to estimate the current plume?

WRi-PMFS asks:

> Which source location is compatible with the sequence of different plumes induced by different winds?

Under a regime shift, old data can be bad for estimating **the current plume** but excellent for identifying **the invariant source**.

That is the key scientific distinction.

---

## 10. Hard first falsification — WRi-TOY-B0

Before any House implementation, create a controlled PMFS-like toy with:

- the same fixed source for the full trial;
- at least two distinct wind regimes;
- identical measurement locations and observations for all scoring methods;
- regime labels supplied as oracle metadata only for this mechanism test.

Compare source rank using:

### A. Current-environment collapse

All observations are collapsed into one historical summary, then compared with / scored under the final-current wind environment.

This represents the structural mismatch hypothesis.

### B. Recency/window baseline

Use only recent/current-regime observations.

This tests whether simply forgetting old data is enough.

### C. Regime-invariant factorization

Score each environment against its matching candidate plume and combine evidence for the same source.

### D. Oracle stationary control

No regime change.

Primary endpoint:
- truth-source candidate rank.

Expected signature if the mechanism is real:

1. stationary: A and C should be equivalent / near-equivalent;
2. strong regime change: A should degrade;
3. recency should recover some consistency but discard information;
4. C should outperform recency because it uses complementary old-regime evidence;
5. permuting regime labels should destroy C's advantage.

If C only wins because it sees more observations than B, add an equal-count control.

---

## 11. House-data gate after Native baseline repair

If toy mechanism passes:

1. identify source-blind wind regimes from the recovered Native traces;
2. first use a predeclared simple regime representation:
   - direction sector + speed bin, or
   - source-blind changepoint segmentation;
3. reconstruct regime-specific PMFS measured maps;
4. generate regime-matched candidate hit maps;
5. aggregate candidate evidence;
6. compare truth-source rank against:
   - Native PMFS;
   - recency/windowed PMFS;
   - regime-label permutation;
   - equal-data-count control.

No closed-loop path changes in the first test.

Inference-only first, so a positive result cannot be attributed to a changed trajectory.

---

## 12. Kill criteria

Kill as main innovation if any of the following holds:

- official/recovered PMFS data are effectively stationary, so there are no meaningful environments;
- regime-conditioned evidence gives no truth-rank gain over a simple recency window;
- the gain disappears under equal-data-count control;
- shuffled regime labels perform equally well;
- useful results require source-truth-dependent regime boundaries;
- the method reduces to a generic sliding window;
- direct prior art is found that already performs environment-indexed PMFS-style source-map intersection under multiple wind regimes.

---

## 13. Current assessment

**Narrative strength:** potentially high.  
**Remote parent strength:** high (ICLR 2025 invariance principle).  
**PMFS interface fit:** very high.  
**Baseline-repair dependence:** low-to-moderate; the temporal semantics are present in official PMFS, but real benefit depends on wind non-stationarity.  
**Main risk:** novelty may collapse to "condition on wind correctly" unless cross-environment invariant-source aggregation produces a distinct, measurable source-identification advantage over recency/window baselines.

Next action:
- run WRi-TOY-B0 immediately.
