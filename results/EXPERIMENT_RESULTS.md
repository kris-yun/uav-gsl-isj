# House01 Experiment Results (v3 - fix package, n=7-8 seeds)

## Summary

| condition | n | mean_error | paired_diff | better/worse |
|-----------|---|------------|-------------|-------------|
| baseline | 8 | 3.469m | - | - |
| pwc | 8 | 3.514m | +0.044 | 3/5 |
| psde_final | 7 | 5.860m | +2.408 | 0/7 |
| psde_online | 7 | 3.676m | +0.224 | 0/4 |
| psde_both | 7 | 5.515m | +2.062 | 1/6 |
| sdr | 7 | 3.086m | -0.366 | 7/0 |
| full | 7 | 3.066m | -0.387 | 7/0 |

## Key findings
- SDR: only effective module (-10.6%), 7/7 seeds improved
- Full: 7/7 improved (-11.2%), but only 0.02m better than SDR alone
- PSDE_final: severely overshoots (+69%), y-coord at -7 to -10 (source at -2.9)
- PWC: neutral effect
- baseline: 0 gas hits, only 2 discrete positions
