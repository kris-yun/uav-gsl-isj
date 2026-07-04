
// ============================================================
// EDPA-GSL Layer 1: Event-Driven Posterior Update
// ============================================================
void OPGSL::updatePosteriorEventDriven(float cx, float cy, float cz,
                                        bool detected, float concentration,
                                        float wind_x, float wind_y, float wind_speed) {
    if (!posterior3d_.initialized_) return;
    
    // Temporal decay
    float decay = 0.995f;
    for (int ii = 0; ii < posterior3d_.nx_; ii++)
        for (int jj = 0; jj < posterior3d_.ny_; jj++)
            for (int kk = 0; kk < posterior3d_.nz_; kk++)
                posterior3d_.grid[ii][jj][kk] *= decay;

    float wind_dir = std::atan2(wind_y, wind_x);
    
    float max_log = -1e9f;
    for (int i = 0; i < posterior3d_.nx_; i++) {
        for (int j = 0; j < posterior3d_.ny_; j++) {
            for (int k = 0; k < posterior3d_.nz_; k++) {
                float sx = posterior3d_.x_min_ + (i + 0.5f) * posterior3d_.dx_;
                float sy = posterior3d_.y_min_ + (j + 0.5f) * posterior3d_.dy_;
                float sz = posterior3d_.z_min_ + (k + 0.5f) * posterior3d_.dz_;
                
                // Compute arrival rate lambda(x, s)
                float dx = cx - sx, dy = cy - sy, dz = cz - sz;
                float dist = std::sqrt(dx*dx + dy*dy + dz*dz);
                float dist_decay = std::exp(-dist / arrival_rate_ell_);
                
                // Wind alignment: angle between wind and (s -> x) direction
                float s_to_x_dir = std::atan2(dy, dx);
                float angle_diff = s_to_x_dir - wind_dir;
                float wind_mod = 1.0f + arrival_rate_alphaw_ * std::cos(angle_diff);
                wind_mod = std::max(wind_mod, 0.1f);  // prevent zero
                
                float lambda = arrival_rate_lambda0_ * dist_decay * wind_mod;
                float p_detect = 1.0f - std::exp(-lambda * 0.1f);  // Delta_t = 0.1
                
                // Event-driven log-likelihood
                float log_lik;
                if (detected) {
                    // d_t = 1: log P(detect | x, s)
                    log_lik = std::log(std::max(p_detect, 1e-10f));
                } else {
                    // d_t = 0: log P(no detect | x, s) -- THIS IS THE KEY INNOVATION
                    log_lik = std::log(std::max(1.0f - p_detect, 1e-10f));
                }
                
                posterior3d_.grid[i][j][k] += log_lik;
                if (posterior3d_.grid[i][j][k] > max_log)
                    max_log = posterior3d_.grid[i][j][k];
            }
        }
    }
    
    // Log-sum-exp normalization
    float log_sum = -1e9f;
    for (int i = 0; i < posterior3d_.nx_; i++)
        for (int j = 0; j < posterior3d_.ny_; j++)
            for (int k = 0; k < posterior3d_.nz_; k++) {
                posterior3d_.grid[i][j][k] -= max_log;
                log_sum = std::log(std::exp(log_sum) + std::exp(posterior3d_.grid[i][j][k]));
            }
    for (int i = 0; i < posterior3d_.nx_; i++)
        for (int j = 0; j < posterior3d_.ny_; j++)
            for (int k = 0; k < posterior3d_.nz_; k++)
                posterior3d_.grid[i][j][k] -= log_sum;
}

// ============================================================
// EDPA-GSL Layer 2: Posterior-Adaptive EIG
// ============================================================
float OPGSL::computeEIGGlobal(float cx, float cy, float cz,
                                float wind_x, float wind_y, float wind_speed) {
    // Standard Infotaxis EIG: variance of predicted concentration
    float mean_c = 0.0f, var_c = 0.0f;
    for (int i = 0; i < posterior3d_.nx_; i++)
        for (int j = 0; j < posterior3d_.ny_; j++)
            for (int k = 0; k < posterior3d_.nz_; k++) {
                float p = std::exp(posterior3d_.grid[i][j][k]);
                float sx = posterior3d_.x_min_ + (i+0.5f) * posterior3d_.dx_;
                float sy = posterior3d_.y_min_ + (j+0.5f) * posterior3d_.dy_;
                float sz = posterior3d_.z_min_ + (k+0.5f) * posterior3d_.dz_;
                float log_lik = posterior3d_.plumeLogLikelihood(
                    sx, sy, sz, cx, cy, cz, wind_x, wind_y, wind_speed);
                float c_pred = std::exp(log_lik);
                mean_c += p * c_pred;
                var_c += p * c_pred * c_pred;
            }
    var_c -= mean_c * mean_c;
    return std::max(var_c, 0.0f);
}

