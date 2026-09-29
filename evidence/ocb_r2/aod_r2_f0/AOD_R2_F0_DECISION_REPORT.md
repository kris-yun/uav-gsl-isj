# AOD-R2 F0 matched-source neighborhood gate

Decision: **`AOD_R2_F0_NO_SIGNAL`**. The frozen positive gate failed. Stop the AOD-R2 F0 mainline at this local mechanism gate; no full 596/630 candidate bank, confirmation, House03, GADEN, or closed loop was run.

## Contract and qualification

- D0A metadata audit: 8/8 fixed House–wind–gas–occupancy–generator–timeline strata, each containing two original configured source positions and four independent realizations per source.
- Targets: 64 qualified H01/H02 discovery GADEN runs. Each target used the frozen nearest native record to 50, 100, ..., 500 s and the E1 source-blind 30-probe 2×2 footprint at z=0.20 m. Time mapping was committed before concentration extraction. No zero target was removed.
- Source test: 0.30 m XY neighborhoods around the two configured truths; 4 selected legal PMFS candidates per H01 context and 5 per H02 context. This is a local two-source discrimination test, not full-map localization or 3D exact-source classification.
- Forward: 3,168 local PMFS runs, 11 canonical OCB-R2 wind states × 8 transport keys per selected candidate. Each `u` and `rawu` map came from the same realization; only amplitude blur differed. Mean banks and individual output hashes were frozen before target extraction. No new GADEN run.
- Score: archived B2 nonnegative gain-profile SSE, `u-ABS` versus `rawu-ABS`, same footprint operator and candidate set. Four plume realizations were aggregated within each source×context group before applying gates.

## Frozen result

| Unit | Median of group mean ΔD | Positive groups | `u` neighborhood wins | `rawu` neighborhood wins | Rescue / harm |
| --- | ---: | ---: | ---: | ---: | ---: |
| House01 | −0.02774144 | 2/8 | 32/32 | 32/32 | 0 / 0 |
| House02 | +0.07973757 | 6/8 | 32/32 | 32/32 | 0 / 0 |
| Overall | −0.00732356 | 8/16 | 64/64 | 64/64 | 0 / 0 |

The House01 median, overall median, 10/16 positive-group threshold, rescue advantage, and leave-one-context-out requirement all failed. Two complete scoring passes produced byte-identical JSON/TSV files. The 64/64 wins in both arms are a local two-source ceiling: they do not measure either arm's full candidate-map Top-1 accuracy. The signed F0 result is therefore no incremental local AOD signal in this OCB-R2 test, while the historical House03 full-map result remains a separate observation under a different acquisition/generator contract.

The forward uses the hashed OCB-R2 3D wind axes sampled at the PMFS candidate z=0.20 m and the fixed House legal occupancy; it is a prospective asset-matched bank, not an exact replay of the older House03 F1 wind input. Full concentration cubes, compact targets, compact mean banks, source code, native frozen snapshots, inventories, and scores are retained in the review ZIP for independent recomputation.
