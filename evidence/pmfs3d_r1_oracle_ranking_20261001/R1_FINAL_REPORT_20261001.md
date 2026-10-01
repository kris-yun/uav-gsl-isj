# PMFS3D-R1 Oracle ranking result — 2026-10-01

Decision: **PMFS3D_R1_HOLD_RANK_NONINFERIORITY (HOLD)**. Execution stopped.

## Pre-scoring freeze

Branch: `research/pmfs3d-r1-oracle-ranking-20261001`.
Asset-audit commit: `93b73031`. Prototype commit: `c928082d`.
Gate and final contract commit, pushed before any historical Oracle forward:
`77d003a3b9090b9313390be5c79b69cdcbdeb1c3`.
Amendment SHA256: `81e2a00b636bb0659487e7638475f1b22e67e2226894f221a135a3e267b8c22f`.

Primary control is Oracle-3D versus Oracle-2D with the same static CFD state0 assets.
Native uses historical GMRF wind and is a secondary reference.

## Four-case results

Ranks are active-leaf midranks; ties are explicitly retained. Larger log likelihood is better.
Margin = truth-owner log likelihood minus the strongest wrong leaf.

| Case | Active leaves | Native rank | Oracle-2D rank | Oracle-3D rank | Delta margin | H2D | H3D | H2D-H3D |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| House01_seed0_off_off | 123 | 81 | 75 | 100 | +26.252943 | 2.326379 | 1.209087 | +1.117292 |
| House01_seed1_off_off | 121 | 90 | 102 | 100.5 | +3.989296 | 1.029963 | 2.343236 | -1.313273 |
| House02_seed0_off_off | 123 | 109.5 | 104 | 105 | +41.574026 | 0.000000 | 1.480442 | -1.480441 |
| House02_seed1_off_off | 119 | 107.5 | 107.5 | 105 | +33.558692 | 0.554357 | 0.541425 | +0.012933 |

## Frozen gate decision

- Margin: **PASS** — 4/4 positive; median delta margin = 29.90581740040632.
- Median-rank noninferiority: **PASS** — 103.00 -> 102.75.
- Rank anti-regression: **FAIL** — 2 worsened cases; allowed maximum was 1.
- Combined rank gate: **FAIL**. Therefore final **HOLD**, not PASS.
- Recall@1 and Recall@5 are 0/4 in all three arms.
- Mean ranks: Native 97.000; Oracle-2D 97.125; Oracle-3D 102.625.
- Entropy is descriptive, decreases in 2/4 and increases in 2/4; it cannot rescue the decision.

## What the margin gain means

All four Oracle-3D truth log scores are exactly equal to their Oracle-2D truth log scores.
Consequently, the positive delta margins arise entirely from lower scores for the
strongest wrong candidates, rather than higher unnormalized truth likelihood.
Truth templates are not globally zero. The independent audit records how many
predicted-hit cells intersect cells with positive observation confidence.
This is a post-result explanation of the saved outputs, not a new scoring rule or gate.
All truth-versus-best-wrong margins remain negative, and truth ranks remain poor.
The result establishes no successful source localization or calibrated posterior.

## Integrity and runtime

Both complete computations have byte-identical forward maps, scores, probability maps
and evaluation JSON. Actual local files were independently hashed against the repeat manifest.
The independent Python/Numpy audit recomputed every candidate log score from saved hit maps
and the frozen measured probability/confidence; max error is below 1e-9. It also verified
all ranks, margin differences, normalization, entropy and the exact final gate decision.
Native replay matches all 130,853 historical alignment entries exactly.
Native posterior differs from archived posterior only at floating point roundoff (<1e-10).
Protected inputs and Oracle asset hashes were unchanged.

24 offline forward executions = 4 cases x 3 arms x 2 repeats.
Recorded total forward runtime: 91.496 s.
New GADEN runs: 0. Training runs: 0. Closed-loop runs: 0.
H03 and confirmation were not opened.

## Scope and stop boundary

These are four historical terminal source-update replays (roughly 274-280 s),
not four new plume realizations or a fresh closed-loop comparison. Candidate support
is the original 119-123 quadtree leaves and 626/631 free cells. H02 truth belongs to
a 5x1 leaf, so exact-point localization within that leaf is unresolved.
Known release height, static CFD state0, point-filament sensor-layer hit definition,
3D voxel collision and vertical noise are all part of the preregistered prototype.
Thus the experiment compares complete forward operators, not w alone.

HOLD does not identify PMFS aggregation as the cause, authorize a fusion model, or
invalidate the earlier O0 field-pattern observation. No scorer, candidate, seed,
physics parameter or gate was changed after scientific scoring. No follow-up run started.

## Evidence

- `R1_RESULT.json`: all case and arm metrics.
- `CASE_METRICS.tsv`: concise paired table.
- `PREFORWARD_FREEZE.json`: exact committed code/input hashes.
- `DETERMINISTIC_REPEAT.json`: per-file hashes for both complete computations.
- `INDEPENDENT_RESULT_AUDIT.json`: independent recomputation and Native parity.
- `PMFS3D_R1_SCIENTIFIC_20261001/`: both forward banks and evaluated probability maps.
- `research/pmfs3d_r1/R1_FORWARD_CONTRACT_FINAL.md`: frozen physics and gates.
Full forward maps and selected historical CSV inputs are included in the review ZIP,
rather than committing thousands of binary files to Git. Original large CFD assets
and runtime libraries remain on the VM; their paths and hashes are recorded.
