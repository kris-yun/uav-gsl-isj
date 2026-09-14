# TROQL/OQIC external gate V2 — development result

Date: 2026-09-14

## Outcome

`TROQL_OQIC_V2_EXTERNAL_DEVELOPMENT_PASS_TO_CONFIRMATION`

The distributional-dominance evidence-release rule passed on the development
source/null pairs in both directions. This result only authorizes opening the
pre-separated confirmation files; it is not itself confirmation evidence.

## Frozen metrics

| Direction | AUC | One-sided p | Source positive fraction | Source median | Nuisance median | Pass |
|---|---:|---:|---:|---:|---:|---|
| `a_to_b` | 0.8925 | 1.1512354940556353e-05 | 0.95 | 0.14238744420771066 | 0.05067290062303148 | yes |
| `b_to_a` | 0.9650 | 2.613442661342888e-07 | 1.00 | 0.13844564437731505 | 0.05881504530323667 | yes |

Frozen thresholds were AUC at least 0.80, one-sided p at most 0.01, and source
positive fraction at least 0.90 in each direction.

## Integrity

- Result artifact: `experiments/troql_oqic_external_v2/DEVELOPMENT_GATE.json`.
- Result SHA-256: `124854900e67035d15ce83051f7255af77ae9c2f71f9d2d8ac5ef9cf8ca00974`.
- Confirmation opened: no.
- The result records and binds the frozen policy, scorer, representation kernel,
  raw-input hashes, and input block spans.

No claim beyond permission to run the untouched confirmation stage is authorized.
