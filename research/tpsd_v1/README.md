# TPSD V1 candidate — Temporal Primacy Source Decorrelation

Status: **candidate only / offline screen pending**.

This branch does not modify PMFS, TNQC, DRPE, R2, or the online planner.

## Scientific source

Primary source:

Karadas et al., *Rapid temporal processing in the olfactory bulb underlies
concentration-invariant odor identification and signal decorrelation*,
Nature Neuroscience, 2026.

The 2026 mechanism is more specific than generic primacy coding or generic
lateral inhibition:

1. the earliest activated channels provide a relatively
   concentration-invariant identity signal;
2. there is a brief early excitability window;
3. delayed/prolonged inhibition suppresses later,
   concentration-dependent responses;
4. the temporal filter simultaneously stabilizes identity and decorrelates
   overlapping odor representations.

Primacy coding itself predates 2026 and is **not** claimed as new.
Lateral inhibition has also been used in electronic-nose classification and
is **not** claimed as new.

## GSL transfer hypothesis

Treat source hypotheses, not sensor channels, as the competing population.

For each odor encounter and each currently valid source hypothesis s, construct
a causal instantaneous evidence stream e_s(t) from the measured hit/absence and
the candidate's predicted hit probability along the executed trajectory.

The proposed imported principle is:

- an encounter opens a short source-blind early-evidence window;
- hypotheses that become consistent first form a sparse primacy set;
- later evidence from highly overlapping hypotheses is inhibited rather than
  accumulated indefinitely;
- only the surviving early/decorrelated evidence is allowed to influence the
  source posterior.

This is intended to test whether late accumulated transport-dependent evidence
is a cause of the historical false-confident collapse.

## Exact novelty boundary to check

Not new by itself:

- latency coding in electronic noses;
- primacy coding in biological olfaction;
- lateral inhibition in artificial olfactory bulbs;
- temporal memory in plume navigation;
- concentration ranking.

Targeted candidate novelty:

**event-locked early-evidence selection plus delayed cross-hypothesis
inhibition used to decorrelate physics-based source hypotheses in robotic gas
source localization.**

No direct equivalent was found in the targeted GSL search as of 2026-09-21.
This is not an exhaustive novelty proof.

## Why this candidate survived the first collision screen

The following newer olfactory ideas were rejected before implementation:

- neural-manifold learning: 2026 GSL already uses manifold learning/UMAP;
- generic working memory: temporal/spatial memory already exists in robotic
  plume navigation;
- sensory adaptation: adaptive threshold/baseline mechanisms already exist;
- generic olfactory-bulb lateral inhibition: already used in 2026 e-nose
  processing;
- active sniff/rotation/bilateral motion: direct robotic-olfaction precedents.

TPSD therefore proceeds only to a cheap offline screen, not to ROS.

## Promotion requirement

The 2026 delayed-inhibition mechanism must outperform all of:

1. native PMFS;
2. ordinary cumulative temporal likelihood;
3. early-window/primacy-only evidence;
4. latency/ranking-only evidence;
5. generic lateral-inhibition without the delayed temporal rule.

Evaluation must end at the native PMFS top-5% ExpectedValue endpoint, not only
candidate rank.

If delayed inhibition is not consistently better across multiple Houses, stop
this branch.
