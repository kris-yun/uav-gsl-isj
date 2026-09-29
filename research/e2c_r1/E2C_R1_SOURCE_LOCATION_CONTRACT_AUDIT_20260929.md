# E2C-R1 source-location contract audit

Status: **HOLD — do not execute the 144-run manifest.** This is a read-only
audit of the VM's original `GADEN_files/scenarios/House01..03` asset tree. No
concentration values, source-localization scores, or sealed E2C data were read.

## What the original scenario configures

Each House has four wind launch configurations. ROS1 and ROS2 launch defaults
agree exactly. The 12 existing gas-simulation directories encode the same
source coordinates and gas types as those defaults. There are **two distinct
configured source positions per House**, each paired with a fast and slow wind:

| House | Source xyz (m) | Gas type | Configured wind pair |
| --- | --- | --- | --- |
| House01 | `(-0.60, 1.95, 0.40)` | 13 | `1,3-2,4_fast/slow` |
| House01 | `(-0.40, -2.90, -0.30)` | 10 | `2,4-1_fast/slow` |
| House02 | `(0.00, -1.00, 0.20)` | 10 | `3,5-1_fast/slow` |
| House02 | `(1.00, -2.30, -0.10)` | 13 | `4,5-3_fast/slow` |
| House03 | `(-0.45, 1.90, -0.10)` | 10 | `1-2,5_fast/slow` |
| House03 | `(8.20, 5.00, -0.20)` | 10 | `5-3_fast/slow` |

Every one of the 12 source–wind directories contains 2,000 saved
`iteration_*` files and 11 `wind_iteration_*` files. These are saved time
records for one configured source–wind simulation, **not 2,000 independent
plume realizations**. The exact directory, launch-file SHA256, gas type and
record counts are in
`evidence/e2c_r1/source_contract_audit/ORIGINAL_CONFIGURED_SOURCE_CATALOG.tsv`.
The release does not assign a `pmfs_i_j` source ID to these configurations;
the configured identity is the launch wind name plus the coordinate/gas-type
triple.

The launch files express x/y/z as `source_location_*` arguments, and the
simulator also accepts runtime source coordinates. This proves technical
editability, not that arbitrary free cells belong to the released dataset's
source-location catalog. No larger explicit source catalog was found in the
three House scenario trees. The CAD outlet meshes are geometry assets; they
do not supply a source-coordinate catalog in the inspected launch and gas
configuration. Re-running at one of the six configured coordinates with a
new seed is technically possible with the existing wind assets, but would
still be a new realization, and exact replay of the historical run requires
its original RNG provenance. Combining a source with a different configured
wind family or moving its coordinate would create a new configuration.
The nested `House02/House02` and `House03/House03` copies were also inspected;
their gas-simulation directories repeat the same two source positions per
House and add no distinct configured source location.

## Effect on the frozen E2C panel

The exact xyz match check gives **0/24** frozen panel sources in the original
configured catalog: H01 0/8, H02 0/8, H03 0/8. This includes all 12 proposed
source-unseen confirmation cells. H01 and H03 original configured source
heights also differ from the E1/E2C `z=0.20 m` rule; one H02 source has the
same height but a different x/y coordinate. The comparison is preserved in
`evidence/e2c_r1/source_contract_audit/FROZEN_PANEL_VS_ORIGINAL_SOURCE_CATALOG.tsv`.

This also clarifies the existing E2 168-run benchmark: its source panel was
already an independently designed, geometrically valid **new simulator
source-configuration benchmark**, rather than a selection of source
locations preconfigured in the original House release. Its data and hashes
remain valid for that explicitly named benchmark. It cannot silently be
relabelled as an expansion confined to the original source catalog.

If future work requires only original configured source positions, there are
at most two distinct source identities per House in the inspected release.
That cannot meet the frozen eight-source-per-House, new-source confirmation
design. A redesigned benchmark must state separately whether it is using
those fixed released configurations or authorizing new simulator source
configurations. No source, seed, or run is selected here.

## Execution record correction

The later HOLD commit says that no simulation was attempted and no output
root was created. Before that HOLD arrived, an execute-only process invoked
the first manifest row, House01 `pmfs_13_18`, seed `2026290004`. The binary
exited with code 127 **before simulating** because `librclcpp.so` was not on
the background process's library path. The failed attempt created an empty
`realization` directory and a 233-byte loader error log. It produced **zero
`iteration_*` files, zero concentration cubes, and zero completed E2C runs**.
The acquisition process has exited. The incomplete attempt and original logs
remain on the VM; copies are in this audit evidence directory. No same-seed
retry was made after the HOLD.

The earlier local `3118fe36` finalizer correction changed only a stale
`len(seed_rows)==120` check to 144, before this source-contract HOLD. It did
not produce or analyze scientific data and gives no authority to resume.

**Decision:** `E2C_R1_HOLD_SOURCE_LOCATION_CONTRACT`. Stop acquisition and
algorithm work. Preserve the previous 144-row freeze and failed loader log as
history; do not run either under the original-dataset label.
