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

namespace GSL {

OPGSL::OPGSL(std::shared_ptr<rclcpp::Node> _node) : Algorithm(_node) { rng_.seed(std::random_device{}()); }

void OPGSL::declareParameters() {
    Algorithm::declareParameters();
    n_cells_ = getParam<int>("opgsl.grid.n_cells", 40);
    resolution_ = getParam<double>("opgsl.grid.resolution", 0.5);
    map_half_size_ = n_cells_ * resolution_ / 2.0f;
    convergence_entropy_threshold_ = getParam<double>("opgsl.convergence.entropy_threshold", 5.0);
    convergence_min_bouts_ = getParam<int>("opgsl.convergence.min_bouts", 5);
    convergence_stable_steps_ = getParam<int>("opgsl.convergence.stable_steps", 5);
    convergence_min_time_ = getParam<double>("opgsl.convergence.min_time", 30.0);
    audit_file_ = getParam<std::string>("opgsl.audit_file", "");
    // Innovation module toggles
    use_levy_ = getParam<bool>("opgsl.modules.levy", true);
    use_bout_ = getParam<bool>("opgsl.modules.bout", true);
    use_adaptive_step_ = getParam<bool>("opgsl.modules.adaptive_step", true);
    // 3D altitude module toggles
    use_esc_altitude_ = getParam<bool>("opgsl.altitude.esc", true);
    use_levy_altitude_ = getParam<bool>("opgsl.altitude.levy", true);
    use_layer_scan_ = getParam<bool>("opgsl.altitude.layer_scan", true);
    use_altitude_decay_ = getParam<bool>("opgsl.altitude.decay", true);
    // Altitude bounds
    z_min_ = getParam<double>("opgsl.altitude.z_min", 0.0);
    z_max_ = getParam<double>("opgsl.altitude.z_max", 3.0);
    GSL_INFO("OPGSL declareParameters: grid={}x{} res={:.1f} levy={} bout={} adaptive={} esc_alt={} levy_alt={} layer_scan={} decay={}",
             n_cells_, n_cells_, resolution_, use_levy_, use_bout_, use_adaptive_step_,
             use_esc_altitude_, use_levy_altitude_, use_layer_scan_, use_altitude_decay_);
}

void OPGSL::Initialize() {
    field_cfg_.n_cells = n_cells_; field_cfg_.resolution = resolution_;
    field_cfg_.map_half_size = map_half_size_; field_cfg_.max_observations = 200;
    field_cfg_.observation_decay = 0.998f; field_cfg_.bandwidth_base = 1.2f;
    field_cfg_.bandwidth_wind_factor = 1.5f; field_cfg_.n_ensemble = 3;
    field_estimator_.init(field_cfg_);
    ig_cfg_.exploration_weight = 0.3f; ig_cfg_.wind_bonus = 0.5f;
    ig_cfg_.uncertainty_weight = 0.4f; ig_cfg_.visit_penalty = 0.2f;
    info_gain_.init(ig_cfg_);
    waitForMapState = std::make_unique<WaitForMapState>(this);
    waitForGasState = std::make_unique<WaitForGasState>(this);
    stopAndMeasureState = std::make_unique<StopAndMeasureState>(this);
    movingState = std::make_unique<MovingStateOPGSL>(this);
    Algorithm::Initialize(); stateMachine.forceSetState(waitForMapState.get());
    prev_gas_ = 0.0f;
    best_hit_conc_ = 0.0f; best_hit_x_ = 0.0f; best_hit_y_ = 0.0f; run_length_ = 0.8f; run_direction_x_ = 0.0f; run_direction_y_ = -1.0f;
    run_steps_remaining_ = 0; tumble_count_ = 0; gradient_threshold_ = 0.002f;
    max_step_ = 1.0f; max_run_steps_ = 8;
    need_next_goal_ = false;
    // Bout-level state
    bout_active_ = false; bout_start_time_ = 0.0f; bout_peak_conc_ = 0.0f;
    bout_count_ = 0; time_since_last_bout_ = 0.0f;
    // Adaptive step state
    step_size_ = 0.8f; prev_gradient_mag_ = 0.0f;
    // Levy state
    levy_step_remaining_ = 0; levy_angle_ = 0.0f;
    // 3D Altitude state
    alt_phase_ = AltPhase::EXPLORE;
    current_altitude_ = 0.3f;
    esc_.reset(0.3f, z_min_, z_max_);
    levy_height_step_remaining_ = 0;
    levy_height_target_ = 0.3f;
    layer_profile_.clear();
    significant_layers_.clear();
    calibration_active_ = false;
    calibration_step_ = 0;
    calibration_z_sequence_.clear();
    calibration_index_ = 0;
    best_calibrated_z_ = 0.3f;
    z_conc_history_.clear();
    for (int k = 0; k < kNumZBins; k++) z_posterior_[k] = 0.0f;
    GSL_INFO("OPGSL initialized: grid={}x{} res={:.1f}m levy={} bout={} adaptive={} alt_phase=EXPLORE z={:.1f}",
             n_cells_, n_cells_, resolution_, use_levy_, use_bout_, use_adaptive_step_, current_altitude_);
}

void OPGSL::OnUpdate() {
    Algorithm::OnUpdate();
    if (need_next_goal_) {
        need_next_goal_ = false;
        double now = node->now().seconds();
        if (last_update_time_ > 0) elapsed_time_ += static_cast<float>(now - last_update_time_);
        last_update_time_ = now;
        auto check = checkSourceFound();
        if (check != GSLResult::Running) {
            GSL_INFO("OPGSL: search complete, result={}", (int)check);
            saveResultsToFile(check);
            return;
        }
        GSL_INFO("OPGSL: selecting next goal (hits={} elapsed={:.1f}s alt_phase={} z={:.2f})",
                 gas_hit_count_, elapsed_time_, (int)alt_phase_, current_altitude_);
        movingState->chooseGoalAndMove();
    }
}

void OPGSL::OnCompleteNavigation(GSLResult result, State* previousState) {
    stateMachine.forceSetState(stopAndMeasureState.get());
}

// ============================================================
// 3D Altitude Controller Implementation
// ============================================================

float OPGSL::levyHeight(float z_current) {
    // Levy flight for height exploration (mu=2, 3D optimal)
    float u = std::uniform_real_distribution<float>(0.0f, 1.0f)(rng_);
    float beta = 2.0f;
    float l_min = 0.3f;
    float l_max = z_max_ - z_min_;
    if (l_max < l_min) l_max = l_min;
    float exponent = 1.0f / (beta - 1.0f);
    float ratio = l_min / l_max;
    float step = l_min * std::pow(1.0f - u * (1.0f - std::pow(ratio, beta - 1.0f)), -exponent);
    float sign = std::uniform_real_distribution<float>(0.0f, 1.0f)(rng_) > 0.5f ? 1.0f : -1.0f;
    float z_new = z_current + sign * step;
    return std::clamp(z_new, z_min_, z_max_);
}

void OPGSL::startCalibration() {
    // Significant Layer scanning: vertical sweep with recursive bisection
    calibration_active_ = true;
    calibration_step_ = 0;
    layer_profile_.clear();
    significant_layers_.clear();

    // First: do a coarse sweep to get endpoints and a few interior points
    calibration_z_sequence_.clear();
    float z_lo = z_min_;
    float z_hi = std::min(z_max_, 2.0f);  // limit scan range

    // Coarse sweep: 5 evenly spaced points
    int n_coarse = 5;
    for (int i = 0; i <= n_coarse; i++) {
        float z = z_lo + (z_hi - z_lo) * static_cast<float>(i) / static_cast<float>(n_coarse);
        calibration_z_sequence_.push_back(z);
    }
    calibration_index_ = 0;
    GSL_INFO("OPGSL: CALIBRATION started, {} sweep points z=[{:.1f}..{:.1f}]",
             n_coarse + 1, z_lo, z_hi);
}

void OPGSL::processCalibrationMeasurement(float z, float concentration) {
    layer_profile_.push_back({z, concentration});
    GSL_INFO("OPGSL: CALIBRATE sample z={:.2f} c={:.4f} ({}/{})",
             z, concentration, calibration_index_ + 1, (int)calibration_z_sequence_.size());

    calibration_index_++;
    if (calibration_index_ >= static_cast<int>(calibration_z_sequence_.size())) {
        // Sweep complete: find significant layers
        // Sort profile by z
        std::sort(layer_profile_.begin(), layer_profile_.end(),
                  [](const LayerPoint& a, const LayerPoint& b) { return a.z < b.z; });

        // Find best z (highest concentration)
        float best_z = layer_profile_[0].z;
        float best_c = layer_profile_[0].concentration;
        for (const auto& lp : layer_profile_) {
            if (lp.concentration > best_c) {
                best_c = lp.concentration;
                best_z = lp.z;
            }
        }
        best_calibrated_z_ = best_z;

        // Detect significant layers (points with large deviation from linear interpolation)
        float threshold = 0.02f;  // ppm
        significant_layers_.clear();
        for (size_t i = 1; i < layer_profile_.size() - 1; i++) {
            float z_i = layer_profile_[i].z;
            float c_i = layer_profile_[i].concentration;
            // Linear interpolation between neighbors
            float z_l = layer_profile_[i-1].z, c_l = layer_profile_[i-1].concentration;
            float z_r = layer_profile_[i+1].z, c_r = layer_profile_[i+1].concentration;
            float c_linear = c_l + (c_r - c_l) * (z_i - z_l) / (z_r - z_l + 1e-6f);
            float deviation = std::abs(c_i - c_linear);
            if (deviation > threshold) {
                significant_layers_.push_back(z_i);
                GSL_INFO("OPGSL: significant layer at z={:.2f} dev={:.4f}", z_i, deviation);
            }
        }

        // Transition to TRACK phase
        calibration_active_ = false;
        alt_phase_ = AltPhase::TRACK;
        if (use_esc_altitude_) {
            esc_.reset(best_calibrated_z_, z_min_, z_max_);
        }
        GSL_INFO("OPGSL: CALIBRATION complete, best_z={:.2f} best_c={:.4f} layers={} -> TRACK",
                 best_z, best_c, (int)significant_layers_.size());
    }
}

void OPGSL::updateAltitudePosterior(float z, float concentration) {
    // Map z to bin index
    int bin = static_cast<int>((z - z_min_) / (z_max_ - z_min_) * kNumZBins);
    bin = std::clamp(bin, 0, kNumZBins - 1);

    // Bayesian update: log-posterior += log-likelihood
    // Likelihood model: P(hit | z) proportional to concentration at z
    if (concentration > 0.01f) {
        float log_lik = std::log(concentration + 1e-10f);
        for (int k = 0; k < kNumZBins; k++) {
            float z_k = z_min_ + (z_max_ - z_min_) * (static_cast<float>(k) + 0.5f) / static_cast<float>(kNumZBins);
            float dz = std::abs(z_k - z);
            // Likelihood decreases with distance from measurement point
            float dist_factor = std::exp(-dz * dz / (2.0f * 0.3f * 0.3f));  // sigma=0.3m
            z_posterior_[k] += log_lik * dist_factor;
        }
    }

    // Temporal decay (reviewer criticism #4: prevents lock-in)
    if (use_altitude_decay_) {
        for (int k = 0; k < kNumZBins; k++) {
            z_posterior_[k] -= z_decay_rate_;
        }
    }

    // Normalize
    float max_log = *std::max_element(z_posterior_, z_posterior_ + kNumZBins);
    float log_sum = 0.0f;
    for (int k = 0; k < kNumZBins; k++) {
        log_sum += std::exp(z_posterior_[k] - max_log);
    }
    log_sum = std::log(log_sum) + max_log;
    for (int k = 0; k < kNumZBins; k++) {
        z_posterior_[k] -= log_sum;
    }
}

float OPGSL::getPosteriorBestZ() const {
    int best_k = 0;
    float best_val = z_posterior_[0];
    for (int k = 1; k < kNumZBins; k++) {
        if (z_posterior_[k] > best_val) {
            best_val = z_posterior_[k];
            best_k = k;
        }
    }
    return z_min_ + (z_max_ - z_min_) * (static_cast<float>(best_k) + 0.5f) / static_cast<float>(kNumZBins);
}

float OPGSL::maxConcAltitude() const {
    // MaxConc-z baseline: select altitude with highest measured concentration
    // Uses sliding window to avoid lock-in on early noisy measurements
    if (z_conc_history_.empty()) return current_altitude_;

    float best_z = current_altitude_;
    float best_conc = 0.0f;
    int start = std::max(0, static_cast<int>(z_conc_history_.size()) - max_conc_window_);
    for (int i = start; i < static_cast<int>(z_conc_history_.size()); i++) {
        if (z_conc_history_[i].concentration > best_conc) {
            best_conc = z_conc_history_[i].concentration;
            best_z = z_conc_history_[i].z;
        }
    }
    return best_z;
}

void OPGSL::updateAltitudePhase(float concentration) {
    float gas_threshold = 0.1f;  // ppm

    switch (alt_phase_) {
        case AltPhase::EXPLORE:
            if (concentration > gas_threshold && use_layer_scan_) {
                alt_phase_ = AltPhase::CALIBRATE;
                startCalibration();
            } else if (concentration > gas_threshold && use_esc_altitude_) {
                // Skip calibration, go directly to ESC tracking
                alt_phase_ = AltPhase::TRACK;
                esc_.reset(current_altitude_, z_min_, z_max_);
            }
            break;

        case AltPhase::CALIBRATE:
            // Handled in processCalibrationMeasurement()
            break;

        case AltPhase::TRACK:
            if (consecutive_misses_ >= consecutive_miss_threshold_) {
                GSL_INFO("OPGSL: {} consecutive misses -> back to EXPLORE", consecutive_misses_);
                alt_phase_ = AltPhase::EXPLORE;
            }
            break;
    }
}

float OPGSL::selectTargetAltitude() {
    switch (alt_phase_) {
        case AltPhase::EXPLORE: {
            if (use_levy_altitude_) {
                // Lévy flight for height exploration
                if (levy_height_step_remaining_ <= 0) {
                    levy_height_target_ = levyHeight(current_altitude_);
                    levy_height_step_remaining_ = std::uniform_int_distribution<int>(3, 6)(rng_);
                }
                levy_height_step_remaining_--;
                return levy_height_target_;
            }
            return current_altitude_;
        }

        case AltPhase::CALIBRATE: {
            if (!calibration_z_sequence_.empty() && calibration_index_ < static_cast<int>(calibration_z_sequence_.size())) {
                return calibration_z_sequence_[calibration_index_];
            }
            return current_altitude_;
        }

        case AltPhase::TRACK: {
            if (use_esc_altitude_) {
                return esc_.getZ();
            }
            // Fallback: posterior best or max-conc
            float z_post = getPosteriorBestZ();
            float z_maxc = maxConcAltitude();
            return 0.5f * z_post + 0.5f * z_maxc;
        }
    }
    return current_altitude_;
}

void OPGSL::logAltitudeState() {
    float z_esc = (alt_phase_ == AltPhase::TRACK) ? esc_.getZ() : -1.0f;
    float z_post = getPosteriorBestZ();
    float z_maxc = maxConcAltitude();
    GSL_INFO("OPGSL-3D: phase={} z_current={:.2f} z_esc={:.2f} z_post={:.2f} z_maxc={:.2f} esc_amp={:.3f} esc_G={:.4f} hits={} misses={}",
             (int)alt_phase_, current_altitude_, z_esc, z_post, z_maxc,
             esc_.amplitude, esc_.G_hat, gas_hit_count_, consecutive_misses_);
}

// ============================================================
// Gas and Wind Measurement Processing
// ============================================================

void OPGSL::processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection) {
    total_measurements_++;
    latest_gas_ = static_cast<float>(concentration);
    latest_wind_speed_ = static_cast<float>(windSpeed);
    float wd = static_cast<float>(windDirection);
    latest_wind_x_ = std::cos(wd);
    latest_wind_y_ = std::sin(wd);
    wind_dir_history_.push_back(wd);
    if (wind_dir_history_.size() > kWindHistorySize) wind_dir_history_.pop_front();

    // Update field estimator
    float rx = currentRobotPosition.x, ry = currentRobotPosition.y;
    field_estimator_.addObservation(latest_gas_, rx, ry, latest_wind_x_, latest_wind_y_, elapsed_time_);

    // Record z-concentration history
    z_conc_history_.push_back({current_altitude_, latest_gas_, elapsed_time_});
    if (z_conc_history_.size() > 200) z_conc_history_.pop_front();

    // Update altitude posterior
    updateAltitudePosterior(current_altitude_, latest_gas_);

    // Bout-level detection
    if (use_bout_) {
        if (latest_gas_ > 0.05f) {
            if (!bout_active_) {
                bout_active_ = true;
                bout_start_time_ = elapsed_time_;
                bout_peak_conc_ = latest_gas_;
            } else {
                bout_peak_conc_ = std::max(bout_peak_conc_, latest_gas_);
            }
            time_since_last_bout_ = 0.0f;
        } else {
            if (bout_active_) {
                bout_active_ = false;
                bout_count_++;
            }
            time_since_last_bout_ += 1.0f;
        }
    }

    if (latest_gas_ > 0.01f) {
        gas_hit_count_++;
        consecutive_misses_ = 0;
        last_hit_time_ = elapsed_time_;
        last_hit_x_ = rx; last_hit_y_ = ry;
        if (latest_gas_ > best_hit_conc_) {
            best_hit_conc_ = latest_gas_;
            best_hit_x_ = rx; best_hit_y_ = ry;
        }
        if (ry < southernmost_hit_y_) { southernmost_hit_y_ = ry; southernmost_hit_x_ = rx; }
        if (ry > northernmost_hit_y_) { northernmost_hit_y_ = ry; }
        if (rx < westernmost_hit_x_) westernmost_hit_x_ = rx;
        if (rx > easternmost_hit_x_) easternmost_hit_x_ = rx;
    } else {
        consecutive_misses_++;
    }

    // ESC update (only in TRACK phase)
    if (alt_phase_ == AltPhase::TRACK && use_esc_altitude_) {
        esc_.update(latest_gas_);
    }

    // Calibration measurement
    if (alt_phase_ == AltPhase::CALIBRATE && calibration_active_) {
        processCalibrationMeasurement(current_altitude_, latest_gas_);
    }

    // Phase management
    updateAltitudePhase(latest_gas_);

    // Log altitude state
    logAltitudeState();

    need_next_goal_ = true;
}

