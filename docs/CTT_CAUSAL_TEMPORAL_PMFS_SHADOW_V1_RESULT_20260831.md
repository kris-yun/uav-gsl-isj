# CTT causal-temporal PMFS shadow V1 result

## Frozen verdict

`CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_NO_GO`

This terminal state is preserved.  The fixed-trajectory V1 shows a large
development signal, but it does not authorize runtime or establish
closed-loop effectiveness because two preregistered tie-sensitivity
catastrophe rules failed.

## Primary result

Across H01/H02/H03 seed0--9 (30 fixed historical PMFS-OFF trajectories), the
canonical official endpoint changed from mean error `5.18232164 m` to
`2.55202397 m`:

- pooled relative improvement: `50.7552%`;
- improved pairs: `27/30`;
- median pair improvement: `58.1074%`;
- canonical catastrophes: `0`;
- new false-confident collapses: `0`.

House-level canonical pooled improvements were:

- H01: `22.1365%` (`8/10` improved);
- H02: `48.7910%` (`9/10` improved);
- H03: `71.1656%` (`10/10` improved).

The reverse-cell-order and tie-symmetrized pooled improvements remained large
at `47.7746%` and `49.3926%`, respectively, with `27/30` improved under both.

## Module evidence

All source-label controls passed at the minimum attainable empirical
probability `1/257 = 0.00389105`, including the free-cell-count-stratified
null.  FULL also beat both preregistered temporal controls:

- `COUNT_ONLY`: canonical pooled improvement `48.2698%`;
- `STOP_LABEL_PERMUTE`: canonical pooled improvement `41.8752%`;
- FULL: canonical pooled improvement `50.7552%`.

Thus the source-conditioned causal operator and stop-resolved temporal
matching both carry incremental development information.  This is not yet a
closed-loop claim.

## Why the hard Gate failed

Only two hard-rule markers were false:

- `reverse_catastrophes`;
- `symmetric_catastrophes`.

Both arise from H01 seed3.  Native PMFS had final error `2.6117 m`, native
true-carrier rank `206.5`, and variance `0.1604 m^2`.  CTRE improved the true
carrier to raw rank `45` / posterior rank `46` and remained broad
(`25.6461 m^2`), but uniform carrier-to-cell projection produced errors
`3.6829 m` (canonical), `4.9226 m` (reverse), and `4.3540 m`
(tie-symmetrized).  The last two satisfy the frozen catastrophe definition.

The other canonical regressions were H01 seed0 (`-3.997%`) and H02 seed8
(`-9.146%`).  No post-result threshold, weight, temperature, Gate, or method
formula was changed.

## Evidence hashes

- `SUMMARY.json`:
  `db71e93f1e346406a13ac65abe615e3b3c34de490047a379e4e5d29ccd0ab7b0`
- `FINAL_PAIRS.csv`:
  `41762eaf041a982ea4b87e3a9c9f1ec1c35f3f3cf78710806c135f4f5c622178`
- `UPDATES.csv`:
  `2e265fe1c4435865cb95fe64647e9b57cb6b08ef7be29fe5d6b0e9f70f32fcce`
- `SOURCE_LABEL_NULLS.csv`:
  `9f4256996b944d6c88a3ea48a69250be741a96c343e111ed610e9d0671804de6`
- `VERDICT.txt`:
  `f1b7ba009050e001b1bce9a0d0dbf5b20d86e99754676995350e8160cc4515a0`

Local evidence root:
`D:/ZYC/A-gas/_staging/CTT_CAUSAL_TEMPORAL_PMFS_SHADOW_RUN_20260831_R1`.
