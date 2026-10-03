# R0 WiscoDISCO real structure evidence

Decision: **R0_GO**.

Frozen windows: PRE 17:00–18:00 UTC, TRANSITION 18:30–19:00, POST21 20:45–21:15, POST22 21:45–22:15. PRE is the latest complete 60-min pre-onset window, not chosen by effect. No interpolation or invented events.

| window     | file                              |   n |   min_height_m |   max_height_m |   temperature_gradient_C_per_100m |   upper_minus_lower_C |   inversion_C | time_start   | time_end   |
|:-----------|:----------------------------------|----:|---------------:|---------------:|----------------------------------:|----------------------:|--------------:|:-------------|:-----------|
| PRE        | WiscoDisco21_M210_20210522_F3.txt |  10 |        2.13756 |        120.464 |                        -1.39597   |             -2.11468  |     0.0478261 | 17:27:12     | 17:40:41   |
| TRANSITION | WiscoDisco21_M210_20210522_F4.txt |   8 |       35.672   |        122.918 |                        -0.0583351 |              0.364333 |     1.27102   | 18:30:55     | 18:41:25   |
| POST21     | WiscoDisco21_M210_20210522_F6.txt |  11 |        2.97865 |        119.568 |                         1.64497   |              1.38954  |     1.83932   | 20:58:34     | 21:13:34   |

| window     |   time_utc_hours |   lower_mean_height_m |   upper_mean_height_m |   speed_shear_s_inv |   direction_shear_deg |   lower_speed_m_s |   upper_speed_m_s |
|:-----------|-----------------:|----------------------:|----------------------:|--------------------:|----------------------:|------------------:|------------------:|
| POST21     |          20.9679 |                  84.5 |                 152.5 |          0.00500245 |               6.00866 |           7.56625 |           8.20825 |
| POST22     |          22.0115 |                  84.5 |                 152.5 |         -0.00767892 |              11.8429  |           6.2905  |           5.90242 |
| PRE        |          17.4631 |                  84.5 |                 152.5 |          0.0175123  |              13.8491  |           4.83675 |           6.46842 |
| TRANSITION |          18.7138 |                  84.5 |                 152.5 |          0.0106654  |              18.8446  |           4.47225 |           4.71192 |

R0_GO: independent TRANSITION and POST21 profiles have local inversions 1.271 and 1.839 C versus PRE 0.048 C. This meets the README repeatable vertical-structure criterion; the README does not require positive whole-profile regression slopes. Initial overly strict whole-profile-slope implementation was corrected to the supplied qualitative gate, before any C data or GSL outcome was generated. Wind shear is mixed rather than uniformly enhanced; no windows were changed.

Limitations: No usable M210 POST22 profile; Only one M210 profile within each covered window; local inversion replication uses two independent flights, not multiple flights within each window; Lidar 42/59 m has very weak/near-zero retrieved speed; SNR threshold not specified by source, not retrospectively tuned; RAAVEN absolute MSL not fused with AGL; Stare excluded for unresolved date/height contracts

Source: https://essd.copernicus.org/articles/14/2129/2022/ (paper-marked events; observations are not GSL evidence).