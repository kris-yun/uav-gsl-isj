# RCEC V13 — Frozen candidate method and scientific boundary

Date: 2026-08-26  
Status: **FROZEN CANDIDATE FOR NEW-SEED QUALIFICATION**. Not yet a confirmatory success.

## 1. Why this version exists

The revealed V11 multiseed experiment did not show that inverse-causal and spatiotemporal evidence vanished. V11 improved 11/15 pairs and pooled error by about 9.08%, but failed the preregistered >=10% qualification threshold and contained one catastrophic regression. The failure mode is therefore a tail risk: one misspecified causal ranking can overwrite the native PMFS source state.

RCEC V13 keeps the validated V11 causal evidence and changes only how evidence from different views and different source-update times is admitted to the source state.

It deliberately does **not** use the rejected CTT HMM/count-survival path. The CTT trace recorder remains diagnostic infrastructure only and is not part of this frozen candidate.

## 2. M1 — ACIT: amplitude-conditioned inverse-transport causal views

M1 is the frozen V11 causal module. It consumes completed StopAndMeasure position/wind/hit events and candidate source coordinates. The 54 frozen nuisance members are unchanged:

- spread: {0.25, 0.5, 1.0};
- decay: {4, 8, 16};
- upstream penalty: {1, 2};
- slope: {0.5, 1, 2}.

The score conditions on the observed hit count, then forms disjoint even/odd normal-rank views `z_even,t(s)` and `z_odd,t(s)`.

The existing truth-blind identifiability rule is unchanged: both temporal folds must contain hit/miss contrast and hits must occur at at least two spatial grid locations. The cumulative V11 event reservoir is also unchanged.

M1 answers: **what source-relative causal evidence is supported by gas/wind observations under amplitude uncertainty?**

## 3. M2 — CREI: cross-view replicated evidence intersection

V11 allowed the causal channel to replace the source state even when it conflicted with the physical/native PMFS update. RCEC adds a separate robust cross-model view.

At source update t, `beginTADMUpdate()` freezes the normalized PMFS source state before the native source update. After native PMFS updates, for each candidate rectangle s compute

`d_native,t(s) = log M_after,t(s) - log M_before,t(s)`.

Only this **current native increment** is used; the absolute native posterior is not treated as fresh evidence. Convert it to candidate normal ranks `z_native,t(s)`.

Define the conjunctive consensus

`c_t(s) = min(z_native,t(s), z_even,t(s), z_odd,t(s))`.

This is intentionally **not** a Bayesian product and makes no independence claim among the three views. It is a lower-envelope generalized evidence operator: a candidate cannot receive a high consensus score if any one of the native/even/odd views strongly opposes it.

No fusion weight, temperature, learned reliability scalar, source truth, localization error, House label, or seed-specific parameter exists.

M2 answers: **is the candidate supported simultaneously by native PMFS change and both replicated causal views?**

## 4. M3 — TMEM: temporal median evidence memory

A turbulent realization may still corrupt one source update. RCEC stores the candidate-aligned CREI score from every identifiable update and uses

`m_t(s) = median{c_u(s): u <= t, u identifiable}`.

The median is defined for every available history size. There is **no extra three-update gate**:

- one snapshot -> that score;
- two snapshots -> midpoint of the two scores;
- three or more -> ordinary sample median.

From three snapshots onward the median can reject one arbitrary temporal score outlier; this is a property, not a tuned threshold.

The final generalized source state is rebuilt from the same fixed geometry-only prior used by frozen V11:

`q_t(s) proportional to q0(s) exp(m_t(s))`.

Historical generalized scores are summarized by an order statistic, not multiplied as repeated likelihoods; therefore TMEM does not recursively count the same cumulative observation history multiple times.

M3 answers: **has the cross-view source evidence remained stable across source updates rather than appearing in only one transient plume realization?**

## 5. Orthogonality of the modules

| Module | Layer | Failure addressed |
|---|---|---|
| ACIT | source/transport causal evidence | amplitude and inverse-transport ambiguity |
| CREI | cross-model evidence consensus | one misspecified causal view overriding PMFS |
| TMEM | temporal robustness | one transient source-update realization dominating the run |

CREI does not learn ACIT parameters. TMEM does not change CREI or ACIT parameters. Neither module changes the planner.

## 6. Runtime ablation contract

The same materialized binary supports all scientific arms through one environment variable while `pfdi_mode=me_aci` remains unchanged:

- `RCEC_V13_ARM=v11_stouffer`: A1, exact frozen V11 score path;
- `RCEC_V13_ARM=crei_latest`: A2, ACIT + CREI;
- `RCEC_V13_ARM=rcec_full`: A3, ACIT + CREI + TMEM.

If `RCEC_V13_ARM` is absent, behavior defaults to `v11_stouffer` for backward parity. Any unknown value is a hard failure.

Candidate IDs and order must remain identical across TMEM updates. Drift is a hard contract failure; history is never silently remapped.

## 7. Offline development evidence

The deterministic replay uses archived V11 candidate scores and exact PMFS candidate geometry. It first reconstructs the archived V11 posterior with maximum absolute error `8.257283745649602e-16`, establishing replay parity.

On all 15 currently revealed V11 pairs, the development-only final-state shadow results are:

| Arm | pooled improvement vs frozen OFF | improved pairs | catastrophes | worst pair |
|---|---:|---:|---:|---:|
| A1 V11 Stouffer | 9.08% | 11/15 | 1 | -38.09% |
| A2 ACIT + CREI | 13.35% | 13/15 | 0 | -11.36% |
| A3 ACIT + CREI + TMEM | **16.39%** | **15/15** | **0** | **+1.35%** |

A3 pooled improvement by House on this revealed development set:

- House01: 22.56%, 5/5 improved;
- House02: 10.16%, 5/5 improved;
- House03: 14.56%, 5/5 improved.

The previously catastrophic House01 seed653959 changes from approximately `4.608 m OFF -> 6.363 m V11` to `4.322 m` under the offline A3 reconstruction.

These results are **not confirmatory evidence**. Every one of these seeds is now development-visible. The replay is also off-policy with respect to a true RCEC closed loop: native increments were recorded on V11 trajectories/source states. The only legitimate next test is a new-seed runtime experiment after source and binary hashes are frozen.

## 8. Prohibited changes after freeze

Do not add or tune adaptive fusion weights, posterior temperatures, House/seed-specific rules, truth-distance gates, final-error gates, new ACIT nuisance members, planner parameters, minimum-history thresholds, or CTT HMM/count-survival terms.

If new-seed qualification fails, archive the failure. Do not rescue the seed.

## 9. Claim boundary

RCEC is a **generalized evidence-consensus source inference method**, not an exact Bayesian fusion rule. `min()` and the temporal median are robust decision operators. The scientific novelty claim is their source-localization use to prevent a replicated but misspecified inverse-causal channel from creating a catastrophic wrong basin while retaining V11's causal/spatiotemporal signal.
