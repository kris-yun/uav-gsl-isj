# P3T-D0 review

Read P3T_D0_DECISION.md, P3T_D0_RESULT.json and INDEPENDENT_D0_AUDIT.json first. Decision STOP, no D1. Four-arm table is fully reported.

point_controls.tar.gz: all frozen R1 P2/P3 maps and scores. gaussian_outputs.tar.gz: all G2/G3 maps, continuous means/maxima/nonzero fractions, scores, diagnostics, repeat1/repeat2 and timing. P3T_D0_TRUTH_CENTER_AND_OCCUPANCY.tar.gz: eight true-leaf center trajectories and original two House occupancy grids. physical_provenance/provenance.tar.gz: frozen source/config/header copies. CENTER_SHA256.json and FULL_CENTER_ARCHIVE.json locate the separately retained 913 MB full bank. It is intentionally omitted from compact review.

All concentration values are ppm; coordinates meters; sigma centimeters. trajbin: 200 frames, each uint32 little-endian count then count packed records (3 float32 xyz, 1 float64 age_seconds). No padding or object IDs; order preserves per-frame active list. Hit maps little-endian float32, indexed by cell_index in corresponding measured_hit_probability.csv. Original occupancy text uses z planes, x rows, y columns.

Source code under research/p3t_world_model_v0; isolated build helper under research/pmfs3d_r1. Small measured inputs plus Native configs retained under inputs/. SHA256SUMS covers all compact evidence files except itself. No simulator or live ROS required to recompute scores from maps. No new GADEN, training, H03, confirmation or closed loop.
