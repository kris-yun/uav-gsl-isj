filepath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(filepath, 'r') as f:
    content = f.read()

# Find the current update function and add event-driven variant
old_update = '''void OPGSL::SourcePosterior3D::update(float cx, float cy, float cz, float concentration,
                                       float wind_x, float wind_y, float wind_speed) {
    if (!initialized_) return;
    // Temporal decay
    float decay = 0.995f;
    for (int ii = 0; ii < nx_; ii++)
        for (int jj = 0; jj < ny_; jj++)
            for (int kk = 0; kk < nz_; kk++)
                grid[ii][jj][kk] *= decay;

    float max_log = -1e9f;
    for (int i = 0; i < nx_; i++) {
        for (int j = 0; j < ny_; j++) {
            for (int k = 0; k < nz_; k++) {
                float sx = x_min_ + (i+0.5f) * dx_;
                float sy = y_min_ + (j+0.5f) * dy_;
                float sz = z_min_ + (k+0.5f) * dz_;
                float log_lik = plumeLogLikelihood(sx, sy, sz, cx, cy, cz, wind_x, wind_y, wind_speed);
                // Weight by concentration
                float weight;
                if (concentration > 0.01f) {
                    weight = std::clamp(std::sqrt(concentration) * 1.5f, 0.0f, 3.0f);
                } else {
                    weight = 0.001f;  // Bug3 fix: weak positive, not negative
                }
                grid[i][j][k] += weight * log_lik;
                if (grid[i][j][k] > max_log) max_log = grid[i][j][k];
            }
        }
    }'''

new_update = '''void OPGSL::SourcePosterior3D::update(float cx, float cy, float cz, float concentration,
                                       float wind_x, float wind_y, float wind_speed) {
    if (!initialized_) return;
    // Temporal decay
    float decay = 0.995f;
    for (int ii = 0; ii < nx_; ii++)
        for (int jj = 0; jj < ny_; jj++)
            for (int kk = 0; kk < nz_; kk++)
                grid[ii][jj][kk] *= decay;

    float max_log = -1e9f;
    
    // Event-driven model parameters (from EDPA config)
    // lambda(x, s) = lambda0 * exp(-||x-s||/ell) * (1 + alpha_w * cos(theta))
    // Detection probability: p_det = 1 - exp(-lambda * dt)
    const float lambda0 = 1.0f;   // source emission rate
    const float ell = 2.0f;       // characteristic transport length
    const float alpha_w = 0.5f;   // wind anisotropy
    const float dt = 1.0f;        // time step duration
    const float det_threshold = 0.01f;  // detection threshold
    bool detected = (concentration > det_threshold);
    
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

if old_update in content:
    content = content.replace(old_update, new_update)
    with open(filepath, 'w') as f:
        f.write(content)
    print('Implemented event-driven posterior update')
else:
    print('ERROR: pattern not found')
    # Show context around the function
    idx = content.find('void OPGSL::SourcePosterior3D::update')
    if idx >= 0:
        print(f'Found at index {idx}')
        print(content[idx:idx+200])
    else:
        print('Function not found at all')
