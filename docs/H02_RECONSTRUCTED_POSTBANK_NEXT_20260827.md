# H02_RECONSTRUCTED_CHALLENGE_V1 — immediate post-bank execution

Status: **BANK VERIFIED; run this before any outcome/margin/bridge inspection**.

The reconstructed bank is complete: 51 frozen H02 context atoms × 201 geometry carriers × 8 keyed members = 82,008 verified traces. The inferential cluster unit is frozen as seed (6 seed clusters), not source-update row.

## Important optimization

Do not rerun the forward simulator merely to recover candidate/member hit-frequency fields.

Each frozen `.cttbin` already stores:

1. `firstHitBins[cell]`;
2. `occupancyWords[timestep,cell]`.

`CTTTransportTrace::reconstructFrequencies()` defines the exact native PMFS cumulative response as

`hit_frequency(cell) = mean_t occupied(t,cell)`.

The builder verified `reconstruction_max_abs == 0` for every record. Current `ctt_bank_io.py` therefore decodes both `first_hit` and exact `hit_frequency` directly from the verified trace product.

## Commands

```bash
set -Eeuo pipefail
cd /home/zyc/uav-gsl-isj   # adjust only repository location if needed

git fetch origin
git checkout research/cg-pc-ctt-v3-observation-quotient-theory
git pull origin research/cg-pc-ctt-v3-observation-quotient-theory

cd experiments/cg_pc_ctt
bash run_v3_selftests.sh

export H02_RECONSTRUCTED_ROOT=/home/zyc/H02_RECONSTRUCTED_CHALLENGE_V1_20260827_r1
export H02_CONTEXT_MANIFEST=/tmp/h02_reconstructed_v1_20260827/H02_RECONSTRUCTED_CONTEXT_MANIFEST.csv

# Use the VERIFY.json produced by the completed independent verification.
# Do not point at the aborted unsuffixed reconstruction root.
export H02_VERIFY_JSON="$(find /home/zyc /tmp -type f -name 'VERIFY.json' 2>/dev/null | grep -E 'H02_RECONSTRUCTED|h02_reconstructed' | head -n1)"
test -n "$H02_VERIFY_JSON" && test -f "$H02_VERIFY_JSON"

echo "VERIFY=$H02_VERIFY_JSON"

bash run_h02_reconstructed_postbank_preoutcome.sh
```

Expected final line:

`H02_RECONSTRUCTED_POSTBANK_PREOUTCOME=PASS`

The default output root is:

`/home/zyc/H02_RECONSTRUCTED_CHALLENGE_V1_PREOUTCOME_20260827`

It should contain at least:

- `H02_RECONSTRUCTED_ANALYSIS_MANIFEST.csv`
- `H02_RECONSTRUCTED_ANALYSIS_CONTRACT.json`
- `tensors/MANIFEST.json`
- `tensors/h02_ctx_*.npz` with both `first_hit[201,8,D]` and `hit_frequency[201,8,D]`
- `H02_TRANSPORT_RESOLUTION_AUDIT.json`
- `H02_EVENT_SUPPORT_DISCOVERY.json`
- `SHA256SUMS.txt`

## If historical event support is found

Before reading any event row values, freeze its schema:

```bash
python3 freeze_h02_event_support_schema.py \
  /home/zyc/H02_RECONSTRUCTED_CHALLENGE_V1_PREOUTCOME_20260827/H02_EVENT_SUPPORT_DISCOVERY.json \
  --out /home/zyc/H02_RECONSTRUCTED_CHALLENGE_V1_PREOUTCOME_20260827/H02_EVENT_SCHEMA_FREEZE.json
```

If this reports `AMBIGUOUS_EVENT_SCHEMA`, do not choose a file using outcome values. Return the discovery product for protocol resolution.

If it succeeds, the next materialization can map actual event positions to `query_cell_index` and obtain both:

`tau[s,m,e]` from `first_hit`, and

`p[s,m,e]` from exact CTT `hit_frequency`.

That is enough to compute observation-conditioned source resolution and Bernoulli observation adequacy without another forward simulation.

## If no event support survives

Do not replace actual observations with full 631-cell support. Full-field structure is model-side evidence only.

Use the existing deterministic PMFS actual-event response path (`rawProbabilities[source][replica][event]`) in a shadow replay. This is the fallback, not the first choice.

## What to return

Package the entire post-bank output directory plus, if created, `H02_EVENT_SCHEMA_FREEZE.json`.

Do not generate source-truth margin, bridge outcome, localization error, or new House/seed-specific tuning in this stage.
