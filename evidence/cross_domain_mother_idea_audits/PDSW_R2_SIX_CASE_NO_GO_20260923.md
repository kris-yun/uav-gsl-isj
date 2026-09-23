# PDSW V1 — authoritative R2 six-case falsification

Date: 2026-09-23  
Status: **CHANGES SOURCE ORDERING / DOES NOT RECOVER SOURCE IDENTITY / NO-GO**

## Frozen scientific object

PDSW transfers divergence-based predictive model weighting to the PMFS source-hypothesis bank.

For final active source hypotheses (k) and observed support cells (i):

[
min_w mathrm{KL}(w|pi)-sum_i logleft(sum_k w_k L_{ik}ight)
]

where (L_{ik}) is the exact Native PMFS pointwise cell likelihood and (pi) is the represented free-cell source prior.

The load-bearing semantic change is **mixture-before-log** rather than Native PMFS candidate-wise sum-log followed by normalization.

No source truth enters the weights.

## Authoritative input

Exact TNQC V5 R2 House01/02/03 × seed0/1 300-s archive.

The frozen TNQC V7 artifacts in all six cases pass their original integrity gates. Native posterior reconstruction from candidate support alignment is at floating-point precision. The same previously-audited standalone C++ PMFS top-5% endpoint clone used for the GCSI falsification reproduces the actual PMFS endpoint within the frozen tolerance and evaluates the PDSW counterfactual.

## Endpoint result

| Case | Native (m) | PDSW (m) | change |
|---|---:|---:|---:|
| House01 seed0 | 5.52735 | 5.54188 | +0.01453 |
| House01 seed1 | 4.00164 | 3.85722 | -0.14442 |
| House02 seed0 | 4.10702 | 4.39039 | +0.28337 |
| House02 seed1 | 3.70074 | 3.27011 | -0.43063 |
| House03 seed0 | 7.78205 | 7.64760 | -0.13445 |
| House03 seed1 | 8.21155 | 8.22580 | +0.01425 |

Pooled:
- Native: **5.55506025 m**
- PDSW: **5.48883462 m**
- improvement: **1.192%**
- improved pairs: **3/6**
- worst relative degradation: **6.90%**
- false-confident-collapse audit: **House01 seed0**

The frozen promotion requirements were >=10% pooled improvement, >=4/6 improved, <=25% worst degradation, and no false-confident collapse. PDSW fails three of these four substantive requirements.

## Evaluator-only source-order audit

After weights were frozen, truth-nearest terminal candidate rank was evaluated:

| Case | Native rank | PDSW rank | terminal count |
|---|---:|---:|---:|
| House01 seed0 | 81 | **95** | 123 |
| House01 seed1 | 90 | **76** | 121 |
| House02 seed0 | 98 | **90** | 123 |
| House02 seed1 | 96 | **87** | 119 |
| House03 seed0 | 112 | **108** | 160 |
| House03 seed1 | 109 | **113** | 160 |

Thus the ordering changes are mixed, not a systematic source-identity recovery.

Highest-weight PDSW candidate distance to true source:
- H01 seed0: 5.35 m
- H01 seed1: 3.99 m
- H02 seed0: 2.84 m
- H02 seed1: 3.75 m
- H03 seed0: 7.65 m
- H03 seed1: 9.31 m

Truth-nearest candidate PDSW weights are especially pathological in the difficult Houses; in H03 they are approximately (2.1	imes10^{-15}) and (2.6	imes10^{-12}).

## Interpretation

The AISTATS-style joint predictive weighting is a genuine semantic change, not a posterior-temperature control. It can change the source-hypothesis ordering.

However, those ordering changes do not systematically move probability toward the true-source neighborhood. The persistent failure is therefore upstream of how the same misspecified candidate predictions are jointly combined.

## Decision

**PDSW V1 = NO-GO AS MAIN INNOVATION.**

Do not escalate to:
- neural predictive weighting;
- learned divergence;
- House-specific source priors;
- truth-tuned KL strength;
- alternative optimizer hyperparameters

on these six development cases.

The next main mechanism must inject source information that is not already encoded in the same Native candidate response family.
