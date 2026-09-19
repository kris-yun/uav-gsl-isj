# Loop 11 — Distributional-Consistency Candidate Falsification

Date: 2026-09-19
Status: INTERNAL SCREENING

Remote-domain anchor:
- ICLR 2026: *Distributional Consistency Loss: Beyond Pointwise Data Terms in Inverse Problems*.

A simple source-conditioned distributional-matching proxy was tested on the existing controlled histories. Slow-wind observation windows were compared with fast-wind candidate windows using Wasserstein-1, quantile distance and empirical CDF distance, against aligned pointwise RMSE.

Across three held-time settings and 5/10/20 s windows, distributional metrics mostly tie the pointwise baseline. The clearest gains are only +1 case in several 20 s conditions; other conditions tie or worsen.

**Decision: NO-GO as current M1.**

The ICLR 2026 idea remains useful if a later stochastic inverse model requires better data fidelity, but the present data do not support it as the paper's main scientific mechanism.

Evidence: `evidence/remote_paradigm_loop_20260919/LOOP11_DISTRIBUTIONAL_CONSISTENCY_PROXY.json`.
