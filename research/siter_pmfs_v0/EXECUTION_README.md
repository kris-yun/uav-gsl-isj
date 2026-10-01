# Executed SITER v0 pipeline

This pipeline is complete and stopped. The commands below document reproducibility; they are not authorization for another model, tuning pass or closed loop.

1. `prepare_features.py`: verifies authoritative raw file SHA256, builds all 30 Native active-leaf partitions and source-blind features, checks Native posterior parity.
2. `recover_endpoint.py`: extracts the frozen historical C++ source only into an isolated output directory, builds Native ExpectedValue and a variance-readout extension. Never writes ROS2 src/build/install.
3. `check_math.py`: checks objective/constraint and evidence behavior independently of labels.
4. `fit_loho.py`: fits nested training-only capacity selection for general/flow/full, plus a bounded signed diagnostic. Freezes every outer model before evaluation.
5. Commit and push frozen model JSON and preprocessing. This happened at `aaabacf5`.
6. `evaluate_frozen.py`: first validates reconstructed C++ against 18 historical outputs; then scores the six held-out terminal posteriors.
7. `independent_audit.py`: uses separate feature/score/gate formulas, audits training exclusions and repeats complete scoring with byte comparison.

Inputs: `/mnt/hgfs/workspace/TNQC_R2_SIX_OFFLINE_20260921_authoritative`.

Isolated execution: `/mnt/hgfs/workspace/SITER_V0_20261001`.

All scripts accept `--root` and `--out`, except mathematical checks. Evaluator/audit additionally accept `--binary-dir`. The compact NPZ in the review package contains the exact cell/hit/wind arrays used by the audit, with the original raw file hashes in `FEATURE_PROVENANCE.json`; the original 140 MB archive remains intact.

`SOURCE_BLIND_FEATURE_DATA.npz` is not committed as a Git dataset; it is included in the compact review ZIP. No cache, ROS build or simulation bank is committed.
