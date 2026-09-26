# Information-layer definitions

For source `s`, reference realization `i`, frozen time `t`, probe `q`:

`B[s,i,t,q] = 1[C[s,i,t,q] > 0]`.

R0 gives 16 independent realizations/source, each with `T=10`, `Q=30`.
Each directed fold uses `K=8` reference realizations and 8 held-out targets.

## L0 — complete mean encounter field

`p_hat[s,t,q] = mean_i B[s,i,t,q]`.

A reference-only cellwise replicate shuffle independently permutes the K
realization labels at every `(t,q)` within the SAME source:

`B_C1[s,i,t,q] = B[s, sigma[s,t,q](i), t,q]`.

This preserves **exactly**:
- every empirical `p_hat[s,t,q]`;
- binary support;
- every source/time expected count `sum_q p_hat[s,t,q]`.

It destroys:
- within-time cross-probe realization pairing;
- cross-time realization pairing.

After shuffling, count trajectories are reconstructed as
`X_C1[s,i,t] = sum_q B_C1[s,i,t,q]`.

Thus C1 is a finite-sample observational surrogate for "marginals retained,
joint pairing destroyed". It is not claimed to be a physically realizable
plume.

## L1 — complete each-time snapshot/count distribution

At every time t, permute the K complete 30-dimensional snapshots as units:

`B_C2[s,i,t,:] = B[s, tau[s,t](i), t,:]`.

This preserves exactly:
- every `p_hat[s,t,q]`;
- the complete empirical set of 30-D spatial snapshots at each time;
- the complete empirical count distribution `P_hat_s(X_t=k)` at each time;
- binary/count support.

It destroys only:
- which time-t snapshot belongs to the same realization as the snapshot at
  another time.

Count trajectories:
`X_C2[s,i,t] = sum_q B_C2[s,i,t,q]`.

## L2 — original paired count trajectories

`X_RAW[s,i,t] = sum_q B[s,i,t,q]`.

This retains the original cross-time realization pairing in the 10-D count
trajectory.

## Interpretation hierarchy

- RAW not distinguishable from C1:
  no evidence, in this representation, for dependence information beyond the
  complete binary marginal field.
- RAW distinguishable from C1 but not C2:
  additional information is attributable to each-time spatial joint/count
  distribution, not cross-time pairing.
- RAW distinguishable from C2:
  cross-time pairing of the count trajectory carries additional development-set
  source identity beyond complete each-time marginals.

These statements are representation- and K-specific. They are not universal
claims about turbulent plume physics.
