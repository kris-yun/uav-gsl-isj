# Codex start here — TNQC VGR 300 s feasibility first

The current frozen candidate is **TNQC (Transport-Nuisance Quotient Canonicalization)** with the **candidate-bank quotient-channel concordance gate**.

## Important correction

Do **not** treat the Orebro 2/5/10-minute source-identity probe as the project feasibility result. It is external measured-data falsification only.

The primary gate is the user's VGR/GADEN House benchmark:
- House01 / House02 / House03;
- seeds 0 / 1;
- full 300 simulation seconds;
- primary endpoint: PMFS `ExpectedValue(sourceProbability, 0.05)` terminal localization error.

Read first:
1. `docs/VGR_300S_PRIMARY_GATE_20260920.md` — authoritative evaluation contract and gate order.
2. `docs/TNQC_RANKING_SAFETY_CORRECTION_20260921.md` — read this before any run; it rejects the old per-candidate sign guard and freezes the bank-level ranking-safe equation.
3. `docs/TNQC_CODEX_HANDOFF_20260920.md` — current equation, theory, literature lineage, novelty boundary, implementation map.
4. `docs/TNQC_OFFLINE_GATE_20260920.md` — VGR 0.3-m spatial mechanism screen and falsification history.
5. `evidence/TNQC_VGR_240S_SPATIAL_MECHANISM_20260921.json` — corrected project-data mechanism record.
6. `docs/CANDIDATE_SYMMETRY_QUOTIENT_20260920.md` — research lineage and rejected predecessor branches.
7. `evidence/TNQC_IMPLEMENTATION_SANITY_20260921.json` — current source SHAs, standalone C++/Python sanity results, online native-bank contract audit.
8. `docs/TNQC_LOCALITY_AUDIT_AND_DISTRIBUTED_SUPPORT_20260921.md` — supplemental VGR audit addressing the “local patch only” critique; it does not alter the frozen 300-s gate.
9. `evidence/TNQC_VGR_DISTRIBUTED_SUPPORT_AUDIT_20260921.json` — disjoint-support, far-field, and source-blind nuisance stress results.

## Execution order

1. Pull current `main`, build, and run `test_tnqc_score`.
2. Reproduce `reference/tnqc_vgr_offline_240s.py`; it must match the corrected VGR spatial mechanism evidence. The old per-candidate sign guard is rejected and must not be restored.
3. Run `reference/run_tnqc_vgr_offline_gate_20260920.sh` on the VM House datasets. This is the authoritative full-300 s fixed-trajectory gate.
4. Require all native-reconstruction audits to pass and inspect `tnqc_vgr_300s_offline_gate.json`.
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

Within each source update the quadtree candidate bank is now generated and
refined **only with native PMFS scores**. TNQC is applied after the complete
native bank is frozen. This is intentional: the online implementation and the
300-s fixed-trajectory replay now operate on the same candidate-bank contract,
and TNQC cannot select the evidence bank it is scored on.

On the archived VGR 240-s cross-transport screen this gate releases 11/12 cases and is 11/11 correct; under all 100 positive-scale and 200 monotone-compression stress seeds, coverage remains 11/12 and conditional accuracy remains 100%. This is mechanism evidence only; the 300-s localization gate is still authoritative.

Current scientifically valid status:

**VGR MECHANISM POSITIVE / RANKING-SAFETY FIXED / VGR-300S PRIMARY GATE PENDING / CLOSED-LOOP HOLD.**

The next command is therefore the 300-s **offline VGR localization gate**, not
the closed-loop matrix:

```bash
bash reference/run_tnqc_vgr_offline_gate_20260920.sh
```

Do not change the TNQC equation based on House truth. If this returns HOLD,
stop and report the six paired errors; do not tune. If it returns GO, proceed
to OFF/SHADOW determinism and then the frozen closed-loop matrix.
