# CODEX TASK — SOLICM-G0 Latent Causal Alignment Transfer Gate

Branch:
`research/solicm-latent-causal-g0-20260926`

Authoritative files:
- `research/solicm_v0/SOLICM_G0_CHARTER_20260926.md`
- `research/solicm_v0/SOLICM_SCIENTIFIC_BOUNDARY_20260926.md`

Pinned upstream code:
- `DMIRLAB-Group/LCA@45c091fca909ac13675c6ddac7e0464f0a186355`
- RO-CRL is literature-only at G0; do not execute it.

Hard scope:
- 0 new plume;
- H02 W0=`3,5-1_slow` and W2=`4,5-3_slow` only;
- exact same six E2 source locations;
- exact same E2 House02 30-probe observation contract;
- all 16 already-open realizations/source/domain;
- do not read H01 DEV or House03;
- do not use G1A 168-source bank;
- no custom SOLICM network yet;
- no hyperparameter search.

Stage A0:
1. verify W0/W2 six-source identity/order and exact probe/time tensor contract;
2. verify 16 realizations/source/domain and freeze realization indices;
3. clone/vendor the pinned LCA code and record all upstream file hashes;
4. implement only a dataset adapter and explicit model variants M0-M3;
5. disable target-label metric computation during training;
6. freeze model configs, folds, seeds and bootstrap seeds before any heldout scoring;
7. write `SOLICM_G0_PRE_RUN_LOCK.json`.

Training:
- both directions W0->W2 and W2->W0;
- four target folds;
- seeds 0,1,2;
- 40 epochs, batch 32;
- source-loss checkpoint selection only;
- M0 SOURCE_ONLY;
- M1 PL_ONLY;
- M2 LCA_NO_ALIGN with only structure_weight=0;
- M3 LCA_FULL official defaults.

Scoring:
1. export logits/probabilities for every heldout target realization;
2. compute multiclass NLL/Brier/accuracy/macro-F1/top3/rank/entropy;
3. compute the three frozen adjacent-pair diagnostics;
4. aggregate seed -> target -> direction×source;
5. run 10,000 cluster bootstrap over the 12 direction×source units;
6. apply G0-1..G0-6 exactly;
7. export latent-structure audit for M2/M3.

Independent verification:
- independently recompute all softmax probabilities and target metrics from saved logits;
- independently recompute Delta_align, Delta_PL, source-unit tables and every gate;
- verify no target label was read by any training/checkpoint-selection code path.

Required deliverables:
- `SOLICM_G0_PRE_RUN_LOCK.json`;
- `SOLICM_G0_DATA_AUDIT.json`;
- upstream-code manifest with pinned SHAs;
- per-run training configuration JSON;
- target-level logits/probabilities/metrics CSV or NPZ;
- direction×source summary CSV;
- seed summary CSV;
- adjacent-pair summary CSV;
- 10,000 cluster-bootstrap output;
- latent-structure audit NPZ/CSV;
- `SOLICM_G0_RESULT.json`;
- independent recomputation JSON;
- code/input/output SHA256 manifests;
- final branch commit;
- review package path/bytes/SHA256.

Final decision exactly one:
- `SOLICM_G0_PASS_LATENT_CAUSAL_ALIGNMENT_TRANSFER_SIGNAL`
- `SOLICM_G0_HOLD_UNSTABLE_NEURAL_TRANSFER_SIGNAL`
- `SOLICM_G0_STOP_LATENT_CAUSAL_ALIGNMENT_NOT_SOURCE_USEFUL`
- `SOLICM_G0_DATA_CONTRACT_STOP`

Stop immediately after G0.