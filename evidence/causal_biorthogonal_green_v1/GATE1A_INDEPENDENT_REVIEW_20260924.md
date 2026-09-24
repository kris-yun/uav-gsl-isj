# Gate 1A Independent Review — 2026-09-24

Branch: `research/causal-biorthogonal-green-v1`  
Reviewed result commit: `a38708d51a62fc2ce932d0bf8df4bf08e5f231ef`  
Frozen decision: **GATE1A_FAIL_STOP_SOURCE_TO_SENSOR_GREEN_FAMILY**

## Package integrity

Reviewed archive:
`BIGREEN_GATE1A_REVIEW_20260924.tar.gz`

Archive SHA-256 independently verified:

`9f2c4e93c3833b00dd82d3f53a21e2286f23afdf3e5087328fc094cada1ba2be`

All files listed in the package's `SHA256SUMS.txt` independently passed `sha256sum -c`.

Prediction inventory independently verified:

- seed 2026092401: 630 `.npy` + 630 provenance `.json`;
- seed 2026092402: 630 `.npy` + 630 provenance `.json`.

Target hashes independently verified:

- S2_W2_A concentration:
  `8faea48d5cf2505024d51250f944fcd731452fb94c758d88d8391ab1b410aa76`
- S2_W2_B concentration:
  `7ee1015bf1f307a4cadb9ed3929051f99bf0ad41f91f0321088e2884af6e18f1`

## Wind-contract audit

Both target manifests state:

- House02;
- `wind_id = W2`;
- `3,5-1_slow`;
- same frozen occupancy hash;
- same frozen GADEN binary hash.

The run evidence records W2 wind-iteration 1..10 SHA-256 values. Historical HCMC W1 (`3,5-1_fast`) traces are excluded from scoring; only their geometry-only PMFS candidate manifest is reused.

Therefore no W1/W2 scoring mismatch was found.

## Independent rank recomputation

The result CSV/JSON ranks were not trusted. Rankings were recomputed directly from:

- the two raw target concentration cubes;
- the frozen 2x2 average-pool probe operator;
- all 630 source vectors for prediction seed 2026092401;
- all 630 source vectors for prediction seed 2026092402;
- the frozen raw-ppm normalized SSE.

Independent ranks exactly reproduce the committed result:

| Target | mean(C,D) truth rank | C rank | D rank | Gate |
|---|---:|---:|---:|---|
| S2_W2_A | 1 | 2 | 1 | PASS |
| S2_W2_B | 7 | 7 | 4 | FAIL |

Thus the frozen overall decision is confirmed:

`GATE1A_FAIL_STOP_SOURCE_TO_SENSOR_GREEN_FAMILY`

## Failure structure

This is not a global source-region collapse.

For S2_W2_B:

- rank 1 is `pmfs_2_34`, only 0.30 m from truth;
- rank 3 is `pmfs_3_33`, only 0.30 m from truth;
- ranks 1..8 remain within roughly 0.30–0.67 m of the true support except the truth itself at rank 7;
- target A/B pooled observation vectors still have cosine similarity about 0.9774;
- however their realization-to-realization relative L2 difference is about 0.2118;
- true-source mean prediction has cosine about 0.9983 with target A but only about 0.9786 with target B.

Interpretation: exact frozen physics contains a strong **local source-basin signal**, but the frozen deterministic candidate-ranking contract is not robust enough to independent stochastic plume realization at 0.30 m source-cell resolution.

This distinction is scientifically useful but does not rescue the frozen Gate 1A criterion.

## Infrastructure patch audit

### `661ddf2`
Corrects only the PMFS quadtree manifest center-support-cell consistency check for even-sized leaves. It does not alter support expansion, source locations, wind, targets, seeds, probes, score, or thresholds. No prediction had been produced before the repair.

**Audit: acceptable infrastructure-only repair.**

### `c1ab107`
Restores the same frozen occupancy symlink after GADEN clears its output directory and before the frozen extractor runs. It does not alter occupancy contents or scientific parameters. No compact prediction/rank had been produced before the repair.

**Audit: acceptable infrastructure-only repair.**

### `a38708d`
Excludes `SHA256SUMS.txt` from hashing itself. Packaging-only change after the scientific evidence commit.

**Audit: acceptable packaging-only repair.**

No result-driven scientific-contract modification was found.

## Frozen action

Do **not** proceed to Gate 1B adjoint/Bi-Green compression.
Do **not** rescue this family by changing score, probe set, prediction seeds, rank threshold, source resolution, or target realization.

Retain the generated 630-source exact-forward bank as reusable infrastructure for future main-innovation candidates.

The main scientific lesson to carry forward is:

> Under the current stochastic GADEN plume model, deterministic source-to-sensor transfer identifies a local source basin but does not provide realization-robust exact-cell identifiability at 0.30 m resolution.

That lesson should constrain the next main-innovation search: a future mother theory must explicitly handle realization-level stochasticity / uncertainty rather than only improving deterministic transport representation.
