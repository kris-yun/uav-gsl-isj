# H0 decision

**`TS_P3T_H0_INVALID_STOP`**

P0 verified the exact historical archive and 61 selected input hashes, but could not recover the full-precision completed-measurement event stream for any of the four R1 cases. The requested `1e-10` terminal map reconstruction parity therefore cannot be established.

Following the frozen handoff, H0 stops before O40/Oupdate reconstruction and scientific scoring. No candidate rankings or truth evidence were recomputed. The historical P3T D0 STOP is unchanged.

This decision does not reject the temporal-closure hypothesis or establish a persistent world model. It establishes that this historical asset cannot support the preregistered exact replay. No replacement run or new simulator execution was performed.

The independent audit validates input hashes and the disabled logging paths. It explicitly marks map/scoring replication as not run; it does not manufacture a parity PASS.
