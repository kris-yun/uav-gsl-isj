# AOD-R2 transfer audit (discovery only)

**Status: audit complete; no AOD-R2 target scoring authorized by this audit.**

This is a read-only compatibility check for the original AOD comparison, `u-ABS` versus `rawu-ABS`. It uses the qualified OCB-R2 S2+S2X inventory: eight fixed House–wind–gas contexts, each with two original configured sources and four independent GADEN realizations per source (64 targets total). H01/H02 confirmation and H03 were not opened. No target concentration, source score, or rank was computed; no GADEN or PMFS forward was run.

## Frozen AOD object

- The scored quantity is the archived B2 positive-gain profile SSE, `min_{g>=0} ||y-gm_s||^2`, with `EPS=1e-9`, strict unique minimum, and the same candidate axis for both arms. There is no posterior, centering, conditional filter, or learned calibration. See `research/amplitude_operator_decoupling_v0/amplitude_readout.py` and `research/aod_house03_f1_full624_20260927/execution/score_amended_f1_vm.py`.
- Both arms must come from the **same PMFS forward realizations**. `rawu` is the pre-blur mean filament count; `u` applies the Native 1.5-cell Gaussian blur and the same occupancy correction. The 0.20 m × 0.20 m footprint is an area average; no outside-map or occupied-area renormalization. The static PMFS map is broadcast over the ten observation times.
- The PMFS count proxy is not calibrated GADEN concentration. B2 profiles a positive gain, but that alone does not establish equivalent physics or source height.

## Context-level inventory

| Context | House | Wind | Gas | Full legal PMFS bank | Existing six-source `u/rawu` forward | Transfer status |
|---|---|---|---:|---:|---|---|
| X00 | H01 | `1,3-2,4_fast` | 13 | 596 `p/rawu` | 6×11×8 | Conditional reuse after wind/occupancy and reconstructed-`u` parity; H01 bank was rebuilt on Native legal occupancy |
| X01 | H01 | `1,3-2,4_slow` | 13 | none | none | Full 596-candidate PMFS bank absent |
| X02 | H01 | `2,4-1_fast` | 10 | none | none | Full 596-candidate PMFS bank absent |
| X03 | H01 | `2,4-1_slow` | 10 | none | none | Full 596-candidate PMFS bank absent |
| X04 | H02 | `3,5-1_fast` | 10 | none | none | Full 630-candidate PMFS bank absent |
| X05 | H02 | `3,5-1_slow` | 10 | 630 `p/rawu` | 6×11×8 | Conditional reuse after wind/occupancy and reconstructed-`u` parity |
| X06 | H02 | `4,5-3_fast` | 13 | none | none | Full 630-candidate PMFS bank absent |
| X07 | H02 | `4,5-3_slow` | 13 | 630 `p/rawu` | 6×11×8 | Conditional reuse after wind/occupancy and reconstructed-`u` parity |

The six-source maps cannot be substituted for complete source localization. The complete banks were built with 11 wind states × 8 PMFS transport keys per candidate, but their retained `.npz` files contain only `p` and `rawu`, not `u`; the per-forward full-support products were deleted after hashing. For the three existing banks, `u` can be generated from each bank's saved mean `rawu` by the frozen linear blur/occupancy operator, subject to a pre-target numerical parity check. The read-only audit script checked all **1,584** retained six-source forward realizations: reconstructed `u` matched each stored `u` exactly in float32; blur-of-mean versus mean-of-blurs differed by at most `4.90e-5` map units. This validates the operator, not bytewise equality of the missing full-support `u` products. The old six-source and full-support rawu means are not bytewise equal for the same source ID; these are separate forward campaigns with different candidate indexing, and H01 also has a different legal occupancy rebuild. The exact cause of the mean differences was not isolated here. Do not silently mix their source means.

The PMFS forward input has no gas-type parameter. Gas is fixed within each OCB-R2 context, so a paired `u/rawu` comparison remains possible, but the PMFS bank cannot be described as gas-type-matched. Wind names match for X00/X05/X07; numerical parity between the old 2D PMFS z=0.20 wind export and OCB-R2's original 3D wind conversion is **not yet established**. A name match is not an asset-hash match.

## Target observation contract

S2/S2X archive complete native filament states and a per-run `record_index → internal_simulation_time_s → wind_index` timeline (1803 records, 0–999.502991 s). The old House03 F1 signed record IDs `91,174,...,965` belong to a different writer/timebase and **must not be copied onto OCB-R2**. Native states can in principle be concentration-extracted without new GADEN, but exact extractor binary, native-grid geometry, z=0.20 plane, file schedule, and area-averaging parity need a source-blind preflight before any target values are read.

The existing E1 contracts provide 30 fixed, source-blind 2×2 probes for each House at z=0.20 m. This is the closest existing H01/H02 AOD observation geometry (10×30); House03 F1 instead used two 10-stop, one-reading-per-slot paths. An AOD-R2 discovery result using E1's 30 simultaneous probes would be a **new, clearly labeled OCB-R2 replication**, not a numerically identical replay of House03 F1. Select and hash one physical-time/record mapping, extractor, probe order, and observation shape before target extraction. Do not select times or probes by plume values.

## Configured truths versus candidate support

The four original configured H01/H02 source coordinates are **not PMFS 0.30 m candidate centers**. The nearest legal XY cells are 0.104–0.242 m away (full coordinates in `evidence/ocb_r2/aod_r2_transfer/ORIGINAL_TRUTH_TO_PMFS_SUPPORT.tsv`). PMFS candidate sources are at z=0.20 m; three of the four configured GADEN truths have different z values (0.40, −0.30, −0.10 m). Consequently, exact-cell truth rank, exact Top-1, and truth-vs-best-wrong margin as used by House03 F1 are **undefined** for this original-configuration panel. Assigning a nearest cell as the “truth label” would change the endpoint, and source-height mismatch cannot be removed by relabeling. A prospective scoring protocol must first specify a physically honest geometric endpoint or a separately justified representation of off-grid 3D truths. This audit does not make that choice after inspecting concentrations.

## Audit conclusion

**No context is ready for direct, exact AOD F1 scoring as-is.** Three have reusable full legal `rawu` model banks and an audited path to derive `u`, pending numerical wind/occupancy and observation parity. Five require full legal PMFS candidate templates under the frozen forward contract. All eight share the off-grid/height endpoint issue. The 64 qualified GADEN runs remain valid prospective targets; no additional GADEN is implied. See `AOD_R2_EXECUTION_PLAN_20260929.md` for the pre-target sequence. This document is not an AOD scientific PASS/FAIL.
