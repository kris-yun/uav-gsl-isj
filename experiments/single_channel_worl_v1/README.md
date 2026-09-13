# Single-channel TAORL H03 gate

TAORL is the one permitted next mechanism after the M1R, CCDE, MC-SCSP and LMBT
negative gates.  It is a small, preregistered test on the known failing H03
development trace.  It does not consume or rebuild any source-response bank.

Read in this order:

1. `LITERATURE_TRACE.md`
2. `PREREGISTRATION_H03_SEED11.json`
3. `taorl_h03_gate.py`
4. `RESULT_VERDICT.md` after the one-shot run

The external ICRA 2026 global-rank method is an explicit comparator.  TAORL is
allowed to continue only if its forward-time, windowed likelihood beats that
comparator, a raw-value comparator, and its reverse-time negative control.

The run is complete.  Read `RESULT_VERDICT.md`; the formal all-required verdict
is NO-GO, while endpoint improvement and forward-time attribution are retained
as component-level positive evidence.
