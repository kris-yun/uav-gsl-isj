# TCMA-D0 code and contract audit

This is a read-only audit after the frozen D0 decision. It does not amend the preregistration, reclassify the STOP, or introduce a new scientific gate.

## Implementation checks

- Recomputed all 146 stored 88-member leave-one-out residual arrays from `PSEUDO_VECTORS.npz` with an independently vectorized implementation. Maximum absolute difference: `9.094947017729282e-13`.
- Recomputed all 98 House01/02 `u` and `rawu` ABS truth ranks from the frozen Native stop observations and Native-legal candidate banks. Rank mismatches: **0**.
- Recomputed all 384 House03 nominal `u` and `rawu` ABS truth ranks from the frozen 12×8×2 target array and 624-candidate path templates. Rank mismatches: **0**.
- Recomputed the source-level Spearman and selector means from `TCMA_D0_SOURCE_RESULTS.csv`; they match `TCMA_D0_RESULT.json`.
- Source IDs, path identifiers, counts, and pseudo bank means have the archived AEC parity checks. The prior deterministic repeat showed six TCMA outputs byte-identical.

These checks find no evidence of an array-index, source-label, rank-sign, or simple arithmetic bug causing the frozen numerical STOP.

## Fundamental adequacy-statistic defect

`compute_adequacy.py` compares target residual `T` from GADEN concentration observations with self-residuals `R_k` from PMFS filament-count-proxy pseudo-vectors. The B2 gain fit makes source **ranking** insensitive to a positive common scaling of templates or observations. It does not make residual magnitudes from these two measurement systems comparable.

For any positive scalar `c`, scaling every simulator pseudo-vector by `c` gives

    T(y, c*m) = T(y, m),
    R_k(c*x, c*m_loo) = c^2 * R_k(x, m_loo).

Thus the percentile `A=[1+#(R_k>=T)]/89` changes under an arbitrary choice of simulator count units even though all B2 candidate ranks remain unchanged. Equivalently, scaling the target concentration values by `c` multiplies `T` by `c^2` while leaving `R_k` unchanged; again, every B2 rank stays the same.

A read-only scale diagnostic with the frozen vectors gives within-House Spearman(ΔA, ΔG):

| Target numerical scale | House01 | House02 | House03 |
|---:|---:|---:|---:|
| 0.1× | +0.800 | −0.224 | +0.073 |
| Original 1× | +1.000 | 0.000 | +0.606 |
| 10× | **−0.200** | +0.410 | +0.186 |

This is an invariance check, **not** a re-scored scientific arm or a proposed fix. It shows why the current `A` cannot be called a physically meaningful model-adequacy probability. Changing the normalization after observing outcomes would violate the freeze.

## Broader interpretation

The House01/02 outcomes are 49 Native action-dependent trajectories compressed to stop averages, with only four and five independent physical source units. House03 has 12 sources, eight target realizations per source, and two fixed paths. These are different observation processes; a failed cross-House association alone does not isolate whether geometry, path selection, measurement aggregation, transport mismatch, or the statistic caused it. The present D0 is also an oracle source-aware diagnostic: it selects the truth-source pseudo bank before scoring. It is not a deployable router.

The defensible conclusion is narrow: **the frozen TCMA-D0 statistic fails its preregistered cross-House gate, and its residual percentile lacks a shared physical scale**. This audit does not imply that every target-conditioned model check or every cross-environment mechanism is impossible.
