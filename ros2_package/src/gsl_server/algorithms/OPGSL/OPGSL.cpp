#include "OPGSL.hpp"
#include "gsl_server/core/GSLResult.hpp"
#include <gsl_server/algorithms/Common/States/WaitForMapState.hpp>
#include <gsl_server/algorithms/Common/States/WaitForGasState.hpp>
#include <gsl_server/algorithms/Common/States/StopAndMeasureState.hpp>
#include "gsl_server/core/Logging.hpp"
#include "gsl_server/core/Vectors.hpp"
#include "gsl_server/algorithms/Common/Utils/Math.hpp"
#include "gsl_server/algorithms/Common/Utils/RosUtils.hpp"
#include <angles/angles.h>
#include <cmath>
#include <iomanip>
#include <limits>
#include <numeric>
#include <filesystem>

namespace GSL {

// ============================================================
// SimpleGP Implementation
// ============================================================
float SimpleGP::getNextZ(float z_current, bool use_ucb) {
    if (xs_.empty()) return std::clamp(z_current, z_min_, z_max_);
    if (xs_.size() == 1) {
        float explore_z = z_current + 0.3f * ((best_z_ > z_current) ? 1.0f : -1.0f);
        return std::clamp(explore_z, z_min_, z_max_);
    }
    int n = xs_.size();
    Eigen::VectorXf y(n);
    for (int i = 0; i < n; i++) y(i) = ys_[i];
    Eigen::MatrixXf K(n, n);
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            K(i,j) = kernel(xs_[i], xs_[j]) + (i==j ? hyper_.noise_var : 0.0f);
    auto K_ldlt = K.ldlt();
    float best_score = -1e9f;
    float best_z = best_z_;
    int n_cand = 20;
    for (int i = 0; i <= n_cand; i++) {
        float z = z_min_ + (z_max_ - z_min_) * i / n_cand;
        Eigen::VectorXf k_star(n);
        for (int j = 0; j < n; j++) k_star(j) = kernel(z, xs_[j]);
        float mu = k_star.transpose() * K_ldlt.solve(y);
        float sigma2 = kernel(z, z) - k_star.transpose() * K_ldlt.solve(k_star);
        float sigma = std::sqrt(std::max(sigma2, 0.0f));
        float score = use_ucb ? (mu + 1.5f * sigma) : mu;
        if (score > best_score) { best_score = score; best_z = z; }
    }
    return std::clamp(best_z, z_min_, z_max_);
}

float SimpleGP::getNextZAnchored(float z_current, float anchor_z, float anchor_weight) {
    float gp_z = getNextZ(z_current, true);
    return std::clamp(gp_z * (1.0f - anchor_weight) + anchor_z * anchor_weight, z_min_, z_max_);
}

// ============================================================
// OPGSL Constructor & Parameters
// ============================================================
OPGSL::OPGSL(std::shared_ptr<rclcpp::Node> _node) : Algorithm(_node) { rng_.seed(std::random_device{}()); }

void OPGSL::declareParameters() {
    Algorithm::declareParameters();
    n_cells_ = getParam<int>("opgsl.grid.n_cells", 40);
    resolution_ = getParam<double>("opgsl.grid.resolution", 0.5);
    map_half_size_ = n_cells_ * resolution_ / 2.0f;
    convergence_entropy_threshold_ = getParam<double>("opgsl.convergence.entropy_threshold", 4.0);
    convergence_min_bouts_ = getParam<int>("opgsl.convergence.min_bouts", 5);
    convergence_stable_steps_ = getParam<int>("opgsl.convergence.stable_steps", 5);
    convergence_min_time_ = getParam<double>("opgsl.convergence.min_time", 30.0);
    audit_file_ = getParam<std::string>("opgsl.audit_file", "");
    mcos_observation_audit_file_ = getParam<std::string>(
        "opgsl.mcos.observation_audit_file", "");
    data_path_ = getParam<std::string>("opgsl.data_path", "");
    use_levy_ = getParam<bool>("opgsl.modules.levy", true);
    use_bout_ = getParam<bool>("opgsl.modules.bout", true);
    use_adaptive_step_ = getParam<bool>("opgsl.modules.adaptive_step", true);
    use_bhex_ = getParam<bool>("opgsl.modules.bhex", false);
    use_waz_ = getParam<bool>("opgsl.modules.waz", false);
    use_sc_ = getParam<bool>("opgsl.modules.sc", false);
    // Event-driven binary model parameters (Poisson filament arrival)
    posterior3d_.use_event_driven_ = getParam<bool>("opgsl.event_driven.enabled", false);
    posterior3d_.detection_threshold_ = getParam<float>("opgsl.event_driven.detection_threshold", 0.01f);
    posterior3d_.arrival_rate_lambda0_ = getParam<float>("opgsl.event_driven.lambda0", 2.0f);
    posterior3d_.arrival_rate_ell_ = getParam<float>("opgsl.event_driven.ell", 3.0f);
    posterior3d_.arrival_rate_alphaw_ = getParam<float>("opgsl.event_driven.alpha_w", 0.5f);
    use_edpa_ = getParam<bool>("opgsl.edpa.enabled", false);
    GSL_INFO("Event-driven model: enabled={} lambda0={:.1f} ell={:.1f} alpha_w={:.2f} threshold={:.3f}",
             posterior3d_.use_event_driven_, posterior3d_.arrival_rate_lambda0_, posterior3d_.arrival_rate_ell_, posterior3d_.arrival_rate_alphaw_, posterior3d_.detection_threshold_);

    use_upwind_tracking_ = getParam<bool>("opgsl.modules.upwind_tracking", true);
    // SBD module parameters
    use_sbd_ = getParam<bool>("opgsl.modules.sbd", false);
    int seed_param = getParam<int>("opgsl.seed", -1);
    if (seed_param >= 0) { GSL_INFO("Using deterministic seed={}", seed_param); }
    if (seed_param >= 0) {
        rng_.seed(seed_param);
        GSL_INFO("RNG seeded with param={}", seed_param);
    } else {
        rng_.seed(std::random_device{}());
        GSL_INFO("RNG seeded randomly");
    }
    use_cp_ = getParam<bool>("opgsl.modules.cp", true);
    cp_width_threshold_ = getParam<float>("opgsl.cp.width_threshold", 1.5f);
    cp_stable_required_ = getParam<int>("opgsl.cp.stable_steps", 3);
    CP::EProcessConfig cp_cfg;
    cp_cfg.delta = getParam<float>("opgsl.cp.alpha", 0.10f);
    cp_cfg.convergence_thresh = cp_width_threshold_;
    cp_cfg.stable_req = cp_stable_required_;
    cp_stopping_ = CP::EProcessStopping(cp_cfg);
    GSL_INFO("SBD DEBUG: use_sbd_={} use_cp_={}", use_sbd_, use_cp_);
    // DDM: Drift-Diffusion Model stopping parameters
    use_ddm_ = getParam<bool>("opgsl.modules.ddm", true);
    DDM::DDMConfig ddm_cfg;
    ddm_cfg.gamma_urgency = getParam<float>("opgsl.ddm.urgency", 0.005f);
    ddm_cfg.theta_min = getParam<float>("opgsl.ddm.theta_min", 1.5f);
    ddm_cfg.leak_lambda = getParam<float>("opgsl.ddm.leak", 0.05f);
    ddm_cfg.min_obs = getParam<int>("opgsl.ddm.min_obs", 25);
    ddm_cfg.min_time = getParam<float>("opgsl.ddm.min_time", 60.0f);
    ddm_stopping_ = DDM::DDMStopping(ddm_cfg);
    // W-RAIG: Risk-Aware Information Gain parameters
    use_wraig_ = getParam<bool>("opgsl.modules.wraig", true);
    wraig_cfg_.beta = getParam<float>("opgsl.wraig.beta", 0.5f);
    wraig_cfg_.n_ensemble = 3;
    wraig_.init(wraig_cfg_);
    GSL_INFO("DDM: enabled={} urgency={:.4f} | W-RAIG: enabled={} beta={:.2f}",
             use_ddm_, ddm_cfg.gamma_urgency, use_wraig_, wraig_cfg_.beta);
    eig_threshold_ = getParam<double>("opgsl.sbd.eig_threshold", 0.01);
    cusum_threshold_ = getParam<double>("opgsl.sbd.cusum_threshold", 5.0);
    cusum_drift_ = getParam<double>("opgsl.sbd.cusum_drift", 0.1);
    // SD-NBV toggles
    use_sdnbv_ = getParam<bool>("opgsl.sdnbv.enabled", true);
    use_gp_altitude_ = getParam<bool>("opgsl.altitude.gp", true);
    use_levy_altitude_ = getParam<bool>("opgsl.altitude.levy", true);
    use_layer_scan_ = getParam<bool>("opgsl.altitude.layer_scan", true);
    use_altitude_decay_ = getParam<bool>("opgsl.altitude.decay", true);
    z_min_ = getParam<double>("opgsl.altitude.z_min", -1.0);
    z_max_ = getParam<double>("opgsl.altitude.z_max", 3.0);
    GSL_INFO("OPGSL-ActiveInference params: grid={} res={:.1f} levy={} bout={} adaptive={} sdnbv={} gp_alt={} sbd={}",
             n_cells_, resolution_, use_levy_, use_bout_, use_adaptive_step_, use_sdnbv_, use_gp_altitude_, use_sbd_);
}

// ============================================================
// Initialize
// ============================================================
void OPGSL::Initialize() {
    field_cfg_.n_cells = n_cells_; field_cfg_.resolution = resolution_;
    field_cfg_.map_half_size = map_half_size_; field_cfg_.max_observations = 200;
    field_cfg_.observation_decay = 0.998f; field_cfg_.bandwidth_base = 1.2f;
    field_cfg_.bandwidth_wind_factor = 1.5f; field_cfg_.n_ensemble = 3;
    field_estimator_.init(field_cfg_);
    ig_cfg_.exploration_weight = 0.3f; ig_cfg_.wind_bonus = 0.5f;
    ig_cfg_.uncertainty_weight = 0.4f; ig_cfg_.visit_penalty = 0.2f;
    info_gain_.init(ig_cfg_);
    // SBD initialization
    if (use_sbd_) {
        eig_field_ = Eigen::MatrixXf::Zero(n_cells_, n_cells_);
        prev_posterior_ = Eigen::MatrixXf::Constant(n_cells_, n_cells_, -std::log((float)(n_cells_*n_cells_)));
        GSL_INFO("SBD MODULE ENABLED: eig_threshold={:.4f} cusum_threshold={:.1f} use_sbd={}", eig_threshold_, cusum_threshold_, use_sbd_);
    }
    waitForMapState = std::make_unique<WaitForMapState>(this);
    waitForGasState = std::make_unique<WaitForGasState>(this);
    stopAndMeasureState = std::make_unique<StopAndMeasureState>(this);
    movingState = std::make_unique<MovingStateOPGSL>(this);
    Algorithm::Initialize(); stateMachine.forceSetState(waitForMapState.get());
    prev_gas_ = 0.0f;
    best_hit_conc_ = 0.0f; best_hit_x_ = 0.0f; best_hit_y_ = 0.0f;
    run_length_ = 0.8f; run_direction_x_ = 0.0f; run_direction_y_ = -1.0f;
    run_steps_remaining_ = 0; tumble_count_ = 0; gradient_threshold_ = 0.002f;
    max_step_ = 1.0f; max_run_steps_ = 8; need_next_goal_ = false;
    bout_active_ = false; bout_start_time_ = 0.0f; bout_peak_conc_ = 0.0f;
    bout_count_ = 0; time_since_last_bout_ = 0.0f;
    step_size_ = 0.8f; prev_gradient_mag_ = 0.0f;
    levy_step_remaining_ = 0; levy_angle_ = 0.0f;
    bhex_stagnation_count_ = 0; waz_phase_ = 0; waz_step_count_ = 0;
    sc_mode_ = 0; sc_cast_dir_ = 1; sc_cast_legs_ = 0; sc_source_est_count_ = 0;
    sc_consecutive_hits_ = 0; sc_consecutive_misses_ = 0;
    bhex_temperature_ = 2.0f; bhex_best_conc_ = 0.0f; bhex_jump_pending_ = false;
    // Legacy EIG (disabled by default)
    use_eig_height_ = false;
    for (int k = 0; k < kNumHeights; k++) eig_height_posterior_[k] = 0.0f;
    eig_selected_height_ = 2.0f; eig_height_update_count_ = 0;
    // SD-NBV: Initialize 3D source posterior
    // Adaptive grid: read environment bounds from OccupancyGrid3D.csv
    {
        float emin_x=-5, emax_x=5, emin_y=-5, emax_y=5;
        if (!data_path_.empty()) {
            std::string occ_file = data_path_ + "/OccupancyGrid3D.csv";
            std::ifstream occf(occ_file);
            if (occf.is_open()) {
                std::string line;
                while (std::getline(occf, line)) {
                    if (line.rfind("#env_min", 0) == 0) {
                        auto pos = line.find(' ');
                        if (pos != std::string::npos) {
                            std::istringstream iss(line.substr(pos));
                            iss >> emin_x >> emin_y;
                        }
                    } else if (line.rfind("#env_max", 0) == 0) {
                        auto pos = line.find(' ');
                        if (pos != std::string::npos) {
                            std::istringstream iss(line.substr(pos));
                            iss >> emax_x >> emax_y;
                        }
                    }
                }
                occf.close();
                GSL_INFO("SDNBV: grid from OccupancyGrid: [{:.1f},{:.1f}]x[{:.1f},{:.1f}]", emin_x, emax_x, emin_y, emax_y);
            } else {
                GSL_WARN("SDNBV: OccupancyGrid not found at {}, using default [-5,5]", occ_file);
            }
        }
        // Adaptive n_cells: maintain ~0.4m resolution regardless of env size
        float env_w = emax_x - emin_x;
        float env_h = emax_y - emin_y;
        float target_res = 0.4f;
        int nx_auto = std::max(16, std::min(50, (int)(env_w / target_res)));
        int ny_auto = std::max(16, std::min(50, (int)(env_h / target_res)));
        int nz_auto = posterior3d_.nz_;
        posterior3d_.nx_ = nx_auto;
        posterior3d_.ny_ = ny_auto;
        GSL_INFO("SDNBV: adaptive grid {}x{}x{}, res ~{:.2f}m, bounds [{:.1f},{:.1f}]x[{:.1f},{:.1f}]",
                 nx_auto, ny_auto, nz_auto, target_res, emin_x, emax_x, emin_y, emax_y);
        posterior3d_.init(emin_x, emax_x, emin_y, emax_y, z_min_, z_max_);
    }
    // Altitude state (no state machine)
    current_altitude_ = 0.3f;
    gp_.reset(0.3f, z_min_, z_max_);
    levy_height_step_remaining_ = 0; levy_height_target_ = 0.3f;
    layer_profile_.clear(); significant_layers_.clear();
    calibration_active_ = false; calibration_step_ = 0;
    calibration_z_sequence_.clear(); calibration_index_ = 0;
    best_calibrated_z_ = 0.3f;
    for (int i = 0; i < kNumZBins; i++) z_posterior_[i] = 0.0f;
    z_conc_history_.clear();
    wind_dir_history_.clear();
    mcos_observation_history_.clear();
    mcos_last_observation_time_s_ = -1.0;
    mcos_have_previous_observation_ = false;
    if (!mcos_observation_audit_file_.empty()) {
        std::filesystem::path audit_path(mcos_observation_audit_file_);
        if (audit_path.has_parent_path()) {
            std::filesystem::create_directories(audit_path.parent_path());
        }
        mcos_observation_audit_stream_.open(
            mcos_observation_audit_file_, std::ios::out | std::ios::trunc);
        if (!mcos_observation_audit_stream_.is_open()) {
            GSL_ERROR("Cannot open MCOS observation audit file: {}",
                      mcos_observation_audit_file_);
        } else {
            mcos_observation_audit_stream_
                << "t_sim_s,x,y,z,gas_ppm,wind_x,wind_y,wind_speed,"
                   "position_delta_m,is_moving,time_monotone\n";
            mcos_observation_audit_stream_.flush();
        }
    }
    GSL_INFO("OPGSL-ActiveInference initialized: grid={} res={:.1f} z=[{:.1f},{:.1f}]",
             n_cells_, resolution_, z_min_, z_max_);
    initModuleActivationLogging();
}

// ============================================================
// SourcePosterior3D Implementation
// ============================================================
void OPGSL::SourcePosterior3D::init(float xmin, float xmax, float ymin, float ymax, float zmin, float zmax) {
    x_min_ = xmin; x_max_ = xmax; y_min_ = ymin; y_max_ = ymax;
    z_min_ = zmin; z_max_ = zmax;
    dx_ = (x_max_ - x_min_) / nx_;
    dy_ = (y_max_ - y_min_) / ny_;
    dz_ = (z_max_ - z_min_) / nz_;
    grid.resize(nx_, std::vector<std::vector<float>>(ny_, std::vector<float>(nz_, 0.0f)));
    reset();
    initialized_ = true;
}

void OPGSL::SourcePosterior3D::reset() {
    float log_prior = -std::log(static_cast<float>(nx_ * ny_ * nz_));
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++)
                grid[i][j][k] = log_prior;
}

