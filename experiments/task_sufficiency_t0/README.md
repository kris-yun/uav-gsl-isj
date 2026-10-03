# Frozen T0-A feasibility probe

Run `prepare.py` (read-only archive inputs, native VM playback), `audit.py` (byte lineage and training freeze), `train.py` (tiny CPU models), then `package.py` (contract verification, report, ZIP).

Dependencies: Python, numpy, pandas, scipy, sklearn, torch, matplotlib; for fresh extraction, the unchanged qualified OCB-R2 VM GADEN library and original host archives are required. No installation or upgrade is performed. Outputs live in `evidence/task_sufficiency_t0_20261003`.

To retrain from the evidence ZIP only, run `train.py`; it needs RUNS.json and the 32 observation CSVs, not native plume payloads. Encoder checkpoints preserve model and normalization; downstream heads are deterministic fits reproducible by the script.

The frozen protocol defines context aliases, split, route, losses, readouts and gate operationalization. The sole engineering repair after first attempted fitting explicitly casts source targets to torch.long; the original freeze and error log are retained. No thresholds, epochs, endpoints or data splits were changed.

Hand statistics are an additional local evidence summary, not PMFS. Generic is a tiny sequence autoencoder. Neither is a faithful reproduction of any published method. No flow-memory, active probing, dense 3D reconstruction or new propagation dataset is run here.

This is a feasibility screen for a specific estimator/route. A failure does not mathematically falsify all task-sufficient source–plume representations. Respect the formal gate and stop subsequent experimental expansion.
