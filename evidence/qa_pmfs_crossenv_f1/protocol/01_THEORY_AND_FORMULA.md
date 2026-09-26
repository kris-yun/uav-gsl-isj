# 1. Scientific object

## 1.1 The failure mode

A source candidate does not generate independent observations after all
unobserved transport variability is averaged out.

If a slowly varying latent plume/environment regime `Z` persists across one
observation episode, the correct marginalization is

`p(y_1:T|s) = ∫ p(z) ∏_t p(y_t|s,z) dz`.

Repeatedly integrating `z` inside every factor instead gives

`∏_t ∫ p(z) p(y_t|s,z) dz`,

which corresponds to re-sampling the slow environment between observations.
The two are not generally equal.

With both fast transport state `W_t` and slow episode state `Z`:

`p(y_1:T|s) = ∫p(z)∏_t[∫p(w_t|z)p(y_t|s,w_t,z)dw_t]dz`.

This is the QA hierarchy.

## 1.2 Minimal marginal-preserving implementation

Let the already-computed candidate event marginal be `p_e(s)`.
Introduce:

`Z ~ N(0,1)`,
`eps_e ~ N(0,1)`,
`U_e = sqrt(rho) Z + sqrt(1-rho) eps_e`,
`H_e = 1[U_e <= Phi^{-1}(p_e(s))]`.

Then exactly:

`P(H_e=1|s) = p_e(s)`.

Thus QA changes **only the joint law**, never the event marginals.

For an observed hit vector `h`:

`L_Q(s) = ∫ phi(z) ∏_e Bernoulli(h_e; Phi((Phi^-1(p_e(s))-sqrt(rho)z)/sqrt(1-rho))) dz`.

`rho=0` is exactly the independent Bernoulli baseline.

## 1.3 Two timescales

For block length `L`, one latent variable is shared per consecutive block.
Candidate set `L={1,2,5,10}` gives a direct timescale test.

On R0, all four reference-only splits selected `L=10, rho=0.6`.
Therefore the observed development signal is consistent with a
quasi-quenched episode regime rather than purely transient correlation.

## 1.4 PMFS output is retained

For prior `pi(s)`:

`q_QA(s|y) = pi(s)L_QA(s) / sum_k pi(k)L_QA(k)`.

No change is required to the concept of the source-location probability map.
