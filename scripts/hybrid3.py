filepath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(filepath, 'r') as f:
    lines = f.readlines()

# Find start: line 285 (0-indexed 284) "// Event-driven model parameters"
# Find end: line 330 (0-indexed 329) "// Log-sum-exp normalization"
start = 284  # "// Event-driven model parameters"
end = 330    # "// Log-sum-exp normalization"

hybrid = '''    // HYBRID MODEL: continuous for detection, event-driven for non-detection
    bool detected = (concentration > 0.01f);
    for (int i = 0; i < nx_; i++) {
        for (int j = 0; j < ny_; j++) {
            for (int k = 0; k < nz_; k++) {
                float sx = x_min_ + (i+0.5f) * dx_;
                float sy = y_min_ + (j+0.5f) * dy_;
                float sz = z_min_ + (k+0.5f) * dz_;
                float log_lik, weight;
                if (detected) {
                    log_lik = plumeLogLikelihood(sx, sy, sz, cx, cy, cz, wind_x, wind_y, wind_speed);
                    weight = std::clamp(std::sqrt(concentration) * 1.5f, 0.5f, 3.0f);
                } else {
                    float dist = std::sqrt((cx-sx)*(cx-sx) + (cy-sy)*(cy-sy) + (cz-sz)*(cz-sz));
                    float wn = std::sqrt(wind_x * wind_x + wind_y * wind_y);
                    float cos_theta = 0.0f;
                    if (wn > 0.01f && dist > 0.01f)
                        cos_theta = (wind_x * (sx - cx) + wind_y * (sy - cy)) / (wn * dist);
                    float lambda = std::max(std::exp(-dist / 2.0f) * (1.0f + 0.5f * cos_theta), 0.001f);
                    float p_det = std::clamp(1.0f - std::exp(-lambda), 0.001f, 0.999f);
                    log_lik = std::log(1.0f - p_det);
                    weight = 0.3f;
                }
                grid[i][j][k] += weight * log_lik;
                if (grid[i][j][k] > max_log) max_log = grid[i][j][k];
            }
        }
    }
'''

new_lines = lines[:start] + [hybrid] + lines[end:]
with open(filepath, 'w') as f:
    f.writelines(new_lines)
print(f'Replaced lines {start+1}-{end} with hybrid model ({len(new_lines)} lines)')
