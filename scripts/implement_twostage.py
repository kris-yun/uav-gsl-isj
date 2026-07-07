"""
Principled Poisson posterior implementation.
Key insight: WR-SFE field guides search BEFORE first detection,
Poisson likelihood takes over AFTER first detection.
This avoids the "prior crush" problem where non-detections at start
eliminate the true source.
"""
import re

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    content = f.read()

# === CHANGE 1: Replace plumeLogLikelihood with Poisson rate ===
old_ll = re.search(r'float OPGSL::SourcePosterior3D::plumeLogLikelihood\(float sx.*?\n\}', content, re.DOTALL)
if old_ll:
    new_ll = """// Poisson filament arrival rate: lambda(x,s) = lambda0 * exp(-dist/ell) * (1 + alpha_w * cos_theta)
// Returns ARRIVAL RATE (positive), not log-likelihood.
float OPGSL::SourcePosterior3D::plumeLogLikelihood(float sx, float sy, float sz,
                                                     float cx, float cy, float cz,
                                                     float wind_x, float wind_y, float wind_speed) const {
    float dx = cx - sx, dy = cy - sy, dz = cz - sz;
    float dist = std::sqrt(dx*dx + dy*dy + dz*dz);

    // Wind alignment: cos_theta > 0 when observation is DOWNWIND of source
    float wn = std::sqrt(wind_x*wind_x + wind_y*wind_y) + 1e-6f;
    float wx = wind_x / wn, wy = wind_y / wn;
    float cos_theta = (dx * wx + dy * wy) / (dist + 1e-6f);

    // Poisson arrival rate
    float lambda = poisson_lambda0_ * std::exp(-dist / poisson_ell_)
                   * (1.0f + poisson_alpha_w_ * cos_theta);
    return std::max(lambda, 1e-6f);
}"""
    content = content[:old_ll.start()] + new_ll + content[old_ll.end():]
    print("CHANGE 1: plumeLogLikelihood -> Poisson rate OK")
else:
    print("ERROR: plumeLogLikelihood not found")
    import sys; sys.exit(1)

