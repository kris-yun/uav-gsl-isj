# HCCE V1 development screen — causal emergence after HCMC failure

Date: 2026-09-22  
Branch: `research/hcce-v1-development-screen-20260922`  
Base raw-data commit: `c5271515d565c343d2fd2a63c77bf0484f45772a`

Status: **DEVELOPMENT-POSITIVE ON ENDPOINTS, BUT MAIN-LINE HOLD AFTER ANTI-METRIC AUDIT / NOT AN INDEPENDENT VALIDATION**

## 0. Why this cycle is different

HCMC V1 was a discovery-set false positive: it was very strong on the old six cases but failed on true independent stochastic plume realizations, including a valid case in which the frozen HCMC representation became undefined.

Therefore HCCE was screened jointly on:

- the old six R2 cases; and
- the six now-unblinded true independent plume cases from HCMC validation.

The second set is no longer a holdout. It is development data.

A new, never-inspected stochastic/source-position holdout is required before HCCE can be promoted.

## 1. Remote-domain mother idea: causal emergence

The mother idea comes from complex-systems science, not gas-source-localization methodology.

Relevant 2025–2026 anchors found with scite:

- Zhang, Tao, Yang et al., **Dynamical reversibility and a new theory of causal emergence based on SVD**, *npj Complexity* (2025), DOI `10.1038/s44260-025-00028-0`.
- **Causal Emergence 2.0: Quantifying emergent complexity** (2025), arXiv:2503.13395.
- Yang, Wang, Zhang, **Partial Effective Information Decomposition for Synergistic Causality** (2026), arXiv:2605.03267.

Public implementation used as a conceptual/code reference:
https://github.com/jessescool/Causal-Emergence-2.0

The central idea is that a coarse-grained macrostate can have **greater causal power / determinism / specificity** than the microscopic state description.

### Transfer to gas-source inference

For source hypothesis (s), sample its PMFS simulated hit-probability field along the actual robot trajectory:

[
q_s(t).
]

Convert the measured sensor trace into a binary encounter state

[
y(t)=mathbf 1[c(t)>10^{-6} {m ppm}],
]

where (10^{-6}) is the recorded sensor-resolution floor, not a truth-tuned localization threshold.

The joint microstate is

[
X_s(t) = (operatorname{bin}_4 q_s(t),,y(t)),
]

with fixed candidate-probability bins ([0,.25,.5,.75,1]).

From the lag-one transition matrix of the eight joint microstates, compute causal power

[
CP = rac{	ext{determinism}+	ext{specificity}}{2},
]

and greedily merge microstates as in CE 2.0. The candidate's macro causal power is the maximum nontrivial causal power reached under coarse-graining.

The hypothesis is:

> the correct source induces a source-conditioned sensor/transport dynamics whose causal structure becomes more deterministic and specific after the appropriate macro coarse-graining.

This is qualitatively different from HCMC: no structure-function slope, no spatial multifractal law, and no requirement that the measured spatial field have non-zero increments.

## 2. Second-level innovation inside HCCE: geometry-conditioned causal excess

A serious confound is that candidate position and robot path alone can create apparent causal structure.

For every source hypothesis, define a geometry-only trajectory channel

[
g_s(t)=1-operatorname{normalized distance}(x_t,s).
]

Let (CE(q,y)) denote macro causal power, and subtract the constant-event causal baseline:

[
C(q,y)=CE(q,y)-CE(q,0).
]

HCCE V1 uses

[
oxed{
S_s =
C(q_s,y)-C(g_s,y)
}
]

so that source evidence is the **causal emergence carried by the simulated plume beyond the causal structure already explainable by robot/source geometry**.

Candidates are converted to average-percentile ranks and projected back to their final leaves.

This geometry-conditioned excess is load-bearing: geometry-only causal scoring is materially weaker.

## 3. Data contract

### Old development set

House01/02/03 × seed0/1, old R2 archive.

For the main final-bank development comparison, the final old source update is used. A separate update-time stress test is reported below.

### New development set

Six true independent stochastic plume realizations from the HCMC validation.

Critical inventory correction:

- every accepted new run contains exactly **one** `source_update_0001`;
- there are no `source_update_0002..0005` banks;
- HCCE does not reconstruct missing updates.

HCCE uses:
- that one source-conditioned candidate bank;
- the full sensor/pose trajectory up to that source update;
- no truth in score construction.

## 4. HCCE V1 development result

Frozen development member in this report:

- sensor event: measured gas (>10^{-6}) ppm;
- candidate bins: (0,.25,.5,.75,1);
- lag: 1 sensor sample = 0.2 s;
- causal statistic: maximum macro causal power;
- score: plume causal coupling minus geometry causal coupling.

### Endpoint matrix

