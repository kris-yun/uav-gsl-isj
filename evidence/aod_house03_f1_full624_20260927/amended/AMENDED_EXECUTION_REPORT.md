# AOD full624 F1 after native-state sampling amendment

Decision: `AOD_F1_FULL624_CONFIRMED_STRESS_NONINFERIOR`. Historical `AOD_F1_HOLD_TIMEBASE` remains unchanged.

## Provenance

Branch: research/aod-house03-f1-full624-20260927
Original pre-target bank freeze: 10dd251eba10b14bca3e0334dbac6ae8af93911a
Native-state amendment commit: 5d082e1832f47e83452d31a03779f241b25d01c6
Full96 pre-scoring data freeze: 99cd87e9
Candidate bank: 54912 original forwards, 624 candidates, all reused; all 219648 raw product files rehashed before new targets.
Targets: 96 complete; existing first reused and exactly 95 original-seed runs added.
Sampling IDs: 91,174,265,365,465,565,665,765,865,965; native state tuples preserved; no frame relabeling, per-run selection or dynamics change. All986 clock/step/wind records matched for every run.
All96 full cubes retained, all960 frame loads checked; no absent-frame zero fill.
Original B2 and evaluator SHA256 remain unchanged.

## Frozen primary gates

Nominal Delta_acc: 0.052083333333333336; CI95: [0.036458333333333336, 0.07291666666666667].
State0 Delta_acc: 0.046875; CI95: [0.03125, 0.0625].
10000 PCG64 bootstrap draws, seed2026092703, fixed source identities, within-source realization resampling, both paths/arms/conditions grouped.

## Descriptive results

|condition|arm|mean rank|unique Top1|Top3|MAP error m|
|---|---|---:|---:|---:|---:|
|nominal|u|115.45572916666667|0.052083333333333336|0.16666666666666666|3.4375182146279655|
|nominal|rawu|116.4296875|0.10416666666666667|0.21875|3.5323864650866508|
|state0_stress|u|77.16927083333333|0.041666666666666664|0.11979166666666667|3.380978499279415|
|state0_stress|rawu|94.16927083333333|0.08854166666666667|0.16145833333333334|3.5472979431024902|

Nominal rescued/harmed path observations: 11/1; improved/harmed sources: 3/1.
Stress rescued/harmed path observations: 17/8; improved/harmed sources: 3/1.
Zero-valued path observations: 25/192; scored as ties, never removed.
Two paths are not treated as independent plumes.

## Integrity, storage and scope

Complete scoring/evaluation repeated; every scientific output is byte-identical. Runtime diagnostics are recorded separately.
96 raw C-drive ZIP archives verified, total 3961327797 bytes. All original raw directories, first-run evidence, candidate bank and original HOLD archive remain.
Infrastructure-only additions: 25ac198f (HGFS occupancy copy because symlinks unsupported), 70fbfe75 (copy-only verified raw archives), ba0523ed (frame-load and repeated-output verification). Native-state sampling amendment is a scientific acquisition-contract change, not an infrastructure-only patch.

This gate tests the preregistered uniqueTop1 difference for fixed12 sources and frozen624 support. Absolute localization accuracy remains low, and mean rank/MAP error did not improve; the PASS does not establish deployable localization or a general superiority claim.

No new method, extra seed, GADEN run beyond95, new forward, network, closed loop or post-result tuning was started. STOP after packaging.
