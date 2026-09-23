# C0-B Historical 2×2 Intervention Pre-Screen — Additive Composition Rejected

Date: 2026-09-23  
Branch: \`research/causal-compositional-plume-world-model-v1\`

## Decision

\`SIMPLE ADDITIVE SOURCE+WIND COMPOSITION = NO-GO\`

\`M4 CAUSAL COMPOSITIONAL WORLD MODEL = NOT KILLED\`

The negative result changes the architecture: the physical mechanisms should compose as **operators**, not as additive field effects.

## 1. Historical controlled asset quality

Data:
- branch \`project/research-master-20260914\`;
- 12 histories;
- H01/H02/H03 × SA/SB × fast/slow;
- 1200 samples to 240 s;
- identical geometry-only measurement route within each House.

Source coordinates:

- H01: SA=(-0.6,1.95), SB=(-0.4,-2.9);
- H02: SA=(0.0,-1.0), SB=(1.0,-2.3);
- H03: SA=(-0.45,1.9), SB=(8.2,5.0).

### Exact intervention checks

For every House:

- all four pose sequences are exactly identical;
- all four time sequences are exactly identical;
- SA_fast and SB_fast wind sequences are exactly identical;
- SA_slow and SB_slow wind sequences are exactly identical.

Thus source changes do not change the recorded transport field.

### Fast vs slow are not merely one scalar gain

Across the 1200 path samples:

| House | mean fast speed | mean slow speed | best scalar fast≈a·slow | relative RMSE after scalar fit |
|---|---:|---:|---:|---:|
| H01 | 0.1693 | 0.0692 | 2.291 | 0.483 |
| H02 | 0.1290 | 0.0536 | 2.205 | 0.444 |
| H03 | 0.4265 | 0.1641 | 2.520 | 0.229 |

Fast/slow vector directions also differ locally and can be oppositely directed at some route locations.

Therefore this historical asset genuinely changes transport along the same route; it is not merely a gas-amplitude post-processing stress.

## 2. Zero-training 2×2 recombination test

For each House and each held-out target \((S,W)\), use the other source \(S'\) and other wind \(W'\).

Test the additive composition identity:

\[
\hat f(S,W)
=
f(S,W')
+
[
f(S',W)-f(S',W')
].
\]

This asks whether a wind effect learned under one source transfers additively to the other source.

Run on PMFS-grid-binned fields at:
- 60 s;
- 120 s;
- 180 s;
- 240 s.

Two fixed representations:
- raw gas concentration;
- \(\log(1+c)\).

No fitted parameter is used.

Baselines:
1. same source / opposite wind:
   \[
   f(S,W')
   \]
2. other source / same wind:
   \[
   f(S',W)
   \]

## 3. Result

At every time horizon and for both raw and log1p representations:

- additive recombination beats the same-source/opposite-wind baseline in **0/12** held-out combinations;
- it therefore beats both baselines in **0/12**.

At 240 s:

### Raw field
- H01 mean ratio to best baseline: ~18.34;
- H02: ~377.71;
- H03: ~1.48.

### log1p field
- H01: ~16.46;
- H02: ~52.14;
- H03: ~1.52.

Some ratios become extreme because the same-source field can be nearly invariant between the two transport conditions while the transferred other-source transport difference is large.

## 4. Interpretation

This rejects the naive mechanistic form:

\[
C_{S,W}
\approx
A_S+B_W.
\]

It also warns against a shallow “source latent + wind latent” story if the decoder is not explicitly capable of nonlinear physical interaction.

This does **not** reject causal modularity.

Advection-diffusion physics itself is compositional in a different sense:

\[
Q_S
\xrightarrow{\;\mathcal T_{W,O}\;}
C.
\]

The source mechanism produces an injection field \(Q_S\).

The wind/geometry mechanism defines a transport operator \(\mathcal T_{W,O}\).

The concentration field is produced by applying the environment-dependent transport operator to the source mechanism:

\[
\boxed{
C_{S,W,O}
=
\mathcal T_{W,O}(Q_S).
}
\]

This is functional/operator composition, not additive effect decomposition.

## 5. Architecture correction for M4

Replace the provisional generic factorization

\[
z_E=E_{\rm env}(O,W),
\quad
z_S=E_{\rm source}(S),
\quad
C=D(z_E,z_S)
\]

as the scientific core with the stronger physical SCM:

### Mechanism 1 — source injection

\[
Q_S=f_Q(do(S=s)).
\]

### Mechanism 2 — environment transport operator

\[
\mathcal T_{W,O}
=
f_T(do(W=w),O).
\]

### Mechanism 3 — observation

\[
Y=f_Y(C,X_{\rm robot},M_{\rm sensor}).
\]

Then

\[
\boxed{
C=\mathcal T_{W,O}(Q_S).
}
\]

A neural implementation may still use latent representations, but the module interface must preserve this causal/physical order.

## 6. Revised C0 learned comparison

The held-out S2-W2 experiment should now compare:

### Monolithic model
\[
F_{\rm mono}(S,W,O)\to C.
\]

### Operator-compositional model
\[
Q_S=f_Q(S),
\qquad
C=\mathcal T_{W,O}(Q_S).
\]

Matched parameter budget.

The second model only earns the M4 claim if:
- source injection module is reusable;
- transport operator is reusable;
- unseen \(S\times W\) recombination improves over monolithic matched-capacity control;
- downstream truth-source rank improves.

## 7. Important positive fact retained

The historical TNQC mechanism screen already showed that at 240 s, source identity can be recovered cross-transport in all 12 query/template cases using raw field matching.

Thus:
- source identity is not completely destroyed by changing transport;
- but raw plume fields do not obey a simple additive source/wind decomposition.

This is exactly the regime where a nonlinear compositional transport operator may be scientifically meaningful.

## 8. Current M4 status

\`KEEP, BUT ARCHITECTURE NARROWED\`

Rejected:
- additive field decomposition;
- shallow “source effect + wind effect” interpretation.

Retained main hypothesis:
- **causal operator composition: source injection → wind/geometry transport → observation.**

Next hard gate:
- learned matched-capacity monolithic vs operator-compositional held-out source×wind recombination.
