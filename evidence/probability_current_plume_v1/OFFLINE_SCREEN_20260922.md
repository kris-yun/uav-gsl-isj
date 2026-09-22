# Hypothesis-Conditioned Probability Current V1 — offline screen

Date: 2026-09-22
Status: **NO-GO AS MAIN INNOVATION**

## Remote-field mother idea

Recent non-equilibrium statistical physics has developed model-free estimation of probability currents directly from stochastic trajectories. A representative recent anchor is:

- Physical Review Letters 135, 238301 (2025), *Model-Free Learning of Probability Flows: Elucidating the Nonequilibrium Dynamics of Flocking*.

The transfer hypothesis was that a gas-source hypothesis should be judged by the state-dependent probability current of the observed gas-motion trajectory in candidate-relative coordinates, rather than by static concentration compatibility.

## Candidate-conditioned proxy

For each source hypothesis s:
- radial coordinate r_s(t) = distance from robot to source candidate;
- gas channel = empirical concentration rank;
- fixed radial state bins;
- dynamic current features include local oriented gas-weighted radial current, signed gas-radius area, and gas increment current.

Cross-wind source identity was tested on the frozen 240-s VGR controlled asset:
H01/H02/H03 × SA/SB × fast/slow.

## Positive checks

At 240 s:
- 6 bins: 12/12;
- 8 bins: 12/12;
- 10 bins: 12/12;
- 12 bins: 12/12;
- even temporal subsequence: 12/12;
- odd temporal subsequence: 12/12.

Gas-order shuffle, preserving the concentration distribution but destroying temporal order:
- 50 source-blind shuffles;
- mean accuracy 49.17%;
- max 91.67%;
- 0 perfect 12/12 runs.

Therefore the current statistic contains genuine temporal-order information.

## Decisive negative control

A static candidate-relative control using only radial occupancy and mean gas rank was evaluated at the same horizons.

Accuracy (current vs static):
- 80 s: 7/12 vs 7/12
- 100 s: 10/12 vs 10/12
- 120 s: 9/12 vs 10/12
- 140 s: 9/12 vs 9/12
- 160 s: 8/12 vs **12/12**
- 176 s: 12/12 vs 12/12
- 180 s: 12/12 vs 12/12
- 200 s: 10/12 vs **12/12**
- 220 s: 9/12 vs **12/12**
- 240 s: 12/12 vs 12/12

At 240 s the current has higher mean separation margin (0.157 vs 0.062), but it is less stable across time.

## Decision

The probability-current representation is real and nontrivial, but it is **not load-bearing for source identity** on this asset. Static candidate-relative spatial structure is earlier and more stable.

Do not promote probability current / nonequilibrium flow as the new paper-level main innovation.

It may remain an auxiliary confidence-margin feature, but no closed-loop work is justified from this screen.