// ============================================================
// Navigation
// ============================================================

void OPGSL::infotaxisStep(float& best_x, float& best_y) {
    float cx = currentRobotPosition.x, cy = currentRobotPosition.y;
    auto field = field_estimator_.computeField();
    float ex = field.peak_x, ey = field.peak_y;
    float grad = field.field_entropy;
    float dx = ex - cx, dy = ey - cy;
    float dist = std::sqrt(dx*dx + dy*dy);

    if (gas_hit_count_ > 0) {
        // Chemotaxis navigation (upwind surge + crosswind cast)
        float wx = smoothWindDirection();
        float upwind_x = -std::cos(wx), upwind_y = -std::sin(wx);
        float cross_x = -std::sin(wx), cross_y = std::cos(wx);

        // Surge: move upwind toward source
        float surge_x = cx + upwind_x * step_size_;
        float surge_y = cy + upwind_y * step_size_;

        // Cast: move crosswind to re-acquire plume
        float cast_dir = (consecutive_misses_ > 3) ? 1.0f : -1.0f;
        float cast_x = cx + cross_x * cast_dir * step_size_;
        float cast_y = cy + cross_y * cast_dir * step_size_;

        // Weighted centroid from field estimate
        float centroid_x = ex, centroid_y = ey;

        // Combine: if hitting gas, surge toward centroid; if missing, cast
        if (latest_gas_ > 0.01f) {
            best_x = 0.7f * centroid_x + 0.3f * surge_x;
            best_y = 0.7f * centroid_y + 0.3f * surge_y;
        } else if (consecutive_misses_ < 5) {
            best_x = 0.5f * surge_x + 0.5f * centroid_x;
            best_y = 0.5f * surge_y + 0.5f * centroid_y;
        } else {
            best_x = 0.3f * surge_x + 0.7f * cast_x;
            best_y = 0.3f * surge_y + 0.7f * cast_y;
        }

        // Adaptive step size based on gradient
        if (use_adaptive_step_) {
            float momentum = 0.7f;
            float target_step = max_step_;
            if (grad > 0.01f) {
                target_step = std::min(max_step_, dist * 0.5f);
            } else if (grad > 0.001f) {
                target_step = std::min(max_step_ * 0.5f, dist * 0.3f);
            } else {
                target_step = std::min(max_step_ * 0.2f, 0.3f);
            }
            step_size_ = momentum * step_size_ + (1.0f - momentum) * target_step;
            prev_gradient_mag_ = grad;
        } else {
            step_size_ = max_step_;
        }

        if (dist > 0.5f) {
            float step = std::min(step_size_, dist * 0.4f);
            best_x = cx + (dx/dist) * step;
            best_y = cy + (dy/dist) * step;
        } else if (grad > 0.001f) {
            best_x = cx + run_direction_x_ * step_size_ * 0.3f;
            best_y = cy + run_direction_y_ * step_size_ * 0.3f;
        } else {
            float ang = std::uniform_real_distribution<float>(0, 2*M_PI)(rng_);
            run_direction_x_ = std::cos(ang); run_direction_y_ = std::sin(ang);
            best_x = cx + run_direction_x_ * step_size_ * 0.3f;
            best_y = cy + run_direction_y_ * step_size_ * 0.3f;
        }
        GSL_INFO("CHEMOTAX step={} target=({:.2f},{:.2f}) centroid=({:.2f},{:.2f}) dist={:.2f} grad={:.4f} step_size={:.2f} hits={}",
                 step_count_, best_x, best_y, ex, ey, dist, grad, step_size_, gas_hit_count_);
    } else {
        if (use_levy_) {
            levyExploration(best_x, best_y, cx, cy);
        } else {
            float ang = std::uniform_real_distribution<float>(0, 2*M_PI)(rng_);
            float step = std::min(run_length_, max_step_);
            best_x = cx + step*std::cos(ang); best_y = cy + step*std::sin(ang);
        }
    }
    clipToMapBounds(best_x, best_y); prev_gas_ = latest_gas_;
}

