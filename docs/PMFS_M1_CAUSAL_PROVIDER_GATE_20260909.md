# M1 causal provider gate: from factorial response to full-map PMFS

> 2026-09-10 correction: C1 below remains historical ranking evidence only.
> Its confidence PASS is withdrawn (nats were compared to concentration-unit
> error). The V2 calibration audit reports all decisions UNCALIBRATED.
> PHIC `aggregate_raw_exposure` is a cell-occupancy timestep count, NOT
> concentration. C2 must provide chronological concentration with audited
> units; relabeling occupancy or adding FOPDT memory does not meet C2.
> See PMFS_M1_OBSERVATION_CONTRACT_FINDING_20260910.md.

## Current completed gate: C1

`CSTAR_M1_EXACT_COUNTERFACTUAL_TRANSFER_V1` is a **necessary premise gate**.
For each House and each target `(source, wind)`, the candidate score receives
only the opposite-wind GADEN `do(source=candidate)` raw input, composes the
fixed delayed FOPDT law, and marginalises no candidate-independent context.
All 12 two-candidate cases ranked the evaluator-only source first and passed
the abstention criterion.  The VM replayed controller-visible histories have
the same SHA-256 values as the frozen current-runtime assets.

C1 is deliberately limited: two source hypotheses per House are not full-map
localisation and no controller was changed.

## C2: deployable full-map forward-provider gate

The next implementation is a provider, not another posterior correction.  For
each source candidate in the geometry-only PMFS support it must emit

`(timestamp, candidate raw exposure, transport member)`

under the executed route and causal wind history.  The causal M1 core then
performs the only allowed conversion to a likelihood:

`do(S=candidate) -> time-resolved exposure -> exact FOPDT -> member marginal likelihood`.

Required invariants:

1. Store each wind/route observation with its timestamp before source scoring;
   a current wind snapshot or accumulated exposure map is rejected.  In the
   deployed PMFS path, a wind observation is the **GMRF-estimated full 2-D
   field** available after each completed measurement block, not an
   interpolation of the local anemometer reading.
2. The provider starts from a declared physical initial condition and carries
   source-specific transport state and FOPDT state through the whole prefix.
3. Source coordinates are generated exclusively from the frozen geometry-only
   candidate support.  It cannot receive source truth, House ID as a feature,
   future gas, future wind, posterior rank, or a development-bank lookup.
4. The provider must be evaluated against held-out members of the existing
   GADEN source-by-wind factorial bank before its PMFS score is enabled.
   Its error/margin report is required for H01/H02/H03 separately.
5. When predicted candidate contrast is bounded by member plus sensor
   discrepancy, the C++ integration records `ABSTAIN`; it may not fall back to
   an old centered-logit, duration, posterior-mass, or distance rule.

### Wind-information boundary

The raw GADEN `wind_iteration_*` volumes are evaluator-side environmental
authority only. They may verify map/time alignment and score a held-out
simulator response, but must never be read by the online M1 provider. Treating
them as a runtime wind field would leak a simulator-hidden state.

The online provider may instead consume PMFS GMRF fields. PMFS obtains those
through its ordinary `/WindEstimation` service with `useWindGroundTruth=false`
(the formal launch default). Each history item must bind `(block_id, sim_time,
pose, map hash, GMRF-grid content fingerprint)`. Transport members represent uncertainty in that
estimated field; they are not post-hoc, per-House adjustments.

The current `cer_core_phic_m1` violates C2 because its `wind` is a single
current grid and its input is an aggregate exposure map.  It remains a
preserved negative diagnostic and is not a C2 candidate.

## C3: one-seed closed-loop pilot

Only after C2 passes may `House1/House2/House3 x seed12` run with the frozen
baseline controller and a new M1-only arm.  It must report, per House:

- provider identity/hash and raw result hash;
- C2 contrast/abstention state before each update;
- terminal error and source-found state relative to the frozen baseline;
- no planner weight, source-conditioned setting, or House-specific parameter.

Failure of C2 prevents C3.  Failure of C3 is a causal-M1 NO-GO unless a
reproducible formula--code contradiction is demonstrated.  Passing C3 is a
pilot result, not multi-seed cross-dataset proof.

## C2 attempt A: rejected local-wind continuum surrogate

`CSTAR_M1_TEMPORAL_PROVIDER_ALIGNMENT_DIAGNOSTIC_V1` tested a causal,
prefix-only finite-volume provider against the exact 12-case GADEN forward
bank.  It is rejected before score integration: its mean log-concentration
shape correlations were H01 `0.234`, H02 `0.183`, and H03 `0.159`; it also
predicted nonzero exposure through most frames where the filament simulator
produced sparse intermittent support.  This is a structural response-family
mismatch, not a parameter to tune.

The next C2 implementation must therefore retain filament transport state and
replay a timestamped wind-field history.  It may not replace sparse filaments
with a local-wind continuum surrogate or rescue this attempt with diffusion,
amplitude, duration, or House-specific parameters.
