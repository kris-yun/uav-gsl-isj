# CESS old D1 630x8 superseded

Date: 2026-09-25

Do **not** execute `CODEX_CESS_D1_HANDOFF_20260924.md`.

Primary-thread audit found that the unexecuted 630x8 D1 used micro-uniform
held-out averaging for macro EI despite declaring uniform macro interventions.
This is incorrect when macro sizes differ.

The corrected 18-source D0 remains positive after intervention-correct
recomputation, but the first confirmation gate has been redesigned as CESS D1A:

- 168 dense micro source cells (>=143 requirement);
- 16 fresh realizations/source;
- 8/8 symmetric splits;
- intervention-weighted raw EI;
- realization bootstrap;
- size-matched random partition control.

Only the new D1A handoff is authorized.
