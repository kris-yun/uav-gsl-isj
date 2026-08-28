#!/usr/bin/env python3
"""Frozen truth-free PF-DEI V3 feature schema."""

FEATURE_NAMES = (
    "robot_dx_to_carrier_centroid",
    "robot_dy_to_carrier_centroid",
    "carrier_width_m",
    "carrier_height_m",
    "carrier_free_mask_00",
    "carrier_free_mask_01",
    "carrier_free_mask_10",
    "carrier_free_mask_11",
    "carrier_free_count_normalized",
    "log1p_measured_ppm_over_threshold",
    "measured_wind_x",
    "measured_wind_y",
    "measured_wind_z",
    "delta_time_s",
    "stop_start",
    "block_boundary",
)
INPUT_DIM = len(FEATURE_NAMES)
DILATIONS = (1, 2, 4, 8, 16, 32, 64, 128, 256)
