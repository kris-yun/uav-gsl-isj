# CG-PC-CTT fast-track diagnostic — 2026-08-27

This note records diagnostics performed on the frozen V2 evidence package. It does **not** alter or supersede the frozen H03 `GATE_V2_GO` result and does not claim the missing H02 hard-28 challenge.

## Frozen evidence boundary

- Gate V2 source commit: `c2b290e1a89a105eca3d5772f725ba8114d52691`.
- H03 real bank: `phi[10,206,8,626]`, 10/10 global Gate V2 PASS.
- H02 exact hard-28 / 201-candidate product remains missing.
- One H02 feasibility reconstruction exists for seed `859169523`, source update 1, with `166 candidates x 8 members`, 631 free-support query cells. This is **not** the preregistered hard-28 product.

## Diagnostic 1 — H03 representation stress

Frozen Gate V2 was reapplied without threshold/rank changes after deterministic feature-axis subsampling:

| feature stride | D | accepted | gamma_cf range | p_signflip |
|---|---:|---:|---:|---:|
| 1 | 626 | 10/10 | 0.8642–0.8655 | 1/128 all |
| 2 | 313 | 10/10 | 0.8577–0.8590 | 1/128 all |
| 4 | 157 | 10/10 | 0.8513–0.8542 | 1/128 all |
| 8 | 79 | 10/10 | 0.8637–0.8673 | 1/128 all |

Interpretation: H03 replicated-completeness PASS is not an obvious artifact of using all 626 free-cell features.

## Diagnostic 2 — single reconstructed H02 context

The one feasibility-only H02 bank was loaded directly from the frozen CTT binary records and evaluated with unchanged Gate V2. This is diagnostic only.

| feature stride | D | gamma_cf | alpha_cf | p_signflip | Gate |
|---|---:|---:|---:|---:|---|
| 1 | 631 | 0.6177 | 40.3089 | 1/128 | PASS |
| 2 | 316 | 0.6300 | 29.3583 | 1/128 | PASS |
| 4 | 158 | 0.6241 | 20.7541 | 1/128 | PASS |
| 8 | 79 | 0.6853 | 15.9785 | 1/128 | PASS |

Interpretation: at least one historical House02 runtime context has strong **global** replicated-completeness under V2. This does not establish reliability because no frozen M1 hard-negative margin is available for this reconstruction.

## Diagnostic 3 — real local candidate aliases in H02 reconstruction

The 166-candidate H02 feasibility manifest contains only 144 unique source coordinates:

- 21 duplicate-coordinate groups;
- 43 candidates participate in a duplicate-coordinate group;
- some distinct quadtree candidate IDs have exactly the same point-source coordinate.

For point-source transport prediction, candidates with identical coordinates are physically identical inputs and therefore cannot be source-separated by any first-passage field using only that coordinate.

Nearest-neighbor replicated pair audit on this H02 context:

- median nearest-neighbor distance: ~0.30 m;
- pair `p<=0.01` fraction: ~0.699;
- pair `p>0.05` fraction: ~0.283;
- several coordinate-alias pairs have `distance=0`, `pair_alpha_cf=0`, `p=1`.

This is a real-data demonstration that:

`global Gate V2 PASS` does not imply `all local hard-negative candidates are identifiable`.

Do not merge/deduplicate candidates post-hoc inside the frozen V2 claim. For the fast-track next method version, candidate-coordinate equivalence classes may be handled only through a newly versioned, truth-free contract.

## Diagnostic 4 — H03 local-pair structure

House03 has 206/206 unique candidate coordinates. Across its 10 contexts, nearest-neighbor pair diagnostics are much stronger than the H02 feasibility reconstruction:

- mean fraction of nearest-neighbor pairs with exact `p<=0.01`: ~0.907;
- only ~0.019–0.024 of nearest-neighbor pairs per context have `p>0.05`;
- nevertheless each context contains at least one weak local pair (`p≈0.336`).

Thus H03 is broadly locally identifiable but global 10/10 PASS still hides a small weak local tail.

## Binding fast-track interpretation

1. Preserve the frozen V2 global Gate as a **model-side replicated-completeness premise** unless the exact H02 hard-28 margins prove reliability stratification.
2. Do not tune Gate V2 from these diagnostics.
3. When the exact H02 28-case product arrives, run simultaneously:
   - frozen global Gate V2;
   - frozen hard-negative margin evaluation;
   - `local_pair_audit.py` as diagnostic only;
   - bridge + negative controls if the bridge data contract is valid.
4. If the frozen bridge fast-track verdict passes, transition directly to the preregistered House01/02/03 x seeds 0..9 OFF/ON closed-loop matrix; no intermediate House/seed-specific tuning.
