# Persistent-Source PMFS V0 — mechanism finding

Date: 2026-09-26

## Status

This is a **development-only mechanism ablation**, not a main-innovation claim and not a closed-loop authorization.

## Native PMFS mechanism being isolated

The upstream PMFS `SimulationSource::getPoint()` redraws a source point inside a quadtree leaf every time a filament is emitted. Therefore a quadtree leaf hypothesis is simulated as a spatially moving/distributed emitter across one forward realization.

For gas-source localization, the physical source position is instead an episode-level persistent latent cause: it is unknown, but it does not jump to a new location for each emitted filament.

The same upstream forward simulation then compresses the result to a per-cell hit frequency and evaluates a product of per-cell fit terms. All cells in a leaf inherit the same leaf score.

## Existing R1 evidence motivating the ablation

Frozen House01/seed0 R1 uses 87 candidate leaves. In the official-PMFS arm:
- 82/87 leaves have area > 1 grid cell (94.25%);
- mean leaf area is about 7.20 cells;
- maximum leaf area is 25 cells;
- the truth-containing leaf is `quadtree_23_14_1_3`, i.e. 1×3 cells;
- its official-PMFS rank is 47/87.

Leaf area alone does not explain the score ordering (development Spearman area-vs-score about -0.22), so the ablation must change only the **persistence semantics**, not add an area correction.

## Scientific hypothesis

The old forward model conflates two different uncertainties:

1. `S`: source position uncertainty — persistent for the whole episode;
2. `Z`: plume/transport randomness — changes between realizations.

Native leaf simulation effectively redraws `S` repeatedly *inside* one realization.

The controlled alternative is

`source point S_m ~ Uniform(leaf)` **once**, then hold `S_m` fixed for the entire forward realization, and average the observation likelihood over persistent source samples and transport realizations.

This is not yet claimed as a novel theory. It is the smallest calculation that can falsify the proposed PMFS failure mechanism.
