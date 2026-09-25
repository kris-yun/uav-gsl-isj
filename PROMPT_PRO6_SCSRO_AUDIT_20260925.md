# PRO6 NEXT TASK — Correlated Stochastic Response Operator Audit

Date: 2026-09-25

Primary-thread status:
- CESS/FSEI mainline STOP;
- successor/occupation mainline STOP;
- RR-MVSI mainline STOP after corrected proper-score re-evaluation;
- SC-SRO has a reproducible linear correlated-uncertainty signal but is not yet promoted.

Current empirical object:
For heldout source classes, a low-rank plume-residual covariance model with source-conditioned modal amplitudes improves full-168-support true-source proper log score over the identical constant-covariance model in all four source/realization directions:
+0.0209, +0.0635, +0.0852, +0.0564 bit/target, each with fixed-source realization-bootstrap lower bound >0.

Scalar source variance fails. Shared full covariance does not explain the signal.

Candidate mother theory:
- probabilistic neural operators / function-space uncertainty;
- stochastic operator networks;
- stochastic closure / SPDE operator learning;
- correlated functional predictive distributions.

Critical direct prior art:
1. 2026 IROS: A physics-informed neural operator for gas source localization in turbulent environments — neural operator in GSL is occupied.
2. arXiv:2608.16221: Deep Probabilistic Indoor Gas Source Localization via Physical Dependency-Guided Sequential Inference — probabilistic GSL is occupied; its field predictors use heteroscedastic diagonal Gaussians and explicitly discard spatial correlation structure.

Your task:
1. Audit whether any GSL/olfaction paper already learns source-conditioned correlated covariance/function-space uncertainty for localization.
2. Audit 2025/2026 probabilistic/stochastic operator theory, prioritizing peer-reviewed top venues and code.
3. Decide whether the scientific object can be stated as a distribution-valued source response operator rather than ordinary covariance regression.
4. Derive a GSL-specific operator form that maps source + wind + geometry to both mean plume response and a PSD correlated covariance/operator, and maps one online observation back to a PMFS probability map.
5. Explain exactly what is new relative to the 2026 IROS neural-operator GSL paper and arXiv:2608.16221.
6. Red-team the magnitude of the current gain: is +0.02 to +0.085 bit/target enough to justify a main innovation, or only an auxiliary correlated-UQ module?
7. Give a no-new-simulation D1 proposal using the existing D1R bank. Do not propose architecture escalation after failure unless theory requires a different objective, not merely a bigger network.
8. Address sim-to-real: online use must not require repeated releases at every real candidate source.

Deliver:
- SCSRO_THEORY_AND_PRIOR_ART.md
- SCSRO_VS_2026_GSL.md
- SCSRO_D1_RECOMMENDATION.md
- SCSRO_SIM_TO_REAL.md
- one-page GO / AUXILIARY / STOP recommendation.

Do not revive stopped routes.
Do not run new simulations.
Do not call generic neural operators or probabilistic GSL novel.