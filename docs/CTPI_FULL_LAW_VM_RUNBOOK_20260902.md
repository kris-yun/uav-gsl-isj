# CTPI-FL V0.3 VM execution runbook

**Purpose:** run the already-frozen Oracle falsification Gate on the existing 30 historical tapes and 4936 exact-route source-member worlds.

**Branch:** `research/ctpi-full-law-ideaspark-20260902`

**Scientific state before execution:** `HOLD / ORACLE FALSIFICATION ONLY`.

Do not change a formula, add a hyperparameter, regenerate GADEN data, train a network/SBI model, or start closed loop after this runbook begins.

---

## 0. Checkout and record provenance

```bash
cd <repo-root>
git fetch origin
git checkout research/ctpi-full-law-ideaspark-20260902
git pull --ff-only origin research/ctpi-full-law-ideaspark-20260902

git status --short
git rev-parse HEAD
git diff --exit-code
```

Required: clean worktree. Record `git rev-parse HEAD` in the final evidence package.

---

## 1. Run all code-level selftests before reading truth

```bash
python3 experiments/cg_pc_ctt/ctpi_full_law_core.py --selftest --iterations 3000
python3 experiments/cg_pc_ctt/ctpi_full_law_controls.py
python3 experiments/cg_pc_ctt/ctpi_full_law_gate.py --selftest
```

Required exact status lines:

```text
CTPI_FULL_LAW_SELFTEST=PASS iterations=3000
CTPI_FULL_LAW_CONTROLS_SELFTEST=PASS
CTPI_FULL_LAW_ORACLE_GATE_SELFTEST=PASS
```

Any failure: STOP. Do not patch after looking at scientific outcomes.

---

## 2. Verify frozen input assets

Expected assets:

```text
FULLGRID_ROOT=/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1
HIST_ROOT=/home/zyc/CG_PC_CTT_V3_ORR_FULL60_PACKAGE_20260827/results
ROUTE_ROOT=/home/zyc/PF_DEI_V3_FINAL_SIM_BANK_20260828_R1
SUPPORT=/home/zyc/PF_DEI_V3_REGION_SUPPORT_20260828/source_region_3d_support_manifest.csv
PREREG=docs/CTPI_FULL_LAW_ORACLE_GATE_V03_PREREG_20260902.json
```

Resolve the **exact** old frozen factorial Stage1 by hash; do not guess a replacement directory:

```bash
EXPECTED_FACTORIAL_MANIFEST_SHA=a284dd44158bca847d1dbb2689153264ba54e29a0764a1fb1dd9e6785da92cb8
find /home/zyc -type f -name FACTORIAL_STAGE1_MANIFEST.json -print | while read -r f; do
  h=$(sha256sum "$f" | awk '{print $1}')
  if [ "$h" = "$EXPECTED_FACTORIAL_MANIFEST_SHA" ]; then
    echo "MATCH $f"
  fi
done
```

There must be exactly one intended frozen match. Set:

```bash
FACTORIAL_STAGE1=<directory-containing-the-matched-FACTORIAL_STAGE1_MANIFEST.json>
```

The evaluator will independently verify:

- route-bank summary SHA256 `17364eb744f4fc53c4b52eee0362f09bdee3e8655b74c9d5e5a2eb0a3a9e2d47`;
- route-bank manifest SHA256 `c68e4bcbd196a85d74ff9a44db01b2090f4487fc84943f82fcd0d17a18629bed`;
- support manifest SHA256 `4fec448feed607ea8c63148750ae9a610cf2e837a3df30808a256402c2d3a402`;
- old CPIR prereg/factorial semantic hashes;
- current full-grid carrier/q0 identity against the frozen old Stage1.

Any mismatch: STOP. Do not substitute another bank.

---

## 3. Stage1 — truth-blind Oracle freeze

Choose fresh, non-existing directories:

```bash
STAGE1=/home/zyc/CTPI_FULL_LAW_V03_STAGE1_20260902_R1
STAGE2=/home/zyc/CTPI_FULL_LAW_V03_STAGE2_20260902_R1
```

Run:

```bash
python3 experiments/cg_pc_ctt/ctpi_full_law_gate.py \
  --stage stage1 \
  --bank-root "$FULLGRID_ROOT" \
  --historical-root "$HIST_ROOT" \
  --support-path "$SUPPORT" \
  --route-bank-root "$ROUTE_ROOT" \
  --factorial-stage1 "$FACTORIAL_STAGE1" \
  --prereg-path "$PREREG" \
  --output "$STAGE1" \
  2>&1 | tee /home/zyc/CTPI_FULL_LAW_V03_STAGE1_20260902_R1.log
```

