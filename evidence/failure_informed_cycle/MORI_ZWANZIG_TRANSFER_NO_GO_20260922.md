# Mori–Zwanzig fallback screen — NO-GO

Date: 2026-09-22
Status: **NO-GO AS MAIN LINE**

## Mother idea

Mori–Zwanzig projection theory from statistical physics describes how unresolved degrees of freedom re-enter reduced dynamics as memory plus orthogonal fluctuation/noise.

Recent cross-domain anchors found with scite:
- *Data-driven Mori–Zwanzig modeling of Lagrangian particle dynamics in turbulent flows*, PNAS 2026, DOI 10.1073/pnas.2525390123.
- *Learning turbulent transport via Mori--Zwanzig graph neural networks*, 2026, DOI 10.48550/arxiv.2606.14918.

The latter explicitly models turbulent tracer acceleration by finite-memory terms and connects memory to generalized fluctuation-dissipation structure.

## GSL transfer tested

For every source candidate:
1. sample its simulated hit-probability field along the actual robot trajectory;
2. use measured gas history, wind and the candidate channel to form a reduced predictor;
3. score the candidate either by held-out predictive loss with finite candidate memory or by how strongly the candidate whitens the residual non-Markovian memory.

This uses the full trajectory and one source-conditioned candidate bank, so it is compatible with the six new runs that contain only source_update_0001.

## Old + new 12-case screen

The best residual-whitening family gave only modest development performance. A representative L=10 result:

- all-12 mean: **4.8315 m**
- pooled reduction: **16.47%**
- non-worse: **10/12**

The finite-memory predictor family was inconsistent:
- old six frequently weak or near zero;
- new six often positive;
- no stable memory horizon dominated both domains.

## Destructive controls

For the representative residual-memory score:

- real mean: **4.8315 m**
- final-leaf permutation null mean: **4.4435 m**
- **82%** of leaf-permutation nulls were as good as/better than the real method.

Temporal-shift controls did not degrade the method reliably:
- shift 50 samples: **4.6874 m**, better than real;
- shift 600 samples: **4.6836 m**, better than real.

Randomly shuffled candidate time series could also match or improve the real score in several repetitions.

Geometry-only score:
- mean **5.4271 m**
- gain only **6.17%**, so pure geometry is not the whole explanation, but the memory mechanism itself is not load-bearing.

## Decision

The cross-domain mother theory is scientifically strong, but this particular source-inference transfer is **not supported by the data**.

The screen fails the failure-informed standard:
- real candidate score does not beat destructive nulls;
- temporal alignment is not load-bearing;
- memory horizon is unstable.

Decision:

`MORI_ZWANZIG_GSL_TRANSFER_NO_GO_20260922`

Do not tune another memory kernel on these same 12 cases.
