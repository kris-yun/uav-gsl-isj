# CODEX TASK — PF-DEI mechanism isolation immediately after forward closure

Date: 2026-08-28

Status: **SUPERSEDED — DO NOT EXECUTE**

The sensor-history locality falsification in this task has already been independently reproduced on the 30-run audit:

- 484 inter-stop transitions;
- 102/484 history-only lower-bound qualifying transitions;
- H01/H02/H03 = 0/37/65;
- median inter-stop gap = sensor tau = 1.2 s.

More importantly, the closed frozen sensor is deterministic, zero-noise, symmetric (`tau_rise=tau_recovery=1.2 s`) and has an exact two-sample dead time at the 0.2-s cadence.  Therefore its measured sequence is algebraically deconvolvable to the corresponding physical concentration sequence on the recoverable sample grid.

The old interpretation `A ideal adequate, B native inadequate -> SENSOR_MEMORY_DOMINANT` is therefore too coarse.  A deterministic invertible sensor does not intrinsically destroy source information in a correct full-sequence model; the established failure is local/context-wise **sensor-state misattribution / trajectory-dependent observation aliasing**.  Any A1/A2 difference must be tested with a truly matched ideal observation sequence, obtained from the source-proven inverse, and a correctly persistent native forward path.

The sole current task is:

`docs/CODEX_PF_DEI_EXACT_DECONVOLUTION_MATCHED_REPLAY_20260828.md`

Do not execute the old M2/M3 interpretation from this file.
