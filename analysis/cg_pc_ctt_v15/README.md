# CG-PC-CTT V15 offline qualification code

Candidate method name: **Completeness-Gated Proximal-Causal Transport Tomography**
（完备性门控近端因果输运层析）.

Status on branch creation: `CURRENTLY TESTING`.

This directory is intentionally isolated from the frozen CTT V13 M1 code.
Nothing here changes:

- `analysis/ctt_v13/ctt_m1_first_passage_gate.py`
- `analysis/ctt_v13/ctt_m1_ordering_gate.py`
- the M1 trace bank
- `main_v8`
- the 300 s closed-loop baseline

## Files

### `completeness_gate.py`

Runs directly on the frozen House03 CTT M1 bank and M1 direct-gate model.

It computes, for each local 9-candidate neighborhood, a transport-uncertainty
whitened source-response spectrum.

Definitions:

- `gamma = sigma_(K-1) / sigma_1`
- `alpha = sigma_(K-1)`

`gamma` is relative conditioning/rank. `alpha` is the absolute weakest source
contrast after transport uncertainty normalization.

Thresholds are calibrated only on CTT development contexts (`VAL_CONTEXTS`).
Final CTT test contexts and held-out transport members are untouched until the
thresholds are frozen.

The qualification endpoint is the already-frozen M1 matched-neighbor ordering
margin, not a new hand-picked score.

Run:

```bash
python3 analysis/cg_pc_ctt_v15/completeness_gate.py \
  /ABS/PATH/TO/CTT_H03_BANK \
  /ABS/PATH/TO/CTT_M1_DIRECT_GATE_OUTPUT \
  /ABS/PATH/TO/NEW/CG_PC_CTT_COMPLETENESS_RESULT
```

The output directory must not already exist.

Primary outputs:

- `completeness_gate_result.json`
- `completeness_gate_contract.json`
- `gate_atoms.csv`

Exit code is `0` only for `GO`; `2` means a scientific `NO_GO`, not a runtime
failure.

### `proximal_bridge.py`

Generic regularized sieve-GMM implementation of the project-specific proximal
bridge moment diagnostic:

`E[g(Z,S) * (Y - h(R,S))] = 0`.

Important:

- `Z` is candidate/source-side physical proxy and is used **only for moment
  fitting**, never as an input to `h` at inference.
- `R` must be identical for all candidate-source rows belonging to the same
  observed event.
- truth is allowed only as `is_true` in offline candidate panels, after model
  and ridge are frozen.
- no source truth, wind ID, route ID, plume seed, simulator phase, oracle field
  or future data may appear in runtime features.

The bridge expects four NPZ files:

1. train rows: `y, r, s, z`
2. development rows: `y, r, s, z`
3. development candidate panel: `event_id, candidate_id, is_true, y, r, s, z`
4. final test candidate panel: same panel schema

Every NPZ must have a sidecar file:

`<file>.npz.contract.json`

with all of the following set to `true`:

```json
{
  "runtime_forbidden_fields_absent": true,
  "r_candidate_independent": true,
  "source_coordinates_are_synthetic_interventions_or_queries": true,
  "test_not_used_for_tuning": true
}
```

Run:

```bash
python3 analysis/cg_pc_ctt_v15/proximal_bridge.py \
  train.npz dev.npz dev_panel.npz test_panel.npz \
  /ABS/PATH/TO/NEW/CG_PC_CTT_BRIDGE_RESULT
```

Outputs:

- `proximal_bridge_result.json`
- `proximal_bridge_contract.json`

The same fixed second-order sieve is used for the proximal bridge and its
direct-ridge comparator. Regularization is selected on development data only.

## Required execution order

Read `docs/CG_PC_CTT_V15_CODEX_EXECUTION_20260827.md` before running anything.

Do not start the 300 s closed loop until both offline gates are frozen.
