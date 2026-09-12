# M1 observation-provider finding, 2026-09-10

## Outcome

PHIC's `aggregate_raw_exposure` is NOT a concentration observation provider.
This is a formula/input contradiction, not evidence that causal inference or
cross-House generalization is impossible. No new simulator/seed was run.

Source inspection in revisions 8d2e211, 429b19f and current HEAD shows:
simulateSourceInPosition increments hitMap once when at least one filament
centre occupies a cell during a recording timestep, then copies hitMap into
exposureMapBeforeNormalization. Dividing by 200 yields occupancy frequency,
not ppm. Raw-record audit: all 268,224 entries are integers in [0,200].
No concentration kernel, filament mass or ppm conversion enters this exported
quantity. The PHIC branch applies FOPDT to a surrogate frequency; that cannot
be claimed as the physical sensor response without a validated observation law.

## Two executed falsification checks

1. Persisting the sensor state and 0.4 s delay on the documented truth-region
   candidate's zero exported history produces exactly zero response, assuming
   zero initial state/input. Therefore a sensor-only repair of these supplied
   inputs cannot fix the zero-support failure. Actual unrecorded prehistory
   remains unknown; do not generalize this to physical non-observability.
2. Synthetic early and late concentration pulses have equal aggregate 5.0 but
   their delayed sensor outputs differ by up to 0.5654017915. Hence even a
   true integrated concentration would not determine the chronological sensor
   sequence. A timestep occupancy aggregate supplies still less information.

The auditor and raw/source hashes are recorded in
evidence/cstar_m1_phic_observation_contract_20260910.json.

## Corrections to candidate and identity interpretation

The exported (-0.5,-2.92999983) is a representative coordinate of a quadtree
region. SimulationSource(node,...) samples that region for each filament;
it is not simply a fixed point displaced from the true source. A fixed unknown
source and a spatially distributed release law are different models. Region
boundaries and source-sampling semantics must be checked before claiming a
discretization diagnosis; do not tune a candidate to the truth coordinate.

The old build report's binary hash a4fc15d... differs from the PHIC runtime
manifest's a943d83... . VM is reachable but the /dev/shm PHIC build is absent;
VM checkout HEAD is 88701c7, not local ec391ca. Inspected git revisions therefore
do not establish an exact historic binary/source binding. No live processes
were stopped and no checkout was overwritten.

## Implementation made in this checkpoint

The Python concentration-likelihood API now requires explicit input_semantics
`time_resolved_concentration` and rejects aggregate occupancy/frequency labels.
Updated the exact GADEN diagnostic caller and unit tests. This contract check
prevents an accidental known mismatch; labels do not themselves certify the
provider. The old C++ PHIC branch is preserved as negative evidence, not promoted
to the new M1 or silently changed into another physical model.

## Narrow next implementation

Audit/implement a chronological source-conditioned observation provider, with
explicit source position (fixed within each member), concentration units,
sensor prehistory, observed wind availability and map dimensions. If using
filaments, concentration needs a mass/size kernel and unit conversion; centre
occupancy alone is insufficient. Region uncertainty must marginalize fixed
source hypotheses, not quietly represent multiple simultaneous source points.

Compare this provider with the native response on the same trajectory before
changing source posterior or controller. Estimated-wind deployment and
evaluator-wind diagnostics must remain separate. Correct observation semantics
is necessary implementation work, NOT by itself a causal main innovation:
source-conditioned evidence must additionally outperform same-input standard
Bayesian inference under controlled transport changes and in the fixed
House123 single-seed closed-loop screen.
