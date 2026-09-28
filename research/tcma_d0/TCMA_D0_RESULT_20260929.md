# TCMA-D0 target-conditioned adequacy audit

Decision: **`TCMA_D0_NO_CROSS_HOUSE_TARGET_CONDITIONED_SIGNAL`**. Stop this frozen adequacy-percentile mechanism. Do not fit a router or revise the percentile on these OPEN targets.

## Frozen order and assets

The evaluator and adequacy calculation were committed before reading source-rank outcomes. All 482 target/operator adequacy rows, 42 source/operator summaries, and 88-member self-residuals were then committed separately as `8c0299eccef33e904c65c99a184b6a7048d7090f`. Its `TARGET_ADEQUACY.csv` SHA256 is `086d14a4f26f4cfd85ff7b3cf2b204706cc9754d106db30da879db91b5fd9d4b`. Only then were the frozen AEC-D0 source ranks joined. The evaluator itself was committed as `9d0fa7c8` before execution. The complete calculation and outcome join were repeated; six output files were byte-identical.

The 21 physical sources comprise four in House01, five in House02, and twelve in House03. House01/02 use 49 archived Native trajectories; House03 uses 12 sources × 8 target realizations × 2 paths. No new GADEN, PMFS forward, VGR, or training was run.

## Frozen gate

| House | Sources | Spearman(ΔA, ΔG) | Nonzero sign agreement | Fixed u mean rank | Fixed rawu mean rank | Adequacy selector mean rank |
|---|---:|---:|---:|---:|---:|---:|
| House01 | 4 | +1.000 | 3/4 | 242.00 | **231.56** | 233.63 |
| House02 | 5 | **0.000** | **2/5** | **75.30** | 75.75 | 76.43 |
| House03 | 12 | +0.606 | 9/12 | 115.46 | 116.43 | **112.68** |

House02 fails both the strictly positive rank association and sign-agreement gates. Its selector is worse than either fixed encoding. House01's selector is worse than the best fixed encoding. Only House03 shows a rank benefit. House02's leave-one-source-out association is negative for four of five omissions, so the result does not rest on a hidden robust cross-House effect. The preregistered conjunction fails; House03 cannot rescue it. The source-aware selector is an oracle diagnostic that uses the physical source ID, not an online decision rule.

## Interpretation limit

The frozen statistic also has a scale problem: target residuals use GADEN concentration values, while the self-residuals use PMFS filament-count-proxy vectors. Fitting a positive gain to the template does not make those **residual magnitudes** commensurate; rescaling target concentration changes `T` quadratically without changing the self-residual distribution `R`. Thus the empirical percentile cannot be read as a physically calibrated model-adequacy probability. We preserved the preregistered calculation and did not introduce a post-result unit correction. This issue strengthens the prohibition on using these values for routing; it is not used to re-label the numerical STOP as an infrastructure HOLD.

The targets and ranks were already OPEN in earlier work, so this is a mechanism audit, not fresh confirmation. The percentile is not a conformal p-value. H01/H02 Native trajectories also depend on past action. Do not infer that all target-conditioned adequacy methods fail; the tested frozen statistic fails its cross-House gate.
