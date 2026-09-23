# C0-PRE Result — Historical 2×2 Source × Transport Recombination

Date: 2026-09-23  
Branch: `research/causal-compositional-plume-world-model-v1`

## Decision

`C0-PRE = NO POSITIVE NEED SIGNAL FOR CAUSAL COMPOSITION`

`M4 STATUS = HOLD / DEMOTE FROM CURRENT #1`

The historical controlled 2×2 assets provide an unusually clean intervention structure, but they do **not** show that compositional source×transport modeling is needed for source identity.

## 1. Asset structure

Historical controlled branch:

- git SHA: `26e89a99532e4268c5022dca2e938bf1473377b1`;
- root: `evidence/cstar_current_runtime_assets240_20260907`.

For each House:

- source SA;
- source SB;
- transport fast;
- transport slow;
- identical geometry-only pose sequence;
- same release/sensor seeds within the controlled asset.

The manifests explicitly record:
- `source_id`;
- `source_xyz_m`;
- `transport_intervention_id`.

Example House02:

- SA = (0.0, -1.0, 0.2);
- SB = (1.0, -2.3, -0.1);
- fast = `current_runtime_H02_fast`;
- slow = `current_runtime_H02_slow`.

## 2. Transport intervention is real, not a label

House02 raw histories:

- 1200 samples per combination;
- pose sequence exactly identical across all four combinations.

Within a transport condition:

- SA-fast vs SB-fast wind vectors are pointwise identical;
- SA-slow vs SB-slow wind vectors are pointwise identical.

Thus changing source does not alter the measured transport sequence.

Fast vs slow:

- mean wind magnitude fast ≈ 0.11783 m/s;
- mean wind magnitude slow ≈ 0.04951 m/s;
- median slow/fast magnitude ratio ≈ 0.438;
- 10–90% ratio range ≈ 0.264–0.756;
- mean pointwise direction difference ≈ 18.9°;
- global vector cosine ≈ 0.921.

Thus the transport intervention is not merely a source relabel and is not a single exact scalar rescaling.

## 3. Zero-parameter compositional test

For each House define transformed gas signal

[
z=log(1+mathrm{ppm}).
]

For a held-out combination, e.g. (B,slow), predict using the other three:

[
hat z_{B,slow}
=
z_{B,fast}
+
z_{A,slow}
-
z_{A,fast}.
]

No fitted parameters, no truth tuning.

All four cells are rotated as hold-outs in all three Houses.

Comparators:

1. same source / other transport;
2. same transport / other source;
3. mean of the first two;
4. additive compositional recombination.

## 4. Source-identification result

Correct held-out source identification:

| prefix | composition | same-source/other-transport | mean-two |
|---:|---:|---:|---:|
| 60 s | 4/12 | 5/12 | 5/12 |
| 120 s | 4/12 | 7/12 | 8/12 |
| 180 s | 12/12 | 12/12 | 12/12 |
| 240 s | 12/12 | 12/12 | 12/12 |

Therefore composition provides **no unique source-identification gain**.

## 5. Held-out signal reconstruction

Mean log-signal RMSE at 240 s:

- composition: **0.15520**;
- same-source / other-transport: **0.09717**;
- same-transport / other-source: **0.35620**;
- mean-two: **0.19766**.

The same-source / other-transport baseline is better than the zero-parameter composition.

Per House at 240 s:

### H01
- composition: 0.01642;
- same-source/other-transport: 0.00843.

### H02
- composition: 0.08299;
- same-source/other-transport: 0.04193.

### H03
- composition: 0.36618;
- same-source/other-transport: 0.24114.

## 6. Scientific interpretation

The controlled assets do confirm that:

- source and transport interventions are independently instantiated;
- source signatures remain distinguishable across the tested transport shift.

But they **do not establish a need for causal compositional world modeling**.

In this asset, a trivial reuse of the same source under the other transport condition is already:
- as good or better for source identification;
- better for held-out signal reconstruction.

Therefore it would be scientifically weak to promote M4 on the basis of this dataset.

## 7. What could revive M4

Only a harder, predeclared regime where:

- simple same-source transfer fails;
- monolithic interpolation fails;
- mechanism-factorized recombination succeeds;
- downstream truth-source rank improves.

Examples:
- stronger wind-topology changes;
- unseen House geometry;
- source×wind combinations outside the current mild transport range.

Do not generate large causal datasets just to rescue M4 unless another candidate fails.

## 8. Current decision

M4 is no longer the lead main innovation.

Status:

`HOLD — CLEAN INTERVENTION INTERFACE, BUT NO UNIQUE COMPOSITIONAL BENEFIT IN EXISTING 2×2 ASSET`.

The C0 generation benchmark is retained in case a future harder intervention test is justified.
