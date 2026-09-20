# Codex start here — TNQC VGR 300 s feasibility first

The current frozen candidate is **TNQC (Transport-Nuisance Quotient Canonicalization)** with the VGR-tested **symmetry-hierarchy consistency guard**.

## Important correction

Do **not** treat the Orebro 2/5/10-minute source-identity probe as the project feasibility result. It is external measured-data falsification only.

The primary gate is the user's VGR/GADEN House benchmark:
- House01 / House02 / House03;
- seeds 0 / 1;
- full 300 simulation seconds;
- primary endpoint: PMFS `ExpectedValue(sourceProbability, 0.05)` terminal localization error.

Read first:
1. `docs/VGR_300S_PRIMARY_GATE_20260920.md` — authoritative evaluation contract and gate order.
2. `docs/TNQC_CODEX_HANDOFF_20260920.md` — current guarded equation, theory, literature lineage, novelty boundary, implementation map.
3. `docs/TNQC_OFFLINE_GATE_20260920.md` — VGR 0.3-m spatial mechanism screen and falsification of unconditional fusion.
4. `evidence/TNQC_VGR_240S_SPATIAL_MECHANISM_20260920.json` — frozen project-data mechanism record.
5. `docs/CANDIDATE_SYMMETRY_QUOTIENT_20260920.md` — research lineage and rejected predecessor branches.

## Execution order

1. Pull current `main`, build, and run `test_tnqc_score`.
2. Reproduce `reference/tnqc_vgr_offline_240s.py`; it must match the frozen VGR spatial mechanism evidence. Do not retune.
3. Run `reference/run_tnqc_vgr_offline_gate_20260920.sh` on the VM House datasets. This is the authoritative full-300 s fixed-trajectory gate.
4. Require all native-reconstruction audits to pass and inspect `tnqc_vgr_300s_offline_gate.json`.
5. Only when `go_for_closed_loop=true`, run OFF vs SHADOW and require exact determinism.
6. Only after that may planner-coupled `fused` closed-loop testing begin.

Authoritative VGR roots used by the frozen runner:
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House01`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House02`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House03`

External launch prerequisite:
`/dev/shm/meaci_online_20260824/launch/vgr_gsl_pmfs_pfdi.launch.py`
must declare and forward `tnqc_mode` to the PMFS node. If absent, change launch plumbing only.

Do not tune TNQC after viewing House truth.

Current scientifically valid status:

**VGR MECHANISM POSITIVE / VGR-300S PRIMARY GATE PENDING / CLOSED-LOOP HOLD.**
