# 04 — Source / Mismatch Subspaces (M3)

Source contrast: `D = [g_s − ḡ]`, `ḡ = Σ_s π⁻(s) g_s` (candidate prior mass from
the captured per-cell prior), cells with confidence > 1e-9, whitened by
`diag(conf)/σ²` (σ²=0.16 frozen).

Mismatch: M2 atoms (+ MOX) on the same confidence cells; rank frozen by fixed
95% cumulative energy (no truth, no final-error selection).

| house/update | rank D | rank B (95% energy) | ρ = \|Q_DᵀQ_B\|²_F/min(rD,rB) | identifiable |
|---|---|---|---|---|
| H01 U0 | 18 | 61 | 0.279 | yes |
| H01 U1 | 20 | 68 | 0.243 | yes |
| H01 U2 | 22 | 79 | 0.235 | yes |
| H03 U0 | 22 | 71 | 0.322 | yes |
| H03 U1 | 20 | 70 | 0.257 | yes |
| H03 U2 | 18 | 66 | 0.222 | yes |

`B = B_∥S + B_⊥S` (parallel = columns in span(D)); A4 uses only `B_⊥S`;
attribution confidence `α = 1−ρ` ∈ [0.68, 0.78].
