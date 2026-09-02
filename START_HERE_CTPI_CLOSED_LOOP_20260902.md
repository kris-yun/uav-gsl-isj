# START HERE — CTPI closed-loop qualification

Branch: `codex/ctpi-full-law-closedloop-20260902`

Terminal offline status: `CTPI_FULL_LAW_FACTORIAL_NO_GO`.

Read the terminal audit first:

1. `docs/CTPI_FULL_LAW_FACTORIAL_TERMINAL_AUDIT_20260902.md`
2. `docs/CTPI_FULL_LAW_FACTORIAL_TERMINAL_AUDIT_20260902.json`

Then read the frozen design:

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
loop for this candidate.  M1 passed, but M2 failed the frozen downstream Gate.
The existing H01/H02/H03 seed0--9 truth has now been opened and may be used only
for failure analysis, not for confirmatory qualification of a replacement M2.

M3 is intentionally absent from fixed-trajectory performance claims.  It must
change actions and earn its increment in a true closed-loop comparison.
