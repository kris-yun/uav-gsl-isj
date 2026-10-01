# PMFS3D-O0 execution result

Decision: **PMFS3D_O0_VERTICAL_INFORMATION_STRONG**

Branch: `research/pmfs3d-o0-mechanism-ready-20261001`

Initial scientific freeze: `a8270ec1d7959259b8bbfd34d2b32b3cdbeb39e4`.
Execution repair freeze: `9ae2f33eb` (occupancy access only; no scientific changes).

## Frozen primary result

House02 / W1 only; both sources z=0.20 m. Original full-3D targets were
unchanged. Opposite-replicate templates were used in every comparison. The
static compositional profile removes total concentration magnitude; the frozen
Hellinger truth-minus-false affinity margin was used without tuning.

| Target | FULL3D margin | PROJECTED2D margin | 3D minus projected |
| --- | ---: | ---: | ---: |
| S1/A | 0.912604 | 0.583531 | +0.329072 |
| S1/B | 0.881192 | 0.595335 | +0.285856 |
| S2/A | 0.864475 | 0.156760 | +0.707715 |
| S2/B | 0.895887 | 0.175578 | +0.720309 |

FULL3D correct: 4/4. PROJECTED2D correct: 4/4. Improved margins: 4/4.
Median margin increment: **0.5183935721975692**, exceeding frozen strong
threshold 0.05. The strong label follows the margin branch of the preregistered
gate. There is **no two-source Top-1 accuracy improvement** in this experiment.

## Execution and evidence

Exactly four GADEN executions completed, each with 566 iteration files. No
simulation reruns. The first extraction failed because the runner omitted the
occupancy file required by the old extractor. The original run was retained,
then extracted successfully after adding the exact occupancy bytes. hgfs does
not support the historical symlink, so a SHA256-verified copy was used. Failed
extraction evidence is retained. Source/seed/physics/time IDs/scorer/thresholds
were unchanged; profile/affinity/evaluate AST matches the original freeze.

All four old reference cube hashes match the historical spatial summary. Frozen
generator, extractor, occupancy and wind anchor hashes match. All 11 input and
projected wind hashes were verified after execution. Projection reports w=0
and preservation of sensor-plane u/v for all 11 states. Native PMFS 2D code
contract and both supplied self-tests passed.

Two complete read-only scoring passes were byte-identical and exactly reproduce
O0_RESULT.json. This is **scoring repeatability**, not a new validation of the
historical generator's same-seed reproducibility.

VM root: approximately 441 MB before, 440 MB after. Outputs were placed on the
existing shared disk, which still has approximately 5.7 GB free. Raw filament
directories were retained instead of deleted; every retained file was hashed.
Total retained raw size: 173,296,328 bytes. The ROS source/build/install and all
original assets were preserved.

Raw location:
`/mnt/hgfs/workspace/PMFS3D_O0_PROJECTED2D_20261001/projected2d_runs/*/raw_retained`

Small review evidence includes projected concentration cubes, generation and
extraction logs, run metadata, raw-file hash inventories, old reference cubes,
projection manifest, scripts, charter and results. Full raw directories remain
outside Git.

## Scope and stop

This supports increased spatial source-discrimination margin from full 3D
transport relative to the frozen vertical projection, in one House02 development
context. It does not establish improved full-map source rank, localization error,
PMFS closed-loop performance, cross-House generalization or outdoor performance.
The projected GADEN arm is not a byte-identical Native PMFS implementation.

No H01/H03, confirmation, second wind, R3A, PMFS closed loop, GenDA or world-model
training was run. **STOP: no follow-up experiment has been started.**
