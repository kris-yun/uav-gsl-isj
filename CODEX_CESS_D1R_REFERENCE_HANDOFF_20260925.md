# CODEX — CESS D1R REFERENCE BANK ONLY

Date: 2026-09-25

Branch:
`research/causal-emergent-source-scale-v0`

The previous D1/D1A scientific decision tasks are superseded for now.

Your mission is **data construction only**.

## Checkout

```bash
git fetch origin
git checkout research/causal-emergent-source-scale-v0
git pull --ff-only
git status --short
git rev-parse HEAD
```

Read:

- `01_idea/CESS_POST_PRO_REVIEW_MAINLINE_REVISION_20260925.md`
- `research/causal_emergent_source_scale_v0/CESS_D1R_REFERENCE_PROTOCOL_20260925.md`

## Static check

```bash
python3 -m py_compile research/causal_emergent_source_scale_v0/build_cess_d1a_panel.py
bash -n research/causal_emergent_source_scale_v0/run_cess_d1r_reference_vm.sh
bash -n research/causal_emergent_source_scale_v0/package_cess_d1r_reference_review.sh
```

## Execute

```bash
bash research/causal_emergent_source_scale_v0/run_cess_d1r_reference_vm.sh
```

Expected:
- 168 sources;
- 16 fresh references/source;
- 2688 runs;
- no replicate 17/18;
- no final partition;
- no mainline PASS/STOP.

Then commit only D1R evidence:

```bash
git add evidence/causal_emergent_source_scale_v0/d1r/
git commit -m "evidence: build CESS D1R 168x16 reference bank"
git push origin research/causal-emergent-source-scale-v0
```

Package:

```bash
bash research/causal_emergent_source_scale_v0/package_cess_d1r_reference_review.sh
```

Upload:

`/home/zyc/CESS_D1R_REFERENCE_REVIEW_20260925.tar.gz`

Report only:

1. branch;
2. final commit;
3. `CESS_D1R_REFERENCE_BANK_COMPLETE` or infrastructure stop;
4. valid source count / realization count;
5. split profile cosine median/q10;
6. split profile relative-error median/q75;
7. package path / bytes / SHA256;
8. infrastructure-only patch if any.

Then stop.

Do not generate final targets.
Do not choose scale.
Do not run D1A analyzer.
Do not run PMFS closed loop.
