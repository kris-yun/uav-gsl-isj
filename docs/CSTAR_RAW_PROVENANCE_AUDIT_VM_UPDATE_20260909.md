# CSTAR raw-realization provenance VM audit update (2026-09-09)

## Result

The manifest was audited on the original VM checkout, where its absolute
evidence paths are valid:

```text
checkout: /home/zyc/CSTAR_RAW_PROVENANCE_20260906
manifest: evidence/cstar_raw_provenance_20260906/CSTAR_RAW_REALIZATION_PROVENANCE_V1.json
verdict: CSTAR_RAW_REALIZATION_PROVENANCE=PASS
entry_count: 12
entry_provenance_pass_count: 12
qualified_m1_transport_pair_count: 6
qualified_m1_general_nuisance_pair_count: 0
exact_source_group_count: 6
qualified_exact_source_group_count: 6
each_house_source_diverse: true
each_house_all_groups_qualified: true
qualified_m2_route_case_count: 0
m2_status: NOT_YET_ROUTE_CONTROLLED
```

The copied, immutable audit result is:

`evidence/cstar_raw_provenance_20260906/CSTAR_RAW_REALIZATION_PROVENANCE_AUDIT_VM_20260909.json`

SHA-256:

`e3c5ce945d0b1b0fb899a65bc0931b09488635bca54fe8d16534d27becf76eb1`

## Interpretation

This is a data/provenance qualification PASS, not an M1 or M2 effectiveness
PASS.  It establishes that the frozen 12-realization set contains six
strictly source-matched, transport-only pairs and that all three Houses have
source-diverse qualified groups.  The next permitted step is to freeze route
definitions without reading gas outcomes and then perform the sensor-
consistent attribution replay.  M2 remains explicitly unqualified until that
route-control step is independently audited.

The earlier local failure was only a portability error: the auditor resolved
the manifest's VM-absolute paths on Windows and therefore reported a missing
file.  No manifest, raw realization, map, or wind evidence was changed.
