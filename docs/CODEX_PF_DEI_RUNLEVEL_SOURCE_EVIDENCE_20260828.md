# CODEX TASK — PF-DEI run-level physical source evidence before SBI

Date: 2026-08-28

Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

This task starts only after all of the following are preserved:

- `PF_DEI_FORWARD_OPERATOR_CLOSED` (`a504e0e` work must not be lost);
- independent sensor-memory audit (`6fbf08c` work must not be lost);
- exact deconvolution result (`33f9a80` work must not be lost): 30/30 runs, 4049/4049 blocks, 159 native/ideal decision flips, truth-blind.

Read first:

- `docs/CG_PC_CTT_PF_DEI_SENSOR_GENERATIVE_CHAIN_FREEZE_20260828.md`
- `docs/PF_DEI_EXACT_SENSOR_DECONVOLUTION_DERIVATION_20260828.md`
- `docs/PF_DEI_RUNLEVEL_SOURCE_EVIDENCE_DERIVATION_20260828.md`

Reference code:

- `experiments/cg_pc_ctt/pf_dei_inverse_sensor_reference.py`
- `experiments/cg_pc_ctt/pf_dei_runlevel_energy_reference.py`
- `experiments/cg_pc_ctt/selftest_pf_dei_runlevel_energy_reference.py`

This task supersedes any instruction to train a neural SBI/NRE immediately.  It does not authorize source truth, localization error, C++, Active Probe or 60-arm experiments.

## Stage 0 — provenance merge/freeze

Preserve the local/work commits and evidence packages above.  Do not reset them away merely because the public research branch has different HEAD.

Before any new GADEN simulation, freeze exact hashes for:

- deployed ROS overlay source/config;
- native GADEN shared library/source;
- native sensor source/config;
- candidate source grid and geometry prior;
- transport nuisance/member definitions;
- trajectory/pose/timestamp input manifest for each of the 30 archived OFF runs.

The historical `/dev/shm` overlay loss remains documented; every newly launched simulation in this task must have reproducible overlay hashes.

## Stage 1 — run reference selftest

Run:

```bash
python3 experiments/cg_pc_ctt/selftest_pf_dei_runlevel_energy_reference.py
```

Required:

`PF_DEI_RUNLEVEL_ENERGY_REFERENCE_SELFTEST PASS`

Also repeat the inverse selftest.  No score parameter may be fitted from H01/H02/H03 observed source-evidence outcomes.

## Stage 2 — materialize candidate physical forward traces only

For every House/seed historical OFF trajectory:

1. use the exact historical robot poses/timestamps and causally available wind/runtime state;
2. use the frozen source candidate grid and geometry prior `q0`;
3. for every candidate source, generate at least the frozen set of source-independent transport nuisance draws using the closed native GADEN physical-concentration path;
4. each draw must be coherent over the complete evaluated run timeline/segment; do not construct a trace by choosing the best member separately at each sample;
5. never read historical true source, localization error or ON/OFF performance;
6. output physical concentration in ppm on the same sample grid as the deconvolved historical trace;
7. record source/member keys and all forward hashes.

Preferred compact payload per run:

- `observed_physical_ppm [T]` = the already frozen truth-blind deconvolved `C_hat`;
- `candidate_physical_ppm [S,M,T]`;
- `geometry_prior [S]`;
- `source_xy [S,2]` or source carrier IDs;
- `member_key [M]`;
- timestamps `[T]`;
- House/seed only as metadata, never as a predictive input.

Do not generate native-sensor candidate traces yet unless needed for Stage 4 parity; the physical candidate ensemble is the normative source-forward object.

## Stage 3 — truth-blind physical run-level source score

Use raw physical ppm and the frozen energy-score reference.  Do not introduce learned features, hand weights, log/asinh transforms, temperature or House-specific normalization after observing results.

For every run:

- compute whole-run candidate source scores;
- compute the source-independent prior-predictive null score using `q0(s)` and the same transport member weights;
- run five-bin chronological blocked forward validation using the reference implementation;
- for every split report prefix-selected source ID, heldout rank, heldout absolute gain versus null and rival margin;
- report the pre-frozen run `predictive_pass`.

No true-source correctness is reported.

Aggregate exactly:

- total predictive-pass runs /30;
- H01/H02/H03 predictive-pass /10;
- mean/median heldout absolute gain by House;
- mean/median heldout rival margin by House;
- heldout top-1 and rank distributions;
- source-score/null permutation tests.

Pre-frozen actionability rule:

- >=20/30 predictive-pass;
- >=5/10 predictive-pass in each House.

Do not alter this rule after results.

## Stage 4 — A1/A2 canonical parity, not two separately trained models

Because the frozen native sensor is source-independent and exactly invertible on the common interval, correctly modelled A1 and A2 source evidence should agree.

For a representative subset first, then all runs if cheap:

### A1

- observed: deconvolved physical `C_hat`;
- candidate: GADEN physical `C_s,m`.

### A2

- observed: historical native measured ppm;
- candidate: exact native persistent sensor applied to the same `C_s,m`;
- canonicalize both observed and candidate native sequences through the same frozen inverse before the normative energy score.

Require:

- identical recoverable interval;
- selected-source/rank parity except numerical ties;
- candidate score and source-independent null score parity within a tolerance derived before observed evaluation from forward/inverse numerical and six-decimal serialization bounds.

If A1/A2 parity materially fails, stop:

`RUNLEVEL_INFERENCE_OPERATOR_NOT_QUALIFIED`.

Do not call this sensor information loss.

## Stage 5 — frozen scientific verdict

Return exactly one:

### `PHYSICAL_RUNLEVEL_SOURCE_FORWARD_ACTIONABLE`

Only if Stage 3 satisfies >=20/30 overall and >=5/10 each House, and Stage 4 parity passes.

Interpretation: the physical run-level source/transport forward family carries transferable truth-blind source information.  The old occupancy/context-local representation is the primary identified failure mechanism.  A learned run-prefix SBI/NRE may then be designed as an online approximation, but localization performance remains closed.

### `FINITE_TRANSPORT_OR_SOURCE_FORWARD_STILL_INSUFFICIENT`

If Stage 4 parity passes but Stage 3 fails the frozen actionability rule.

Interpretation: sensor-state misattribution is real, but after exact correction the remaining candidate source/transport forward family is still not predictively adequate.  Do not tune the scoring rule.  Proceed to a separately frozen source-independent physics-randomized GADEN transport expansion before any neural SBI.

### `RUNLEVEL_INFERENCE_OPERATOR_NOT_QUALIFIED`

If reference/selftests/permutation/null/A1-A2 parity fail.

No localization performance may be opened from this task.

## Stage 6 — required artifacts

Commit:

- materializer/build script(s);
- candidate payload manifest with hashes;
- per-run/per-split CSV;
- aggregate JSON;
- `docs/PF_DEI_RUNLEVEL_SOURCE_EVIDENCE_RESULTS_20260828.md`;
- exact provenance hashes and invalid/missing counts.

The final response must state which of the three frozen verdicts applies and the exact H01/H02/H03 counts.