float OPGSL::SourcePosterior3D::plumeLogLikelihood(float sx, float sy, float sz,
                                                     float cx, float cy, float cz,
                                                     float wind_x, float wind_y, float wind_speed) const {
    // ================================================================
    // ACTIVE INFERENCE GENERATIVE MODEL: Adaptive Anisotropic Kernel
    //
    // Replaces Gaussian plume (assumes steady uniform open-space flow)
    // with a wind-adaptive kernel for indoor environments:
    //   High wind -> anisotropic (aligned with wind, tight)
    //   Low wind  -> isotropic (diffusion-dominated, broad)
    //   No wind   -> pure distance decay
    //
    // Physical basis: In indoor environments, the key issue is NOT
    // low Peclet number (Pe~10^5 for VGR), but rather complex geometry
    // causing recirculation zones, intermittency, and non-Gaussian
    // concentration distributions. This kernel captures the essential
    // monotonic relationship (closer to source -> higher expected
    // concentration) without assuming a specific plume shape.
    // ================================================================

    float dx = cx - sx, dy = cy - sy, dz = cz - sz;
    float dist2 = dx*dx + dy*dy + dz*dz;
    float dist = std::sqrt(dist2);
    float wn = std::sqrt(wind_x*wind_x + wind_y*wind_y);

    // ---- No wind: isotropic exponential decay ----
    if (wn < 0.05f) {
        float beta = 0.4f;
        return -beta * dist - 0.15f * dist2;
    }

    // ---- Wind present: adaptive anisotropic kernel ----
    float wx = wind_x / wn, wy = wind_y / wn;
    float d_parallel = dx*wx + dy*wy;       // Along-wind component
    float d_perp_sq = dist2 - d_parallel*d_parallel;  // Cross-wind squared
    float dz_sq = dz*dz;

    // Anisotropy adapts to wind speed
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
}

float OPGSL::SourcePosterior3D::poissonRate(float sx, float sy, float cx, float cy,
                                             float wind_x, float wind_y, float wind_speed) const {
    // ============================================================
    // GBI-based Detection Probability (Generalized Bayesian Inference)
    //
    // Replaces the exponential decay model exp(-d/ell) with a logistic
    // detection probability that better matches indoor gas dispersion.
    //
    // Theory: Bissiri et al. 2016 (JRSS-B), Fong et al. 2021 (Biometrika)
    // The loss function does not need to be the true likelihood;
    // GBI guarantees convergence to the optimal approximation under
    // model misspecification when eta < 1.
    //
    // Key improvement over exp(-d/ell):
    // - exp(-d/1.0) at 3m = 0.05 (too low, misses real detections)
    // - sigmoid(-1.5*(d-3.0)) at 3m = 0.50 (matches GADEN observations)
    // ============================================================
    float dx = cx - sx, dy = cy - sy;
    float dist = std::sqrt(dx*dx + dy*dy);
    float wn = std::sqrt(wind_x*wind_x + wind_y*wind_y);

    // Logistic detection probability
    // d0 = 3.0m: characteristic detection range for indoor GADEN
    // gamma = 1.5: transition sharpness (higher = sharper boundary)
    float d0 = 1.5f;
    float gamma = 2.0f;
    float spatial = 1.0f / (1.0f + std::exp(gamma * (dist - d0)));

    // Wind modulation with confidence gating
    float wind_mod = 1.0f;
    if (wn > 0.05f && dist > 0.01f) {
        float cos_theta = (dx * wind_x + dy * wind_y) / (dist * wn);
        float alpha_w_eff = arrival_rate_alphaw_ * wind_confidence_;
        wind_mod = 1.0f + alpha_w_eff * cos_theta;
        wind_mod = std::max(wind_mod, 0.1f);
    }

    // Clamp to valid probability range
    return std::clamp(spatial * wind_mod, 0.01f, 0.99f);
}