void OPGSL::levyExploration(float& best_x, float& best_y, float cx, float cy) {
    // Levy flight for horizontal exploration (mu=2)
    if (levy_step_remaining_ <= 0) {
        // New Levy step
        float u = std::uniform_real_distribution<float>(0.0f, 1.0f)(rng_);
        float beta = 2.0f;
        float l_min = 0.5f, l_max = 5.0f;
        float exponent = 1.0f / (beta - 1.0f);
        float ratio = l_min / l_max;
        float step = l_min * std::pow(1.0f - u * (1.0f - std::pow(ratio, beta - 1.0f)), -exponent);
        levy_angle_ = std::uniform_real_distribution<float>(0, 2*M_PI)(rng_);
        levy_step_remaining_ = static_cast<int>(step / max_step_) + 1;
        run_direction_x_ = std::cos(levy_angle_);
        run_direction_y_ = std::sin(levy_angle_);
    }
    levy_step_remaining_--;
    best_x = cx + run_direction_x_ * max_step_;
    best_y = cy + run_direction_y_ * max_step_;
}

float OPGSL::smoothWindDirection() const {
    if (wind_dir_history_.empty()) return 0.0f;
    float sin_sum = 0.0f, cos_sum = 0.0f;
    for (float d : wind_dir_history_) {
        sin_sum += std::sin(d);
        cos_sum += std::cos(d);
    }
    return std::atan2(sin_sum, cos_sum);
}

