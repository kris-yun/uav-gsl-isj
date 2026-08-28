# CG-PC-CTT V6-B — Dynamic Transport Factorization Freeze

Date: 2026-08-28

Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Status: **PYTHON/TRUTH-BLIND DYNAMIC REPLAY ONLY / NO C++ AUTHORIZATION**

## 1. Why V6-B exists

V4 failed because hard source components were rarely invariant across three physical stops.
V5 accumulated ~16 unique stops per run but still produced 0/30 passive ACCEPT runs.
V6-A removed hard components entirely and still produced 0/30 continuous predictive pass.
Therefore hard-component fragmentation is real but is not the primary remaining blocker.

The next falsifiable hypothesis is that the current transport representation destroys the temporal information needed for source transfer because each stop is compressed from an ordered block tape to one hit fraction.

V6-B does **not** loosen any previous gate. It changes the observation model.

## 2. Scientific factorization

The run is modeled as

`global source s -> context-specific transport z_c -> ordered stop observations y_cj1:B`.

Binding distinction:

- source `s` is shared across the run;
- transport state/member `z_c` may change between source-update contexts;
- observed block order is preserved;
- repeated blocks are not pseudo-independent source samples; they form one ordered stop tape.

For context `c`, source `s`, transport member `m`, and physical stop `j`, the truth-free CTT bank supplies an ordered binary occupancy trace

`x[s,m,j,1:T]`, currently `T=200`.

The runtime archive supplies the ordered PMFS completed-block tape

`y[c,j,1:B]`, currently `B=8`.

## 3. Timing contract is mandatory

The simulator trace step and PMFS completed-block cadence are different clocks. V6-B MUST NOT compare one-step CTT transitions directly with one-block PMFS transitions unless the mapping is established from authoritative code/configuration.

Let

`lag_steps = block_cadence / ctt_record_step`.

Normative reference accepts only a verified positive integer `lag_steps`.

If the real timing ratio is not an exact integer, do **not** round it. Instead extend the truth-free trace materializer so that the predicted binary trace is sampled/aggregated at the actual PMFS completed-block cadence before scoring. If neither route can be proven from source/config, output `STOP_DYNAMIC_TIMING_UNRESOLVED`.

No timing parameter may be tuned from localization outcome.

## 4. Ordered dynamic likelihood

For one truth-free CTT occupancy trace, count one-step transitions

`n00, n01, n10, n11`.

Use fixed Jeffreys row smoothing:

`P(1|0) = (n01 + 1/2)/(n00+n01+1)`

`P(1|1) = (n11 + 1/2)/(n10+n11+1)`.

This gives a strictly positive two-state one-step transition matrix `P1`.

Advance it to the verified PMFS block cadence:

`P_block = P1 ^ lag_steps`.

Use the stationary mass of `P_block` for the first block. This deliberately removes arbitrary simulator phase while retaining persistence, entry/exit asymmetry and intermittency.

For observed stop tape `y_1:B`:

`ell(s,m,j) = log pi[y1] + sum_{b=2..B} log P_block[y_{b-1}, y_b]`.

Context member score:

`L_c(s,m) = sum_j ell(s,m,j)`.

Transport is context-specific, therefore source evidence is

`E_c(s) = logmeanexp_{m=4..7} L_c(s,m)`.

This is intentionally **not**

`logmeanexp_m sum_c L_c(s,m)`,

which would force one transport realization to persist across changing contexts.

## 5. Global source accumulation

For context set `C`:

`q(s | C) proportional q0(s) exp(sum_c E_c(s))`.

No hard observation-resolved source components are used in V6-B.

M1's geometric component construction is retained only as historical diagnostic material, not as a source identity constraint.

## 6. Leave-one-context-out source transfer

For held-out context `h`, build

`q_-h(s) proportional q0(s) exp(sum_{c != h} E_c(s))`.

Model predictive score:

`A_h = log sum_s q_-h(s) exp(E_h(s))`.

Geometry-prior source-mixture score:

`B_h = log sum_s q0(s) exp(E_h(s))`.

Cross-context source-transfer gain:

`G_h = A_h - B_h`.

Transfer pass requires:

- no held-out context with negative gain beyond numerical zero;
- at least two held-out contexts with strictly positive gain.

## 7. Dynamic absolute null

The absolute null must match the richer observation model.

Use a source-independent first-order binary Markov model with independent Jeffreys `Beta(1/2,1/2)` priors for:

- initial state probability;
- `P(1|0)`;
- `P(1|1)`.

Only training contexts update this null. Held-out tapes are scored by the exact posterior-predictive Beta-binomial marginal. No source candidate, House, seed, localization error or held-out-fitted parameter enters the null.

Every held-out model score must beat this dynamic source-independent null.

## 8. Mandatory matched static ablation

The same dynamic raw data must also be compressed back to frequency:

`p = mean_t x`, `r = mean_b y`.

Run the old frequency-style source-transfer diagnostic on these matched inputs.

This ablation answers whether any recovery comes from ordered dynamics rather than bank rebuilding or source-grid changes.

Do not compare raw dynamic and static log-score magnitudes because they score different observation units. Compare pass/failure structure.

## 9. Truth-blind actionability verdict

Across H01/H02/H03 seeds 0..9:

- if dynamic predictive pass >=20/30 and every House has at least one pass:
  `V6B_ORDERED_DYNAMICS_ACTIONABLE_FOR_RUNTIME_REFERENCE`;
- if 10..19/30:
  `V6B_PARTIAL_DYNAMIC_RECOVERY_NO_CPP_YET`;
- if <10/30:
  `V6B_CTT_DYNAMIC_FAMILY_INSUFFICIENT_ESCALATE_TO_PHYSICS_FACTORIZED_SBI`.

These are pre-C++ feasibility rules, frozen before V6-B outcomes. They do not replace the final >=10% closed-loop localization endpoint.

## 10. 2026 scientific lineage and boundary

V6-B is inspired by, but does not copy equations from, 2026 big-science work:

1. Somer, Mannor & Alon, **Nature 2026**, `Temporal tissue dynamics from a spatial snapshot`: infer latent dynamics/velocity from local event markers instead of treating a snapshot as a static state.
2. Lenain et al., **Nature Geoscience 2026**, `An unprecedented view of ocean currents from geostationary satellites`: recover hidden velocity from short sequences of transformed scalar fields, emphasizing evolution of tracer structure rather than scalar amplitude alone.
3. Peng, Zhou & Li, **Nature Methods 2026**, `stVCR: spatiotemporal dynamics of single cells`: separate evolving transport/migration dynamics from snapshot identity.
4. Karchev, Trotta & Jimenez, **Nature Astronomy 2026**, `CIGaRS I`: use physics-based hierarchical forward modelling and simulation-based inference to separate intrinsic and extrinsic latent factors.
5. Peng et al., **ICLR 2026**, `WFR-FM`: jointly model displacement and mass/growth dynamics in unbalanced evolving systems.

Scientific boundary: V6-B is a minimal falsification of the ordered-dynamics hypothesis using the existing CTT family. If V6-B fails, do not add more hand-designed tape features. Escalate to V6-C physics-factorized GADEN simulation-based inference.

## 11. V6-C fallback if V6-B fails

The next model is

`source s` (global),

`transport latent z_c` (context-specific),

`sensor/noise latent n_c` (context-specific),

with GADEN as the randomized physics-based forward simulator.

Target inference:

`p(s, z_1:C, n_1:C | y_1:C)`

or a neural likelihood-ratio/posterior equivalent.

The planner remains PMFS unless a later separately frozen experiment proves a transport-aware planning benefit. Active sensing is not claimed as the main innovation.