void OPGSL::SourcePosterior3D::binaryEventUpdate(float cx, float cy, float cz,
                                                   float concentration, float detection_threshold,
                                                   float wind_x, float wind_y, float wind_speed) {
    if (!initialized_) return;
    bool detected = (concentration > detection_threshold);

    // === Adaptive decay based on wind stability ===
    // When wind is stable: decay=0.999 (trust history, ~100-step half-life)
    // When wind is chaotic: decay=0.99 (forget faster, ~30-step half-life)
    // Ge Quanbo: state-dependent random forgetting
    float decay = 0.99f + 0.009f * wind_confidence_;  // range [0.99, 0.999]
    for (int ii = 0; ii < nx_; ii++)
        for (int jj = 0; jj < ny_; jj++)
            for (int kk = 0; kk < nz_; kk++)
                grid[ii][jj][kk] *= decay;

    // === GBI Tempered Update (Bissiri et al. 2016, JRSS-B) ===
    //
    // Standard Bayes: p(s|data) propto p(s) * L(data|s)
    // Problem: when L is misspecified, posterior converges to wrong value.
    //
    // Generalized Bayes: p(s|data) propto p(s) * exp(-eta * loss(data, s))
    // eta in (0,1): tempering prevents over-commitment to misspecified model
    // eta -> 1: standard Bayes (trust model completely)
    // eta -> 0: ignore observation (trust prior)
    //
    // Our adaptive eta:
    // - Gas detected + stable wind: eta high (0.6-0.9) -> trust observation
    // - Gas detected + chaotic wind: eta medium -> partial trust
    // - No gas + stable wind: eta medium (0.15-0.5) -> non-detection informative
    // - No gas + chaotic wind: eta low -> non-detection unreliable
    float eta;
    if (detected) {
        eta = 0.6f + 0.3f * wind_confidence_;  // [0.6, 0.9]
    } else {
        eta = 0.15f + 0.35f * wind_confidence_;  // [0.15, 0.5]
    }
    float dt_measure = 3.0f;
    float max_log = -1e9f;
    for (int i = 0; i < nx_; i++) {
        for (int j = 0; j < ny_; j++) {
            for (int k = 0; k < nz_; k++) {
                float sx = x_min_ + (i+0.5f) * dx_;
                float sy = y_min_ + (j+0.5f) * dy_;
                float phi = poissonRate(sx, sy, cx, cy, wind_x, wind_y, wind_speed);
                // phi is now a valid probability in [0.01, 0.99]
                float log_lik;
                if (detected) {
                    log_lik = std::log(phi);         // log P(detect | source at s)
                } else {
                    log_lik = std::log(1.0f - phi);  // log P(no detect | source at s)
                }
                grid[i][j][k] += eta * log_lik;
                if (grid[i][j][k] > max_log) max_log = grid[i][j][k];
            }
        }
    }
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

void OPGSL::SourcePosterior3D::update(float cx, float cy, float cz, float concentration,
                                       float wind_x, float wind_y, float wind_speed) {
    if (!initialized_) return;
    // Dispatch to binary event model if enabled
    if (use_event_driven_) {
        binaryEventUpdate(cx, cy, cz, concentration, detection_threshold_, wind_x, wind_y, wind_speed);
        return;
    }
    // Temporal decay (adaptive to wind confidence)
    float decay = 0.98f + 0.015f * wind_confidence_;  // range [0.98, 0.995]
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
}

void OPGSL::SourcePosterior3D::getMAP(float& mx, float& my, float& mz) const {
    float best = -1e9f;
    int bi=0, bj=0, bk=0;
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++)
                if (grid[i][j][k] > best) { best = grid[i][j][k]; bi=i; bj=j; bk=k; }
    mx = x_min_ + (bi+0.5f) * dx_;
    my = y_min_ + (bj+0.5f) * dy_;
    mz = z_min_ + (bk+0.5f) * dz_;
}

float OPGSL::SourcePosterior3D::getEntropy() const {
    float H = 0.0f;
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++) {
                float p = std::exp(grid[i][j][k]);
                if (p > 1e-15f) H -= p * grid[i][j][k];
            }
    return H;
}

float OPGSL::SourcePosterior3D::getVariance() const {
    float mean_x = 0.0f, mean_y = 0.0f, mean_z = 0.0f, total = 0.0f;
    for (int i = 0; i < nx_; i++) {
        for (int j = 0; j < ny_; j++) {
            for (int k = 0; k < nz_; k++) {
                float p = std::exp(grid[i][j][k]);
                float x = x_min_ + (i + 0.5f) * dx_;
                float y = y_min_ + (j + 0.5f) * dy_;
                float z = z_min_ + (k + 0.5f) * dz_;
                total += p;
                mean_x += p * x; mean_y += p * y; mean_z += p * z;
            }
        }
    }
    if (total <= 1e-15f) return 0.0f;
    mean_x /= total; mean_y /= total; mean_z /= total;
    float variance = 0.0f;
    for (int i = 0; i < nx_; i++) {
        for (int j = 0; j < ny_; j++) {
            for (int k = 0; k < nz_; k++) {
                float p = std::exp(grid[i][j][k]) / total;
                float x = x_min_ + (i + 0.5f) * dx_;
                float y = y_min_ + (j + 0.5f) * dy_;
                float z = z_min_ + (k + 0.5f) * dz_;
                variance += p * ((x - mean_x) * (x - mean_x)
                               + (y - mean_y) * (y - mean_y)
                               + (z - mean_z) * (z - mean_z));
            }
        }
    }
    return variance;
}

void OPGSL::SourcePosterior3D::getMarginalEntropyPrecision(
    float& precision_x, float& precision_y, float& precision_z) const {
    // Legacy navigation heuristic only. Reciprocal marginal entropy is not a
    // Fisher matrix, has no score/Hessian construction, and cannot support a
    // CRLB or MCOS observability claim.
    // Compute marginal distributions
    std::vector<float> marg_x(nx_, 0.0f), marg_y(ny_, 0.0f), marg_z(nz_, 0.0f);
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++) {
                float p = std::exp(grid[i][j][k]);
                marg_x[i] += p; marg_y[j] += p; marg_z[k] += p;
            }
    auto entropy1d = [](const std::vector<float>& marg) -> float {
        float H = 0.0f;
        for (float p : marg) if (p > 1e-15f) H -= p * std::log(p);
        return H;
    };
    float Hx = entropy1d(marg_x);
    float Hy = entropy1d(marg_y);
    float Hz = entropy1d(marg_z);
    precision_x = 1.0f / (Hx + 0.1f);
    precision_y = 1.0f / (Hy + 0.1f);
    precision_z = 1.0f / (Hz + 0.1f);
}

OPGSL::SourcePosterior3D::NBVResult OPGSL::SourcePosterior3D::selectNBV(
    float robot_x, float robot_y, float robot_z,
    float wind_x, float wind_y, float wind_speed) const {
    NBVResult result;
    result.x = robot_x; result.y = robot_y; result.z = robot_z;
    result.expected_info_gain = -1e9f;
    // Get MAP as reference point
    float map_x, map_y, map_z;
    getMAP(map_x, map_y, map_z);
    // Evaluate candidate positions in a grid around the robot
    // Bug2 fix: dynamic search radius centered on MAP, not just robot
    float dist_to_map = std::sqrt((map_x-robot_x)*(map_x-robot_x) + (map_y-robot_y)*(map_y-robot_y));
    float search_radius = std::max(3.0f, dist_to_map * 1.2f + 2.0f);
    float step = 1.5f;  // Bug6 fix: larger step for faster NBV
    float best_eig = -1e9f;
    for (float dx = -search_radius; dx <= search_radius; dx += step) {
        for (float dy = -search_radius; dy <= search_radius; dy += step) {
            for (float dz = -0.5f; dz <= 1.5f; dz += 0.6f) {  // Bug6 fix: fewer z candidates
                // Bug2: search around midpoint of robot and MAP
                float center_x = 0.5f * robot_x + 0.5f * map_x;
                float center_y = 0.5f * robot_y + 0.5f * map_y;
                float cx = std::clamp(center_x + dx, x_min_ + 0.5f, x_max_ - 0.5f);
                float cy = std::clamp(center_y + dy, y_min_ + 0.5f, y_max_ - 0.5f);
                float cz = std::clamp(robot_z + dz, z_min_, z_max_);
                // Compute expected information gain
                float mean_c = 0.0f;
                for (int i = 0; i < nx_; i++)
                    for (int j = 0; j < ny_; j++)
                        for (int k = 0; k < nz_; k++) {
                            float sx = x_min_ + (i+0.5f) * dx_;
                            float sy = y_min_ + (j+0.5f) * dy_;
                            float sz = z_min_ + (k+0.5f) * dz_;
                            float p = std::exp(grid[i][j][k]);
                            float log_lik = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,
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
                            var_c += p * (c_pred - mean_c) * (c_pred - mean_c);
                        }
                float eig = var_c;
                float dist = std::sqrt(dx*dx + dy*dy + dz*dz);
                eig *= std::exp(-0.1f * dist);
                float upwind_bonus = -(dx*wind_x + dy*wind_y) / (wind_speed + 0.01f);
                if (wind_speed > 0.1f) eig *= std::exp(0.2f * upwind_bonus);
                if (eig > best_eig) {
                    best_eig = eig;
                    result.x = cx; result.y = cy; result.z = cz;
                    result.expected_info_gain = eig;
                }
            }
        }
    }
    return result;
}

