# Codex start here — TNQC V3 VGR 300 s feasibility first

The current frozen candidate is **TNQC V3 (Transport-Nuisance Quotient Canonicalization)** with a **final-active-leaf quotient-channel concordance gate**.

V3 code/evaluator correction freeze: `3024ff349c37105aee1816f6648db3e81c178202`.
Read `docs/TNQC_V3_FINAL_LEAF_FREEZE_20260921.md` before running anything.

## Important correction

Do **not** treat the Orebro 2/5/10-minute source-identity probe as the project feasibility result. It is external measured-data falsification only.

The primary gate is the user's VGR/GADEN House benchmark:
- House01 / House02 / House03;
- seeds 0 / 1;
- full 300 simulation seconds;
- primary endpoint: PMFS `ExpectedValue(sourceProbability, 0.05)` terminal localization error.

Read first:
1. `docs/TNQC_V3_FINAL_LEAF_FREEZE_20260921.md` — latest correction: exact online variable, quotient theorem/claim boundary, final-leaf gate, C++ endpoint audit, and frozen 300-s V3 protocol.
2. `docs/VGR_300S_PRIMARY_GATE_20260920.md` — authoritative evaluation contract and gate order.
3. `docs/TNQC_RANKING_SAFETY_CORRECTION_20260921.md` — historical ranking-safety correction; V3 further restricts its bank to terminal leaves.
4. `docs/TNQC_CODEX_HANDOFF_20260920.md` — method lineage and execution handoff, subject to the V3 correction above.
5. `docs/TNQC_OFFLINE_GATE_20260920.md` — VGR 0.3-m concentration-space mechanism screen and falsification history; auxiliary only.
6. `evidence/TNQC_VGR_240S_SPATIAL_MECHANISM_20260921.json` — corrected concentration-space mechanism record.
7. `docs/CANDIDATE_SYMMETRY_QUOTIENT_20260920.md` — research lineage and rejected predecessor branches.
8. `evidence/TNQC_IMPLEMENTATION_SANITY_20260921.json` — pre-V3 implementation sanity record; use current CI plus V3 gate for authoritative integrity.
9. `docs/TNQC_LOCALITY_AUDIT_AND_DISTRIBUTED_SUPPORT_20260921.md` — supplemental concentration-space locality audit; distributed-support is not enabled in V3.
10. `evidence/TNQC_VGR_DISTRIBUTED_SUPPORT_AUDIT_20260921.json` — auxiliary disjoint-support/far-field evidence.

## Execution order

1. Pull current `main`, build, and run `test_tnqc_score`.
2. Reproduce `reference/tnqc_vgr_offline_240s.py` only as an auxiliary concentration-space mechanism check. Do not use it as proof of the online hit-logit score.
3. Run `reference/run_tnqc_vgr_offline_gate_20260920.sh` on the VM House datasets. This is the authoritative full-300 s fixed-trajectory gate for the online representation.
4. Require, for all six cases: native posterior reconstruction PASS, native C++ `ExpectedValue(...,0.05)` endpoint anchor PASS, and `candidate_gate_scope=final_partition_leaf_candidates_only`. Then inspect `tnqc_vgr_300s_offline_gate.json`.
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

The current secondary mechanism computes one source-blind candidate-bank concordance
`C = mean sign(q_aff_i-q_aff_j) sign(q_ord_i-q_ord_j)`, then
`g=max(0,C)`, and uses `e_i=g*q_aff_i`. Because the same `g>=0` multiplies every candidate, local order may attenuate/abstain but cannot reverse affine candidate ordering.

Within each source update the quadtree is generated and refined **only with
native PMFS scores**. After refinement, V3 computes the TNQC concordance gate
only over the **terminal active free leaves that form the final posterior
partition**. Subdivided ancestors remain search history and cannot change the
gate. The 300-s replay reconstructs the same terminal hypothesis set.

On the archived VGR 240-s cross-transport screen this gate releases 11/12 cases and is 11/11 correct; under all 100 positive-scale and 200 monotone-compression stress seeds, coverage remains 11/12 and conditional accuracy remains 100%. This is mechanism evidence only; the 300-s localization gate is still authoritative.

Current scientifically valid status:

**CONCENTRATION-SPACE MECHANISM POSITIVE / V3 FINAL-LEAF INTEGRITY FIXED / ONLINE HIT-LOGIT VGR-300S PRIMARY GATE PENDING / CLOSED-LOOP HOLD.**

The next command is therefore the 300-s **offline VGR localization gate**, not
the closed-loop matrix:

```bash
bash reference/run_tnqc_vgr_offline_gate_20260920.sh
```

Do not change the TNQC equation based on House truth. If this returns HOLD,
stop and report the six paired errors; do not tune. If it returns GO, proceed
to OFF/SHADOW determinism and then the frozen closed-loop matrix.
