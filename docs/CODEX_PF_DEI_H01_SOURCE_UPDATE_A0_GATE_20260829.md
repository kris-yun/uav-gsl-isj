# CODEX — H01 actual-source-update + A0 gate before closed loop

Date: 2026-08-29
Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`
Priority: run before any PF-DEI ON closed-loop matrix
Expected wall time: seconds to a few minutes after existing-bank views are available

## Purpose

The completed H01 historical seed0..9 replay established useful terminal physical ordering and strong M2 nuisance-marginalization value, but exposed two pre-closed-loop blockers:

1. arbitrary early prefixes can rank the true carrier very poorly;
2. A0 (`q0 * exp(Gaussian-rank evidence)`) can select a different carrier even when the raw physical score ranks the true carrier first.

The old `-M1` replay is also not interpretable because it compared measured M with physical C. The branch now contains a corrected C++ M1 ablation and a new exact source-update Python replay.

No neural training is authorized. No new GADEN simulation is authorized.

## 1. Pull and provenance

Pull the branch latest HEAD. Record HEAD and dirty status.

Required new files/changes include:

- `experiments/cg_pc_ctt/pf_dei_h01_source_update_replay.py`;
- corrected measured-domain M1 ablation in `PFDEIEngine.hpp`;
- Python/C++ consistent M4 deletion semantics in `PFDEIModularRuntime.hpp`;
- `docs/PF_DEI_H01_10SEED_POST_REPLAY_DECISION_20260829.md`.

Do not overwrite the original H01 10-seed replay package or its V1 output.

## 2. Reuse only existing data

Inputs:

- frozen `CG_PC_CTT_V3_ORR_FULL60_PACKAGE_20260827.tar.gz`;
- existing audited `PF_DEI_V3_HISTORICAL_NATIVE_BANK_V1`;
- H01 seed0..9 -> stream0..9 schedule-hash mapping already proven PASS;
- eight frozen H01 training nuisance members;
- the previously materialized `H01_seed{0..9}_candidate_physical.npz` views if still present.

If those NPZ views were deleted, recreate only the views from the already-existing 1680 verified H01 shards. This is indexing/materialization, not GADEN generation. Do not regenerate physical fields.

## 3. Run exact source-update replay

Use the actual historical `context_bank/source_update_timing.csv` times, not 25/50/75% fractions.

Run `pf_dei_h01_source_update_replay.py` for seeds0..9. Supply the H01 3-D support manifest so candidate posterior expected XY can be computed. If exact controlled-release truth XY is available from the frozen evaluator/config, provide it only as evaluation arguments after scoring; otherwise omit the XY error fields rather than guessing.

For every one of the 50 actual source updates and every mode FULL/-M1/-M2/-M3/-M4, preserve:

- source-update id and sim time;
- last causal sensor timestamp;
- measured/aligned sample count;
- raw physical-score true-carrier rank and normalized rank;
- raw Top1/5/10;
- true-vs-best-rival score margin;
- q0 true-carrier rank;
- A0 posterior true-carrier rank;
- A0 rank shift = posterior rank - raw rank;
- posterior truth mass, max mass and entropy;
- selected source id;
- posterior expected XY/error if exact evaluation truth is supplied.

## 4. Correct M1 semantics

The only admissible M1 removal is:

- FULL: `M_obs -> inverse sensor -> C_obs`, score against `C_sim`;
- `-M1`: keep `M_obs`, run every `C_sim` through the same frozen delayed first-order sensor `T`, score `M_obs` against `T(C_sim)`.

The first fixed delay samples are dropped from both measured-domain sequences. M2/M3/M4 must otherwise be unchanged.

Never compare `M_obs` directly with `C_sim`.

Run a parity smoke using an archived H01 true physical trace as evaluation-only input and require forward-sensor reconstruction error at serialization scale (the independent local check found worst error about `7.2e-7 ppm`).

## 5. Python/C++ static parity repair

Compile/run the minimal modular C++ selftest before any ROS integration. In particular verify:

- FULL path level normalization matches Python;
- `-M4` removes only the adjacent-difference channel and preserves the same `1/sqrt(T)` level normalization;
- clean `-M1` compares measured-domain observation/predictions;
- M1 forward then inverse recovery matches within floating-point/serialization tolerance.

Do not change formulas to fit source-ranking results.

## 6. Frozen interpretation

Do not tune anything from this replay.

Report separately:

### A. Online physical-ordering gate

At source updates 1..5, aggregate across 10 seeds:

- raw Top5;
- raw median normalized rank;
- number of severe raw failures (`normalized rank > 0.5`).

If early actual updates are near-null or repeatedly severe, direct PF-DEI is not online-ready. STOP before closed-loop ON. Do not rescue with a network.

### B. A0 preservation gate

For each update and overall, report counts where A0:

- improves true rank;
- ties raw rank;
- worsens true rank.

Also compare raw Top5 vs posterior Top5 and, if available, expected-location error vs geometry prior.

If raw physical ordering is useful but A0 systematically destroys it, STOP before ON and declare `PFDEI_A0_CALIBRATION_BLOCKER`. Do not delete q0, force raw top1, or tune a temperature on H01 outcomes.

### C. Module evidence

- M2 is already supported by terminal replay; check whether this remains true at actual updates.
- M3/M4 are currently unsupported. They remain paper modules only if actual-update results provide consistent pre-outcome evidence. Otherwise remove/weaken these claims before formal closed loop.
- M1 must be judged only from the corrected same-domain ablation.

## 7. Network rule

Do not launch the proposed TrajCast/autoregressive trajectory network. Current H01 evidence does not support M3/M4 as the neural core.

If later a neural backend becomes necessary, its target must be reconsidered after this gate. The strongest current signal is M2 predictive-distribution marginalization and the current weakness is evidence calibration / tail robustness, not demonstrated temporal-state inference.

## 8. Return and STOP

Return one compact package containing:

- exact command and HEAD;
- source-update replay JSON/CSV;
- per-update aggregate table;
- A0 preservation table;
- corrected M1 comparison;
- Python/C++ selftest logs;
- wall time;
- hashes.

Then STOP. Do not start shadow or ON closed-loop until this gate is interpreted.
