# Red:Vapor input-contract audit for TROQL/OQIC

Date: 2026-09-14

## Verdict

`RED_VAPOR_SOURCE_CONTRAST_CONTRACT_NO_GO`

Red:Vapor supplies strong same-source transport variation, but it does not supply
the positive control required for the present claim: two known source locations
in one fixed environment, each repeated under multiple transport members.

The public experiment table contains low/high-wind pairs for setups B, C, and D,
plus an additional low-wind replicate for setup C. The accompanying spatial-data
notebook states that setup D is the complete setup-C scale-model landscape rotated
45 degrees counter-clockwise. Thus C versus D changes the environment/attack angle
as a whole; it is not a source-position intervention in a fixed environment.

## Read boundary

Only repository documentation, the experiment overview, the header specification,
and file checksums were inspected. The checksum-verified `voxel_maps.pkl` was not
unpickled and no concentration outcome was scored. This prevents a dataset with
the wrong causal factor structure from becoming an informal tuning set.

## Provenance

- Repository: <https://github.com/DLR-KN/red-vapor>
- Repository commit: `a267df617df665a7d7bcb9c28c942a2ece0a751c`
- Dataset record: <https://zenodo.org/records/18299926>
- `overview_table.csv` SHA-256:
  `04a2400300d99b24a8d0a13380b0be26fc22508d36d2a586e516337932b34935`
- `voxel_maps.pkl` MD5 (matches the published record):
  `9a3ec10b1645ff2788ab8d292fb41dcf`
- `voxel_maps.pkl` SHA-256:
  `af35deefb90709798a891242568c522a7f9dfe9131d235bdc0d7541ef9ad8a12`

Red:Vapor remains useful for a later nuisance-only study, but it cannot establish
the different-source component of the TROQL/OQIC main-innovation premise.
