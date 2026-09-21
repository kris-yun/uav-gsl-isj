# TNQC VGR 300-s correction and required offline gate
Date: 2026-09-20

## Correction

The Orebro3DSEN 2/5/10-min experiments are **not** the project-level offline gate for TNQC.

They test only whether a quotient/canonical representation carries repeated-source identity in an independent measured sensor array. They do **not** evaluate the project endpoint:
- VGR/GADEN House01/02/03;
- matched PMFS localization task;
- 300 s budget;
- final source localization error;
- PMFS primary metric `ExpectedValue(sourceProbability, 0.05)`.

Therefore Orebro AUC/LOCO numbers must not be used to say that TNQC is already localization-positive.

## Correct target metric

For each House/seed pair, the endpoint is

[
E_{300}=left\|\operatorname{ExpectedValue}(P_{300},0.05)-s^*\right\|_2,
]

where (P_{300}) is the source posterior at the end of the frozen 300-s budget and (s^*) is evaluator-only source truth.

The main paired development set remains:
- House01 seed0/1;
- House02 seed0/1;
- House03 seed0/1.

The existing frozen reference matrix for the prior ME-ACI V10 work is shown below **only as a historical first-identifiable-intervention snapshot**. These values were evaluated at the first accepted ME-ACI source update (72.851–217.811 simulation seconds depending on case), not at the final 300-s endpoint:

| House | seed | native PMFS top-5% error m | ME-ACI V10 top-5% error m |
|---|---:|---:|---:|
| H01 | 0 | 5.152589 | 2.501097 |
| H01 | 1 | 6.928495 | 5.006343 |
| H02 | 0 | 2.926781 | 2.271832 |
| H02 | 1 | 1.813416 | 1.307146 |
| H03 | 0 | 6.652648 | 2.863832 |
| H03 | 1 | 5.219942 | 2.982003 |

Those values must **not** be used as the 300-s baseline for TNQC and must not be mixed into the VGR 300-s gate. They are historical ME-ACI development evidence only. The new TNQC gate regenerates native PMFS trajectories through the full 300-s budget and evaluates the last source posterior at or before that budget.

## Required offline TNQC gate before Codex closed loop

The intended offline test is a **fixed-trajectory VGR replay to 300 s**, not a 5/10-min classifier.

For each of the six frozen VGR House/seed runs:

1. keep the historical robot trajectory and measurement stream fixed;
2. keep the PMFS candidate transport simulation contract fixed;
3. replay source-posterior updates using:
   - native PMFS score;
   - TNQC shadow diagnostics;
   - TNQC fused score;
4. do not let the replayed TNQC posterior change the historical trajectory;
5. evaluate the final 300-s top-5% expected-location error against evaluator-only truth.

This is a counterfactual inference replay. It answers whether TNQC improves source inference on the **actual VGR localization data** before spending a full closed-loop batch. It is not yet a closed-loop result because planning remains fixed.

### Offline GO criterion

TNQC may proceed to a new closed-loop batch only if the fixed-trajectory VGR replay shows:
- pooled final 300-s top-5% error lower than native PMFS;
- at least 4/6 paired cases improve;
- no catastrophic false-confident collapse;
- the effect is not created by source truth, candidate rank, or a post-hoc fitted fusion parameter.

A 10% pooled improvement is the preferred development GO threshold. If the signal is weaker or mixed, TNQC remains unconfirmed and must not be sent to closed loop as a validated candidate.

## Data availability note

The repository contains extensive VGR/GADEN House evidence and the historical 6-case reference archive, including hashes for context-bank / candidate / event artifacts. The 5 MB ME-ACI evidence ZIP is binary, and the current chat execution environment cannot directly unpack that archive through the GitHub text connector. The authoritative VGR raw scenarios are also referenced on the VM under `/mnt/hgfs/workspace/GADEN_files/scenarios/House01|02|03`.

Therefore the next implementation task is to expose/materialize the required fixed-trajectory candidate-field artifacts from the existing VGR archive or regenerate them read-only from the frozen VGR scenarios, then run the 300-s counterfactual replay above.

## Status

**Orebro: auxiliary external representation evidence only.**
**VGR 300-s offline localization signal: not yet established.**
**Closed loop: HOLD.**


---

## Implemented fixed-trajectory replay — 2026-09-20

The required House-level offline gate is now implemented in the repository.

### Files

- `reference/tnqc_vgr_fixed_trajectory_replay.py`
- `reference/aggregate_tnqc_vgr_offline_gate.py`
- `reference/run_tnqc_vgr_offline_gate_20260920.sh`
- `reference/test_tnqc_vgr_fixed_trajectory_replay.py`

### Why the existing context-bank export is sufficient

A native PMFS update already exports, for every evaluated quadtree source
candidate:

1. the candidate rectangle and native score in `candidate_manifest.csv`;
2. measured probability/confidence and the same candidate's simulated hit
   probability at every supported free cell in
   `candidate_support_alignment.csv`;
3. the exact measured log-odds field in `measured_hit_probability.csv`;
4. the normalized native source posterior in `source_posterior.csv`;
5. source-update simulation time in `source_update_timing.csv`.

