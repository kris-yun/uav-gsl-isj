# SUPERSEDED — do not execute this task

Date superseded: 2026-08-28

The first-order Markov V6-B replay defined in the previous version of this file has been superseded before runtime validation.

Reason: reducing the 200-step ordered CTT trace to a 2x2 transition matrix is itself another dynamics compression and can discard phase, dwell-time, and within-context transport structure. The revised PF-DEI contract scores the full ordered occupancy trace directly and uses a source-independent semi-Markov model only as the absolute dynamic null.

Current normative files:

- `docs/CG_PC_CTT_PF_DEI_PHASE_MARGINAL_FREEZE_20260828.md`
- `docs/CODEX_PF_DEI_DYNAMIC_REPLAY_20260828.md`
- `experiments/cg_pc_ctt/pf_dei_phase_marginal_reference.py`
- `experiments/cg_pc_ctt/selftest_pf_dei_phase_marginal_reference.py`
- `experiments/cg_pc_ctt/ctt_dynamic_io.py`

Do not run the old Markov coverage and do not implement C++ or Active Probe from this file. Historical content remains available in Git history.
