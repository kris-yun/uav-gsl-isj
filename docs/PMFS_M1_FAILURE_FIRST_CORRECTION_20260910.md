# M1 failure-first correction, 2026-09-10

Scope: continuation from ec391ca. No ROS run, new seed, bank rebuild,
controller change, or M2 work. Historical evidence remains untouched.

## Measured finding: model zero is not physical non-observability

Re-read the PHIC H01 seed12 attribution CSV (SHA256
0c20fc4691885ba3156a2a9228d87713678edc7d0dd71d3b01751ef624115e27).
The previously documented truth-region candidate quadtree_23_16_1_1 is at
(-0.5, -2.92999983), not the exact simulated source (-0.4, -2.9).
It has 1,584 member rows, grouped into 528 update/block/cell event records.
299 positive event records have zero aggregate exposure in all three members.
The first is update 1, block 6, cell 675, t=45.5969597 s:
concentration 0.113416292, threshold 0.1. Other candidates have nonzero
exposure (145,464 rows across the full export); the export is not globally zero.

These counts include repeated historical export across updates, NOT independent
observations or the exact subset used in each likelihood update. The auditor
also reports 88 distinct timestamp/cell records, 41 positive. Truth is used
only for evaluation.

This falsifies the inference in PMFS_M1_PHIC_H01_SEED12_VM_SCREEN_20260909.md
that zero predicted exposure establishes route non-identifiability. It does
not prove the converse (hits alone do not prove all-source identifiability).
Transport support, discretization, sensor memory and alignment remain competing
explanations. No full candidate posterior is recorded in this CSV; the exact
time the truth region was excluded remains unmeasured.

## Formula-code evidence

Current internal/Simulations.cpp::sourceProbFromContrastiveEvents initializes
fopdtState=0 inside each scoring call/member. Its first event uses
iterationsToRecord*deltaTime (200*0.2=40 s), rather than actual persistent
sensor prehistory. It uses aggregate exposure, clipped to [0,1], and subtracts
a raw context exposure logit without filtering that context through the same
sensor history. No explicit 0.4 s delay appears in this branch. These are
source-inspected discrepancies, not a demonstrated attribution of closed-loop
loss. Match the historic binary/source before attributing every detail to it.

Do not fix this by carrying one scalar through calls: candidate changes,
historical replay, and source-dependent transport histories require explicit
state identity and a chronological observation provider.

## Confidence-gate correction

counterfactual_likelihood.py formerly compared log-likelihood contrast in nats
against a sum of response-unit standard deviations and observation sigma.
The decision changed under a pure concentration-unit conversion. Removed that
automatic conversion. Without an independently justified whole-contrast error
bound in nats the result is now UNCALIBRATED. The optional bound interface is
conditional arithmetic, not a statistical calibration method or causal theorem.

Recomputed the two-source/opposite-wind audit into a new V2 artifact. Rankings
remain 12/12, but all 12 decisions are uncalibrated. V1 confidence PASS is
withdrawn, not relabeled as a source-information failure. Also clarified that
both wind regimes enter sigma calibration: excluded same-wind scoring means
do not make the entire evaluation held-out-wind.

## Next gate, before any closed-loop expansion

1. Bind historic source/binary and event selection to the export. Record
   candidate prior, likelihood increment and posterior in a future diagnostic
   replay; never infer truth rank from MAP and entropy.
2. On the same recorded trajectory, compare native source responses with a
   chronological, persistent sensor-consistent response. Use all map-derived
   candidates, not a truth-selected online candidate set. Diagnostic exact
   source simulations may identify discretization error but are evaluator-only.
3. Separate observable estimated-wind inputs from evaluator wind fields.
   If only evaluator input repairs support, deployment is still unproven.
4. Evaluate support violations, source ranking and predictive calibration;
   member agreement is not evidence against shared systematic error. No
   scalar posterior tempering or House-specific tuning substitutes for this.
5. Freeze one justified M1 and the matched baseline; only then run
   House1/2/3 seed12 with the same controller. Failed pilot means no multiseed
   expansion. These reused Houses remain development, not unseen datasets.

The established progress here is an attribution correction and safety fix,
not M1 closed-loop effectiveness or a new causal-theory contribution.
