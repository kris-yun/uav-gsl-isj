# CPIR pre-closed-loop P0 fixes — 2026-09-01

Status: `SOURCE_FIX_COMMITTED_PENDING_VM_BUILD_AND_BANK_BACKED_PARITY`

This note records code-level corrections applied after three-module alignment commit `e398e246272fe59c0d5c043331d96312b0ecf55a`. No GADEN bank is regenerated or scientifically changed.

## 1. Planner closure

Problem: CPIR source updates replaced `Simulations::updateSourceProbability()`, while the PMFS controller still reads planner-side forward products such as `resultsFirstLevel` and `varianceOfHitProb`. In CPIR mode these could therefore be zero or stale.

Fix: at every source-update boundary in CPIR mode, run the native PMFS update **first** to refresh planner-side predictive products, validate the planner variance map, then overwrite the transient native source posterior with the frozen CPIR A1/A2/A3 posterior.

```text
native PMFS forward refresh
    -> resultsFirstLevel / varianceOfHitProb
    -> transient native sourceProbability (discarded)
CPIR applyCPIRPosterior
    -> final sourceProbability exposed to estimator/logging
PMFS controller
    -> retains native truth-blind predictive planning products
```

This intentionally does **not** add posterior blending or a fourth planner module. `posterior_guidance_weight` is forced to zero for CPIR. The baseline PMFS active-sensing controller remains the navigation policy while M1/M2/M3 replace the source-inference channel.

Fail-closed checks:

- planner variance size equals the source grid size;
- every free-cell variance is finite and non-negative;
- at least one free-cell variance is positive;
- `resultsFirstLevel` is non-empty.

Because the controller is intentionally baseline-preserving, paired OFF/ON trajectory equivalence is now a required diagnostic whenever observation tapes and RNG seeds are otherwise identical. A path divergence must be explained before it can be treated as a valid CPIR effect.

## 2. Seed propagation bug

The GSL node previously received `random_seed` but not the `seed` parameter that `PMFS::configureNativeDeterminism()` actually reads. This could make native planner RNG silently use seed 0 across nominal paired seeds.

The launch now passes both from the same experiment seed.

## 3. Runtime cadence: explicit recovery, not guesswork

A prior draft incorrectly tried to freeze `stepsSourceUpdate=3` from a development replay. That is too strong: repository history also contains a paired PMFS runner whose default cadence is 10 and whose acceleration studies override it to 3.

The fix therefore does **not** infer the authoritative cadence.

Formal A0/A1/A2/A3 launches must explicitly provide values recovered from the exact frozen paired PMFS parameter manifest:

- `cpir_expected_steps_source_update`;
- `cpir_expected_max_warmup_iterations`;
- `cpir_expected_min_warmup_iterations`.

The launch fails if these do not equal the actual runtime values. `tools/cpir_formal_preflight.py` likewise requires these values and deliberately refuses to guess them.

Other fixed observation contracts remain:

- `deltaTime=0.2 s`;
- 80 native samples / physical stop;
- zero settle samples;
- `measurement_deduplicate_sim_timestamps=true`;
- `th_gas_present=0.1 ppm`;
- sensor metadata `fopdt_tau1p2_dead0p4_noise0` with dynamic sensor mode.

## 4. Bank / House provenance

Every CPIR ON launch requires explicit:

- `cpir_expected_house`;
- `cpir_expected_bank_summary_sha256`;
- `cpir_expected_cell_manifest_sha256`;
- `cpir_integrity_report`;
- `cpir_lookup_root` and audit directory.

Before ROS nodes start, the launch validates:

- `CPIR_FULLGRID_LOOKUP_V1` / PASS;
- exact House identity;
- 8 predictive members / 1500 samples;
- 8 unique prediction transport keys;
- frozen prediction and external-observation RNG-domain labels;
- bank summary SHA;
- cell manifest SHA and summary consistency;
- independent `CPIR_LOOKUP_INTEGRITY_PASS` report consistency;
- House-specific dataset/config/source metadata.

`tools/cpir_formal_preflight.py` prints the exact launch arguments from an already-generated bank and integrity report.

Boundary: runtime has no hidden observation-world member id. Therefore this proves file/domain separation, but must not be described as a stronger numerical identity test between the external GADEN observation realization and every synthetic prediction draw unless additional metadata is independently recovered.

## 5. Sensor contract

The formal metadata/launch is pinned to `fopdt_tau1p2_dead0p4_noise0` and dynamic sensor mode, matching M2's candidate operator:

`tau=1.2 s`, `dead time=0.4 s`, `dt=0.2 s`, `threshold=0.1 ppm`.

A live VGR impulse/step response parity test is still required because metadata alone does not prove implementation parity.

## 6. Remaining gates before formal closed loop

1. Recover the authoritative source-update and warmup values from the exact paired PMFS runtime/parameter manifest; do not infer them from a development replay.
2. VM Release build from the fix commit.
3. Run the bank-free contract selftest.
4. Run `tools/cpir_formal_preflight.py` for H01/H02/H03 against the existing banks.
5. One immutable tape: Python reference vs C++ A1/A2/A3 posterior max-abs difference <= `1e-12`.
6. Repeat one parity case on H02 and H03.
7. Live observation sensor impulse/step parity for M2.
8. Official evaluator tie/row-order permutation audit for the carrier-to-cell interface.
9. Measure native planner refresh and `applyCPIRPosterior` wall time.
10. Run nested fixed-trajectory `A0 -> A1 -> A2 -> A3` on all 30 historical pairs.
11. Require controller-preserving OFF/ON path equivalence when the paired observation/RNG contract predicts identical trajectories.
12. Only if M2 and M3 have independent cross-House increments, run one paired closed-loop smoke, then the preregistered formal paired test.

No bank regeneration, temperature/blend/Top-K rescue, M2 parameter tuning, M3 pseudo-count tuning, dynamic/coherent-K revival, or neural rescue is authorized by these fixes.
