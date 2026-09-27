# AOD House03 F0 freeze report

**Decision: AOD_H03_F0_READY_FOR_PREREG**

Branch: `research/aod-house03-f0-prereg-20260927`
Base: `25803d287aa299f78a06458e37437a91c3fa3890`
Final commit: recorded after committing in review ZIP `GIT_STATE.json`.

Source panel: 12 sources, 6 disjoint 0.30 m neighbour pairs. Minimum pair-center spacing: 4.373213921134 m.

| Pair | Source A | Source B |
| --- | --- | --- |
| 1 | pmfs_24_13 | pmfs_24_14 |
| 2 | pmfs_1_4 | pmfs_2_4 |
| 3 | pmfs_43_26 | pmfs_44_26 |
| 4 | pmfs_41_1 | pmfs_41_2 |
| 5 | pmfs_11_25 | pmfs_11_26 |
| 6 | pmfs_16_1 | pmfs_17_1 |

## Paths

Nominal speed: 1.500000 m/s. Start: (2,0). Slot: 50 s. Dwell: 3 s. Allowed travel: 47 s.

| Path | Ordered probe ranks | Route distance | Maximum segment travel |
| --- | --- | --- | --- |
| A | 16, 2, 27, 24, 1, 8, 6, 11, 15, 14 | 101.450466301 m | 14.243719019 s |
| B | 25, 17, 10, 12, 7, 23, 4, 5, 9, 13 | 100.988411280 m | 11.029505681 s |

Path overlap: 0. Full xyz, per-segment metric distances and timings are in the two path TSVs. Cell routes are in `PATH_SEGMENT_GEOMETRY.json`.

## Wind and future seeds

Family: `1-2,5_fast`; 11 states. CSV and preprocessed GADEN hashes are both recorded in `HOUSE03_WIND_HASHES_11.tsv`.

Nominal: equal 1/11 state weights, 8 replicas per state. Mismatch: state0 only, using the same 8 state0 replicas from the nominal bank.

Future GADEN manifest: 96 rows. Future PMFS manifest: 1056 rows. All seeds are deterministic, positive, unique and domain-separated. Nothing has been executed.

- `HOUSE03_FUTURE_GADEN_SEEDS_96.tsv`: `d67a84684b6cd5e99868113910c693ae455974749ef04b0c72205e5916d7b8a8`
- `HOUSE03_FUTURE_PMFS_SEEDS_1056.tsv`: `257c298772d1faf29201abb2981ab7eb13555922d2a94ab5da12d6d3f8b0b254`
- `HOUSE03_TEMPLATE_STATE_WEIGHTS.tsv`: `f5b8589e4fabf9d71b35f96e6d44ef5b812f704f15ce04c78dfdd6223c21973a`

## F1 timebase must be signed

Bind frozen relative slots 50,100,...,500 seconds to physical simulator timestamps and sufficient generation duration; do not reuse legacy frame indices as seconds or the 300-second generation duration without explicit F1 configuration.

The historical acquisition code has `sim_time=300.0` and `results_time_step=0.5`. It is archived as provenance, not adopted as a finalized future configuration. F0 keeps the supplied 50-second path budget and leaves physical snapshot binding to the final F1 preregistration.

## Stop boundary

No fresh GADEN plume, no PMFS scientific forward, no House03 gas array, no source score, no D1 rerun, and no F1 execution. The unchanged amplitude/B2/Native implementation is preserved at the stated base.
