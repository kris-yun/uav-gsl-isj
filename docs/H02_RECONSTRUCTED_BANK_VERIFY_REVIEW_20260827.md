# H02_RECONSTRUCTED_CHALLENGE_V1 — bank verification review

Date: 2026-08-27
Status: **BANK VERIFIED / POST-BANK PRE-OUTCOME**

## Verified product

Uploaded freeze/verify bundle establishes:

- challenge identity: `H02_RECONSTRUCTED_CHALLENGE_V1`;
- historical hard-28 remains `LEGACY_HARD28_PROVENANCE_LOST` and was not recreated;
- outcome-blind frozen context atoms: 51;
- frozen geometry carriers: 201 unique coordinates;
- transport members: 8;
- records per context: 1,608;
- total records: 82,008;
- total trace bytes: 2,646,234,144;
- builder SHA-256: `31d81e18e41319769751d328adca04f92232fda7967ed86ae6a205026a3f99b4`;
- context manifest SHA-256: `fea1b64d7a7a47c072cfd6f9e8b52c1f2dfa41263e6b32e3669fe6737f8aee55`;
- carrier manifest SHA-256: `06dd0f91bc837a2e0bb698f11ce802045ac42f3957ff222e5e7c61488bc3fcc4`;
- independent verifier verdict: `H02_RECONSTRUCTED_CHALLENGE_V1_BANK_VERIFY_PASS`.

The verifier checked complete 201×8 carrier/member coverage, record headers, exact file sizes, zero reconstruction error, per-context CTT V13 contract, carrier-manifest identity, and absence of temporary trace files.

## Dependence structure frozen before outcomes

The 51 atoms are not 51 independent experiments.

They comprise:

- 11 distinct `run_uuid` values;
- 6 seed clusters: `0`, `332814273`, `661532441`, `783030861`, `845534703`, `859169523`;
- for five nonzero seeds, historical OFF and ON trajectories contribute repeated source updates.

Therefore the V3 H02 analysis contract defines:

`cluster_id = seed`

and treats OFF/ON trajectories and repeated source updates within one seed as dependent observations. The preregistered cluster-level advancement rule must be evaluated by seed cluster, not by pretending all 51 atoms are iid.

## Archived metadata versus allowed model inputs

All 51 historical `candidate_manifest.csv` files advertise a `native_score` column. This does not invalidate the outcome-blind freeze because the selection procedure did not use its values; it used structural existence, identifiers and hashes only.

However `native_score` and historical `source_posterior` values are explicitly forbidden as V3 model/scoring inputs. They may remain hashed provenance artifacts only. Final `forbidden_feature_audit_pass` remains pending until the actual method-input pipeline is frozen and checked.

## Frozen CTT rebuild contract

- family: `CTT_V13_TRUTH_FREE_TRACE_BANK_V1`;
- method seed: `20260818`;
- transport substream: `6077111455669390931`;
- members: `8`;
- timesteps: `200`;
- dt: `0.2`;
- noise standard deviation: `0.5`;
- source truth used: `false`.

## Immediate post-bank path

No new source margin, bridge result, localization result or new-seed experiment was generated in the bank stage. Therefore full multi-seed closed loop is not yet authorized by this bundle alone.

The next outcome-blind pipeline is:

1. freeze seed-cluster analysis manifest;
2. materialize compact CTT tensors from `.cttbin`;
3. perform header-only discovery of surviving measurement/event-history logs;
4. if event history survives, freeze the event schema before reading values and materialize `Z[s,m,e]=H_e phi[s,m]`;
5. if event history does not survive, use deterministic shadow replay to export actual-event `rawProbabilities[s,m,e]` rather than substituting unvisited full-field support;
6. only then reveal evaluation truth and compute V3 source margin / adequacy / destruction controls;
7. if the frozen H02 reconstructed verdict passes, hand off immediately to the existing 3-House × 10-seed OFF/ON closed-loop matrix.
