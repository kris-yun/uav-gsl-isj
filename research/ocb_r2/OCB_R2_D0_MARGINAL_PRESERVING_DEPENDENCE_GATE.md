# OCB-R2 D0 — Marginal-Preserving Dependence Gate

Date: 2026-09-29

Status: **PREREGISTERED DISCOVERY-ONLY / NOT EXECUTED**

Prerequisites already passed:

- `OCB_R2_GENERATOR_REFOUNDATION_PASS`
- `OCB_R2_S1_H12_STRUCTURAL_PASS`
- `OCB_R2_S2_DISCOVERY_DATASET_PASS`

Frozen prospective generator SHA256:

`ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`

This phase may use only the qualified 32-run H01/H02 discovery partition.
H01/H02 confirmation and House03 remain sealed.

## 1. Scientific question

The old dependence-layer work showed a development-set cross-time signal after
preserving complete each-time marginals, but the complete spatial marginal
field was itself substantially stronger than the compressed 10-D count
trajectory.

Therefore D0 must **not** replace spatial marginal evidence with a count-only
joint model.

The question is:

> After preserving the strongest complete spatial marginal source evidence,
> does source-conditioned cross-time dependence contribute additional source
> discrimination on the new OCB-R2 prospective stochastic realizations?

The intended doctrine is:

`keep robust marginals -> destroy only dependence -> measure what is lost -> add dependence only if incremental`

No posterior fusion coefficient is fitted in D0.

## 2. Cross-domain theory lineage

Primary mother idea:

David Huk and Theodoros Damoulas,
**Diffusion and Flow-based Copulas: Forgetting and Remembering Dependencies**,
ICLR 2026.

Official proceedings:
https://proceedings.iclr.cc/paper_files/paper/2026/hash/41ca8a0eb2bc4927a499b910934b9b81-Abstract-Conference.html

Transferable principle:

> progressively forget dependence while leaving dimension-wise distributions
> unchanged, then learn only the missing dependence.

Practical density-ratio anchor:

David Huk, Mark F. J. Steel, Ritabrata Dutta,
**Your copula is a classifier in disguise: classification-based copula density
estimation**, AISTATS 2025.

Official proceedings:
https://proceedings.mlr.press/v258/huk25a.html

D0 does **not** train a diffusion model or claim a unique Bernoulli copula.
It tests the scientific object first.

## 3. Historical evidence boundary

The following prior result is motivation only:

`DEPENDENCE_D0_CROSS_TIME_SIGNAL`

from branch:

`research/dependence-layer-d0-v2-20260926`

That result used an older OPEN 18-source / 16-realization bank and a 10-D count
trajectory Energy Score. It must not be presented as OCB-R2 confirmation.

The old result also showed why the new test must change:
full 300-D marginal Brier evidence was stronger than the count-only RAW score.

The prior MPDI preregistration on
`research/marginal-preserving-dependence-v0-20260928` was **not executed**.
This D0 reuses only its scientifically useful principle on the new prospective
OCB-R2 discovery bank.

## 4. D0A hard preflight — source-comparison comparability

Before any scientific score is computed, establish the exact source-comparison
contract.

For every target observation, all candidate source hypotheses compared against
that target must have identical non-source conditioning:

- House / geometry
- occupancy asset
- wind asset and wind-state timeline
- gas type
- observation coordinates
- observation times
- readout definition
- generator/timebase semantics

A configuration label that changes wind together with source is **not** a valid
source-identification class by itself.

### D0A required decision

If at least two source hypotheses can be compared under the same frozen
non-source conditions using provenance-compatible existing assets, report:

`OCB_R2_D0A_SOURCE_COMPARABILITY_PASS`

If the qualified S2 data alone do not provide this, first check whether the
existing read-only PMFS/candidate forward bank can provide source-conditioned
candidate evidence under the same wind/geometry without generating new plume.

If neither route is provenance-compatible, report:

`OCB_R2_D0A_SOURCE_COMPARABILITY_HOLD`

and STOP before scoring.

Do not generate extra plume or silently pair different wind fields merely to
create source classes.

## 5. Observation representation preflight

The primary representation must retain full spatial information.

Preferred route:

reuse the frozen earlier dependence contract only if its 10 times x 30 spatial
probes map exactly and source-blindly onto the OCB-R2 H01/H02 assets.

If exact transfer is not possible:

- do not choose new probes after looking at source-discrimination results;
- stop and preregister a deterministic geometry-derived probe/time contract in
  a separate commit before scientific scoring.

Forbidden primary representation:

- 10-D encounter-count trajectory alone;
- globally normalized amplitude-only summaries;
- source/result-selected probes;
- source/result-selected time points.

Binary encounter fields may be used as the primary D0 readout if the fixed
threshold/readout contract is inherited without result-driven tuning.

## 6. Discovery cross-fitting

Each qualified OCB-R2 discovery configuration has four frozen stochastic
realizations.

If the D0A comparison contract supports source-conditioned ensembles, use
leave-one-realization-out discovery evaluation:

- one target realization;
- the other three frozen discovery realizations as reference ensemble;
- repeat for all four targets.

Thus the nominal reference budget is `K=3`.

This is intentionally a low-K **discovery** test only. It is not independent
confirmation and must be described as such.

No confirmation realization may be generated/opened to increase K.

## 7. M0 — complete marginal evidence

For each candidate source s and target y, compute the full fixed spatial
marginal evidence over the complete preregistered time x probe field.

For a binary encounter field, freeze a proper marginal score such as the
complete coordinate-wise Brier loss:

`M0_s(y) = mean_{t,q} (y[t,q] - p_hat_s[t,q])^2`

