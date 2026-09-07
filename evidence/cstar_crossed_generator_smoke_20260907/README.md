# Crossed-generator smoke — 2026-09-07

This is a non-qualification diagnostic. A one-second H01 run using the VM's
current GADEN build and converted modern wind files completed successfully in
`/dev/shm`, but a same-source reproduction check was not byte-identical to the
frozen raw realization. The smoke output was deleted after the check.

Consequently, no crossed-source trajectory was retained or added to the M1
dataset. Generating six new trajectories with this runtime would not establish
matched transport/release interventions and would risk invalid causal attribution.

See `REPORT.json` for the exact hashes and the required runtime-recovery step.
