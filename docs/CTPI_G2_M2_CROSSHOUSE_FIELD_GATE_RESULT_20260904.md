# CTPI-G2 M2 cross-House field gate result

Date: 2026-09-04  
Verdict: `CTPI_G2_M2_CROSSHOUSE_FIELD_GATE=PASS`

This replacement gate fixes the leakage in the earlier VM `/tmp` scripts. It
never recovers a candidate source position from a bank-field argmax and never
uses a truth-guided trajectory. For every carrier it marginalizes the frozen M2
prediction over all free native cells inside that carrier. H02/H03 GADEN peak
fields are read only as held-out evaluation targets.

| House | carriers | median corr M2 | median corr plume | corr W/L | median MSE M2 | median MSE plume | MSE W/L |
|---|---:|---:|---:|---:|---:|---:|---:|
| H02 | 201 | 0.355966 | 0.268898 | 146/55 | 0.016173 | 0.016744 | 123/78 |
| H03 | 206 | 0.463817 | 0.302287 | 149/57 | 0.019589 | 0.024353 | 133/73 |

All four pre-registered criteria pass in both held-out Houses. H03 contains four
all-zero GADEN target members (audited and excluded only from per-member shape
normalization) and three all-zero plume predictor carriers (retained with the
predeclared zero-vector metric). The numerical M2 predictor has zero all-zero
carrier predictions.

This is a PASS for the M2 core claim: bank-free cross-environment predictive
field generalization relative to the current G2 Gaussian plume. It is not a
claim that M2 already improves downstream closed-loop localization.

Raw gate SHA-256:
`3c48921fb8400d346009784430abee69544480d171ef3ab18c67eff1f5bc26fe`

Serialized field hashes:

- H01: `4c8c31ef5db48d2529dd12001ee6ed6fbf7b64e1869429b150eee91d31fce1d8`
- H02: `544985a5a5a1c9e9f8ba19dae76fcf64c7d029d94e2ffb36f83839b841714a13`
- H03: `1affa6aefa240dba47589879f328642b222f1733e116d04df981b6606e2d7d56`
