# R2B operational freeze

Source branch: `research/ocb-r2-r2b-dependence-sensitive-score-20260930`.
Source commit: `8281f5d4dccd485c411c2529d430fa51119d2df7`.

Execute `research/ocb_r2/R2B_DEPENDENCE_SENSITIVE_SCORE_PROTOCOL_20260930.md` exactly. The SC-MPDR definition is read as an unvalidated algorithm candidate; no learned module is authorized in this phase.

- Binary `concentration > 0`, 64 existing discovery tensors, exact R0 input hashes.
- K=3, true-source leave-own-target-out. Primary alternative omission equals target replicate index; four synchronized alternative-omission views also exported.
- Primary includes every cross-time component pair with lag 1,2,3, equally weighted: `(9+8+7)*30*30 = 21600` pairs/candidate score. Lag-specific and full-lag scores are descriptive only.
- Exact empirical Q: all K^2 cross-realization pairs, no surrogate draws. The binary identity `p_a+p_b-2*p_a*p_b` is checked against the explicit K^2 construction.
- Use the protocol's squared Variogram Score formula without adding a U-statistic correction or any tunable scale. Higher `VS_Q-VS_RAW` is better. Strict `Delta>0` counts as correct; ties do not count as correct.
- Comparator is the hash-verified frozen R2 `Delta_BM` export, with 53/64 positives; no Energy Score rerun or selection.
- Group summary uses four-target mean, then House/pooled median of source-context group means. Exact sign flip uses all 256 context sign assignments and the inherited `1e-15` comparison tolerance. Discordant target probability is the exact one-sided binomial tail.
- Repeat full scoring and aggregation twice and require byte parity before assigning the final protocol label.

No thresholds, representation, source support, input, lag, or weights may be changed after evaluation. End after evidence and review packaging; confirmation/H03 remain sealed.
