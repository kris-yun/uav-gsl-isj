# Dynamic-information audit — final status

**Verdict: `AUDIT_COMPLETE / DYNAMIC_EXPORT_STOP_PARITY_NOT_ESTABLISHED`.**

The inventory and loss-chain audit are retained. A temporary summary-only export prototype compiled and produced the requested rows, but the mandatory existing-case OFF/ON test failed Native parity. In the H01_R2026092201 pair, both runs reached terminal output and each produced 154 candidates; ON produced 154 dynamic files. Nevertheless, trajectory/sensor/wind traces, candidate IDs and scores, final posterior, support alignment and terminal result differed. The terminal results were `Search_t=299.89, Error=4.60` (OFF) and `Search_t=299.91, Error=4.63` (ON). The prototype was therefore removed from the branch; no PMFS source or launch/reference implementation is delivered.

This does **not** prove that computing a summary mathematically changes PMFS. It proves that the attempted in-loop collection/I/O did not satisfy the required closed-loop invariance under the actual asynchronous runtime. Runtime overhead can change estimator/update timing and therefore scientific behavior. Under the task's STOP rule, that distinction is not permission to optimize or retry.

Artifacts:

- `INFORMATION_INVENTORY_20260923.md/.json`: what exists, is discarded, can be regenerated, is unavailable, or is non-causal.
- `INFORMATION_LOSS_CHAIN_20260923.md`: exact aggregation/loss chain.
- `MOTHER_IDEA_DATA_REQUIREMENTS_20260923.md`: testability matrix, not method selection.
- `NATIVE_PARITY_20260923.json`: failed mandatory gate and trace hashes.

Key audit correction: accepted runs explicitly used 200 recording steps × 0.2 s (40 s internal model time), not the `SimulationSettings` initializer's 100 × 0.1. The GADEN wind files are complete 3D spatial fields, while Native candidate simulation uses one fixed PMFS-estimated 2D wind grid. Full GADEN fields and future snapshots are simulator oracle data and remain `NON_CAUSAL_NOT_ALLOWED` for an online method.

No new plume realization, method test, parameter tuning, posterior change, quadtree change, planner change, source-update change, RNG change, or endpoint change was retained.
