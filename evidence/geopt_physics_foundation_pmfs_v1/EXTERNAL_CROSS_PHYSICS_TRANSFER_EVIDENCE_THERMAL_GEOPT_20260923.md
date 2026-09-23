# M6 External Cross-Physics Transfer Evidence — GeoPT -> OpenFOAM Heat Conduction

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Status

`EXTERNAL FEASIBILITY EVIDENCE — NON-PEER-REVIEWED`

This is not a GSL novelty source and must not be cited as a definitive scientific result.

It is useful as independent engineering evidence that the original GeoPT checkpoint can transfer outside the original paper's downstream domains.

## Source

Public technical repository:

`OzasaHiro/thermal-geopt`

Report:

`docs/original_geopt_heat_transfer_preliminary_report.md`

Date: 2026-05-11.

The report explicitly labels itself:
- preliminary;
- non-peer-reviewed.

## Task

Original GeoPT checkpoint transferred to OpenFOAM-solved steady solid-conduction heat-sink surrogate modeling.

The GeoPT checkpoint was not pretrained on thermal labels.

Two generated benchmarks were used:
- Benchmark A: 300 cases;
- Benchmark B: 300 cases.

Low-data settings:
- 25 training cases;
- 50 training cases;
- 3 split seeds per setting.

## Reported transfer result

Benchmark A, paired improvement over same-architecture scratch:

- 25 training cases: **+13.4%**
- 50 training cases: **+17.2%**

Benchmark B:

- 25 training cases: **+10.8%**
- 50 training cases: **+15.7%**

The report also states that temperature-extrema/hotspot metrics improved.

## Important negative control

The project's own small thermal-specific pretraining prototype produced large negative transfer.

Thus the result does not support the trivial statement:

> any domain-specific pretraining helps.

Instead, it is consistent with the importance of:
- pretraining scale;
- geometry diversity;
- pretext alignment;
- the original GeoPT representation.

## Checkpoint-loading detail

For their thermal task, original GeoPT reportedly loaded 166 shape-compatible tensors.

It skipped/missed:
- `preprocess.linear_pre.0.weight`;
- final `blocks.7.mlp2.weight`;
- final `blocks.7.mlp2.bias`.

The first projection was incompatible because their thermal downstream input shape changed.

Despite that partial transfer, low-data improvement was observed.

## Why this matters to M6

Our M6 gas mapping was deliberately designed to preserve the official:

- `space_dim=3`;
- `fun_dim=11`;
- separate `pos3 + fx11` contract.

Therefore M6 has a chance to preserve even the first pretrained input projection, unlike this thermal transfer experiment.

This does NOT imply M6 will improve GSL.

But it reduces the concern that GeoPT transfer is limited to its original fluid/solid-mechanics benchmarks.

## Strong caution

Do not turn this into a paper-level claim that GeoPT is universally transferable.

The report itself notes:
- only 3 split seeds;
- one training seed;
- controlled simplified conduction;
- preliminary status;
- incomplete artifact redistribution.

Use it only for prioritization / feasibility.

## Consequence for G1

The correct M6 control remains:

`same Transolver architecture from scratch vs original GeoPT pretrained checkpoint`

under identical scarce GADEN data.

The heat-transfer evidence increases the value of running this test; it cannot substitute for it.

Status:

`M6 FEASIBILITY CONFIDENCE INCREASED — SOURCE-RANK GATE UNCHANGED`.
