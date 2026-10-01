# P3T-D0 final decision

P3T_D0_NO_POSITIVE_TRUTH_SUPPORT_STOP

P0: PASS, commit a623e998. Pre-scoring driver: 03a930a2. Parameters and thresholds were not tuned.

## Four-arm results

| Case | Arm | Truth log-score | Midrank | Pessimistic rank | Wrong-leaf ties | Margin | Entropy (nats) |
|---|---|---:|---:|---:|---:|---:|---:|
| House01_seed0_off_off | P2 | -170.432808106 | 75 | 91 | 32 | -139.221636573 | 2.326378813 |
| House01_seed0_off_off | P3 | -170.432808106 | 100 | 122 | 44 | -112.968693502 | 1.209086633 |
| House01_seed0_off_off | G2 | -170.432808106 | 75 | 91 | 32 | -137.736179620 | 2.911569940 |
| House01_seed0_off_off | G3 | -170.432808106 | 77.5 | 99 | 43 | -135.568921032 | 1.874111356 |
| House01_seed1_off_off | P2 | -160.569339637 | 102 | 118 | 32 | -129.571022158 | 1.029963467 |
| House01_seed1_off_off | P3 | -160.569339637 | 100.5 | 120 | 39 | -125.581726610 | 2.343236492 |
| House01_seed1_off_off | G2 | -160.569339637 | 105 | 121 | 32 | -119.002319700 | 1.208110933 |
| House01_seed1_off_off | G3 | -160.569339637 | 99.5 | 119 | 39 | -126.140947034 | 1.896065398 |
| House02_seed0_off_off | P2 | -259.439970254 | 104 | 117 | 26 | -217.212105517 | 0.000000483 |
| House02_seed0_off_off | P3 | -259.439970254 | 105 | 119 | 28 | -175.638079234 | 1.480441719 |
| House02_seed0_off_off | G2 | -259.439970254 | 106.5 | 117 | 21 | -219.772337014 | 0.005495632 |
| House02_seed0_off_off | G3 | -259.439970254 | 103.5 | 116 | 25 | -215.344901772 | 0.675106189 |
| House02_seed1_off_off | P2 | -257.803160762 | 107.5 | 119 | 23 | -219.037398648 | 0.554357251 |
| House02_seed1_off_off | P3 | -257.803160762 | 105 | 119 | 28 | -185.478706918 | 0.541424565 |
| House02_seed1_off_off | G2 | -257.803160762 | 108.5 | 119 | 21 | -213.858153494 | 1.344821225 |
| House02_seed1_off_off | G3 | -257.803160762 | 107.5 | 119 | 23 | -216.589609394 | 1.661971738 |

## Frozen gate results

Gate A FAIL: truth score increased 0/4; continuous concentration at confident observation cells 0/4; ties reduced 3/4; rank improved 3/4, worsened 1/4; median rank gain 1.25 (<10); margin improved 0/4. Truth positive support is mandatory; rank movement cannot rescue this gate.

Gate B FAIL (descriptive because A already stopped): positive margins 2/4; median G3−G2 margin −0.2820986563; median ranks 101.5 vs 105.75; worsening 1/4; each House has one positive margin case. No D1 authorization.

## Physical provenance and independent verification

Historical mass=6.440736978853164e-06 mol/filament; air density=4.0894632701667424e-05 mol/cm³; sigma0=10 cm; gamma=15 cm²/s; sigma(age)=sqrt(100+15*age) cm; detector=0.1 ppm. Verified against original launches, actual compressed legacy iteration headers, legacy growth code and frozen Native threshold code/runtime parameters. Historical Gaden-RT operator includes a strict 3sigma cutoff and occupancy line-of-sight. G2/G3 use identical constants. D0 >= vs historical > has no equality effect with float32 concentration and float64 threshold 0.1.

All 972 center banks reproduce R1 point maps and eight scores tables byte-for-byte. Frozen reference libraries/source unchanged. Independent SciPy normalized Gaussian check: maximum relative error 1.8313e-7 over 20 probes. Brute per-query checks on 24 source-blind probe/candidate combinations verified mean/max concentration and exact hit probability. All 3,904 output files repeat identically; all 27 evaluation files repeat identically. Independent recomputation verified all 1,944 four-arm candidate log-scores, ranks, margins and area-preserving posteriors.

Post-result truth geometric audit independently confirms zero physical support. All confident query points are in fine 3D free space. G3 had 3 (H01 each seed) / 1463 (H02 each seed) query-center pairs inside 3sigma, but none passed historical line-of-sight. H01 G2 had zero pairs inside cutoff; H02 G2 had 15 but none passed line-of-sight. No cutoff/LOS modification is authorized. Gaussian maps have nonzero support elsewhere, so zero truth evidence is not a globally empty-map artifact.

## Cost and data retention

Only on-demand concentration at frozen coarse PMFS cell centers, sensor z=0.3 m, was queried. No dense volume allocated. Equivalent float32 volume per timestep: H01 1,309,176 bytes; H02 1,027,208 bytes (200 frames would be 261,835,200 / 205,441,600 bytes). Scientific two-pass total 134.10 s; first-pass per-arm costs below.

| Case | G2 seconds | G3 seconds | G2 peak KiB | G3 peak KiB |
|---|---:|---:|---:|---:|
| House01_seed0_off_off | 10.724 | 4.685 | 61772 | 62024 |
| House01_seed1_off_off | 10.605 | 4.828 | 61900 | 61924 |
| House02_seed0_off_off | 11.552 | 6.931 | 61796 | 61860 |
| House02_seed1_off_off | 11.350 | 6.519 | 61976 | 61580 |

972 trajectory files: 1,856,043,320 bytes uncompressed, preserved in VM shared output and host archive C:\GADEN_P3T_D0_ARCHIVE\20261001\P3T_D0_CENTERS_20261001.tar.zst (913,053,466 bytes, SHA256 13948d43b4a88b68ea9161292a062ed2bec59a6461ed7101d87bd65ed962064c). VM/Windows hashes match. No raw/history data or protected ROS directories deleted. Review retains eight truth trajectories and both occupancy files; full bank is separate from compact review.

## Interpretation and STOP

The frozen state0, 200-step R1 center banks plus the historical physical Gaussian operator did not restore true-source support. D0 rejects this proposed rescue of P3T; it does not establish that 3D has no information, identify the sole cause of failure, or authorize parameter tuning. Static state0, short template horizon, known source height, coarse-cell query and Native propagated confidence remain scope limits. R1 release count is unchanged (five per 0.2s), rather than the original variable 7/s emission. Historical sensor dynamic filtering/stop averaging is baked into measured maps, not reproduced on simulated Gaussian instantaneous queries. No main innovation or calibrated likelihood claim.

New GADEN=0; training=0; H03/confirmation opened=0; closed loop=0. Completed independent audit; STOP.
