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

