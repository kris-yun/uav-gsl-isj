# HCMC V1 fixed power-order ablation — 2026-09-22

Frozen data and endpoint are identical to `OFFLINE_SCREEN_20260922.md`.

No order was selected by truth. This audit asks whether the pre-frozen (p=1,2,3,4) multiscaling result is carried by one special moment order.

| powers | mean endpoint error (m) | improved cases |
|---|---:|---:|
| 1,2,3,4 (frozen V1) | 2.4488 | 6/6 |
| 2 only | 2.6647 | 6/6 |
| leave p=4 out: 1,2,3 | 2.6880 | 6/6 |
| leave p=3 out: 1,2,4 | 2.4861 | 6/6 |
| leave p=2 out: 1,3,4 | 2.3788 | 6/6 |
| leave p=1 out: 2,3,4 | 2.3534 | 6/6 |

Single-order diagnostics, not candidates for post-hoc promotion:

- p=1 only: 3.3917 m, 5/6 improved
- p=3 only: 2.3544 m, 6/6 improved
- p=4 only: 2.6285 m, 6/6 improved

Interpretation:

- the signal is not uniquely dependent on second-order structure functions;
- no single high-order moment is required for the six-case gain;
- the fixed p=1..4 family remains the V1 method because choosing p=3 after seeing these cases would be post-hoc tuning;
- independent validation must keep the p=1..4 family frozen.
