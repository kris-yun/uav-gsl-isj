# CESS D0 Strict Interventional Control

Date: 2026-09-24

Purpose: remove the strongest finite-sample confound in the first exploratory macro-information screen.

Status:
**CESS_D0_STRICT_CONTROL_PASS — continue D1 design**

## 1. Confound being tested

The first D0 screen estimated a Bernoulli encounter profile by pooling all training realizations from the micro source cells belonging to one macrostate.

Because a macrostate contains several micro source cells, that macro profile is estimated from more training samples than a single microstate profile.

Therefore a macro advantage could be caused by estimator sample size rather than a real information-scale effect.

## 2. Strict control

Train **only the 18 micro-source likelihoods**:

\[
\hat p(h\mid do(S=s)).
\]

Every micro source uses exactly the same number of training realizations.

No macro model is trained.

For a proposed macrostate \(m\), construct its likelihood only from the already-trained micro likelihoods according to the frozen intervention contract:

\[
\hat p(h\mid do(M=m))
=
\frac{1}{|\mathcal S_m|}
\sum_{s\in\mathcal S_m}
\hat p(h\mid do(S=s)).
\]

Therefore macro inference receives **zero additional parameter-estimation samples**.

The macro intervention prior remains uniform over macrostates.

## 3. Held-out raw effective-information lower bound

For uniform macro interventions:

\[
I(M;H)=\log |M|-H(M|H).
\]

Using held-out negative log posterior / cross entropy:

\[
\underline{EI}_{val}(M)
=
\log |M|-\mathrm{CE}_{val}.
\]

This raw lower bound is the primary scale-selection quantity.

Normalized effectiveness

\[
\underline{\eta}_{val}(M)
=
\underline{EI}_{val}(M)/\log|M|
\]

is retained only as a diagnostic because it can prefer excessively coarse representations.

## 4. Strict-control result

Average across first8→last8 and last8→first8:

| Macro states M | raw EI lower bound (nats) | normalized bound |
|---:|---:|---:|
| 18 micro | **1.306475** | 0.452009 |
| 12 | **1.990245** | 0.800934 |
| 9 | 1.775344 | 0.807994 |
| 6 | 1.456854 | 0.813086 |
| 4 | 1.322942 | 0.954301 |
| 3 | 1.098612 | ~1.000 |
| 2 | 0.693147 | ~1.000 |

The raw interventional information lower bound has a genuine intermediate-scale peak at **M=12**.

This is qualitatively different from normalized effectiveness, which approaches one for very coarse states.

## 5. Split detail

### 18 microstates
- first8→last8: 0.942668 nats
- last8→first8: 1.670282 nats

### M=12
- first8→last8: 2.279068 nats
- last8→first8: 1.701422 nats

Thus the M=12 macro representation exceeds the micro lower bound in **both** split directions, although the second-direction margin is small.

This is why D1 must use many more source cells and locked fresh realizations.

## 6. Size-matched random-partition control

For each spatial macro partition, 250 random non-spatial partitions were generated with the **same cluster-size vector**.

Spatial raw EI lower bounds versus random controls:

| M | spatial EI | random mean | random 95th percentile | spatial percentile |
|---:|---:|---:|---:|---:|
| 12 | 1.990 | 0.962 | 1.164 | 1.000 |
| 9 | 1.775 | 0.733 | 1.438 | 1.000 |
| 6 | 1.457 | 0.471 | 1.218 | 1.000 |
| 4 | 1.323 | 0.163 | 0.854 | 1.000 |
| 3 | 1.099 | 0.218 | 0.950 | 1.000 |
| 2 | 0.693 | -0.096 | 0.581 | 1.000 |

For every tested macro count, the spatial partition beats all 250 random partitions.

## 7. Interpretation

The exploratory signal cannot be explained merely by:

- fewer labels;
- more samples for macro parameter estimation;
- arbitrary grouping with the same group sizes.

The remaining hypothesis is specific:

> spatially neighboring source interventions induce encounter distributions that are partially degenerate at the finest PMFS scale, and an intermediate spatial coarse-graining can increase held-out interventional effective information.

## 8. What this does NOT prove

This is still not a mainline confirmation because:

- only 18 source positions are present;
- the panel is spatially sparse;
- the result was derived after R0 inspection;
- no physical macro radius can be inferred;
- the factorized Bernoulli micro likelihood is only a lower-bound decoder;
- House02/W2 only.

Therefore the only authorized decision is:

\`CESS_D0_STRICT_CONTROL_PASS_ADVANCE_D1_DESIGN\`.

No PMFS closed loop is authorized.
