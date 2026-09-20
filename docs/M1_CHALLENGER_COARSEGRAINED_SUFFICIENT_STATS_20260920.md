# M1 Challenger 6 — Coarse-Grained Sufficient Statistics for Hidden Source Inference

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: SCREENED / NO-GO AS M1

## Remote-domain provenance

Primary source:
- Wu & Jia, *Parameter Inference and Nonequilibrium Identification for Markov Networks Based on Coarse-Grained Observations*, Physical Review Letters 134, 087103 (2025), DOI 10.1103/PhysRevLett.134.087103.

Core scientific idea:
- the microscopic state of a stochastic system may be experimentally inaccessible;
- one observes only a coarse-grained state trajectory;
- an appropriate set of sufficient statistics can retain all statistical information available in that coarse-grained trajectory for parameter inference, under the paper's Markov-network assumptions.

This is a genuine statistical-physics inference object, not generic feature engineering.

## Structural GSL analogy

Potential mapping:
- hidden plume microstate -> inaccessible turbulent filament/flow microstate;
- coarse-grained observed state -> thresholded gas-sensor state along robot trajectory;
- unknown model parameter -> source location;
- coarse-grained path sufficient statistics -> source evidence.

Scientific question:
> Can path-level sufficient statistics of a coarse-grained plume observation preserve source identity that is lost by marginal concentration occupancy?

## Existing-data proxy

Data:
H01/H02/H03 × {SA,SB} × {fast,slow}.

Fixed source-blind concentration states:
[0,1e-4), [1e-4,1e-3), [1e-3,1e-2), [1e-2,0.1), [0.1,1), >=1 ppm.

Representations:
1. OCC — coarse-state occupation fractions only;
2. MARKOV — occupation + transition probabilities + state dwell means/CVs;
3. FULL — MARKOV + length-3 state motifs.

Evaluation:
- fast-wind source references;
- slow-wind held condition;
- horizons 120/150/180/210/240 s;
- deterministic time permutation preserves occupation exactly but destroys path ordering.

## Results

### Physical-support sanity
H02 at 120/150 s:
- OCC, MARKOV, FULL all remain 0/2.
- the representation does not manufacture missing source support.

### H01
At 180 s:
- OCC: 2/2, ratio 0.726;
- MARKOV: 2/2, ratio 0.687;
- FULL: 2/2, ratio 0.661.
Time permutation hurts path statistics, confirming they contain temporal information.

But:
- at 150 s all remain only 1/2;
- at 240 s OCC ratio 0.456 while MARKOV/FULL worsen to ~0.594/~0.557.

### H02 after support
180 s:
- OCC ratio 0.581;
- MARKOV 0.664;
- FULL 0.670.

210 s:
- OCC 0.416;
- MARKOV 0.514;
- FULL 0.525.

240 s:
- OCC 0.300;
- MARKOV 0.456;
- FULL 0.443.

Thus path statistics are consistently less source-stable than simple occupancy in this House.

### H03
120/150 s:
- OCC = 2/2;
- MARKOV = 2/2;
- FULL falls to 1/2.

180 s:
- all reach 2/2 but OCC has the best wind/source ratio (0.285 vs ~0.390/~0.417).

210 s:
- OCC remains 2/2;
- FULL drops to 1/2.

The higher-order coarse path object therefore adds transport-sensitive structure rather than stable source identity.

## Destructive-control interpretation

Time permutation often changes MARKOV/FULL and sometimes reduces held-source identity, so temporal path information is genuinely present.

However:
> temporal dependence being real is not enough; it must be source-specific and transport-stable.

Across H02/H03, the additional transition/dwell/motif information is frequently more transport-specific than source-specific.

## Theory-transfer limitation

The PRL result assumes a Markov network observed through a fixed coarse-graining and derives sufficiency for parameters of that network.

Robotic GSL differs materially:
- the observation operator changes with robot position;
- wind/geometry change the latent dynamics;
- concentration thresholds are a moving projection of a spatial turbulent field;
- source location is a persistent boundary/input parameter, not simply a transition-rate parameter of one stationary coarse-grained Markov chain.

Therefore the exact sufficiency theorem cannot be imported directly.

## Decision

COARSE-GRAINED SUFFICIENT-STATISTICS M1 = **NO-GO**.

Reason:
- excellent theory provenance;
- structurally interesting analogy;
- but its unique path statistics do not beat the simpler marginal occupancy baseline across the existing Houses.

Allowed future use:
- analysis of what information sensor coarse-graining destroys;
- not a main innovation or auxiliary slot.
