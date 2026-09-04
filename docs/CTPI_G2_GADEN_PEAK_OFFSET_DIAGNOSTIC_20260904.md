# CTPI-G2 GADEN instantaneous peak-offset diagnostic

Date: 2026-09-04  
Status: `DIAGNOSTIC_ONLY_NOT_M3_GATE`

The diagnostic inspected the true carrier in each House across eight frozen
GADEN transport members and all 1,500 instantaneous snapshots per member:
36,000 snapshots total. Distances use the physical source placement recorded in
`PF_DEI_V3_REGION_PLACEMENT_V1`, not the carrier center.

| House | snapshots | peak inside true carrier | within 1 cell | within 2 cells | mean distance | median distance | p90 distance |
|---|---:|---:|---:|---:|---:|---:|---:|
| H01 | 12,000 | 25.62% | 25.62% | 89.55% | 0.939 m | 0.300 m | 0.949 m |
| H02 | 12,000 | 24.91% | 24.91% | 24.91% | 3.706 m | 1.530 m | 7.500 m |
| H03 | 12,000 | 53.28% | 19.17% | 97.51% | 0.325 m | 0.300 m | 0.424 m |

Member-level variability is large. The fraction inside the true carrier ranges
from 0.2% to 99.47% in H01, 0% to 100% in H02, and 1.53% to 99.07% in H03.
This rejects the universal claim that the instantaneous peak is always at the
source cell. It also rejects the opposite universal claim that the peak is
always displaced downstream: the behavior is transport-member and House
dependent.

The frozen world files do not contain a snapshot-aligned wind-state ledger.
Therefore signed along-wind offsets are explicitly `NOT_COMPUTED` rather than
being inferred from an average or assumed wind direction. This missing field
does not affect the distance/inside-carrier findings, but it prevents a complete
test of the specifically *downstream* displacement hypothesis.

Raw result:
`evidence/ctpi_g2_m3_20260904/CTPI_GADEN_PEAK_OFFSET_DIAGNOSTIC_V1_20260904.json`

Raw result SHA-256:
`4f33683515e45aa702d4151a4e0015ed2f31361c4da9c347037fad237eda1011`
