# M1 cross-House information audit (2026-09-09)

## Decision

Do not try to make M1 cross-House effective by further training or tuning a
source classifier.  The qualified controlled data contain a common causal
measurement chain, but they do **not** contain a factorial source--wind
intervention that identifies a source effect from raw histories alone.

The reproducible evaluator-only audit is:

```text
D:\Anaconda\python.exe -X utf8 experiments/ctpi_cstar/audit_m1_crosshouse_information.py \
  --out evidence/cstar_m1_crosshouse_information_audit_20260909.json
```

Its verdict is `M1_SOURCE_WIND_FACTORIAL_IDENTIFICATION_NOT_SUPPORTED`.
It does not alter a model input, route, source posterior, or simulator field.

## What is genuinely shared across H01--H03

The immutable 12-parent bundle verifies all of the following:

- a source/gas-blind, geometry-only history route within each House;
- the same causal observation operator: 0.2 s samples, 0.4 s piecewise-linear
  dead time, and a 1.2 s first-order state transition;
- measured gas and local wind prefixes at each route location; and
- source-independent candidate support registered to each House map.

The audit replays the archived authoritative sensor implementation against the
evaluator-only raw concentrations.  Its maximum absolute reconstruction error
is exactly zero for all 12 parents.  This corrects the tempting but wrong
shortcut of treating the sensor as a delay-free `tau=1.2` exponential filter.

## What the data do *not* identify

Every House has two exact physical sources and two observed transport
realizations per source, but no complete normalized wind-file sequence occurs
for two distinct sources.  The complete realization `transport_fingerprint`
is source-specific, so it is not a valid wind-intervention identity; the audit
therefore compares the actual normalized wind sequence and replay semantics.
That stricter comparison still finds no shared wind intervention.  Hence the
bundle supports same-source robustness diagnostics, not the causal comparison
`do(S=s)` versus `do(S=s')` at fixed wind.

The observed concentration histories show why a history-only representation
cannot repair this by itself.  The ratio of mean within-source (different
transport) RMS to mean cross-source RMS is:

| House | Ratio |
| --- | ---: |
| H01 | 0.952 |
| H02 | 0.205 |
| H03 | 0.289 |

Thus H01's transport-induced trajectory difference is almost as large as the
average cross-source difference, while H02/H03 happen to separate more in
this tiny sample.  A learned representation can exploit that accidental
House-specific geometry/signal relation, but cannot establish a transferable
source mechanism.  This agrees with the failed PICR LOHO controls and the
M1H cross-House failure; it is not a wind-index or map-alignment failure.

## Consequence for the M1 innovation

The valid cross-House estimand is a **candidate-conditioned, sensor-consistent
counterfactual likelihood**, not an invariant embedding of raw histories:

```text
do(S=c), observed route + wind history
  -> candidate exposure time series
  -> exact delayed FOPDT sensor state
  -> continuous/block observation likelihood
  -> transport-member marginal posterior or abstention
```

This is the concrete version of the partial-invariance rationale in
`PMFS_CORE_M1_PHIC_DESIGN_20260909.md`: source-responsive evidence may be
shared, while candidate-by-transport discrepancy must remain explicit rather
than being centered away or merely variance-penalized.

The existing `cer_core_phic_m1` is therefore only a wiring diagnostic.  It
uses an aggregate exposure map at each source update, whereas the above law
requires a time-resolved candidate exposure trace and the persistent sensor
state.  Its H01 seed12 failure is correctly interpreted as non-identifying
route evidence, not as a parameter to retune.

## Required next M1-only gate

Before another closed-loop M1 run, build one source/gas-blind, precommitted
candidate-forward witness for each House that records, per candidate and
transport member, the route-time exposure sequence.  Then freeze these three
items together:

1. the exact delayed FOPDT replay and continuous likelihood;
2. an observability rule that abstains when the visited route has insufficient
   candidate contrast; and
3. a source-by-transport factorial microbank (two admissible sources under
   the same two transport realizations per House), generated independently of
   M1 scores.

`tools/cstar_generate_current_runtime_dataset.sh` specifies such a microbank,
but it is a generator, not evidence: it has not been qualified as part of the
current immutable asset bundle and must not be treated as if it had already
supplied the needed intervention pairs.

## Independent current-runtime factorial development evidence

There is a separate, self-consistent current-runtime development bundle:
`evidence/cstar_current_runtime_assets240_20260907`.  It must not be mixed
with the immutable raw bundle above, but it does contain a true two-source by
two-transport design per House.  The companion audit
`audit_m1_factorial_signal.py` verifies its hashes and computes orthogonal
source, wind, and source-by-wind interaction contrasts from the evaluator-only
arm labels.

At 180 s, the source-main-effect / source-by-wind-interaction RMS ratios are
H01 `2.76`, H02 `6.85`, and H03 `2.67`.  At 60 s, H02 has no source-main
effect and H03 is near the interaction scale.  Hence the shared empirical
condition is not an early gas-pattern classifier; it is **conditional
observability**: only assimilate a candidate likelihood after the visited
route makes predicted source contrast exceed transport interaction.

This explains why a time-local, candidate-conditioned observability gate is a
scientific M1 repair, whereas another global invariance loss or early-posterior
tuning is not.  The current-runtime PICR screen remains a NO-GO, because it
does not provide the candidate-forward sensor-consistent likelihood required
to use this condition in a real PMFS posterior.

Only if this M1 premise gate improves true-source compatibility over the
native likelihood in held-out source--transport cells is a single-seed
House123 M1 closed-loop screen justified.  M2 is deliberately out of scope
until that M1 gate has passed.
