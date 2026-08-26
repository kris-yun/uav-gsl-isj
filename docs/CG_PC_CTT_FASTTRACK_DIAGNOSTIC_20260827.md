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

## Diagnostic 3 — candidate-ID aliases versus physical source resolution

The 166-candidate H02 feasibility manifest contains only 144 unique source coordinates:

- 21 duplicate-coordinate groups;
- 43 candidate IDs participate in a duplicate-coordinate group;
- duplicated IDs at the same coordinate have byte-identical first-passage fields for every member because candidate ID is not part of the transport RNG key.

The original ID-level nearest-neighbor audit therefore reported apparently weak local separation:

- pair `p<=0.01` fraction: ~0.699;
- pair `p>0.05` fraction: ~0.283;
- coordinate-alias pairs have `distance=0`, `pair_alpha_cf=0`, `p=1`.

That statistic mixes **representation aliasing** with **physical localization identifiability**. After taking the truth-free coordinate quotient (one physical source class per unique `(x,y)` coordinate), the same frozen H02 context becomes:

- 144 physical source classes;
- nearest unique-neighbor `p<=0.01` fraction: **0.9583**;
- nearest unique-neighbor `p>0.05` fraction: **0.0139**;
- only one reciprocal 0.30 m source pair is clearly weak (`p=0.2265625`).

Therefore the earlier 28.3% weak-pair number must **not** be interpreted as 28.3% physical source ambiguity. Most of it is duplicate candidate-ID aliasing. For localization, exact coordinate aliases should be treated as one source equivalence class in any newly versioned method; the frozen V2 result itself remains unchanged.

## Diagnostic 4 — H03 local-pair structure

House03 has 206/206 unique candidate coordinates. Across its 10 contexts, nearest-neighbor pair diagnostics are strong at full field support:

- mean fraction of nearest-neighbor pairs with exact `p<=0.01`: ~0.907;
- only ~0.019–0.024 of nearest-neighbor pairs per context have `p>0.05`;
- nevertheless each context contains at least one weak local pair (`p≈0.336`).

Thus H03 is broadly locally identifiable but global 10/10 PASS still hides a small weak local tail.

## Diagnostic 5 — sparse-observation stress exposes the real information bottleneck

A separate diagnostic sampled only `Q` free-support query cells from each frozen H03 field, with no Gate retuning. The **global** V2 statistic remains 10/10 PASS even with only four sampled query cells. In contrast, local nearest-neighbor replicated separation degrades sharply when observation support is sparse.

Across five fixed random subsamples per support size and all 10 H03 contexts, the mean fraction of nearest-neighbor source pairs with exact `p<=0.01` was approximately:

| sampled query cells Q | local pair p<=0.01 fraction | local pair p>0.05 fraction |
|---:|---:|---:|
| 1 | 0.038 | 0.912 |
| 2 | 0.067 | 0.831 |
| 4 | 0.157 | 0.736 |
| 8 | 0.266 | 0.526 |
| 16 | 0.380 | 0.390 |
| 32 | 0.529 | 0.264 |
| 64 | 0.696 | 0.132 |
| 128 | 0.800 | 0.069 |
| 256 | 0.871 | 0.050 |
| 626 | 0.907 | 0.021 |

This is the strongest current evidence that the next gate must be **observation-conditioned and local** rather than global-field-only. The relevant failure is not that the full forward field lacks source structure; it is that the robot may not yet have sampled enough of that structure along its actual trajectory to resolve nearby source hypotheses.

## Binding fast-track interpretation

1. Preserve the frozen V2 global Gate as a **model-side replicated-completeness premise** unless the exact H02 hard-28 margins prove reliability stratification.
2. Do not tune Gate V2 from these diagnostics.
3. Distinguish candidate-ID aliases from physical source classes in all diagnostics. Do not count identical `(x,y)` duplicates as physical localization failures.
4. When the exact H02 28-case product arrives, run simultaneously:
   - frozen global Gate V2;
   - frozen hard-negative margin evaluation;
   - local source-pair / physical-equivalence audit;
   - bridge + negative controls if the bridge data contract is valid.
5. If the frozen bridge fast-track verdict passes, transition directly to the preregistered House01/02/03 x seeds 0..9 OFF/ON closed-loop matrix; no intermediate House/seed-specific tuning.
6. Any post-V2 research version may use a truth-free coordinate/source equivalence quotient and observation-conditioned resolution gate, but it must be versioned separately from V2.
