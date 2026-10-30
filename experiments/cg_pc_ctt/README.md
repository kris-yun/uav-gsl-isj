# CG-PC-CTT Gate V2 — protocol repair branch

Candidate method: **Completeness-Gated Proximal-Causal Transport Tomography（完备性门控近端因果输运层析）**.

Status: **PROTOCOL REPAIR / NOT YET OFFLINE-QUALIFIED**.

V1 is `INVALID_PROTOCOL`: finite M=8 candidate-mean noise could create false rank-3 and false absolute strength under a true null. V2 does not tune that failure away. It changes the statistic.

## V2 gate
Input per context: `phi[S,M,D]`.

V2 estimates feature-wise member-noise scale from pairwise member differences, centers sources separately inside each member, then forms only **cross-member** products. The resulting replicated source operator has no same-member mean-noise square:

`K = sum_{m!=n} C_m^T C_n / (M(M-1)S)`.

For the pre-registered third source-contrast direction:

- `alpha_cf = sqrt(max(lambda_3,0))` — replicated absolute contrast amplitude after nuisance scaling;
- `gamma_cf = sqrt(max(lambda_3,0)/max(lambda_1,eps))` — relative conditioning;
- `p_signflip` — exact member-level sign-flip null. With M=8 there are 128 unique patterns and the smallest possible p-value is 1/128 = 0.0078125.

Primary V2 screen is frozen at `rank_k=3`, `gamma_min=0.05`, `p_max=0.01`. There is **no alpha threshold calibration** in V2.

## Member semantics are binding

Before real data evaluation, declare exactly one:

- `exchangeable_realizations`: independently sampled/exchangeable transport realizations around one nuisance-generating process. Only this permits inferential PASS.
- `fixed_nuisance_design`: deterministic support points / parameter grid / hand-selected transport variants. V2 will return `inferential_valid=False` and refuse source release. A separate robust-set protocol is required.

Do not guess this field from filenames.

## Commands

```bash
git checkout research/cg-pc-ctt-gate-v2
cd experiments/cg_pc_ctt
python3 selftest.py

# Then locate and qualify the actual M1 bank; do not use ME-ACI V10 evidence as a substitute.
python3 find_m1_bank.py /path/to/search/root --out /tmp/m1_bank_candidates.json
python3 qualify_m1_bank.py /path/to/m1_context_ensemble.npz

# Only after SELFTEST V2 PASS + bank qualification + exchangeable member semantics:
python3 run_gate_eval.py \
  --npz /path/to/m1_context_ensemble.npz \
  --out /tmp/cg_pc_ctt_gate_v2.csv \
  --member-semantics exchangeable_realizations
```

Read `docs/CODEX_CG_PC_CTT_PROTOCOL_V2_20260827.md` before any H03/H02 evaluation. No 300 s closed-loop run is authorized by this branch until the V2 offline protocol reaches GO.
