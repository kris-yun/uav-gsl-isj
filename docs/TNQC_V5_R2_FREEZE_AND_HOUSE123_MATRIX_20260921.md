# TNQC V5 — R2 Execution Freeze and House123 Matrix Contract

Date: 2026-09-21

## 1. Purpose

R2 is an **execution-contract revision**, not a TNQC V5 method revision.

The reason for R2 is terminal lifecycle correctness: the previous execution
path could exit at the server budget check before native PMFS
`saveResultsToFile()`, so the authoritative `RESULT IS` endpoint was not
emitted. R2 must preserve the <=300-s scientific state while allowing the
native terminal result to be saved.

No TNQC equation, candidate score, PMFS likelihood, planner, gate threshold,
source-update cadence, or ExpectedValue semantics may change in R2.

## 2. R2 must be captured before the six-case matrix

The validated VM checkout reported by Codex is:

`b24da77fd24bd5ea2cbb33caf856f80b9d7670e4`

This commit must be pushed to GitHub before the authoritative matrix begins.

Create/push an immutable execution branch:

`freeze/tnqc-v5-r2-execution-20260921`

The branch must point to the exact validated R2 commit or an exact descendant
that adds evidence/docs only. No scientific/runtime code changes are allowed
after the freeze tag/branch is recorded.

Record:

- Git commit SHA;
- complete `ros2_package` tree SHA;
- algorithm binary SHA256;
- linked-native endpoint SHA256;
- launch SHA256;
- simulator/runtime overlay SHA256;
- resolved parameters;
- ROS/GADEN dependency paths;
- clock mode and publisher;
- timeout/search-budget semantics.

## 3. Remove comparison ambiguity

Before running the matrix, write one resolved experiment manifest containing
all common parameters and the per-House fields.

Common frozen fields must include at least:

- algorithm=PMFS;
- TNQC_MODE=off for trajectory generation;
- PFDI_MODE=off;
- stepsSourceUpdate=3;
- 300.0-s scientific search budget;
- same PMFS likelihood and source-discrimination power;
- same map resolution and PMFS parameters;
- same TNQC V5 replay equations;
- same linked-native top-5% endpoint;
- same terminal-lifecycle R2 behavior;
- no post-freeze observation/navigation/posterior update.

Per-House fields are allowed only where the historical benchmark already
requires them, such as:

- dataset/scenario path;
- source truth used only by evaluator;
- start pose;
- gas backend;
- GADEN realization/config id;
- wind server/player path.

Do not silently mix historical binaries, old launch overlays, R2 overlays, or
different runtime trees across cases.

## 4. Pre-matrix repeatability gate

Before the full matrix, repeat House01/seed0 once with:

- exact R2 code;
- exact R2 launch/runtime overlay;
- exact scientific parameters;
- fresh output directory;
- new ROS domain only.

Compare against the first valid R2 House01/seed0 run.

Scientific quantities that should match under the frozen deterministic
contract include:

- measurement timestamps/values;
- robot pose trajectory;
- source-update ids/times;
- candidate geometry;
- candidate-support rows;
- native posterior;
- native linked endpoint;
- TNQC replay endpoint.

Run UUID, absolute paths and wall-clock timestamps are not scientific equality
fields.

Any unexplained scientific mismatch blocks the six-case matrix.

## 5. Authoritative six-case offline matrix

After the repeatability gate passes, run exactly:

- House01 seed0
- House01 seed1
- House02 seed0
- House02 seed1
- House03 seed0
- House03 seed1

All six must use the same R2 execution contract and the same TNQC V5 replay.

For each case preserve:

- runtime manifest;
- launch log with terminal `RESULT IS`;
- source-update timing;
- measured hit-probability field;
- candidate manifest;
- candidate support alignment;
- native source posterior;
- replay evaluation JSON;
- linked-native endpoint audit;
- gate diagnostics;
- checksums.

Do not stop or modify the method after observing an early case.

## 6. Frozen scientific verdict

Use the pre-registered aggregate criteria already in the project:

- all six integrity-valid;
- pooled error reduction >=10%;
- at least 4/6 paired cases improve;
- worst paired degradation <=25%;
- no false-confident-collapse case under the frozen definition.

House01/seed0 from the first valid R2 run was approximately neutral/slightly
worse. This does not change any threshold.

If the six-case result is HOLD, V5 remains HOLD. Do not tune V5 on these same
six cases.

## 7. Closed-loop stage after offline matrix

Two distinct follow-ups must not be confused.

### If TNQC V5 offline gate is GO

1. OFF vs SHADOW determinism under R2.
2. Then FUSED closed-loop House01/02/03 x seed0/1.
3. Compare final 300-s linked-native endpoint under the same R2 contract.

### If TNQC V5 offline gate is HOLD

Do not rescue V5 by changing the gate after seeing these cases.

The next-generation active source–transport deconfounding direction must use a
new method/version and a separately frozen experimental protocol.

## 8. Branch discipline

- `main`: theory, docs, frozen scientific source line.
- `freeze/tnqc-v5-r2-execution-20260921`: exact R2 execution implementation.
- `results/tnqc-v5-r2-house123-seed01-20260921`: evidence-only result branch
  created from the R2 freeze.

No result branch may silently change source/runtime code.
