# CODEX — PF-DEI existing-offline-data coherence audit

Date: 2026-08-29
Status: EXECUTION CONTRACT / NO NEW GADEN / NO NEW NEURAL TRAINING

## Goal

Use already-generated PF-DEI physical-bank data to answer three different questions without localization-outcome tuning:

1. Does the physically closed predictive bank contain held-out source-identifiable information?
2. Does chronological dynamics add source information beyond level matching?
3. Does preserving one nuisance member as one coherent whole trajectory add information beyond the same per-time ensemble marginals?

Do not merge these into one PASS. A source-ranking method may work even when the claimed temporal/coherence mechanism does not.

## Hard prohibitions

- Do not launch GADEN or regenerate any completed member merely for this audit.
- Do not launch H01/H02/H03 neural training, shared training, LOHO training, or fine-tuning.
- Do not read localization error, ON/OFF outcome, true source coordinates from historical runs, or performance labels to set any method parameter.
- Do not alter the currently running independent H01 full 8-member source-information audit. This task is a parallel code/audit path over existing materialized bank data.
- Do not tune lags, block size, transform, threshold, or permutations from observed ranking performance.

## Code to use

`experiments/cg_pc_ctt/pf_dei_offline_coherent_audit.py`

First:

```bash
git fetch origin research/cg-pc-ctt-v6-dynamic-transport-sbi
git checkout research/cg-pc-ctt-v6-dynamic-transport-sbi
git pull --ff-only
python3 experiments/cg_pc_ctt/pf_dei_offline_coherent_audit.py --selftest
```

Expected:

`PF_DEI_COHERENT_OFFLINE_AUDIT_SELFTEST PASS`

## Input contract

Prefer an already-materialized canonical NPZ with:

- `candidate_physical_ppm[S,M,T]`
- `source_id[S]`
- `transport_id[M]`
- `geometry_prior[S]`
- optional `sample_time_s[T]`

The canonical full physical-bank validation contract remains in
`experiments/cg_pc_ctt/pf_dei_physical_bank_contract.py`.

If the completed 7404-member bank is currently stored as per-carrier/per-member payloads rather than one NPZ, materialize the required tensor by reading those existing payloads only. Do not invoke the simulator. Preserve exact carrier IDs, member IDs, timestamp ordering and measured/physical concentration semantics. Record every input SHA-256 and the materializer source SHA.

## Stage 1 — immediate existing-member LOMO

Run on any currently complete H01 bank with >=4 nuisance members and a common trajectory. If an existing 4-member reserved tensor is already available, use it now; otherwise use the existing 8-member train tensor. One held-out member generates all source observations and is removed from every candidate-source predictive ensemble.

```bash
python3 experiments/cg_pc_ctt/pf_dei_offline_coherent_audit.py \
  --mode lomo \
  --bank <EXISTING_CANONICAL_H01_NPZ> \
  --output <OUT>/H01_existing_lomo_coherent_audit.json
```

This is diagnostic. Do not replace the independently running strict train8-vs-reserved audit with this result.

## Stage 2 — strongest existing-data CROSS audit

When both already-generated tensors are available on the identical frozen trajectory grid:

- predictive bank = 8 train nuisance members;
- observation bank = independent reserved nuisance members.

```bash
python3 experiments/cg_pc_ctt/pf_dei_offline_coherent_audit.py \
  --mode cross \
  --predictive-bank <H01_TRAIN8_CANONICAL_NPZ> \
  --observation-bank <H01_RESERVED_CANONICAL_NPZ> \
  --output <OUT>/H01_train8_vs_reserved_coherent_audit.json
```

The generating reserved member must never appear inside the predictive ensemble.

## What is being compared

### A. `level`

Multivariate energy score on the complete physical sequence. It is a valid source-separability baseline but is exactly invariant to a common permutation of all time coordinates under Euclidean distance. Therefore it cannot by itself validate a temporal-order claim.

### B. `causal`

A frozen diagnostic embedding containing level plus backward lag increments. Channel scales are fit from the predictive bank only. Current default lags are diagnostic, not a final paper estimator. Do not tune them from source-rank results.

### C. `coherence_scramble`

Deterministically reassign nuisance-member identity between time blocks while preserving the exact per-time set of member values. If coherent trajectories contain source information, the intact-member causal score should outperform this ablation.

### D. `time_shuffle`

Deterministically permute prediction time blocks while leaving the observed chronological sequence intact. If chronological dynamics matter, intact ordering should outperform this negative control.

### E. permutation/null

Candidate-label permutation is used only to assess whether source ranking is beyond label chance.

## Interpretation — no outcome tuning

Report the raw values and use the following scientific interpretation, not a new threshold search:

1. **Source information present, temporal/coherence mechanisms present**
   - held-out source ranking is clearly better than permutation/null;
   - intact causal representation improves paired ranks relative to time-shuffle;
   - intact coherent members improve paired ranks relative to coherence scramble.
   Then retain the physically closed + coherent chronological method core.

2. **Source information present, but temporal/coherence controls do not hurt**
   - keep the physically closed predictive ensemble as useful;
   - drop or soften the claim that temporal order/member coherence is the source of the gain;
   - do not force a TCN/recurrent architecture merely to preserve a claim unsupported by the data.

3. **Level score is as good as or better than causal score**
   - prefer the simpler training-free level/predictive inference for the next experiment;
   - temporal neural machinery is not justified by this diagnostic.

4. **Held-out source ranking is near permutation/null**
   - stop neural rescue;
   - the current predictive family/nuisance support, not network capacity, is the limiting object.

## Stage 3 — optional amplitude/Q diagnostic, never a benchmark gate

Only after the core CROSS result is frozen:

```bash
python3 experiments/cg_pc_ctt/pf_dei_offline_coherent_audit.py \
  --mode cross \
  --predictive-bank <H01_TRAIN8_CANONICAL_NPZ> \
  --observation-bank <H01_RESERVED_CANONICAL_NPZ> \
  --amplitude-stress \
  --output <OUT>/H01_train8_vs_reserved_amplitude_stress.json
```

Scales `0.5,0.75,1,1.5,2.0` are predeclared engineering stress values. This does not change the frozen Q=10 benchmark. If ranking collapses under scale shift, the real-world contract must marginalize or externally calibrate source strength Q before any localization outcome is observed.

## Required return package

Return exactly:

- selftest output;
- canonical input paths and SHA-256 hashes;
- source/member/sample dimensions;
- LOMO JSON if available;
- train8-vs-reserved CROSS JSON when available;
- wall time and peak RSS;
- a short table with `level`, `causal`, `coherence_scramble`, `time_shuffle` Top-5 and median normalized rank;
- paired `coherence_test` and `order_test` counts/p-values;
- permutation/null p-values;
- any schema/provenance failure.

Then STOP. Do not start shared/LOHO training automatically.
