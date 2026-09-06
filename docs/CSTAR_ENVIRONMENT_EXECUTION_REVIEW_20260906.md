# Environment-first execution review of 82f3491

The ordering is accepted, not its unexecuted PASS claims. No production smoke,
12-run, model redesign, GMRF tuning, protected-bank read or old-checkout rewrite.

Implementation corrections before real input probes:

- Parse standard ROS YAML including the actual exporter's block-style origin.
  Reject unsupported nonzero map yaw and invalid map/raster parameters.
- Compare the real VGR `/map` raster, frame, origin and resolution to the frozen
  YAML/PGM. Merely hashing CLI-supplied files is not runtime map loading evidence.
- Release only an isolated, paused simulator after aligned t=0 AND map parity.
  Bound the probe by a wall deadline; preserve failure JSON.
- Bootstrap t=0 wind is a placeholder, not an observation. Require eight positive
  frames plus bootstrap, verify JSONL stamps/values and bind the actual wind CSV.
- Reject failed audits, changed git identity, bad frame counts, and substituted
  wind probes. A boolean audit and three topic strings alone are insufficient.

The geometric candidate support is preregistered as ALL free fine-grid cell
centres, generated without source labels, gas data or outcomes. This freezes the
input for a future controlled producer; it does not imply that producer exists.
The short route is the unchanged R4 seed12 start point with 1.6s stationary dwell.
It establishes endpoint feasibility only, NOT general route-planning performance.
Shared A0/F00/F10/F11 identities remain a binding requirement on future arms;
no four-arm execution equivalence is claimed by a standalone loader test.

The historical VM checkout's origin is an old bundle. Execution uses a separate
clone transferred from the verified GitHub revision. It does not alter the old
checkout or its origin. Missing volatile `/dev/shm` helpers are restored only in
this new isolated directory using persistent archived source/libraries.

Selftest fixtures are synthetic implementation tests and never House evidence.
Real House audit results are recorded separately in evidence/cstar_environment_20260906.
