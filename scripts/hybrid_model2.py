filepath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(filepath, 'r') as f:
    lines = f.readlines()

# Find the start and end of the block to replace
start_line = None
end_line = None
for i, line in enumerate(lines):
    if '// Event-driven model parameters' in line and 'Default values' in lines[i+1] if i+1 < len(lines) else False:
        start_line = i
    if start_line and 'float log_sum = -1e9f;' in line:
        end_line = i
        break

if start_line and end_line:
    # Replace lines start_line to end_line-1 with hybrid model
    hybrid_code = '''    // HYBRID MODEL:
    // - Detection (z > threshold): use continuous plume likelihood with concentration-weighted update
    // - Non-detection (z <= threshold): use event-driven exclusion model
    bool detected = (concentration > 0.01f);
    
    for (int i = 0; i < nx_; i++) {
        for (int j = 0; j < ny_; j++) {
            for (int k = 0; k < nz_; k++) {
                float sx = x_min_ + (i+0.5f) * dx_;
                float sy = y_min_ + (j+0.5f) * dy_;
                float sz = z_min_ + (k+0.5f) * dz_;
                
                float log_lik;
                float weight;
                
                if (detected) {
                    // DETECTION: use continuous plume log-likelihood (existing model)
                    log_lik = plumeLogLikelihood(sx, sy, sz, cx, cy, cz, wind_x, wind_y, wind_speed);
                    weight = std::clamp(std::sqrt(concentration) * 1.5f, 0.5f, 3.0f);
                } else {
                    // NON-DETECTION: use event-driven exclusion model
                    float dist = std::sqrt((cx-sx)*(cx-sx) + (cy-sy)*(cy-sy) + (cz-sz)*(cz-sz));
                    float wn = std::sqrt(wind_x * wind_x + wind_y * wind_y);
                    float dx_s = sx - cx, dy_s = sy - cy;
                    float cos_theta = 0.0f;
                    if (wn > 0.01f && dist > 0.01f) {
                        cos_theta = (wind_x * dx_s + wind_y * dy_s) / (wn * dist);
                    }
                    float lambda = std::max(1.0f * std::exp(-dist / 2.0f) * (1.0f + 0.5f * cos_theta), 0.001f);
                    float p_det = std::clamp(1.0f - std::exp(-lambda), 0.001f, 0.999f);
                    log_lik = std::log(1.0f - p_det);  // non-detection likelihood
                    weight = 0.3f;  // moderate weight for exclusion
                }
                
                grid[i][j][k] += weight * log_lik;
                if (grid[i][j][k] > max_log) max_log = grid[i][j][k];
            }
        }
    }
'''
    new_lines = lines[:start_line] + [hybrid_code] + lines[end_line:]
    
    with open(filepath, 'w') as f:
        f.writelines(new_lines)
    print(f'Replaced lines {start_line+1}-{end_line} with hybrid model')
else:
    print(f'start={start_line}, end={end_line} - not found')
