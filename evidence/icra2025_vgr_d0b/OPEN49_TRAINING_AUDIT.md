# D0B historical OPEN49 training audit

**Decision: OPEN49_TRAINABLE**

- Exact historical cohort: 49 Native trajectories, 16 House01 + 33 House02; 48 archive hashes and 1 raw-log hash set verified.
- Maps: original occupancy SHA in each historical launch log matches restored 3D occupancy; exact z=0.20m slice and logged uncropped domain reconstructed. No propagated measured-map probabilities are training inputs.
- Pose, completed block time, actual hit/miss and local measured wind are present in all 49. Causal pose age and event/block XY agreement pass.
- Labels use only the archived truth XY, checked against runtime bindings. Labels are excluded from input channels.
- 697 encounter prefixes; 4 official rotations = 2,788 tensor samples. These remain 49 physical trajectories, not 2,788 independent plumes.
- Five trajectories have no encounter and yield no official encounter-index prefix; retained in audit, no synthetic hit/label invented.
- 553 training + 144 validation prefixes. Historical train/dev source split is retained; the extra historical OPEN House02 source joins training. All prefix/rotation samples from a physical trajectory remain in one split.
- Current ocb_r2_cfg00_r01 realization excluded. No confirmation or House03 read. No GADEN, PMFS run or closed loop.
- Exact official label-constructor and incremental-vs-cumulative adapter parity checked on 3 representative prefixes across both Houses.

## Scope and limitations

Historical custom source panel and legacy generator are training data only. The current original-source prospective target uses a different generator and sensor altitude (0.30m vs training 0.20m). This is a transfer headroom test, not a matched benchmark.
Validation contains the two historically held-out House01 sources; there is no House02 validation source in the preserved historical split. Do not imply House02 validation performance.
Original notebooks train 100 epochs. This bounded engineering test freezes 20 epochs, with the same architecture, loss, optimizer, batch size and initial learning rate. The checkpoint is selected solely by validation loss; target error cannot affect any choice.

## Execution boundary

Train once from random initialization. Evaluate only the existing D0-Lite event stream, then STOP. No new case, model changes, PMFS-3D, or 64-run campaign.
