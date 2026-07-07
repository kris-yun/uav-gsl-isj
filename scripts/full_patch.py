import re

# ============ Read files ============
with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    cpp = f.read()
with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp', 'r') as f:
    hpp = f.read()

# ============ CPP CHANGE 1: Replace plumeLogLikelihood function ============
# Find and replace the entire function body
old_ll_pattern = r'float OPGSL::SourcePosterior3D::plumeLogLikelihood\(float sx.*?\n\}'
match = re.search(old_ll_pattern, cpp, re.DOTALL)
if match:
    new_ll = '''// Poisson filament arrival model: lambda(x,s) = lambda0 * exp(-dist/ell) * (1 + alpha_w * cos_theta)
// Returns the ARRIVAL RATE (positive value), not log-likelihood.
// The binary event log-likelihood is computed in update() using:
//   detected:     log(1 - exp(-lambda * dt))
//   not detected: -lambda * dt
// This is physically motivated by GADEN filament dispersion model.
float OPGSL::SourcePosterior3D::plumeLogLikelihood(float sx, float sy, float sz,
                                                     float cx, float cy, float cz,
                                                     float wind_x, float wind_y, float wind_speed) const {
    float dx = cx - sx, dy = cy - sy, dz = cz - sz;
    float dist = std::sqrt(dx*dx + dy*dy + dz*dz);

    // Wind alignment: cos_theta > 0 when observation point is DOWNWIND of source candidate
    float wn = std::sqrt(wind_x*wind_x + wind_y*wind_y) + 1e-6f;
    float wx = wind_x / wn, wy = wind_y / wn;
    float cos_theta = (dx * wx + dy * wy) / (dist + 1e-6f);

    // Poisson arrival rate: exponential distance decay with wind modulation
    float lambda = poisson_lambda0_ * std::exp(-dist / poisson_ell_)
                   * (1.0f + poisson_alpha_w_ * cos_theta);
    lambda = std::max(lambda, 1e-6f);
    return lambda;
}'''
    cpp = cpp[:match.start()] + new_ll + cpp[match.end():]
    print("CHANGE 1: plumeLogLikelihood -> Poisson rate model OK")
else:
    print("ERROR: plumeLogLikelihood not found")
    import sys; sys.exit(1)

# Verify brace balance
opens = cpp.count('{')
closes = cpp.count('}')
print("After CHANGE 1: braces open=%d close=%d" % (opens, closes))

# ============ CPP CHANGE 2: Replace update function ============
old_upd_pattern = r'void OPGSL::SourcePosterior3D::update\(float cx.*?void OPGSL::SourcePosterior3D::getMAP'
match2 = re.search(old_upd_pattern, cpp, re.DOTALL)
if match2:
    new_update = '''void OPGSL::SourcePosterior3D::update(float cx, float cy, float cz, float concentration,
                                       float wind_x, float wind_y, float wind_speed) {
    if (!initialized_) return;

    // Temporal decay: prevents posterior from becoming overconfident on old data
    float decay = 0.995f;
    for (int ii = 0; ii < nx_; ii++)
        for (int jj = 0; jj < ny_; jj++)
            for (int kk = 0; kk < nz_; kk++)
                grid[ii][jj][kk] *= decay;

    // Binary detection event: threshold-based
    bool detected = (concentration > detection_threshold_);
    float dt = observation_dt_;

    float max_log = -1e9f;
    for (int i = 0; i < nx_; i++) {
        for (int j = 0; j < ny_; j++) {
            for (int k = 0; k < nz_; k++) {
                float sx = x_min_ + (i+0.5f) * dx_;
                float sy = y_min_ + (j+0.5f) * dy_;
                float sz = z_min_ + (k+0.5f) * dz_;

                // Poisson arrival rate at (robot, source_candidate)
                float lambda = plumeLogLikelihood(sx, sy, sz, cx, cy, cz, wind_x, wind_y, wind_speed);
                lambda = std::max(lambda, 1e-6f);

                // Binary event log-likelihood (no heuristic weights!)
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
}

void OPGSL::SourcePosterior3D::getMAP'''
    cpp = cpp[:match2.start()] + new_update + cpp[match2.end():]
    print("CHANGE 2: update() -> Poisson binary event model OK")
else:
    print("ERROR: update function not found")

opens = cpp.count('{')
closes = cpp.count('}')
print("After CHANGE 2: braces open=%d close=%d" % (opens, closes))

