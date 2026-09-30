# OCB-R2 R1 — Cross-Time Memory Anatomy Before Mother-Theory Selection

Date: 2026-09-30

Status: **PREREGISTERED DISCOVERY-ONLY / NOT EXECUTED**

Parent result:

`OCB_R2_MECH_CROSS_TIME_STABLE`

Evidence commit:

`c7b52bb969f8d48ffdbf87016574c00f1dd0cdae`

## Purpose

R0 established that intact cross-time realization pairing adds a stable
source-discrimination margin beyond complete each-time spatial snapshot
structure on the repaired OCB-R2 H01/H02 discovery benchmark.

R1 does **not** build a method.

R1 asks one narrower mechanistic question before choosing any far-domain mother
theory:

> Is the stable cross-time source information mainly short-memory/local
> transition structure, or does source identity require broader multi-lag /
> whole-path dependence?

This distinction determines which theory family is scientifically appropriate.

Use only the already-frozen R0 64 binary tensors and metadata. No new target
extraction, GADEN, PMFS forward, learned model, confirmation, H03 or closed
loop.

## 1. Input freeze

Require exact hash parity with the R0 inputs and observation contract:

- S2+S2X 64 discovery targets
- 8 fixed matched House-wind-gas contexts
- 2 sources/context
- 4 realizations/source
- E1 30 probes
- physical times 50,100,...,500 s
- binary encounter definition B[t,q] = 1[C[t,q] > 0]
- same-index leave-one-realization-out primary split
- K=3 references for truth and alternative

If any hash differs, STOP with:

`OCB_R2_R1_HOLD_INPUT_PARITY`

## 2. Lag-specific pair mechanism

For each temporal lag L = 1,...,9 and each valid pair t,t+L:

- target pair is the concatenated 60-D vector
  `[B_target[t,:], B_target[t+L,:]]`
- each reference realization contributes the corresponding concatenated 60-D
  pair
- score truth and alternative source with the same fair U-statistic Energy
  Score used in R0
- average the score across all valid t for that lag

Define intact source margin:

`G_RAW_L = ES_RAW_L(alt,target) - ES_RAW_L(truth,target)`

Construct the lag-specific null by independently permuting, within each
candidate source and each valid t, the K realization labels of the second
snapshot t+L while leaving the first snapshot t fixed.

This preserves:

- both time-specific 30-D snapshot multisets
- all coordinate marginals
- within-time spatial structure
- K and support

It destroys only the realization pairing across lag L.

Use exactly 1000 surrogates per candidate/reference view.

Frozen RNG seed family:

`2026093100 + L`

Define:

`I_LAG[L] = G_RAW_L - median_b G_SHUFFLED_L[b]`

Positive I_LAG means source identity benefits from intact pairing at that lag.

## 3. Contiguous-block preservation curve

R0 C2 is equivalent to block length 1: every time slot may come from a
different realization.

RAW is block length 10: the whole trajectory comes from one realization.

Add two intermediate block interventions.

### BLOCK-2

Fixed blocks:

- [1,2]
- [3,4]
- [5,6]
- [7,8]
- [9,10]

Within each candidate source, independently permute the K realization labels
for each complete 2-time block.

This preserves all temporal dependence inside each 2-slot block and destroys
pairing between blocks.

### BLOCK-5

Fixed blocks:

- [1,2,3,4,5]
- [6,7,8,9,10]

Independently permute the K realization labels for the two complete 5-time
blocks.

This preserves all within-half trajectory dependence and destroys pairing
between the two halves.

Use 1000 surrogates per candidate/reference view.

Frozen seeds:

- BLOCK-2: `2026093120`
- BLOCK-5: `2026093150`

For each target define source margins:

- `G_B1` = R0 C2 median margin
- `G_B2` = BLOCK-2 median margin
- `G_B5` = BLOCK-5 median margin
- `G_B10` = R0 RAW margin

Define normalized descriptive recovery when the R0 cross-time denominator is
positive:

`R_B2 = (G_B2 - G_B1) / (G_B10 - G_B1)`

`R_B5 = (G_B5 - G_B1) / (G_B10 - G_B1)`

Do not clip these values. Report negative or >1 values honestly.

These recovery ratios are descriptive; they are not tuning objectives.

## 4. Aggregation

For every lag and block intervention report:

- 64 target-level effects
- 16 source×context group means and medians
- 8 context means and medians
- House01 median
- House02 median
- positive group count /16
- positive context count /8
- leave-one-context-out pooled medians

Do not treat time pairs as independent targets.

## 5. Reference-omission robustness

Repeat the lag and block summary under all four alternative-source 3-of-4
reference omissions, exactly as in R0.

No theory label may be based on one omission convention only.

## 6. Mechanism interpretation labels

R1 is an anatomy stage. It does not choose a paper or build a model.

### `OCB_R2_R1_SHORT_MEMORY_DOMINANT`

Use only if:

- lag 1 has positive House01 and House02 medians;
- at least 12/16 groups have positive mean I_LAG[1];
- BLOCK-2 preserves at least 2/3 of the R0 cross-time increment in the median
  source×context group in both Houses;
- the same qualitative conclusion holds for all reference-omission choices.

Interpretation:

most stable source-relevant path information is recoverable from local
short-time transitions. A trajectory-entropy / local-transition mother theory
is scientifically plausible.

### `OCB_R2_R1_BROAD_MEMORY_REQUIRED`

Use if SHORT_MEMORY_DOMINANT fails, but:

- at least one lag L >= 3 has positive medians in both Houses and at least
  12/16 positive source×context groups; and/or
- BLOCK-2 recovers less than 2/3 while BLOCK-5 recovers at least 2/3 of the R0
  cross-time increment in both Houses;
- conclusion is robust to reference omission.

Interpretation:

source identity requires broader temporal dependence than a first-order/local
transition description. A high-dimensional path-dependence / copula / flow
mother theory is more appropriate.

### `OCB_R2_R1_WHOLE_PATH_REQUIRED`

Use if neither shorter-memory label passes and BLOCK-5 still recovers less than
2/3 of the R0 cross-time increment in either House while RAW remains positive
under the original R0 gate.

Interpretation:

the source-relevant information is genuinely whole-path / long-range under this
10-slot observation contract.

### `OCB_R2_R1_MEMORY_ANATOMY_HOLD`

Use if the lag/block spectrum is inconsistent across Houses or reference
omissions and does not support a stable memory-scale interpretation.

## 7. Stop boundary

After assigning one R1 anatomy label:

- STOP
- do not search literature automatically
- do not implement Maximum Caliber
- do not implement copula/diffusion/flow models
- do not train a classifier
- do not generate new data
- do not open confirmation or H03

Human review will map the observed memory anatomy to the most appropriate
far-domain mother theory.

## 8. Required outputs

- `research/ocb_r2/cross_time_anatomy_r1/R1_PROTOCOL_FROZEN.md`
- `evidence/ocb_r2/cross_time_anatomy_r1/R1_INPUT_PARITY.json`
- `evidence/ocb_r2/cross_time_anatomy_r1/R1_LAG_TARGETS.tsv`
- `evidence/ocb_r2/cross_time_anatomy_r1/R1_LAG_GROUPS.tsv`
- `evidence/ocb_r2/cross_time_anatomy_r1/R1_BLOCK_TARGETS.tsv`
- `evidence/ocb_r2/cross_time_anatomy_r1/R1_BLOCK_GROUPS.tsv`
- `evidence/ocb_r2/cross_time_anatomy_r1/R1_REFERENCE_OMISSION.tsv`
- `research/ocb_r2/cross_time_anatomy_r1/R1_DECISION_REPORT.md`
