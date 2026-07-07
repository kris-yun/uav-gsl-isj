with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    lines = f.readlines()

content = ''.join(lines)

# Fix NBV function: plumeLogLikelihood now returns lambda (rate), not log-lik
# Replace: mean_c += p * std::exp(log_lik);
# With:    mean_c += p * (1.0f - std::exp(-lambda * observation_dt_));
# And:     var_c += p * (c_pred - mean_c) * (c_pred - mean_c);
old_nbv = '''                            float log_lik = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,
                                                               wind_x, wind_y, wind_speed);
                            mean_c += p * std::exp(log_lik);
                        }
                float var_c = 0.0f;
                for (int i = 0; i < nx_; i++)
                    for (int j = 0; j < ny_; j++)
                        for (int k = 0; k < nz_; k++) {
                            float sx = x_min_ + (i+0.5f) * dx_;
                            float sy = y_min_ + (j+0.5f) * dy_;
                            float sz = z_min_ + (k+0.5f) * dz_;
                            float p = std::exp(grid[i][j][k]);
                            float log_lik = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,
                                                               wind_x, wind_y, wind_speed);
                            float c_pred = std::exp(log_lik);
                            var_c += p * (c_pred - mean_c) * (c_pred - mean_c);'''

new_nbv = '''                            float lambda = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,
                                                               wind_x, wind_y, wind_speed);
                            float p_detect = 1.0f - std::exp(-lambda * 1.0f);
                            mean_c += p * p_detect;
                        }
                float var_c = 0.0f;
                for (int i = 0; i < nx_; i++)
                    for (int j = 0; j < ny_; j++)
                        for (int k = 0; k < nz_; k++) {
                            float sx = x_min_ + (i+0.5f) * dx_;
                            float sy = y_min_ + (j+0.5f) * dy_;
                            float sz = z_min_ + (k+0.5f) * dz_;
                            float p = std::exp(grid[i][j][k]);
                            float lambda = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,
                                                               wind_x, wind_y, wind_speed);
                            float p_detect = 1.0f - std::exp(-lambda * 1.0f);
                            var_c += p * (p_detect - mean_c) * (p_detect - mean_c);'''

if old_nbv in content:
    content = content.replace(old_nbv, new_nbv)
    print("Fixed NBV function")
else:
    print("WARNING: NBV pattern not found")

# Fix EFE function
old_efe = '''                            float ll = posterior3d_.plumeLogLikelihood(psx, psy, psz, cand_x, cand_y,
                                                          current_altitude_, wx, wy, ws);
                            float cp = std::exp(ll);'''

new_efe = '''                            float lambda = posterior3d_.plumeLogLikelihood(psx, psy, psz, cand_x, cand_y,
                                                          current_altitude_, wx, wy, ws);
                            float cp = 1.0f - std::exp(-lambda * 1.0f);'''

if old_efe in content:
    content = content.replace(old_efe, new_efe)
    print("Fixed EFE function")
else:
    print("WARNING: EFE pattern not found")

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.write(content)
print("All fixes applied")