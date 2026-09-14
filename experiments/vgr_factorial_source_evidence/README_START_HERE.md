# VGR factorial source-evidence audit

Date: 2026-09-14

## Decision

```text
REFERENCED_TASK_USED_NEW_PUBLIC_DATASET = YES_OREBRO3DSEN
REFERENCED_TASK_STAYED_ON_CCDE = NO_SWITCHED_TO_M1R_TROQL_OQIC
VGR_VM_ASSET_FOUND = YES
VGR_NUMERIC_REPLICATION = FAIL_PSEUDOREPLICATES
VGR_ZERO_EXPOSURE = FAIL_21_OF_72_EPISODES
SOURCE_BLIND_CONTRAST_ROUTE_PREMISE = ALREADY_NO_GO
MAIN_INNOVATION_EFFECTIVE = NOT_ESTABLISHED
```

The referenced Codex task used the newly located public Orebro3DSEN real-sensor
dataset.  It did not merely replace one CCDE dataset with another: it changed the
mechanism line from CCDE to M1R/TROQL/OQIC.  Its reason for not treating VGR as
untouched confirmation was scientifically valid—VGR is simulated—but the task
did not make clear that VGR could still be audited as a development asset, nor
did it expose the defects of the available VGR derivative.

## What is actually present on the VM

The shared VGR/GADEN scenarios are under
`/mnt/hgfs/workspace/GADEN_files/scenarios` and include House01 through
House20.  The already collected factorial derivative is
`/home/zyc/SCTT_DISCOVERY_DATASET_V2_R2_20260817`:

- four source positions;
- three nominal wind conditions;
- three nominal plume seeds;
- two source-blind fixed routes;
- 72 episodes of 750 rows each.

The source files were copied read-only into an ignored staging directory.  The
auditable result is `REPLICATION_AUDIT.json`.

## Decisive VGR defects

The numeric audit hashes only the raw concentration and processed sensor
series, deliberately excluding identifiers and metadata.  In every one of the
24 source x wind x route cells, all three nominal plume seeds have the same
numeric signal hash.  Thus the 72 files contain 24 unique signal realizations,
not 72 independent plume realizations.  In addition, 21/72 episodes contain no
gas hit at all.

Consequences:

1. the files are useful for a deterministic development diagnostic;
2. they cannot estimate session-conditional nuisance or support source-blind
   cross-fitting across independent plume realizations;
3. treating the repeated metadata labels as independent evidence would be
   pseudoreplication;
4. the asset is neither untouched nor real-sensor confirmation evidence.

## Core scientific idea retained

An admissible innovation must change the true source's evidence relative to
fixed wrong candidates *before* Bayesian accumulation.  It must remain
source-blind at inference, survive transport/acquisition controls, and beat a
source-association shuffle.  Posterior blending, a lower threshold, abstention,
or a better-looking endpoint rank does not create source information.

## Candidate generated and why it is rejected

The isolated idea-spark run generated one candidate: a nuisance-null signed
contrast route that would select waypoint pairs with stable candidate
separation, compile them into a source-blind route, and emit paired-difference
evidence before Bayes.

That direction is not opened for another VGR run.  The repository already
contains stronger, precommitted premise tests:

- 12 map-only source-blind routes: 0/12 passed the design-wind observability
  gate;
- 150 s sensing-support upper bound: 0/12;
- 222.8 s support extension: 0/12;
- observability-aware learning falsification: NO-GO;
- held `W_altfast`: correctly left unopened after the design-wind failure.

The replication audit does hash the already-spent 72-episode derivative, which
contains rows labeled `W_altfast`; it does not query the protected raw held-wind
cache or execute a new held-wind gate for the rejected route candidate.

The generated candidate assumes the existence of stable, flight-feasible
source-separating edges.  The existing gates and the new pseudoreplication audit
invalidate that premise in the available House02/VGR asset.  Running another
edge selector or opening the held wind would repeat a closed route and inflate
the chance of a false positive.

## One next mechanism and required evidence

The only surviving mechanism from the Orebro terminal audit remains
`CROSS_FITTED_TRANSPORT_STRATIFIED_E_VALUE`: a candidate-relative, pre-Bayesian
e-value calibrated within transport strata using source-blind folds, with
evidence combined only across independently replicated strata.

It cannot be validated on this VGR derivative because the nominal plume seeds
are numerically identical, and it must not be tuned on the spent Orebro
confirmation pair.  The decisive next object is therefore a certifiably
untouched factorial dataset with at least two source positions, at least two
transport conditions per source, and multiple genuinely independent
acquisition sessions per cell.  Until that asset exists, the honest verdict is
`MAIN_INNOVATION_EFFECTIVE = NOT_ESTABLISHED`.
