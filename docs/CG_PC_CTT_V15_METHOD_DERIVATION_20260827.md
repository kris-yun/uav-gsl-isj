# CG-PC-CTT V15 — method derivation and claim boundary

Date: 2026-08-27

Status: **CANDIDATE / CURRENTLY TESTING**

Candidate name: **Completeness-Gated Proximal-Causal Transport Tomography
(CG-PC-CTT; 完备性门控近端因果输运层析)**.

This document freezes the mathematical object to be tested. It is not a
statement that the main innovation has already succeeded.

## 1. Scientific problem

CTT V13 M1 established a wind-conditioned first-passage transport field and
improved held-out source ordering in House03. The hard House02 transport gate,
however, showed that a source candidate can still obtain a strong but
physically wrong score under model mismatch.

A one-dimensional observability/rank test is insufficient. A source-response
matrix may have nonzero relative rank while its weakest source direction is
small compared with unresolved transport variability. In that regime a sharp
posterior update is not justified.

Therefore V15 separates two questions:

1. **Is source discrimination identifiable at this update?**
2. **If it is, can hidden transport nuisance be handled without explicitly
   reconstructing the nuisance state?**

## 2. Frozen M1

M1 is unchanged.

For candidate source `s`, query/location `q`, wind/context `W,E`:

`M1: (s,q,W,E) -> p(tau | s,q,W,E), h_{s,q}(t)`.

The existing CTT V13 M1 GO checkpoint is the parent of this branch. V15 must
not change M1 weights, bank generation, source candidates, transport members,
held-out contexts, or the M1 ordering endpoint.

## 3. G_id — transport-uncertainty-whitened completeness gate

Let the candidate-by-transport-member M1 response representation at one
external context be

`phi_{s,m,t} in R^d`.

For candidate `s`, using development/available transport members:

`mu_{s,t} = (1/M) sum_m phi_{s,m,t}`.

Pooled within-candidate transport covariance:

`Sigma_tr,t = [1/(S(M-1))] sum_s sum_m
              (phi_{s,m,t}-mu_{s,t})(phi_{s,m,t}-mu_{s,t})^T`.

The implementation uses a fixed shrinkage regularizer

`Sigma_hat = 0.9 Sigma_tr + 0.1 tr(Sigma_tr)/d * I`

to avoid an unstable inverse. The shrinkage coefficient is frozen before
final testing.

For the local active candidate set `A_t` of size `K`, center the candidate
means:

`M_t = P_K [mu_{s,t}]_{s in A_t}`,

where `P_K = I - 11^T/K`.

Whiten:

`M_t^w = M_t Sigma_hat^{-1/2}`.

Let nonzero local source-contrast singular values satisfy

`sigma_1 >= ... >= sigma_(K-1)`.

Define two non-redundant diagnostics:

`gamma_t = sigma_(K-1) / sigma_1`

and

`alpha_t = sigma_(K-1)`.

Interpretation:

- `gamma_t`: relative conditioning / whether all local source directions are
  present instead of collapsing onto a lower-dimensional contrast.
- `alpha_t`: absolute strength of the weakest local source direction after
  transport-uncertainty normalization.

A large `gamma` alone is not sufficient. For example, a spectrum
`[1e-3, ..., 1e-4]` has a seemingly acceptable ratio but negligible absolute
separation.

The gate is:

`G_id(t) = 1[gamma_t >= theta_gamma and alpha_t >= theta_alpha]`.

If it fails, the later runtime implementation must **abstain exactly**:

`q_t(s) = q_{t-1}(s)`.

No low-weight update, softened likelihood, entropy trick, or posterior
sharpening is allowed on a failed gate.

### Threshold rule

The implementation does not tune `theta_gamma` or `theta_alpha` on final CTT
test contexts or hard H02 final cases.

Thresholds are selected on development contexts by a frozen grid of
development quantiles, with minimum coverage and minimum accepted-atom count.
The evaluation endpoint is the already-frozen M1 matched-neighbor source
ordering margin.

The script also reports gamma-only and alpha-only comparators. V15 requires
evidence that adding absolute strength is useful beyond gamma-only gating.

## 4. M2 — proximal causal bridge

Let:

