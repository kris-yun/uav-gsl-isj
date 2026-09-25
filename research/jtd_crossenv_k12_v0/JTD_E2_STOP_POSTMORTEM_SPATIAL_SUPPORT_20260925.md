# JTD E2 STOP Postmortem — Spatial-Support Generality Failure

Date: 2026-09-25

Frozen verdict:
`JTD_E2_STOP_CROSSBLOCK_VALUE_NOT_ENVIRONMENT_GENERAL`.

## 1. Do not rescue the JTD mainline

E2 is a hard STOP for JTD as the paper-level main innovation.

All six frozen E2 gates failed. FULL beats BP/MBD in H01, but loses to both in both H02 OPEN wind environments.

Do not:
- relax gates;
- add more seeds to reverse the result;
- rename JTD using a new biological/physics story;
- enter G2 representation innovation under the JTD mainline.

## 2. Stronger postmortem finding: G1A dense support was spatially local

The G1A 168-source panel forms a contiguous 24 x 7 rectangular strip in House02:

- x range approximately [-4.94273, 1.95727] m;
- y range approximately [-3.70088, -1.90088] m;
- 24 unique x coordinates;
- 7 unique y coordinates;
- 168 = 24 x 7 sources.

The six H02 E2 sources are:
- pmfs_12_20 / pmfs_11_20 near y=-1.30088;
- pmfs_1_1 / pmfs_2_1 near y=-7.00088;
- pmfs_2_38 / pmfs_2_37 near y=4.10 / 3.80.

None of these six sources lies inside the G1A y-support strip.

Therefore G1A did NOT establish whole-House dense source-space generality.
It established dense utility inside one specific spatial transport region.

## 3. Crucial same-wind contradiction

G1A and E2 H02 `3,5-1_slow` use the same House and the same nominal wind environment, but different source locations.

G1A central-strip panel:
- FULL > BP broadly;
- FULL > MBD broadly.

E2 H02 `3,5-1_slow` off-strip six-source panel:
- mean delta_BP = -27.611;
- mean delta_MBD = -26.202;
- only 1/6 positive source units vs BP;
- only 2/6 positive source units vs MBD.

This shows that the failure cannot be explained only as cross-wind environment shift.

The value of cross-block dependence is source-location / transport-regime dependent even within the same nominal House and wind.

## 4. E2 source-level structure

The H02 failures are heterogeneous and include catastrophic source-specific reversals.

Examples:
- H02 W0 pmfs_11_20: mean delta_BP about -23.1, delta_MBD about -28.5;
- H02 W0 pmfs_2_38: mean delta_BP about -142.2, delta_MBD about -128.8;
- H02 W2 pmfs_11_20: mean delta_BP about -308.9, delta_MBD about -451.3.

Many other source units are near numerical ties.

This is not a uniform small degradation; it is transport/source-regime heterogeneity with occasional highly overconfident failures.

## 5. Revised scientific lesson

The evidence supports:

> Temporal cross-block dependence can be strongly source-discriminative in some spatial transport regimes, but the sign and value of that dependence are not invariant across source locations and transport regimes.

It does NOT support:
- a universal JTD mechanism;
- a universal cross-block covariance representation;
- direct entry into a JTD mother-theory innovation stage.

## 6. New problem statement for the next mainline search

Do not ask:
`How can we model temporal dependence better?`

Ask:

> What determines whether a temporal dependence component is source-discriminative, source-common, or actively misleading under a particular transport regime?

Any new candidate must predict that sign/value BEFORE using target outcomes.

## 7. Governance

- JTD G0/G1A remain valid limited-setting findings.
- JTD E2 STOP is final for this mainline.
- H01 DEV remains sealed.
- House03 remains sealed.
- No JTD G2 model/theory work is authorized.
- Future far-domain theory search may use this failure mechanism as evidence, but must be registered as a NEW mainline rather than a JTD rescue.