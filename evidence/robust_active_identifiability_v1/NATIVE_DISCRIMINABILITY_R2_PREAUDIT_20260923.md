# Native discriminability is not real identifiability: R2 active-design pre-screen

Date: 2026-09-23

Status: **NATIVE DISCRIMINABILITY GATE FAILS**

## Question

Before designing an active-sensing method, test the necessary mechanism:

> If the robot preferentially samples cells where the current PMFS candidate forward fields disagree most, do those cells actually carry more truth-source identity in the real observation map?

This is a source-blind pre-screen. Truth coordinates are used only after the cell-selection rule and candidate scores are frozen.

## Data and frozen score

Authoritative R2 final banks, House01-03 seed0-1.

- candidate set: terminal quadtree leaves only;
- cell discriminability: variance of simulated hit probability across terminal candidates;
- primary virtual design budgets: top 5%, 10%, and 20% of the already-supported cells by candidate variance;
- score after selection: unchanged Native PMFS per-cell agreement product, restricted to selected cells;
- no posterior temperature, no fitted coefficient, no truth-aware cell selection.

Because the context bank stores candidate values only on the already-supported region, this is deliberately an optimistic retrospective mechanism test, not yet a counterfactual trajectory experiment.

## Results

| case | terminal candidates | Native/all-support truth-owner rank | top 5% discriminability | top 10% | top 20% |
|---|---:|---:|---:|---:|---:|
| H01 seed0 | 123 | 81.0 | 96.5 | 97.5 | 98.0 |
| H01 seed1 | 121 | 90.0 | 99.5 | 101.0 | 103.0 |
| H02 seed0 | 123 | 109.5 | 101.0 | 103.0 | 102.5 |
| H02 seed1 | 119 | 107.5 | 105.5 | 107.0 | 107.5 |
| H03 seed0 | 160 | 112.0 | 131.0 | 132.0 | 133.0 |
| H03 seed1 | 160 | 109.0 | 129.5 | 132.5 | 133.0 |

Only H02 seed0 shows a modest improvement. The remaining cases are unchanged or materially worse; H03 becomes dramatically worse.

## Independent-realization stability of the discriminability map

The failure is **not** because the candidate-variance map is Monte-Carlo noisy.

Using cells and terminal candidate IDs common to the two independent seeds of each House:

| House | common terminal candidates | common cells | Spearman variance-map seed0 vs seed1 | top-10% cell overlap |
|---|---:|---:|---:|---:|
| H01 | 55 | 221 | 0.9957 | 95.7% |
| H02 | 80 | 268 | 0.9999 | 100% |
| H03 | 144 | 250 | 0.9996 | 100% |

Thus PMFS has a very stable internal notion of *where its own candidate models separate*. That notion is nevertheless misaligned with real truth-source evidence.

## Direct source-update locations

As a sanity check, the five actual source-update robot locations were mapped back to final-grid cells and their candidate-variance percentile was measured. Several late stops already fall in high-discriminability regions (e.g. H02 seed0 updates 3-5 are ~92-96th percentile), yet the truth-source rank remains poor. Restricting scoring to the five direct stop cells does not produce a robust rescue across Houses.

## Mechanistic conclusion

**Stable simulator discriminability is not the same as real-world identifiability.**

A conventional active policy that maximizes entropy, candidate variance, or expected separation under the Native PMFS forward family is likely to *actively amplify model bias*. This explains why simply importing generic active sensing / information gain is not a defensible main innovation.

The only active-design direction still scientifically alive is stronger:

> **misspecification-aware active identifiability**: choose observations that are both source-discriminative and supported by evidence that the corresponding forward physics is trustworthy under model-reality gap.

This aligns with 2025 robust optimal experimental design work that explicitly treats misspecified inverse-problem components, rather than assuming the forward model used by the design objective is correct.

## Hard boundary for the next step

Do not tune a new cell-weight formula on these six cases.

The next test must define an outcome-blind reliability signal *independently* of truth-source rank, and then ask whether a robust discriminability criterion recovers source identity. If the reliability signal is derived from the same candidate-vs-observation residual and optimized after seeing truth, it is only another scoring patch and should be rejected.
