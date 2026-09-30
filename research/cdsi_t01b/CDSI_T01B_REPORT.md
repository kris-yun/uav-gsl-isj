# CDSI-T0.1B independent-realization information audit

Date: 2026-10-01

Branch: `research/cdsi-t01b-independent-information-audit-20261001`

Pre-target protocol/script/metadata freeze: `52721852`.

## Decision: `CDSI_T01B_SOURCE_INFORMATION_STATIC_ONLY_HOLD`

Independent-sample contract: **8/8 PASS**, 64 distinct discovery runs/seeds. The prior `CDSI_T01_MATCHED_INTERVENTION_FAIL` remains unchanged.

## Eight-context results

| Context | House | E FULL | E STATIC | E C2 | p FULL | Z FULL | Z STATIC | Z C2 | Delta static | Delta pairing |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| X00 | House01 | 0.55514650 | 0.53203665 | 0.55279696 | 0.02857143 | 4.25383954 | 4.19950396 | 4.35658341 | 0.05433558 | -0.10274387 |
| X01 | House01 | 0.67773072 | 0.69044696 | 0.67409182 | 0.02857143 | 4.37862865 | 4.39707849 | 4.50810708 | -0.01844984 | -0.12947843 |
| X02 | House01 | 0.59173265 | 0.58674757 | 0.58670841 | 0.02857143 | 4.34729796 | 4.40460649 | 4.46078508 | -0.05730853 | -0.11348712 |
| X03 | House01 | 0.71724883 | 0.63851975 | 0.71445434 | 0.02857143 | 4.39700700 | 4.44155026 | 4.55258341 | -0.04454327 | -0.15557642 |
| X04 | House02 | 0.78705038 | 0.72308256 | 0.78513438 | 0.02857143 | 4.45551718 | 4.46472980 | 4.68933887 | -0.00921262 | -0.23382169 |
| X05 | House02 | 0.74195354 | 0.74763141 | 0.73760121 | 0.02857143 | 4.40632703 | 4.44303945 | 4.59799154 | -0.03671242 | -0.19166451 |
| X06 | House02 | 0.56243502 | 0.47672877 | 0.56178516 | 0.02857143 | 4.04914524 | 3.94031680 | 4.13168871 | 0.10882844 | -0.08254347 |
| X07 | House02 | 0.76741252 | 0.75041880 | 0.75865031 | 0.02857143 | 4.36824753 | 4.36110787 | 4.51035709 | 0.00713966 | -0.14210956 |

## Frozen gates

```json
{
  "G1_FULL_SOURCE_DISTRIBUTION": {
    "above_null_median_count": 8,
    "aggregate_p": 9.99999000001e-07,
    "exact_context_p_le_005_count": 8,
    "exact_direction_sign_test_p": 0.00390625,
    "pass": true
  },
  "G2_DYNAMIC_ADVANTAGE": {
    "exact_one_sided_p": 0.85546875,
    "median": -0.013831229487370589,
    "negative": 5,
    "pass": false,
    "positive": 3,
    "sign_p_is_descriptive": true,
    "ties": 0
  },
  "G3_PAIRING_ADVANTAGE": {
    "exact_one_sided_p": 1.0,
    "median": -0.1357939967360262,
    "negative": 8,
    "pass": false,
    "positive": 0,
    "sign_p_is_descriptive": true,
    "ties": 0
  }
}
```

## House summaries

| House | median Z FULL | median Delta static | median Delta pairing | positive static | positive pairing |
|---|---:|---:|---:|---:|---:|
| House01 | 4.36296331 | -0.03149655 | -0.12148277 | 1/4 | 0/4 |
| House02 | 4.38728728 | -0.00103648 | -0.16688704 | 2/4 | 0/4 |

## Exact versus Monte Carlo null

Every context exhaustively evaluates 70 source-label assignments, including the observed assignment. FULL, STATIC and C2 each use their own assignment null. C2 is rebuilt under every assignment; 1000 source-local time-block shuffles are numerical integration, not independent scientific replicates.

The aggregate tests mean FULL standardized effect 4.332001266.
It samples 1,000,000 stratified assignments from 70^8=576,480,100,000,000.
Exceedances: 0; plus-one p=9.99999e-07;
95% Monte Carlo binomial interval=[0.0, 3.6888726502064885e-06].
It is **Monte Carlo**, not exhaustive aggregate enumeration.

The context sign tests are exact. G2/G3 use the explicitly listed median/6-of-8 criteria; their sign-test p-values are reported descriptively because the request specifies no extra cutoff.

## Preservation, arithmetic and determinism

C2 passed full 30D snapshot-multiset and all-300-marginal preservation for every assignment/draw/source. Synthetic C2 K=3 output is bitwise equal to the actual R0 routine. The K=4 extension changes only the present sample count; it retains R0 block-shuffle semantics. Optimized distances were checked against direct transformed-path distances. Known-value and zero-signal Energy checks passed.

Two complete calculations matched byte-for-byte for 15 result files, including all null arrays.
C2 finite Monte Carlo values are symmetrized over A/B-complement assignments as frozen before analysis.

## Interpretation and limits

This task tests different configured **xyz** source distributions under the same non-source context. H01 source z is 0.4 versus -0.3 m; H02 source z is 0.2 versus -0.1 m. Neither pure xy nor continuous two-dimensional source identifiability is established.

The Energy primary is the signed V-statistic. It is upward-biased with 4-vs-4 samples; raw Energy >0 alone is not a positive finding. The context permutation tests and standardized contrasts determine the signed gates. A comparison of standardized distances is this protocol's operational dynamic criterion, not a conditional-information, PID/PIRD synergy, Fisher information or deployable source likelihood estimate.

Observed unstandardized FULL Energy is higher than C2 in all eight contexts, but FULL Z is lower in all eight because their permutation references differ. G3 is defined using Z, so the raw difference cannot rescue it. Report both to avoid interpreting this gate as a direct proof that cross-time coupling contains no information.

These are already-used discovery tensors. This is a new pre-analysis implementation freeze for this statistic, not untouched external confirmation. Four realizations/source/context and two configured sources limit power and scope. A gate failing to establish dynamic advantage does not prove temporal dependence absent under all scores or acquisition policies.

No optional secondary scorer was run. No source/seed/probe/time/threshold was changed. No GADEN, PMFS, network, 3D change, R3A, confirmation/H03 or closed loop was executed.

**COMPLETED AND STOPPED.**
