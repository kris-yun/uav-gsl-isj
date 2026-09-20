# Codex start here — TNQC VGR 300 s feasibility first

The current frozen candidate is **TNQC (Transport-Nuisance Quotient Canonicalization)**.

## Important correction

Do **not** treat the Orebro 2/5/10-minute source-identity probe as the project feasibility result. It is external measured-data falsification only.

The primary gate is the user's VGR/GADEN House benchmark:
- House01 / House02 / House03;
- seeds 0 / 1;
- full 300 simulation seconds;
- primary endpoint: PMFS `ExpectedValue(sourceProbability, 0.05)` terminal localization error.

Read first:
1. `docs/VGR_300S_PRIMARY_GATE_20260920.md` — authoritative evaluation contract and gate order.
2. `docs/TNQC_CODEX_HANDOFF_20260920.md` — theory, equations, literature lineage, novelty boundary, implementation map.
3. `docs/TNQC_OFFLINE_GATE_20260920.md` — external Orebro falsification only.
4. `docs/CANDIDATE_SYMMETRY_QUOTIENT_20260920.md` — research lineage and rejected predecessor branches.

## Execution order

1. Build and run `test_tnqc_score`.
2. Reproduce Orebro only as a sanity/falsification check; do not use it to accept the method.
3. On the VM House datasets, first run full-300 s native PMFS + `tnqc_mode=shadow`.
4. Verify OFF == SHADOW in trajectory/final native result.
5. Produce a read-only TNQC-rescored posterior on the same native 300 s trajectory and evaluate its final top-5% error.
6. Only if the frozen VGR 300 s gate passes may planner-coupled `fused` closed-loop testing begin.

Authoritative VGR roots used by the frozen runner:
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House01`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House02`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House03`

External launch prerequisite:
`/dev/shm/meaci_online_20260824/launch/vgr_gsl_pmfs_pfdi.launch.py`
must declare and forward `tnqc_mode` to the PMFS node. If absent, change launch plumbing only.

Do not tune TNQC after viewing House truth.

Current scientifically valid status:

**EXTERNAL-PROXY POSITIVE / VGR-300S PRIMARY GATE PENDING / CLOSED-LOOP PENDING.**
