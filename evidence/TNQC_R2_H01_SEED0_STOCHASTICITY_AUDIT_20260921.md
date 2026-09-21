# TNQC R2 H01/seed0 Stochasticity Audit — 2026-09-21

## Verdict

- House02/House03 static compatibility: PASS.
- House01/seed0 second 300-s R2 run: internally valid, but strict cross-run determinism: FAIL.
- This is **not** a TNQC scientific HOLD and **not** an execution-integrity failure.
- It characterizes the ROS/GADEN/navigation stack as trajectory-level
  stochastic/asynchronous under repeated launches, even with the same nominal
  scientific parameters and seed.

## Frozen identity

Validated VM checkout:

`b24da77fd24bd5ea2cbb33caf856f80b9d7670e4`

The repeat reused the original R2 binary/runtime overlay without rebuilding or
patching.

Recorded identities:

- actionserver SHA256:
  `db64039fca97195cad7077ae0485ddd91ebdde898124bb77938650bdc2d2df7b`
- linked-native evaluator SHA256:
  `9d0954c32021f6b808ba4bec06e98ea9fe8193b25cc4ed33d4189330d40c9ac6`
- launch SHA256:
  `8ce5845fa0d57a83b954de12ad79826d4cc1db68b13cf7f23cdb7e70c740f648`

Repeat run:

- House01 / seed0
- native PMFS, off/off
- 300 s
- new ROS domain 223
- same effective scientific launch parameters after normalizing output
  path/run identifiers.

## Cross-run comparison

The two valid R2 H01/seed0 runs diverged first at approximately step 77 /
15.4 s.

Observed maximum cross-run differences included:

- measured gas: 0.451391 ppm;
- true gas: 1.505413 ppm;
- pose position: 2.5243 m;
- wind speed: 0.974443 m/s;
- source-update time: 1.4 s;
- candidate count difference: 6;
- native posterior cell probability: 0.1013687884;
- linked-native top-5% endpoint:
  5.461751564981095 m vs 5.523705299436255 m,
  difference 0.061953734455159726 m.

The candidate geometry of common identities was unchanged, but the adaptive
candidate identity sets differed after the trajectory diverged.

## Within-run integrity

Both runs independently passed:

- 300-s terminal result;
- native posterior reconstruction;
- linked-native endpoint parity;
- V7 replay integrity.

For the repeat run:

- reconstruction max_abs:
  `1.887379141862766e-15`
- reconstruction L1:
  `5.110803820729446e-15`
- linked-native vs two-decimal terminal difference:
  `0.003705299436255416 m`

Therefore the run-to-run mismatch is distinct from context-bank or endpoint
corruption.

## Scientific interpretation

Exact equality between two separately launched ROS/GADEN closed-loop runs is
not a valid prerequisite for the TNQC **fixed-trajectory offline gate**.

The offline comparison is paired inside each single native run:

`native posterior on trajectory T`
vs
`TNQC replay on the same trajectory T`.

Thus the trajectory-level stochasticity is held fixed within each paired
comparison.

This audit does matter for later closed-loop evaluation. Same nominal seed
does not by itself create an exact counterfactual pair between separately
launched OFF and FUSED runs. Closed-loop effect sizes must therefore be
interpreted relative to native repeat variability or evaluated with a
prospectively deterministic exogenous harness.

## Consequence

This audit is nonblocking for the six-case House01/02/03 x seed0/1 offline
fixed-trajectory matrix.

It blocks only claims of exact cross-launch determinism.
