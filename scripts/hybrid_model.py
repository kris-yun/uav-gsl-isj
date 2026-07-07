filepath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(filepath, 'r') as f:
    content = f.read()

# Replace the event-driven update with a HYBRID approach:
# - Detection (concentration > threshold): use original continuous log-likelihood with weight
# - Non-detection (concentration <= threshold): use event-driven exclusion with moderate weight

old_update_start = '''    // Event-driven model parameters (from OPGSL member variables)
    // Default values: lambda0=5.0, ell=4.0, alpha_w=0.3, threshold=0.01
    const float lambda0 = 5.0f;
    const float ell = 4.0f;
    const float alpha_w = 0.3f;
    const float dt = 1.0f;
    const float det_threshold = 0.01f;
    bool detected = (concentration > det_threshold);
    bool use_event_driven = true;
    
    float wn = std::sqrt(wind_x * wind_x + wind_y * wind_y);
    
    for (int i = 0; i < nx_; i++) {
        for (int j = 0; j < ny_; j++) {
            for (int k = 0; k < nz_; k++) {
                float sx = x_min_ + (i+0.5f) * dx_;
                float sy = y_min_ + (j+0.5f) * dy_;
                float sz = z_min_ + (k+0.5f) * dz_;
                
                // Compute event-driven likelihood
                float dist = std::sqrt((cx-sx)*(cx-sx) + (cy-sy)*(cy-sy) + (cz-sz)*(cz-sz));
                
                // Wind alignment: angle between wind direction and (robot -> candidate source)
                float dx_s = sx - cx, dy_s = sy - cy;
                float cos_theta = 0.0f;
                if (wn > 0.01f && dist > 0.01f) {
                    cos_theta = (wind_x * dx_s + wind_y * dy_s) / (wn * dist);
                }
                
                // Arrival rate at robot position from candidate source
                float lambda = lambda0 * std::exp(-dist / ell) * (1.0f + alpha_w * cos_theta);
                lambda = std::max(lambda, 0.001f);  // floor to prevent log(0)
                
                // Detection probability
                float p_det = 1.0f - std::exp(-lambda * dt);
                p_det = std::clamp(p_det, 0.001f, 0.999f);
                
                // Event-driven log-likelihood
                float log_lik;
                if (detected) {
                    log_lik = std::log(p_det);           // detection: source likely nearby
                } else {
                    log_lik = std::log(1.0f - p_det);    // non-detection: source likely far
                }
                
                // Equal weight for detection and non-detection (core of event-driven model)
                float weight = 1.0f;
                grid[i][j][k] += weight * log_lik;
                if (grid[i][j][k] > max_log) max_log = grid[i][j][k];
            }
        }
    }'''

new_update_start = '''    // HYBRID MODEL:
    // - Detection (z > threshold): use continuous plume likelihood with concentration-weighted update
    // - Non-detection (z <= threshold): use event-driven exclusion model
    // This combines the precision of continuous model near source with
    // the information content of non-detection far from source.
    
    float wn = std::sqrt(wind_x * wind_x + wind_y * wind_y);
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
                    float dx_s = sx - cx, dy_s = sy - cy;
                    float cos_theta = 0.0f;
                    if (wn > 0.01f && dist > 0.01f) {
                        cos_theta = (wind_x * dx_s + wind_y * dy_s) / (wn * dist);
                    }
                    float lambda = std::max(1.0f * std::exp(-dist / 2.0f) * (1.0f + 0.5f * cos_theta), 0.001f);
                    float p_det = std::clamp(1.0f - std::exp(-lambda), 0.001f, 0.999f);
                    log_lik = std::log(1.0f - p_det);  // non-detection likelihood
                    weight = 0.3f;  // moderate weight for exclusion (not too aggressive)
                }
                
                grid[i][j][k] += weight * log_lik;
                if (grid[i][j][k] > max_log) max_log = grid[i][j][k];
            }
        }
    }'''

if old_update_start in content:
    content = content.replace(old_update_start, new_update_start)
    with open(filepath, 'w') as f:
        f.write(content)
    print('Implemented hybrid model: continuous for detection, event-driven for non-detection')
else:
    print('ERROR: pattern not found')
