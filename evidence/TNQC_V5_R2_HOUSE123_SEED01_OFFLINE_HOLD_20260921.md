# TNQC V5 R2 House123 x seed0/1 Offline Gate — FINAL HOLD

Date: 2026-09-21

## Frozen verdict

**TNQC_VGR_300S_OFFLINE_HOLD**

All six newly acquired cases passed the frozen integrity contract. Earlier
House01/seed0 diagnostic/repeat runs were excluded from this authoritative
batch.

| Case | Native m | Fused m | Delta m | Improvement % | g | rho | Concordance |
|---|---:|---:|---:|---:|---:|---:|---:|
| H01/s0 | 5.527347155 | 5.527760816 | +0.000413661 | -0.007484 | 0.244681 | 0.882523 | 0.277252 |
| H01/s1 | 4.001642364 | 4.004095039 | +0.002452674 | -0.061292 | 0.408362 | 0.875686 | 0.466334 |
| H02/s0 | 4.107022746 | 4.107022746 | 0 | 0 | 0 | 0.997235 | -0.092186 |
| H02/s1 | 3.700743269 | 3.700743269 | 0 | 0 | 0 | 1.000000 | -0.035520 |
| H03/s0 | 7.782054929 | 7.782049365 | -0.000005565 | +0.000072 | 0.328865 | 0.999670 | 0.328974 |
| H03/s1 | 8.211551290 | 8.211744248 | +0.000192958 | -0.002350 | 0.139210 | 0.999752 | 0.139245 |

Aggregate:

- pooled native = 5.555060292 m
- pooled fused = 5.555569247 m
- pooled improvement = -0.009162%
- improved cases = 1/6
- worst degradation = 0.061292%
- false-confident-collapse cases = 6/6
- integrity valid = true

The frozen GO criteria were not changed after observing results.

## Evidence-package verification

Authoritative uploaded package:

`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz`

SHA-256:

`81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708`

Size is approximately 135 MiB, so the full archive is retained on the
experimental VM/shared storage rather than committed directly to normal Git.

The package-internal `SHA256SUMS.json` declares 428 files. Independent
verification on 2026-09-21 found:

- declared files: 428
- missing files: 0
- SHA mismatches: 0

Frozen R2 Git identity recorded inside the package:

`b24da77fd24bd5ea2cbb33caf856f80b9d7670e4`

## Scientific interpretation

This is a clean negative result for TNQC V5 on the registered 300-s online
hit-logit fixed-trajectory endpoint.

The failure is not an execution failure:

- all six terminal RESULT IS anchors exist;
- all six native posterior reconstructions pass;
- all six linked-native endpoint parity checks pass;
- all six candidate-support completeness checks pass;
- all six V7 integrity checks pass.

TNQC V5 therefore remains frozen and is not retuned on these six cases.

## Mechanism diagnosis from the frozen batch

Additional post-verdict diagnostics were performed only to understand the
negative result, not to rescue V5.

In House01 and House03, the final-leaf candidate covering the true-source
neighborhood has a low/negative affine quotient score, while the maximum
q_aff candidates are several metres from the true source. House02's
true-source owner is not a valid quotient-score candidate under the final
support conditions.

Therefore the central limitation is not merely an insufficient fusion gain:
the online hit-logit quotient representation itself does not reliably rank
the true-source neighborhood above transport-confounded alternatives in this
batch.

Positive q_aff/q_ord concordance can consequently represent internal
agreement on a wrong candidate ordering. The local-order gate is a
consistency gate, not a truth-calibration oracle.

The native posterior is also extremely concentrated while remaining several
metres from truth, so a bounded weak posterior tilt cannot by itself create
the missing source identifiability.

## Decision

Do not run TNQC V5 FUSED closed loop.

Do not tune TNQC V5 on House01/02/03 x seed0/1.

Proceed, under a new method/version, to the pre-declared
Active Source–Transport Deconfounding research line.
