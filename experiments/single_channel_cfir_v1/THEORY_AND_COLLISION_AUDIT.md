# CFIR theory and collision audit

Date frozen: 2026-09-13

## Implementation -> observed failure

The best existing physical-footprint attempt is LMBT with exact first-order
sensor-memory correction and simulation-known spatial CFD wind.  At the frozen
`kappa=0.03` setting on H03 seed11 it moved the MAP error to 1.6004 m and placed
the true source at rank 790 / 7,258.  This is much closer than the contextual
native-PMFS endpoint (8.584 m), but the reversed-wind arm was slightly better:
1.5479 m and rank 630.  Chronological transport therefore did not provide
source-specific causal evidence.

CTAER subsequently placed the forward/reverse contrast at the candidate level,
but only on ordinal local response sequences.  It reached rank 804 and improved
MAP by just 0.0294 m over TAORL.  Its false MAP mode had stronger arrow evidence
than the true source in six of ten windows.  Pooling or window tuning cannot
create the missing spatial transport information.

## Missing theoretical property

The missing object is a candidate-specific test of whether the *physical
source-to-receptor footprint* depends on the observed arrow of time.  LMBT
ranked chronological and reversed footprint fields separately.  CTAER formed a
paired arrow contrast, but its response field was not a backward physical
footprint.  Neither asked whether the same candidate is supported specifically
by chronological transport rather than by a reversible spatial coincidence.

## One next mechanism: Causal Footprint Irreversibility Ratio

Let `S_F(c,kappa)` be LMBT's mean log footprint for candidate `c`, using the
chronological CFD wind sequence, sensor deconvolution, and reconstructed whiff
times.  Let `S_R(c,kappa)` use the same events, candidate, sensor model,
diffusion and footprint construction, changing only the wind-order negative
control.  Define

`J_CFIR(c,kappa) = S_F(c,kappa) - S_R(c,kappa)`.

Since `S_F` and `S_R` are log footprints on the same normalized scale, `J_CFIR`
is a log footprint ratio.  Higher values favour a candidate whose source
footprint explains the data specifically under chronological transport.  No
temperature, weight, learned coefficient, posterior repair, or truth-dependent
parameter is introduced.

CFIR changes candidate-relative source evidence before Bayesian accumulation.
The sign-reversed score `-J_CFIR` is frozen as the causal-direction negative
control.

## 2026 distant-field transfer and second innovation

Nonequilibrium statistical physics uses a forward/reverse path-probability
ratio to quantify trajectory irreversibility.  Turbulent inverse-source theory
uses adjoint or backward domains of dependence to connect a sensor observation
to possible upstream sources.  CFIR transfers both principles and composes a
new object for single-channel mobile gas localization: a *candidate-wise
chronological/reversed backward-footprint ratio with explicit sensor memory*.

CFIR is not an entropy-production estimator and does not solve an adjoint PDE.
Its Lagrangian backward kernel is an approximate footprint.  The full CFD wind
is oracle information available only for this simulator premise test.

## Collision audit

- Adjoint and backward source localization already exist; novelty cannot be
  claimed for source footprints alone.
- Forward/reverse trajectory ratios already exist in statistical physics;
  novelty cannot be claimed for irreversibility alone.
- LMBT already computed both chronological and reversed footprint arms, but
  never formed their candidate-wise ratio.
- CTAER already formed a candidate-wise forward/reverse contrast, but did not
  use physical backward footprints.
- M1R contrasts candidate response with source-agnostic context.  CFIR instead
  contrasts the same candidate under chronological and reversed transport.
- CCDE changes a posterior with covariance-decomposed structure.  CFIR is a
  pre-Bayes evidence operator and does not mix with the posterior.

The defensible second innovation is the exact composition above, subject to the
pre-registered H03 falsification gate.  A H03 pass would nominate the object for
new cross-House confirmation; it would not itself establish transfer.