- `U_t`: unresolved plume/transport realization, not explicitly reconstructed.
- `Y_t`: observed gas/encounter response.
- `S`: candidate source intervention/query.
- `Z_t(S)`: candidate-dependent source/treatment-side proxy derived from M1
  physics, e.g. predicted first-arrival structure, travel time, source-query
  wind alignment, path features.
- `R_t`: candidate-independent onboard proxy of transport/sensor state, e.g.
  recent local wind sequence/variability, pose and motion history, encounter
  history summary, sensor transient state.
- `C_t`: allowed measured context.

The bridge is not trained to recover `U_t`. It seeks `h(R,S,C)` satisfying a
conditional-moment approximation:

`E[Y - h(R,S,C) | Z,C] ~= 0`.

The implemented finite-dimensional operationalization uses sieve bases

`H = Phi_h(R,S)`

and

`G = Phi_g(Z,S)`,

then solves the regularized moment problem

`beta* = argmin_beta || G^T(Y - H beta)/N ||_F^2
                         + lambda ||beta||_2^2`.

The closed form is:

`A = G^T H / N`

`b = G^T Y / N`

`beta* = (A^T A + lambda I)^(-1) A^T b`.

`lambda` is selected on development data only by moment loss, with prediction
MSE used only as a deterministic tie-breaker.

At inference:

`h_theta(R,s) = Phi_h(R,s) beta*`.

`Z` is not supplied to `h` at inference.

For an observed event and candidate panel, the minimal source-ordering
diagnostic is

`score(s) = - ||Y_obs - h_theta(R_obs,s)||^2`.

The offline source margin is

`Delta = score(s_true) - max_{s != s_true} score(s)`.

Equivalently, in the implementation:

`margin = min_false_error - true_error`.

Positive margin means the true synthetic source outranks all tested false
candidates.

## 5. Why the bridge data contract is strict

The current House03 first-passage bank is sufficient to test G_id, but it does
not automatically provide a valid member-varying, candidate-independent
outcome-side proxy `R` for proximal identification.

Therefore M2 must not fabricate a proxy from source truth, wind IDs, transport
member IDs, route IDs, simulator phase, or future outcomes.

If the available onboard history does not contain an `R` that carries
information about unresolved transport nuisance, M2 is **scientifically
unidentified on that dataset** and must be reported `INVALID_FOR_BRIDGE`,
rather than forcing a positive result.

## 6. Negative controls

The bridge must be tested with at least:

1. `Z` row shuffle: destroys the source-side proxy moment structure.
2. source-query `S` shuffle: destroys source intervention alignment.
3. later hard-H02 test: no tuning after the H02 panel is opened.

A bridge gain that survives all causal destruction controls is not accepted as
evidence for the claimed mechanism.

## 7. Outer posterior

Do not invent a new sequential Bayes update in this phase.

If G_id and M2 pass offline qualification, later closed-loop integration should
reuse the already positive reversible cumulative/fixed-prior outer mechanism
from V11 or another separately frozen native-anchored mechanism, with exact
abstention on `G_id=FAIL`.

The offline branch does not change the planner.

## 8. Claim boundary

If only G_id succeeds:

> The project has a transport-uncertainty-normalized source-identifiability
> gate that predicts when M1 source evidence is trustworthy.

Do not call the whole method proximal causal inference yet.

If G_id and M2 both succeed on held-out and hard H02 tests:

> The project has evidence for completeness-gated proximal causal source
> inference: source updates are allowed only when local source contrasts are
> strong relative to transport uncertainty, and hidden transport nuisance is
> handled through an observed-proxy bridge rather than explicit nuisance-state
> reconstruction.

Still do not claim a general proximal-identification theorem or Pearl-style
interventional effect identification.

## 9. Status taxonomy at branch creation

CONFIRMED:
- CTT M1 House03 GO remains frozen.
- full rank / gamma alone is not a sufficient reliability claim.
- final-test threshold tuning is prohibited.
- exact abstention is the required behavior on a failed gate.

CURRENTLY TESTING:
- dual `gamma + alpha` completeness gate.
- finite-dimensional proximal bridge moment model.

REJECTED:
- contrast-cosine stability as the second gate.
- naive context mean subtraction as M2.
- simple H02 transport penalty/correction.
- gamma-only as a complete reliability mechanism.

HOLD:
- transition-dynamics M3.
- 300 s closed loop.
