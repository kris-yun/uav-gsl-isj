# START HERE — CTPI closed-loop qualification

Branch: `codex/ctpi-full-law-closedloop-20260902`

Read:

1. `docs/CTPI_CLOSED_LOOP_THREE_MODULE_FREEZE_20260902.md`
2. `docs/CTPI_CLOSED_LOOP_THREE_MODULE_PREREGISTRATION_20260902.json`
3. `experiments/cg_pc_ctt/ctpi_closed_loop_core.py`
4. `experiments/cg_pc_ctt/ctpi_full_law_factorial.py`

Run bank-free checks first:

```bash
python3 experiments/cg_pc_ctt/ctpi_full_law_core.py --selftest --iterations 1500
python3 experiments/cg_pc_ctt/ctpi_full_law_gate.py --selftest
python3 experiments/cg_pc_ctt/ctpi_closed_loop_core.py --selftest
python3 experiments/cg_pc_ctt/ctpi_full_law_factorial.py --selftest
```

Do not generate a bank, train a network, implement ROS runtime, or start closed
loop until the existing exact-route assets give an M1+M2 offline PASS.

M3 is intentionally absent from fixed-trajectory performance claims.  It must
change actions and earn its increment in a true closed-loop comparison.
