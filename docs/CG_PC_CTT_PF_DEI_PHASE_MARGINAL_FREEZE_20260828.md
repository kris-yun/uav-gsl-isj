# PF-DEI — Physics-Factorized Dynamic Event Inference

Date: 2026-08-28

Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Status: **SCIENCE CONTRACT FROZEN FOR TRUTH-BLIND REPLAY / NO C++ AUTHORIZATION**

## 1. Why this version exists

V6-A established a stronger negative result than V4/V5:

- 30 development OFF runs / 150 contexts were valid;
- removing hard source components did not restore actionability;
- continuous predictive pass remained 0/30;
- transfer-only pass was H01 1/10, H02 0/10, H03 2/10;
- absolute adequacy pass was 0/30.

Therefore the main remaining hypothesis is not Gate strictness. The frequency-only observation model is insufficiently stable across contexts. The next test must preserve ordered plume-event dynamics before any runtime or planner change.

## 2. Paper-level method name

**Physics-Factorized Dynamic Event Inference (PF-DEI)**

Chinese: **物理因子化动态事件推断**

The causal terminology is intentionally narrow. PF-DEI factorizes a global source variable from context-specific transport nuisance variables. It is not a Pearl/Rubin source causal-effect estimator.

## 3. Generative structure

For run-level source `S` and context `c`:

`S` is global and does not change across contexts.

`Z_c` is a context-specific transport nuisance state. In the current finite reference it is represented by the keyed CTT scoring member and, only when timing provenance requires it, a context-specific trace phase.

Observed data are ordered block events:

`Y_c[j,b] in {0,1}`

for physical stop `j` and completed measurement block `b`.

The intended factorization is

`p(Y_1:C | S) = product_c integral p(Y_c | S, Z_c) p(Z_c | context_c) dZ_c`.

The finite reference marginalizes `Z_c` independently inside each context; it never forces one transport-member identity to persist across contexts.

## 4. No frequency collapse in the normative dynamic model

The truth-free CTT V13 record already stores ordered occupancy:

`X[s,m,j,t] in {0,1}`, `t=1..T`.

The PF-DEI source model must not replace `X` by any of the following before scoring:

- mean hit frequency;
- first-hit time alone;
- transition counts alone;
- run length alone;
- slope, autocorrelation, spectrum, or manually weighted feature vector.

Those quantities may be reported as diagnostics or ablations only.

## 5. Timing and phase contract

The dynamic score is valid only after an outcome-independent timing provenance is established.

For every real completed block, materialization must provide:

`block_intervals_steps[j,b] = [a,b]`

in CTT record-step units relative to the context timing anchor. Fractional interval boundaries are allowed; rounding a non-integer cadence ratio is forbidden.

The context must also provide an explicit set:

`phase_indices`.

This set is frozen from CTT builder/runtime semantics, never from HIT/NOTHING outcomes.

- If the CTT trace and source-update context share a known synchronized anchor, `phase_indices` should normally contain one provenance-derived phase.
- If the trace age/anchor is genuinely latent, multiple phases may be included only when that uncertainty is justified before outcomes. PF-DEI then averages over those phases with a uniform prior.
- Maximizing over phase after seeing observations is forbidden.
- If the timing anchor cannot be established, stop with `STOP_PF_DEI_TIMING_ANCHOR_UNRESOLVED`.

## 6. Full-trace block likelihood

For one source `s`, member `m`, stop `j`, phase `phi`, and observed block interval `[a,b]`, define the exposure-weighted occupied mass from the full CTT trace:

`O = integral_[a+phi,b+phi] X[s,m,j,t] dt`

with time expressed in CTT record-step units.

Let `D = b-a` be the block duration in record-step units.

Use the fixed Jeffreys-smoothed block HIT probability:

`p = (O + 1/2) / (D + 1)`.

This is a finite-support regularizer. It is not a House/seed threshold and is not fitted from localization performance.

The ordered context score is

`L_c(s,m,phi) = sum_j sum_b [ y_jb log p_jb + (1-y_jb) log(1-p_jb) ]`.

No empirical feature weight appears.

## 7. Context-specific nuisance marginalization

For scoring members `m=4..7` and frozen timing-derived phases:

`E_c(s) = logmeanexp_(m,phi) L_c(s,m,phi)`.

Thus source identity is shared across contexts, but transport member and allowed phase are marginalized independently inside every context.

Global source posterior from a set of contexts `C` is

`q_C(s) proportional q0(s) exp(sum_c E_c(s))`,

with fixed geometry prior `q0`.

## 8. Leave-one-context-out source transfer

For held-out context `h`, train on all other contexts:

`q_-h(s) proportional q0(s) exp(sum_c!=h E_c(s))`.

Held-out model score:

`A_h = log sum_s q_-h(s) exp(E_h(s))`.

Geometry-prior source mixture:

`B_h = log sum_s q0(s) exp(E_h(s))`.

Transfer gain:

`G_h^transfer = A_h - B_h`.

The transfer contract is:

- no held-out context may have a negative transfer gain beyond numerical zero;
- at least two held-out contexts must have strictly positive transfer gain.

No tuned positive margin is used.

## 9. Source-independent semi-Markov absolute null

A richer dynamic source model must not be compared against the old IID Bernoulli null.

PF-DEI therefore uses a source-independent Jeffreys semi-Markov null over the observed block tapes.

For state `a in {0,1}` and run duration `d`, define a duration-specific end hazard. Initial state and every hazard use independent `Beta(1/2,1/2)` priors.

Training contexts form the posterior. The entire held-out context is scored by the exact Beta posterior-predictive ratio. The final run in each finite tape is treated as right-censored.

The null contains no source candidate, transport member, House, seed, route, localization error, or true-source coordinate.

Absolute gain:

`G_h^abs = A_h - N_h`.

Every held-out context must satisfy `G_h^abs > numerical_zero`.

This prevents PF-DEI from receiving credit merely for describing persistence/intermittency that a source-independent dynamic model already explains.

## 10. Scoring-member leave-one-out

Only after the full four-member PF-DEI predictive contract passes, recompute the entire cross-context contract four times, each time removing one scoring member from `4..7`.

Every 3-of-4 member model must retain the complete predictive contract. Otherwise `PF_DEI_MEMBER_LOO_FAIL`.

This is deliberately stronger than the earlier V5 member check, which allowed some removal-induced abstentions.

## 11. Matched frequency-only ablation

The same dynamic payload must also be reduced back to the old static representation:

`p_static[s,m,j] = mean_t X[s,m,j,t]`

and

`r_static[j] = mean_b Y[j,b]`.

Run the frequency-only cross-context source diagnostic from exactly these raw inputs.

The key mechanistic comparison is therefore matched on:

- source carriers;
- transport members;
- actual physical stops;
- observed blocks;
- context boundaries;
- geometry prior.

The only intended difference is preservation versus destruction of temporal order.

## 12. Truth-blind feasibility verdict

For each of the 30 development OFF runs report:

- core dynamic transfer pass;
- semi-Markov absolute-null pass;
- scoring-member LOO pass;
- final `PF_DEI_PASS`;
- matched frequency-only result.

Frozen verdict:

- `PF_DEI_PASS >= 20/30` and every House has at least one pass:
  `PF_DEI_TRUTHBLIND_ACTIONABLE_FOR_FROZEN_PERFORMANCE_SCREEN`;
- `10..19/30`:
  `PF_DEI_PARTIAL_RECOVERY_NO_CPP`;
- `<10/30`:
  `PF_DEI_CTT_DYNAMIC_FAMILY_INSUFFICIENT_ESCALATE_TO_GADEN_SBI`.

Do not alter the likelihood, phase set, null, member split, or pass rule after seeing these outcomes.

## 13. Performance sequence after truth-blind success

Only if the first verdict occurs:

1. freeze git SHA, materializer SHA, dynamic context hashes, and science-contract hash;
2. then unblind the existing development archive for a clearly labeled **offline performance screen**, not a closed-loop claim;
3. require pooled expected-location error reduction >=10%, >=20/30 improved runs, no House pooled mean degradation >5%, and zero new false-confident collapses;
4. if that screen passes, implement C++/Python parity and then run the frozen 60-arm paired closed-loop development matrix;
5. final paper-level development GO still comes only from the real closed loop.

## 14. Stop rule

If PF-DEI remains below 10/30, do not add post-hoc first-hit, slope, dwell-time, run-count, autocorrelation, spectral, or feature-weight patches.

The next method is **physics-randomized GADEN simulation-based inference**, with explicit source, transport, and sensor/noise latent factors.

## 15. 2026 cross-domain provenance

The conceptual provenance is limited to transferable scientific ideas, not copied equations:

- Nature 2026 OSDR: infer latent dynamics rather than treat a snapshot as a static state;
- Nature Methods 2026 stVCR: separate persistent biological identity from time-varying migration/proliferation dynamics across snapshots;
- Nature Geoscience 2026 GOFLOW: recover hidden transport from contiguous tracer evolution rather than scalar amplitude alone;
- ICLR 2026 WFR-FM: jointly model displacement and mass change in unbalanced dynamics;
- Nature Astronomy 2026 CIGaRS: use a physics-based hierarchical simulator and simulation-based inference to separate intrinsic and extrinsic factors.

These papers motivate the factorization. They do not validate PF-DEI on GSL; validation remains the frozen truth-blind and closed-loop protocol above.