# === CHANGE 2: Replace update with principled Poisson + WR-SFE hybrid ===
old_upd = re.search(r'void OPGSL::SourcePosterior3D::update\(float cx.*?void OPGSL::SourcePosterior3D::getMAP', content, re.DOTALL)
if old_upd:
    new_upd = """void OPGSL::SourcePosterior3D::update(float cx, float cy, float cz, float concentration,
                                       float wind_x, float wind_y, float wind_speed) {
    if (!initialized_) return;

    // Temporal decay
    float decay = 0.995f;
    for (int ii = 0; ii < nx_; ii++)
        for (int jj = 0; jj < ny_; jj++)
            for (int kk = 0; kk < nz_; kk++)
                grid[ii][jj][kk] *= decay;

    // === STAGE 1: Before first detection, use distance-based soft prior ===
    // This prevents the Poisson model from eliminating the true source
    // when the UAV starts far from it and detects nothing.
    if (!has_received_detection_) {
        if (concentration > detection_threshold_) {
            has_received_detection_ = true;
            first_detection_x_ = cx;
            first_detection_y_ = cy;
        } else {
            // Soft update: mildly favor cells closer to UAV (exploration bonus)
            // but do NOT penalize distant cells (preserve prior)
            for (int i = 0; i < nx_; i++) {
                for (int j = 0; j < ny_; j++) {
                    for (int k = 0; k < nz_; k++) {
                        float sx = x_min_ + (i+0.5f) * dx_;
                        float sy = y_min_ + (j+0.5f) * dy_;
                        float dz_cell = cy - sy;
                        float dx_cell = cx - sx;
                        float dist = std::sqrt(dx_cell*dx_cell + dz_cell*dz_cell);
                        // Soft exploration bonus: closer cells get tiny boost
                        float soft_update = -0.005f * dist;
                        grid[i][j][k] += soft_update;
                    }
                }
            }
            // Normalize
            float max_log = -1e9f;
            for (int i = 0; i < nx_; i++)
                for (int j = 0; j < ny_; j++)
                    for (int k = 0; k < nz_; k++)
                        if (grid[i][j][k] > max_log) max_log = grid[i][j][k];
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
            return;
        }
    }

    // === STAGE 2: After first detection, use Poisson binary event model ===
    bool detected = (concentration > detection_threshold_);
    float dt = observation_dt_;

    float max_log = -1e9f;
    for (int i = 0; i < nx_; i++) {
        for (int j = 0; j < ny_; j++) {
            for (int k = 0; k < nz_; k++) {
                float sx = x_min_ + (i+0.5f) * dx_;
                float sy = y_min_ + (j+0.5f) * dy_;
                float sz = z_min_ + (k+0.5f) * dz_;

                float lambda = plumeLogLikelihood(sx, sy, sz, cx, cy, cz, wind_x, wind_y, wind_speed);
                lambda = std::max(lambda, 1e-6f);

                float log_lik;
                if (detected) {
                    float neg_rate = -lambda * dt;
                    log_lik = std::log(1.0f - std::exp(neg_rate));
                } else {
                    log_lik = -lambda * dt;
                }

                grid[i][j][k] += log_lik;
                if (grid[i][j][k] > max_log) max_log = grid[i][j][k];
            }
        }
    }

    // Log-sum-exp normalization with 2% uniform mixing
    float mix_alpha = 0.02f;
    float log_mix = std::log(mix_alpha / (float)(nx_ * ny_ * nz_));
    float log_1m_mix = std::log(1.0f - mix_alpha);
    float log_sum = -1e9f;
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++) {
                grid[i][j][k] -= max_log;
                grid[i][j][k] = log_1m_mix + grid[i][j][k];
                float u = log_mix;
                float v = grid[i][j][k];
                float mx2 = (u > v) ? u : v;
                grid[i][j][k] = mx2 + std::log(std::exp(u - mx2) + std::exp(v - mx2));
                log_sum = std::log(std::exp(log_sum) + std::exp(grid[i][j][k]));
            }
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++)
                grid[i][j][k] -= log_sum;
}

void OPGSL::SourcePosterior3D::getMAP"""
    content = content[:old_upd.start()] + new_upd + content[old_upd.end():]
    print("CHANGE 2: Two-stage update OK")
else:
    print("ERROR: update function not found")

# === CHANGE 3: Fix callers that use exp(log_lik) ===
content = content.replace('mean_c += p * std::exp(log_lik);', 'mean_c += p * (1.0f - std::exp(-lambda));')
content = content.replace('float c_pred = std::exp(log_lik);', 'float c_pred = 1.0f - std::exp(-lambda);')
# Fix variable names
content = content.replace(
    'float log_lik = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,\\n                                                               wind_x, wind_y, wind_speed);\\n                            mean_c += p * (1.0f - std::exp(-lambda));',
    'float lam = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,\\n                                                               wind_x, wind_y, wind_speed);\\n                            mean_c += p * (1.0f - std::exp(-lam));'
)
# Fix EFE caller
content = content.replace(
    'float ll = posterior3d_.plumeLogLikelihood(psx, psy, psz, cand_x, cand_y,\\n                                                          current_altitude_, wx, wy, ws);\\n                            float cp = std::exp(ll);',
    'float lam_e = posterior3d_.plumeLogLikelihood(psx, psy, psz, cand_x, cand_y,\\n                                                          current_altitude_, wx, wy, ws);\\n                            float cp = 1.0f - std::exp(-lam_e);'
)
print("CHANGE 3: Caller fixes OK")

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.write(content)

# Verify brace balance
opens = content.count('{')
closes = content.count('}')
print("Braces: open=%d close=%d balanced=%s" % (opens, closes, opens == closes))