// ============================================================
// SD-NBV Step: unified decision for next position
// ============================================================
void OPGSL::sdnbvStep(float& best_x, float& best_y) {
    float cx = currentRobotPosition.x, cy = currentRobotPosition.y;
    float wx = latest_wind_x_, wy = latest_wind_y_, ws = latest_wind_speed_;

    // V5.2: ALWAYS update posterior (even low gas = negative evidence)
    // Pass wind confidence to posterior for adaptive update strength
    posterior3d_.wind_confidence_ = wind_confidence_;
    posterior3d_.update(cx, cy, current_altitude_, std::max(latest_gas_, 0.0001f), wx, wy, ws);

    // ====== V5: Two-phase search strategy ======
    // Phase 1 (steps 1-15): Coarse exploration with large steps
    // Phase 2 (steps 16+): Fine convergence with NBV + concentration guidance
    
    // -- V5.2: Overshoot detection: require 3 consecutive drops --
    bool overshoot_detected = false;
    if (obs_history_c_.size() >= 7) {
        int n = obs_history_c_.size();
        // Find peak in last 7 readings
        float peak_c = 0; int peak_idx = 0;
        for (int i = n-7; i < n; i++) {
            if (obs_history_c_[i] > peak_c) { peak_c = obs_history_c_[i]; peak_idx = i; }
        }
        // Check for 3 consecutive drops after peak
        if (peak_idx < n-3 && peak_c > 0.05f) {
            bool three_drops = true;
            for (int i = peak_idx+1; i < n && i < peak_idx+4; i++) {
                if (obs_history_c_[i] >= obs_history_c_[i-1] * 0.8f) {
                    three_drops = false;
                    break;
                }
            }
            if (three_drops && latest_gas_ < peak_c * 0.3f) {
                overshoot_detected = true;
                float px = obs_history_x_[peak_idx], py = obs_history_y_[peak_idx];
                float dx = px - cx, dy = py - cy;
                float d = std::sqrt(dx*dx + dy*dy);
                if (d > 0.5f) {
                    float ret_step = std::min(1.5f, d * 0.5f);
                    best_x = cx + ret_step * dx / d;
                    best_y = cy + ret_step * dy / d;
                    clipToMapBounds(best_x, best_y);
                    GSL_INFO("SDNBV: SUSTAINED overshoot! returning to peak ({:.2f},{:.2f}) peak_c={:.3f}",
                             best_x, best_y, peak_c);
                    return;
                }
            }
        }
    }

    // -- EARLY MAP SWITCH: if posterior converged, go to MAP directly --
    {
        float H = posterior3d_.getEntropy();
        float H_max = std::log((float)(posterior3d_.nx_ * posterior3d_.ny_ * posterior3d_.nz_));
        float H_ratio = H / H_max;
        float precision_x, precision_y, precision_z;
        posterior3d_.getMarginalEntropyPrecision(
            precision_x, precision_y, precision_z);
        float min_precision = std::min({precision_x, precision_y, precision_z});
        if (H_ratio < 0.80f && min_precision > 0.4f && gas_hit_count_ >= 5 && step_count_ >= 3) {
            float map_x, map_y, map_z;
            posterior3d_.getMAP(map_x, map_y, map_z);
            float dx = map_x - cx, dy = map_y - cy;
            float d = std::sqrt(dx*dx + dy*dy);
            if (d > 0.3f) {
                float nav_step = std::min(1.5f, d * 0.7f);
                best_x = cx + nav_step * dx / d;
                best_y = cy + nav_step * dy / d;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-EARLY-MAP: ({:.2f},{:.2f}) H_ratio={:.2f} entropy_precision={:.3f} d={:.2f} step={}", best_x, best_y, H_ratio, min_precision, d, step_count_);
                return;
            }
        }
    }

    // -- Phase 1: Coarse downwind exploration (steps 1-6) --
    if (step_count_ <= 6) {
        float coarse_step = 1.2f;
        if ((step_count_ == 3 || step_count_ == 4) && ws > 0.1f) {
            float wn = std::sqrt(wx*wx + wy*wy);
            if (wn > 0.01f) {
                float perp_x = -wy / wn;
                float perp_y =  wx / wn;
                if (step_count_ == 4) { perp_x = -perp_x; perp_y = -perp_y; }
                best_x = cx + coarse_step * perp_x;
                best_y = cy + coarse_step * perp_y;
                clipToMapBounds(best_x, best_y);
                char tag = (step_count_==3) ? 'A' : 'B';
                GSL_INFO("SDNBV-P1: cross-wind-{} ({:.2f},{:.2f})", tag, best_x, best_y);
                return;
            }
        }
        if (best_hit_conc_ > 0.01f) {
            float dx = best_hit_x_ - cx, dy = best_hit_y_ - cy;
            float d = std::sqrt(dx*dx + dy*dy);
            if (d > 0.3f) {
                best_x = cx + std::min(coarse_step, d * 0.6f) * dx / d;
                best_y = cy + std::min(coarse_step, d * 0.6f) * dy / d;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-P1: best-hit ({:.2f},{:.2f}) d={:.2f} c={:.3f}", best_x, best_y, d, best_hit_conc_);
                return;
            }
        }
        if (ws > 0.05f) {
            float wn = std::sqrt(wx*wx + wy*wy);
            float down_x = -wx / wn, down_y = -wy / wn; // UPwind toward source
            float perp_x = -down_y, perp_y = down_x;
            float cross_offset = std::uniform_real_distribution<float>(-0.3f, 0.3f)(rng_);
            best_x = cx + coarse_step * down_x + cross_offset * perp_x;
            best_y = cy + coarse_step * down_y + cross_offset * perp_y;
        } else {
            float angle = step_count_ * 2.39996323f;
            float radius = std::min(0.8f + 0.2f * step_count_, 3.0f);
            best_x = -0.9f + radius * std::cos(angle);
            best_y = 0.15f + radius * std::sin(angle);
        }
        clipToMapBounds(best_x, best_y);
        GSL_INFO("SDNBV-P1: explore ({:.2f},{:.2f}) step={}", best_x, best_y, step_count_);
        return;
    }

    // -- Phase 1.5: Upwind plume-tracking with peak-based overshoot detection (steps 7-16) --
    // FIX V6.3: Use peak concentration tracking for overshoot detection
    // Peak-based: if current gas drops below 30% of peak seen during upwind, we passed source
    if (use_upwind_tracking_ && step_count_ >= 7 && step_count_ <= 16 && ws > 0.05f && gas_hit_count_ > 0) {
        // Find peak concentration from recent observations (last 8 readings)
        float peak_c = 0.0f;
        int peak_idx = -1;
        int hist_n = obs_history_c_.size();
        int lookback = std::min(8, hist_n);
        for (int i = hist_n - lookback; i < hist_n; i++) {
            if (obs_history_c_[i] > peak_c) {
                peak_c = obs_history_c_[i];
                peak_idx = i;
            }
        }
        
        // Overshoot: current gas dropped below 30% of recent peak, and peak was significant
        bool overshoot = (peak_c > 0.1f && latest_gas_ < peak_c * 0.3f && peak_idx >= 0);
        
        if (overshoot) {
            // Passed the source! Navigate back toward peak concentration position
            float px = obs_history_x_[peak_idx], py = obs_history_y_[peak_idx];
            float dx = px - cx, dy = py - cy;
            float d = std::sqrt(dx*dx + dy*dy);
            if (d > 0.3f) {
                float nav_step = std::min(1.2f, d * 0.5f);
                best_x = cx + nav_step * dx / d;
                best_y = cy + nav_step * dy / d;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-P1.5: OVERSHOOT! -> peak ({:.2f},{:.2f}) peak_c={:.3f} now={:.3f} d={:.2f}",
                         best_x, best_y, peak_c, latest_gas_, d);
            } else {
                best_x = px;
                best_y = py;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-P1.5: OVERSHOOT near peak ({:.2f},{:.2f}), switch Phase 2", best_x, best_y);
            }
            return;
        }
        
        // Normal upwind tracking
        float wn = std::sqrt(wx*wx + wy*wy);
        float upwind_x = -wx / wn;
        float upwind_y = -wy / wn;
        float nav_step = 0.8f;
        best_x = cx + nav_step * upwind_x;
        best_y = cy + nav_step * upwind_y;
        clipToMapBounds(best_x, best_y);
        GSL_INFO("SDNBV-P1.5: UPWIND ({:.2f},{:.2f}) ws={:.2f} c={:.3f} peak={:.3f}",
                 best_x, best_y, ws, latest_gas_, peak_c);
        return;
    }

    // ================================================================
    // Phase 2+ (steps 17+): Adaptive MAP/Gradient Switching
    // ================================================================
    // Auxiliary Innovation 1: Adaptive Phase Switching
    //
    // When posterior is confident (low entropy): use MAP navigation
    //   - MAP is theoretically optimal under the binary observation model
    //   - Posterior has converged, MAP is reliable
    //
    // When posterior is uncertain (high entropy): use concentration gradient
    //   - Gradient ascent is model-free and robust
    //   - Avoids MAP drift when posterior hasn't converged
    //
    // The switching threshold is calibrated from the binary observation model:
    //   - Entropy < H_threshold: posterior converged, use MAP
    //   - Entropy >= H_threshold: posterior uncertain, use gradient
    // ================================================================
    if (step_count_ >= 17) {
        // Compute posterior confidence metrics
        float H_current = posterior3d_.getEntropy();
        float H_max = std::log((float)(posterior3d_.nx_ * posterior3d_.ny_ * posterior3d_.nz_));
        float H_ratio = H_current / H_max;  // Normalized entropy in [0, 1]
        
        // Legacy reciprocal-marginal-entropy confidence heuristic.
        float precision_x, precision_y, precision_z;
        posterior3d_.getMarginalEntropyPrecision(
            precision_x, precision_y, precision_z);
        float min_precision = std::min({precision_x, precision_y, precision_z});
        
        // Decision: MAP or Gradient?
        bool use_map = (H_ratio < 0.85f) && (min_precision > 0.3f);
        
        if (use_map) {
            // ===== MAP Navigation (posterior confident) =====
            float map_x, map_y, map_z;
            posterior3d_.getMAP(map_x, map_y, map_z);
            float dx = map_x - cx, dy = map_y - cy;
            float d = std::sqrt(dx*dx + dy*dy);
            if (d > 0.3f) {
                float nav_step = std::min(1.0f, d * 0.6f);
                best_x = cx + nav_step * dx / d;
                best_y = cy + nav_step * dy / d;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-ADAPT: MAP ({:.2f},{:.2f}) H_ratio={:.2f} min_entropy_precision={:.3f} d={:.2f}",
                         best_x, best_y, H_ratio, min_precision, d);
            } else {
                // Near MAP, stop
                GSL_INFO("SDNBV-ADAPT: near MAP ({:.2f},{:.2f}) d={:.2f}", map_x, map_y, d);
            }
            return;
        } else {
            // ===== Concentration Gradient Ascent (posterior uncertain) =====
            // Compute gradient from recent observations
            int hist_n = obs_history_c_.size();
            float grad_x = 0.0f, grad_y = 0.0f;
            int grad_window = std::min(6, hist_n);
            if (grad_window >= 2) {
                for (int i = hist_n - grad_window; i < hist_n - 1; i++) {
                    float dc = obs_history_c_[i+1] - obs_history_c_[i];
                    float ddx = obs_history_x_[i+1] - obs_history_x_[i];
                    float ddy = obs_history_y_[i+1] - obs_history_y_[i];
                    float dd = std::sqrt(ddx*ddx + ddy*ddy);
                    if (dd > 0.01f) {
                        grad_x += dc * ddx / dd;
                        grad_y += dc * ddy / dd;
                    }
                }
            }
            float grad_mag = std::sqrt(grad_x*grad_x + grad_y*grad_y);
            
            // Overshoot detection for gradient mode
            float peak_c = 0.0f;
            int peak_idx = -1;
            for (int i = 0; i < hist_n; i++) {
                if (obs_history_c_[i] > peak_c) {
                    peak_c = obs_history_c_[i];
                    peak_idx = i;
                }
            }
            bool grad_overshoot = (peak_c > 0.05f && latest_gas_ < peak_c * 0.3f && peak_idx >= 0);
            
            if (grad_overshoot && peak_idx >= 0) {
                // Overshoot! Navigate back toward peak
                float px = obs_history_x_[peak_idx], py = obs_history_y_[peak_idx];
                float dx = px - cx, dy = py - cy;
                float d = std::sqrt(dx*dx + dy*dy);
                if (d > 0.3f) {
                    float nav_step = std::min(1.0f, d * 0.5f);
                    best_x = cx + nav_step * dx / d;
                    best_y = cy + nav_step * dy / d;
                    clipToMapBounds(best_x, best_y);
                    GSL_INFO("SDNBV-ADAPT: GRAD OVERSHOOT -> peak ({:.2f},{:.2f}) peak={:.3f} now={:.3f}",
                             best_x, best_y, peak_c, latest_gas_);
                }
                return;
            }
            
            if (latest_gas_ > 0.01f && grad_mag > 0.001f) {
                // Gas detected: follow gradient
                float nav_step = std::min(1.0f, std::max(0.3f, 1.0f - latest_gas_));
                best_x = cx + nav_step * grad_x / grad_mag;
                best_y = cy + nav_step * grad_y / grad_mag;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-ADAPT: GRAD ({:.2f},{:.2f}) c={:.3f} grad_mag={:.4f} H_ratio={:.2f}",
                         best_x, best_y, latest_gas_, grad_mag, H_ratio);
                return;
            } else if (best_hit_conc_ > 0.01f) {
                // No current gas but have past hit: navigate toward it
                float dx = best_hit_x_ - cx, dy = best_hit_y_ - cy;
                float d = std::sqrt(dx*dx + dy*dy);
                if (d > 0.3f) {
                    float nav_step = std::min(0.8f, d * 0.5f);
                    best_x = cx + nav_step * dx / d;
                    best_y = cy + nav_step * dy / d;
                    clipToMapBounds(best_x, best_y);
                    GSL_INFO("SDNBV-ADAPT: best-hit ({:.2f},{:.2f}) c={:.3f} d={:.2f}",
                             best_x, best_y, best_hit_conc_, d);
                }
                return;
            } else {
                // No gas: go upwind
                if (ws > 0.05f) {
                    float wn = std::sqrt(wx*wx + wy*wy);
                    best_x = cx + 0.8f * (-wx / wn);
                    best_y = cy + 0.8f * (-wy / wn);
                    clipToMapBounds(best_x, best_y);
                    GSL_INFO("SDNBV-ADAPT: UPWIND ({:.2f},{:.2f}) ws={:.2f}",
                             best_x, best_y, ws);
                }
                return;
            }
        }
    }
}

