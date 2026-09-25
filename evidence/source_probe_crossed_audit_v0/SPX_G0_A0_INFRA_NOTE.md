# SPX-G0 A0 infrastructure correction before scoring

The first asset-audit invocation incorrectly compared the House02 occupancy
SHA256 string with the whole `occupancy_sha256` dictionary in the frozen E2
initial lock. It emitted a provisional `SPX_G0_DATA_CONTRACT_STOP` for that
implementation error. Direct SHA inspection showed that the numerical House02
occupancy file matched the locked `occupancy_sha256["House02"]` value exactly.

The lookup was corrected before any crossed extraction or FULL/BP/MBD score.
The corrected audit verified 2,688 CENTRAL raw cubes, 96 OFFSTRIP raw cubes,
both probe contracts, all 11 numeric wind arrays, and the numeric occupancy
grid. Cross-extraction then reproduced both historical cells with maximum
absolute error 0.0, including the OFFSTRIP tensor after its original float32
serialization. No simulation or scientific threshold changed.
