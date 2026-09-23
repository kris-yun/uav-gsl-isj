# M6 G1-B full compact bank — completion evidence

Date: 2026-09-23  
Protocol: `G1_B_COMPACT_SAMPLER_PROTOCOL_20260923.md`  
Launcher commits: `c888761`, `9657148`, `e0fca11`  
Status: **G1-B BANK / MANIFEST PASS; STOP BEFORE G1-C**

## Authoritative bank

The authoritative bank is the detached-run output copied into
`G1B_FULL_RAW_20260923/`. The remote source was
`/mnt/hgfs/workspace/M6_G1_STAGE1_PILOT_20260923/full_final`.
The earlier `/mnt/hgfs/workspace/M6_G1_STAGE1_PILOT_20260923/full` is retained as
failed-run residue and is not included in this bank: an interrupted foreground
SSH run and a concurrent rerun left it incomplete. No files in that residue
were used below, and it was not overwritten after the race was identified.

The corrected manifest was generated after all 24 runs finished; it uses the
source/seed directory depth (`mindepth=3,maxdepth=3`) and was checked with
`sha256sum -c` for all 24 case manifests.

## Coverage and fixed inputs

- 12 pre-registered sources: 8 train, 2 validation, 2 test.
- Two process-level plume seeds per source: `2026092311`, `2026092312`.
- 24/24 `metadata.json` files and 24/24 per-case `SHA256SUMS.txt` files.
- Every case: 250 primary samples, 631 free tokens, source z `0.20`, sensor z
  `0.30`, strict threshold `C>0.1`; primary `hit_samples_u8.bin` size is
  157,750 bytes and each float32 map is 2,524 bytes.
- Input hashes in `G1B_FULL_RAW_20260923/MANIFEST_INPUT_HASHES.txt`:
  - corrected metadata path list:
    `6df18869005dee5736176b98ff19a8977ff4eb87aa7292068b217838296f2c77`;
  - geometry grid:
    `f30c7de2ea892120b70411edb7187f2769246896152f9bb9b8181e15f749a397`;
  - source table:
    `d103e93dc756dd9edbab4d1af4b5a58566826237e07de38d3fea55a7dfc1a639`.
- Seeded binary/source provenance remains the G1-A audit:
  filament simulator `4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1`,
  `libgaden.so` `aca55af4e39831f97c1480bb31c014eb06294ced8a71329c3aa216e6cf7991a8`,
  seed-only source patch `50f04ec609157189d3f9fed72a87e6729c0b66691fcaee8da6864d9194575278`.

## Runtime and seed checks

All 24 sampler processes returned `G1B_SAMPLER_OK`; recorded wall time was
approximately 1–2 s per case and maximum resident set size was 73,556–73,688
kB. A separate train1 same-seed replay is preserved in
`G1B_PROOF_RAW_20260923/` and was byte-identical, while the second seed
diverged. The full-bank verification also compared each source's two primary
hit-frequency maps and found seed divergence for all 12 sources.

The bank contains only compact sensor-plane samples, fields, metadata, logs and
hash manifests. No PMFS model training, truth-source rank, candidate tuning,
closed-loop replay, or unknown-House transfer evaluation was performed.

## Gate decision

`G1-B = PASS` for frozen data generation, compact field integrity, and
independent seed control. This evidence ends the authorized data-generation
stage. Per the hard gate, stop here; do not start G1-C training or G1-D source
rank until the parent explicitly launches the next stage with the bank frozen.
