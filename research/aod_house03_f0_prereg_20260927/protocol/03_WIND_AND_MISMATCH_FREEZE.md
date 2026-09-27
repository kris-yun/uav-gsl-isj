# House03 wind and mismatch contract

## Target / nominal environment

Use the already declared House03 scenario:
`1-2,5_fast`.

Audit and freeze:
- all 11 numbered wind CSV states;
- occupancy/navigation assets;
- GADEN configuration;
- source z=0.20 m compatibility;
- exact hashes.

No gas realization is opened in F0.

## Candidate amplitude forward for later F1

For each of the 12 selected source candidates, later generate the same PMFS
forward replicas for both `u` and `rawu` in one run.

Nominal candidate template:
average the same 11 wind states with equal frozen weight.

The score will remain archived B2 for both arms.

## Single predeclared mismatch diagnostic

Use **state-0-only candidate templates** as the sole model-mismatch condition.

Why:
- requires no additional simulator family;
- represents a deployment-relevant under-modeling of wind-state variability;
- applies identically to `u` and `rawu`;
- does not require target outcomes to choose a mismatch.

Do not add rotations, alternate wind families, noise sweeps or additional
mismatch strengths after outcomes are seen.

F0 only audits that nominal 11-state and state0-only templates can both be
constructed from the same later PMFS bank.
