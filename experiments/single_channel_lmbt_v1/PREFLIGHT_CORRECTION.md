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

## Third preflight failure and final input correction

The per-step point-cloud matcher at commit `fcd3bcb` also stopped before arm
scoring.  Of 1380 frames, only six exceeded 0.002 m/s error, but the maximum was
0.08081 m/s.  Inspection of the verified runtime adapter showed why: the live
wind server does not query the original unstructured CFD CSV by nearest point.
GADEN first converts it into `wind_iteration_*` values on the occupancy-defined
regular 3-D grid and samples that grid.

The formal implementation now imports the project's existing audited
`NumericWindReader` from `experiments/ctpi_cstar/environment_runtime.py`, reads
the exact binary wind files used by the realization, and uses the same float32
grid indexing rule.  No new interpolation and no relaxed tolerance are
introduced.  The full 1380-frame wind binding must pass before scoring.

## First scoring launch boundary failure

At commit `38bdc26`, the 1380-frame wind binding passed and the program entered
construction of the first arm's backward paths.  A path left the finite GADEN
grid, and the audited reader correctly raised `POINT_OUTSIDE_GRID`.  No complete
arm score, source-truth read, or Gate output was produced.

The correction terminates a backward path as soon as it leaves either the
runtime wind grid or the candidate-map envelope.  It does not clamp the path to
the wall, invent wind outside the domain, or alter any registered numerical
parameter.  Since all source candidates are inside the map, the out-of-domain
remainder cannot contribute valid candidate evidence.
