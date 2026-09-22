# CS-MoM V1 — simplex blend falsification

Date: 2026-09-22
Status: **NEGATIVE CONTROL / DO NOT REPAIR CS-MoM BY NATIVE MIXING**

## Frozen data

Archive SHA256:

`81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708`

Cases: House01/02/03 × seed0/1, authoritative 300-s final source-update banks.

Native mean endpoint error: **5.555060 m**.

Pure correlation-scale MoM:
- mean endpoint error: **3.939253 m**;
- pooled reduction: **29.0871%**;
- non-worse: **5/6**;
- blocking case: House01 seed0, **5.527347 -> 7.213470 m**.

## Convex log-evidence blend

Test one global weight

`score_w = (1-w) * score_native + w * score_CSMoM`

with `0 <= w <= 1`, grid step 0.001.

Result:
- optimum is exactly **w=1.0**, i.e. pure CS-MoM;
- no nontrivial blend obtains 6/6 non-worse;
- fixed w=0.25: pooled -0.30%;
- fixed w=0.50: pooled -0.34%;
- fixed w=0.75: pooled +0.39%.

Interpretation: the sharp native log-likelihood is too dominant to be a safe correction channel.

## Convex posterior blend

Also test

`p_w = (1-w) p_native + w p_CSMoM`.

Results:
- w=0.50: **7.57%** pooled reduction, 5/6 non-worse;
- w=0.75: **15.26%**, 5/6;
- w=0.90: **21.91%**, 5/6;
- w=0.95: **25.02%**, 5/6;
- w=0.99: **28.51%**, 5/6;
- optimum again at w=1.0: **29.09%**, 5/6.

No weight gives both >=20% pooled reduction and 6/6 non-worse.

Leave-one-House-out selection also chooses pure CS-MoM and therefore does not repair House01:
- held-out House01: **-12.33%**;
- held-out House02: **+52.21%**;
- held-out House03: **+42.47%**.

## Decision

Do **not** spend the innovation budget tuning simplex weights between native PMFS and CS-MoM.

The unresolved failure is structural: CS-MoM restores true-source support but point release can still select a wrong robust mode. The next admissible extension is an identifiability/set-release mechanism, not native-posterior interpolation.
