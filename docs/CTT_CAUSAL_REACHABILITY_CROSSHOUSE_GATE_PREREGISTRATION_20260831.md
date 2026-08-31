# CTT causal-reachability cross-House premise Gate

This Gate freezes the requested two-module method before its cross-House
scores are read. It reuses the audited 1.2468 GB native physical bank and does
not run GADEN, train a network, read a PMFS posterior, or inspect localization
error.

## The two modules

For candidate source `s` and frozen nuisance member `m`, M1 is the native
interventional response

```text
do(S=s) -> native GADEN concentration -> run-persistent delayed sensor.
```

The sensor is propagated over the entire trajectory before any event is
extracted. Its state is never reset at a movement, stop, or source update.

M2 reduces each distinct physical stop to one right-censored reachability
event. A physical stop is one maximal contiguous stationary run; only its first
80 samples are used and shorter runs are excluded. Let `E[s,m,r,b]` be one if
the sensor exceeds `0.1 ppm` within that window. The candidate predictive
probability is

```text
p[s,r,b] = (0.5 + sum_m E[s,m,r,b]) / (8 + 1).
```

For a held-out reserved observation, the source score is the censored
Bernoulli composite log likelihood

```text
L[s] = sum_b E_obs[b] log p[s,b] + (1-E_obs[b]) log(1-p[s,b]).
```

Fast transport and placement nuisance is marginalized inside each stop. No
turbulent realization identity is forced to persist across stops. The object
is a finite-ensemble composite likelihood, not an exact joint likelihood for
autocorrelated stops.

Precise first-passage phase remains a report-only ablation. It cannot rescue a
failed reachability Gate because fresh H01 winds already showed that exact
phase was not a stable increment over reachability.

## Independence and data split

- predictive bank: eight `train` members;
- observation generator: four disjoint `reserved` members;
- Houses: H01/H02/H03;
- fixed historical routes: seeds 0..9, accepted only after exact schedule-hash
  equality between the historical OFF file and both bank splits;
- independent units: the 12 `House x reserved-member` pairs. Sources, routes,
  stops and seeds are repeated measurements inside those units.

## Hard decision

All conditions in the JSON contract are required. In short: pooled normalized
true-source rank must be below 0.30, every House below 0.35, all 12 independent
units better than random, at least 9/12 below 0.35, and deterministic
source-label destruction must have empirical `p<=0.01` both pooled and within
each House. All hash and permutation contracts must pass.

A PASS is only a cross-House physical premise. The next step is a measured-only
source-update shadow against native PMFS on the existing 30 OFF runs. True
paired 300 s closed loop additionally requires a trajectory-independent native
lookup, exact source-channel single consumption, and planner closure.
