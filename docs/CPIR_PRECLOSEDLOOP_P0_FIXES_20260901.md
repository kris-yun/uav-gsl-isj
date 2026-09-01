# CPIR pre-closed-loop P0 fixes — 2026-09-01

Status: `SOURCE_FIX_COMMITTED_PENDING_VM_BUILD_AND_BANK_BACKED_PARITY`

This note records the final code-level corrections applied after the three-module source-alignment commit `e398e246272fe59c0d5c043331d96312b0ecf55a`.  No GADEN bank is regenerated or scientifically changed.

## 1. P0 planner closure

Problem: CPIR source updates replaced `Simulations::updateSourceProbability()`, but the PMFS controller still reads planner-side forward products such as `resultsFirstLevel` and `varianceOfHitProb`.  In CPIR mode these could therefore be zero or stale.

Fix: at every source-update boundary in CPIR mode, run the native PMFS update **first** only to refresh its planner-side predictive products, validate the planner variance map, then overwrite the transient native source posterior with the frozen CPIR A1/A2/A3 posterior.

The ordering is now:

```text
native PMFS forward refresh
    -> resultsFirstLevel / varianceOfHitProb
    -> transient native sourceProbability (discarded)
CPIR applyCPIRPosterior
    -> final sourceProbability exposed to estimator/logging
PMFS controller
    -> retains native truth-blind predictive planning products
```

This intentionally does **not** add a new posterior-guidance/blend module.  `posterior_guidance_weight` is forced to zero for CPIR.  The scientific contribution remains the source-inference chain M1/M2/M3 while the baseline PMFS active-sensing controller is retained as the navigation policy.

Fail-closed checks added:

- planner variance size equals the source grid size;
- every free-cell variance is finite and non-negative;
- at least one free-cell variance is positive;
- `resultsFirstLevel` is non-empty.

## 2. P0 paired timing contract

The historical fixed-tape CPIR evaluation contains five source updates after 3, 6, 9, 12 and 15 completed physical stops.  The formal paired launch is now frozen to:

- `stepsSourceUpdate=3`;
- `deltaTime=0.2 s`;
- `maxUpdatesPerStop=8`;
- `measurement_block_samples=10`;
- zero settle samples;
- 80 native samples / physical stop;
- `measurement_deduplicate_sim_timestamps=true`;
- `th_gas_present=0.1 ppm`.

These are checked before ROS nodes start.

A separate existing bug was also closed: the GSL node now receives the experiment `seed` parameter in addition to the benchmark `random_seed`.  `PMFS::configureNativeDeterminism()` reads `seed`; without this pass-through every paired seed could silently use native planner RNG seed 0.

## 3. P0 bank/House provenance

Every CPIR ON launch now requires explicit:

- `cpir_expected_house`;
- `cpir_expected_bank_summary_sha256`;
- `cpir_expected_cell_manifest_sha256`;
- `cpir_integrity_report`;
- `cpir_lookup_root` and audit directory.

Before launch, Python validates:

- `CPIR_FULLGRID_LOOKUP_V1` / PASS;
- exact House identity;
- 8 predictive members / 1500 samples;
- 8 unique prediction transport keys;
- frozen prediction and external-observation RNG-domain labels;
- bank summary SHA;
- cell manifest SHA and summary consistency;
- independent `CPIR_LOOKUP_INTEGRITY_PASS` report consistency;
- House-specific dataset/config/source metadata.

A read-only helper `tools/cpir_formal_preflight.py` prints the exact launch arguments from an already-generated bank and integrity report.

Important boundary: the runtime has no hidden observation-world member id.  Therefore the preflight proves file/domain separation, but must not claim a stronger numerical identity test between the external GADEN observation realization and every synthetic prediction draw unless such metadata is independently recovered.

## 4. Sensor contract

The formal metadata/launch is frozen to `fopdt_tau1p2_dead0p4_noise0` and dynamic sensor mode, matching M2's candidate operator:

`tau=1.2 s`, `dead time=0.4 s`, `dt=0.2 s`, `threshold=0.1 ppm`.

A live VGR impulse/step response parity test is still required before formal closed loop because metadata alone does not prove implementation parity.

## 5. What remains before any formal paired closed loop

1. VM Release build from this commit.
2. Bank-free contract selftest.
3. Run `tools/cpir_formal_preflight.py` for H01/H02/H03 against the already-generated banks.
4. One immutable tape: Python reference vs C++ A1/A2/A3 posterior max-abs difference <= `1e-12`.
5. Repeat one parity case on H02 and H03.
6. Live observation sensor impulse/step parity for M2.
7. Official evaluator tie/row-order permutation audit for the carrier-to-cell interface.
8. Measure `applyCPIRPosterior` and native planner-refresh wall time.
9. Run nested fixed-trajectory `A0 -> A1 -> A2 -> A3` on all 30 historical pairs.
10. Only if M2 and M3 have independent cross-House increments, run one paired closed-loop smoke; then the preregistered 9-pair formal test.

No bank regeneration, temperature/blend/Top-K rescue, M2 parameter tuning, M3 pseudo-count tuning, dynamic/coherent-K revival, or neural rescue is authorized by this fix.
