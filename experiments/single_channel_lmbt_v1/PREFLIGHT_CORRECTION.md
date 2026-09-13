# Formal preflight correction before any arm scoring

The first launch at preregistered commit `218c2d5` stopped inside
`validate_wind_binding`; no backward path, candidate score, source truth read, or
Gate result was produced.

The initial code indexed the ten looping CFD fields from the GADEN gas-file
`iteration`.  That counter wraps from the historical file iteration to a small
integer near 192 s in the concatenated trace.  The controller-visible `step`
remains continuous and is the clock followed by the wind record.  This created
zero median binding error but a 0.36165 m/s maximum error over 100 audit points.

The corrected mapping is

`field = ((((continuous_trace_step - 1) // 2) + 5) % 10) + 1`.

The correction is admissible because it is fixed from the recorded wind values
before any LMBT arm score or source-truth evaluation.  The full-run validator
still requires median error <= 1e-4 m/s and maximum error <= 2e-3 m/s.  If that
check fails, scoring remains blocked.

## Second preflight failure

Commit `fa3e620` also stopped before any arm score or source-truth read.  The
continuous-step formula matched the initial segment but failed after the replay
seam because the player briefly used CFD `field 0` and reset the subsequent
phase.  Its 100-point median error was zero but maximum error was 0.37446 m/s.

The second correction removes the guessed global formula.  At each saved step,
it matches the allowed local wind observation against CFD fields 0 through 10
at the same location and records the minimum-error field index.  It uses the
native pre-seam periodic rule only for emission ages before the saved trace
begins.  This is a historical wind-field ledger built without gas values,
source truth, or algorithm outcomes.  The formal validator now checks every
saved step, not a 100-point sample, under the same error bounds.
