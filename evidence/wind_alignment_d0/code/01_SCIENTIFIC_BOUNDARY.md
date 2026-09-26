# Scientific boundary

Do not merge the two mechanisms.

## HZ — height contract defect

Historical Native candidate forward:
`state 0, z=0`.

Actual measurement wind:
`z=0.30 m`.

If changing only the forward grid to `state 0, z=0.30` materially improves
source identity, this is a **baseline/adaptation correction**, not a paper
innovation. The Native baseline must then be repaired before screening new
ideas.

## HDYN — dynamic transport mismatch

Each measured event was formed from ten sensor readings that traversed a
source-blindly recoverable sequence of wind states. The historical candidate
forward nevertheless used one static full spatial field: state 0.

The D0 dynamic question is deliberately smaller than a full time-varying plume
simulator:

> Do candidate probabilities become more source-informative when each event is
> evaluated against the mixture of static forward responses corresponding to
> its recovered wind-state sequence?

This is a first-order mixture diagnostic, not a claim that transport operators
commute or that a mixture equals true switching dynamics.

If this diagnostic is positive, the next scientific stage may test a genuine
time-ordered switching transport operator. If it is null/adverse, do not build
that larger model.

This is distinct from JTD, Source-Lineage and M4:
- no temporal neural model;
- no trajectory reconstruction;
- no source×wind learned factorization;
- no new score family beyond the already frozen raw-event proper scores.
