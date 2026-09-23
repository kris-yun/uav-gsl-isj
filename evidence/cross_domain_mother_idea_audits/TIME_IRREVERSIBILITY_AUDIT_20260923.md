# Mother-idea audit — nonequilibrium time irreversibility / arrow-of-time evidence

Date: 2026-09-23
Branch: `research/cross-domain-mother-idea-audits-20260923`

Status: **PHYSICAL PHENOMENON POSITIVE / NAIVE PMFS TRANSFER NO-GO / CANDIDATE-LOCAL OBSERVABLE TEST REQUIRED**

No gas-source-localization method is named or promoted here.

## 1. Mother theory

The external scientific idea is time-reversal symmetry breaking / entropy production in nonequilibrium stochastic dynamics.

Recent 2025–2026 anchors found with scite include:
- *Macroscopic arrow of time from multiscale perspectives* (EPL, 2025).
- *Time Irreversibility and Entropy Production in Non-Hermitian Model A Field Theories* (2026).
- *Time Irreversibility, Entropy Production, and Effective Temperature Are Independently Regulated in the Actin Cortex of Living Cells* (Physical Review X, 2026).
- *Self-Propulsion Symmetries Determine Entropy Production of Active Particles with Hidden States* (Physical Review Letters, 2026).

The transferable hypothesis is not that plume amplitude is invariant. It is that source-conditioned nonequilibrium transport may leave a source-specific **time-arrow / irreversible transition structure** that can survive a transport intervention better than static plume appearance.

## 2. Necessary phenomenon test on controlled CStar

Controlled asset:
- H01/H02/H03;
- source SA/SB;
- transport fast/slow;
- same robot route within each House;
- 1200 samples/episode.

A simple source-blind time-irreversibility representation was built from gas trajectories:
- log(1+gas);
- four within-episode amplitude states using quartiles;
- lags {1,2,5,10,25};
- for every state pair i<j, record normalized antisymmetric transition current
  J_ij(lag) = P(i->j)-P(j->i).

Cross-transport source-identity test:
- fast target classified only from slow SA/SB templates;
- slow target classified only from fast SA/SB templates.

Result:
- real chronological trajectories: **9/12** correct;
- reverse target only: **4/12**;
- reverse template only: **4/12**;
- reverse both: **9/12**.

A 200-repetition within-episode temporal shuffle null previously gave:
- null mean about 5.88/12;
- only **2.5%** of shuffled trials reached the real 9/12 result.

Interpretation:
- unlike HCCE, a genuine time-order-dependent source signal exists in the measured gas trajectories;
- the one-sided reversal control is load-bearing;
- simultaneous reversal preserves pairwise distance by symmetry and is therefore an expected invariance, not evidence against the signal.

This passes the **physical phenomenon** gate.

## 3. First PMFS transfer attempt — rejected

The new verified standalone replay for H01_R2026092201 provides 121 terminal candidates, each with 200 x 0.2 s candidate-internal dynamics.

A deliberately simple first transfer compared:
- measured sensor-gas time-irreversibility feature;
- candidate **global hit-cell-count** time-irreversibility feature from the replay.

This was done only as a kill test.

H01_R2026092201:
- terminal candidates: 121;
- truth-nearest source candidate distance: 0.2335 m;
- truth-nearest candidate rank by irreversibility match: **113/121**;
- truth-nearest percentile: **6.7%**;
- Spearman(score, -source distance): **-0.224**.

Decision:
**NAIVE GLOBAL-CANDIDATE-OBSERVABLE TRANSFER = NO-GO.**

This does not invalidate the mother theory. It shows that comparing a robot-local measured gas observable with a global candidate plume-occupancy count is the wrong observable mapping.

## 4. Why this failure is informative rather than a rescue excuse

The theory requires comparing like with like.

Observed signal:
- gas concentration / hit process at the robot measurement location over time.

Naive candidate signal:
- total number of occupied cells across the whole candidate plume over time.

These are different observables of the dynamical system.

The inventory already established that a causal, source-conditioned **candidate time series at the frozen current robot position** is regeneratable from the PMFS internal rollout, while future robot trajectory alignment is forbidden.

Therefore the next and only justified test is:

> At each actual StopAndMeasure/source-update location, compare the measured within-block temporal sequence with the candidate-predicted local temporal sequence at that same fixed robot position.

No future pose is used. No full GADEN oracle field is used. No source truth enters the score.

## 5. Required next kill test

Before any localization posterior:

1. prospectively or offline-replay candidate occupancy/hit at the **frozen current robot position** for all 200 internal steps;
2. recover the measured within-block sensor sequence at that same stop location;
3. construct the same source-blind time-arrow statistic on both;
4. rank candidates;
5. check direct truth-candidate rank and source-distance correlation;
6. repeat on old six and independent-plume six;
7. then test source x transport CStar identity if a candidate-local replay equivalent can be built.

Hard failure:
- if truth-nearest candidate does not consistently improve beyond simple hit-rate / static PMFS baselines, reject the mother idea for localization.

## 6. Current decision

The route is **not** promoted.

What survived:
- source identity in measured trajectories is genuinely time-order dependent under transport intervention.

What failed:
- global candidate dynamics do not map that signal back to source.

What remains scientifically justified:
- one candidate-local same-observable test at the measurement point.

No method name, no V1, no posterior integration, and no new holdout should be created before that test.
