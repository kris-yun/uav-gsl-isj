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

The existing frozen reference matrix for the prior ME-ACI V10 work is:

| House | seed | native PMFS top-5% error m | ME-ACI V10 top-5% error m |
|---|---:|---:|---:|
| H01 | 0 | 5.152589 | 2.501097 |
| H01 | 1 | 6.928495 | 5.006343 |
| H02 | 0 | 2.926781 | 2.271832 |
| H02 | 1 | 1.813416 | 1.307146 |
| H03 | 0 | 6.652648 | 2.863832 |
| H03 | 1 | 5.219942 | 2.982003 |

Those values are reference endpoints only; they do not imply anything about TNQC.

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
