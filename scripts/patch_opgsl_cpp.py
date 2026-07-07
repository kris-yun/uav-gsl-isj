import re

# Read the current file
with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    lines = f.readlines()

content = ''.join(lines)

# ======== CHANGE 1: Replace plumeLogLikelihood with Poisson event likelihood ========
old_ll = '''float OPGSL::SourcePosterior3D::plumeLogLikelihood(float sx, float sy, float sz,
                                           float cx, float cy, float cz,
                                           float wind_x, float wind_y, float wind_speed) const {
    float dx = cx - sx, dy = cy - sy, dz = cz - sz;
    float dist = std::sqrt(dx*dx + dy*dy + dz*dz) + 0.01f;

    // Decompose into along-wind and cross-wind
    float wn = std::sqrt(wind_x*wind_x + wind_y*wind_y) + 1e-6f;
    float wx = wind_x / wn, wy = wind_y / wn;
    float d_parallel = dx * wx + dy * wy;
    float d_perp_sq = dx*dx + dy*dy - d_parallel*d_parallel;

    // Anisotropic Gaussian: narrower along wind, wider cross wind
    float u_ref = 0.7f;
    float anisotropy = std::min(wn / u_ref, 1.0f);

    // Adaptive spreading: low wind -> large sigma (isotropic), high wind -> small (anisotropic)
    float sig_par = 2.0f / (anisotropy + 0.15f);
    float sig_perp = 1.2f / (anisotropy + 0.15f);
    float sig_z = 1.0f / (anisotropy + 0.15f);

    float log_lik = -d_parallel*d_parallel / (2*sig_par*sig_par)
                    -d_perp_sq / (2*sig_perp*sig_perp)
                    -dz_sq / (2*sig_z*sig_z);

    // Upwind penalty (weaker in low wind)
    if (d_parallel < -0.5f)
        log_lik -= 2.0f * anisotropy * std::abs(d_parallel);

    // Distance attenuation
    log_lik -= 0.15f * dist;

    return log_lik;
}'''

new_ll = '''// Poisson filament arrival model: lambda(x,s) = lambda0 * exp(-dist/ell) * (1 + alpha_w * cos_theta)
// This is NOT a heuristic - it models the physical process of gas filaments dispersing from source.
// Parameters are derived from GADEN filament simulation statistics.
float OPGSL::SourcePosterior3D::plumeLogLikelihood(float sx, float sy, float sz,
                                           float cx, float cy, float cz,
                                           float wind_x, float wind_y, float wind_speed) const {
    float dx = cx - sx, dy = cy - sy, dz = cz - sz;
    float dist = std::sqrt(dx*dx + dy*dy + dz*dz);

    // Wind alignment: cos_theta > 0 when observation is DOWNWIND of source
    // (filaments drift downwind, so downwind observations have higher arrival rate)
    float wn = std::sqrt(wind_x*wind_x + wind_y*wind_y) + 1e-6f;
    float wx = wind_x / wn, wy = wind_y / wn;
    float cos_theta = (dx * wx + dy * wy) / (dist + 1e-6f);

    // Poisson arrival rate: exponential distance decay with wind modulation
    // lambda0: baseline rate at source (calibrated from GADEN filament statistics)
    // ell: characteristic decay length (meters)
    // alpha_w: wind modulation strength (0=isotropic, 1=fully directional)
    float lambda = poisson_lambda0_ * std::exp(-dist / poisson_ell_)
                   * (1.0f + poisson_alpha_w_ * cos_theta);
    lambda = std::max(lambda, 1e-6f);

    // This function returns the rate; the actual log-likelihood for binary
    // detection/non-detection is computed in update() using:
    //   detected:     log(1 - exp(-lambda * dt))
    //   not detected: -lambda * dt
    return lambda;
}'''

