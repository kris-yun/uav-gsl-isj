# HCMC V1 fixed scale-family ablation — 2026-09-22

Cell size in the frozen R2 runs is 0.3 m. No scale family below is selected for promotion from this discovery set; the V1 method remains frozen at 1/2/4/8 cells.

| scales (cells) | physical scales (m) | mean endpoint error (m) | improved |
|---|---|---:|---:|
| 1,2,4,8 (V1) | 0.3,0.6,1.2,2.4 | 2.4488 | 6/6 |
| 1,2,4 | 0.3,0.6,1.2 | 3.9869 | 5/6 |
| 2,4,8 | 0.6,1.2,2.4 | 2.7069 | 6/6 |

Single-transition diagnostics only:

- 1→2 cells: 4.8979 m, 4/6 improved
- 2→4 cells: 4.5046 m, 5/6 improved
- 4→8 cells: 3.5162 m, 5/6 improved

Interpretation:

- the effect is genuinely cross-scale; a single transition is insufficient;
- the coarse-scale transition is load-bearing for House03 in this discovery set;
- the complete fixed scale family remains the only V1 method;
- no scale may be removed or reweighted using source truth before independent validation.