# ============ CPP CHANGE 3: Fix NBV caller ============
old_nbv1 = 'mean_c += p * std::exp(log_lik);'
new_nbv1 = 'mean_c += p * (1.0f - std::exp(-lambda));'
if old_nbv1 in cpp:
    cpp = cpp.replace(
        'float log_lik = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,\\n                                                               wind_x, wind_y, wind_speed);\\n                            mean_c += p * std::exp(log_lik);',
        'float lambda = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,\\n                                                               wind_x, wind_y, wind_speed);\\n                            mean_c += p * (1.0f - std::exp(-lambda));'
    )
    # Simpler: just replace the exp(log_lik) pattern
    cpp = cpp.replace('mean_c += p * std::exp(log_lik);', 'mean_c += p * (1.0f - std::exp(-lambda));')
    cpp = cpp.replace('float c_pred = std::exp(log_lik);', 'float c_pred = 1.0f - std::exp(-lambda);')
    # Fix the variable name in NBV
    cpp = cpp.replace('float log_lik = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,\\n                                                               wind_x, wind_y, wind_speed);\\n                            float c_pred',
                      'float lambda = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,\\n                                                               wind_x, wind_y, wind_speed);\\n                            float c_pred')
    print("CHANGE 3a: NBV caller fix OK")

# ============ CPP CHANGE 3b: Fix EFE caller ============
cpp = cpp.replace(
    'float ll = posterior3d_.plumeLogLikelihood(psx, psy, psz, cand_x, cand_y,\\n                                                          current_altitude_, wx, wy, ws);\\n                            float cp = std::exp(ll);',
    'float lambda = posterior3d_.plumeLogLikelihood(psx, psy, psz, cand_x, cand_y,\\n                                                          current_altitude_, wx, wy, ws);\\n                            float cp = 1.0f - std::exp(-lambda);'
)
print("CHANGE 3b: EFE caller fix applied (may need manual check)")

# ============ CPP CHANGE 4: Add Poisson parameters ============
old_cp = '    use_cp_ = getParam<bool>("opgsl.modules.cp", true);'
new_cp = '''    // Poisson filament arrival model parameters
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
if old_cp in cpp:
    cpp = cpp.replace(old_cp, new_cp)
    print("CHANGE 4: Poisson parameters added OK")

opens = cpp.count('{')
closes = cpp.count('}')
print("Final: braces open=%d close=%d" % (opens, closes))

# ============ Write CPP ============
with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.write(cpp)
print("OPGSL.cpp written")

# ============ HPP CHANGE: Add Poisson params ============
# Add to SourcePosterior3D class
old_reset = '        void reset();'
new_reset = '''        // Poisson model params (set by OPGSL::declareParameters)
        float poisson_lambda0_ = 2.0f;
        float poisson_ell_ = 2.5f;
        float poisson_alpha_w_ = 0.5f;
        float observation_dt_ = 1.0f;
        float detection_threshold_ = 0.005f;

        void reset();'''
if old_reset in hpp:
    hpp = hpp.replace(old_reset, new_reset)
    print("HPP CHANGE 1: Poisson params in SourcePosterior3D OK")

# Add to OPGSL class
old_edpa = '    bool use_edpa_=false; bool edpa_should_stop_=false; bool use_event_driven_posterior_=false;\n    float detection_threshold_=0.01f;\n    float arrival_rate_lambda0_=1.0f,arrival_rate_ell_=2.0f,arrival_rate_alphaw_=0.5f;'
new_edpa = '''    bool use_edpa_=false; bool edpa_should_stop_=false; bool use_event_driven_posterior_=false;

    // Poisson filament arrival model parameters
    float poisson_lambda0_ = 2.0f;
    float poisson_ell_ = 2.5f;
    float poisson_alpha_w_ = 0.5f;
    float observation_dt_ = 1.0f;
    float detection_threshold_ = 0.005f;'''
if old_edpa in hpp:
    hpp = hpp.replace(old_edpa, new_edpa)
    print("HPP CHANGE 2: Poisson params in OPGSL class OK")
else:
    print("WARNING: old_edpa pattern not found in hpp")
    # Try finding it
    idx = hpp.find('use_edpa_')
    if idx >= 0:
        print("  use_edpa_ found at position %d" % idx)
        print("  Context: %s" % repr(hpp[idx:idx+200]))

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp', 'w') as f:
    f.write(hpp)
print("OPGSL.hpp written")
print("ALL CHANGES APPLIED")