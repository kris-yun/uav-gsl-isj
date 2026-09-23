# O0 Precheck — State-Dependence Warning for Transport Residuals

Date: 2026-09-23  
Branch: \`research/testtime-compositional-plume-operators-v1\`

## 1. Historical route-level precheck

Using the frozen 2×2 controlled histories at:

\`26e89a99532e4268c5022dca2e938bf1473377b1\`

for each House define:

\[
z=\log(1+\mathrm{ppm})
\]

and the transport-intervention response

\[
\Delta_S
=
z(S,\mathrm{slow})
-
z(S,\mathrm{fast}).
\]

Compare \(\Delta_{SA}\) and \(\Delta_{SB}\) along the exact same geometry-only robot route.

### H01

- correlation: -0.0049
- cosine: -0.0081
- \(\|\Delta_{SA}\|=0.568\)
- \(\|\Delta_{SB}\|=0.0157\)

### H02

- correlation: -0.00935
- cosine: 0.00239
- \(\|\Delta_{SA}\|=0.0299\)
- \(\|\Delta_{SB}\|=2.875\)

### H03

- correlation: -0.0851
- cosine: -0.152
- \(\|\Delta_{SA}\|=8.617\)
- \(\|\Delta_{SB}\|=8.089\)

Thus the observed fast→slow signal change is strongly source/state dependent.

## 2. This is NOT evidence that a reusable transport operator is impossible

A physical operator acts on the current plume state:

\[
c_{t+\Delta}
=
\mathcal T_W[c_t].
\]

Even if the same operator \(\mathcal T_W\) is reused for all sources,

\[
\mathcal T_W[c^{SA}]
-
c^{SA}
\]

and

\[
\mathcal T_W[c^{SB}]
-
c^{SB}
\]

need not be similar because \(c^{SA}\neq c^{SB}\).

Therefore the following criterion is invalid:

> reusable operator ⇒ residual vectors from different sources should be equal/correlated.

Do not use that criterion.

## 3. Correct reuse test

The scientifically correct test is:

> fit/calibrate the same mechanism operator using one source and evaluate that **same frozen operator** on a second source.

For analytical O0:

1. calibrate the single global diffusivity / residual hyperparameter panel on source SA transitions only;
2. freeze it;
3. apply identical:
   - source-independent advection implementation;
   - obstacle/boundary handling;
   - diffusion parameter;
   to SB field transitions under the same House/wind;
4. compare against persistence and wrong-wind null.

For learned O1:

1. train a residual mechanism operator on source SA;
2. freeze weights;
3. apply it to source SB;
4. source information is allowed only through the physical input field/source injection, not by selecting source-specific weights.

This is the actual **source-transferability** claim.

## 4. Useful positive signal from the same route-level data

Although transport deltas are state-dependent, the source-difference signature is substantially more stable across fast/slow transport:

### H01
- source-difference fast-vs-slow correlation: 0.817
- cosine: 0.824

### H02
- correlation: 0.988
- cosine: 0.989

### H03
- correlation: 0.762
- cosine: 0.745

This is compatible with the idea that:
- source identity is persistent;
- transport response is state-dependent;
- the forward mechanism should therefore act on the evolving field rather than be represented by an additive source-independent correction vector.

This favors an **operator** representation over static residual templates.

It is motivation only, not validation.

## 5. O0 criterion correction

The O0 decision should prioritize:

### T1 — within-source held-out time transfer
Freeze analytical split parameters on early SA transitions; evaluate later SA transitions.

### T2 — cross-source transfer
Freeze the same parameters from SA; evaluate SB under the same House/wind.

### T3 — cross-realization transfer
Freeze on plume seed 1; evaluate plume seed 2.

### T4 — cross-transport test
Freeze the mechanism except for the explicitly supplied wind field \(W\); evaluate a second physical wind regime without retuning diffusion/residual parameters.

A reusable mechanism is supported only if the same operator parameterization survives T1–T4.

## 6. Implication for residual dictionaries

Do not cluster raw residual vectors across sources.

If M7 reaches O1/O2, cluster or identify **operator behavior conditioned on state and local physics**, e.g.:

\[
R_\theta(c_t,W,O)
\]

or latent operator codes inferred from local trajectory/context.

The dictionary should represent reusable mechanisms, not memorize source-specific error maps.

## 7. Current decision

\`PRECHECK = STATE-DEPENDENCE WARNING / M7 NOT KILLED\`

The historical route data strengthen the requirement for a true state-dependent operator test and rule out simplistic additive residual-template interpretations.
