# PF-DEI-SR V2 autonomous closed-loop report

Date: 2026-08-28
Terminal status: `PF_DEI_PHYSICAL_BANK_ENGINEERING_NO_GO`

## Frozen history

- Requested remote HEAD: `0f2824ed237570961d33b83c832d32df84335e58`
- Active branch: `codex/pf-dei-final-autonomous-closed-loop-20260828`
- V2 merge commit: `591851f`
- Evidence/support freeze commit: `78e6299`
- V1 terminal evidence remains reachable at `2fc133f`.
- Preserved commits `a504e0e`, `6fbf08c`, `33f9a80`, and `55dd893` remain reachable; no reset or overwrite was used.

## V2 contracts that passed

1. Persistent carrier support was checked against all 50 geometry-only context NPZ files per House. H01/H02/H03 contain 210/201/206 carriers, respectively; all 150 geometry priors match the carrier free-cell weights.
2. The planar target is the native PMFS `S_xy`; no historical source z was copied.
3. Geometry-only vertical support was enumerated from native `OccupancyGrid3D.csv` free voxels inside each exact quadtree carrier footprint. All 617 nonzero-prior carriers have legal height support (19–29 distinct native z levels).
4. Source strength is fixed at `Q=10.0 ppm` from source-independent House launch parameters. The filtered configuration hashes are recorded in `source_strength_manifest.csv`.

Artifacts and hashes:

| Artifact | SHA-256 |
|---|---|
| `source_support_xy_manifest.csv` | `fcdd9f93420f228bcd4c51868627bd4012de467d54ac99444bfd323d4dedfff4` |
| `source_height_support_manifest.csv` | `33f622aea84317cc2e2fdcacd6a76e4bb02367e72dd06552b32fe40a200ea6ff` |
| `source_strength_manifest.csv` | `a27da2b6adcf5a8974ad72d6976f16899c693b42878cc4a9564681a29b4eee4a` |
| `nuisance_manifest.csv` | `4f3e19f480ff045631c473794bd58642b2e2f006891f5cada5b01184e17c20da` |

## First failed downstream contract

V2 requires eight auditable native transport members with seeds `101,211,307,401,503,601,701,809`, plus reserved seeds `907,1009,1103,1201`. The preserved GADEN source currently uses static default-constructed `std::mt19937` engines in `MathUtils.hpp` and exposes no seed/substream parameter. The relevant VM source hashes are:

- `MathUtils.hpp`: `86727e26c7f799d213250a77a29fc4fb98c7262066a57614dd58990667fa2265`
- `filament_simulator.cpp`: `6d2bf5cd234205c6981846aca18a190f47a5ce2143d6204da5d09901f61643a8`
- preserved native query binary: `f6070d681b7e738bf8713a5462e0bbb7aaf1c1f30ea62bd4b7bbc83a9b1f50fc`

The query binary only samples an already materialized field. The active repository contains no V2 arbitrary-candidate native-field materializer. Therefore the required `(House, planar source, height, Q, transport seed)` bank cannot be generated with the frozen nuisance contract. Reusing one default RNG stream, substituting occupancy/hit maps, or adding an unplanned transport variation would violate V2.

## Stages intentionally not run

No new GADEN field, training/reserved bank, source-independent trajectory dataset, causal-TCN training, synthetic qualification, truth-blind historical qualification, offline safety, runtime integration, smoke, 60-arm matrix, or confirmatory seeds were started. No true source, historical `true_gas_ppm`, future observation, occupancy-to-ppm conversion, Active Probe, architecture sweep, Gate/temperature/blend, or result-driven nuisance expansion was used.

This is an engineering/materialization NO-GO under the frozen V2 contract, not evidence that PF-DEI-SR scientific inference or the planar formulation fails. The next permissible action is to provide a reproducible native GADEN seed/substream interface and a source-independent candidate-field materializer, then rerun V2 from the frozen support/manifests without changing the method.