| case | Native m | HCCE m |
|---|---:|---:|
| House01 seed0 | 5.5273 | 4.9161 |
| House01 seed1 | 4.0016 | 1.5133 |
| House02 seed0 | 4.1070 | 3.5621 |
| House02 seed1 | 3.7007 | 1.1995 |
| House03 seed0 | 7.7821 | 3.1115 |
| House03 seed1 | 8.2116 | 3.7358 |
| H01 R2026092201 | 4.6014 | 2.7441 |
| H01 R2026092202 | 4.2738 | 2.4880 |
| H02 R2026092211 | 6.9341 | 0.7579 |
| H02 R2026092212 | 4.3579 | 2.8796 |
| H03 R2026092221 | 7.9527 | 1.9897 |
| H03 R2026092222 | 7.9608 | 2.4951 |

Aggregate:

- all-12 HCCE mean = **2.6161 m**
- pooled reduction vs Native = **54.77%**
- non-worse = **12/12**

Split:

- old six: **45.88%**, 6/6
- new stochastic-plume six: **62.99%**, 6/6

The H01 realization that made HCMC spatial multiscaling undefined remains fully definable here because HCCE uses the sensor trajectory and source-conditioned dynamic coupling rather than requiring non-zero spatial slopes.

## 5. Destructive controls for the exact frozen development member

### Final-leaf score permutation, 1000 repetitions

- null mean: **4.4381 m**
- 1–99%: **3.4660–5.3941 m**
- null repetitions as good as real HCCE: **0/1000**

### Circular temporal misalignment, 30 repetitions

Shift both plume and geometry candidate channels relative to the sensor sequence while preserving their internal dynamics.

- null mean: **4.3538 m**
- fraction as good as real HCCE: **0/30**

### Sensor block-order destruction, 30 repetitions

Shuffle 5 s sensor-event blocks, preserving within-block intermittency.

- null mean: **4.2203 m**
- fraction as good as real HCCE: **0/30**

### Candidate-identity mismatch, 30 repetitions

Randomly reassign the physical candidate plume sequence to another candidate identity while retaining each candidate's own geometry channel.

- null mean: **4.3073 m**
- fraction as good as real HCCE: **0/30**

These controls indicate that spatial candidate identity and correctly aligned sensor/plume dynamics are both load-bearing.

## 6. Geometry confound audit

Pure geometry-only macro causal scoring:

- old improvement: **18.57%**, 4/6
- new improvement: **23.25%**, 5/6
- all: **21.00%**, 9/12

HCCE geometry-conditioned causal excess:

- all: **54.77%**, 12/12

Thus path/source geometry contains real benchmark information, but it does not explain the full HCCE result.

Raw HCCE score correlations with distance-to-origin/start/path-mean vary substantially in sign and magnitude across cases rather than showing a single fixed geometric preference.

## 7. Cross-realization score reproducibility

For common candidate IDs between the two new stochastic realizations in each house:

- H01: Spearman **0.878** over 113 common candidates
- H02: **0.842** over 95
- H03: **0.902** over 157

This is substantially stronger than the realization-specific behavior that motivated the HCMC failure audit.

## 8. Coarse-graining family robustness

The original (y>0) discovery screen was deliberately expanded across candidate-state bin families and temporal lags.

Examples:

- equal-four bins, lag 1: 54.61%, 12/12
- equal-four bins, lag 2: 46.87%, 12/12
- equal-four bins, lag 5: 40.99%, 12/12
- low-tail bins, lag 5: 47.77%, 12/12
- mid-tail bins, lag 1: 50.34%, 12/12
- mid-tail bins, lag 2: 51.39%, 12/12
- mid-tail bins, lag 5: 59.91%, 12/12
- mid-tail bins, lag 10: 45.39%, 12/12

No best member is selected from these numbers for validation.

## 9. Sensor-event threshold stress

Holding candidate bins and lag fixed, HCCE remains positive across a broad sensor-event threshold family:

| threshold ppm | all gain | non-worse |
|---:|---:|---:|
| 0 | 54.61% | 12/12 |
| 1e-6 | 54.77% | 12/12 |
| 1e-4 | 47.20% | 12/12 |
| 1e-3 | 35.58% | 10/12 |
| 1e-2 | 36.95% | 10/12 |
| 5e-2 | 36.77% | 10/12 |
| 1e-1 | 21.81% | 7/12 |
| 2e-1 | 21.41% | 8/12 |

The result is strongest when the observable is interpreted as **encounter/no-encounter**, not the PMFS 0.1 ppm update threshold.

The current frozen development definition uses (10^{-6}) ppm to exclude the recorded numerical floor.

## 10. Old-source-update maturity stress

Using the same HCCE concept on the five old source-update banks:

- ~67 s: +8.75%, 2/6
- ~120 s: +19.86%, 3/6
- ~175 s: +48.95%, 5/6
- ~226 s: +24.38%, 4/6
- ~278 s: +47.28%, 6/6