where `p_hat_s[t,q]` is estimated only from the reference realizations.

Lower is better.

Do not compress `M0` to timewise counts.

Record:

- true-source rank
- strongest wrong candidate
- score margin
- top1/top3 when candidate count permits
- source/House/wind strata

M0 is the evidence that the dependence layer is not allowed to erase.

## 8. P versus Q-time — dependence intervention

For candidate source s, let `P_s` be the intact reference realization tensors.

Construct `Q_time,s` by independently permuting whole spatial snapshots
across reference realization labels at each frozen time.

This must preserve exactly:

- every empirical coordinate marginal;
- the complete empirical spatial snapshot set at each time;
- all per-time support/count information.

It destroys only which snapshots belong to the same stochastic realization
across time.

All preservation assertions are hard gates.

Use a fixed surrogate RNG seed committed before execution.
With K=3, sample a fixed preregistered number of surrogate banks (default 500)
or exhaustively enumerate if the implementation proves the finite set is
tractable. Do not change this based on results.

## 9. Dependency residual diagnostic

Using the same fair U-statistic Energy Score on the **full fixed tensor
representation**, not the 10-D count compression, compute:

`ES(P_s, y)`

and for each Q-time surrogate:

`ES(Q_time,s^(b), y)`

Define:

`R_s(y) = median_b [ ES(Q_time,s^(b),y) - ES(P_s,y) ]`

Higher `R_s(y)` means the target benefits more from the intact cross-time
pairing for that same candidate source.

D0 does not add `R_s` to M0 and does not fit a mixing coefficient.

## 10. Incremental diagnostic against M0

For each target, let `c(y)` be the strongest wrong source candidate under M0.

Define:

`G_D(y) = R_truth(y) - R_c(y)`

Report separately:

- M0-error targets: does dependence point toward truth?
- M0-correct targets: does dependence remain compatible rather than
  systematically oppose the correct marginal decision?

Also report:

- per-House
- per-wind/regime
- per-source
- per-realization
- leave-one-configuration-out summaries

Do not aggregate away a House/configuration reversal.

If M0 makes too few errors to judge correction behavior, report that explicitly
as insufficient discovery support rather than manufacturing a stronger claim.

## 11. Destructive controls

At minimum:

1. source-label permutation for the residual ranking;
2. replace the intact P reference with Q-time before forming the supposed
   intact residual;
3. target-time-order permutation as a diagnostic.

A valid cross-time source-conditioned residual should lose its advantage under
controls 1 and 2.

## 12. Frozen D0 decisions

### `OCB_R2_D0_DEPENDENCE_INCREMENTAL_POSITIVE`

Use only if all are true:

1. D0A source-comparability PASS;
2. all marginal-preservation assertions PASS;
3. residual source discrimination beats its destructive source-label null;
4. direction is consistent across both H01 and H02 rather than one House only;
5. direction is not explained by one source/configuration/seed;
6. on available M0-error targets, `G_D` predominantly points toward truth;
7. on M0-correct targets, residual is not systematically truth-opposing;
8. Q-time destructive control removes or materially attenuates the advantage;
9. no fixed stratum shows a strong reversal that is hidden by pooling.

This licenses method construction only. It is not a paper-level confirmation.

### `OCB_R2_D0_DEPENDENCE_PRESENT_NOT_INCREMENTAL`

Use if dependence is detectably source-conditioned but does not improve the
information missing from M0, especially if it fails to help M0 mistakes.

Stop this dependence mainline rather than replacing a stronger marginal model.

### `OCB_R2_D0_NO_DEPENDENCE_SIGNAL`

Use if the prospective discovery bank does not reproduce a stable
source-conditioned cross-time residual.

Stop.

### `OCB_R2_D0_HOLD_COMPARABILITY`

Use if source candidates cannot be compared under identical non-source
conditioning, or the probe/time/readout contract cannot be transferred
source-blindly.

Stop and redesign the observation contract before any method claim.

## 13. What a positive D0 would license

Only after `OCB_R2_D0_DEPENDENCE_INCREMENTAL_POSITIVE`:

freeze a method-development stage based on the probability factorization idea

`log p_s(y) = log q_s(y) + log r_s(y)`

where:

- `q_s` preserves the strong source-conditioned marginal evidence;
- `r_s` models only the dependence density ratio against a
  marginal-preserving/dependence-destroyed reference.

First implementation candidate should be the simpler classifier-based
density-ratio route motivated by AISTATS 2025.

Only if that confirmed residual cannot be represented adequately should the
ICLR 2026 diffusion/flow copula machinery be considered.

Do not use model scale as a substitute for a failed D0 mechanism.

## 14. Seals and stop boundary

Throughout D0:

- H01/H02 confirmation remains unopened/unrun;
- H03 remains `SEALED_NOT_RUN`;
- no closed loop;
- no result-driven seed replacement;
- no new GADEN data unless a later separately approved protocol requires it;
- no method freeze until D0 itself is complete.

Required outputs:

- `research/ocb_r2/d0/D0A_SOURCE_COMPARABILITY_AUDIT.md`
- `evidence/ocb_r2/d0/D0_OBSERVATION_CONTRACT.json`
- `evidence/ocb_r2/d0/D0_MARGINAL_PRESERVATION_CHECKS.tsv`
- `evidence/ocb_r2/d0/D0_TARGET_RESULTS.tsv`
- `evidence/ocb_r2/d0/D0_STRATIFIED_RESULTS.tsv`
- `evidence/ocb_r2/d0/D0_DESTRUCTIVE_CONTROLS.tsv`
- `research/ocb_r2/d0/OCB_R2_D0_RESULT.md`

STOP after the D0 decision. Do not generate/open confirmation or H03.
