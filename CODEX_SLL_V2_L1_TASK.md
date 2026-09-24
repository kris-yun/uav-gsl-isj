# CODEX TASK — Source-Lineage Lagrangian v2 L1 ONLY

Branch:
`research/source-lineage-lagrangian-v2`

Purpose:
Run the already-frozen raw-filament L1 necessary-condition test.
Do NOT tune, generate new plume data, modify ROS/PMFS, or enter closed loop.

## Exact command

```bash
git switch research/source-lineage-lagrangian-v2
git pull --ff-only
bash research/source_lineage_lagrangian_v2/run_l1_vm.sh
```

The runner:
1. reads the existing raw bank at `/home/zyc/c0_5_real_gaden_bank_20260923`;
2. exports all 8 raw filament snapshot series;
3. reconstructs persistent lineage from exact GADEN save timing, sigma growth and 7 Hz birth schedule;
4. exports the canonical full 3-D W1/W2 fields;
5. trains only a small source-agnostic ridge residual on:
   - S1-W1 A/B
   - S2-W1 A/B
   - S1-W2 A/B
6. opens only then:
   - S2-W2 A/B
7. compares:
   - matched 2-D particle baseline;
   - deterministic 3-D lineage physics;
   - learned 3-D source-agnostic lineage transition;
   - destroyed-lineage null.

## Stop decisions

Possible outputs are intentionally distinct:

- `L1_FAIL_STOP_SOURCE_LINEAGE_MAINLINE`
  - 3-D lineage state itself does not solve the missing transport.
  - STOP the particle/lineage mainline.

- `L1_STATE_PASS_OPERATOR_NO_GO`
  - 3-D lineage representation helps, but deterministic physics explains the gain.
  - Do NOT claim a learned particle operator as the main innovation.
  - STOP learned-operator escalation.

- `L1_OPERATOR_PASS_FREEZE_BEFORE_L2`
  - both the lineage state and learned source-agnostic operator survive.
  - Freeze hashes first; only then authorize L2 source-candidate ranking.

## Required evidence

Commit/push only the compact files:
- `evidence/source_lineage_lagrangian_v2/SLL_V2_L1_RESULT_20260924.json`
- `evidence/source_lineage_lagrangian_v2/SLL_V2_L1_RESULT_20260924.model.npz`
- `evidence/source_lineage_lagrangian_v2/SLL_V2_L1_SHA256_20260924.txt`
- L1/export logs if small.

Do not commit the large lineage cache under `/home/zyc/sll_v2_lineage_bank_20260924`.

No L2 or closed-loop execution in this task.
