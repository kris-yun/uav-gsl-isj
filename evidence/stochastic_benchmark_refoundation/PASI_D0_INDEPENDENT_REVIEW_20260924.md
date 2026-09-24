# PASI D0 Independent Review and Meta-Diagnosis — 2026-09-24

Reviewed branch:
`research/path-action-source-inference-v0`

Reviewed result commit:
`d43db8ff581b7e855c953fea972fa28e00fd5bf3`

Frozen scientific decision remains:

`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`

This document does **not** rescue PASI. It diagnoses why several recent candidate mainlines have shown promising discovery-set signals and then failed immediately on fresh stochastic plume realizations.

## 1. Package integrity

Reviewed archives:

### PASI D0 S3 package
- bytes: 142,204
- SHA256:
  `36283a86ca5ca61e0782e5a84b45a0c77f02e998d743bfb20b7570214a84931b`

### Gate1A prediction package
- bytes: 1,281,180
- SHA256:
  `9f2c4e93c3833b00dd82d3f53a21e2286f23afdf3e5087328fc094cada1ba2be`

Both archives' internal `SHA256SUMS.txt` manifests independently verify.

## 2. Independent recomputation

Using the original 630-source C/D prediction bank, frozen probe operator, and the two new S3 target cubes, the four scores were independently recomputed.

Truth:
- `pmfs_3_12`
- `(-4.342730045, -3.700880051, 0.20)`

Exact reproduced ranks:

| target | raw | homoscedastic | heteroscedastic residual | path action |
|---|---:|---:|---:|---:|
| S3_W2_E | 4 | 3 | 3 | 3 |
| S3_W2_F | 13 | 14 | 13 | 13 |

Rank sums:
- raw: 17
- homoscedastic: 17
- heteroscedastic residual: 16
- path action: 16

Therefore the frozen decision is correctly:
`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`.

## 3. Crucial diagnostic: the S3 stochastic regime estimate was wrong

S3 was selected before fresh targets because prediction C/D appeared to show a typical realization-variability regime.

For S3 prediction C/D:
- cosine similarity: ~0.99353
- relative L2 discrepancy: ~0.15391

But fresh same-source targets E/F show:
- cosine similarity: ~0.92831
- relative L2 discrepancy: ~0.53436

Thus the fresh same-source realization difference is more than 3 times the C/D estimate.

The source was not actually demonstrated to be a stable “median stochasticity regime”; one randomly sampled pair C/D merely looked median.

No wind/config drift was found: C/D/E/F share House02, W2, the same GADEN binary, occupancy, extractor and source location.

## 4. Four-realization S3 audit

S3 now has four realizations for diagnosis:
- C = 2026092401
- D = 2026092402
- E = 2026092403
- F = 2026092404

Pairwise relative path discrepancies:
- C-D: ~0.154
- C-E: ~0.264
- C-F: ~0.323
- D-E: ~0.143
- D-F: ~0.422
- E-F: ~0.534

F also shows substantially earlier and larger plume mass than C/D/E.

## 5. Two realizations are insufficient for stochastic-distribution claims

PASI used

[
v^{local}_{s,k}=\frac{(x^C_{s,k}-x^D_{s,k})^2}{2}
]

as candidate-specific stochastic variance.

With two samples, a sample variance has only one degree of freedom.

Even under Gaussian assumptions, the variance-estimator coefficient of variation at n=2 is approximately

[
\sqrt{2/(n-1)}=\sqrt{2}\approx141\%.
]

The plume is additionally sparse and intermittent, so two draws cannot support strong claims about source-conditioned path distributions.

The 630×C/D bank remains excellent deterministic-transfer infrastructure, but is statistically inadequate for estimating per-source stochastic variance, covariance, heavy-tail structure or path action.

## 6. Why recent routes repeatedly looked good before fresh validation

The emerging common pattern is:

- Bi-Green: exact deterministic physics identifies a local source basin but fresh plume realization reorders nearby exact cells.
- MZ: S2-based invariance looked strong, but fresh S1 showed that global nuisance removal deleted useful information.
- PASI: S1/S2 plus the same two-seed C/D bank suggested source-conditioned variance; fresh S3 showed that the source stochastic regime itself was badly estimated.

The project has therefore been adaptively interpreting under-sampled realization structure as mechanism.

## 7. Exact-cell rank is also exposing an identifiability-scale issue

PASI errors remain spatially local.

For E:
- best path-action candidate is 0.30 m from truth;
- truth rank 3.

For F:
- best path-action candidate is ~0.67 m from truth;
- truth rank 13;
- many high-ranked candidates remain in the local basin.

The frozen PASI FAIL remains valid. Do not change its gate after the result.

For future candidates, pre-register and report separately:
1. exact-cell truth rank;
2. MAP spatial error;
3. top-k spatial radius / basin concentration;
4. proper probabilistic score when a probability map exists.

## 8. Scientific conclusion

The current bottleneck is one level below mother-theory selection:

> the project does not yet have a statistically adequate offline benchmark for testing methods whose claimed mechanism depends on stochastic plume distributions.

Before choosing the next main innovation, the stochastic evaluation foundation must be repaired.

## 9. Frozen action

PASI remains stopped.

Do not rescue PASI by:
- adding seeds and reinterpreting the same D0;
- changing variance floor;
- fitting richer covariance after seeing S3;
- changing thresholds.

Additional realizations are authorized only as a **new benchmark-characterization study**, not a PASI rescue.
