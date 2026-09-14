# Next stage — finite-horizon physical support audit

Date: 2026-09-14
Starting evidence: `1be4363959fcf7909e935568bb74d0a0dbd4328b`

## Purpose

This is a **physics qualification task**, not an innovation test.

The goal is to determine whether the current House02 / Main-V8 / 150 s / frozen-FOPDT setting fails because:

- the plume does not physically reach robot-accessible space;
- the gas reaches accessible space but slow sensor dynamics erase usable contrast;
- usable contrast exists but current trajectories miss it;
- or physical support is adequate and the remaining failure is genuinely inferential.

Do not create another localization score in this task.

## Phase P0 — freeze assets

Use only the existing audited raw caches and authoritative occupancy map.

No new GADEN, no posterior, no planner, no source-specific runtime policy.

Audit source/wind/cache hashes and preserve the existing Main-V8 physical identity.

## Phase P1 — raw transport-support map

For each source x design wind pair, using raw gas before FOPDT:

At horizons 60, 120, 150, 240, and 300 s, compute over robot-accessible free cells:

- first-arrival time above the pre-existing physical gas floor;
- fraction of accessible cells ever reached;
- connected reached area;
- cumulative concentration exposure;
- maximum and median exposure;
- earliest time at which at least 1%, 5%, 10%, and 25% of accessible cells are reached.

Do not tune the gas floor from localization performance.

Output a source x wind x horizon support table and maps.

## Phase P2 — sensor-surviving support

Replay the frozen FOPDT at the same accessible cells / representative deterministic grid sample.

For each source x wind x horizon, report the fraction of raw-supported cells that retain a non-negligible FOPDT response.

Classify separately:

```text
RAW_SUPPORT
FOPDT_SURVIVING_SUPPORT
```

This distinguishes transport failure from sensor-bandwidth failure.

## Phase P3 — route-coverability

Using the existing frozen admissible motion model, estimate whether the support identified above can be intersected by a 150 s route without source truth as a deployment input.

This is not an optimizer competition.

Report only:

- reachable support fraction from admissible start regions;
- shortest map-distance / travel-time to supported regions;
- whether one source-wind support region is effectively unreachable within 150 s;
- whether a common route corridor exists that intersects non-negligible support for all source hypotheses.

## Phase P4 — failure-layer classification

For every source x wind pair, assign exactly one primary label, with evidence:

```text
RAW_TRANSPORT_SUPPORT_FAILURE
SENSOR_BANDWIDTH_FAILURE
TRAJECTORY_COVERAGE_FAILURE
SUPPORT_ADEQUATE_INFERENCE_REMAINS
```

If evidence does not separate two layers, use `UNRESOLVED` and state the minimum missing measurement.

## Hard scientific rules

- Do not expand route budgets to rescue the previous persistent-excitation result.
- Do not use W_altfast for method selection.
- Do not call adjoint/domain-of-dependence a novel contribution; 2026 AIAA SciTech already applies this idea to turbulent scalar source localization.
- Do not introduce a network, Bayesian correction, causal score, threshold sweep, or new dual-receiver representation.
- No cross-dataset or causal claim.

## Decision after audit

If most failures are `RAW_TRANSPORT_SUPPORT_FAILURE`:
- stop algorithm development on the current 150 s House02 experiment;
- choose between a longer physically justified horizon or a new validation environment.

If most failures are `SENSOR_BANDWIDTH_FAILURE`:
- the next scientific design variable is sensor modality / response time, not inference.

If most failures are `TRAJECTORY_COVERAGE_FAILURE`:
- measurement design may reopen, but route generation must be guided by transport-support physics rather than map-only diversity.

If support is adequate but source identity still collapses:
- only then return to inference/model innovation.

## Required GitHub outputs

```text
PHYSICAL_SUPPORT_AUDIT.json
RAW_SUPPORT_BY_SOURCE_WIND_HORIZON.csv.gz
FOPDT_SUPPORT_BY_SOURCE_WIND_HORIZON.csv.gz
ROUTE_COVERABILITY.json
FAILURE_LAYER_CLASSIFICATION.json
PHYSICAL_SUPPORT_AUDIT_REPORT.md
SHA256SUMS
```

Final response fields:

```text
branch
starting SHA
final SHA
RAW_SUPPORT_VERDICT
SENSOR_BANDWIDTH_VERDICT
ROUTE_COVERABILITY_VERDICT
DOMINANT_FAILURE_LAYER
MAIN_INNOVATION_STATUS
NEXT_SCIENTIFIC_DECISION
```

Then stop.
