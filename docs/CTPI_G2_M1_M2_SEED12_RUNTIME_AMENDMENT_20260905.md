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

## R2 zero-weight variance defect

R2 passed the identity preflight and produced valid A0 and F00 terminal
artifacts.  H01/F01 then activated M2 and stopped with
`CPIR_PLANNER_VARIANCE_INVALID` before its 240 s horizon.  The M2 posterior
contained legitimate exact-zero probabilities.  The native PMFS weighted
variance helper divided by zero when its first hypothesis had zero posterior
weight, and cells with no posterior mass also divided a zero accumulator by a
zero total weight.

R2 is therefore runtime-invalid and cannot enter the scientific comparison.
The definition-level repair skips zero-weight observations and assigns zero
posterior-weighted predictive variance when a cell's total posterior weight is
zero.  This introduces no floor, threshold, or tunable value.  The runtime
logs the number of zero-mass cells.  Because the algorithm binary changes, the
valid run must restart all A0/F00/F01 arms under a fresh R3 root.
