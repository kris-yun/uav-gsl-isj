# V12-M pre-House freeze and closed-loop route

## Current stop line

Do not start H01/H02/H03. The method formula and production adapter compile,
but the three truth-blind physical response banks, their SHA-256 manifest and
the absolute-path launcher have not been frozen.

## Stage 1 — freeze the method, not results

1. Copy the audited source into one new immutable VM worktree and build into one
   new install prefix. Do not overwrite V11 or the active ROS install.
2. Run the 14 C++ contract tests and sanitizer tests from that source.
3. Record source-tree hash, binary SHA-256, config hash and method seed. The
   method seed is constant across all Houses and all qualification seeds; it is
   not the GADEN/run seed.
4. Freeze mode `rc_sd_tfei_v12`, `R=8`, `B=1`, carrier stride 2, `J=min(64,
   N_carrier)`, formulas, planner and source-update trigger. No likelihood
   temperature, gate, fallback, nuisance family or posterior repair exists.

Any source or formula change after Stage 1 invalidates every later bank and
returns to Stage 1. Do not patch a single House/seed result.

## Stage 2 — truth-blind response-bank preparation

For H01, H02 and H03 separately:

1. Use the frozen ON binary with an absolute
   `PFDI_V12_RESPONSE_BANK_PATH` and `PFDI_V12_BUILD_RESPONSE_BANK=1`.
2. Build the bank before qualification seeds are selected and without reading
   source truth or final localization output. The builder may reach the first
   source-update hook solely to obtain map geometry; observed events are not an
   input to bank generation.
3. Preserve builder log, map/carrier manifest, construction wall time, bank
   byte size and SHA-256. Builder mode refuses an existing bank.
4. Restart with builder mode unset. The runtime must load the same bank and pass
   every header check. `sha256sum -c` must pass before process start.
5. Run a no-truth activation smoke only: exact bank loaded, 8 x 1 contract,
   event ledger present, finite eigenspectrum, unit posterior mass and replay
   error <= `1e-10`. Do not read final source error.

Failure in Stage 2 is infrastructure/formula activation failure. It does not
authorize changing a formula or inspecting qualification truth.

## Stage 3 — freeze the experiment before selecting seeds

Freeze in one manifest:

- exact H01/H02/H03 data identities and occupancy hashes;
- native PMFS OFF binary and V12-M ON binary absolute paths and SHA-256;
- three response-bank paths and SHA-256 values;
- fixed method seed and transport substream;
- fresh GADEN/run seeds not used in V10/V11/V12 development;
- paired arm order, counterbalanced across Houses;
- 300 s simulated-time budget for both arms;
- native PMFS StopAndMeasure/source-update trigger, unchanged. V12 handles every
  native update and does not impose a new 100/300/600/900 s clock;
- official metric `ExpectedValue(sourceProbability, 0.05)`;
- secondary anti-gaming metrics: true-source cell rank/mass, mass within 1 m,
  posterior spatial variance, update count, false-confident collapse and wall
  cost (bank preparation and online inference reported separately).

The response bank removes repeated physical simulation from the online update,
so V12 should no longer delay the native roughly minute-scale update cycle.
This is measured, not guaranteed by altering the PMFS clock.

## Stage 4 — one-shot fresh-seed closed loop

Run exactly one full paired 300 s OFF/ON arm for each House on the preregistered
fresh seed. Do not stop at the first accepted update. Do not reveal or react to
an individual House until all six arms finish and integrity checks pass.

Integrity failures (wrong binary/bank/config, missing events, bank mismatch,
posterior mass failure, replay failure, runtime crash) are reported separately
and rerun only after the same frozen artifact is restored. Scientific
regressions are never rerun or tuned away.

## Stage 5 — preregistered decision

V12-M qualifies as the main innovation only if all are true:

1. pooled official final-error improvement is at least 10%;
2. at least two of three Houses improve;
3. no catastrophic regression (pre-freeze definition: ON error exceeds OFF by
   both >= 20% and >= 0.5 m);
4. no false-confident collapse: low posterior variance cannot coexist with a
   severe true-source rank/mass failure;
5. activation and artifact integrity pass for all six arms.

Three of three improvement is the strongest result. Two of three plus pooled
>=10% is a qualified but heterogeneous result that must report the negative
House. Anything below the five conditions is a scientific NO-GO for V12-M;
TADM or a third module may not rescue or rename it.

Only after V12-M passes may independent TADM calibration and the V12-F
`C+S+D` ablation begin.
