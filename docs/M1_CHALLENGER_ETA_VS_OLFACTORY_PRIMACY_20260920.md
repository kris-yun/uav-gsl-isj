# M1 Challenger Screen — η-Learning vs Adaptive Olfactory Primacy Coding

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: INTERNAL SCREENING / NO PAPER CLAIM

## Candidate A — Extreme Event Aware (η-) Learning

### Remote-domain provenance
Primary source:
- Chang & Sapsis, *Extreme Event Aware (η-) Learning*, Nature Communications, 2026.
- The method learns with an observable/statistic η that characterizes extreme regimes and constrains training so models do not fit only common/quiescent states.

### Structural match to turbulent GSL
Potential match:
- turbulent plume observations are intermittent;
- rare whiffs / first arrivals / upper-tail bursts can be source-informative;
- ordinary objectives can be dominated by blanks/common weak-signal states.

### Existing-data test
Using the 12 controlled H01/H02/H03 × {SA,SB} × {fast,slow} histories, compare:
- bulk representation: mean/median/lower-order statistics + overall hit fraction;
- tail/η representation: q90/q95/q99, max, top-1% mean, first/last hit, burst count/duration.

Held-wind source discrimination:
- H01 240 s: tail ratio (same-source wind / cross-source) 0.158 vs bulk 0.278; both 2/2.
- H02 180 s: tail 0.049 vs bulk 0.035; both 2/2.
- H02 240 s: tail 0.124 vs bulk 0.036; both 2/2.
- H03 120/180/240 s: tail ratios 0.206/0.152/0.341 vs bulk 0.107/0.089/0.142; both usually 2/2.
- H02 120 s: neither bulk nor tail has source identity (0/2), consistent with missing physical support.

### Interpretation
η/tail observables are clearly useful in the H01 late-intermittency regime and can rescue predictive-compression failures, but they are not uniformly more source-stable than bulk statistics across Houses.
Therefore:
- η-learning is **not strong enough as M1**.
- it remains a strong auxiliary mechanism specifically protecting rare/intermittent source evidence from being erased by a representation learner.

Decision:
**DEMOTE TO AUXILIARY CANDIDATE.**

---

## Candidate B — Adaptive Olfactory Temporal Filtering / Primacy Coding

### Remote-domain provenance
Primary 2026 source:
- Karadas et al., *Rapid temporal processing in the olfactory bulb underlies concentration-invariant odor identification and signal decorrelation*, Nature Neuroscience, 2026.

Scientific mechanism:
- the earliest activated glomerular/MTC channels form a short temporal window that preserves odor identity across concentration;
- later responses are more concentration-dependent;
- temporal filtering decorrelates odor representations.

Older lineage:
- Wilson et al., *A primacy code for odor identity*, Nature Communications, 2017.
- recurrent cortical and sniff-invariant coding work establishes the broader primacy-code lineage.

### Candidate transfer to GSL
Potential mapping:
- early plume encounter structure ↔ earliest activated olfactory channels;
- source identity ↔ odor identity;
- concentration/wind-dependent later plume response ↔ concentration-dependent later neural activity.

### Existing-data test
Fixed 0.1 ppm physical hit floor.
Representations:
- first 5 or 8 onset events;
- 20 s window immediately after first hit;
- full-history summary.

Held-wind classification (fast prototypes, slow held condition):
- H01: early-20 s = 2/2, full = 2/2; ratio improves 0.349 -> 0.198.
- H02: early-20 s = 2/2, full = 2/2; ratio improves 0.378 -> 0.207.
- H03: early-20 s = 2/2, full = 1/2; early ratio 0.708 vs full 0.727.

Synthetic concentration-scale perturbation (0.5× and 2× gas amplitude):
- H01 early-20 scale/source ratio 0.264 vs full 0.355.
- H02 0.113 vs full 0.114.
- H03 0.490 vs full 0.975.
Thus early-event representation is materially more amplitude-stable in H01/H03.

### Destructive control
Reversing concentration time order does not consistently destroy classification:
- H01 remains 2/2, though margin shrinks;
- H02 remains 2/2;
- H03 remains 1/2.

This reveals a structural mismatch:
- biological primacy coding relies on a *population of receptor channels* whose activation order identifies odor identity;
- current PMFS/GSL has primarily a scalar gas time series sampled along a moving path.
The first-hit window mixes route position, plume support and amplitude; it is not a direct analogue of receptor-population primacy coding.

### Interpretation
The 2026 Nature Neuroscience mechanism is scientifically strong and the existing data show that early encounter windows can be more transport/amplitude stable than full-history summaries.
However the transfer is not exact enough for M1 because the biological “primacy set” is a multi-channel receptor-order code, whereas the robot currently observes one scalar chemical channel along space-time.

Decision:
**CONDITIONAL AUXILIARY / BIOPHYSICAL INSPIRATION, NOT M1.**

---

## Head-to-head conclusion

Neither candidate replaces the current predictive-representation M1.

- η-learning: strong for preserving rare/intermittent evidence, but too regime-specific to carry the whole paper.
- adaptive olfactory primacy coding: elegant biological mechanism and positive proxy evidence, but the receptor-population-to-mobile-scalar mapping is not structurally exact enough.

Current consequence:
- keep **predictive latent physical representation** as the M1 leader;
- keep **η-learning / extreme-event-aware intermittency preservation** as the stronger auxiliary;
- do not promote olfactory primacy coding unless a multi-sensor or multi-feature “activation order” object can be defined without fabrication.

Next:
screen a third paradigm-level challenger against the same hard criteria and existing-data gates.
