# CSTAR correction note — strict committor terminology and load-bearing M1 path

Date: 2026-09-06
Status: authoritative addendum to the first theory freeze.

Two implementation-level corrections were found during model self-review before any experiment. They are scientific corrections, not result-driven tuning.

## 1. M1 causal representation must be on the source-posterior path

The first executable PICR skeleton initially allowed the candidate scorer to read the unconstrained temporal hidden state directly while also exposing a nuisance-constrained `zS` head. That architecture would permit a degenerate failure: `zS` could look invariant while the actual source posterior bypassed it through transport-correlated hidden features.

This is now forbidden and the code has been changed. The source logits may use only:

- the nuisance-constrained `source_representation zS`; and
- known candidate-relative physical context derived from the causal wind/pose history and candidate coordinate.

`zN` and the unconstrained temporal hidden state cannot directly bypass `zS` into the source score. Therefore intervention invariance is load-bearing for the actual M1 output rather than an auxiliary decorative loss.

Any future architecture change must preserve this dependency rule and demonstrate it in a destructive ablation.

## 2. Strict committor terminology

In transition-path theory the committor is a probability of reaching a target set before the competing return/termination set. Therefore the horizon-wise cumulative vector must not all be called “the committor”.

CSTAR V2 terminology is:

- `first_hit_prob[j] = P(T=j)` for j=1..H, plus terminal `P(T>H)`;
- `encounter_cdf[h] = P(T<=h)` — the first-passage cumulative distribution;
- `route_committor = P(T<=H) = 1-P(T>H)` — probability of reaching the gas-encounter set before the planned route/horizon terminates.

The route-termination event is the competing absorbing outcome for this finite-horizon planning problem. This is the quantity directly analogous to the committor idea transferred from rare-event chemical physics.

PHS continues to use the full first-passage categorical law, not only the scalar route committor, because timing differences between competing source hypotheses are informative.

## 3. Superseded wording

Where earlier CSTAR theory/implementation documents say a length-H `committor` vector, read it as `encounter_cdf`; add the scalar `route_committor` defined above. The machine-readable `CSTAR_INTERFACE_CONTRACT.json` V2 and current executable references are authoritative for code.