void OPGSL::computeEIGField() {
    auto& ensemble = field_estimator_.ensembleFields();
    int n_e = field_estimator_.ensembleSize();
    if (n_e == 0 || eig_field_.rows() == 0) return;

    int rows = std::min((int)eig_field_.rows(), (int)ensemble[0].rows());
    int cols = std::min((int)eig_field_.cols(), (int)ensemble[0].cols());
    eig_field_.setZero();

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            float eig = 0.0f;
            float p_marginal = 0.0f;
            std::vector<float> p_e(n_e);
            for (int e = 0; e < n_e; e++) {
                float log_val = ensemble[e](i, j);
                p_e[e] = 1.0f / (1.0f + std::exp(-std::clamp(log_val, -20.0f, 20.0f)));
                p_marginal += p_e[e];
            }
            p_marginal /= n_e;

            for (int e = 0; e < n_e; e++) {
                float pe = p_e[e];
                if (pe > 1e-7f && pe < 1.0f - 1e-7f && p_marginal > 1e-7f && p_marginal < 1.0f - 1e-7f) {
                    eig += (1.0f / n_e) * (
                        pe * std::log(pe / p_marginal) +
                        (1.0f - pe) * std::log((1.0f - pe) / (1.0f - p_marginal))
                    );
                }
            }
            eig_field_(i, j) = eig;
        }
    }
}

float OPGSL::computePosteriorKL(const Eigen::MatrixXf& prev, const Eigen::MatrixXf& curr) {
    if (prev.rows() == 0) return 0.0f;
    float kl = 0.0f;
    int N = prev.rows();
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            float p = std::exp(prev(i, j));
            float q = std::exp(curr(i, j));
            if (p > 1e-10f && q > 1e-10f) {
                kl += p * std::log(p / q);
            }
        }
    }
    return kl;
}


void OPGSL::computeWRAIGField() {
    if (!use_wraig_ || eig_field_.rows() == 0) return;
    auto& ensemble = field_estimator_.ensembleFields();
    int n_e = ensemble.size();
    if (n_e < 2) return;

    int rows = eig_field_.rows();
    int cols = eig_field_.cols();
    wraig_field_ = Eigen::MatrixXf::Zero(rows, cols);

    // For each grid cell, compute EIG for each ensemble member
    std::vector<Eigen::MatrixXf> ensemble_eig(n_e);
    for (int e = 0; e < n_e; e++) {
        ensemble_eig[e] = Eigen::MatrixXf::Zero(rows, cols);
    }

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            float p_marginal = 0.0f;
            std::vector<float> p_e(n_e);
            for (int e = 0; e < n_e; e++) {
                float log_val = ensemble[e](i, j);
                p_e[e] = 1.0f / (1.0f + std::exp(-std::clamp(log_val, -20.0f, 20.0f)));
                p_marginal += p_e[e];
            }
            p_marginal /= n_e;
            for (int e = 0; e < n_e; e++) {
                float pe = p_e[e];
                float eig = 0.0f;
                if (pe > 1e-7f && pe < 1.0f - 1e-7f && p_marginal > 1e-7f && p_marginal < 1.0f - 1e-7f) {
                    eig = pe * std::log(pe / p_marginal) +
                          (1.0f - pe) * std::log((1.0f - pe) / (1.0f - p_marginal));
                }
                ensemble_eig[e](i, j) = eig;
            }
        }
    }
    wraig_.computeField(ensemble_eig, wraig_field_);
    GSL_INFO("W-RAIG field computed: beta={:.2f}", wraig_cfg_.beta);
}

void OPGSL::infotaxisStep(float& best_x, float& best_y) {
    sdnbvStep(best_x, best_y);
}

// ============================================================
// Gas & Wind Processing
// ============================================================
void OPGSL::recordMCOSObservationAudit(
    double t_sim_s, float x, float y, float z, float gas,
    float wind_x, float wind_y, float wind_speed) {
    float position_delta = 0.0f;
    if (mcos_have_previous_observation_) {
        float dx = x - mcos_last_observation_x_;
        float dy = y - mcos_last_observation_y_;
        float dz = z - mcos_last_observation_z_;
        position_delta = std::sqrt(dx*dx + dy*dy + dz*dz);
    }
    bool time_monotone = (
        !mcos_have_previous_observation_ || t_sim_s > mcos_last_observation_time_s_);
    MCOSObservationAuditRecord record{
        t_sim_s, x, y, z, gas, wind_x, wind_y, wind_speed,
        position_delta, time_monotone};
    mcos_observation_history_.push_back(record);
    if (mcos_observation_history_.size() > 5000) {
        mcos_observation_history_.pop_front();
    }
    if (mcos_observation_audit_stream_.is_open()) {
        mcos_observation_audit_stream_
            << std::fixed << std::setprecision(6)
            << t_sim_s << ',' << x << ',' << y << ',' << z << ','
            << gas << ',' << wind_x << ',' << wind_y << ',' << wind_speed << ','
            << position_delta << ',' << (position_delta > 1e-6f ? 1 : 0) << ','
            << (time_monotone ? 1 : 0) << '\n';
        mcos_observation_audit_stream_.flush();
    }
    if (!time_monotone) {
        GSL_ERROR("MCOS observation time is nonmonotone: current={} previous={}",
                  t_sim_s, mcos_last_observation_time_s_);
    }
    mcos_last_observation_time_s_ = t_sim_s;
    mcos_last_observation_x_ = x;
    mcos_last_observation_y_ = y;
    mcos_last_observation_z_ = z;
    mcos_have_previous_observation_ = true;
}

