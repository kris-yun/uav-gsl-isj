# Codex RCEC V13 bounded self-repair policy

Status: ACTIVE FOR TOOLING / BUILD-CLOSURE FAILURES ONLY

Purpose: prevent repeated one-token-at-a-time handoffs for non-scientific implementation issues while preserving the frozen scientific method.

## Scientific boundary that Codex MUST NOT change autonomously

Do not change any of the following without stopping and reporting upstream first:

- ACIT inverse-transport equations or the frozen 54-member nuisance family;
- STRI / identifiability conditions, hit/miss semantics, or spatial replication threshold;
- CREI definition: current post-native / pre-RCEC PMFS absolute candidate normal-rank combined with even/odd ACIT ranks through the lower envelope `min(...)`;
- TMEM definition or its candidate-wise temporal history semantics;
- candidate geometry, candidate ID mapping, source prior construction, or generalized-posterior reconstruction;
- PMFS planner or `posterior_guidance_weight`;
- any adaptive weight, temperature, House-specific parameter, truth/error gate, seed-dependent rule, or new learned model;
- experiment seeds after they are selected, evaluator, 300 s budget, or success/failure thresholds;
- any dependency copied from an untracked VM/workstation path.

If a proposed fix touches any item above, STOP and report before editing.

## What Codex MAY self-repair

Codex is authorized to diagnose and repair, without waiting for upstream, failures that are demonstrably limited to:

- `tools/*.py` materializer logic;
- `reference/*.py` verifier logic;
- RCEC unit/core tests;
- deterministic build-closure handling of the already-declared unavailable legacy V12-M path;
- syntax, whitespace, anchor, brace-matching, idempotence, forbidden-token, or stale-legacy-mode issues;
- CMake/build plumbing only when the change does not alter which RCEC scientific path executes.

For these failures, do NOT just report the first token. Investigate all occurrences and fix the class of failure once.

## Required self-repair procedure

1. Start from the exact remote HEAD and a clean working tree.
2. Reproduce the failure once.
3. Before editing, enumerate the whole failure class. For legacy V12 closure, for example:

```bash
rg -n 'rc_sd_tfei_v12|RCSDTFEIV12|V12ResponseBank' \
  ros2_package/src/gsl_server/algorithms/PMFS tools reference
```

4. Classify every occurrence as one of:
   - active RCEC scientific code;
   - build/tooling logic;
   - dormant legacy V12 code;
   - comment/diagnostic only.
5. If any occurrence is active RCEC scientific code, STOP.
6. Otherwise repair the TOOL/MATERIALIZER, not the already-generated runtime file by ad-hoc manual edits. The tool must remain deterministic and transactional.
7. Add or extend a regression test that would have caught the failure.
8. Run:

```bash
python3 -m py_compile tools/*.py reference/*.py
git diff --check
```

9. Re-run the full materializer/verifier chain from a freshly reset tree, not from the partially transformed tree.
10. Inspect the generated diff and prove that frozen scientific tokens/formulas did not change.
11. Commit the tooling fix with a narrow commit message and report the commit SHA plus full PASS output.

## Hard stop conditions

Stop immediately and report upstream if any repair would require:

- changing `applyMEAci()` evidence mathematics rather than deterministic plumbing;
- changing candidate scores/ranks to make a failed seed improve;
- touching planner behavior;
- introducing a new threshold, alpha, temperature, weight, model, or dataset;
- using truth source location or final localization error to decide the repair;
- copying missing code/dependencies from outside the tracked repository;
- changing OFF behavior;
- choosing or looking at new held-out seeds before source/binary freeze.

## Build-closure specific rule

For the unavailable V12-M mode, the closure objective is semantic, not string-layout-specific:

- equality with the unavailable mode is always false;
- inequality with the unavailable mode is always true;
- the V12 implementation remains fail-closed;
- the historical mode cannot be selected by the PMFS parser;
- RCEC `me_aci + RCEC_V13_ARM` behavior is unchanged.

Do not write one-off replacements for only the latest whitespace/operator spelling. Search and handle all syntactic variants, then enforce the postcondition.

## Reporting format after autonomous repair

Return:

- failure classification;
- files changed;
- why the change is outside the scientific boundary;
- regression test added;
- materializer/verifier outputs;
- `git diff --stat` and `git diff --check` result;
- source SHA(s);
- commit SHA.

Do not proceed to parity, mechanism regression, or 300 s closed-loop experiments until the build/tooling chain is fully PASS and upstream has reviewed the final materialized source SHA.
