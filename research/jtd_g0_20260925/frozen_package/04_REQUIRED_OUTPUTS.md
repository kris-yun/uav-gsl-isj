# 04 — REQUIRED OUTPUTS AND EVIDENCE TREE

Create only under:

`evidence/jtd_g0_20260925/`

Required tree:

```text
evidence/jtd_g0_20260925/
├── audit/
│   ├── R0_INPUT_AUDIT.json
│   └── R0_INPUT_AUDIT.md
├── cache/
│   └── canonical_r0.npz
├── config/
│   ├── frozen_config.yaml
│   ├── folds.json
│   └── shuffle_seeds.json
├── metrics/
│   ├── target_metrics_full.csv
│   ├── target_metrics_null_long.csv
│   ├── null_replicate_summary.csv
│   ├── fold_summary.csv
│   ├── source_summary.csv
│   ├── leave_one_source_out.csv
│   ├── confusion_full.csv
│   ├── confusion_null_median.csv
│   └── control_models_summary.csv
├── models/
│   ├── pca_manifest.json
│   └── model_manifest.json
├── figures/
│   ├── nll_null_distribution.png
│   ├── source_delta_nll.png
│   ├── fold_delta_nll.png
│   └── rank_full_vs_null.png
├── logs/
│   ├── run.log
│   └── environment.txt
├── MANIFEST_SHA256.txt
├── JTD_G0_MACHINE_SUMMARY.json
└── JTD_G0_DECISION_20260925.md
```

## Machine summary required keys

See `templates/machine_summary_schema.json`.

## Decision report must answer exactly

1. What exact R0 commit/data were used?
2. Did input contract pass?
3. How many sources?
4. How many independent realizations/source?
5. Was ordered 10×30 structure verified from metadata?
6. FULL mean NLL?
7. Median SHUFFLED mean NLL?
8. Relative NLL gain?
9. Empirical null p-value?
10. Bootstrap CI?
11. Four fold effects?
12. Positive source count?
13. Leave-one-source-out sign stability?
14. Rank/top-3 comparison?
15. Decision label?
16. What scientific claim is allowed?
17. What claim is forbidden?
18. Was any closed loop, dense expansion, new plume generation, or hyperparameter rescue run?
19. Branch/final commit?
20. Evidence ZIP path/SHA256?

## ZIP

At the end create:

`JTD_G0_REVIEW_PACKAGE_20260925.zip`

Include:
- required evidence tree
- exact scripts used
- frozen config
- git diff patch
- `git status`
- `git log -5`
- environment/package versions

Do not include huge old R0 raw archives if already immutable and hashed; include their provenance/hash references.