void OPGSL::processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection) {
    // Guard: stop processing after convergence reported
    if (convergence_reported_) return;
    total_measurements_++;
    latest_gas_ = static_cast<float>(concentration);
    latest_wind_speed_ = static_cast<float>(windSpeed);
    latest_wind_x_ = static_cast<float>(windSpeed * std::cos(windDirection));
    latest_wind_y_ = static_cast<float>(windSpeed * std::sin(windDirection));

    float cx = currentRobotPosition.x, cy = currentRobotPosition.y;
    float cz = current_altitude_;
    // Use the algorithm-relative clock so audit traces align with the
    // measurement trace; node->now() is wall-clock time in these runs.
    double observation_time_s = static_cast<double>(elapsed_time_);
    recordMCOSObservationAudit(
        observation_time_s, cx, cy, cz, latest_gas_, latest_wind_x_,
        latest_wind_y_, latest_wind_speed_);

    // Update field estimator
    field_estimator_.addObservation(latest_gas_, cx, cy, latest_wind_x_, latest_wind_y_, elapsed_time_);

    // CP: update confidence region
    if (use_cp_) {
        float mx, my, mz;
        posterior3d_.getMAP(mx, my, mz);
        cp_region_.addMAP(mx, my, mz);
        // BUG-1 fix: use member variables instead of static
        float residual = std::sqrt((mx - cp_prev_mx_) * (mx - cp_prev_mx_) + (my - cp_prev_my_) * (my - cp_prev_my_));
        cp_stopping_.addObs(residual);
        cp_prev_mx_ = mx; cp_prev_my_ = my;
    }

    // DDM: accumulate evidence for stopping decision (FIXED: posterior entropy change rate)
    // Fix: old formula had step-1 false positive (map_move=0, gas high -> huge LLR)
    // New: posterior-based LLR with warm-up period
    if (use_ddm_) {
        float mx, my, mz;
        posterior3d_.getMAP(mx, my, mz);
        float map_move = std::sqrt((mx - ddm_prev_map_x_) * (mx - ddm_prev_map_x_) +
                                    (my - ddm_prev_map_y_) * (my - ddm_prev_map_y_));

        // Warm-up: don't accumulate evidence in first 5 steps
        // The posterior needs time to burn in before we trust its state
        if (step_count_ > 5) {
            // Posterior change rate: negative when converging (good)
            float posterior_change = map_move;

            // Gas evidence: only matters if posterior is still moving
            // If posterior is stable AND gas is consistent -> source found
            float gas_consistency = 0.0f;
            if (map_move < 0.5f) {  // Posterior is relatively stable
                // Check if gas readings are consistent with source at MAP
                float dist_to_map = std::sqrt((cx - mx)*(cx - mx) + (cy - my)*(cy - my));
                float expected_conc = std::exp(-dist_to_map * dist_to_map / 2.0f);
                gas_consistency = latest_gas_ * expected_conc;
            }

            // LLR: evidence FOR convergence
            // Positive when: posterior stable AND gas consistent
            // Negative when: posterior still moving
            float llr = gas_consistency - 0.5f * posterior_change;

            ddm_stopping_.addObservation(llr, elapsed_time_);
        }

        ddm_prev_map_x_ = mx;
        ddm_prev_map_y_ = my;
    }

    // Update altitude posterior
    updateAltitudePosterior(cz, latest_gas_);

    // Update GP with current observation
    if (use_gp_altitude_ && latest_gas_ > 0.001f && calibration_count_ > 0) {
        gp_.addObservation(cz, latest_gas_);
    }

    // Track max concentration
    if (latest_gas_ > best_hit_conc_) {
        best_hit_conc_ = latest_gas_;
        best_hit_x_ = cx; best_hit_y_ = cy;
    }

    // Bout detection (Module 2)
    if (use_bout_) {
        if (latest_gas_ > 0.01f) {
            if (!bout_active_) {
                bout_active_ = true;
                bout_start_time_ = elapsed_time_;
                bout_peak_conc_ = latest_gas_;
            } else {
                bout_peak_conc_ = std::max(bout_peak_conc_, latest_gas_);
            }
            consecutive_misses_ = 0;
            gas_hit_count_++;
            last_hit_x_ = cx; last_hit_y_ = cy;
            last_hit_time_ = elapsed_time_;
        } else {
            if (bout_active_) {
                bout_active_ = false;
                bout_count_++;
                time_since_last_bout_ = 0.0f;
            }
            consecutive_misses_++;
            time_since_last_bout_ += 1.0f;
        }
    } else {
        if (latest_gas_ > 0.01f) {
            gas_hit_count_++;
            last_hit_x_ = cx; last_hit_y_ = cy;
            consecutive_misses_ = 0;
        } else {
            consecutive_misses_++;
        }
    }

    // Wind history
    wind_dir_history_.push_back(windDirection);
    if (wind_dir_history_.size() > kWindHistorySize) wind_dir_history_.pop_front();
    
    // Compute wind direction confidence (circular variance)
    // R_t = |1/L * sum(exp(i*theta_k))| in [0,1]
    // R_t ~ 1: stable direction, R_t ~ 0: chaotic
    {
        float sx = 0.0f, sy = 0.0f;
        for (float d : wind_dir_history_) { sx += std::cos(d); sy += std::sin(d); }
        float L = (float)wind_dir_history_.size();
        wind_confidence_ = std::sqrt(sx*sx + sy*sy) / std::max(L, 1.0f);
    }

    // Adaptive step (Module 3)
    if (use_adaptive_step_) {
        float gradient_mag = std::abs(latest_gas_ - prev_gas_);
        if (gradient_mag > prev_gradient_mag_ * 1.2f) {
            step_size_ = std::max(0.3f, step_size_ * 0.85f);
        } else if (gradient_mag < prev_gradient_mag_ * 0.5f && gradient_mag > 0.001f) {
            step_size_ = std::min(1.5f, step_size_ * 1.1f);
        }
        prev_gradient_mag_ = gradient_mag;
    }

    // Z conc history
    z_conc_history_.push_back({cz, latest_gas_, elapsed_time_});
    if (z_conc_history_.size() > max_conc_window_) z_conc_history_.pop_front();

    // Layer scan processing
    if (calibration_active_) {
        processCalibrationMeasurement(cz, latest_gas_);
    }

    // Record observation history for gradient estimation
    obs_history_x_.push_back(cx);
    obs_history_y_.push_back(cy);
    obs_history_c_.push_back(latest_gas_);
    if ((int)obs_history_x_.size() > 30) {
        obs_history_x_.erase(obs_history_x_.begin());
        obs_history_y_.erase(obs_history_y_.begin());
        obs_history_c_.erase(obs_history_c_.begin());
    }
    prev_gas_ = latest_gas_;

    // Trigger navigation after measurement
    auto check = checkSourceFound();
    if (check != GSLResult::Running) {
        GSL_INFO("OPGSL-SDNBV: search complete, result={}", (int)check);
        saveResultsToFile(check);
        return;
    }
    movingState->chooseGoalAndMove();
}

// ============================================================
// Legacy altitude selection (reciprocal marginal-entropy heuristic)
// ============================================================
float OPGSL::selectTargetAltitude() {
    float precision_x, precision_y, precision_z;
    posterior3d_.getMarginalEntropyPrecision(
        precision_x, precision_y, precision_z);

    // Lower reciprocal entropy means greater marginal uncertainty.
    bool z_needs_exploration = (
        precision_z * 1.5f < std::min(precision_x, precision_y));

    // If calibration hasn't been done yet and enough steps, start it
    if (use_layer_scan_ && step_count_ > 10 && calibration_count_ < 1 && !calibration_active_) {
        startCalibration();
    }

    // If actively calibrating, follow calibration sequence
    if (calibration_active_) {
        if (calibration_index_ < calibration_z_sequence_.size()) {
            return calibration_z_sequence_[calibration_index_];
        } else {
            calibration_active_ = false;
            calibration_count_++;
            best_calibrated_z_ = getPosteriorBestZ();
            GSL_INFO("SDNBV calibration done: best_z={:.2f}", best_calibrated_z_);
        }
    }

    // SD-NBV altitude with height exploration for unknown source altitude
    // During initial steps without gas, sweep through heights to find plume
    float sweep_heights[] = {0.3f, 0.0f, -0.3f, 0.5f, 1.0f, 0.3f};
    float target_z = (step_count_ <= 6 && gas_hit_count_ == 0)
        ? std::clamp(sweep_heights[step_count_ % 6], z_min_, z_max_)
        : 0.3f;
    float gp_z = use_gp_altitude_ ? gp_.getNextZAnchored(current_altitude_, best_calibrated_z_, 0.3f) : current_altitude_;
    float post_z = getPosteriorBestZ();
    float maxc_z = maxConcAltitude();

    // Weighted combination based on data availability
    if (gp_.getXS().size() >= 3) {
        // GP has enough data: trust it more
        target_z = 0.5f * gp_z + 0.3f * post_z + 0.2f * maxc_z;
    } else if (z_needs_exploration) {
        // Z dimension uncertain: use Lévy exploration
        target_z = levyHeight(current_altitude_);
    } else {
        // Default: use posterior + max concentration
        target_z = 0.6f * post_z + 0.4f * maxc_z;
    }

    // If we have calibrated, blend in the calibrated value
    if (calibration_count_ > 0) {
        target_z = 0.5f * target_z + 0.5f * best_calibrated_z_;
    }

    return std::clamp(target_z, z_min_, z_max_);
}

// ============================================================
// Levy Flight
// ============================================================
void OPGSL::levyExploration(float& best_x, float& best_y, float cx, float cy) {
    if (levy_step_remaining_ <= 0) {
        // New Levy step
        std::uniform_real_distribution<float> udist(0.0f, 1.0f);
        float u = udist(rng_);
        float beta = 2.0f, l_min = 0.3f, l_max = 3.0f;
        float exponent = 1.0f / (beta - 1.0f);
        float l = l_min * std::pow(1.0f - u * (1.0f - std::pow(l_min/l_max, beta-1.0f)), -exponent);
        levy_step_remaining_ = std::max(1, int(l / 0.5f));
        levy_angle_ = std::uniform_real_distribution<float>(0, 2*M_PI)(rng_);
    }
    float dist = step_size_;
    best_x = cx + dist * std::cos(levy_angle_);
    best_y = cy + dist * std::sin(levy_angle_);
    clipToMapBounds(best_x, best_y);
    levy_step_remaining_--;
}

float OPGSL::levyHeight(float z_current) {
    if (levy_height_step_remaining_ <= 0) {
        std::uniform_real_distribution<float> udist(0.0f, 1.0f);
        float u = udist(rng_);
        float beta = 2.0f, l_min = 0.2f, l_max = 2.0f;
        float exponent = 1.0f / (beta - 1.0f);
        float l = l_min * std::pow(1.0f - u * (1.0f - std::pow(l_min/l_max, beta-1.0f)), -exponent);
        levy_height_step_remaining_ = std::max(1, int(l / 0.3f));
        float dir = (udist(rng_) > 0.5f) ? 1.0f : -1.0f;
        levy_height_target_ = std::clamp(z_current + dir * l, z_min_, z_max_);
    }
    levy_height_step_remaining_--;
    return levy_height_target_;
}

// ============================================================
// Calibration (layer scan)
// ============================================================
void OPGSL::startCalibration() {
    calibration_active_ = true;
    calibration_step_ = 0;
    calibration_z_sequence_.clear();
    // Sweep from z_min to z_max
    for (float z = z_min_; z <= z_max_; z += 0.3f) {
        calibration_z_sequence_.push_back(z);
    }
    calibration_index_ = 0;
    GSL_INFO("SDNBV calibration started: {} z levels", calibration_z_sequence_.size());
}

void OPGSL::processCalibrationMeasurement(float z, float concentration) {
    layer_profile_.push_back({z, concentration});
    if (calibration_index_ < calibration_z_sequence_.size()) {
        calibration_index_++;
    }
}

// ============================================================
// Altitude helpers
// ============================================================
void OPGSL::updateAltitudePosterior(float z, float concentration) {
    int bin = std::clamp(int((z - z_min_) / (z_max_ - z_min_) * kNumZBins), 0, kNumZBins-1);
    // Temporal decay
    for (int i = 0; i < kNumZBins; i++) z_posterior_[i] *= (1.0f - z_decay_rate_);
    // Update with concentration
    z_posterior_[bin] += concentration;
}

float OPGSL::getPosteriorBestZ() const {
    int best_bin = 0;
    float best_val = -1e9f;
    for (int i = 0; i < kNumZBins; i++) {
        if (z_posterior_[i] > best_val) { best_val = z_posterior_[i]; best_bin = i; }
    }
    return z_min_ + (best_bin + 0.5f) * (z_max_ - z_min_) / kNumZBins;
}

float OPGSL::maxConcAltitude() const {
    if (z_conc_history_.empty()) return current_altitude_;
    float best_z = z_conc_history_[0].z;
    float best_c = z_conc_history_[0].concentration;
    for (const auto& rec : z_conc_history_) {
        if (rec.concentration > best_c) { best_c = rec.concentration; best_z = rec.z; }
    }
    return best_z;
}

// ============================================================
// Utilities
// ============================================================
float OPGSL::smoothWindDirection() const {
    if (wind_dir_history_.empty()) return 0.0f;
    float sx = 0.0f, sy = 0.0f;
    for (float d : wind_dir_history_) { sx += std::cos(d); sy += std::sin(d); }
    return std::atan2(sy, sx);
}

void OPGSL::clipToMapBounds(float& x, float& y) const {
    float margin = 0.5f;
    x = std::clamp(x, -map_half_size_ + margin, map_half_size_ - margin);
    y = std::clamp(y, -map_half_size_ + margin, map_half_size_ - margin);
}

