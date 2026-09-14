# TROQL/OQIC external real-data gate V1

Date: 2026-09-14

## Scientific claim under test

The candidate main innovation is the **transport-replicated observation-
quotient identifiability certificate** (TROQL/OQIC).  It does not sharpen a
posterior.  Before Bayesian accumulation, it releases a candidate-relative
edge only when the observed spatial response distinguishes both endpoints
repeatedly beyond a same-source nuisance scale.  Unreleased edges remain in
one observation-quotient cell.

The bounded V1 claim is:

> Under matched physical sensing conditions, TROQL/OQIC can distinguish a
> replicated different-source edge while refusing a same-source edge, and the
> decision transfers without refitting to a disjoint real indoor experiment.

This is an identifiability claim, not a claim of closed-loop PMFS improvement,
online deployment, universal source recovery, or House/seed confirmation.

## Independent dataset

Use the public `jburgues/Orebro3DSEN` repository at upstream commit
`d5a55a0fc5e77b95456fbb7be62bc8154508dbee`.  It contains 27 simultaneous MOX
concentration channels on a 3 x 3 x 3 grid sampled at 2 Hz, source coordinates,
and measured wind.  The upstream paper and README state that source position,
release configuration, and airflow were varied.

The raw checkout lives only under `_staging/troql_external/Orebro3DSEN` and is
not rewritten.  Exact raw hashes are frozen in
`experiments/troql_oqic_external_v1/POLICY_FREEZE.json`.

## Outcome-blind representation

For every experiment:

1. discard the first and last 10 percent of samples;
2. divide the remaining prefix into 40 equal contiguous time blocks;
3. take the median of each of the 27 concentration channels in a block;
4. replace the 27 values by centered mid-ranks and L2-normalize them.

This removes absolute emission scale from the evidence and retains only the
spatial response ordering.  Even-numbered blocks form the candidate prototype
by a coordinate-wise median.  Odd-numbered blocks are never used in that
prototype and supply 20 replicated target decisions.  No source coordinate,
experiment label, beaker size, airflow label, or truth flag enters the feature
or distance calculation.

For target block `x` and candidate prototypes `p_a,p_b`, use cosine distance
and the pre-Bayes relative margin

```text
Delta_a_to_b(x) = d(x, p_b) - d(x, p_a).
```

Positive values favor the target's own candidate.  An edge is released only
when at least 18 of 20 target blocks exceed the frozen nuisance threshold in
**both** directions.  The threshold is the finite-sample upper 95 percent
conformal order statistic of absolute margins from the development same-source
pair.  It is computed once and carried verbatim into confirmation.

Temporal blocks are repeated plume realizations, not asserted IID samples.
The consistency count is therefore a deterministic replication gate, not an
IID p-value claim.

## Frozen stages and stop rules

### Development

- null edge `Exp01` vs `Exp02`: same source `(2.70, 0.50, 0.90)`, airflow off,
  closed window, different beaker size; it must remain unresolved;
- source edge `Exp02` vs `Exp03`: large beaker, airflow off, closed window,
  different source positions; it must be resolved.

Failure freezes `TROQL_OQIC_EXTERNAL_DEVELOPMENT_NO_GO`; confirmation remains
unread by the scorer.

### Untouched confirmation

Only after development passes:

- source edge `Exp06` vs `Exp07`: small beaker, DC fan, closed window,
  different source positions; it must be resolved;
- null edge `Exp08` vs `Exp09`: same source `(2.70, 0.50, 0.90)`, tower fan I,
  closed window, different beaker size; it must remain unresolved.

No feature, block count, trim, order statistic, direction count, or pair may be
changed after development.  Confirmation failure freezes
`TROQL_OQIC_EXTERNAL_CONFIRMATION_NO_GO`.

## Main-innovation gate

`TROQL_OQIC_MAIN_INNOVATION_PREMISE_PASS` requires all of:

- raw hashes and upstream commit match the freeze;
- the development source edge resolves and its null edge does not;
- the untouched confirmation source edge resolves and its null edge does not;
- scorer and policy hashes are identical between stages;
- no protected VGR/GADEN bank, held wind, unseen seed, or new House is read.

A pass establishes the bounded cross-dataset identifiability mechanism premise.
It still does not establish closed-loop localization gain; that would require a
separately frozen online provider and paired closed-loop evaluation.

