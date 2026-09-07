# Offline orchestrator diagnostic — 2026-09-07

This invocation is preserved as an infrastructure negative result, not as a
scientific M1/M2 gate. `run_offline_gates.py` consumes the older generic
`episodes` manifest schema, while the current controlled causal assets use
`m1_episodes`/`m2_route_cases`. Passing the controlled manifest directly
therefore fails closed with `KeyError: episodes` before either model runs.

No model result, checkpoint, or closed-loop authorization is inferred from this
file. A schema adapter or a separately registered controlled-gate producer is
required before the orchestrator can be used for this asset package.
