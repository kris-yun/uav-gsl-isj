# Primary endpoint and confidence interval

## Unit of fresh stochastic replication

There are:
- 12 fixed truth sources;
- 8 independent GADEN realizations/source;
- 2 frozen paths per realization.

The two paths are correlated measurements of the SAME plume realization and
are never counted as two independent plumes.

## Unique Top-1

For arm a, source s, realization r and path p:

`I_a(s,r,p)=1`

iff the true source is the unique minimum-B2-SSE candidate among ALL 624 legal
candidates.

Otherwise `I=0`.

Use the exact unique-tie semantics of the frozen amplitude-operator
implementation. Do not introduce a new tie tolerance after targets are read.

An all-zero target is retained and counted as not uniquely correct for both
arms.

## Paired source-realization effect

First average the two paths:

`d_sr = 0.5 * sum_p [I_rawu(s,r,p)-I_u(s,r,p)]`.

Then:

`Delta_acc = (1/12) sum_s (1/8) sum_r d_sr`.

This is the PRIMARY F1 endpoint.

## Frozen practical-effect threshold

Nominal confirmation requires:

`Delta_acc >= 0.05`.

Interpretation:
at least five percentage points of paired unique-Top1 improvement across the
fixed 12-source panel.

This threshold is signed prospectively and is not estimated from the old OPEN
House01/House02 effect.

## Paired stratified bootstrap

Use exactly:
- 10,000 bootstrap replicates;
- RNG seed `2026092703`;
- NumPy PCG64;
- percentile interval;
- quantiles 0.025 and 0.975;
- NumPy `quantile(..., method="linear")`.

For each bootstrap replicate:
for EACH of the 12 sources independently, sample 8 realization indices with
replacement from its frozen 8 realizations.

Whenever a realization index is selected, keep grouped:
- both paths;
- both arms u/rawu;
- nominal and state0 stress scores.

Source identities are NOT resampled.

Thus the main CI is conditional on:
- this fixed 12-source truth panel;
- the frozen 624-candidate template banks.

It quantifies plume-realization variability, not whole-House source-selection
uncertainty.

Nominal CI gate:

`95% lower bound of Delta_acc > 0`.

Both the 0.05 point-effect gate and lower-bound gate are required.

## Stress non-inferiority

Compute `Delta_acc_state0` using the same definition and the SAME bootstrap
draws.

Stress non-inferiority is supported iff:

`95% lower bound >= -0.05`.

Failure of this non-inferiority condition is NOT automatically a proven
resolution-robustness tradeoff.
