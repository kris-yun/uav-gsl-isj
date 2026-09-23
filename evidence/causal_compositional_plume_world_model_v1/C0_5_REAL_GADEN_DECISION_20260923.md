# C0.5 REAL-GADEN DECISION — 2026-09-23

Branch: `research/causal-compositional-plume-world-model-v1`  
Status: **NO-GO AS MAIN — HOUSE02 FIELD SIGNAL DOES NOT SUPPORT THE M4-v2 REUSABLE TRANSPORT MECHANISM**

This report records the evidence actually generated and preserves the stricter
unknown-House boundary. It does not promote the House02 bank to a main-line
M4 result.

## Required answers

1. **House:** House02 was used for the C0.5 physical precondition and compact
   eight-realization bank. Occupancy dimensions are 83×119×26, cell size
   0.1 m, occupancy SHA-256
   `9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d`.

2. **Sources:**
   - S1 = `(-2.242730141, -2.200880051, 0.20)`, GADEN cell `(31,52,12)`,
     free, nearest nonfree distance 0.50 m.
   - S2 = `(-4.342730045, 2.899120331, 0.20)`, GADEN cell `(10,103,12)`,
     free, nearest nonfree distance 0.80 m.
   - Source separation is 5.515433 m. Coordinates were frozen before plume
     outputs were inspected.

3. **Winds:** W1 is the canonical `3,5-1_fast` field and W2 is the canonical
   `3,5-1_slow` field under the same House02 occupancy. They are not rotated
   or numerically scaled. Across 11 iterations, one initial field is identical
   and iterations 1–10 differ; 62.2115% of components differ by more than
   `1e-12`, with maximum component difference 1.032032 m/s. The wind-slice
   artifacts use predeclared iteration 1, whose hashes are
   `2fa27ec7...9846` (W1) and `54d7bc33...dda8` (W2).

4. **Plume seeds:** The bank uses seedA `2026092301` and seedB `2026092302`.
   All four same-source/same-wind pairs have 566 raw frames; 565 frames are
   byte-distinct after the common initial frame. Official GADEN spatial slices
   are non-identical with mean absolute differences from 0.0601 to 0.0980.
   The raw and spatial replication audits both pass.

5. **Generation cost:** The one-source benchmark completed at 30/120/300 s.
   Wall times were 0.89/0.88/1.89 s and the 300 s output had 566 iteration
   files and 42,961,851 bytes. The bank uses the 300 s contract. This is an
   infrastructure cost result, not a source-rank result.

6. **Held-out field prediction:** Evaluated as a bounded House02 local
   diagnostic after four checkpoints were frozen. On S2×W2 A/B, operator
   `log1p` field MSE was 0.135064/0.113821 for training seed 1729 and
   0.141936/0.120340 for seed 2718. Matched monolithic errors were
   0.442162/0.431375 and 0.310335/0.297871. This is a consistent local
   field signal, not unknown-House evidence.

7. **Truth-source candidate rank:** A source-blind, 30-probe, two-candidate
   offline diagnostic ranked true S2 first for **both** models on both
   training seeds and both plume seeds. There is no rank gain. This is not
   the charter's Native PMFS-compatible source-rank replay, which remains
   unevaluated. No G3 target-House candidate replay exists.

8. **Nulls:** The source swap changes the sparse score in the expected
   direction for both models. The M4 transport swap has tiny paired error
   changes (`+0.000353`, `+0.000112`, `+0.000051`, `-0.000027`); one reverses.
   Source-label and wind-label shuffle retraining were not run after the
   rank-tie stop rule. No full null battery is claimed.

9. **M4 decision:** **NO-GO AS MAIN for M4-v2.** The original C0.5 evaluation
   stopped at HOLD because source-rank superiority and a reliable transport
   effect were not established. A subsequent frozen, kill-only transport-response
   audit used the same checkpoints without retraining and rejected the reusable
   transport interpretation: the operator's W1→W2 field-change amplitude was
   only 4.31%–5.25% of the paired real-GADEN wind intervention, while its
   source-intervention amplitude was 80.60%–85.83% of the paired real-GADEN
   source intervention. The predicted wind/source response ratio was only
   about 5.35%–6.11% of the true ratio. M4-v2 therefore does not proceed to G3.

10. **Closed loop:** **Not justified.** Do not modify PMFS movement, source
    updates, stopping logic, or ROS/live-loop code.

## Evidence locations

- Local compact bank and hashes:
  `evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank/`
- Raw VM bank (large files intentionally not copied into Git):
  `/home/zyc/c0_5_real_gaden_bank_20260923`
- G3 audit:
  [`G3_UNKNOWN_HOUSE_DATA_AUDIT_20260923.md`](G3_UNKNOWN_HOUSE_DATA_AUDIT_20260923.md)
- Frozen local comparison and exact scores:
  [`C0_5_LOCAL_COMPARISON_RESULT_20260923.md`](C0_5_LOCAL_COMPARISON_RESULT_20260923.md)
- Hard boundary:
  [`G3_UNKNOWN_HOUSE_TRANSFER_HARD_GATE_20260923.md`](G3_UNKNOWN_HOUSE_TRANSFER_HARD_GATE_20260923.md)
- Post-freeze M4-v2 transport-response kill audit:
  [`M4_V2_FROZEN_TRANSPORT_RESPONSE_AUDIT_20260923.md`](M4_V2_FROZEN_TRANSPORT_RESPONSE_AUDIT_20260923.md)

## Post-freeze boundary

The transport-response audit is **kill-only** because S2×W2 had already been
opened. It may reject M4-v2 but cannot convert the same House02 evidence into
ADVANCE. No dense candidate-ranking, G3 generation, ROS/PMFS integration, or
closed-loop run is authorized for this frozen v2.

No claim of M4 ADVANCE or scientific PASS is made.
