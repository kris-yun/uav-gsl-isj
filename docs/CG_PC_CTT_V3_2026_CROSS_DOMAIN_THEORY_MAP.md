# CG-PC-CTT V3 — 2026 cross-domain theory-to-equation map

Purpose: every borrowed scientific idea must map to one project failure, one equation/contract, and one executable module. Similarity of vocabulary is not sufficient.

| 2026 source field | 2026 scientific principle | GSL failure it addresses | Project equation / contract | Code object |
|---|---|---|---|---|
| Nature Biomedical Engineering — geometry-aware EEG/MEG source imaging | Constrain an ill-conditioned source inverse problem by the physical geometry of the source domain | candidate IDs / quadtree aliases are not physical source states; global rank ignores local geometry | `S0 = S_id / ~coord`; local geometry graph; optional `F_i = E_{m!=n}[J_im^T W^2 J_in]` | `observation_quotient_gate.py`, `local_pair_audit.py` |
| Nature — OSDR tissue dynamics from a spatial snapshot | A sparse spatial observation can encode dynamics if it contains a marker with temporal meaning | too few UAV spatial stops / early trajectory has weak source resolution | `Y_e=[mean(log1p c), sd(log1p c), hit fraction, within-stop slope]` | `block_dynamic_marker.py` |
| Nature Communications — host-aware intrinsic biopart identification | Separate intrinsic object parameters from host/context effects using a context-conditioned mechanistic digital twin | shared wind/context variation can dominate source-specific effect | `Y=b(R)+delta(R,S)+eps`; proximal residual moment `E[g(Z,S){Y-b(R)-h_delta(R,S)}]=0` | planned host-aware bridge; `qualify_bridge_causal_contract.py` freezes valid R/Y/Z first |
| Nature Communications — Celcomen spatial causal disentanglement | Explicitly disentangle internal and inter-environment/spatial programs before counterfactual perturbation prediction | source effect, transport context and sensor response are entangled in one score | source-specific `S` channel separated from context `R` and latent transport `U`; no oracle context labels | causal data contract + residual bridge |
| Nature Biotechnology — TxPert | Compare predictions to split-half experimental reproducibility; use context-matched controls | one noisy source ordering can look convincing | even/odd accepted-event folds must agree on source-vs-rival ordering before posterior release | `reversible_rank_posterior.py` + V3 split-half release condition |
| Astronomy — field-level weak-lensing inference | Inference compares the actually observed field to forward-modelled fields and validates calibration/coverage | full 626-cell M1 field claims information the UAV has not observed | observation operator `z_{s,m,e}=H_e phi_{s,m}`; only actual visited space-time support enters current resolution | `observation_quotient_gate.py`, `sparse_observation_stress.py` |
| npj Digital Medicine / Nature Biomedical Engineering digital twins | Initialize from limited measurements and update/personalize as data accrue; infer latent state rather than force early certainty | early GSL data are too sparse for precise point localization | observational quotient `Q_e=S0/~e` starts coarse and splits as evidence arrives; no false precision | `observation_quotient_gate.py` |
| 2026 spatiotemporal proximal causal inference | Hidden spatiotemporal nuisance can be handled with treatment/outcome proxies under exclusion + completeness + bridge moment restrictions | unresolved plume realization U confounds candidate source evidence | operational moment `E[g(Z,S)(Y-h(R,S))]=0`, with project-specific exclusion audit; no claim of general theorem | V15 sieve-GMM bridge + `qualify_bridge_causal_contract.py` |

## Supporting caution, not counted as a new 2026-origin idea

`Systema` appears in Nature Biotechnology volume 44 (2026) but was published online in August 2025. It is therefore used only as supporting evidence for the design rule “remove systematic/common variation before evaluating perturbation-specific effects”, not advertised as a newly published 2026 method.

## Binding discipline

1. No borrowed paper is cited merely because terminology sounds similar.
2. The original paper's theorem/equation is not claimed to transfer unless its assumptions are actually satisfied here.
3. Each cross-domain idea enters as a project-specific mechanism whose own GSL evidence must be established.
4. The paper may claim a cross-domain scientific transfer only after held-out H02 and closed-loop multi-seed evidence supports the resulting GSL mechanism.