void OPGSL::logAltitudeState() {
    float precision_x, precision_y, precision_z;
    posterior3d_.getMarginalEntropyPrecision(
        precision_x, precision_y, precision_z);
    float map_x, map_y, map_z;
    posterior3d_.getMAP(map_x, map_y, map_z);
    GSL_INFO("SDNBV-Alt: z={:.2f} post_MAP=({:.2f},{:.2f},{:.2f}) entropy_precision=({:.2f},{:.2f},{:.2f}) gp_best={:.2f}",
             current_altitude_, map_x, map_y, map_z,
             precision_x, precision_y, precision_z, gp_.getBestZ());
}

// ============================================================
// Optional modules (BH-EX, WAZ, SC) - kept for ablation
// ============================================================
void OPGSL::bhexCheckStagnation(float current_conc, float cx, float cy) {
    if (current_conc > bhex_best_conc_) {
        bhex_best_conc_ = current_conc; bhex_best_x_ = cx; bhex_best_y_ = cy;
        bhex_stagnation_count_ = 0;
    } else {
        bhex_stagnation_count_++;
    }
    if (bhex_stagnation_count_ >= bhex_stagnation_threshold_) {
        bhex_jump_pending_ = true;
        bhex_jump_x_ = cx + std::normal_distribution<float>(0, bhex_temperature_)(rng_);
        bhex_jump_y_ = cy + std::normal_distribution<float>(0, bhex_temperature_)(rng_);
        clipToMapBounds(bhex_jump_x_, bhex_jump_y_);
        bhex_temperature_ *= bhex_cooling_;
        bhex_stagnation_count_ = 0;
    }
}

void OPGSL::wazExplore(float& out_x, float& out_y, float cx, float cy) {
    float wind_dir = smoothWindDirection();
    float perp = wind_dir + M_PI/2.0f;
    if (waz_phase_ == 0) {
        out_x = cx + waz_step_size_ * std::cos(perp);
        out_y = cy + waz_step_size_ * std::sin(perp);
    } else {
        out_x = cx - waz_step_size_ * std::cos(perp);
        out_y = cy - waz_step_size_ * std::sin(perp);
    }
    waz_step_count_++;
    if (waz_step_count_ >= waz_steps_per_leg_) {
        waz_phase_ = 1 - waz_phase_;
        waz_step_count_ = 0;
    }
    clipToMapBounds(out_x, out_y);
}

void OPGSL::scStep(float& out_x, float& out_y, float cx, float cy) {
    // Surge-Cast plume tracking
    if (latest_gas_ > 0.01f) {
        sc_consecutive_hits_++;
        sc_consecutive_misses_ = 0;
        if (sc_mode_ == 1) { sc_mode_ = 0; sc_cast_legs_ = 0; }
        float wind_dir = std::atan2(latest_wind_y_, latest_wind_x_);
        out_x = cx + sc_surge_step_ * std::cos(wind_dir);
        out_y = cy + sc_surge_step_ * std::sin(wind_dir);
        sc_source_est_x_ = 0.9f * sc_source_est_x_ + 0.1f * cx;
        sc_source_est_y_ = 0.9f * sc_source_est_y_ + 0.1f * cy;
        sc_source_est_count_++;
    } else {
        sc_consecutive_misses_++;
        sc_consecutive_hits_ = 0;
        if (sc_consecutive_misses_ > 3) sc_mode_ = 1;
        if (sc_mode_ == 1) {
            float wind_dir = std::atan2(latest_wind_y_, latest_wind_x_);
            float perp = wind_dir + M_PI/2.0f * sc_cast_dir_;
            out_x = cx + sc_cast_step_ * std::cos(perp);
            out_y = cy + sc_cast_step_ * std::sin(perp);
            sc_cast_legs_++;
            if (sc_cast_legs_ > 5) { sc_cast_dir_ *= -1; sc_cast_legs_ = 0; }
        }
    }
    clipToMapBounds(out_x, out_y);
}

// ============================================================
// Convergence & Results
// ============================================================
GSLResult OPGSL::checkSourceFound() {
    // V5: Relaxed early constraints for faster convergence
    if (convergence_reported_) return GSLResult::Success;
    if (elapsed_time_ < 5.0f) return GSLResult::Running;
    if (gas_hit_count_ < 3) return GSLResult::Running;
    if (step_count_ < 5) return GSLResult::Running;

    auto field = field_estimator_.computeField();
    float cx = currentRobotPosition.x, cy = currentRobotPosition.y;
    float map_x, map_y, map_z;
    posterior3d_.getMAP(map_x, map_y, map_z);
    float dx = map_x - cx, dy = map_y - cy;
    float dist_to_peak = std::sqrt(dx*dx + dy*dy);
    float dz = std::abs(map_z - current_altitude_);

    // BUG-5 fix: Actually use CP stopping criterion
    if (use_cp_ && cp_stopping_.shouldStop()) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("CP-STOP: converged at step={} MAP=({:.2f},{:.2f},{:.2f}) width={:.3f}",
                 step_count_, mx, my, mz, cp_stopping_.getWidth());
        convergence_reported_ = true; return GSLResult::Success;
    }

    // DDM: Drift-Diffusion Model evidence-accumulation stopping
    if (use_ddm_ && ddm_stopping_.shouldStop()) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("DDM-STOP: converged at step={} MAP=({:.2f},{:.2f},{:.2f}) evidence={:.3f} theta={:.3f}",
                 step_count_, mx, my, mz, ddm_stopping_.getEvidence(), ddm_stopping_.getAdaptiveThreshold());
        convergence_reported_ = true; return GSLResult::Success;
    }

    // BUG-5 fix: Actually use CP stopping criterion
    if (use_cp_ && cp_stopping_.shouldStop()) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("CP-STOP: converged at step={} MAP=({:.2f},{:.2f},{:.2f}) width={:.3f}",
                 step_count_, mx, my, mz, cp_stopping_.getWidth());
        convergence_reported_ = true; return GSLResult::Success;
    }

    // V5: Multiple convergence paths
    bool near_map = dist_to_peak < 1.5f;
    bool near_best_hit = std::sqrt((best_hit_x_-cx)*(best_hit_x_-cx) + (best_hit_y_-cy)*(best_hit_y_-cy)) < 1.0f;
    bool entropy_low = field.field_entropy < convergence_entropy_threshold_;
    bool z_ok = dz < 1.0f;
    bool high_conc = best_hit_conc_ > 0.08f;  // VGR: lower threshold for intermittent plumes

    // V5.2: all paths require MAP reasonably close to robot
    bool map_reasonable = dist_to_peak < 3.0f;
    bool converged = map_reasonable && ((near_map && entropy_low && z_ok) || (near_best_hit && high_conc && entropy_low));

    if (converged) {
        stable_steps_count_++;
    } else {
        stable_steps_count_ = 0;
    }

    // V5: fewer stable steps needed (3 vs 5)
    if (stable_steps_count_ >= 3) {
        logStopDecision("entropy_convergence");
        GSL_INFO("OPGSL-SDNBV CONVERGED: entropy={:.2f} dist={:.2f} z_dist={:.2f} hits={} step={} best_c={:.3f}",
                 field.field_entropy, dist_to_peak, dz, gas_hit_count_, step_count_, best_hit_conc_);
        convergence_reported_ = true; return GSLResult::Success;
    }
    // V5.2: fast exit requires MAP also near robot (not just best_hit)
    float map_dist = std::sqrt((map_x-cx)*(map_x-cx) + (map_y-cy)*(map_y-cy));
    if (step_count_ >= 20 && best_hit_conc_ > 0.05f && near_best_hit && map_dist < 2.5f) {
        logStopDecision("fast_exit");
        GSL_INFO("OPGSL-SDNBV FAST EXIT: best_c={:.3f} near_hit={} map_dist={:.2f} step={}",
                 best_hit_conc_, near_best_hit, map_dist, step_count_);
        convergence_reported_ = true; return GSLResult::Success;
    }
    // BUG-4 fix: Removed forced 250s timeout - let algorithm converge naturally
    // Only hard timeout at 300s (from maxSearchTime param)
    if (elapsed_time_ > 295.0f && !convergence_reported_) {
        logStopDecision("timeout");
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("HARD TIMEOUT: MAP=({:.2f},{:.2f},{:.2f}) step={}", mx, my, mz, step_count_);
        convergence_reported_ = true; return GSLResult::Success;
    }
    if (step_count_ >= 300) { logStopDecision("step_limit"); return GSLResult::Failure; }
    return GSLResult::Running;
}

void OPGSL::saveResultsToFile(GSLResult result) {
    float map_x, map_y, map_z;
    posterior3d_.getMAP(map_x, map_y, map_z);
    auto field = field_estimator_.computeField();
    float field_x = field.peak_x, field_y = field.peak_y;
    float maxc_z = maxConcAltitude();
    float post_z = getPosteriorBestZ();
    GSL_INFO("OPGSL-SDNBV RESULT: posterior_MAP=({:.2f},{:.2f},{:.2f}) field=({:.2f},{:.2f}) "
             "maxc_z={:.2f} post_z={:.2f} steps={} hits={} t={:.1f}s",
             map_x, map_y, map_z, field_x, field_y, maxc_z, post_z,
             step_count_, gas_hit_count_, elapsed_time_);
    if (!audit_file_.empty()) {
        audit_stream_.open(audit_file_, std::ios::app);
        if (audit_stream_.is_open()) {
            audit_stream_ << std::fixed << std::setprecision(3)
                          << map_x << "," << map_y << "," << map_z << ","
                          << field_x << "," << field_y << ","
                          << maxc_z << "," << post_z << ","
                          << step_count_ << "," << gas_hit_count_ << "," << elapsed_time_ << ","
                          << (int)result << "\n";
            audit_stream_.close();
        }
    }
}

void OPGSL::OnUpdate() {
    Algorithm::OnUpdate();
}

void OPGSL::OnCompleteNavigation(GSLResult result, State* previousState) {
    stateMachine.forceSetState(stopAndMeasureState.get());
}

// ============================================================
// MovingStateOPGSL
// ============================================================
MovingStateOPGSL::MovingStateOPGSL(Algorithm* _algorithm) : MovingState(_algorithm) {
    opgsl_ = dynamic_cast<OPGSL*>(_algorithm);
}

NavigateToPose::Goal MovingStateOPGSL::posToGoal(float x, float y, float z) {
    NavigateToPose::Goal g;
    g.pose.pose.position.x = x;
    g.pose.pose.position.y = y;
    g.pose.pose.position.z = z;
    g.pose.pose.orientation.w = 1.0f;
    return g;
}

