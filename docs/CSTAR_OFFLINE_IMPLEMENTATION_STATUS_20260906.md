# CSTAR offline implementation status — revised 2026-09-06

Branch: `g3-cstar-revise-before-exec-20260906`
Status: **REVISE_BEFORE_EXECUTION**

This file replaces the earlier status text that overstated the scientific
meaning of the spent offline layer.

## Current interpretation

The existing spent-data scripts are **premise/replay tools only**.

- M1 spent output: `CSTAR_M1_SPENT_REPLAY_PREMISE_V3`.
- M2 spent output: `CSTAR_M2_SPENT_OBSERVATIONAL_REPLAY_V2`.
- M3 is not required in the spent M1/M2 premise stage; a missing M3 panel there
  is not a scientific M3 failure.
- No spent replay result can authorize formal closed loop.

## Important corrections after review

### Trace ingestion

`common/trace_io.py` now rejects malformed, duplicate, out-of-order and stale
causal context instead of sorting/deduplicating/skipping such evidence.

The derived low-pass gas channel is named/treated as `gas_ema_aux`; it is **not**
an audited FOPDT sensor internal state.

### M1

The spent trainer is not the formal causal gate producer. It does not create a
formal checkpoint or the required destructive controls.

The revised M1 architecture closes the reviewed history-context bypass: all
history-dependent source evidence must enter `zS` before candidate scoring, and
candidate-only evidence is subtracted by evaluating the score at `zS=0`.

This only closes an architectural shortcut; it does not prove causal
identifiability. See:

`docs/CSTAR_M1_IDENTIFIABILITY_BOUNDARY_20260906.md`.

### M2

Historical future executed trajectory segments are now explicitly labeled as
retrospective path-conditioned replay. They are **not** `do(route)` evidence.

A formal M2 route must be a decision-time locked planned route or a controlled
open-loop route under the typed controlled-asset contract.

### Formal controlled assets

The active typed asset contract is:

`experiments/ctpi_cstar/CSTAR_CONTROLLED_CAUSAL_ASSET_CONTRACT_V1.json`.

Use:

`experiments/ctpi_cstar/validate_controlled_assets.py`

before formal M1/M2 training.

### Authorization / AUC / 12-run

The authorization layer now requires real required fields, referenced raw
artifacts, checkpoint files/hashes, gate-to-checkpoint consistency, production
identity and full-stack smoke evidence.

The performance evaluator no longer back-fills future estimates into the past;
formal traces require explicit available estimates at t=0 and t=240 and use
causal zero-order-hold AUC.

The 12-run driver rechecks authorization input hashes and arm-specific module
call identities. Missing fields do not default to zero. Formal attribution cases
with fallback are invalid.

## Current stop line

Do **not** run the H01/H02/H03 × seed12 × A0/F00/F10/F11 matrix yet.

The active Codex handoff is:

`docs/CSTAR_REVISE_BEFORE_EXECUTION_CODEX_HANDOFF_20260906.md`.

The next task is finite revision validation: mandatory regression tests,
controlled-asset audit, formal M1/M2 producer completion, genuine M3
counterfactual evaluation when available, and a reviewable evidence bundle.
