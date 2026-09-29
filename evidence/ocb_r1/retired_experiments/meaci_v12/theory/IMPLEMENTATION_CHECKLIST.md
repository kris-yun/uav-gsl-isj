# Implementation and no-run checklist

## Phase T — theory freeze

- [x] Every formula-core symbol maps in `SYMBOL_CODE_MAP.csv`; V12-M production
  posterior integration is present and carrier refinement is forbidden by contract.
- [x] V12-M has no fitted sensor-noise or transport-persistence parameter;
  Bernoulli noise and protocol-fixed block transitions are explicit.
- [ ] V12-F remains unavailable until the separate 3-D TADM discrepancy
  calibration passes every gate in `CALIBRATION_PROTOCOL.md`.
- [x] The 15 V11 pairs are marked development evidence and excluded from the
  final held-out claim.
- [x] No House experiment has been launched during theory/formula-core work.

## Phase U — formula/code tests without House data

- [x] Formula-core compile-time contract is exactly `R=8,B=1`; V12-F is exactly
  `R=8,B=8`.
- [x] Production V12-M serialized member counts are emitted from the same
  compile-time constants used by the formula core.
- [x] Formula-core V12-F guard rejects absent/mismatched calibration;
  production startup wiring remains pending.
- [x] Reference full-method container can enumerate 64 crossed logits.
  Production V12-M dispatch/logging is complete; V12-F remains unavailable.
- [x] Formula core and production adapter use Jeffreys correction from recorded
  simulator timestep count and have no empirical response floor.
- [x] `transportEventKey()` pins the legacy update slot to zero and exposes no
  candidate, event or outcome input; equal `r` has identical root draw prefixes.
- [x] Increment-rate projection is idempotent and orthogonal to pattern projection.
- [x] One rate group is used per immutable likelihood increment; using one group
  per StopAndMeasure block is rejected by a block-constant contrast test.
- [x] Reference monotone intercept solve preserves each member's increment mean hit
  probability to `1e-12` after pattern filtering.
- [x] The geometry-stratified operator source subset is deterministically selected
  from fixed geometry carriers and is independent of native candidates/posterior.
- [x] Every update consumes only new completed events; its event ledger, fold
  scores and spectrum are immutable after the likelihood increment commits.
- [x] Generalized eigenvalues are finite/nonnegative within numerical tolerance.
- [x] Continuous weights are `lambda/(1+lambda)`; there is no eigenvalue gate.
- [x] Calibration and scoring replica folds are disjoint and swapped.
- [x] Reference and production Bernoulli likelihood use both hits and misses and
  contain no rank transform.
- [x] Reference TADM discrepancy index is static over a trajectory and is
  marginalized once. This applies only to V12-F; production remains pending.
- [x] Reference transport state is block-persistent and resets uniformly at
  StopAndMeasure boundaries; there is no fitted `tau_eta`.
- [x] Reference online and replay evidence differ by at most `1e-12`.
- [x] V12 qualification uses a fixed non-overlapping `2 x 2` carrier partition;
  any carrier/map change fails closed and native refinement cannot enter V12.
- [x] Flat evidence is posterior-neutral in the reference test.
- [x] Saturated-hit counterexample is rate-correct in the reference test.
- [x] Early-error reversal counterexample passes in the reference test.
- [x] V12 inference receives only fixed carriers, completed events, map geometry,
  simulator settings and the response bank; no source-truth API is referenced.
- [x] OFF qualification uses the separately frozen native PMFS binary. The V12
  binary is never used to manufacture an OFF arm, so baseline identity is explicit.
- [x] Response-bank serialization is atomic, refuses overwrite, and rejects map,
  carrier, simulator-setting, method-seed or transport-substream mismatch.
- [ ] House-specific response banks are not yet built or SHA-256 frozen.
- [ ] Absolute-path launcher performs SHA-256 verification before V12 startup.

## Phase S — no-offline boundary requested by the user

- [x] Existing House/V11 event logs were not replayed to choose formulas,
  thresholds, channels, carrier size, ensemble seed or likelihood scale.
- [x] Failure-mode closure used deterministic synthetic counterexamples only.
- [ ] After final freeze, proceed directly to the preregistered closed loop;
  do not insert a truth-revealed offline tuning round.

## Phase F — final freeze before a new closed loop

- [ ] Source tree hash.
- [ ] Binary hash.
- [ ] V12-M source/config hashes (no external parameter-fit artifact).
- [ ] V12-F TADM calibration hash, only if V12-F is later qualified.
- [ ] Exact House data identities.
- [ ] Fresh seed search record and seed list.
- [ ] OFF/ON arm order.
- [ ] 300 s budget and source-update cadence.
- [ ] Official and anti-gaming metrics.
- [ ] GO/NO-GO thresholds and catastrophe definition.
- [ ] Unique VM worktree, install prefix and output root.
- [ ] Absolute-path launcher rejects every non-frozen binary.

Only after every item through Phase F passes may the first new House arm start.
