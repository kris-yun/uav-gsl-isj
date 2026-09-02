# CTPI V0.4 three-module theory freeze

## Common chain

`causal stochastic transport -> information-geometric metrology -> proper-score statistical decision`.

## M1 — CREL: Causal Route-Encounter Law

For candidate source `s`, current deployment-available context and stochastic transport nuisance `U`, CREL preserves a candidate response law rather than collapsing transport to one deterministic plume:

\[
P(Y\mid do(S=s),do(X_{1:t}=x^{obs}_{1:t}),M,W,U).
\]

When `U` is unobserved, evidence marginalizes source-independently over transport members. Candidate-specific amplitude/nuisance rescue is forbidden.

**Identity:** physical causal generator. It answers: *what physical consequences can this source produce under the current sensing design?*

## M2 — PSRG: Pullback Source Resolution Geometry

For Bernoulli response probability `p`, use the Fisher-Rao coordinate

\[
u=2\arcsin\sqrt p.
\]

On exact quadtree shared-edge source neighbours, locally fit

\[
\Delta u \approx \Delta s B_s,\qquad J_s=B_sB_s^\top.
\]

`J_s` is a source-space information tensor. Its eigenstructure describes directional local source separation. The diagnostic scale

\[
r_{local}=1/\sqrt{\lambda_{min}(J_s)}
\]

is **only a local response-separation scale**. It is not a confidence interval, posterior radius, or localization-error bound.

No kNN `k`, neighbourhood radius, kernel bandwidth, or outcome-tuned threshold is used. Neighbours come from the quadtree carrier geometry.

**Identity:** local source metrology / resolution geometry.

## M3 — APRS: Adaptive Proper-Score Resolution

On the current PMFS observation support, marginalize transport members:

\[
\bar p_{sj}=M^{-1}\sum_m p_{smj}.
\]

Use current measured-hit probability `y_j` and current PMFS confidence `c_j`:

\[
\ell_s=\sum_j c_j[y_j\log\bar p_{sj}+(1-y_j)\log(1-\bar p_{sj})].
\]

The finite-Monte-Carlo floor is inherited from forward-map resolution, not selected from localization outcomes. A common scaling of all `c_j` does not change source ordering; no temperature/blend parameter is introduced.

This is a confidence-weighted proper cross-entropy against the **current measured-hit field**. Runtime integration must not double-consume the same gas evidence by multiplying APRS onto a native PMFS posterior that already assimilated that field.

**Identity:** observation evidence arbiter.

## Non-negotiable boundaries

- PSRG may not be used as an error/confidence radius without separate calibration proof.
- APRS may not use future gas/wind/route, truth, localization error, planner reward, source rank, or post-outcome tuning.
- Current-update response fields may not be carried tens of seconds forward as if transport context were unchanged; that stale-context variant failed offline and is retained as negative evidence.
- Old CPIR persistent-sensor M2 and stop-resolved M3 NO-GO results remain frozen negative evidence.
- Bank-free CREL for unknown-site deployment remains open; bank/oracle CREL is a development teacher, not the final deployment contract.
