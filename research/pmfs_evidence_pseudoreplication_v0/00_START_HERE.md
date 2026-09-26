# PMFS Evidence Pseudoreplication V0

Development-only mechanism test. No new forward simulation, no GADEN, no network, no closed loop.

Question:

**Does PMFS lose source-location discrimination because each raw sensor observation is spatially propagated into many correlated map cells, after which `sourceProbFromMaps()` multiplies those cells as though they were independent evidence?**

Use the already frozen House01/seed0 R1 **Native C-arm candidate hit maps**. Do not regenerate them.

Read:
1. `01_MECHANISM.md`
2. `02_EXPERIMENT_SPEC.md`
3. `score_frozen_r1_maps.py`
4. `evaluate_after_freeze.py`
5. `03_CODEX_EXECUTE_ONLY.txt`
