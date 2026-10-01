# R1P5 run provenance

Execution HEAD: `62a10ed2fdef6fca1e411d23bd1ab974a96685ff`.
Branch: `research/pmfs3d-r1p5-suppression-audit-20261001`.
Python: `3.10.19 | packaged by Anaconda, Inc. | (main, Oct 21 2025, 16:41:31) [MSC v.1929 64 bit (AMD64)]`.
Analysis script SHA256 (unmodified): `f242ce09420dcf410b82c26394a5e377dcdfe2e02ffc2864385bd664b523d05a`.
Charter SHA256: `5b6f637adea761e5d25c852124d023ff03e05eaf7a5722708534aae6eb96013d`.

## Invocation

```powershell
D:/Anaconda/envs/DL_5060_New/python.exe research/pmfs3d_r1p5/analyze_suppression_selectivity.py
  --science-root D:/ZYC/A-gas/_worktrees/ocb-r2-census-20260930/evidence/pmfs3d_r1_oracle_ranking_20261001/PMFS3D_R1_SCIENTIFIC_20261001
  --r1-result D:/ZYC/A-gas/_worktrees/ocb-r2-census-20260930/evidence/pmfs3d_r1_oracle_ranking_20261001/PMFS3D_R1_SCIENTIFIC_20261001/evaluation1/R1_RESULT.json
  --out evidence/pmfs3d_r1p5_suppression_audit_20261001
```

The frozen analysis was executed once. Input hash verification preceded execution.
All eight score files matched the previously committed R1 deterministic repeat manifest,
and their repeat2 copies were byte identical. The R1 result was also byte identical to
its committed R1 evidence copy. All original files remain unchanged.
Small exact input CSV copies are now retained and committed for independent review.

## Input files and SHA256

| Absolute original location | SHA256 |
|---|---|
| `D:\ZYC\A-gas\_worktrees\ocb-r2-census-20260930\evidence\pmfs3d_r1_oracle_ranking_20261001\PMFS3D_R1_SCIENTIFIC_20261001\evaluation1\R1_RESULT.json` | `f1b79a979a796ef0a410ac4f531b16c499ef649721c47e7071fa89c807ea07cf` |
| `D:\ZYC\A-gas\_worktrees\ocb-r2-census-20260930\evidence\pmfs3d_r1_oracle_ranking_20261001\PMFS3D_R1_SCIENTIFIC_20261001\repeat1\House01_seed0_off_off\oracle2d\candidate_log_scores.csv` | `13e09417759bfed5c955d0ccc7e135048036a5cebe01f55666e5327e3ea6f0f8` |
| `D:\ZYC\A-gas\_worktrees\ocb-r2-census-20260930\evidence\pmfs3d_r1_oracle_ranking_20261001\PMFS3D_R1_SCIENTIFIC_20261001\repeat1\House01_seed0_off_off\oracle3d\candidate_log_scores.csv` | `1c9bd8a9432548d3dee6ac38db3293d6df089b7189212bfe5bf1977ba5d6cf23` |
| `D:\ZYC\A-gas\_worktrees\ocb-r2-census-20260930\evidence\pmfs3d_r1_oracle_ranking_20261001\PMFS3D_R1_SCIENTIFIC_20261001\repeat1\House01_seed1_off_off\oracle2d\candidate_log_scores.csv` | `624c345c8eddd65825748e6018786b90925238157900d8a9ee787ef3b3531f3e` |
| `D:\ZYC\A-gas\_worktrees\ocb-r2-census-20260930\evidence\pmfs3d_r1_oracle_ranking_20261001\PMFS3D_R1_SCIENTIFIC_20261001\repeat1\House01_seed1_off_off\oracle3d\candidate_log_scores.csv` | `5f6b72a22dffac6a3a467be7f86e07038bec4459b7794cba73ff5c7dc5723e57` |
| `D:\ZYC\A-gas\_worktrees\ocb-r2-census-20260930\evidence\pmfs3d_r1_oracle_ranking_20261001\PMFS3D_R1_SCIENTIFIC_20261001\repeat1\House02_seed0_off_off\oracle2d\candidate_log_scores.csv` | `f7b2e861cc6cd550dc4967940562233702c3f1b172190401a90c457968b6e096` |
| `D:\ZYC\A-gas\_worktrees\ocb-r2-census-20260930\evidence\pmfs3d_r1_oracle_ranking_20261001\PMFS3D_R1_SCIENTIFIC_20261001\repeat1\House02_seed0_off_off\oracle3d\candidate_log_scores.csv` | `75ec35016fba3963d947b716fe6ca7c17b41ade3829c7f0b9e653b189d72e12e` |
| `D:\ZYC\A-gas\_worktrees\ocb-r2-census-20260930\evidence\pmfs3d_r1_oracle_ranking_20261001\PMFS3D_R1_SCIENTIFIC_20261001\repeat1\House02_seed1_off_off\oracle2d\candidate_log_scores.csv` | `de53a5514288d861d5479c945facc62bf0bee185e6d8706685120ba896403166` |
| `D:\ZYC\A-gas\_worktrees\ocb-r2-census-20260930\evidence\pmfs3d_r1_oracle_ranking_20261001\PMFS3D_R1_SCIENTIFIC_20261001\repeat1\House02_seed1_off_off\oracle3d\candidate_log_scores.csv` | `1e9720fd11e555063c8b768bb3c6815ac2be6e63e2a92845ac6beb1960445477` |

## Boundaries

No new GADEN, forward, training, ROS/closed loop or protected data access.
No gate, scorer, score value or input candidate set changed. Only post-result
verification using independent Numpy/SciPy arithmetic was added.
Evidence text files are normalized to LF for portable Git and ZIP SHA256 manifests;
retained input copies are byte-for-byte unchanged.

## Interpretation limits

Candidate IDs here denote original quadtree leaves. Cross-seed correlations use
only shared identical leaf IDs: 54 in H01 and 79 in H02. The original forward RNG
key was seed0 in all four R1 replays, as documented in the frozen R1 contract.
Thus these correlations assess suppression across different historical terminal
observation maps; they are not a test of independent new forward RNG realizations.
This is an OPEN historical diagnostic, not fresh confirmation.
The analysis uses truth only for post-hoc evaluation. It does not supply an online
truth-free contradiction verifier or authorize candidate elimination.
