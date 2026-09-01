# CPIR three-module bank-free review

Date: 2026-09-01

Verdict: `THREE_MODULE_SOURCE_AND_BUILD_PASS_BANK_NOT_OPENED_RUNTIME_PARITY_PENDING`

## Boundary

This review did not open, hash-scan, replay, copy, or regenerate any CPIR bank
payload. The frozen generator
`experiments/cg_pc_ctt/ctt_final_hazard_20260830/materialize_cpir_fullgrid_lookup.py`
is unchanged. All changes are downstream inference, PMFS interface, launch
guard, documentation, or bank-free test changes.

## Module review

- **M1 / CSPI: PASS at contract boundary.** Candidate-conditioned native
  GADEN fields remain the only main mechanism. Each of the eight members is
  documented as a joint within-carrier source-placement/height/transport
  nuisance atom, marginalized independently at each stop; it is not a temporal
  latent state.
- **M2 / PSST: PASS in source and synthetic parity.** `cpir_a2` and `cpir_a3`
  carry the delayed first-order sensor state through motion, stops, and source
  updates. `cpir_a1` is the clean memoryless comparator. The measured sensor
  tape is not filtered a second time.
- **M3 / SRDCL: PASS in source and synthetic parity.** Only `cpir_a3` uses the
  stop-resolved Bernoulli composite score. A1/A2 and historical `cpir_m1` keep
  the count-collapsed comparator. No exact joint turbulent likelihood is
  claimed.
- **Carrier-to-cell interface: PASS in source and synthetic parity.** It is a
  KL/I-projection under the frozen uniform geometry-only pre-gas reference,
  not a fourth module.

## Defects found and repaired before bank use

1. The CPIR launch still selected `SensorAwareSurgeCastPF`, contained duplicate
   launch arguments, used 1.0 m flight height, and formed only 30 samples per
   stop. It now requires `PMFS`, an explicit A0/A1/A2/A3 arm, 0.3 m height,
   zero settle samples, and exactly 80 samples at 0.2 s.
2. The runtime checked only the number of manifest cells. It now rejects any
   occupied/out-of-range manifest row and any missing runtime free cell.
3. The Python I-projection helper silently accepted a posterior carrier with no
   reference cells. It now fails closed.
4. The first VM compile exposed a missing `GSL::` qualifier on `Vector2Int` in
   `carrierIdForCell()`. The qualifier was added and the incremental build then
   passed.

## Verification

- `CPIR_THREE_MODULE_REFERENCE_SELFTEST=PASS`
- `CPIR_THREE_MODULE_BANK_FREE_CONTRACT_SELFTEST=PASS`
- `PF_DEI_MODULAR_SELFTEST PASS`
- Python syntax checks: PASS
- JSON parse and `git diff --check`: PASS
- Isolated VM root: `/dev/shm/cpir_runtime_review_20260901_r1`
- Final VM build: `3 packages finished`; final `gsl_server/stderr.log` has 0 lines
- Built executable:
  `/dev/shm/cpir_runtime_review_20260901_r1/install/gsl_server/lib/gsl_server/gsl_actionserver_node`
- Executable SHA-256:
  `fc8d10f51298f89e4214bc07cd0f853c1060292072382d070367118beb6746bc`
- Local and VM `CPIR.cpp` SHA-256:
  `278e86e96542658cad8953a08b7cf8ff8ba6c30e290fcffe65af782a96a6ff26`

## Remaining boundary

This is not bank-backed runtime parity, a fixed-trajectory nested result, or a
closed-loop result. The next scientific step must remain A0/A1/A2/A3 nested
parity on one immutable tape, followed by the preregistered shadow matrix. Do
not regenerate the bank for M2, M3, projection, or launch-only changes.
