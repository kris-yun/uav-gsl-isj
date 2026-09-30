# CDSI-T0.1B implementation freeze

Date: 2026-10-01. Freeze before decoding any target values in this task.

The authoritative scientific request is `protocol/USER_EXECUTION_REQUEST.txt`.
The old T0.1 matched-intervention FAIL remains unchanged. The new independent
sample estimand concerns the two configured source **xyz**, including their
different heights; it does not establish pure xy or continuous identifiability.

## Inputs and contract

Use precisely the existing 64 R0 input `.pooled.npy` files, checked against
`R0_INPUT_HASHES.json`, then convert them using the original `C>0` definition.
Do not extract new observations. Metadata check all non-source simulation
parameters (except output directory), asset hashes, generator, time axis,
wind-index sequence and single-worker contract; verify eight distinct master
seeds in each context and 64 distinct seeds overall. Different seeds are
required, not a failure. The same generator and salts define the noise law.

## Energy and context exact tests

Use the request's V-statistic Energy Distance (including zero diagonals), not
a fair-U estimator. Each Euclidean distance is divided by sqrt(d): FULL/C2
d=300, STATIC d=30. STATIC is the time mean. Population interpretation and
finite-sample null are distinct: the finite V-statistic is upward-biased;
positivity alone is not evidence. All gates use the permutation null as signed.

For each context, sort source IDs and each source's replicate ordinals. Concatenate
four A then four B realizations. Enumerate every 4-element subset of 0..7 in
lexicographic order, exactly 70 assignments; observed assignment is 0..3.
One-sided p is count(T_perm >= T_obs)/70, including the observed assignment.
Use comparison tolerance 1e-12 solely for numerical ties. Null median uses
NumPy's usual midpoint convention; null mean and population SD use ddof=0.
Z=(T_obs-null_mean)/null_sd; if SD=0 and all values equal, set Z=0, p=1.
Null percentile is the fraction <= observed, with the same numerical tolerance.

## C2 reuse and its null

Reuse R0's operation: independently permute the four realization labels at
each time while preserving the entire 30D snapshot. K=4 follows the present
4-vs-4 audit, rather than R0's K=3 reference-only score. Do not permute probes
or change the binary threshold. R0's argsort-of-iid-uniforms operation, stable
ordering and seed base 2026093002 are retained. Keys are
SeedSequence([2026093002, context_index, group_index, 0, 0]); the two zero
fields mean this two-sample audit has no target/omitted-reference index.

Use exactly 1000 draws as in R0. Apply the same frozen permutation arrays
under every label assignment. For every assignment, reconstruct its two source
banks and repeat C2 **after** assignment; never shuffle under the original
labels and subsequently relabel those artificial trajectories.

The C2 statistic is the average Energy Distance over these 1000 transformed
4-vs-4 banks. Average that statistic with its A/B-complement assignment to
remove finite integration orientation noise. This retains exactly the same
C2 operation and enforces source-label symmetry; no outcome selects shuffles.
All each-time snapshot multisets and scalar marginals must pass preservation.
Surrogates are integration draws, not additional independent plumes.

## Cross-context aggregate

The G1 pooled statistic is the arithmetic mean of the eight FULL permutation-
standardized context effects. Independently draw one of each context's 70
assignments, 1,000,000 times, default_rng(2026100102). These draws sample the
70^8 exact joint space (576,480,100,000,000 possibilities). Report the aggregate
as Monte Carlo stratified permutation, not exact enumeration. Use
(1+count(null >= observed))/(1,000,001), record the exceedance count and a
binomial 95% Monte Carlo interval. Context-level tests remain exact.

G1 exactly follows the request: >=7/8 FULL effects above null median;
>=6/8 FULL context p<=.05; one-sided exact sign-test p<.05 on above-median
directions; aggregate stratified permutation p<.05.

G2/G3 exactly follow the listed criteria: median Z difference>0 and >=6/8
positive contexts. Also report exact one-sided sign-test p-values; the request
does not list an additional p cutoff for these two gates, so do not add one.
Exact signs are tested against Binomial(n, .5), dropping exact-zero effects.
If G1 passes, either G2 or G3 passing allows the signed dynamic label.

## Verification and stop

Before target analysis, verify primary energy arithmetic, exact assignment
count/complement symmetry, zero-signal behavior, and parity with R0's C2
implementation on synthetic K=3 data. On real inputs validate optimized C2
distance lookup against direct transformed-path distances for a fixed subset.
Run complete analysis twice and require byte-identical scientific outputs.
Report eight contexts, both Houses, source xyz, FULL/STATIC/C2 and all exact
nulls, preservation, hashes, aggregate MC and the sole signed decision.
No optional MMD/centroid model is necessary for this gate. No new simulations,
PMFS, network, confirmation/H03, literature search or closed loop. STOP.
