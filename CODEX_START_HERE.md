# Codex start here — TNQC closed-loop screen

The current frozen candidate is **TNQC (Transport-Nuisance Quotient Canonicalization)**.

Read first:
1. `docs/TNQC_CODEX_HANDOFF_20260920.md` — complete theory, equations, verified literature lineage, novelty boundary, implementation map, no-touch list, and execution protocol.
2. `docs/TNQC_OFFLINE_GATE_20260920.md` — frozen offline measured-data evidence and pre-registered advancement gate.
3. `docs/CANDIDATE_SYMMETRY_QUOTIENT_20260920.md` — research lineage and rejected predecessor branches.

Then execute in this order:

```bash
# public-data sanity
python3 reference/tnqc_orebro_offline.py --window-minutes 2
python3 reference/tnqc_orebro_offline.py --window-minutes 5
python3 reference/tnqc_orebro_offline.py --window-minutes 10

# first: OFF vs SHADOW determinism only
TNQC_MODES="off shadow" bash reference/run_tnqc_closed_loop_matrix_20260920.sh

# only after OFF == SHADOW for all 6 House/seed pairs
TNQC_MODES="off shadow fused only" bash reference/run_tnqc_closed_loop_matrix_20260920.sh
```

External VM prerequisite:
`/dev/shm/meaci_online_20260824/launch/vgr_gsl_pmfs_pfdi.launch.py`
must declare and forward `tnqc_mode` to the PMFS node. If absent, change launch plumbing only.

**Do not tune TNQC after viewing House truth.** The first matrix is frozen at 1:1 continuous/local-order fusion, bounded evidence ([-1,1]), `exp(e)` likelihood modifier, `stepsSourceUpdate=3`, and 300 s.

Current scientific status: **OFFLINE POSITIVE / CLOSED-LOOP PENDING.**
