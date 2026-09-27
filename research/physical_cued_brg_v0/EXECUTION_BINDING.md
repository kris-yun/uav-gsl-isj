# Execution binding, before scored campaign

Original ZIP: 39c79bf3a3053a61ff47d333e06edbc27a71e8f21e59f11e0f386bab43feffd8.
Amendment ZIP: 759f4593921fc41f3c902ad6a896fdd8d844e58c048c353690c3bbd8260db3df.
The amendment supersedes the six-label scored training and small H01/H02 campaign.
House03 is explicitly OPEN DEVELOPMENT. No fresh scientific status is restored.

VM software tests: 26 passed. Original three 30-epoch CPU six-label models are
FUNCTIONAL_SMOKE_ONLY and excluded from the scored deployment checkpoints.
ROS hook compilation succeeded on an isolated copy of the recovered Native source.
The desktop worktree helper was bound to cp-sbd-gsl and could not resolve the
uav-gsl-isj ref; the completed clean uav checkout was reused on the requested branch.

Full-support banks: all PMFS free cells, 626/631/631, all 11 physical wind CSV
states and 8 fixed transport RNG seeds (1..8), the audited native PMFS kernel,
unchanged p blur and unblurred rawu observer. No GADEN concentration counterfactual
is used. Exact old OPEN observations and 216/72 plume grouping are retained.
Bank generation is necessary model preparation, not newly generated GADEN plume.

Training: unchanged model.py/features.py, hidden32 BRG/ungated, hidden35 GRU,
30 epochs, 8 training / 4 dev routes, batch48, AdamW lr1e-3 weight_decay1e-4,
seed2026092701, OPEN-dev final-prefix NLL checkpoint selection. Unequal legal
supports are batched homogeneously; no candidate pruning or padding is used.
All three models use the same deterministic batching and device.

GPU preflight: RTX 5060 Laptop GPU 8GB, existing gas-tracking-cu130 environment,
PyTorch2.11.0+cu130. Full631-candidate batch48/10-step BRG: GPU0.5812s versus
CPU2-thread6.4529s per train step; peak allocated2.815GB. This is a synthetic
resource/software check only. No model score or scientific gate was produced.
Use isolated Python (-I), deterministic algorithms, CUBLAS_WORKSPACE_CONFIG=:4096:8,
no mixed precision, no TF32. No package installation or model search.

CLOSED LOOP: 96 existing H03 plumes x4 arms, full624 candidates, 300s,
0.5m evaluator radius. User geometric endpoint clarification is separately frozen.
Native PMFS top5%-probability weighted source estimate is the common estimate
operator for all arms; robot terminal pose cannot substitute for source estimate.
Actual existing recovered Native launch and gsl_benchmark_runner are the runtime
basis; adapter ports must record diffs and argv. Campaign will preserve all cases.
