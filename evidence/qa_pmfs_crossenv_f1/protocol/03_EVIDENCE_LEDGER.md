# 3. Evidence ledger

## A. Dependence D0 V2 — retained

Frozen decision: `DEPENDENCE_D0_CROSS_TIME_SIGNAL`.

Do not rerun it and do not reinterpret it as a world-model proof.

## B. QA marginal-preserving OPEN prototype

Exact input: `5016e8a56ff747d153c332d0346a0e4f8beed648757e4136b5e808f9267d6c7f`.

Reference-only model selection:
- candidate block lengths: 1,2,5,10;
- candidate rho: 0.0..0.8 by 0.1;
- Jeffreys smoothing, reference only;
- 40-point Gauss-Hermite likelihood integration.

All four splits select:
`L=10, rho=0.6`.

Primary A+B:
- independent P0 mean rank = 1.125000
- QA mean rank = 1.062500
- P0 Top-1 = 89.93%
- QA Top-1 = 95.49%

Robustness C+D:
- independent P0 mean rank = 1.142361
- QA mean rank = 1.062500
- P0 Top-1 = 89.24%
- QA Top-1 = 94.79%

This is still OPEN/development evidence.

## C. House01 R1 bridge

Exact input: `a20c5d6bd66c37f7039f4059f6a419fa333b0a62936e87177536a2d77435180f`.

`rho=0.6` is transferred from R0; no House01 truth tuning.

| Marginal arm | Independent truth rank | QA truth rank |
|---|---:|---:|
| historical static | 47 | 66 |
| P1 height-only | 49 | 68 |
| C1 multi-state/site-pooled | 31 | 23 |
| P2 event-matched multi-state | 28 | 25 |

C1 true-source posterior under uniform prior:
`1.6217% -> 1.9090%`, NLL `4.1217 -> 3.9586`.

P2:
`1.6344% -> 1.8431%`, NLL `4.1139 -> 3.9937`.

This interaction is the key mechanism evidence:
**joint dependence correction is useful only when the fast-state marginals are
already credible enough.**