Therefore HCCE, like other source-conditioned evidence, is not assumed useful before enough source-conditioned trajectory/support has accumulated.

No release time is selected from this development set.

## 11. Degeneracy contract

Future HCCE must check sensor-event entropy before forming a posterior.

If the sensor event sequence is constant or below a frozen minimum-information requirement, the method must **ABSTAIN**, not create an arbitrary source ranking.

This is a direct methodological lesson from HCMC's undefined-posterior failure.

The development cases used here all have non-degenerate encounter histories at the selected source update.

## 12. Simple-baseline audit

Several simpler statistics were also tested.

Examples over all 12:

- static mutual information: +38.4%, 8/12
- correlation: +40.3%, 6/12
- transition mutual information: +15.9%, 8/12
- raw macro causal power without geometry-conditioned excess: +36.1%, 9/12

The full HCCE geometry-conditioned causal-excess score is stronger at **54.77%, 12/12**, so the current evidence is not explained merely by replacing PMFS with a static correlation statistic.

## 13. Novelty collision screen

A targeted scite query for

`"causal emergence" AND ("gas source localization" OR "odor source localization" OR olfaction OR plume)`

returned no direct GSL/OSL use of causal emergence as source-hypothesis evidence. Returned hits were unrelated uses of "plume" or general causal-emergence work.

This is a targeted collision screen, not an exhaustive novelty proof.

## 14. What is and is not established

Established at development level:

- unlike HCMC, the candidate is jointly positive on old and new stochastic realizations;
- it is defined on the H01 independent plume that broke HCMC;
- candidate identity and temporal alignment are load-bearing;
- geometry alone does not explain the full gain;
- new-realization candidate scores reproduce strongly within house;
- the effect survives a family of coarse-graining choices.

Not established:

- fresh-holdout generalization;
- source-position transfer;
- arbitrary wind/geometry invariance;
- linked-native endpoint parity for an HCCE posterior;
- closed-loop improvement.

## 15. Next hard gate

Do **not** use the present 12 cases as validation again.

Freeze HCCE V1, then generate a new holdout that changes both:

1. stochastic plume realization; and
2. source position within each House.

The HCCE posterior must be generated source-blind before truth release and evaluated with the same linked-native C++ top-5% endpoint used in the HCMC audit.

A minimum promotion gate should include:

- HCCE defined or explicit source-blind ABSTAIN in every case;
- pooled reduction >=10%;
- >=4/6 non-worse;
- no new false-confident collapse;
- real result better than leaf, temporal-misalignment, and candidate-identity null means;
- geometry-only baseline materially weaker than HCCE;
- no parameter changes after holdout generation.

Only after this gate should a closed-loop planner or two auxiliary innovations be promoted.


## 16. Anti-metric-gaming audit — critical downgrade

After the strong top-5% endpoint result was obtained, HCCE was audited using metrics that do not depend on the same top-5% centroid.

Across all 12 cases:

- Native full-posterior expected distance: **5.7644 m**
- HCCE full-posterior expected distance: **5.1834 m**
- Native mass within 1 m: **0.0067**
- HCCE mass within 1 m: **0.0348**
- Native mass within 2 m: **0.0188**
- HCCE mass within 2 m: **0.1255**
- Native MAP-cell error: **5.5677 m**
- HCCE MAP-cell error: **4.7377 m**

These are positive but much weaker than the 54.77% top-5% endpoint improvement.

More importantly, direct candidate-level source identification is not yet strong enough for promotion:

- mean percentile of the candidate nearest the true source: **0.764**
- mean Spearman correlation between HCCE score and negative source-distance: **0.194**
- mean distance from truth of the single highest-scoring candidate: **4.570 m**

The two new House01 realizations are the clearest warning:
- the candidate nearest truth is only at about the **51st percentile** in both;
- nevertheless the top-5% centroid endpoint improves.

Therefore the present endpoint gain can partly arise from a broad spatial ranking/centroid effect rather than the true source hypothesis being directly selected.

### Consequence

HCCE is **not promoted to the paper's main innovation yet**.

It survives as a scientifically interesting causal-emergence candidate because:
- old/new stochastic realization transfer is strong;
- destructive controls are strong;
- geometry subtraction is load-bearing;
- alternative posterior diagnostics improve.

But before main-line promotion, HCCE must pass a source-position intervention test in which the true source is moved substantially and the candidate-level truth rank is a primary criterion, not merely the top-5% ExpectedValue endpoint.

The existing 240 s SA/SB controlled asset cannot honestly provide this test because its published candidate-domain files contain only map coordinates, not the source-conditioned candidate plume fields required by HCCE.

Final development verdict for this cycle:

`HCCE_V1_MAINLINE_HOLD_SOURCE_IDENTITY_NOT_YET_PROVEN`
