# Candidate Challenger — Multi-Fidelity Source Inference

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: SCREENED / DEMOTED

## Remote-domain provenance

Primary recent anchor:
- Nature Communications 2026 — Shi et al., *A multi-fidelity tabular prior-data fitted network model for accurate prediction and uncertainty quantification*.
  - explicitly fuses low- and high-fidelity data and models cross-fidelity correlations.
  - demonstrates CFD use among the evaluation tasks.

Additional scientific lineage:
- multi-fidelity modeling is a mature scientific-computing paradigm for combining cheap approximate models with expensive high-fidelity observations/simulations.

## GSL translation

Low fidelity:
- existing PMFS / estimated transport / reduced plume response.

High fidelity:
- exact GADEN candidate-forward simulations during development;
- DNS plume data;
- controlled wind-tunnel measurements.

Candidate thesis:
> combine low- and high-fidelity source-response data to infer a source probability map robustly while minimizing expensive high-fidelity supervision.

## Existing-project fit

The project provides a textbook fidelity gap:
- exact candidate-conditioned opposite-wind responses rank the source correctly in 12/12 controlled cases;
- the H01 deployable estimated provider can reverse source ranking;
- high-fidelity source responses are expensive and sparse.

## Why it is not promoted to M1

1. “multi-fidelity” describes the data/resource relation but does not by itself identify **what physical error should be learned**.
2. a generic cross-fidelity mapping can collapse into ordinary response regression and inherit the blank-dominated MSE pathology already demonstrated in H01.
3. source-independent fidelity correction is contradicted by the 10/12 failed cross-source residual transfers.
4. the strongest recent Nature Communications implementation is a general tabular predictor/UQ architecture, not a new physical mechanism specific to turbulent source evidence.
5. the current learned-missing-physics candidate is a stricter scientific statement: it explicitly models the structured discrepancy of the coarse prior and places the correction inside the physical response chain.

## Decision

MULTI_FIDELITY_AS_M1 = DEMOTED

Allowed use:
- training/data-efficiency strategy for the missing-physics corrector;
- high-fidelity data allocation and low/high-fidelity batching;
- comparator.

Not counted as one of the final 1+2 innovations unless a future test shows a distinct, source-localization-specific mechanism not captured by missing-physics correction.
