# CODEX HANDOFF — D3 S1-W2 Second-Source Falsification

Date: 2026-09-24  
Branch: `research/realization-invariant-source-signature-v0`  
Minimum required ancestor: `b8e663ef9063905141ec3c19305364bfd7a0ae0d`

Status: **EXECUTE FROZEN D3 ONLY — NO THEORY CHANGES, NO CLOSED LOOP**

## Mission

Test whether the D0/D1/D2 realization-invariant finite-memory source signal generalizes from the original true source S2 to a different true source S1 in the same House02/W2 environment.

This is intentionally cheap:

- reuse the existing 630-source Gate-1A prediction bank for seeds C/D;
- generate only two new target realizations for S1 under W2;
- score them with the already-frozen D3 scorer.

Do not regenerate the 630-source prediction bank.

## Frozen truth

Truth source:

- source id: `pmfs_10_17`;
- xyz: `(-2.242730141, -2.200880051, 0.20)`.

The frozen 630-source bank already contains this exact source support cell.

Targets:

- `S1_W2_A`, seed `2026092301`;
- `S1_W2_B`, seed `2026092302`.

Prediction bank remains:

- seed C `2026092401`;
- seed D `2026092402`.

Wind remains House02 W2:

`3,5-1_slow`

No W1 data may enter scoring.

## Hard no-change rules

Do not change:

- 630-source bank;
- source truth;
- target seeds;
- prediction seeds;
- W2 wind;
- occupancy;
- GADEN parameters;
- 30 frozen pooled probes;
- 10 frozen times;
- per-time L1 mass-fraction projection;
- memory covariance construction;
- target-blind memory-horizon rule;
- D3 PASS/STOP rule.

No neural network.
No MEMnets training.
No Gate D4 / cross-House work.
No ROS / PMFS closed loop.
No score rescue after seeing S1 ranks.

Infrastructure-only repairs are permitted only if they preserve every item above. Commit them separately before the result commit.

## Checkout

```bash
cd /path/to/uav-gsl-isj
git fetch origin
git checkout research/realization-invariant-source-signature-v0
git pull --ff-only
git status --short
git rev-parse HEAD
```

Require a clean worktree.

Verify these files exist:

```bash
test -f research/realization_invariant_source_signature_v0/score_d3_second_source.py
test -f research/realization_invariant_source_signature_v0/run_d3_s1_w2_vm.sh
test -f research/realization_invariant_source_signature_v0/package_d3_s1_review.sh
test -f evidence/realization_invariant_source_signature_v0/D1_MORI_ZWANZIG_MEMORY_PROXY_20260924.md
test -f evidence/realization_invariant_source_signature_v0/D2_FINITE_MEMORY_SOURCE_LIKELIHOOD_20260924.md
```

Syntax check:

```bash
python3 -m py_compile research/realization_invariant_source_signature_v0/score_d3_second_source.py
bash -n research/realization_invariant_source_signature_v0/run_d3_s1_w2_vm.sh
bash -n research/realization_invariant_source_signature_v0/package_d3_s1_review.sh
```

## Execute D3

Run exactly:

```bash
bash research/realization_invariant_source_signature_v0/run_d3_s1_w2_vm.sh
```

Expected scientific work:

1. verify the existing Gate-1A bank has 630 predictions for each C/D seed;
2. verify `pmfs_10_17` equals the frozen S1 coordinates;
3. generate S1_W2_A;
4. generate S1_W2_B;
5. extract the same 10 x 83 x 119 cubes;
6. apply the same 30 pooled probes;
7. compute raw, D0-static, diagonal-time, and D2 finite-memory source ranks.

## Frozen memory rule

The memory horizon is estimated **only from prediction C-D realization differences**, never from S1 target ranks.

The rule is:

> retain all positive-lag correlations before the first non-positive mean temporal correlation.

No manual lag choice.

## Frozen PASS / STOP

Let the two target ranks be A and B.

D3 PASS requires all of:

1. D2 finite-memory truth rank <= 3 for A;
2. D2 finite-memory truth rank <= 3 for B;
3. sum(D2 A,B ranks) <= sum(raw A,B ranks);
4. sum(D2 A,B ranks) <= sum(D0-static A,B ranks);
5. sum(D2 A,B ranks) < sum(diagonal-time A,B ranks).

PASS decision:

`D3_PASS_SECOND_SOURCE_MEMORY_GENERALIZES`

Any failure:

`D3_FAIL_STOP_MZ_SOURCE_INFERENCE_MAINLINE`

If FAIL, do not rescue and do not generate cross-House data.

If PASS, still do not start cross-House work until independent review of the package.

## Commit evidence

After the run:

```bash
git add evidence/realization_invariant_source_signature_v0/
git status --short
git commit -m "evidence: record MZ D3 S1-W2 second-source result"
git push origin research/realization-invariant-source-signature-v0
```

If an infrastructure-only patch was needed, commit that patch separately first.

## Package for independent review

Run:

```bash
bash research/realization_invariant_source_signature_v0/package_d3_s1_review.sh
```

Upload this archive to ChatGPT:

`/home/zyc/MZ_D3_S1_W2_REVIEW_20260924.tar.gz`

## Report back

Report only:

1. branch;
2. final commit SHA;
3. D3 decision;
4. S1_W2_A raw / D0 / diagonal / D2 ranks;
5. S1_W2_B raw / D0 / diagonal / D2 ranks;
6. automatically selected memory horizon;
7. package path;
8. package bytes;
9. package SHA256;
10. any infrastructure-only patch.