Stage1 must not read `case_result.json` truth. It must reproduce the frozen F00 artifact to max absolute error `<=1e-12` and freeze the full-law outputs before Stage2.

After Stage1 completes, **do not edit anything inside `$STAGE1`**. Record hashes:

```bash
find "$STAGE1" -maxdepth 1 -type f -print0 | sort -z | xargs -0 sha256sum \
  > /home/zyc/CTPI_FULL_LAW_V03_STAGE1_20260902_R1.sha256
sha256sum "$STAGE1/CTPI_STAGE1_MANIFEST.json"
```

Before opening truth, inspect only truth-blind mechanism fields in the manifest / Stage1 files:

- exact F00 parity;
- `contexts_with_mean_alias_distinct_pairs` for H01/H02/H03;
- nonzero M2 CDF-law separation;
- nonzero M3 RPS robustness structure.

If Stage1 itself raises a hash/parity/shape/strict-expressivity contract error: STOP and report the error verbatim. Do not alter the method.

---

## 4. Stage2 — truth evaluation only after Stage1 is frozen

Run exactly once against the frozen Stage1:

```bash
python3 experiments/cg_pc_ctt/ctpi_full_law_gate.py \
  --stage stage2 \
  --bank-root "$FULLGRID_ROOT" \
  --historical-root "$HIST_ROOT" \
  --support-path "$SUPPORT" \
  --prereg-path "$PREREG" \
  --stage1-root "$STAGE1" \
  --output "$STAGE2" \
  2>&1 | tee /home/zyc/CTPI_FULL_LAW_V03_STAGE2_20260902_R1.log
```

The code first re-verifies Stage1/prereg/support/full-grid hashes and the House-level truth-carrier statistical unit. Only then does it evaluate truth.

Terminal status is one of:

```text
CTPI_FULL_LAW_ORACLE_GO_TO_BANKFREE_M1_GATE
CTPI_FULL_LAW_ORACLE_NO_GO
```

Do not reinterpret a failed Boolean Gate after seeing the result.

---

## 5. Required result inspection

Read:

```text
$STAGE2/CTPI_STAGE2_SUMMARY.json
$STAGE2/CTPI_UPDATE_ROWS.csv
$STAGE2/VERDICT.txt
```

Report separately for H01/H02/H03:

1. `J_H_true` for CTPI-FL and area-matched F00;
2. source-label tail mass;
3. mean true-source normalized rank;
4. number of truth contexts with exact-F00-mean/full-law-distinct competitors;
5. truth-vs-alias CTPI persistence margin when such contexts exist;
6. source-law reassignment control degradation and break-strength/degradation Spearman sign;
7. final error / error AUC / time-to-2m as **secondary** diagnostics only.

Do not pool away a reversed House.

---

## 6. Package evidence without modifying outputs

```bash
EVID=/home/zyc/CTPI_FULL_LAW_V03_ORACLE_EVIDENCE_20260902_R1
mkdir -p "$EVID"
cp /home/zyc/CTPI_FULL_LAW_V03_STAGE1_20260902_R1.log "$EVID/"
cp /home/zyc/CTPI_FULL_LAW_V03_STAGE2_20260902_R1.log "$EVID/"
cp /home/zyc/CTPI_FULL_LAW_V03_STAGE1_20260902_R1.sha256 "$EVID/"
cp "$STAGE1/CTPI_STAGE1_MANIFEST.json" "$EVID/"
cp "$STAGE2/CTPI_STAGE2_SUMMARY.json" "$EVID/"
cp "$STAGE2/CTPI_UPDATE_ROWS.csv" "$EVID/"
cp "$STAGE2/VERDICT.txt" "$EVID/"
git rev-parse HEAD > "$EVID/GIT_HEAD.txt"
sha256sum "$PREREG" > "$EVID/PREREG_SHA256.txt"

tar -C /home/zyc -czf /home/zyc/CTPI_FULL_LAW_V03_ORACLE_EVIDENCE_20260902_R1.tar.gz \
  "$(basename "$EVID")"
sha256sum /home/zyc/CTPI_FULL_LAW_V03_ORACLE_EVIDENCE_20260902_R1.tar.gz
```

---

## 7. Decision boundary

If verdict is `NO_GO`:

- freeze the result;
- do not tune RPS, robustness axes, source-law controls, sensor threshold, or source strength;
- do not introduce network/SBI;
- do not regenerate GADEN worlds from truth.

If verdict is `GO`:

- this authorizes **only** the next bank-free M1 Gate:

```text
map + executed route + deployable local wind/context
        -> source-conditioned route-encounter law or conservative law envelope
```

- held-out House bank remains forbidden;
- source strength must be a source-shared nuisance;
- no closed-loop claim is authorized yet.
