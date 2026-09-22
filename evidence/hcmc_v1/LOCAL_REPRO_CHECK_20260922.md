# HCMC V1 — independent local reproduction check

Date: 2026-09-22
Status: **REPRODUCED ON THE USER-SUPPLIED FROZEN ARCHIVE**

A fresh compact reimplementation was executed from the extracted archive rather than reading the stored HCMC result JSON.

Archive SHA256:
`81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708`

Frozen HCMC definition retained:
- powers p = 1,2,3,4;
- scales = 1,2,4,8 cells;
- +x/+y pairs;
- pair weight sqrt(conf_i * conf_j);
- confidence floor 1e-6;
- score = negative mean absolute mismatch of adjacent log2 structure-function slopes;
- authoritative final-leaf IDs only;
- average-percentile leaf density;
- unchanged 300-s top-5% ExpectedValue endpoint.

## Exact reproduced endpoints

| case | native m | HCMC m |
|---|---:|---:|
| House01 seed0 | 5.527347155 | 2.054147392 |
| House01 seed1 | 4.001642364 | 2.194595449 |
| House02 seed0 | 4.107022746 | 1.229000897 |
| House02 seed1 | 3.700743269 | 3.110970202 |
| House03 seed0 | 7.782054929 | 1.282938532 |
| House03 seed1 | 8.211551290 | 4.821311331 |

Aggregate:
- native mean = **5.555060292 m**;
- HCMC mean = **2.448827301 m**;
- pooled relative reduction = **55.9171787%**;
- improved = **6/6**.

The values match the frozen HCMC result exactly to ordinary floating-point precision.

## Meaning

This is a code-path/data-provenance reproduction check, **not an independent statistical validation set**. The next promotion gate remains genuinely new GADEN/VGR stochastic realizations with HCMC V1 unchanged.
