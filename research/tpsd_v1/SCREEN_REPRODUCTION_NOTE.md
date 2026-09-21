# TPSD screen reproduction note

The executed offline screen used the frozen R2 sensor traces and final
candidate-support maps. The exact local scripts were executed against the
materialized authoritative archive and are summarized in
`evidence/tpsd_v1/OFFLINE_NOGO_20260921.md`.

Key fixed construction:

- hit event = measured_gas_ppm > 0.1
- instantaneous candidate evidence = Bernoulli log score from the candidate
  simulated hit probability at the robot's occupied PMFS grid cell
- primacy = event-locked early evidence
- generic inhibition = candidate-overlap-weighted population competition
- TPSD = event-locked early rank evidence minus delayed,
  candidate-similarity-weighted late rank activity
- final candidate scores are mapped to terminal PMFS leaves, normalized with
  free-cell measure through the cell expansion, and applied as a bounded
  exponential posterior tilt for the endpoint sensitivity screen

This branch is a scientific record, not a production implementation.
