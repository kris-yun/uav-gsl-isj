# Scientific object

Let `N_t(x;s,w)` be the number of active PMFS filaments occupying cell x in
recording timestep t for candidate source s and wind state w.

Current PMFS retains only

`H_t = 1[N_t>0]`

through the hit-frequency map.

The marked representation retains two moments:

`p_s(x) = E[H_t]`

and

`u_s(x) = E[N_t]`.

The conditional positive-event mark is

`mu_s(x) = u_s(x) / p_s(x)` when `p_s(x)>0`.

For a bank of wind states k, annealed moments are combined BEFORE the ratio:

`pbar_s = mean_k p_{s,k}`

`ubar_s = mean_k u_{s,k}`

`mubar_s = ubar_s / pbar_s`.

This is the correct mixture identity for the conditional mean mark; do not
average conditional marks directly.

## Observation likelihood used only for D0

For a target concentration field C at observed positions:

`H=1[C>0]`.

Occurrence evidence:
Bernoulli likelihood from `pbar_s`.

Positive marks:
`z=log C` only where H=1.

The candidate forward mark is:
`x_s=log(mubar_s)` at the same observed probes.

To remove an unknown positive sensor/source-strength transformation of the
form

`C_obs = g * C_true^gamma`,  g>0, gamma>0,

fit for each candidate the nuisance regression

`z = a + b x_s + eps`,  b>=0,

and profile `(a,b,sigma^2)`.

The candidate-dependent part of the profiled mark log likelihood is

`ell_mark(s) = -(n/2) log(RSS_s/n)`.

Under any target transformation
`z' = log g + gamma z`,
`RSS'_s = gamma^2 RSS_s`; therefore every candidate score gains the SAME
additive constant `-n log gamma`. Source ranking is exactly invariant.

The full development score is

`ell_ME(s) = ell_occ(s) + ell_mark(s)`.

This is a hurdle/marked likelihood: absence/presence is counted once; positive
amplitude is conditioned on presence and is not a second hit likelihood.
