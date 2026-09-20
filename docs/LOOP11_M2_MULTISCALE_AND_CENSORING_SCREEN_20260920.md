# Loop 11 — M2 Search: Multiscale History and Censoring Semantics

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: two auxiliary routes screened; neither selected.

## A. Multiscale history integration

Remote anchor:
- NeurIPS 2025 — *Predicting partially observable dynamical systems via diffusion models with a multiscale inference scheme*.
  The paper targets partially observable long-memory physical systems and integrates history at fine resolution near the present and coarser resolution farther into the past.

GSL motivation:
- sparse intermittent plume observations are partially observable;
- short predictive windows may miss old source evidence.

### Offline proxy
Compared:
- short context: 5 s recent window;
- multiscale context: 5 s + 20 s + 60 s history summaries;
- same source-blind next-window predictor;
- fast-wind training, held slow-wind test.

### Result
Mixed, not a valid universal auxiliary.

Positive:
- H02 180 s wind/source ratio 0.137 -> 0.056, source identity remains 2/2.
- H02 240 s 0.078 -> 0.063.
- H03 180 s 0.120 -> 0.101.

Negative:
- H03 120 s source identity 2/2 -> 1/2.
- H03 240 s 2/2 -> 1/2.
- H01 240 s ratio worsens 0.139 -> 0.249.

Decision:
```
GENERIC_MULTISCALE_HISTORY_AS_M2 = NO_GO
```

Do not rescue with House-specific history scales.

## B. Censoring-aware / survival-analysis evidence

Remote-domain provenance is strong:
- ICML 2025 — *Survival Analysis via Density Estimation*: survival inference under right/dependent censoring with bounds under unknown dependence.
- AISTATS 2025 — *Survival Models: Proper Scoring Rule and Stochastic Optimization with Competing Risks*.
- Nature Machine Intelligence 2026 — *Transfer learning with deployment-covariate recalibration for survival prediction under covariate shift*.

Scientific mapping is attractive:
- finite mission horizon -> right censoring;
- first plume hit -> event time;
- no hit by T should not automatically mean “source impossible”.

However the project already contains a much stronger internal test:
`docs/CTT_H01_FINAL_OFFLINE_VERDICT_20260830.md`.

Frozen CTT evidence:
- native 0.2 s first-passage timing is genuinely source-informative;
- but the factorized neural model
  `P(F=t)=p_event * p_phase(t|event)`,
  `P(F=never)=1-p_event`
  failed the preregistered source-evidence gate.
- full first-passage neural evidence did not beat survival-only and destructive temporal controls did not produce the required source gain.

Therefore:
```
RIGHT_CENSORING_SEMANTICS = SCIENTIFICALLY VALID
SURVIVAL/FIRST_PASSAGE_AS_NEW_M2 = INTERNAL_COLLISION / NO_GO
```

It can remain a correctness rule for handling no-hit observations, but it cannot be sold as the new auxiliary innovation without new physical data coverage.

## C. Current architecture status

M1:
- Predictive latent physical representation — ACTIVE PRIMARY.

M2:
- OPEN.
- η weighting: no-go in current form.
- generic multiscale history: no-go.
- handcrafted event features: no-go.
- censoring/first-passage: scientifically correct but already internally spent/no-go as a source module.
- direct nuisance alignment: no-go.

M3:
- structured shift-aware source region — ACTIVE CANDIDATE.

## D. Next M2 search rule

Stop searching for another temporal-statistics variant.

Next M2 must target a distinct layer:
1. reconstruct a physically meaningful intermediate state from sparse predictive latents; or
2. preserve an identifiable physical mechanism that PMFS probability maps currently destroy.

The next remote-domain candidate is state-first inverse inference / intermediate physical states, anchored by Nature Machine Intelligence 2025/2026.
