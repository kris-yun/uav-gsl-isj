import csv,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2];e=root/'evidence/p3t_d0_gaussian_support_20261001';r=json.loads((e/'evaluation1/P3T_D0_RESULT.json').read_text())
for name in ['P3T_D0_RESULT.json','P3T_D0_CASES.tsv','P3T_D0_CANDIDATES.tsv']:(e/name).write_bytes((e/'evaluation1'/name).read_bytes())
lines=['# P3T-D0 final decision','',r['decision'],'','P0: PASS, commit a623e998. Pre-scoring driver: 03a930a2. Parameters and thresholds were not tuned.','',
'## Four-arm results','',
'| Case | Arm | Truth log-score | Midrank | Pessimistic rank | Wrong-leaf ties | Margin | Entropy (nats) |',
'|---|---|---:|---:|---:|---:|---:|---:|']
for c in r['cases']:
 for a in ['P2','P3','G2','G3']:
  m=c['arms'][a];lines.append(f"| {c['case']} | {a} | {m['truth_log_score']:.9f} | {m['truth_midrank']:g} | {m['truth_pessimistic_rank']} | {m['truth_ties']} | {m['source_margin']:.9f} | {m['entropy_nats']:.9f} |")
lines+=['','## Frozen gate results','', 'Gate A FAIL: truth score increased 0/4; continuous concentration at confident observation cells 0/4; ties reduced 3/4; rank improved 3/4, worsened 1/4; median rank gain 1.25 (<10); margin improved 0/4. Truth positive support is mandatory; rank movement cannot rescue this gate.', '',
'Gate B FAIL (descriptive because A already stopped): positive margins 2/4; median G3−G2 margin −0.2820986563; median ranks 101.5 vs 105.75; worsening 1/4; each House has one positive margin case. No D1 authorization.', '',
'## Physical provenance and independent verification','',
'Historical mass=6.440736978853164e-06 mol/filament; air density=4.0894632701667424e-05 mol/cm³; sigma0=10 cm; gamma=15 cm²/s; sigma(age)=sqrt(100+15*age) cm; detector=0.1 ppm. Verified against original launches, actual compressed legacy iteration headers, legacy growth code and frozen Native threshold code/runtime parameters. Historical Gaden-RT operator includes a strict 3sigma cutoff and occupancy line-of-sight. G2/G3 use identical constants. D0 >= vs historical > has no equality effect with float32 concentration and float64 threshold 0.1.', '',
'All 972 center banks reproduce R1 point maps and eight scores tables byte-for-byte. Frozen reference libraries/source unchanged. Independent SciPy normalized Gaussian check: maximum relative error 1.8313e-7 over 20 probes. Brute per-query checks on 24 source-blind probe/candidate combinations verified mean/max concentration and exact hit probability. All 3,904 output files repeat identically; all 27 evaluation files repeat identically. Independent recomputation verified all 1,944 four-arm candidate log-scores, ranks, margins and area-preserving posteriors.', '',
'Post-result truth geometric audit independently confirms zero physical support. All confident query points are in fine 3D free space. G3 had 3 (H01 each seed) / 1463 (H02 each seed) query-center pairs inside 3sigma, but none passed historical line-of-sight. H01 G2 had zero pairs inside cutoff; H02 G2 had 15 but none passed line-of-sight. No cutoff/LOS modification is authorized. Gaussian maps have nonzero support elsewhere, so zero truth evidence is not a globally empty-map artifact.', '',
'## Cost and data retention','',
'Only on-demand concentration at frozen coarse PMFS cell centers, sensor z=0.3 m, was queried. No dense volume allocated. Equivalent float32 volume per timestep: H01 1,309,176 bytes; H02 1,027,208 bytes (200 frames would be 261,835,200 / 205,441,600 bytes). Scientific two-pass total 134.10 s; first-pass per-arm costs below.', '',
'| Case | G2 seconds | G3 seconds | G2 peak KiB | G3 peak KiB |', '|---|---:|---:|---:|---:|']
for c in r['cases']:
 x,y=c['arms']['G2'],c['arms']['G3'];lines.append(f"| {c['case']} | {x['runtime_wall_seconds']:.3f} | {y['runtime_wall_seconds']:.3f} | {x['peak_memory_kib']} | {y['peak_memory_kib']} |")
lines+=['', '972 trajectory files: 1,856,043,320 bytes uncompressed, preserved in VM shared output and host archive C:\\GADEN_P3T_D0_ARCHIVE\\20261001\\P3T_D0_CENTERS_20261001.tar.zst (913,053,466 bytes, SHA256 13948d43b4a88b68ea9161292a062ed2bec59a6461ed7101d87bd65ed962064c). VM/Windows hashes match. No raw/history data or protected ROS directories deleted. Review retains eight truth trajectories and both occupancy files; full bank is separate from compact review.', '',
'## Interpretation and STOP','',
'The frozen state0, 200-step R1 center banks plus the historical physical Gaussian operator did not restore true-source support. D0 rejects this proposed rescue of P3T; it does not establish that 3D has no information, identify the sole cause of failure, or authorize parameter tuning. Static state0, short template horizon, known source height, coarse-cell query and Native propagated confidence remain scope limits. R1 release count is unchanged (five per 0.2s), rather than the original variable 7/s emission. Historical sensor dynamic filtering/stop averaging is baked into measured maps, not reproduced on simulated Gaussian instantaneous queries. No main innovation or calibrated likelihood claim.', '',
'New GADEN=0; training=0; H03/confirmation opened=0; closed loop=0. Completed independent audit; STOP.']
(e/'P3T_D0_DECISION.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(e/'RUN_PROVENANCE.md').write_text('''# Run provenance

Branch research/p3t-d0-gaussian-control-20261001 from 4612ea8c4427b531efb0abd28f9f7a2e0a977548. Isolated worktree. P0 commit a623e998 pushed before Gaussian execution. Driver commit 03a930a2 pushed before execution. Gaussian binary/source/protected library hashes in GAUSSIAN_BUILD_AUDIT.json. No live ROS or simulator started.

VM: zyc@192.168.111.128. Inputs /mnt/hgfs/workspace/PMFS3D_R1_AUDIT_20261001/replay_inputs. Native reference libraries reused read-only. Export centers /mnt/hgfs/workspace/P3T_D0_CENTERS_20261001. Gaussian outputs /mnt/hgfs/workspace/P3T_D0_GAUSSIAN_OUTPUT_20261001. Run drivers and isolated compile helper retained in repository. Source and binary arrays little-endian. Trajectory frame: uint32 count, count records of float32 x/y/z + float64 age, 200 frames, no padding. Center ages advance with unchanged float32 transport timestep; no target-dependent path.

Full scientific scoring run twice from same frozen centers. All files byte-identical; timing metadata separate. evaluation1/evaluation2 use respective repeat banks. All input/control maps and scores retained for recomputation. Independent query audit is source-blind; truth geometry audit is explicitly post-result, not parameter selection.

Original R1 outputs retained. Source hypotheses are adaptive leaves, 123/121/123/119, not a new full 3D source grid. Posterior normalized over original free cells to preserve leaf-area prior. Do not relabel this four-case development gate as full source-map confirmation or mutual-information estimation.

No new GADEN; no new seed; no training; no closed loop; no H03 or confirmation access. ROS src/build/install unchanged. STOP after decision.
''',encoding='utf-8')
