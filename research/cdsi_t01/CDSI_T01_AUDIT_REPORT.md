# CDSI-T0.1 matched-intervention prerequisite audit

Date: 2026-10-01

Branch: `research/cdsi-t01-1d-information-audit-20261001`

Base: `169a54da59a33e4f170e20bed27c616968ab6294`

Request/script initial freeze: `c5743248` (metadata audit only).

## Decision

**`CDSI_T01_MATCHED_INTERVENTION_FAIL` — STOP at Gate A.**

This is an execution-contract failure, not a negative source-information result.
G1/G2/G3 and all scientific statistics are **NOT EXECUTED**.

## Verified evidence

| Check | Result |
|---|---:|
| Exact discovery run count | 64 |
| Contexts / proposed A-B ordinal pairs | 8 / 32 |
| Same House, wind, gas, non-source simulation parameters | 32/32 |
| Same input asset hashes, generator, time axis, wind sequence, single-worker contract | 32/32 |
| Same master random-stream identity | **0/32** |
| Distinct master random streams | **32/32** |
| Archive/repository manifest semantic parity | 64/64 |
| File hashes matching R0's frozen tensor-input hashes | 64/64 |
| Tensor numerical values deserialized or analyzed | 0 |

Example X00 / ordinal 1:

- S2: `ocb_r2_cfg00_r01`, master seed `2026900001`.
- S2X: `ocb_r2_s2x_x00_r01`, master seed `2026910001`.
- The ordinal `r01` denotes position within separate runlists, not a shared disturbance stream.

The original S2X plan explicitly prohibits reusing the S2 master seed and calls
for independent realizations. The run wrappers bind `master_seed` directly to
`GADEN_RNG_SEED`. The frozen generator derives the Gaussian/uniform streams
from that seed with fixed salts. These 32-bit seed values differ; there is no
documented additional common-stream identity mapping.

S2X `parent_s2_run_id` also does **not** establish pairing: all four S2X runs
within a context reference that context's S2 `r01` manifest as the non-source
configuration provenance. The audit records this field separately.

## Execution boundary

No new GADEN, PMFS forward, training, closed loop, PMFS change, 3D upgrade,
confirmation or House03 access occurred.

Only run metadata and frozen-input file bytes for hash binding were read. No
concentration/tensor numerical values were loaded. Full plume payloads were
not rehashed: archive metadata parity is a metadata audit, not a new complete
raw-archive integrity certification.

Per-context cosine, covariance, crossnobis, FULL/STATIC/C2 effects, and null
distributions are not supplied because the signed protocol orders STOP when
Gate A cannot establish matched intervention. R3A geometry calculations are
also deferred at that stop boundary. Existing source xyz are preserved in
`SOURCE_COORDINATES.tsv`; no new source was selected.

## Audit implementation correction and repeat

The first metadata-only execution stopped on an overly strong assertion that
each S2X run's provenance parent must equal the same-ordinal S2 run. Inspection
of `prepare_s2x_freeze.py` showed that all S2X replicates inherit the context's
`r01` contract. The assertion was corrected to that actual documented
provenance; it did not relax the master-stream requirement. No scientific
calculation was executed during this correction.

The corrected complete audit was executed twice. All generated tables and
result JSON must be byte-identical; details are in `DETERMINISTIC_REPEAT.json`.

## Interpretation

The historical S2X dataset qualification and subsequent independent-source
comparison are not invalidated. They used matched non-source environmental
conditions with independent physical realizations, as originally intended.

The new request changes the estimand to a same-disturbance source intervention.
The existing design cannot support the claim that subtracting same-ordinal A/B
runs holds the disturbance fixed or removes realization noise. Independent
samples can still support source-distribution comparisons under a separately
specified protocol. Such an amendment is not executed here.

Do not record this as `CDSI_T01_NO_SOURCE_INFORMATION_STOP` or `THEORY_PASS`.
No source-information test has taken place in this audit.
