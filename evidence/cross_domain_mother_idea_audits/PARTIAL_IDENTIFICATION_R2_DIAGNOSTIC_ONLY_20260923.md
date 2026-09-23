# Partial-identification R2 mother-idea screen — diagnostic PASS / localization NO-GO

Date: 2026-09-23
Status: **DIAGNOSTIC NECESSITY POSITIVE / MAIN LOCALIZATION INNOVATION NO-GO**

## Frozen mother idea

Use partial identification under forward-model misspecification instead of assuming that one misspecified PMFS candidate model point-identifies the gas source.

For every candidate s, use the pre-existing source-blind robustness radius

rho_star(s) = max_i confidence_i * |p_measured_i - p_simulated_i|

over the common support. The identified set at radius rho contains candidates with rho_star <= rho.

No truth is used to construct the radius or select a radius.

## Authoritative input

Exact 300-s TNQC V5 R2 six-case archive:
- House01/02/03 x seed0/1
- final source update <= 300 s (all update 5)
- complete context-bank candidate support alignment
- native PMFS candidate scores

## Source-blind diagnosis

| Case | candidates | support | robust-best rho* | Native-best rho* | Native=robust best? |
|---|---:|---:|---:|---:|---|
| House01 seed0 | 152 | 261 | 0.9450 | 0.9529 | no |
| House01 seed1 | 148 | 265 | 0.8037 | 0.8697 | no |
| House02 seed0 | 148 | 279 | 0.8912 | 0.9200 | no |
| House02 seed1 | 144 | 272 | 0.8520 | 0.8826 | no |
| House03 seed0 | 197 | 291 | 0.9300 | 0.9700 | no |
| House03 seed1 | 199 | 254 | 0.99998 | 0.99998 | no |

For every case:
- no candidate is feasible for rho <= 0.50;
- at rho = 1.0 essentially/all candidates are feasible;
- Native best and minimum-radius candidate disagree in 6/6 cases;
- robust-best to second-best radius gaps are only about 0 to 0.031.

This is strong evidence that the sharp Native posterior is not supported by a small model-discrepancy neighborhood.

## Evaluator-only truth check after radius freeze

Terminal-leaf truth-nearest candidates enter only at essentially maximal discrepancy:

| Case | terminal leaves | truth rho* | truth robustness rank | earliest robust candidate distance to truth |
|---|---:|---:|---:|---:|
| House01 seed0 | 123 | ~1.0000 | 93 | 3.55 m |
| House01 seed1 | 121 | ~1.0000 | 93 | 4.38 m |
| House02 seed0 | 123 | ~1.0000 | 97 | 3.48 m |
| House02 seed1 | 119 | ~1.0000 | 89.5 | 4.02 m |
| House03 seed0 | 160 | ~1.0000 | 114.5 | 8.29 m |
| House03 seed1 | 160 | ~1.0000 | 113.5 | 6.92 m |

When the truth-nearest candidate becomes feasible, the identified set has already expanded to essentially the full terminal candidate family.

## Decision

Partial identification correctly diagnoses a real scientific problem:

> Native PMFS converts severe forward-model non-identifiability into false posterior certainty.

But this radius does not create source identity or improve source localization. It therefore fails the predeclared requirement that a main innovation must provide localization utility rather than honest uncertainty alone.

**Decision: DEMOTE TO AUXILIARY RELIABILITY / ABSTENTION.**

Do not truth-tune the radius, norm, or confidence weighting on these six cases.

The next main mother idea must create a new source-information channel or replace the misspecified candidate evidence generator, not only quantify its unreliability.
