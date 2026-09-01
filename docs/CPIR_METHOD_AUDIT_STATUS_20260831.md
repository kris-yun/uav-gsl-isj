# CPIR method and bank audit status (2026-08-31)

## Scope

This is a read-only engineering/science audit of the frozen CPIR M1-only
implementation at commit `a82440d`.  It does not revive the retired M2,
change a score, or authorize a closed-loop run.

## Current evidence

- The remote full-grid materializer has finished all three Houses:
  H01 `1680/1680`, H02 `1608/1608`, H03 `1648/1648`.
- Each House has a `bank_summary.json` with
  `contract=CPIR_FULLGRID_LOOKUP_V1` and
  `verdict=CPIR_FULLGRID_LOOKUP_PASS`.
- The cell sets in the materializer inputs match the geometry-only region
  support manifest exactly by House (H01 626, H02 631, H03 626 XY cells).
  `source_probability` is not read by the materializer; it is provenance in
  the input file, not a posterior factor in the generated bank.
- An independent per-file header/size/SHA verifier has completed.  All three
  reports are `CPIR_LOOKUP_INTEGRITY_PASS`; retained copies are under
  `D:\ZYC\A-gas\_deliveries\CPIR_FULLGRID_BANK_INTEGRITY_20260831_R1` and
  authoritative VM copies are `/tmp/cpir_integrity_r2_H01.json` through
  `H03.json`.

  The verified reports record H01 1,680 files/6,314,306,880 bytes,
  H02 1,608 files/6,091,965,888 bytes, and H03 1,648
  files/6,194,034,368 bytes.  Their file-manifest SHA-256 values are,
  respectively, `bfc56d511d030f326e5658225fd4665c3216728fe6f3a810be4f912a70e0c667`,
  `4562d6df11621e611332e93d32f42635cb40a211f048563ddb5c1eb9f3371d75`, and
  `2036032ece0e50e1a3e0e2b1b82bee25eea91ae14615957b0420856c32eebd2b`.

## Scientific audit

The existing 30-pair result is a fixed-trajectory shadow, not closed loop:

- 23/30 wins, pooled mean improvement 48.27%.
- H01 8/10 (45.46%), H02 5/10 (9.82%), H03 10/10 (67.11%).
- The seven losses are H01 seeds 1/2 and H02 seeds 5--9.

The result should be named `CPIR-base` when discussing implementation
attribution: the C++ path includes a persistent candidate sensor state
(`tau=1.2 s` and two-sample delay) and then collapses stop identity to a
count-only score.  It is therefore not evidence for an independent M2 or M3
increment.

The retired exact-first-passage/coherent-K/dynamic-K M2 is permanently
`CTT_DYNAMIC_TRANSPORT_M2_PREMISE_NO_GO`.  The reviewed worktree now implements
explicit A1/A2/A3 modes: only A3 uses the proposed stop-resolved M3, while A1,
A2, and the historical `cpir_m1` alias retain the count-only comparator.
Historical nested M2/M3 numbers remain diagnostic only and are not clean
incremental evidence.

## Blocking checks before any closed loop

1. The reviewed launch now defaults to `flight_height=0.3`,
   `maxUpdatesPerStop=8`, and `measurement_block_samples=10`, and rejects any
   CPIR/A0 arm that violates the 80-sample, zero-settle, 0.2-s contract. The
   actual arm remains mandatory (`pfdi_mode=UNSET` fails closed).
2. Native PMFS hit/source updates execute before the CPIR replacement.  A
   smoke must prove that only the source channel is replaced and that no
   native posterior or hit-map side effect leaks into the CPIR score.
3. Each placement row jointly varies position/height and transport seed.  It
   must be documented as a joint nuisance atom, not as a pure transport-only
   member claim.
4. The carrier-to-free-cell mapping and observation/prediction member
   disjointness still require runtime parity evidence.

## Decision

The bank generation and independent integrity audit are complete, but the
formal method/closed-loop audit is **not complete**. The source now contains
the nested A1/A2/A3 formulas, the frozen KL/I-projection, exact free-cell
support checks, and launch-level tape guards. Bank-free formula self-tests and
an isolated VM Release build pass. No 9-pair/30-pair closed-loop result is
currently authorized by this file. The bank was not opened or regenerated
during this review, so runtime formula parity remains pending.
