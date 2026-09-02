# CTPI-FL V0.3 Oracle Route-Law Gate

## Purpose

Test the **framework itself** on the already frozen exact-route oracle before any bank-free transport approximation is attempted.

No GADEN, ROS launch, network/SBI training, parameter tuning, or closed-loop action is permitted.

## Stage 0 — mathematical and glue self-tests

```bash
python3 experiments/cg_pc_ctt/ctpi_full_law_core.py --selftest --iterations 1500
python3 experiments/cg_pc_ctt/ctpi_full_law_gate.py --selftest
```

Required:

```text
CTPI_FULL_LAW_SELFTEST=PASS
CTPI_FULL_LAW_ORACLE_GATE_SELFTEST=PASS
```

The core self-test contains the load-bearing strict-expressivity example: two source response laws with identical F00 mean projection but different CDFs. It also verifies the exact RPS-regret/CDF-distance identity numerically and checks histogram-DP RPS envelopes against exhaustive subset enumeration on small cases.

## Stage 1 — truth-blind freeze

Expected VM assets:

```text
bank/carrier geometry:
  /mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1
historical tapes:
  /home/zyc/CG_PC_CTT_V3_ORR_FULL60_PACKAGE_20260827/results
exact route bank:
  /home/zyc/PF_DEI_V3_FINAL_SIM_BANK_20260828_R1
support manifest:
  /home/zyc/PF_DEI_V3_REGION_SUPPORT_20260828/source_region_3d_support_manifest.csv
prior frozen factorial Stage1:
  /home/zyc/CPIR_FACTORIAL_ROUTE_DIAGNOSTIC_20260901_e2bb4a0_R3/stage1
```

The exact prior Stage1 directory should be resolved on the VM by locating `FACTORIAL_STAGE1_MANIFEST.json`; the code then verifies its preregistration, semantic-freeze and file hashes. Do not guess a replacement directory if the frozen manifest cannot be located.

Example command after resolving the exact Stage1 directory:

```bash
python3 experiments/cg_pc_ctt/ctpi_full_law_gate.py \
  --stage stage1 \
  --bank-root /mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1 \
  --historical-root /home/zyc/CG_PC_CTT_V3_ORR_FULL60_PACKAGE_20260827/results \
  --support-path /home/zyc/PF_DEI_V3_REGION_SUPPORT_20260828/source_region_3d_support_manifest.csv \
  --route-bank-root /home/zyc/PF_DEI_V3_FINAL_SIM_BANK_20260828_R1 \
  --factorial-stage1 <EXACT_FROZEN_FACTORIAL_STAGE1_DIR> \
  --prereg-path docs/CTPI_FULL_LAW_ORACLE_GATE_V03_PREREG_20260902.json \
  --output /home/zyc/CTPI_FULL_LAW_V03_STAGE1_20260902
```

Stage 1 must not read source truth. It freezes, per House × seed × update:

- complete `K[source,member]` route-count samples;
- exact F00 mean-projection numerator `T_s`;
- CDF/Cramer separation matrix;
- empirical transport replacement-radius matrix;
- exact RPS deletion envelopes and observation robustness depth;
- full `M x M` two-axis survivor surface;
- source-support persistence score;
- F00 area-matched comparison surface;
- counts of F00-exact-mean aliases that have distinct full laws.

### Truth-blind strict-expressivity Gate

For each House, the existing bank must contain at least one pair satisfying

\[
T_i=T_j,\qquad G_{ij}>0.
\]

If not, the claimed strict expressivity gain over F00 is not load-bearing in that House and the framework cannot receive the full-law mechanism claim from these data.

F00 posterior reproduction must match the already frozen Stage1 artifact to maximum absolute error `<= 1e-12` (an inherited parity tolerance, not a scientific tuning parameter).

## Stage 2 — truth evaluation

Only after Stage1 semantic/file hashes pass may Stage2 read `case_result.json` truth.

```bash
python3 experiments/cg_pc_ctt/ctpi_full_law_gate.py \
  --stage stage2 \
  --bank-root /mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1 \
  --historical-root /home/zyc/CG_PC_CTT_V3_ORR_FULL60_PACKAGE_20260827/results \
  --support-path /home/zyc/PF_DEI_V3_REGION_SUPPORT_20260828/source_region_3d_support_manifest.csv \
  --prereg-path docs/CTPI_FULL_LAW_ORACLE_GATE_V03_PREREG_20260902.json \
  --stage1-root /home/zyc/CTPI_FULL_LAW_V03_STAGE1_20260902 \
  --output /home/zyc/CTPI_FULL_LAW_V03_STAGE2_20260902
```

First verify the 10 seeds in a House map to one common truth carrier. Seeds are repeat realizations, not ten independent source labels.

## Primary development metrics

- integrated excess identification `J` over the full intrinsic robustness surface;
- q0-weighted source-label tail mass;
- true-source normalized rank of the descriptive persistence support;
- matched-area F00 versions of the same set-identification quantities;
- count of truth cases with a same-F00-mean but full-law-distinct competitor;
- within those truth-hard-alias contexts, the unweighted CTPI persistence margin of the true source over its exact-F00-mean alias competitors;
- control degradation under complete source-law reassignment.

Localization error, error AUC and time-to-2m are report-only downstream diagnostics, not tuning objectives.

## Parameter-free decision shape

No absolute improvement magnitude is selected. The Gate uses only direction/Pareto relations:

1. `J` must be positive in every House;
2. each House must be Pareto no-worse than area-matched F00 on `(J up, source-label tail down, true-source rank down)` with at least one strict improvement;
3. pooled CTPI-FL must be strictly better than F00 on all three quantities;
4. source-law reassignment must degrade the downstream `J`, and stronger physical-law destruction must correspond to greater degradation;
5. both M2 distribution separation and M3 robust RPS preference must be nontrivial in every House;
6. the truth-blind same-mean/distinct-law mechanism condition must occur in every House.
7. the strict-expressivity mechanism must touch the actual task at least once: across H01/H02/H03 there must be at least one context where the true source has an exact-F00-mean but full-law-distinct competitor. On the Houses where such contexts exist, the mean CTPI persistence margin of the true source over those alias competitors must not be negative, and the pooled context-weighted margin must be strictly positive. A House with no truth-hard-alias context is reported as `NOT_IDENTIFIED` for this direct mechanism diagnostic rather than being fabricated into positive evidence.

Possible outputs:

```text
CTPI_FULL_LAW_ORACLE_GO_TO_BANKFREE_M1_GATE
CTPI_FULL_LAW_ORACLE_NO_GO
```

A GO authorizes only the next **bank-free M1 approximation Gate**. It does not authorize a neural surrogate, unseen-House claim, closed loop, or paper-level confirmation.
