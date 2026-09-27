# Full 624-candidate template contract

## Support

Candidate support is the complete frozen:
`HOUSE03_CANONICAL_SOURCE_GEOMETRY_BANK_624.tsv`.

No candidate may be removed because:
- its template is weak;
- it is far from the 12 truth sources;
- u/rawu are poorly separated;
- it causes a rank error.

The 12 truth sources are members of this 624 set.

## Forward bank

Use exactly:
`HOUSE03_FUTURE_PMFS_SEEDS_FULL624_54912.tsv`.

For every candidate:
- 11 states;
- 8 replicas/state;
- same Native PMFS forward settings;
- same occurrence operator;
- export u and rawu from the same forward realization.

## Nominal template

For each candidate, average:
- 8 replicas inside each state;
- then states 0..10 with weight 1/11.

## Stress template

Use only the same 8 state-0 realizations already present in the nominal bank.

Terminology:
this is a **reduced wind-state coverage + reduced template Monte Carlo depth
stress condition**.

It is NOT a pure causal wind-error experiment, because nominal uses 88 forward
samples/candidate while the stress condition uses 8.

Do not add a replica-depth control, alternate wind, rotation or sigma sweep in
this F1.

## Observation operator

Primary arms:

C0 = `u_footprint` + archived B2

C1 = `rawu_footprint` + same archived B2.

Nearest readout remains an implementation regression only.

Do not change B2, fit a new gain model, add B0 to the score or form a softmax
posterior.
