# CG-PC-CTT scientific status — 2026-08-27

## Current verdict

`BLOCKED_M1_BANK_MISSING`

with a second unresolved prerequisite:

`BLOCKED_MEMBER_SEMANTICS`

## V1

`INVALID_PROTOCOL`.

Reason: finite M=8 candidate-mean noise could be whitened and mistaken for rank-3 / absolute source strength. Weak, null and collapse counterexamples invalidated the gate before any H03/H02 evaluation.

## V2 repair implemented

- cross-member replicated source operator; same-member mean-noise squares removed;
- pair-difference nuisance scaling;
- pre-registered third replicated source direction;
- exact M=8 member sign-flip null (128 unique patterns);
- no alpha threshold calibration;
- explicit `exchangeable_realizations` vs `fixed_nuisance_design` semantics;
- hard refusal of inferential acceptance for fixed/undeclared member semantics;
- regression tests: strong, weak, null, collapse, candidate/member shuffle, member-order invariance, ABSTAIN;
- M1 bank forensic locator and NPZ qualifier.

## What is not established

- the real House03 206×8×10 M1 bank has not yet been recovered on this branch;
- it is not yet established whether the eight historical transport members are stochastic/exchangeable realizations or a deterministic nuisance design;
- no V2 H03/H02 performance result exists;
- no V2 proximal-bridge result exists;
- no V2 300 s closed-loop run is authorized.

## Binding next action

Follow `docs/CODEX_CG_PC_CTT_PROTOCOL_V2_20260827.md` exactly. First require `SELFTEST V2 PASS`, then recover/freeze M1 provenance and member semantics. Do not use ME-ACI V10 results as substitute evidence.