float OPGSL::computeEIGLocal(float cx, float cy, float cz,
                               float wind_x, float wind_y, float wind_speed) {
    // Upwind-weighted EIG: concentrate information gain in upwind direction
    float eig = computeEIGGlobal(cx, cy, cz, wind_x, wind_y, wind_speed);
    
    // Weight by upwind alignment
    float map_x, map_y, map_z;
    posterior3d_.getMAP(map_x, map_y, map_z);
    float dx = map_x - cx, dy = map_y - cy;
    float dist = std::sqrt(dx*dx + dy*dy);
    if (dist > 0.1f && wind_speed > 0.05f) {
        float wn = std::sqrt(wind_x*wind_x + wind_y*wind_y);
        float upwind_x = -wind_x / wn, upwind_y = -wind_y / wn;
        float alignment = (dx * upwind_x + dy * upwind_y) / dist;
        // Strong upwind bonus when posterior is concentrated
        eig *= std::exp(1.0f * alignment);
    }
    return eig;
}

OPGSL::AdaptiveEIGResult OPGSL::computeAdaptiveEIG() {
    AdaptiveEIGResult result;
    float wx = latest_wind_x_, wy = latest_wind_y_, ws = latest_wind_speed_;
    float cx = currentRobotPosition.x, cy = currentRobotPosition.y;
    
    // Compute search granularity gamma = H(pi_t) / H(pi_0)
    float H_t = posterior3d_.getEntropy();
    if (!entropy_initialized_) {
        initial_entropy_ = H_t;
        entropy_initialized_ = true;
    }
    float gamma = (initial_entropy_ > 1e-6f) ? (H_t / initial_entropy_) : 0.0f;
    gamma = std::clamp(gamma, 0.0f, 1.0f);
    
    // Search over candidate actions (grid of nearby positions)
    float best_eig = -1e9f;
    float best_x = cx, best_y = cy;
    float search_radius = 2.0f;
    int n_cand = 12;
    
    for (int a = 0; a < n_cand; a++) {
        float angle = 2.0f * M_PI * a / n_cand;
        float cand_x = cx + search_radius * std::cos(angle);
        float cand_y = cy + search_radius * std::sin(angle);
        clipToMapBounds(cand_x, cand_y);
        
        float eig_global = computeEIGGlobal(cand_x, cand_y, current_altitude_, wx, wy, ws);
        float eig_local = computeEIGLocal(cand_x, cand_y, current_altitude_, wx, wy, ws);
        
        // Adaptive blend
        float eig_gamma = (1.0f - gamma) * eig_local + gamma * eig_global;
        
        if (eig_gamma > best_eig) {
            best_eig = eig_gamma;
            best_x = cand_x;
            best_y = cand_y;
        }
    }
    
    result.x = best_x;
    result.y = best_y;
    result.z = current_altitude_;
    result.eig_value = best_eig;
    result.gamma = gamma;
    return result;
}

// ============================================================
// EDPA-GSL Layer 3: Anytime-Valid Stopping (Credible Region)
// ============================================================
bool OPGSL::CredibleRegionStopping::checkAndUpdate(float current_radius, int step) {
    if (fired) return true;
    if (step < warmup_steps) return false;
    
    // Compute contraction
    float contraction = prev_radius - current_radius;
    float e_value = 1.0f + eta * std::max(0.0f, contraction);
    e_process *= e_value;
    
    prev_radius = current_radius;
    
    // Check stopping condition
    if (e_process >= 1.0f / delta && current_radius <= epsilon) {
        fired = true;
        return true;
    }
    return false;
}

void OPGSL::CredibleRegionStopping::reset() {
    e_process = 1.0f;
    prev_radius = 1e9f;
    fired = false;
}

// ============================================================
// Helper: Compute posterior credible region radius
// ============================================================
float OPGSL::computeCredibleRegionRadius() {
    float map_x, map_y, map_z;
    posterior3d_.getMAP(map_x, map_y, map_z);
    
    // Find radius containing (1-alpha) of posterior mass
    float target_mass = 1.0f - cr_stopping_.alpha;
    float accumulated = 0.0f;
    
    // Collect (distance, probability) pairs
    std::vector<std::pair<float, float>> dist_prob;
    for (int i = 0; i < posterior3d_.nx_; i++)
        for (int j = 0; j < posterior3d_.ny_; j++)
            for (int k = 0; k < posterior3d_.nz_; k++) {
                float p = std::exp(posterior3d_.grid[i][j][k]);
                float sx = posterior3d_.x_min_ + (i+0.5f) * posterior3d_.dx_;
                float sy = posterior3d_.y_min_ + (j+0.5f) * posterior3d_.dy_;
                float sz = posterior3d_.z_min_ + (k+0.5f) * posterior3d_.dz_;
                float d = std::sqrt((sx-map_x)*(sx-map_x) + (sy-map_y)*(sy-map_y) + (sz-map_z)*(sz-map_z));
                dist_prob.push_back({d, p});
            }
    
    // Sort by distance
    std::sort(dist_prob.begin(), dist_prob.end());
    
    // Accumulate until we reach target mass
    for (auto& [d, p] : dist_prob) {
        accumulated += p;
        if (accumulated >= target_mass) return d;
    }
    return 100.0f;  // fallback
}
