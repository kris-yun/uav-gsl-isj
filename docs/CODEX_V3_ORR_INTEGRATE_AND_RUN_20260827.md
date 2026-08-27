# Codex directive — integrate V3-ORR and go directly to full closed loop

Date: 2026-08-27
Branch: `research/cg-pc-ctt-v3-observation-quotient-theory`

## Binding decision

STOP all additional H02 bank generation, hard-28 recovery, bridge-panel gating, post-bank pre-outcome gating, and small-seed method tuning.

The H02 reconstructed bank is already verified and sufficient as a development asset. The next performance experiment is the frozen 60-arm matrix after one infrastructure-only smoke.

Read first:

`docs/CG_PC_CTT_V3_DIRECT_CLOSED_LOOP_FREEZE_20260827.md`

Do not change its mathematics or criteria.

## 1. Baseline selftests

```bash
git fetch origin
git checkout research/cg-pc-ctt-v3-observation-quotient-theory
git pull origin research/cg-pc-ctt-v3-observation-quotient-theory
cd experiments/cg_pc_ctt
bash run_v3_selftests.sh
```

Required:

`CG_PC_CTT_V3_DIRECT_RUNTIME_SELFTEST PASS`

and final:

`CG_PC_CTT_V3_STATIC_AND_MATH_SELFTEST PASS`.

## 2. C++ integration only — no new method design

Runtime core already exists:

`ros2_package/src/gsl_server/algorithms/PMFS/internal/ObservationResolvedV3.hpp`

Reference parity implementation:

`experiments/cg_pc_ctt/v3_direct_runtime_reference.py`

Modify the existing PMFS code minimally.

### 2.1 Include and mode

In `Simulations.cpp` include `ObservationResolvedV3.hpp`.

Add explicit `pfdiMode == "v3_orr"` wherever persistent geometry-only carriers are enabled.

In the TADM/PFDI dispatch, route `v3_orr` through the existing EC-ECDL physical-response construction, but branch to V3 immediately after `rawProbabilities[source][replica][event]` has been fully populated and BEFORE historical Hellinger normalization/generalized-eigenchannel/conditional-ledger logic.

Do not execute the old EC-ECDL score path for `v3_orr`.

### 2.2 Adapter inputs

Build:

```cpp
std::vector<unsigned char> observedHit;
std::vector<uint64_t> blockId;
std::vector<std::array<int,4>> rectangles;
std::vector<long double> priorMass;
```

from:

- `pcAciActiveEvents[e].hit`;
- `pcAciActiveEvents[e].blockId`;
- `p2LastEvaluatedCandidates[s].rect`;
- `pcAciDesignPriorGrid` summed over free cells of each persistent carrier rectangle.

The prior MUST NOT come from the same-window native PMFS posterior.

Call exactly:

```cpp
auto result = GSL::PMFS_internal::v3_orr::compute(
    rawProbabilities, observedHit, blockId, rectangles, priorMass);
```

### 2.3 ABSTAIN

If `result.released == false`:

- `pcAciAcceptedThisUpdate = false`;
- if a previous accepted V3 causal posterior exists, copy `pcAciCausalPosteriorGrid` into `sourceProbInternal`;
- otherwise copy the fixed `pcAciDesignPriorGrid` into `sourceProbInternal`;
- never fall back to the current native same-window PMFS posterior;
- return success after writing the audit row.

### 2.4 RELEASE

If released:

- zero `sourceProbInternal`;
- for each persistent carrier `s`, distribute
  `result.candidateMass[s] / freeCellsPerSource[s]`
  uniformly over its free cells;
- normalize/check finite mass;
- set
  `pcAciCausalPosteriorGrid = sourceProbInternal`,
  `pcAciCausalStateAvailable = true`,
  `pcAciLastAcceptedUpdateId = tadmSourceUpdateId`,
  `pcAciAcceptedThisUpdate = true`;
- do NOT multiply by previous V3 posterior; each release is a reversible recomputation from current accumulated completed events and the fixed prior.

### 2.5 Audit

Write one append-only CSV, e.g. `v3_orr_update_audit.csv`, containing at least:

`run_uuid,source_update_id,sim_time,event_count,even_events,even_hits,odd_events,odd_hits,carrier_count,resolution_cells,resolved_edges,unresolved_edges,nuisance_rank,released,reason,source_probability_sum`

Also freeze the online binary SHA256 in the run output.

No source truth fields are allowed in this method audit.

## 3. Build and parity

Build a new isolated install root. Do not overwrite the frozen main ME-ACI install.

Suggested root:

`/dev/shm/cg_pc_ctt_v3_orr_20260827`

Compile with the existing ROS2 Humble overlay contract.

Run the Python selftests again after build. Add a small C++ synthetic/parity harness if compilation exposes any type/roundoff discrepancy; it must compare the C++ candidate masses and component IDs against the Python reference on a fixed synthetic fixture. Do not tune method parameters from real House outcomes.

## 4. One infrastructure-only smoke

Use a non-confirmatory seed outside 0..9, fixed now as:

`SMOKE_SEED=314159`

Use House02 and `pfdiMode=v3_orr` only long enough to verify:

- launch succeeds;
- V3 branch is reached;
- persistent carrier identities are stable;
- `rawProbabilities` are finite;
- both ABSTAIN and/or RELEASE leave a normalized posterior;
- audit is written;
- no NaN/Inf/segfault;
- clean timeout/exit;
- final posterior artifact is produced.

DO NOT inspect localization error or source truth to change the algorithm. Smoke truth may be used only by the outer evaluator after the online process exits; do not feed it to V3.

If smoke fails for an engineering reason, fix only the engineering defect and rerun the same smoke seed. No method-threshold change is authorized.

## 5. Freeze binary, then full matrix

Freeze:

- git commit SHA;
- binary SHA256;
- runtime/launch script SHA256;
- parameter manifest;
- `PFDI_MODE=v3_orr`;
- `STEPS_SOURCE_UPDATE=3` for BOTH OFF and ON matched arms;
- `TIMEOUT_SEC=300`;
- 8 keyed members;
- no House/seed-specific settings.

Use the existing truth-isolated wrapper:

`closed_loop/cg_pc_ctt/run_case_after_online_build.sh`

and matrix:

`closed_loop/cg_pc_ctt/run_multiseed_matrix.sh`.

Matrix is exactly:

`House01,House02,House03 x seeds 0..9 x OFF/ON = 60 arms`.

OFF = Classic PMFS, same cadence/runtime.
ON = V3-ORR.

No additional pilot subset is authorized between smoke and the full matrix.

## 6. Final verdict

Run the existing `aggregate_multiseed.py` unchanged.

Frozen GO criteria remain:

1. all 30 matched pairs valid;
2. pooled PMFS top-5 expected-value localization error reduction >=10%;
3. one-sided paired sign test p<=0.05;
4. no House pooled mean degrades >5%;
5. zero false-confident-collapse flags.

Return the entire matrix output plus aggregate JSON/CSV and all V3 audit files. Do not summarize only selected seeds.
