# OCB-R2 D0A source-comparability audit

**Decision: `OCB_R2_D0A_SOURCE_COMPARABILITY_HOLD`.** The enclosing D0 decision is `OCB_R2_D0_HOLD_COMPARABILITY`. No scientific score was computed.

## Frozen inputs and audit scope

- D0 preregistration: `research/ocb_r2/OCB_R2_D0_MARGINAL_PRESERVING_DEPENDENCE_GATE.md`, committed before this audit at `810d1ac0b6a938e2e0e9acd7ce050711e3ddc5da`.
- Qualified S2 runlist: SHA256 `f1d8604b49a74ba3ab698f445a2c1e381d84164c809e1bcf8b0f08beddf40974`.
- Frozen prospective generator: SHA256 `ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`.
- The script `audit_d0a.py` read only S2 runlist, run manifests and structural QC JSON. It did not open concentration/filament payloads or score a source. Its eight configuration rows and exact asset hashes are in `evidence/ocb_r2/d0/D0A_CONFIG_CONTRACTS.tsv`.

## S2 candidate comparison

Grouping all 32 discovery runs by House, occupancy hash, wind-bundle hash, gas type, native timeline hash, wind-index sequence hash and frozen generator hash gives **eight** non-source strata. Each stratum has **four realizations of exactly one source position**. Source 1 and source 2 differ in wind family and gas type within both houses:

| House | Source 1 | Source 2 | Shared source-comparison environment? |
|---|---|---|---|
| House01 | `(-0.6,1.95,0.4)`, gas 13, `1,3-2,4` fast/slow | `(-0.4,-2.9,-0.3)`, gas 10, `2,4-1` fast/slow | No: wind and gas change with source. |
| House02 | `(0,-1,0.2)`, gas 10, `3,5-1` fast/slow | `(1,-2.3,-0.1)`, gas 13, `4,5-3` fast/slow | No: wind and gas change with source. |

The 32 samples support within-configuration stochastic analysis, but a source rank across these eight labels would confound source with wind and gas. Replicates increase realization count; they do not create a second candidate source under fixed conditions.

## Existing read-only forward banks

The inventory in `evidence/ocb_r2/d0/D0A_EXISTING_BANK_AUDIT.tsv` records the relevant candidate banks checked in the repository and VM; `D0A_BANK_METADATA_SHA256.tsv` records their metadata hashes. The repository and VM metadata searches found the frozen OCB-R2 binary hash only in OCB-R2 build/run/qualification records, not in an additional candidate forward bank.

- The historical House01 wind-alignment bank has 87 PMFS candidate hit maps and 20 historical sensor events. Its replay binary SHA is `59a1751f...`, not the OCB-R2 GADEN SHA; its observation process is different.
- The marked-encounter bank has 1584 PMFS forwards across older OPEN environments and 0.30 m PMFS moment maps. Its historical PMFS binary SHA is likewise `59a1751f...`; it does not supply prospective OCB-R2 raw trajectories at the same readout and timebase.
- The historical HCMC context bank is a Native PMFS adaptive-update bank, not a same-condition OCB-R2 GADEN realization ensemble.
- The legacy Bi-Green Gate1A bank does have 630 House02 candidate sources, but uses 10 historical record IDs and two old prediction seeds. Its contract does not identify the frozen OCB-R2 binary, native 1803-record timebase, or a House01 counterpart. The original VM contract was copied without scientific outputs and checked SHA256 equal at source and destination: `68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334`.

Some legacy banks share House geometry or an input wind name; that alone does not establish the identical generator, time/readout and reference-ensemble contract required by D0A. None of the audited existing banks can supply the missing provenance-compatible same-condition source hypotheses for both H01 and H02.

## Stop boundary

D0A fails before an observation operator is frozen. `D0_OBSERVATION_CONTRACT.json` therefore records observation coordinates, times and readout as null. No M0, P, Q-time, residual, null or source-rank result exists; the later D0 score tables are intentionally absent. Confirmation replicates 5–8 were neither generated nor opened, and H03 remains `SEALED_NOT_RUN`.

The S2 dataset PASS remains valid as a reproducible prospective stochastic bank. This HOLD is about the **source-comparison task definition** in D0, not about simulator QC or whether cross-time dependence exists.
