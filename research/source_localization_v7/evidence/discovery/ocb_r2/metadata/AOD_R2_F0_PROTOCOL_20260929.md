# AOD-R2 F0 matched-source neighborhood mechanism gate

Frozen before opening any S2/S2X concentration. This is an OCB-R2 prospective replication of the **original** AOD `u-ABS` versus `rawu-ABS`, not House03 F1 exact replay or full-map localization. Input is the 64 qualified H01/H02 discovery runs only. H01/H02 confirmation and H03 stay sealed.

## Preparation

1. Metadata-only D0A must verify eight House–wind–gas–occupancy–generator–timeline contexts, each with exactly two configured source XYZ positions and four independent seeds per source. Otherwise STOP.
2. Use the existing E1 source-blind 30 probes per House at z=0.20 m. Requested physical times are 50, 100, ..., 500 s. For each run/slot choose the native record minimizing absolute time error; on exact ties choose the earlier actual time, then lower record index. Freeze all 640 mappings and wind indices before concentration extraction.
3. Within each House's Native legal candidate axis (H01 596, H02 630), freeze `N(s)={c: ||XY(c)-XY(s)||_2 <= 0.30 m}` for each of the four original configured truths. Both neighborhoods in every context must be nonempty and disjoint. The target source z is retained as provenance; this is explicitly a **2D XY neighborhood** test, not exact 3D-source identification.
4. Freeze only the union of the two neighborhoods for each context. The PMFS candidate input retains the House's entire legal `sources.csv` ordering, while the forward runlist invokes only those neighborhood source indices. Each selected candidate receives all 11 canonical wind states and PMFS keys 1..8. `u` and `rawu` must come from each same forward realization; use the audited Native 1.5-cell Gaussian blur and occupancy correction. No historical six-source mean or full-support mean is mixed in. Commit the runlist/input hashes before the first forward.
5. Only after steps 1–4, extract the frozen native snapshots into one 10×30 GADEN concentration observation per target. Preserve zero observations and extraction hashes. No time/probe changes after observing values.

## Frozen scoring

Use the unchanged `research/amplitude_operator_decoupling_v0/amplitude_readout.py` B2 score: `min_{g>=0} ||y-g m_c||²`, `EPS=1e-9`, static template broadcast over ten slots, same candidate set, gain profile, and tie semantics for both arms. `u` and `rawu` differ only in the PMFS amplitude blur.

For a target from truth source `s`, let `b` be the other configured source in the same context. For each arm:

`best_truth=min_{c in N(s)} SSE(c)`; `best_alt=min_{c in N(b)} SSE(c)`; `D_arm=(best_alt-best_truth)/max(||y||², EPS)`; `Delta_D=D_rawu-D_u`.

If `||y||²=0`, set both D values and Delta_D to zero and retain the target. A strict neighborhood win is `D>0`. `RESCUE` is `D_u<=0 and D_rawu>0`; `HARM` is `D_u>0 and D_rawu<=0`. There is no exact-cell rank, full-support Top-1, posterior, centering, conditional filter, or network in F0.

Aggregate four independent realizations first within each of the 16 context×truth groups. Report group mean/median Delta_D, positive-realization count, u/rawu win counts, rescue, harm; then context, House, and overall summaries. Ten slots and 30 probes are parts of one target, not extra independent samples.

## Decision (frozen before target values)

`AOD_R2_F0_LOCAL_SIGNAL_POSITIVE` requires **all**:

1. Median of the 16 group-mean Delta_D values > 0.
2. Median of the eight H01 group means > 0 and median of the eight H02 group means > 0.
3. At least 10/16 group means > 0.
4. Total RESCUE > total HARM.
5. Improvement is not supplied by one context alone: recompute the median group mean after omitting each of eight whole contexts in turn; all eight leave-one-context-out medians must remain > 0. This operationalizes the supplied “not only one context” condition without looking at outcomes.
6. A second complete scoring pass produces byte-identical scientific output.

If the overall median is positive but any of conditions 2–5 fail, decision is `AOD_R2_F0_HETEROGENEOUS_HOLD`. If the overall median is nonpositive and RESCUE does not exceed HARM, decision is `AOD_R2_F0_NO_SIGNAL`. Remaining nonpositive-median/rescue-positive cases are conservatively `AOD_R2_F0_HETEROGENEOUS_HOLD`. Infrastructure/contract failure yields `AOD_R2_F0_INFRASTRUCTURE_HOLD`, never a scientific result.

Even on POSITIVE, stop: no full 596/630 candidate generation, no confirmation/H03, no GADEN, no PMFS closed loop. This gate can only justify considering a later full-map experiment.
