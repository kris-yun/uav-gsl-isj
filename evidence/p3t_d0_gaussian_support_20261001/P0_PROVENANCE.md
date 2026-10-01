# P0 provenance

Decision: P3T_D0_P0_PROVENANCE_AND_TRAJECTORY_PASS.

Both original ROS1 House01 2,4-1_fast / House02 3,5-1_fast launch files set gas10, center10 ppm, sigma0=10 cm, gamma=15 cm²/s, 298 K, 1 atm. Eight actual legacy iteration headers uniquely agree on mass=6.440736978853164e-06 mol and air=4.0894632701667424e-05 mol/cm³. Stored sigma values agree with legacy analytical sigma=sqrt(sigma0²+gamma*age); current Gaden-RT Euler growth is NOT substituted. Stored mass avoids legacy pi approximation ambiguity.

Historical Gaussian query: isotropic normalized 3D Gaussian in centimeters, summed in ppm, strict radius<3sigma cutoff, occupancy line-of-sight. Physical growth uses known center ages from the unchanged R1 release/advance loop, not target fitting. Scipy Gaussian-density calculation independently checks twenty deterministic probes.

Threshold: frozen exact_b24 Algorithm.cpp defaults th_gas_present=0.1; all four retained resolved runtime files have no override. StopAndMeasureState uses strict >. D0 explicitly freezes >=; equality occurrences will be audited, never tuned.

972 center trajectories exported using exact original deterministic source draws, transport keys, float timestep and collision helpers. All 972 predicted point maps and eight score tables byte-match frozen R1. G2 embeds the 2D path at the frozen sensor plane; G3 retains original xyz. Reference libraries and source unchanged. Full bank stored on shared mount, hashes retained here.

Scope limits frozen BEFORE Gaussian evaluation: R1 emits five centers/0.2s (25/s), not the historical variable 7/s law. Preserve R1 center count and apply actual historical per-filament mass; do not rescale mass or change release rate. Historical VGR dynamic sensor filtering/stop aggregation remains baked into measured PMFS maps. This D0 tests instantaneous physical Gaussian support with the frozen threshold; it does NOT reproduce the complete historical sensor transfer function or prove point support was the sole mismatch. State0 CFD and old R1 hypotheses are development conditions. No new plume, live runtime, or probability-calibration claim.
