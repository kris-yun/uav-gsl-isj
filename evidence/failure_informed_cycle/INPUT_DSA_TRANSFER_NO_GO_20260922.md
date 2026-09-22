# InputDSA / input-demixed dynamical similarity transfer — NO-GO

Date: 2026-09-22
Status: **NO-GO AS MAIN LINE**

## Mother idea

Cross-domain origin: computational neuroscience / dynamical-systems comparison.

Scite anchor:
- Huang, Ostrow, Singh et al., **InputDSA: Demixing then Comparing Recurrent and Externally Driven Dynamics** (2025), arXiv:2510.25943.

The paper extends Dynamical Similarity Analysis by separating intrinsic/recurrent dynamics from externally driven dynamics using a DMD-with-control / subspace-identification formulation. The motivation is directly relevant to this project because robot motion and wind are strong shared drives that can create false dynamical similarity.

Related public reference implementation:
- https://github.com/CMC-unit/fastDSA
- paper: *Fast dynamical similarity analysis* (2025), arXiv:2511.22828.

No dedicated public InputDSA repository was found in the targeted GitHub search at this time.

## GSL transfer tested

For each case and source candidate:
1. measured signal = continuous measured-gas trajectory up to the frozen source update;
2. candidate signal = source-conditioned simulated hit probability sampled along the same robot trajectory;
3. external input = source-independent robot position and measured wind components;
4. standardize observed and input channels;
5. form a fixed five-delay state (1 s at 0.2 s sampling);
6. identify DMDc-style intrinsic operator A and input operator B;
7. align measured/candidate delay-state coordinates with an orthogonal Procrustes map;
8. score each source by equal-weight normalized discrepancy in aligned A and B.

A simpler scalar ARX/DMDc version was also checked as a sanity screen.

No source truth enters the operator estimation.

## Development result: old six + now-unblinded new six

### Scalar ARX/DMDc demixing
- all-12 mean = **5.2645 m**
- pooled reduction = **8.99%**
- non-worse = **7/12**
- old six = **3.33%**, 3/6
- new six = **14.21%**, 4/6

### Delay-state DMDc + orthogonal operator alignment
- all-12 mean = **4.3921 m**
- pooled reduction = **24.07%**
- non-worse = **7/12**
- old six = **28.12%**, 4/6
- new six = **20.32%**, **3/6**

Per-case delay-state endpoint errors:
[4.8289, 4.1299, 2.7102, 5.6008, 2.4636, 4.2233,
 4.8693, 3.0023, 1.3775, 1.7250, 8.1893, 9.5853] m.

## Decision

The method fails the failure-informed development gate before destructive-null escalation:

- fewer than 4/6 new independent-plume development cases are non-worse;
- the result is not consistently transferable across stochastic plume realizations;
- the scalar and delay-state forms disagree materially in case-level behavior.

No delay number, ridge strength, input-channel subset, Procrustes objective, or DMD rank was tuned after seeing these results.

Final verdict:

`INPUT_DSA_GSL_TRANSFER_NO_GO_20260922`

The conceptual lesson remains useful: shared external drive is a major confound and future dynamical methods should explicitly audit it, but InputDSA-style operator demixing is not the next main innovation on this corpus.
