# Active Source–Transport Deconfounding V1 — Offline NO-GO

Date: 2026-09-21

Research branch:

`research/active-source-transport-deconfounding-v1`

Frozen final commit:

`2bd715e3285b5f6cf77b490df14984d628424f95`

## Verdict

**NO_GO_WITHIN_FROZEN_OFFLINE_SCREEN**

The screen used six already-seen development contexts, a frozen 27-value
design transport bank and 8 held-out grid-off transport values.

Necessary promotion cases: **0/6**.

For every case:

- greedy source-MI minimum separation = 0;
- two-step deconfounding minimum separation = 0;
- held-out passing worlds = 0/8.

No ROS planner modification or closed-loop experiment was authorized.

## What this result supports

The selected two-step actions did not resolve the ambiguity in this frozen
surrogate. At the selected action pair, the true-source representative
predicted no hits in all held-out worlds, while false sources several metres
away could produce the same no-hit response.

Thus the tested short-horizon active-deconfounding construction does not
provide a positive promotion signal.

## What this result does NOT support

This result does **not** prove that broad transport confounding is the
dominant cause of the historical TNQC/PMFS failures.

The local source-vs-fixed-false contrast retained roughly 92–100% of its
weighted energy after projection against the three tested nuisance columns.
That is inconsistent with claiming that these nuisance directions generally
span away the source contrast in the tested local diagnostic.

The result also does not prove that every possible active measurement policy
is uninformative. Some non-selected candidate actions predict nonzero
true-source responses in five cases.

The correct conclusion is narrower:

> this particular finite-bank, finite-budget, native-response surrogate and
> two-step deconfounding criterion is a NO-GO.

## Provenance

The V5 execution freeze remains unchanged at:

`b24da77fd24bd5ea2cbb33caf856f80b9d7670e4`

Release:

`tnqc-v5-r2-execution-20260921`

The research screen reports that 41 frozen runtime files remained unchanged.

A provenance limitation is preserved: the first H01/seed0 standalone wrapper
binary hash was not retained before an obstacle-only validation correction.
The wrapper source commit and response hash were retained. This limitation is
not a reason to promote or rerun the screen.

## Decision

Stop this research branch.

Do not rescue it by changing the nuisance bank, action gate or held-out
threshold after seeing these results.

The next candidate must attack a different failure mechanism and must again
pass a cheap, pre-registered offline screen before ROS implementation.
