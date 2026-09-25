# CODEX TASK — SPX-G0 Source-Panel × Probe-Protocol Crossed Audit

Branch:
`research/source-probe-crossed-audit-20260925`

Authoritative charter:
`research/source_probe_crossed_audit_v0/SPX_G0_CHARTER_20260925.md`

Hard scope:
- 0 new plume;
- House02 `3,5-1_slow` only;
- use existing G1A 168×16 raw cubes and E2 H02-W0 6×16 raw cubes;
- do not read H01 DEV or House03;
- no new theory/model;
- no JTD rescue;
- no NPG rescue.

Stage A0:
1. resolve exact G1A and E2 raw cube manifests;
2. load exact P_G1A and P_E2 30-probe contracts;
3. freeze CENTRAL 84 pairs and OFFSTRIP 3 pairs;
4. cross-extract both probe protocols from all required cubes;
5. prove historical-cell reproduction:
   - CENTRAL×P_G1A reproduces G1A tensors;
   - OFFSTRIP×P_E2 reproduces E2 tensors;
6. if exact reproduction fails, return DATA_CONTRACT_STOP.

Stage G0:
1. run identical fourfold 12-ref/4-test two-source FULL/BP/MBD scoring for every pair×probe protocol;
2. compute pairwise margins, two-class NLL, Brier/accuracy diagnostics;
3. compute paired probe effects on the same raw realizations;
4. apply the frozen diagnostic-label rules exactly.

Required deliverables:
- `SPX_G0_A0_COMPATIBILITY.json`;
- `SPX_G0_RESULT.json`;
- cross-extraction tensor/hash manifest;
- exact historical reproduction report;
- CENTRAL pair×probe CSV;
- OFFSTRIP pair×probe CSV;
- paired probe-effect CSV;
- bootstrap outputs;
- independent recomputation JSON;
- code/input/output SHA256 manifests;
- final branch commit;
- review package path/bytes/SHA256.

Final label exactly one:
- `SPX_G0_SOURCE_REGIME_DOMINANT`
- `SPX_G0_PROBE_PROTOCOL_DOMINANT`
- `SPX_G0_SOURCE_PROBE_INTERACTION`
- `SPX_G0_DATA_CONTRACT_STOP`

Stop immediately after SPX-G0.

---

## Amendment A execution requirements

The charter's Amendment A is authoritative.

Before any scoring:

1. create `SPX_G0_ASSET_AUDIT.json`;
2. verify readable numeric raw cubes, exact probe contracts, actual wind arrays and occupancy arrays;
3. record bytes/SHA256/shape/dtype and asset usability;
4. do not infer missing assets from filenames or hashes;
5. if exact cross-extraction cannot be performed, return `SPX_G0_DATA_CONTRACT_STOP`.

Primary science is ONLY House02 / `3,5-1_slow` adjacent-pair discrimination under a uniform two-source conditional support.

Do not use H02 W2 distant-aliasing cases in the SPX-G0 primary decision.
Do not use 168-way vs 6-way posterior magnitudes as a causal comparison.

Historical tensor reproduction tolerance: <=1e-12 absolute where serialization permits.

Also output a deployment-context inventory distinguishing realistic inputs from simulator-oracle inputs.
