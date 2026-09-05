# CTPI G2 M1+M2 seed12 cross-House result (2026-09-05)

Verdict: `CTPI_G2_M12_SEED12_SCREEN=NO_GO`

This is a valid negative performance result, not a runtime failure.  All nine
H01/H02/H03 seed12 A0/F00/F01 arms reached the frozen 240 s horizon and passed
their terminal guards.  The causal-chain check passed in every House: M1 and
M2 both executed and changed the closed-loop trajectory or estimate signature,
and M3 remained inactive in F01.

## Frozen comparisons

| Module | Comparison | Error-AUC wins | Mean AUC delta (m s) | Seed12 screen |
| --- | --- | ---: | ---: | --- |
| M1 source-posterior likelihood and source-seeking navigation | F00 - A0 | 1/3 | +118.808 | NO_GO |
| M2 bank-free most-recent-wind transport increment | F01 - F00 | 1/3 | -118.537 | NO_GO |
| M1+M2 joint | F01 - A0 | 1/3 | +0.270 | NO_GO |

Lower error AUC is better.  M1 improved H01 by 169.467 m s, but worsened H02
by 377.158 m s and H03 by 148.732 m s.  M2 worsened H01 by 232.557 m s and H02
by 4.253 m s, while improving H03 by 592.422 m s.  M2's large H03 gain makes
its mean delta negative, but the preregistered gate requires strict wins in at
least two of three Houses, so it fails.

No arm reached 2 m within 240 s.  Final-error results do not rescue the primary
gate: M1's mean final-error delta was +0.034 m, M2's was +2.095 m, and the joint
delta was +2.129 m.

## Interpretation

- M1 and M2 are now proven to be wired into and causally active in real
  closed-loop runs across all three Houses.
- M1 is not proven cross-House effective by the seed12 screen.  Its earlier H01
  three-seed development PASS must not be promoted to a cross-House claim.
- M2 retains its separate leakage-free H02/H03 field-prediction PASS, but it is
  not proven to improve downstream closed-loop localization.
- M3 remains frozen `PROPER_H2_NO_GO` / `POST_H2_IDEA_GATE_NO_GO` and was not
  enabled in this experiment.

Per the preregistration, this NO_GO is preserved without per-House tuning,
seed rescue, or removal of losing Houses.

## Provenance and evidence

- Git commit: `a897ab31ad53ecb2ef5a1c53d2aa85aa51735c21`
- Algorithm binary SHA-256:
  `074065e2ebba74b80553768895a863646813ea84555d5be1073be516e4afa19f`
- Isolated vgr_bridge contract SHA-256:
  `924d4afbf6de52b59d6215316b8ee086440ddabe47b4b8451612ba0bb1012a62`
- Performance JSON SHA-256:
  `7fa5dae8c07a885bdb0a93be2be0c936380fee53825a65f23de09a11f4aebf9e`
- Full R4 evidence tar SHA-256:
  `92915c3011d2b4fec9280a74b523cd0cdf082d5d27109839079189805faf78f1`
- Full evidence package:
  `D:\ZYC\A-gas\_staging\CTPI_G2_M12_SEED12_CROSSHOUSE_20260905_R4_FULL_EVIDENCE.tar.gz`
- Small decision artifacts:
  `evidence/ctpi_g2_m12_seed12_20260905/`

R1-R3 are documented runtime-invalid attempts and are excluded from every
metric.  The identity-overlay, zero-weight variance, and CRLF parser repairs
are recorded in `CTPI_G2_M1_M2_SEED12_RUNTIME_AMENDMENT_20260905.md`.
