# Codex start here — TNQC V4 VGR 300 s feasibility first

The current frozen candidate is **TNQC V4 (Transport-Nuisance Quotient Canonicalization)** with a **partition-measure-weighted final-active-leaf quotient-channel concordance gate**.

V4 method code checkpoint: `725dae6de2f58b766bc309fd40a9c5722429fb8a`.
Read `docs/TNQC_V4_PARTITION_MEASURE_GATE_20260921.md` first, then
`docs/TNQC_V3_FINAL_LEAF_FREEZE_20260921.md` for the quotient theorem and claim boundary.

## Important correction

Do **not** treat the Orebro 2/5/10-minute source-identity probe as the project feasibility result. It is external measured-data falsification only.

The primary gate is the user's VGR/GADEN House benchmark:
- House01 / House02 / House03;
- seeds 0 / 1;
- full 300 simulation seconds;
- primary endpoint: PMFS `ExpectedValue(sourceProbability, 0.05)` terminal localization error.

Read first:
1. `docs/TNQC_V4_PARTITION_MEASURE_GATE_20260921.md` — authoritative gate: terminal active leaves weighted by represented free-cell measure.
2. `docs/TNQC_V3_FINAL_LEAF_FREEZE_20260921.md` — quotient theorem, exact online variable, claim boundary, and C++ endpoint audit.
3. `docs/VGR_300S_PRIMARY_GATE_20260920.md` — authoritative evaluation contract and gate order.
4. `docs/TNQC_RANKING_SAFETY_CORRECTION_20260921.md` — historical ranking-safety correction; V4 preserves its non-reversal guarantee while correcting hypothesis measure.
5. `docs/TNQC_CODEX_HANDOFF_20260920.md` — older full handoff; V4/V3 corrections above are authoritative wherever wording differs.
6. `docs/TNQC_OFFLINE_GATE_20260920.md` — VGR 0.3-m concentration-space mechanism screen and falsification history; auxiliary only.
7. `evidence/TNQC_VGR_240S_SPATIAL_MECHANISM_20260921.json` — corrected concentration-space mechanism record.
8. `docs/CANDIDATE_SYMMETRY_QUOTIENT_20260920.md` — research lineage and rejected predecessor branches.
9. `evidence/TNQC_IMPLEMENTATION_SANITY_20260921.json` — pre-V4 sanity record; current synthetic/CI checks plus V4 gate are authoritative.
10. `docs/TNQC_LOCALITY_AUDIT_AND_DISTRIBUTED_SUPPORT_20260921.md` — supplemental concentration-space locality audit; distributed-support is not enabled in V4.
11. `evidence/TNQC_VGR_DISTRIBUTED_SUPPORT_AUDIT_20260921.json` — auxiliary disjoint-support/far-field evidence.

## Execution order

1. Pull current `main`, build, and run `test_tnqc_score`.
2. Reproduce `reference/tnqc_vgr_offline_240s.py` only as an auxiliary concentration-space mechanism check. Do not use it as proof of the online hit-logit score.
3. Run `reference/run_tnqc_vgr_offline_gate_20260920.sh` on the VM House datasets. This is the authoritative full-300 s fixed-trajectory gate for the online representation.
4. Require, for all six cases: native posterior reconstruction PASS, native C++ `ExpectedValue(...,0.05)` endpoint anchor PASS, and `candidate_gate_scope=final_partition_leaf_candidates_free_cell_measure_weighted`. Then inspect `tnqc_vgr_300s_offline_gate.json`.
5. Only when `go_for_closed_loop=true`, run OFF vs SHADOW and require exact determinism.
6. Only after that may planner-coupled `fused` closed-loop testing begin.

Authoritative VGR roots used by the frozen runner:
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House01`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House02`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House03`

External launch prerequisite for the later SHADOW/FUSED closed-loop arms:
`/dev/shm/meaci_online_20260824/launch/vgr_gsl_pmfs_pfdi.launch.py`
must declare and forward `tnqc_mode` to the PMFS node. **Do not block the
300-s offline gate on this:** that gate runs `TNQC_MODE=off` online and
applies TNQC only in the read-only replay. If the offline gate returns GO and
the launch argument is absent, change launch plumbing only before the
OFF/SHADOW determinism run.

Do not tune TNQC after viewing House truth.

## Ranking-safety correction

The earlier per-candidate sign guard was insufficient: averaging two channels can preserve each candidate's sign while still reversing the ordering between candidates. It has been rejected.

The current secondary mechanism computes one source-blind concordance over terminal leaves using pair measure `m_i*m_j`, where `m_i` is the number of free source cells represented by leaf `i`. Then `g=max(0,C_cell)` and `e_i=g*q_aff_i`. The measure-weighted leaf statistic is exactly equal to ordinary concordance on the cell-expanded hypothesis bank. Because the same `g>=0` multiplies every candidate, local order may attenuate/abstain but cannot reverse affine candidate ordering.

Within each source update the quadtree is generated and refined **only with
native PMFS scores**. After refinement, V4 computes the TNQC gate only over
the **terminal active free leaves** and weights each leaf by its represented
free-cell count. Subdivided ancestors remain search history and cannot change
the gate. The 300-s replay reconstructs the same terminal hypothesis measure.

The archived 240-s cross-transport screen remains concentration-space
mechanism evidence only. It motivated the quotient/order hierarchy but does
not directly validate the V4 online hit-logit partition-measure gate.

Current scientifically valid status:

**CONCENTRATION-SPACE MECHANISM POSITIVE / V4 PARTITION-MEASURE FINAL-LEAF GATE FROZEN / ONLINE HIT-LOGIT VGR-300S PRIMARY GATE PENDING / CLOSED-LOOP HOLD.**

The next command is therefore the 300-s **offline VGR localization gate**, not
the closed-loop matrix:

```bash
bash reference/run_tnqc_vgr_offline_gate_20260920.sh
```

Do not change the TNQC equation based on House truth. If this returns HOLD,
stop and report the six paired errors; do not tune. If it returns GO, proceed
to OFF/SHADOW determinism and then the frozen closed-loop matrix.
