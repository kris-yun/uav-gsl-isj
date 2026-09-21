# Active source–transport deconfounding V1

This branch starts from exact R2 commit
`b24da77fd24bd5ea2cbb33caf856f80b9d7670e4`. It adds an offline development
screen only. `ros2_package`, `reference`, and `codex` are unchanged.

Read [CONTRACT.md](CONTRACT.md) and
[the result](../../evidence/active_deconfounding_v1/REPORT.md) first.

## Audit of the proposed transition

Closing TNQC V5 is justified by the frozen six-case gate, not by a judgement
that its gain is too small to tune. Increasing g has no demonstrated direction
of benefit when the quotient ranks the wrong regions. No FUSED loop is allowed.

The causal explanation is weaker than the proposed wording: poor quotient
ranking and confident wrong posteriors do not uniquely identify transport
confounding. Missing source support, forward-model mismatch, spatial map
propagation and earlier path choices remain possible. New sensitivity maps
are model-based diagnostics, not causal proof about the observed failures.

The earlier `active_observability_v1` result remains NO_GO_0_OF_12 with held
wind W_altfast unopened. Its local FINAL_GATE.json and result document were
read again for this audit. This screen does not reopen those routes or winds.

Nuisance projection and Bayesian optimal design are established techniques;
see [Alsing & Wandelt, 2019](https://arxiv.org/abs/1903.01473) and
[Bartuska et al., 2021 preprint](https://arxiv.org/abs/2112.06794).
The present screen supplies neither a verified 2026 external mother theory
nor a novelty claim. A useful positive result would still need that separate
assessment and independent response validation.

## Reproduce the screen

Python 3 with NumPy is sufficient to score the archived responses:

```sh
python -m unittest discover -s research/active_deconfounding -p test_screen.py -v
python research/active_deconfounding/screen.py select \
  --design evidence/active_deconfounding_v1/pre_response/House01_seed0.json \
  --bank EXTRACTED_BANK/House01_seed0 --out EXTRACTED_BANK/House01_seed0/selection.json
python research/active_deconfounding/screen.py evaluate \
  --design evidence/active_deconfounding_v1/pre_response/House01_seed0.json \
  --bank EXTRACTED_BANK/House01_seed0 \
  --selection EXTRACTED_BANK/House01_seed0/selection.json \
  --truth evidence/active_deconfounding_v1/evaluation_truth.json \
  --out EXTRACTED_BANK/House01_seed0/evaluation.json
```

Run selection for all cases and freeze its hashes before evaluation. Repeat
the evaluation command for the six existing cases, then `report.py` and
`verify_results.py`. Selection never accepts a truth path. Its serialized
runtime field can vary, so a reproduction should compare actions and metrics,
not expect a byte-identical selection file across machines.

For forward regeneration, `native_bank.cpp` calls the frozen native
`runPointForwardReplay`. `build_native.py` compiles and links an isolated
executable from the R2 library objects; it does not invoke make/install or
change the original workspace. The absolute paths in `run_native.sh` describe
the actual VM used. Restore frozen dependencies or adapt paths on another VM.

One historical wrapper attempt stopped because an obstacle-cell raw counter
was mistaken for a probability. The frozen kernel normalizes only free cells.
The wrapper now checks free-cell probabilities and zeros unused obstacle
entries. Failed output was preserved; no model or nuisance value was adjusted.
House01/seed0 completed before that wrapper correction and was not rerun.
Its free-cell values use the same library/kernel and are unaffected.

## Deliberate limits

- Final native contexts only, with their **remaining** 300-s time budget.
  A negative result is scoped to these actions, contexts and model; it does
  not prove every earlier intervention or every deconfounding method fails.
- Point source at each native leaf's recorded first sample, not exact replay
  of the region generator. Truth is evaluated through its leaf representative.
- Bernoulli observation surrogate; actual temporal sensor correlations and
  external GADEN model discrepancy are not validated.
- Grid-off parameter values plus independent keyed replica, not an independent
  physics model or an untouched final test set.
- Native acquisition **heuristic**, with native weights and regenerated point
  responses, not a full native navigation/exploration-state replay.
- Confidence-weighted sensitivity projection is not calibrated Fisher
  information. Local null directions and zero source contrasts remain failures.

No ROS promotion, localization improvement, or main-innovation claim follows
automatically from this development screen.