Therefore no source truth and no TNQC-generated trajectory are needed to test
the TNQC likelihood itself on VGR.  The native run supplies the frozen
trajectory and frozen PMFS candidate bank.

### Replay equations

For each native candidate (s), the replay reconstructs the native PMFS
likelihood in log space from the exact current PMFS cell score

[
\ell_{\rm PMFS}(s)=
\sum_{i\in\mathcal S}
\log\!\left[
1-w_i\,|p_i-\hat p_i(s)|\,\gamma
\right],
]

where (w_i) is PMFS confidence, (p_i) is measured hit probability,
(hat p_i(s)) is the native simulated hit probability and
(gamma=1) is the frozen `sourceDiscriminationPower`.

TNQC evidence is computed with the same equations as
`TNQCScore.hpp`:

[
q_{\rm aff}(s)=
\frac{\sum_i w_i(x_i-\bar x_w)(y_{s,i}-\bar y_{s,w})}
{\sqrt{\sum_iw_i(x_i-\bar x_w)^2}
 \sqrt{\sum_iw_i(y_{s,i}-\bar y_{s,w})^2}},
]

[
q_{\rm ord}(s)=
\frac{\sum_{(i,j)\in E}\min(w_i,w_j)
\operatorname{sgn}(x_i-x_j)
\operatorname{sgn}(y_{s,i}-y_{s,j})}
{\sum_{(i,j)\in E}\min(w_i,w_j)},
]

and the corrected candidate-bank quotient-channel concordance gate.

For all valid **terminal active leaf candidates in the reconstructed final
PMFS partition** of one frozen update, write
(a_i=q_{\rm aff}(s_i)) and (o_i=q_{\rm ord}(s_i)), then compute

[
C_u=
\frac{1}{|\mathcal P_u|}
\sum_{(i,j)\in\mathcal P_u}
\operatorname{sgn}(a_i-a_j)
\operatorname{sgn}(o_i-o_j),
]

ignoring ties and candidates without enough local-order support. Subdivided
ancestors and other evaluated-but-nonterminal candidates are retained only
for a source-blind sensitivity audit; they cannot control the V3 gate. The
shared source-blind gate and candidate evidence are

[
g_u=\max(0,C_u),
\qquad
e_i=g_u a_i.
]

This replaces the earlier per-candidate sign guard. That older rule was
falsified by a ranking counterexample: preserving the sign of each candidate
score does not guarantee preservation of the ordering between candidates.
With one shared non-negative (g_u), local order may attenuate or abstain but
cannot reverse any affine candidate ordering. Evidence remains bounded in
([-1,1]).

The fixed-bank counterfactual likelihood is

[
\ell_{\rm TNQC}(s_i)=\ell_{\rm PMFS}(s_i)+e_i.
]

No coefficient is fitted.

### Exact native reconstruction audit

The replay does **not** assume its reconstruction is correct.  Before TNQC is
evaluated, it rebuilds the final native quadtree partition: for each free grid
cell, the smallest evaluated candidate rectangle covering that cell is the
last PMFS refinement value assigned there.  It normalizes those native
candidate likelihoods and compares the result cell-by-cell with the exported
`source_posterior.csv`.

Default validity limits:

- maximum absolute cell-probability discrepancy <= (5\times10^{-6});
- posterior L1 discrepancy <= (5\times10^{-4});
- Python native top-5% error must match the native C++ `RESULT IS: Error=`
  endpoint within 0.011 m (the C++ log is printed to two decimals);
- gate scope must be `final_partition_leaf_candidates_only`.

If any integrity condition fails, that House/seed replay is invalid and the
six-case gate cannot return GO. These audits detect mismatches in candidate
refinement/support, PMFS likelihood reconstruction, terminal endpoint
semantics, or final-hypothesis selection before a TNQC gain is interpreted.

### Correct 300-s experiment command

On the VGR VM, after building the current repository binary:

```bash
bash reference/run_tnqc_vgr_offline_gate_20260920.sh
```

This command runs **native PMFS only** for House01/02/03 x seed0/1 for the
full 300-s budget, exports context banks, then performs the counterfactual
TNQC replay.  It exits non-zero when the frozen GO criterion is not met.

Only after
`tnqc_vgr_300s_offline_gate.json` contains

```json
{"go_for_closed_loop": true}
```

may the separate TNQC closed-loop matrix be started.

### Important interpretation

This replay tests whether TNQC improves **final VGR localization inference on
the actual 300-s benchmark while trajectory and PMFS candidate refinement are
held fixed**.  It is intentionally not equivalent to the online fused arm:
online TNQC can additionally change quadtree refinement and future robot
motion.  The offline replay is the lower-risk causal screen required before
allowing those feedback paths.

The VGR 240-s spatial mechanism screen is recorded in
`evidence/TNQC_VGR_240S_SPATIAL_MECHANISM_20260921.json`: the affine representation is 12/12 at 240 s. The corrected candidate-bank
gate releases 11/12 cases with 100% conditional accuracy, and preserves that
11/12 coverage / 100% conditional accuracy across all 100 positive-scale and
200 monotone-compression source-blind stress seeds. This is mechanism evidence
only.
The Orebro 2/5/10-min result remains auxiliary and is not used in the GO
decision.
