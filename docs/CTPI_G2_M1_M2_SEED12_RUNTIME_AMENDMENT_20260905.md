# CTPI G2 M1+M2 seed12 runtime amendment (2026-09-05)

The first launch root, `CTPI_G2_M12_SEED12_CROSSHOUSE_20260905_R1`, is
runtime-invalid.  Before any GSL goal was issued, the external
`vgr_bridge.result_contract.CANONICAL` registry rejected the new identity
`CTPI_G2_M1_M2`.  No R1 output may enter the scientific comparison.

The sole amendment is to create an isolated copy of `vgr_bridge` and add
`CTPI_G2_M1_M2` to its canonical identity registry with the existing PMFS
algorithm/type fields.  The persistent ROS workspace is not edited.  Every arm
must record the isolated contract and runner paths and SHA-256 hashes, and an
import preflight must prove that the benchmark runner resolves from that
overlay before ROS launch.

No algorithm formula, bank, seed, House configuration, horizon, cadence,
performance threshold, or preregistered decision rule changes.  The valid
rerun must use a fresh result root.