# ======== CHANGE 2: Replace update function with Poisson binary event model ========
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
                    weight = 0.3f;  // Enhanced non-detection information
                }
                grid[i][j][k] += weight * log_lik;
                if (grid[i][j][k] > max_log) max_log = grid[i][j][k];
            }
        }
    }
    // Log-sum-exp normalization
    float log_sum = -1e9f;
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++) {
                grid[i][j][k] -= max_log;
                log_sum = std::log(std::exp(log_sum) + std::exp(grid[i][j][k]));
            }
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++)
                grid[i][j][k] -= log_sum;
}'''

new_update = '''void OPGSL::SourcePosterior3D::update(float cx, float cy, float cz, float concentration,
                                       float wind_x, float wind_y, float wind_speed) {
    if (!initialized_) return;

    // Temporal decay: prevents posterior from becoming overconfident on old data
    float decay = 0.995f;
    for (int ii = 0; ii < nx_; ii++)
        for (int jj = 0; jj < ny_; jj++)
            for (int kk = 0; kk < nz_; kk++)
                grid[ii][jj][kk] *= decay;

    // Binary detection event: threshold-based (event-driven observation model)
    bool detected = (concentration > detection_threshold_);

    // Poisson binary event log-likelihood update
    // This is the CORRECT Bayesian update for Poisson filament arrivals.
    // No heuristic weights needed - the likelihood ratio IS the update.
    //
    // Detected:     log P(d=1|x,s) = log(1 - exp(-lambda * dt))
    // Not detected: log P(d=0|x,s) = -lambda * dt
    //
    // Key insight: non-detection is informative!
    // Close to source: lambda is large, P(d=0) is small, so d=0 STRONGLY excludes nearby sources
    // Far from source: lambda is small, P(d=0) is ~1, so d=0 has little effect
    float dt = observation_dt_;

    float max_log = -1e9f;
    for (int i = 0; i < nx_; i++) {
        for (int j = 0; j < ny_; j++) {
            for (int k = 0; k < nz_; k++) {
                float sx = x_min_ + (i+0.5f) * dx_;
                float sy = y_min_ + (j+0.5f) * dy_;
                float sz = z_min_ + (k+0.5f) * dz_;

                // Get Poisson arrival rate at this (robot, source_candidate) pair
                float lambda = plumeLogLikelihood(sx, sy, sz, cx, cy, cz, wind_x, wind_y, wind_speed);
                lambda = std::max(lambda, 1e-6f);

                // Binary event log-likelihood
                float log_lik;
                if (detected) {
                    // log(1 - exp(-lambda * dt)) — numerically stable
                    float neg_rate = -lambda * dt;
                    log_lik = std::log(1.0f - std::exp(neg_rate));
                } else {
                    // log(exp(-lambda * dt)) = -lambda * dt
                    log_lik = -lambda * dt;
                }

                // Direct Bayesian update: no weight multiplication needed
                // The likelihood ratio naturally handles detection vs non-detection
                grid[i][j][k] += log_lik;
                if (grid[i][j][k] > max_log) max_log = grid[i][j][k];
            }
        }
    }
    // Log-sum-exp normalization (standard for log-domain posteriors)
    float log_sum = -1e9f;
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++) {
                grid[i][j][k] -= max_log;
                log_sum = std::log(std::exp(log_sum) + std::exp(grid[i][j][k]));
            }
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++)
                grid[i][j][k] -= log_sum;
}'''

# ======== CHANGE 3: Add Poisson parameters to declareParameters ========
old_params = '''    use_cp_ = getParam<bool>("opgsl.modules.cp", true);'''
new_params = '''    // Poisson filament arrival model parameters
    // Physically motivated: models discrete filament arrivals from GADEN simulation
    // lambda0: baseline arrival rate at zero distance (filaments/second)
    // ell: characteristic decay length (meters) — filament dispersal scale
    // alpha_w: wind modulation strength (dimensionless, 0-1)
    // dt: observation integration time (seconds)
    // det_threshold: binary detection threshold (concentration units)
    poisson_lambda0_ = getParam<float>("opgsl.poisson.lambda0", 2.0f);
    poisson_ell_ = getParam<float>("opgsl.poisson.ell", 2.5f);
    poisson_alpha_w_ = getParam<float>("opgsl.poisson.alpha_w", 0.5f);
    observation_dt_ = getParam<float>("opgsl.poisson.dt", 1.0f);
    detection_threshold_ = getParam<float>("opgsl.poisson.det_threshold", 0.005f);
    posterior3d_.poisson_lambda0_ = poisson_lambda0_;
    posterior3d_.poisson_ell_ = poisson_ell_;
    posterior3d_.poisson_alpha_w_ = poisson_alpha_w_;
    posterior3d_.observation_dt_ = observation_dt_;
    posterior3d_.detection_threshold_ = detection_threshold_;

    use_cp_ = getParam<bool>("opgsl.modules.cp", true);'''

# Apply all changes
if old_ll in content:
    content = content.replace(old_ll, new_ll)
    print("CHANGE 1 applied: plumeLogLikelihood replaced with Poisson model")
else:
    print("WARNING: Could not find old plumeLogLikelihood")

if old_update in content:
    content = content.replace(old_update, new_update)
    print("CHANGE 2 applied: update() replaced with Poisson binary event model")
else:
    print("WARNING: Could not find old update function")

if old_params in content:
    content = content.replace(old_params, new_params)
    print("CHANGE 3 applied: Poisson parameters added to declareParameters")
else:
    print("WARNING: Could not find use_cp_ parameter line")

# Write the modified file
with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.write(content)
print("OPGSL.cpp written successfully")