# CTPI V0.4 closed-loop runtime boundary

Status on the visible `research/ctpi-crel-psrg-aprs-v04-20260902` code base:

`BLOCKED_BY_RUNTIME_PARITY`

This directory prevents a labelled CTPI V0.4 run from silently executing inherited CPIR/TADM runtime paths.
It does **not** change the frozen V0.4 science.

## Why the current inherited runtime is not V0.4

1. `PMFS.cpp` accepts inherited `cpir_*` modes and calls the CPIR posterior path; it does not expose an explicit `ctpi_v04` runtime contract.
2. The inherited CPIR launch/runner maps old factorial arms to `cpir_a1/cpir_a2/cpir_a3/cpir_m1_m3`. Those mappings are not the V0.4 module graph.
3. Simply adding `ctpi_v04` to the current allowed `pfdi_mode` list is unsafe: the broad legacy assignment `tadmEnabled = pfdiMode != "off" && !cpirEnabled` would route an unseparated CTPI mode into TADM unless an explicit CTPI enable path is added.
4. V0.4 APRS must not multiply the same current measured-hit evidence onto a native PMFS posterior that already consumed it. Runtime integration must implement a replacement/ownership boundary for the same observation update.
5. V0.4 PSRG is a parallel metrology output. It must not be inserted into the source posterior or planner as an unregistered weighting term.
6. The current PMFS movement score primarily uses `varianceOfHitProb * (1-confidence)`. A formal V0.4 closed loop must explicitly prove that the frozen V0.4 posterior used at update `t` is the posterior handed to the next action decision. Do not claim this from node liveness alone.

## Required runtime handshake

The actual C++/ROS implementation must deliberately expose these provenance markers so source and compiled-binary identity can be checked:

- runtime mode: `ctpi_v04`
- runtime contract: `CTPI_V04_RUNTIME_CONTRACT_V1`
- posterior entry point: `applyCTPIV04Posterior`
- APRS observation ownership: `CTPI_V04_APRS_OWNS_CURRENT_OBSERVATION_V1`
- PSRG boundary: `CTPI_V04_PSRG_TELEMETRY_ONLY_V1`
- planner consumption boundary: `CTPI_V04_PLANNER_CONSUMES_POSTERIOR_V1`

These are engineering provenance markers, not scientific parameters. They do not replace numerical Python↔C++ parity tests.

Before a run, execute:

```bash
python3 tools/ctpi_v04_runtime_parity_guard.py \
  --repo-root "$REPO_ROOT" \
  --binary "$PFDI_INSTALL_ROOT/install/gsl_server/lib/gsl_server/gsl_actionserver_node" \
  --json-out /tmp/ctpi_v04_runtime_parity.json
```

The only acceptable pre-run verdict is:

`CTPI_V04_RUNTIME_PARITY_PASS`

While the runtime port is absent, exit 42 / `BLOCKED_BY_RUNTIME_PARITY` is the correct behavior. Do not bypass it by mapping V0.4 to a CPIR or TADM mode.

## Safe runner wrapper

Use `run_ctpi_v04_case_safe_20260902.sh` only around the actual CTPI V0.4 canonical runner. It rejects:

- old CPIR arm names and CPIR runners;
- ROS domain IDs outside 0..232;
- reused target run directories;
- missing/stale terminal `run_status.json`;
- run status that reports a CPIR runtime.

Preflight artifacts are intentionally written outside the target run directory until the canonical runner creates that directory itself, preventing stale/fresh-run ownership conflicts.

## True-closed-loop evidence

The runtime should emit a per-decision causal trace with the schema required by:

```bash
python3 tools/ctpi_v04_closed_loop_causal_chain_check.py \
  --trace "$RUN_DIR/ctpi_v04_causal_chain.csv" \
  --json-out "$RUN_DIR/ctpi_v04_causal_chain_verdict.json"
```

The checker requires explicit evidence that the posterior handed to the planner is the newly updated CTPI V0.4 posterior, that a command was acknowledged, motion occurred, and the next observation is fresh rather than replayed.

Only `TRUE_CLOSED_LOOP_CAUSAL_CHAIN=PASS` may support a true V0.4 closed-loop claim.