void MovingStateOPGSL::chooseGoalAndMove() {
    if (!opgsl_) { GSL_ERROR("OPGSL pointer null"); return; }
    opgsl_->step_count_++;
    double now = opgsl_->node->now().seconds();
    if (opgsl_->last_update_time_ > 0) opgsl_->elapsed_time_ += static_cast<float>(now - opgsl_->last_update_time_);
    opgsl_->last_update_time_ = now;

    // Select target altitude
    // During Phase 1 & 1.5 (steps 1-16): stay at default flight height
    // During Phase 2 (steps 17+): use adaptive altitude selection
    float tz;
    if (opgsl_->step_count_ < 17) {
        tz = 0.3f;  // Fixed during exploration/upwind tracking
    } else {
        tz = opgsl_->selectTargetAltitude();
    }
    opgsl_->current_altitude_ = tz;

    // Select horizontal target (SD-NBV)
    float tx, ty;
    opgsl_->infotaxisStep(tx, ty);

    auto waypoint_string = [](float x, float y, float z) {
        return std::to_string(x) + "|" + std::to_string(y) + "|" + std::to_string(z);
    };

    // Log state
    opgsl_->logAltitudeState();
    GSL_INFO("OPGSL-AI step={} ({:.2f},{:.2f},{:.2f}) hits={} t={:.1f}",
             opgsl_->step_count_, tx, ty, tz, opgsl_->gas_hit_count_, opgsl_->elapsed_time_);

    float cx = opgsl_->currentRobotPosition.x, cy = opgsl_->currentRobotPosition.y;
    auto goal = posToGoal(tx, ty, tz);
    if (checkGoal(goal)) {
        opgsl_->logWaypointCandidate(opgsl_->elapsed_time_, "sdnbv", tx, ty, tz, true, -1);
        opgsl_->logModuleActivation(opgsl_->elapsed_time_, waypoint_string(tx, ty, tz), "sdnbv");
        sendGoal(goal); return;
    }
    opgsl_->logWaypointCandidate(opgsl_->elapsed_time_, "sdnbv", tx, ty, tz, false, -1);

    // Fallback: try shorter distances
    float dx = tx-cx, dy = ty-cy, d = std::sqrt(dx*dx+dy*dy);
    if (d > 0.1f) {
        float dirx = dx/d, diry = dy/d;
        float fa[] = {0.75f, 0.5f, 0.3f, 0.2f};
        int fallback_index = 0;
        for (float f : fa) {
            float fx = cx+dirx*d*f, fy = cy+diry*d*f;
            opgsl_->clipToMapBounds(fx, fy);
            auto fg = posToGoal(fx, fy, tz);
            bool accepted = checkGoal(fg);
            opgsl_->logWaypointCandidate(opgsl_->elapsed_time_, "fallback_short", fx, fy, tz, accepted, fallback_index++);
            if (accepted) {
                opgsl_->logModuleActivation(opgsl_->elapsed_time_, waypoint_string(fx, fy, tz), "fallback_short");
                sendGoal(fg); GSL_INFO("OPGSL-SDNBV fb1 ({:.2f},{:.2f},{:.2f})", fx, fy, tz); return;
            }
        }
    }
    // Random fallback
    for (int i = 0; i < 8; i++) {
        float ang = std::uniform_real_distribution<float>(0, 2*M_PI)(opgsl_->rng_);
        float dist = std::uniform_real_distribution<float>(0.3f, 1.5f)(opgsl_->rng_);
        float rx = cx+dist*std::cos(ang), ry = cy+dist*std::sin(ang);
        opgsl_->clipToMapBounds(rx, ry);
        auto rg = posToGoal(rx, ry, tz);
        bool accepted = checkGoal(rg);
        opgsl_->logWaypointCandidate(opgsl_->elapsed_time_, "fallback_random", rx, ry, tz, accepted, i);
        if (accepted) {
            opgsl_->logModuleActivation(opgsl_->elapsed_time_, waypoint_string(rx, ry, tz), "fallback_random");
            sendGoal(rg); GSL_INFO("OPGSL-SDNBV fb2 ({:.2f},{:.2f},{:.2f})", rx, ry, tz); return;
        }
    }
    opgsl_->logModuleActivation(opgsl_->elapsed_time_, "", "none");
    GSL_ERROR("OPGSL-SDNBV ALL fallbacks failed!");
}

void MovingStateOPGSL::Fail() {
    if (!opgsl_) return;
    float ang = std::uniform_real_distribution<float>(0, 2*M_PI)(opgsl_->rng_);
    float nx = opgsl_->currentRobotPosition.x + 1.5f*std::cos(ang);
    float ny = opgsl_->currentRobotPosition.y + 1.5f*std::sin(ang);
    opgsl_->clipToMapBounds(nx, ny);
    auto goal = posToGoal(nx, ny, opgsl_->current_altitude_);
    if (checkGoal(goal)) sendGoal(goal);
}

// ============================================================
// Module Activation Logging (read-only, no algorithm logic change)
// ============================================================
void OPGSL::initModuleActivationLogging() {
    module_activation_trace_file_ = getParam<std::string>("opgsl.trace.module_activation", "");
    waypoint_candidate_trace_file_ = getParam<std::string>("opgsl.trace.waypoint_candidate", "");
    stop_decision_trace_file_ = getParam<std::string>("opgsl.trace.stop_decision", "");

    if (!module_activation_trace_file_.empty()) {
        module_activation_stream_.open(module_activation_trace_file_, std::ios::out | std::ios::trunc);
        if (module_activation_stream_.is_open()) {
            module_activation_stream_ << "sim_time,cycle_id,gas_update_type,posterior_entropy,"
                << "posterior_variance,active_estimator,active_planner,"
                << "selected_waypoint,selected_waypoint_source,Levy_active,chemotaxis_active,"
                << "bout_active,adaptive_step_active,WRAIG_active,"
                << "GP_height_active,GBI_eta,CP_triggered,DDM_triggered,"
                << "entropy_triggered,distance_triggered,fast_exit_triggered,"
                << "timeout_triggered,algorithm_declared_success\n";
        }
    }
    if (!waypoint_candidate_trace_file_.empty()) {
        waypoint_candidate_stream_.open(waypoint_candidate_trace_file_, std::ios::out | std::ios::trunc);
        if (waypoint_candidate_stream_.is_open()) {
            waypoint_candidate_stream_ << "sim_time,cycle_id,current_x,current_y,current_z,"
                << "candidate_x,candidate_y,candidate_z,source,accepted,fallback_index\n";
        }
    }
    if (!stop_decision_trace_file_.empty()) {
        stop_decision_stream_.open(stop_decision_trace_file_, std::ios::out | std::ios::trunc);
        if (stop_decision_stream_.is_open()) {
            stop_decision_stream_ << "sim_time,trigger,cp_should_stop,ddm_should_stop,"
                << "entropy_low,near_map,near_best_hit,high_conc,map_distance,"
                << "stable_steps,gas_hit_count,step_count\n";
        }
    }
}

void OPGSL::logModuleActivation(double sim_time, const std::string& selected_waypoint,
                                const std::string& selected_waypoint_source) {
    if (!module_activation_stream_.is_open()) return;
    trace_cycle_count_++;
    float H = posterior3d_.getEntropy();
    float mx, my, mz;
    posterior3d_.getMAP(mx, my, mz);
    float H_max = std::log((float)(posterior3d_.nx_ * posterior3d_.ny_ * posterior3d_.nz_));
    float H_ratio = H / H_max;
    float posterior_variance = posterior3d_.getVariance();

    std::string gas_type = (latest_gas_ > 0.01f) ? "HIT" : "MISS";

    // GBI eta computation (mirror of binaryEventUpdate logic)
    float wind_conf = wind_confidence_;
    bool detected = (latest_gas_ > 0.01f);
    float eta = detected ? (0.6f + 0.3f * wind_conf) : (0.15f + 0.35f * wind_conf);

    module_activation_stream_ << std::fixed << std::setprecision(4)
        << sim_time << "," << trace_cycle_count_ << "," << gas_type << ","
        << H << "," << posterior_variance << ","
        << "SourcePosterior3D,SD-NBV," << selected_waypoint << ","
        << selected_waypoint_source << ","
        << (use_levy_ ? "true" : "false") << ","
        << (use_upwind_tracking_ ? "true" : "false") << ","
        << (use_bout_ ? "true" : "false") << ","
        << (use_adaptive_step_ ? "true" : "false") << ","
        << (use_wraig_ ? "true" : "false") << ","
        << (use_gp_altitude_ ? "true" : "false") << ","
        << eta << ","
        << (use_cp_ ? "true" : "false") << ","
        << (use_ddm_ ? "true" : "false") << ","
        << (H_ratio < 0.85f ? "true" : "false") << ","
        << "false,"  // distance_triggered (no GT)
        << (step_count_ >= 20 && best_hit_conc_ > 0.05f ? "true" : "false") << ","
        << (elapsed_time_ > 295.0f ? "true" : "false") << ","
        << (convergence_reported_ ? "true" : "false") << "\n";
    module_activation_stream_.flush();
}

void OPGSL::logWaypointCandidate(double sim_time, const std::string& source,
                                 float candidate_x, float candidate_y, float candidate_z,
                                 bool accepted, int fallback_index) {
    if (!waypoint_candidate_stream_.is_open()) return;
    waypoint_candidate_stream_ << std::fixed << std::setprecision(4)
        << sim_time << "," << trace_cycle_count_ << ","
        << currentRobotPosition.x << "," << currentRobotPosition.y << ","
        << current_altitude_ << "," << candidate_x << "," << candidate_y << ","
        << candidate_z << "," << source << "," << (accepted ? "true" : "false")
        << "," << fallback_index << "\n";
    waypoint_candidate_stream_.flush();
}

void OPGSL::logStopDecision(const std::string& trigger) {
    if (!stop_decision_stream_.is_open()) return;
    float mx, my, mz;
    posterior3d_.getMAP(mx, my, mz);
    float cx = currentRobotPosition.x, cy = currentRobotPosition.y;
    float map_dist = std::sqrt((mx-cx)*(mx-cx) + (my-cy)*(my-cy));
    float H = posterior3d_.getEntropy();
    float H_max = std::log((float)(posterior3d_.nx_ * posterior3d_.ny_ * posterior3d_.nz_));
    bool entropy_low = (H / H_max) < 0.85f;
    bool near_map = map_dist < 1.5f;
    bool near_best = std::sqrt((best_hit_x_-cx)*(best_hit_x_-cx) + (best_hit_y_-cy)*(best_hit_y_-cy)) < 1.0f;
    bool high_conc = best_hit_conc_ > 0.08f;

    stop_decision_stream_ << std::fixed << std::setprecision(4)
        << elapsed_time_ << "," << trigger << ","
        << (use_cp_ && cp_stopping_.shouldStop() ? "true" : "false") << ","
        << (use_ddm_ && ddm_stopping_.shouldStop() ? "true" : "false") << ","
        << (entropy_low ? "true" : "false") << ","
        << (near_map ? "true" : "false") << ","
        << (near_best ? "true" : "false") << ","
        << (high_conc ? "true" : "false") << ","
        << map_dist << "," << stable_steps_count_ << ","
        << gas_hit_count_ << "," << step_count_ << "\n";
    stop_decision_stream_.flush();
}

} // namespace GSL
