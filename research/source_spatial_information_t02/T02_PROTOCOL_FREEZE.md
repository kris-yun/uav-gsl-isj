# T02 — Static Spatial Source Information Audit

Date: 2026-10-01. Frozen before this task decodes target values.

Branch: `research/source-spatial-information-t02-20261001`.
Base: `f5fab1c5f5dfee5731a13a21d8995902d7a31434`.

## Authorized task

This is a mechanism diagnosis, not a new main method or main-innovation PASS.
Keep all prior CDSI and R0/R1/R2 results unchanged. Use precisely the 64 frozen
OCB-R2 S2+S2X H01/H02 discovery inputs, 8 contexts x 2 configured sources x
4 independent realizations. Reuse their original binary definition C>0 and
their 10 times / 30 probes. No observation re-extraction or selection.

No GADEN, new plume, PMFS, neural network, R3A, confirmation, House03 or closed
loop. No fixed-z 12-run experiment is authorized here. Finish and STOP.

## Frozen representations

For each binary 10x30 tensor B, let v=mean_t B, a 30D static profile.

1. TOTAL_RATE_1D: mean of all 300 entries, shape (1,).
2. STATIC_SPATIAL_30D: v, unchanged from T0.1B STATIC.
3. AMPLITUDE_REMOVED_SPATIAL_30D: v-mean_q(v), removing the additive common level.
4. COMPOSITIONAL_SPATIAL_30D: v/sum_q(v) if sum>0; an all-zero v maps to the
   all-zero vector. No epsilon, imputation, dropped sample or source-specific
   rule. Report every zero-profile run. The zero vector retains absence of any
   encounter; compositional results must not silently claim this flag removed.

Centering does not remove every multiplicative or histogram feature. Composition
does not remove every spatial marginal or shape/histogram distinction.

LOCATION_DESTROYED starts from STATIC, independently permuting the 30 probe
identities of **each actual realization**. Preserve its full value multiset,
sum, mean and squared norm. No source-label pooling and no time permutation.
Use 1000 permutations per context, all 8 samples independently. NumPy keys
SeedSequence([2026100103, context_index, sample_index]) and stable argsort of
iid uniforms of shape (1000,30). Sample order is sorted source ID then
replicate ordinal, used only as fixed file ordering; labels never enter RNG.

For each draw compute the same normalized Euclidean V-statistic Energy
Distance. Average over all 1000 draws. The averaged statistic can be computed
from the average distance matrix because Energy is linear in pairwise
distances. Reuse those source-blind sample transformations under all 70
source-label assignments. This differs appropriately from source-conditional
C2, which needed rebuilding after assignment. Surrogates do not enlarge N.

## Exact source-label null and standardization

Strictly reuse `research/cdsi_t01b/run_audit.py` functions all_energy,
energy_matrix, summary, ASSIGN, COMPLEMENT, and sign_test. Its hash is frozen
in the implementation binding. Normalized distances divide by sqrt(d),
with d=1 for TOTAL and d=30 for every spatial arm. Same V-statistic, tie
tolerance 1e-12, ddof=0, 70 exact 4-vs-4 assignments and one-sided p-values.
No kernel/bandwidth, fair-U replacement or calibration.

Cross-context source stability for each representation exactly follows T0.1B:
>=7/8 above exact-null median, >=6/8 exact p<=.05, exact direction sign-test
p<.05, stratified aggregate permutation p<.05. The aggregate is mean of the
eight exact-null-standardized Z values. Use the same 1,000,000 independent
stratified assignment draws with default_rng(2026100102) for every arm, common
assignment indices across arms. Report it as Monte Carlo, not exhaustive 70^8.
Retain every exact 70-assignment null. For the million-draw aggregate nulls,
save counts, summaries and SHA256 of the complete float64 byte arrays; their
fixed seed and exact-context Z tables permit regeneration without putting
five large million-row arrays into the review package.

## Human-approved diagnostic label amendment

The user confirmed: **按上述诊断规则冻结** in response to the numeric-label
question before any T02 score calculation.

Apply this fixed hierarchy:

1. If TOTAL is stable and both centered and compositional arms are unstable:
   STATIC_SIGNAL_PRIMARILY_AMPLITUDE.
2. Otherwise, if both centered and compositional arms are stable and
   STATIC Z - LOCATION_DESTROYED Z has positive median, >=6/8 positive contexts
   and exact one-sided context sign-test p<.05:
   STATIC_SIGNAL_PRIMARILY_SPATIAL_PATTERN.
3. Otherwise, if TOTAL is stable and at least one of centered/compositional
   is stable: STATIC_SIGNAL_MIXED.
4. Otherwise: STATIC_SIGNAL_UNRESOLVED.

Only these mechanism labels are allowed; no new theory or innovation PASS.
"Primarily" is this operational label, not a fractional causal attribution.
TOTAL being stable means it can distinguish these two configured sources;
it does not prove sufficiency for every component of source information.

## Verification and limitations

Check metadata-only independent-sample contract first. If metadata unexpectedly
fails, stop with STATIC_SIGNAL_UNRESOLVED and a reason before scoring.
Bind all 64 file hashes to R0. Check STATIC parity with T0.1B, exact assignment
and A/B complement symmetry, zero-case behavior, profile multiset preservation,
normalization arithmetic, optimized/direct LOCATION draw arithmetic, and an
independent direct-sum Energy implementation. Complete two full calculations,
require byte-identical scientific outputs, commit evidence, package and STOP.

Report all 8 contexts and both Houses, original xyz, four representations,
LOCATION evidence, nulls, Z differences, zero flags, preservation and hashes.
Source heights differ within both Houses: this diagnoses configured xyz source
identity, not pure xy or continuous identifiability. Same discovery data have
been examined before; this is a frozen diagnostic, not fresh confirmation.
