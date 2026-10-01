# Codex handoff — MDBIL-D0

Work only on:

`research/mdbil-d0-source-weather-invariance-20261001`

Read `research/mdbil_d0/MDBIL_D0_FREEZE.md` first. The prior CDSI-T0.1B result remains frozen and must not be overwritten.

## Execute exactly

```bash
git checkout research/mdbil-d0-source-weather-invariance-20261001
python3 -m pip install -r research/mdbil_d0/requirements.txt
python3 research/mdbil_d0/run_mdbil_d0.py --self-test

rm -rf evidence/mdbil_d0/pass1 evidence/mdbil_d0/pass2
python3 research/mdbil_d0/run_mdbil_d0.py --output evidence/mdbil_d0/pass1
python3 research/mdbil_d0/run_mdbil_d0.py --output evidence/mdbil_d0/pass2
python3 research/mdbil_d0/verify_repeat.py --a evidence/mdbil_d0/pass1 --b evidence/mdbil_d0/pass2 | tee evidence/mdbil_d0/DETERMINISTIC_REPEAT.json
```

Do not change epochs, seeds, loss weights, gate thresholds, C>0 tensor definition, source labels, or split after seeing held-out metrics.

If a tensor is missing, fails SHA, has illegal shape/range, or breaks the frozen context contract, record `MDBIL_D0_INVALID_INPUT_STOP` and stop.

Commit both evidence pass directories plus `DETERMINISTIC_REPEAT.json`. Preserve INPUT_SHA256.tsv, DATA_CONTRACT.json, MODEL_CONFIG.json, SEED_METRICS.tsv, FOLD_METRICS.tsv, MDBIL_D0_RESULT.json, and DECISION.md.

Hard contract:

- new GADEN = 0
- new source interventions = 0
- PMFS = 0
- closed loop = 0
- H03 / confirmation = 0

Regardless of the D0 decision, do not integrate MDBIL into PMFS in this task.

Return branch + final commit; D0 decision; input/SHA contract; all 8 FOLD_METRICS rows; G1-G4; median RAW/VANILLA/MDBIL held-out accuracy; general and same-gas cross-wind ratios; z_s context leakage and z_m context decoding; deterministic repeat; and confirmation that all prohibited run counts are zero.

Then STOP.
