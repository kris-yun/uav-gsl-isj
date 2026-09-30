# D0B VGR-supervised transfer headroom test

**D0B_VGR_TRAINED_DL_NO_GO**

Engineering development result on one previously viewed OPEN target. No new PMFS trajectory or plume was generated. No confirmation or House03 was read.

| Estimator | Position error (m) |
|---|---:|
| Native PMFS, existing same-stream estimate | 0.832047854 |
| Three compatible official zero-shot weights, mean | 4.813847963 |
| Compatible zero-shot best, reference only | 4.307897451 |
| D0B random-start trained 3-channel U-Net | 5.278820185 |

Truth XY: [-0.6, 1.95]. Trained official probability-weighted centroid XY: [-3.234445391320711, -2.6244551614624765]. Peak XY (diagnostic): [0.7500001236796381, -7.479999994039535].
Improvement against the frozen zero-shot mean: -9.66%. Inference: 0.703365s. Repeat predictions byte-identical: True.

## Frozen training

OPEN49_TRAINABLE: 49 original trajectories (H01=16, H02=33), 697 positive-event prefixes and four exact official rotations. Five no-encounter trajectories remain in the audit but produce no artificial training prefixes.
Actual positive-prefix trajectories: train 36, validation 8. Prefixes: train 553, validation 144. Augmented samples: train 2,212, validation 576. Validation contains two historically held-out H01 sources only; train/validation physical sources and trajectories do not overlap.
Exact upstream UNet(3,1), random initialization, float32. Exact CustomLoss positive_weight=5, Adam lr=1e-5 / weight_decay=0.1, batch=8, ReduceLROnPlateau factor=0.5/patience=5. No attention or additional inputs.
Fixed engineering budget: 20 epochs (upstream full run is 100); no early stopping or target-dependent continuation. Best validation epoch=20, loss=0.168910920. Total training time=4507.65s.
GPU: NVIDIA GeForce RTX 5060 Laptop GPU; parameter count: 31,037,633. Checkpoint: C:\GADEN_OCB_R2_ARCHIVE\d0b_supervised_20260930\training\best_validation_unet.pth. SHA256: `3d1a910d58d0794e116ed7147a92fc32eb5a01a51cdd663d4bfc06722866bd12`.

## Input and label audit

Maps reconstructed from original 3D occupancy at the archived 0.20m sensor altitude. Every archived occupancy SHA and domain matched; actual causal pose, block completion time, measured hit and local world-frame wind enter the same audited adapter. Propagated hit maps, candidate templates, unknown-area concentrations and truth are excluded from inputs.
Labels match the exact official labeler, including encounter-count-dependent radial radius, occupancy masking and %.2f output quantization. Three representative labels and complete channel tensors are exactly equal to independent upstream construction. Official padding asymmetry retained: training map=-1, inference map=0.
Current target has the prospective OCB generator, original source position and 0.30m sensor altitude. These differ from historical training; this remains a transfer test with limited source coverage. It cannot establish arbitrary-source generalization or a backbone performance ceiling.

## Scientific scope and stop boundary

The test case and zero-shot results were already viewed before this task. Neither the validation checkpoint nor training parameters were selected using target error. A development label is not a statistical claim that U-Net beats PMFS, nor a claim that the entire DL route succeeds/fails.
Route status under the requested finite-budget engineering gate: `TARGET_DOMAIN_TRAINED_BASELINE_NO_HEADROOM`.
STOP. No second case, four-case expansion, 64-run campaign, architecture change, extra epochs, GADEN, PMFS-3D or closed loop.

Frozen protocol commit: `dd31a09e`. Original raw archives and ROS2 src/build/install remain untouched.
