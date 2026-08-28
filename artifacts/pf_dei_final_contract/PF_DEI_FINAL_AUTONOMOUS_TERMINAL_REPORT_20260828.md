# PF-DEI-SR final autonomous closed-loop report

Date: 2026-08-28
Terminal status: `STOP_PF_DEI_SOURCE_SUPPORT_IDENTITY_UNRESOLVED`

## Frozen execution base

- Requested remote: `research/cg-pc-ctt-v6-dynamic-transport-sbi`
- Requested remote HEAD: `04339884b54694481d01c077595406a4ae899dc6`
- Active local branch: `codex/pf-dei-final-autonomous-closed-loop-20260828`
- Active local HEAD before evidence commit: `119ff43`; evidence/report is committed on the active branch immediately after that merge.
- Preserved history objects verified present: `a504e0e`, `6fbf08c`, `33f9a80`, `55dd893`
- No reset or overwrite was used. The four preserved commits remain reachable through the merge history.

## Reference selftests completed before the hard gate

All six current PF-DEI reference selftests passed on the VM copy of the active source:

| Test | Result |
|---|---|
| `selftest_pf_dei_physical_bank_contract.py` | `PF_DEI_PHYSICAL_BANK_CONTRACT_SELFTEST PASS` |
| `selftest_pf_dei_runlevel_energy_reference.py` | `PF_DEI_RUNLEVEL_ENERGY_REFERENCE_SELFTEST PASS` |
| `selftest_pf_dei_inverse_sensor_reference.py` | `PF_DEI_INVERSE_SENSOR_REFERENCE_SELFTEST PASS` |
| `selftest_pf_dei_observation_contract.py` | `PF_DEI_OBSERVATION_OPERATOR_CONTRACT_SELFTEST PASS` |
| `selftest_pf_dei_phase_marginal_reference.py` | `PF_DEI_PHASE_MARGINAL_REFERENCE_SELFTEST PASS` |
| `selftest_pf_dei_sensor_history_counterfactual.py` | `PF_DEI_SENSOR_HISTORY_COUNTERFACTUAL_SELFTEST PASS` |

The inverse selftest also reported `max_abs_physical_recovery_ppm=1.4210854715202004e-14`; this is only sensor/deconvolution evidence, not source-localization evidence.

## Source-support audit

The only surviving persistent carrier manifests contain:

`carrier_index,carrier_id,x,y,free_cells`

They do not contain an authoritative `z` coordinate, native GADEN source-node identifier, or a mapping from each carrier to a native GADEN source configuration. The 150 geometry-only context NPZ payloads likewise contain no `source_xyz` field. Their stable support sizes are H01=210, H02=201, H03=206, and the corresponding manifests were copied without modification:

| Manifest | Rows | SHA-256 |
|---|---:|---|
| `H01_persistent_carriers.csv` | 210 | `9822fabce119920c9a073c2ff0cf292e1e051ea05d67ef446e1840bda6103df4` |
| `H02_persistent_carriers.csv` | 201 | `bbe4971ec33bfc13f1d152623ef9f12200ff852b0f2f57b0efafc4c73b3afa89` |
| `H03_persistent_carriers.csv` | 206 | `8ba99c2599edf148a864b1aa6b36ba5dadc79f875cf2333d3e7c0b6966cc4778` |

The historical House launch files expose source-location parameters for the particular recorded source fields, but those values are source-truth/location fields and cannot be used to assign a candidate support z-coordinate before the truth-free stage. They also differ by House, so a global assumed height would not be source-proven.

Therefore the required identity

`stable source id <-> native GADEN xyz <-> geometry_prior mass`

is not proven. Assigning `z=0.2`, copying a historical source z, or treating occupancy cell centers as ppm/source coordinates would violate the final method contract.

## Stages not run by contract

Because the first hard source-support gate failed, the following were not started: source-strength/nuisance freeze, complete native physical candidate bank, source-independent trajectory dataset, causal-TCN NRE training, reserved synthetic qualification, 30-run truth-blind predictive qualification, runtime `pfdei_sr`, six smoke runs, 60-arm development, and seeds10..19 confirmation. No historical `true_gas_ppm`, true source, future observation, occupancy-to-ppm conversion, Active Probe, architecture sweep, Gate/temperature/blend, or result-driven transport expansion was used.

This is a provenance/identity stop, not a scientific performance NO-GO. The next permissible action is to obtain an authoritative, source-independent carrier-to-native-GADEN `(x,y,z)` support manifest (including geometry-prior alignment) and then restart the final contract from Section 1. No downstream result can be interpreted scientifically until that artifact exists.
