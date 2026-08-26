# CG-PC-CTT offline research screen

Candidate method: **Completeness-Gated Proximal-Causal Transport Tomography（完备性门控近端因果输运层析）**.

Status: **CURRENTLY TESTING**, not a frozen paper claim.

## Gate
For M1 features `phi[s,m,t]`, compute candidate means, source contrasts, project transport residuals into the `<=S-1` source-contrast subspace, estimate regularized transport covariance there, whiten source contrasts, then compute:

- `gamma = sigma_min / sigma_max`: relative conditioning;
- `alpha = sigma_min`: absolute weakest source direction after transport-uncertainty normalization;
- `beta = minimum pairwise whitened source separation`: diagnostic only in V1.

On FAIL the exact contract is **ABSTAIN**: `q_t(s)=q_{t-1}(s)`.

## Commands
```bash
cd experiments/cg_pc_ctt
python3 selftest.py
python3 calibrate_gate.py --npz /path/to/m1_context_ensemble.npz --gamma-min 0.05 --min-coverage 0.20
python3 run_gate_eval.py --npz /path/to/m1_context_ensemble.npz --out /tmp/gate_eval.csv --gamma-min 0.05 --alpha-min <FROZEN_DEV_VALUE>
```

Input NPZ: `phi[N,S,M,D]`, optional `context[N]`, `house[N]`, and required-for-calibration `split[N]`, `margin[N]`.

See `docs/CODEX_CG_PC_CTT_EXPERIMENT_PROTOCOL_20260827.md` before running any held-out or closed-loop experiment.
