# CTT CBPE two-module V3 result

## Frozen verdict

`CTT_CBPE_TWO_MODULE_V3_NO_GO`

This verdict is preserved. V3 is not authorized for runtime or closed-loop use.
The result does not negate the frozen M1 causal premise or the synthetic M2
premise; it rejects the specific whole-run fixed-transport persistence model as
a safe incremental temporal correction on measured historical runs.

## Integrity

- Frozen code commit: `77e400b7157d8c851467b084de211abd9dd8c9d0`
- Execution-freeze commit: `67eef18e16e842e166cb09e139b8bd2f0daf9c82`
- Evaluator SHA-256: `7039a4948108a667c04a77053b0b559c308a3bda214aac34356930b5cbe6d479`
- Synthetic selftest: `CTT_CBPE_TWO_MODULE_V3_SELFTEST=PASS`
- V3 summary SHA-256: `850d5ebf21b5277d11caacf451a44f7a5d0d9c8488188c3ac9cd520d7580ba42`
- V3 verdict SHA-256: `3e4616eca6ea6c2531ec25777b4c90ae0f3c25aecb67cec099d115baa77b56ff`
- New GADEN simulations: 0
- Neural training: none
- Historical runs: H01/H02/H03, seeds 0..9, five source updates each
- Truth separation: all 150 method/control posteriors were frozen and externally
  hashed before native PMFS posteriors or truth were opened.

## Predictive-only M2 premise

The premise used 240 strict member-LOO diagnostic folds but only 30 independent
House-by-route clusters for inference.

| Test | Result |
|---|---:|
| Ordered mean normalized true-source rank | 0.144572 |
| Source-label randomization p | 1/257 = 0.003891 |
| Ordered vs block-permuted route clusters | 30 wins, 0 losses, p = 9.31e-10 |
| Coherent vs per-block member switching | 28 wins, 2 losses, p = 4.34e-7 |
| H01 / H02 / H03 normalized rank | 0.139074 / 0.102378 / 0.192263 |

The predictive simulator family therefore contains source-identifiable ordered
block information. This is a premise result, not a localization-performance
claim.

## Historical fixed-trajectory performance

Official error metric: `ExpectedValue(sourceProbability, 0.05)`.

| Tie mode | PMFS mean (m) | FULL mean (m) | Pooled improvement | Improved runs | Catastrophes |
|---|---:|---:|---:|---:|---:|
| ascending | 5.182322 | 2.621127 | 49.4218% | 27/30 | 1 |
| descending | 5.182322 | 2.650470 | 48.8555% | 27/30 | 1 |
| symmetric | 5.182322 | 2.627272 | 49.3032% | 27/30 | 1 |

Ascending per-House results:

| House | PMFS mean (m) | FULL mean (m) | Pooled improvement | Improved runs | Catastrophes |
|---|---:|---:|---:|---:|---:|
| H01 | 5.001303 | 3.108930 | 37.8376% | 9/10 | 1 |
| H02 | 3.222866 | 2.412613 | 25.1407% | 8/10 | 0 |
| H03 | 7.322797 | 2.341837 | 68.0199% | 10/10 | 0 |

The three ascending regressions were H01 seed 3 and H02 seeds 8 and 9. H01
seed 3 was catastrophic: PMFS 2.611708 m versus FULL 4.108767 m.

## Why the hard Gate failed

The following rules failed:

1. `catastrophes_every_tie_mode`: H01 seed 3 remained catastrophic.
2. FULL did not strictly beat `GLOBAL_COUNT` in every primary tie mode.
3. FULL did not strictly beat `INCOHERENT_PER_BLOCK` in every primary tie mode.
4. The 30-run paired exact sign tests against all temporal controls did not
   reach the frozen significance threshold.

For ascending error:

| Comparator | FULL total (m) | Comparator total (m) | FULL wins/losses/ties | Exact one-sided p |
|---|---:|---:|---:|---:|
| M1/global count | 78.6338 | 78.9942 | 15/15/0 | 0.5722 |
| Block-order permutation | 78.6338 | 80.6120 | 14/13/3 | 0.5000 |
| Per-block member switching | 78.6338 | 77.6438 | 12/18/0 | 0.8998 |

Thus the large aggregate improvement cannot be used to claim that the fixed
whole-run transport identity is a stable measured-data temporal contribution.

## Frozen interpretation and one permitted next step

M1 remains the causal physical reachability operator. M2 remains temporal, but
the V3 assumption `one latent transport member is fixed for the whole run` is
too rigid, whereas previously tested independent per-stop member redraw was too
weak. Exactly one final M2-only revision is permitted: a preregistered discrete
state-space model with a transport latent that is persistent but evolves between
physical source-update blocks. Its transition/persistence must be estimated
only from frozen simulation statistics, before localization outcomes, and must
be marginalized exactly. If that final Gate fails, M2 is retired and M1 is
preserved as the sole main mechanism.
