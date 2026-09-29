# OCB-R1 — Original-Configured Cross-House Benchmark
Date: 2026-09-29
Branch: `research/original-config-common-benchmark-r1-20260929`
Base: `b145b7b152ed8486122587a0d20294d842e26357`

Status: PREREGISTRATION / NO SIMULATION AUTHORIZED BY THIS FILE

## Why this replaces E2C 144

The source-location audit established that the released House01/02/03 scenarios
contain exactly TWO configured source positions per House, each paired with
fast/slow wind configurations. The previous E2/E2C panels use geometrically
valid but newly assigned runtime source coordinates and therefore constitute a
custom simulator benchmark, not the original source-location catalog.

For the main benchmark, do NOT invent additional source positions.

## Frozen original source catalog

House01
- (-0.60,  1.95,  0.40), gas 13, winds 1,3-2,4 fast/slow
- (-0.40, -2.90, -0.30), gas 10, winds 2,4-1 fast/slow

House02
- ( 0.00, -1.00,  0.20), gas 10, winds 3,5-1 fast/slow
- ( 1.00, -2.30, -0.10), gas 13, winds 4,5-3 fast/slow

House03
- (-0.45,  1.90, -0.10), gas 10, winds 1-2,5 fast/slow
- ( 8.20,  5.00, -0.20), gas 10, winds 5-3 fast/slow

There are therefore:
- 6 physical source positions total;
- 12 source x wind configurations total.

No runtime source-coordinate override is allowed.

## Fresh-realization design

For each of the 12 original source x wind configurations:
- generate exactly 8 independent fresh RNG realizations;
- keep source xyz, gas type, wind assets, occupancy and launch configuration
  unchanged;
- only RNG seed and output destination may vary.

Total planned new runs:
  12 configurations x 8 realizations = 96 runs.

Do not count the historical 2000 saved iteration files as 2000 realizations.
They are time records from one historical simulation per configured directory.

## Common observation operator

Use one source-blind operator in all Houses:
- raw GADEN concentration;
- the existing E1 House-specific 30-probe geometry rule;
- 2x2 native-grid mean footprint;
- z_observation = 0.20 m;
- the same ten certified writer-record selections;
- no Native adaptive trajectory;
- no stop averaging;
- no source-dependent probe selection.

If the ten-record writer/time mapping cannot be certified for the original
configured runs, HOLD before generation.

## Scientific role split

H01 + H02, per source-wind configuration:
- realizations 1-4: DISCOVERY;
- realizations 5-8: SEALED_STOCHASTIC_CONFIRMATION.

House03:
- realizations 1-8: SEALED_EXTERNAL_HOUSE_CONFIRMATION.

Important claim boundary:
- confirmation is fresh-realization confirmation at the ORIGINAL configured
  source positions;
- House03 is a fresh-data external-House confirmation;
- it is NOT an unseen-source-position claim, because the configured positions
  are known and historically studied.

## Scientific unit

Primary independent structural unit:
- physical source position (6 total).

Wind and plume realization are nested conditions, not additional independent
source identities.

Any later mechanism discovery on H01/H02 must report:
- both physical sources separately in each House;
- fast and slow wind results separately;
- House-aggregated source-balanced summaries.

A mechanism may advance only if its direction is not driven by one source or
one wind configuration.

## Discovery -> confirmation sequence

After all 96 raw runs are frozen and hashed:

1. Open only H01/H02 realizations 1-4.
2. Perform a finite, preregistered information-layer audit.
3. Identify at most ONE mechanism with the same direction across H01 and H02.
4. Freeze that mechanism and any theory-derived new prediction.
5. Open H01/H02 realizations 5-8.
6. If it survives, open House03.
7. Only after House03 confirmation may it enter PMFS probability-map and
   autonomous-navigation closed-loop testing.

## What E2 is now

E2 remains valid as:
  CUSTOM_GEOMETRY_SIMULATOR_BENCHMARK.

It may be used for exploratory diagnostics, but it must not be described as
sampling the original configured source-location catalog and must not be mixed
with OCB-R1 as if they shared source identities.

## Forbidden

- no new source coordinates;
- no changing gas type;
- no source-wind recombination outside the original launch catalog;
- no E2C 120/144 manifest execution;
- no selective rerun replacement after seeing concentration outputs;
- no mechanism score before raw-run/hash freeze;
- no H03 unsealing before the frozen confirmation stage;
- no VGR/ROS/planner changes in this benchmark stage.

## Required pre-run artifacts

research/ocb_r1/OCB_R1_TIMEBASE_AND_RUNNER_AUDIT.md
evidence/ocb_r1/ORIGINAL_CONFIG_CATALOG.tsv
evidence/ocb_r1/SEED_MANIFEST_96.tsv
evidence/ocb_r1/SPLIT_MANIFEST.tsv
evidence/ocb_r1/PRE_RUN_SHA256.tsv

These must be committed before the first successful simulation run.
