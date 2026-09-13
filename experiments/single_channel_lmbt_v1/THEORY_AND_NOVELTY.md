# Lag-Marginalized Backward Transport (LMBT)

## Scientific object

LMBT treats a sensor sample as a **delayed receptor event**, not as gas created
at the current robot cell.  It reconstructs the latent exposure supported by
the sensor dynamics and propagates the associated receptor locations backward
through the transport field to obtain a source footprint.

For the frozen first-order sensor law,

\[
y_k=a y_{k-1}+(1-a)c_{k-d},\qquad a=\exp(-\Delta t/\tau),
\]

the noise-free latent delayed exposure is

\[
\hat c_{k-d}=\max\left(0,\frac{y_k-a y_{k-1}}{1-a}\right).
\]

In a real noisy sensor this becomes a non-negative state observer and a
distribution over lag, rather than hard deconvolution.  V1 uses the exact frozen
simulation contract only to test the premise.

For a receptor event at position \(x_r\) and time \(t_r\), the backward path
obeys

\[
\frac{dX}{da}=-u(X,t_r-a),
\]

where \(a\) is emission age.  Diffusion turns the path into a footprint

\[
F_r(s)=\int_0^A
\mathcal N\!\left(s;X_r(a),\sigma_0^2 I+2\kappa aI\right)\,da.
\]

Equal-weight log pooling across distinct reconstructed whiffs gives source
evidence without using concentration magnitude as an emission-rate proxy:

\[
\log L(s)=\frac1R\sum_{r=1}^R \log(F_r(s)+\epsilon).
\]

## The second-order transfer

The module combines three established ideas whose conjunction addresses the
observed failure:

1. robotic olfaction timing layers: explicitly invert or observe sensor
   hysteresis and align gas, pose, and wind timestamps;
2. atmospheric source-receptor footprints: transport evidence backward from a
   receptor instead of simulating every candidate source independently;
3. stochastic backward transport: integrate multiple detections as endpoint
   evidence over possible emission histories.

The proposed contribution is **not** generic backward transport.  That idea is
old in atmospheric inversion and appears directly in a July 2026 source-
localization preprint.  The candidate novelty is the combination of:

- lag-marginalized receptor assignment induced by a mobile gas sensor's state;
- obstacle- and time-conditioned backward footprints;
- source-posterior evidence, rather than a learned search drift;
- a one-channel online contract with no source-response lookup bank.

The current formal test uses simulation-known wind only as a falsification
instrument.  A paper claim cannot call this deployable until a causal, past-only
wind provider passes an independent predictive gate.

## Relation to causality

The structural chain fixes what may cause what and forbids future wind, source
truth, and current-pose reassignment of delayed gas.  This makes LMBT a
mechanism-constrained inverse estimator.  The present single-stream evidence
does not justify the broader phrase “causal source localization.”  Causality can
remain the design and falsification principle; the main algorithmic claim must
be backward transport attribution unless a later intervention test identifies
the source effect across transports.

## Collision boundary with prior project modules

- TSDC predicts a future encounter for planning; LMBT attributes a completed
  measurement backward to candidate sources.
- CTT carries exact pre-generated source responses; LMBT computes one receptor-
  to-source footprint online and has no per-source response library.
- M1R and CCDE transform candidate evidence after it exists; LMBT changes the
  observation likelihood that creates the evidence.
- The earlier G2 committor documents proposed a forward/future operator.  They
  did not implement lag-marginalized retrodictive source evidence on the failed
  H03 trace.

