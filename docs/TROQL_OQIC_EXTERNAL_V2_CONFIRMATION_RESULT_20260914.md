# TROQL/OQIC external gate V2 — untouched confirmation result

Date: 2026-09-14

## Outcome

`TROQL_OQIC_V2_EXTERNAL_CONFIRMATION_NO_GO`

The frozen V2 distributional-dominance certificate did not pass untouched
confirmation in both directions. The main-innovation premise is therefore not
established.

## Confirmation metrics

| Direction | AUC | One-sided p | Source positive fraction | Source median | Nuisance median | Pass |
|---|---:|---:|---:|---:|---:|---|
| `a_to_b` | 1.0000 | 3.397807564086694e-08 | 1.00 | 0.3199975406549248 | 0.13783747911755106 | yes |
| `b_to_a` | 0.7500 | 0.003556747017886293 | 1.00 | 0.31787162528566354 | 0.1493333293773657 | no |

The frozen per-direction thresholds were AUC at least 0.80, one-sided p at most
0.01, and positive fraction at least 0.90. The second direction failed only the
AUC requirement. Its significant p-value and all-positive source margins cannot
replace the failed pre-registered effect-size gate.

## Integrity

- Result artifact: `experiments/troql_oqic_external_v2/CONFIRMATION_GATE.json`.
- Result SHA-256: `7fbb6a46bc2f27a6255f77a0be8fb6d95901b962ee148530a53e0f5d534f1eff`.
- Bound development result SHA-256:
  `124854900e67035d15ce83051f7255af77ae9c2f71f9d2d8ac5ef9cf8ca00974`.
- Frozen policy SHA-256:
  `3bd434f3bb499769bc17113990d5ceb8181b988a0d5b8578279000efa3516487`.
- Frozen scorer SHA-256:
  `c59491dc5f5ba0ea1d6cf57d59492132e7585768f1e5346bd15aed385385269e`.
- Frozen representation-kernel SHA-256:
  `a24be01a0f672c2c2f63ca38af2d7974e67bb5b58865363dd3bd04c24e00c692`.

No threshold, representation, split, or claim boundary was modified after
confirmation was opened.

## Authorized conclusion

- Bounded cross-dataset identifiability mechanism: `NOT_AUTHORIZED`.
- Closed-loop localization improvement: `NOT_AUTHORIZED`.
- Online PMFS deployment: `NOT_AUTHORIZED`.
- Universal identifiability: `NOT_AUTHORIZED`.

The confirmation result is informative but asymmetric. It supports the diagnosis
that source-relative evidence exists, while falsifying the claim that the present
certificate separates it from experiment-level nuisance with the required effect
size in every source direction.
