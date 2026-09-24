# CODEX HANDOFF — CESS D1A Dense Emergent-Scale Gate

Date: 2026-09-25

Branch:
`research/causal-emergent-source-scale-v0`

IMPORTANT:
**Do not run the older `CODEX_CESS_D1_HANDOFF_20260924.md`. It is superseded.**

## Mission

Execute only the frozen CESS D1A offline falsification.

Scientific workload:
- 168 dense source microstates;
- 16 fresh W2 realizations/source;
- total 2688 GADEN runs;
- corrected intervention-weighted EI;
- no PMFS closed loop.

## Read first

1. `01_idea/CESS_MAINLINE_FREEZE_V1_20260925.md`
2. `evidence/causal_emergent_source_scale_v0/CESS_D0_INTERVENTION_WEIGHTING_CORRECTION_20260925.md`
3. `evidence/causal_emergent_source_scale_v0/CESS_OLD_D1_630X8_SUPERSEDED_20260925.md`
4. `research/causal_emergent_source_scale_v0/CESS_D1A_PROTOCOL_FREEZE_20260925.md`

## Hard freeze

Do not change:

- Gate1A source-bank / contract hashes;
- largest-complete-rectangle panel selection;
- frozen 168-cell result;
- House02 W2;
- 16 realizations/source;
- seed formula;
- 10×30 observation operator;
- encounter threshold >0;
- Bernoulli Jeffreys alpha=0.5;
- connected Ward hierarchy;
- frozen M sequence;
- macro likelihood = uniform mixture of already-trained micro likelihoods;
- uniform macro intervention / uniform-within-macro evaluation;
- raw EI lower bound;
- 2000 realization bootstraps;
- 250 size-matched random controls;
- PASS/STOP logic.

No old C/D or R0 realization enters D1A estimation.

No neural model.
No PASI/MZ rescue.
No alternate clustering.
No closed loop.

## Checkout

```bash
git fetch origin
git checkout research/causal-emergent-source-scale-v0
git pull --ff-only
git status --short
git rev-parse HEAD
```

Require a clean worktree.

## Static checks

```bash
python3 -m py_compile   research/causal_emergent_source_scale_v0/build_cess_d1a_panel.py   research/causal_emergent_source_scale_v0/build_cess_d1a_hierarchy.py   research/causal_emergent_source_scale_v0/analyze_cess_d1a.py

bash -n research/causal_emergent_source_scale_v0/run_cess_d1a_vm.sh
bash -n research/causal_emergent_source_scale_v0/package_cess_d1a_review.sh
```

If a genuine infrastructure bug is found before result generation, fix only
that bug, preserve every scientific contract, and commit it separately.

## Execute

```bash
bash research/causal_emergent_source_scale_v0/run_cess_d1a_vm.sh
```

The runner is resumable. Do not delete valid completed outputs after
interruption.

Scientific exits:

- 0: `CESS_D1A_PASS_EMERGENT_SOURCE_SCALE`
- 20: `CESS_D1A_FAIL_STOP_CAUSAL_EMERGENT_SCALE_MAINLINE`

There is no scientific HOLD.

Do not alter any threshold after exit 20.

## Commit evidence

```bash
git add evidence/causal_emergent_source_scale_v0/d1a/
git status --short
git commit -m "evidence: record CESS D1A dense emergent-scale gate"
git push origin research/causal-emergent-source-scale-v0
```

## Package

```bash
bash research/causal_emergent_source_scale_v0/package_cess_d1a_review.sh
```

Upload:

`/home/zyc/CESS_D1A_REVIEW_20260925.tar.gz`

## Report only

1. branch;
2. final result commit;
3. decision;
4. supported scale bands;
5. peak M in Split A / Split B;
6. micro EI in both splits;
7. maximum macro EI and corresponding M in both splits;
8. bootstrap q2.5/q50/q97.5 for all supported M;
9. spatial random-control percentile for all supported M;
10. physical cluster cell-count/area/diameter at supported M;
11. micro top1/top3 and MAP-error median/q90;
12. posterior mass within 0.5m / 1.0m;
13. neighbor 0.3m vs >=3m encounter-profile cosine diagnostic;
14. package path / bytes / SHA256;
15. any infrastructure-only patch.

Then stop.

Do not run full 630 confirmation, House01/03, other wind, auxiliary module, or
PMFS closed loop.