void OPGSL::clipToMapBounds(float& x, float& y) const {
    float margin = 0.5f;
    x = std::clamp(x, -map_half_size_ + margin, map_half_size_ - margin);
    y = std::clamp(y, -map_half_size_ + margin, map_half_size_ - margin);
}

// ============================================================
// MovingStateOPGSL
// ============================================================

MovingStateOPGSL::MovingStateOPGSL(Algorithm* _algorithm) : MovingState(_algorithm) { opgsl_ = dynamic_cast<OPGSL*>(_algorithm); }

NavigateToPose::Goal MovingStateOPGSL::posToGoal(float x, float y, float z) {
    NavigateToPose::Goal g;
    g.pose.header.frame_id = "map"; g.pose.header.stamp = opgsl_->node->now();
    g.pose.pose.position.x = x; g.pose.pose.position.y = y;
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

    // Select target altitude using 3D controller
    float tz = opgsl_->selectTargetAltitude();
    opgsl_->current_altitude_ = tz;

    // Select horizontal target
    float tx, ty; opgsl_->infotaxisStep(tx, ty);

    GSL_INFO("OPGSL step={} target=({:.2f},{:.2f},{:.2f}) gas_hits={} elapsed={:.1f} alt_phase={}",
             opgsl_->step_count_, tx, ty, tz, opgsl_->gas_hit_count_, opgsl_->elapsed_time_, (int)opgsl_->alt_phase_);

    float cx = opgsl_->currentRobotPosition.x, cy = opgsl_->currentRobotPosition.y;
    auto goal = posToGoal(tx, ty, tz);
    if (checkGoal(goal)) { sendGoal(goal); return; }

    // Fallback: try shorter distances
    float dx = tx-cx, dy = ty-cy, d = std::sqrt(dx*dx+dy*dy);
    if (d > 0.1f) {
        float dirx = dx/d, diry = dy/d;
        float fa[] = {0.75f, 0.5f, 0.3f, 0.2f};
        for (float f : fa) {
            float fx = cx+dirx*d*f, fy = cy+diry*d*f;
            opgsl_->clipToMapBounds(fx, fy);
            auto fg = posToGoal(fx, fy, tz);
            if (checkGoal(fg)) { sendGoal(fg); GSL_INFO("OPGSL fb1 ({:.2f},{:.2f},{:.2f})", fx, fy, tz); return; }
        }
    }

    // Fallback: random nearby points
    for (int i = 0; i < 8; i++) {
        float ang = std::uniform_real_distribution<float>(0, 2*M_PI)(opgsl_->rng_);
        float dist = std::uniform_real_distribution<float>(0.3f, 1.5f)(opgsl_->rng_);
        float rx = cx+dist*std::cos(ang), ry = cy+dist*std::sin(ang);
        opgsl_->clipToMapBounds(rx, ry);
        auto rg = posToGoal(rx, ry, tz);
        if (checkGoal(rg)) { sendGoal(rg); GSL_INFO("OPGSL fb2 ({:.2f},{:.2f},{:.2f})", rx, ry, tz); return; }
    }
    GSL_ERROR("OPGSL ALL fallbacks failed!");
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
// Convergence check and result saving (stubs - implement per your pipeline)
// ============================================================

GSLResult OPGSL::checkSourceFound() {
    // Check if search is complete
    if (elapsed_time_ < convergence_min_time_) return GSLResult::Running;
    if (gas_hit_count_ < convergence_min_bouts_) return GSLResult::Running;

    auto field = field_estimator_.computeField();
    if (field.field_entropy < convergence_entropy_threshold_) {
        stable_steps_count_++;
    } else {
        stable_steps_count_ = 0;
    }

    if (stable_steps_count_ >= convergence_stable_steps_) {
        return GSLResult::SourceFound;
    }

    // Timeout check (200 steps max)
    if (step_count_ >= 200) {
        return GSLResult::TimeLimitReached;
    }

    return GSLResult::Running;
}

void OPGSL::saveResultsToFile(GSLResult result) {
    auto field = field_estimator_.computeField();
    float final_x = field.peak_x, final_y = field.peak_y;
    float final_z = current_altitude_;

    // Also report MaxConc-z baseline
    float maxc_z = maxConcAltitude();
    float post_z = getPosteriorBestZ();

    GSL_INFO("OPGSL-3D RESULT: error_xy=({:.2f},{:.2f}) z={:.2f} maxc_z={:.2f} post_z={:.2f} steps={} hits={} time={:.1f}s phase_final={}",
             final_x, final_y, final_z, maxc_z, post_z, step_count_, gas_hit_count_, elapsed_time_, (int)alt_phase_);

    if (!audit_file_.empty()) {
        audit_stream_.open(audit_file_, std::ios::app);
        if (audit_stream_.is_open()) {
            audit_stream_ << std::fixed << std::setprecision(3)
                          << final_x << "," << final_y << "," << final_z << ","
                          << maxc_z << "," << post_z << ","
                          << step_count_ << "," << gas_hit_count_ << "," << elapsed_time_ << ","
                          << (int)result << "," << (int)alt_phase_ << "\n";
            audit_stream_.close();
        }
    }
}

} // namespace GSL