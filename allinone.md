# 2026 causal-theory search for PMFS CORE-M1

Search window: 2026. Queries covered adaptive interventions, sequential
decision-making, nuisance invariance, interventional contrast and causal
representation learning. The local multi-source search returned 106 unique
records (arXiv 24, OpenAlex 36, Semantic Scholar 24, Crossref 36; 14 duplicates
merged); DBLP and OpenReview returned no hits for the broad query. Semantic
Scholar repeatedly returned HTTP 429 for one query, arXiv had one SSL EOF, and
DBLP returned JSON parse errors. Manual checking against first-party publisher
pages retained the three records below; 103 clearly unrelated or non-venue
records were filtered out.

| # | Title | Date | Venue | Why retained | Source |
|---|---|---|---|---|---|
| 1 | Toward Interpretable Deep Generative Models via Causal Representation Learning | 2026-04 | JASA 121(553) | Current top-journal synthesis of intervention, latent representation and identifiability boundaries | <https://doi.org/10.1080/01621459.2026.2620154> |
| 2 | Intervening to learn and compose causally disentangled representations | 2026-04 | CLeaR 2026, PMLR 323 | Context-separated intervention mechanism plus an identifiability result | <https://proceedings.mlr.press/v323/markham26a.html> |
| 3 | Partial Causal Structure Learning for Valid Selective Conformal Inference under Interventions | 2026-08 | UAI 2026, PMLR 337 | Learns only task-relevant intervention-target relations and quantifies invariance-set errors | <https://proceedings.mlr.press/v337/asiaee26b.html> |

## Overview

The relevant 2026 literature does not provide a ready-made gas-localization
estimator. It consistently requires explicit interventions, explicit invariance
or context assumptions, and a sharply bounded identifiability claim.

## Trends

The shift is from attaching causal language to predictive robustness toward
finite-sample, intervention-indexed claims with explicit failure conditions.
Specialized causal-learning venues and top statistics journals emphasize that
heterogeneity helps only when the preserved or changed mechanisms are stated.

## Key themes

1. Interventions provide extra structure, but do not remove the need for
   assumptions (1, 2).
2. Context separation can isolate intervention-responsive factors (2).
3. Partial, downstream-specific causal structure is more defensible than a
   universal causal graph claim (3).

## Keywords frequency

| Keyword | Count |
|---|---:|
| causal | 3 |
| intervention | 2 |
| representation | 2 |
| identifiability | 2 |
| invariance/context | 2 |

## Most cited by accepted paper

Fresh 2026 citation counts are too immature and inconsistent across indexes to
rank responsibly; venue and methodological fit are used instead.

## Most cited by first author

Not reported because the 2026 citation window is incomplete and would be
misleading.

## Recommendations for reading

Read Moran and Aragam first for the claim boundary, Markham et al. for the
intervention/context construction, then Asiaee et al. for falsification of an
incorrect invariance set. CORE-M1 uses these principles but relies on its own
task-specific log-odds cancellation proposition and closed-loop validation.

