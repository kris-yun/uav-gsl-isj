# CODEX HANDOFF — CESS D1 630-Source Emergent-Scale Falsification

Date: 2026-09-24

Branch:
`research/causal-emergent-source-scale-v0`

Mission:
execute the frozen CESS D1 offline gate only.

## Scientific context

R0 has independently passed.

A strict 18-source D0 control showed an intermediate-scale peak in held-out raw source effective-information lower bound even when macro likelihoods were constructed only by mixing already-trained micro likelihoods.

D1 now tests this on the complete 630 equal-area PMFS source-cell bank.

This is not PMFS closed loop.

## Read first

`01_idea/CESS_THEORY_AND_D0_FREEZE_20260924.md`

`evidence/causal_emergent_source_scale_v0/CESS_D0_STRICT_INTERVENTIONAL_CONTROL_20260924.md`

`research/causal_emergent_source_scale_v0/CESS_D1_PROTOCOL_FREEZE_20260924.md`

## Hard freeze

Do not change:

- 630-source bank;
- House02 W2;
- 8 fresh realizations/source;
- seed formula;
- 10×30 observation operator;
- encounter threshold >0;
- Jeffreys alpha=0.5;
- connected Ward hierarchy;
- frozen M sequence;
- strict macro mixture likelihood;
- raw EI lower bound as primary scale metric;
- 2000 source-cluster bootstraps;
- 250 size-matched random controls;
- PASS/HOLD/STOP logic.

Do not use old C/D in D1 training.

No neural model.

No PASI/MZ rescue.

No closed loop.

## Checkout

```bash
git fetch origin
git checkout research/causal-emergent-source-scale-v0
git pull --ff-only
git status --short
git rev-parse HEAD
```

Require clean worktree.

## Static checks

```bash
python3 -m py_compile \
  research/causal_emergent_source_scale_v0/build_connected_ward_hierarchy.py \
  research/causal_emergent_source_scale_v0/analyze_cess_d1.py \
  research/causal_emergent_source_scale_v0/test_cess_d1_weighting.py

python3 research/causal_emergent_source_scale_v0/test_cess_d1_weighting.py

bash -n research/causal_emergent_source_scale_v0/run_cess_d1_vm.sh
bash -n research/causal_emergent_source_scale_v0/package_cess_d1_review.sh
```

The branch already contains one audited infrastructure-only repair: the D1 analyzer now evaluates held-out macro CE/EI under the frozen **uniform-macro intervention** rather than accidentally weighting macrostates by their number of microcells. The regression test above must print `CESS D1 weighting self-test: PASS`.

If any additional syntax/infrastructure defect is found before scientific execution, fix only the defect, preserve every frozen scientific contract, and commit the infrastructure patch separately.

## Execute

```bash
bash research/causal_emergent_source_scale_v0/run_cess_d1_vm.sh
```

The runner is resumable. Do not delete valid completed source/replicate outputs after interruption.

Expected new simulations:
`630 × 8 = 5040`.

Scientific exits:

- 0:
  `CESS_D1_PASS_EMERGENT_SOURCE_SCALE`
- 10:
  `CESS_D1_HOLD_MORE_REALIZATIONS`
- 20:
  `CESS_D1_FAIL_STOP_CAUSAL_EMERGENT_SCALE_MAINLINE`

Do not alter thresholds because exit 10/20 occurs.

## Commit evidence

After the run:

```bash
git add evidence/causal_emergent_source_scale_v0/d1/
git status --short
git commit -m "evidence: record CESS D1 630-source emergent-scale gate"
git push origin research/causal-emergent-source-scale-v0
```

If an infrastructure patch was required, it must already be a separate earlier commit.

## Package

```bash
bash research/causal_emergent_source_scale_v0/package_cess_d1_review.sh
```

Upload:

`/home/zyc/CESS_D1_REVIEW_20260924.tar.gz`

The package contains the full consolidated `(630,8,10,30)` pooled observation tensor, so the primary thread can independently recompute D1 without the 5040 full concentration cubes.

## Report only

1. branch;
2. final result commit;
3. decision;
4. supported scale bands;
5. peak M for Split A and Split B;
6. EI micro for each split;
7. maximum macro EI and M for each split;
8. macro physical cluster-size/diameter stats at the supported band;
9. random-control percentiles for supported M values;
10. bootstrap q2.5/q50/q97.5 for supported M values;
11. package path;
12. package bytes;
13. package SHA256;
14. infrastructure-only patch if any.

Then stop.

Do not run House01/03, cross-wind, PMFS closed loop, or auxiliary modules.
