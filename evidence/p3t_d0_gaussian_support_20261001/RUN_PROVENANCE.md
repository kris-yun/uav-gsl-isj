# Run provenance

Branch research/p3t-d0-gaussian-control-20261001 from 4612ea8c4427b531efb0abd28f9f7a2e0a977548. Isolated worktree. P0 commit a623e998 pushed before Gaussian execution. Driver commit 03a930a2 pushed before execution. Gaussian binary/source/protected library hashes in GAUSSIAN_BUILD_AUDIT.json. No live ROS or simulator started.

VM: zyc@192.168.111.128. Inputs /mnt/hgfs/workspace/PMFS3D_R1_AUDIT_20261001/replay_inputs. Native reference libraries reused read-only. Export centers /mnt/hgfs/workspace/P3T_D0_CENTERS_20261001. Gaussian outputs /mnt/hgfs/workspace/P3T_D0_GAUSSIAN_OUTPUT_20261001. Run drivers and isolated compile helper retained in repository. Source and binary arrays little-endian. Trajectory frame: uint32 count, count records of float32 x/y/z + float64 age, 200 frames, no padding. Center ages advance with unchanged float32 transport timestep; no target-dependent path.

Full scientific scoring run twice from same frozen centers. All files byte-identical; timing metadata separate. evaluation1/evaluation2 use respective repeat banks. All input/control maps and scores retained for recomputation. Independent query audit is source-blind; truth geometry audit is explicitly post-result, not parameter selection.

Original R1 outputs retained. Source hypotheses are adaptive leaves, 123/121/123/119, not a new full 3D source grid. Posterior normalized over original free cells to preserve leaf-area prior. Do not relabel this four-case development gate as full source-map confirmation or mutual-information estimation.

No new GADEN; no new seed; no training; no closed loop; no H03 or confirmation access. ROS src/build/install unchanged. STOP after decision.
