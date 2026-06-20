#include "SensorAwareSurgeCastPF.hpp"
#include "gsl_server/core/GSLResult.hpp"

#include "angles/angles.h"
#include "gsl_server/algorithms/PlumeTracking/MovingStatePlumeTracking.hpp"
#include "gsl_server/core/Vectors.hpp"
#include "gsl_server/algorithms/Common/Utils/RosUtils.hpp"

#include <cmath>
#include <iomanip>
#include <limits>
#include <numeric>

namespace GSL {

void SensorAwareSurgeCastPF::declareParameters() {
    SurgeCast::declareParameters();

    sensor_config_.tau_rise_s = getParam("saisc.sdbe.tau_rise_s", 1.2);
    sensor_config_.tau_decay_s = getParam("saisc.sdbe.tau_decay_s", 4.0);
    sensor_config_.baseline_tau_s = getParam("saisc.sdbe.baseline_tau_s", 45.0);
    sensor_config_.noise_tau_s = getParam("saisc.sdbe.noise_tau_s", 20.0);
    sensor_config_.z_midpoint = getParam("saisc.sdbe.z_midpoint", 3.0);
    sensor_config_.z_temperature = getParam("saisc.sdbe.z_temperature", 0.75);
    sensor_config_.hit_on_probability = getParam("saisc.sdbe.hit_on_probability", 0.70);
    sensor_config_.hit_off_probability = getParam("saisc.sdbe.hit_off_probability", 0.35);

    policy_config_.input_wind_is_flow_to = getParam("saisc.iasc.input_wind_is_flow_to", true);
    policy_config_.minimum_wind_speed = getParam("saisc.iasc.minimum_wind_speed", 0.05);
    policy_config_.minimum_wind_concentration = getParam("saisc.iasc.minimum_wind_concentration", 0.45);
    policy_config_.surge_min_step_m = getParam("saisc.iasc.surge_min_step_m", 0.5);
    policy_config_.surge_max_step_m = getParam("saisc.iasc.surge_max_step_m", 2.0);
    policy_config_.cast_min_step_m = getParam("saisc.iasc.cast_min_step_m", 0.6);
    policy_config_.cast_max_step_m = getParam("saisc.iasc.cast_max_step_m", 4.0);
    policy_config_.plume_memory_s = getParam("saisc.iasc.plume_memory_s", 25.0);
    policy_config_.maximum_casts_before_explore = getParam("saisc.iasc.maximum_casts", 8);
    policy_config_.explore_step_m = getParam("saisc.iasc.explore_step_m", 2.5);

    pf_config_.particle_count = static_cast<std::size_t>(getParam("saisc.sepf.particles", 1500));
    pf_config_.random_seed = static_cast<std::uint64_t>(getParam("random_seed", 1));
    pf_config_.background_hit_probability = getParam("saisc.sepf.background_hit_probability", 0.01);
    pf_config_.plume_gain = getParam("saisc.sepf.plume_gain", 2.0);
    pf_config_.crosswind_sigma_base_m = getParam("saisc.sepf.crosswind_sigma_base_m", 0.35);
    pf_config_.crosswind_sigma_growth = getParam("saisc.sepf.crosswind_sigma_growth", 0.30);
    pf_config_.downwind_decay_length_m = getParam("saisc.sepf.downwind_decay_length_m", 15.0);
    pf_config_.default_wind_sigma_rad =
        getParam("saisc.sepf.wind_sigma_deg", 15.0) * uav_gsl::kPi / 180.0;
    pf_config_.resample_ess_ratio = getParam("saisc.sepf.resample_ess_ratio", 0.45);

    audit_file_ = getParam("saisc.audit_file", std::string("saisc_pf_audit.csv"));
    // Ablation flags - use bool getParam
    use_sdbe_ = getParam("saisc.use_sdbe", 1) != 0;
    use_iasc_ = getParam("saisc.use_iasc", 1) != 0;
    use_sepf_ = getParam("saisc.use_sepf", 1) != 0;

    // Initialize Posterior Contraction Rate Declaration
    uav_gsl::PosteriorContractionDeclaration::Config pcr_cfg;
    pcr_cfg.particle_count = static_cast<std::size_t>(getParam("saisc.sepf.particles", 1500));
    pcr_cfg.window_seconds = getParam("saisc.pcr.window_seconds", 8.0);
    pcr_cfg.min_declare_seconds = getParam("saisc.pcr.min_declare_seconds", 10.0);
    pcr_cfg.significance_level = getParam("saisc.pcr.significance_level", 0.05);
    pcr_decl_ = std::make_unique<uav_gsl::PosteriorContractionDeclaration>(pcr_cfg);

    // Reconstruct modules only after ROS parameters are loaded.
    sensor_ = uav_gsl::SensorBoutEstimator(sensor_config_);
    policy_ = uav_gsl::AdaptiveSurgeCast(policy_config_);
}

void SensorAwareSurgeCastPF::Initialize() {
    SurgeCast::Initialize();
    last_gas_time_s_ = node->now().seconds();
    last_check_s_ = 0.0;
    best_estimate_valid_ = false;
    best_cov_trace_ = 1e9;
    prev_estimate_valid_ = false;
    stable_count_ = 0;
    low_cov_count_ = 0;
    min_dist_to_estimate_ = 1e9;
    near_estimate_count_ = 0;
    very_near_estimate_count_ = 0;
    independent_bouts_ = 0;
    gt_source_reached_ = false;
    last_raw_hit_ = false;
    pf_updated_at_least_once_ = false;
    final_estimate_type_ = "unset";
    time_to_first_reliable_bout_s_ = std::numeric_limits<double>::quiet_NaN();
    last_bout_onset_s_ = std::numeric_limits<double>::quiet_NaN();
    reacquisition_times_s_.clear();
    raw_sample_count_ = 0;
    raw_hit_count_ = 0;
    sepf_update_count_ = 0;
    iasc_goal_count_ = 0;
    invalid_goal_count_ = 0;
    planning_failure_count_ = 0;
    pose_history_ = uav_gsl::PoseHistory(20.0);
    sensor_.reset();
    policy_.reset();
    if (pf_) { pf_.reset(); }
    latest_evidence_ = {};
    latest_estimate_ = {};
    recent_wind_directions_.clear();
    uav_gsl::PosteriorContractionDeclaration::Config pcr_cfg;
    pcr_cfg.particle_count = static_cast<std::size_t>(getParam("saisc.sepf.particles", 1500));
    pcr_cfg.window_seconds = getParam("saisc.pcr.window_seconds", 8.0);
    pcr_cfg.min_declare_seconds = getParam("saisc.pcr.min_declare_seconds", 10.0);
    pcr_cfg.significance_level = getParam("saisc.pcr.significance_level", 0.05);
    pcr_decl_ = std::make_unique<uav_gsl::PosteriorContractionDeclaration>(pcr_cfg);
}

void SensorAwareSurgeCastPF::OnUpdate() {
    SurgeCast::OnUpdate();
    const double px = currentRobotPose.pose.pose.position.x;
    const double py = currentRobotPose.pose.pose.position.y;
    pose_history_.push(node->now().seconds(), {px, py});
    // Track min distance to best PF estimate (not GT)
    if (best_estimate_valid_) {
        const double d = std::hypot(px - best_estimate_.mean.x, py - best_estimate_.mean.y);
        if (d < min_dist_to_estimate_) min_dist_to_estimate_ = d;
        if (d < 2.0) ++near_estimate_count_;
        if (d < 0.5) ++very_near_estimate_count_;
    }
    // Check declaration periodically (once per second) so it fires during movement
    {
        static double last_check_s = 0.0;
        const double now_s = node->now().seconds();
        if (currentResult == GSLResult::Running && now_s - last_check_s > 1.0) {
            last_check_s = now_s;
            currentResult = checkSourceFound();
        }
    }
}

float SensorAwareSurgeCastPF::gasCallback(
    const olfaction_msgs::msg::GasSensor::SharedPtr msg) {
    const float ppm = SurgeCast::gasCallback(msg);
    ++raw_sample_count_;
    const bool raw_hit_for_audit = ppm > thresholdGas;
    if (raw_hit_for_audit) ++raw_hit_count_;
    const double now_s = node->now().seconds();
    const double dt_s = last_gas_time_s_ < 0.0 ? 0.1 : std::max(1e-3, now_s - last_gas_time_s_);
    last_gas_time_s_ = now_s;
    latest_measurement_dt_s_ = dt_s;
    if (use_sdbe_) {
        latest_evidence_ = sensor_.update(ppm, dt_s);
        ++sdbe_update_count_;
    } else {
        const bool raw_hit = ppm > thresholdGas;
        latest_evidence_.raw = ppm;
        latest_evidence_.filtered = ppm;
        latest_evidence_.baseline = 0.0;
        latest_evidence_.latent_excess = std::max(0.0, static_cast<double>(ppm));
        latest_evidence_.noise_sigma = 0.0;
        latest_evidence_.z_score = raw_hit ? 1.0 : 0.0;
        latest_evidence_.hit_probability = raw_hit ? 1.0 : 0.0;
        latest_evidence_.confidence = 1.0;
        latest_evidence_.estimated_delay_s = 0.0;
        latest_evidence_.bout_onset = raw_hit && !last_raw_hit_;
        latest_evidence_.bout_offset = !raw_hit && last_raw_hit_;
        latest_evidence_.in_bout = raw_hit;
        last_raw_hit_ = raw_hit;
    }
    if (latest_evidence_.bout_onset) {
        ++independent_bouts_;
        if (!std::isfinite(time_to_first_reliable_bout_s_) && latest_evidence_.hit_probability >= sensor_config_.hit_on_probability) {
            time_to_first_reliable_bout_s_ = (node->now() - startTime).seconds();
        }
        if (std::isfinite(last_bout_onset_s_)) {
            reacquisition_times_s_.push_back(now_s - last_bout_onset_s_);
        }
        last_bout_onset_s_ = now_s;
    }
    return ppm;
}

void SensorAwareSurgeCastPF::ensureParticleFilterInitialized() {
    if (pf_) return;
    pf_config_.bounds.min_x = map.info.origin.position.x;
    pf_config_.bounds.min_y = map.info.origin.position.y;
    pf_config_.bounds.max_x = pf_config_.bounds.min_x + map.info.width * map.info.resolution;
    pf_config_.bounds.max_y = pf_config_.bounds.min_y + map.info.height * map.info.resolution;
    pf_ = std::make_unique<uav_gsl::SoftEvidenceParticleFilter>(pf_config_);
    pf_->initializeUniform([this](const uav_gsl::Vec2& p) {
        return isPointFree(Vector2(p.x, p.y));
    });
}

double SensorAwareSurgeCastPF::windConcentration() const {
    if (recent_wind_directions_.empty()) return 0.0;
    double sum_cos = 0.0;
    double sum_sin = 0.0;
    for (double angle : recent_wind_directions_) {
        sum_cos += std::cos(angle);
        sum_sin += std::sin(angle);
    }
    return std::hypot(sum_cos, sum_sin) /
           static_cast<double>(recent_wind_directions_.size());
}

void SensorAwareSurgeCastPF::processGasAndWindMeasurements(
    double concentration, double windSpeed, double windDirection) {
    (void)concentration;
    recent_wind_directions_.push_back(windDirection);
    if (recent_wind_directions_.size() > 30) recent_wind_directions_.pop_front();

    const double now_s = node->now().seconds();
    double posterior_spread_m = 0.0;

    if (use_sepf_) {
        ensureParticleFilterInitialized();
        const double delay = use_sdbe_ ? latest_evidence_.estimated_delay_s : 0.0;
        const uav_gsl::Vec2 sensing_position = pose_history_.delayCompensated(now_s, delay);
        uav_gsl::SoftEvidenceParticleFilter::Observation observation;
        observation.sensing_position = sensing_position;
        observation.hit_probability = latest_evidence_.hit_probability;
        observation.evidence_confidence = latest_evidence_.confidence;
        observation.wind_flow_to_rad = windDirection;
        observation.wind_speed = windSpeed;
        observation.wind_sigma_rad = pf_config_.default_wind_sigma_rad;
        observation.dt_s = std::max(0.01, latest_measurement_dt_s_);
        latest_estimate_ = pf_->update(observation, [this](const uav_gsl::Vec2& p) {
            return isPointFree(Vector2(p.x, p.y));
        });
        ++sepf_update_count_;
        pf_updated_at_least_once_ = true;
        posterior_spread_m = std::sqrt(std::max(0.0, latest_estimate_.covariance_trace));
        if (pcr_decl_) {
            const double entropy_est = 0.5 * std::log(std::max(1e-12, latest_estimate_.covariance_trace));
            pcr_decl_->addSnapshot(now_s, latest_estimate_.covariance_trace, entropy_est);
        }
    } else {
        latest_estimate_.mean = {currentRobotPose.pose.pose.position.x,
                                 currentRobotPose.pose.pose.position.y};
        latest_estimate_.covariance_trace = std::numeric_limits<double>::quiet_NaN();
        latest_estimate_.effective_sample_size = 0.0;
    }

    if (!use_iasc_) {
        SurgeCast::processGasAndWindMeasurements(concentration, windSpeed, windDirection);
        return;
    }

    uav_gsl::AdaptiveSurgeCast::Input policy_input;
    policy_input.time_s = now_s;
    policy_input.hit_probability = latest_evidence_.hit_probability;
    policy_input.evidence_confidence = latest_evidence_.confidence;
    policy_input.wind_speed = windSpeed;
    policy_input.wind_direction_rad = windDirection;
    policy_input.wind_concentration = windConcentration();
    policy_input.posterior_spread_m = use_sepf_ ? posterior_spread_m : 1.0;

    auto decision = policy_.decide(policy_input);

    // Chemotaxis-inspired Linger Module (CLM)
    const double hit_prob = latest_evidence_.hit_probability;
    if (hit_prob > 0.5 && use_iasc_) {
        const double linger_factor = std::max(0.20, 1.0 - hit_prob);
        decision.step_m *= linger_factor;
        if (decision.step_m < 0.3) decision.step_m = 0.3;
    }

    sendAdaptiveGoal(decision);
    ++iasc_goal_count_;
}

void SensorAwareSurgeCastPF::sendAdaptiveGoal(
    const uav_gsl::AdaptiveSurgeCast::Decision& decision) {
    NavigateToPose::Goal goal;
    double step = decision.step_m;
    bool valid = false;
    for (int attempt = 0; attempt < 15 && step >= 0.2; ++attempt) {
        goal.pose.header.frame_id = "map";
        goal.pose.header.stamp = node->now();
        goal.pose.pose.position.x = currentRobotPose.pose.pose.position.x +
                                    step * std::cos(decision.heading_rad);
        goal.pose.pose.position.y = currentRobotPose.pose.pose.position.y +
                                    step * std::sin(decision.heading_rad);
        goal.pose.pose.orientation =
            Utils::createQuaternionMsgFromYaw(angles::normalize_angle(decision.heading_rad));
        if (movingState->checkGoal(goal)) {
            valid = true;
            break;
        }
        step -= 0.2;
        ++invalid_goal_count_;
    }
    if (!valid) {
        ++planning_failure_count_;
        setExplorationGoal();
        return;
    }

    auto* moving = dynamic_cast<MovingStatePlumeTracking*>(movingState.get());
    if (!moving) throw std::runtime_error("unexpected moving state type");
    switch (decision.mode) {
        case uav_gsl::AdaptiveSurgeCast::Mode::Surge:
            moving->currentMovement = PTMovement::FollowPlume;
            break;
        case uav_gsl::AdaptiveSurgeCast::Mode::Cast:
            moving->currentMovement = PTMovement::RecoverPlume;
            break;
        case uav_gsl::AdaptiveSurgeCast::Mode::Explore:
            moving->currentMovement = PTMovement::Exploration;
            break;
    }
    movingState->sendGoal(goal);
}

GSLResult SensorAwareSurgeCastPF::checkSourceFound() {
    const double elapsed_s = (node->now() - startTime).seconds();

    if (!use_sepf_) {
        if (elapsed_s > resultLogging.maxSearchTime) {
            saveResultsToFile(GSLResult::Failure);
            return GSLResult::Failure;
        }
        return GSLResult::Running;
    }

    if (elapsed_s > resultLogging.maxSearchTime) {
        // On timeout, use best estimate instead of current
        if (best_estimate_valid_) {
            latest_estimate_ = best_estimate_;
        }
        saveResultsToFile(GSLResult::Failure);
        return GSLResult::Failure;
    }
    if (!pf_) return GSLResult::Running;

    const auto est = pf_->estimate();
    const double cov_trace = est.covariance_trace;
    const double spread = std::sqrt(std::max(0.0, cov_trace));

    // Track best estimate (lowest covariance)
    if (!best_estimate_valid_ || cov_trace < best_cov_trace_) {
        best_estimate_ = est;
        best_cov_trace_ = cov_trace;
        best_estimate_valid_ = true;
    }

    // Track consecutive low-covariance readings
    if (cov_trace < 3.0) {
        ++low_cov_count_;
    } else {
        low_cov_count_ = 0;
    }

    // Track estimate stability
    if (prev_estimate_valid_) {
        const double drift = std::hypot(est.mean.x - prev_estimate_.x, est.mean.y - prev_estimate_.y);
        if (drift < 0.5) {
            ++stable_count_;
        } else {
            stable_count_ = 0;
        }
    }
    prev_estimate_ = est.mean;
    prev_estimate_valid_ = true;

    // Declaration: PCR-D (Posterior Contraction Rate Declaration)
    // Theory-driven: declares when posterior has stopped contracting
    // No hand-tuned thresholds - adapts to particle count automatically
    const bool pcr_declare = pcr_decl_ && pcr_decl_->shouldDeclare(elapsed_s);

    if (pcr_declare) {
        const bool posterior_converged = (cov_trace < 1.0);
        const bool evidence_sufficient = (independent_bouts_ >= 4);
        const bool estimate_stable = (stable_count_ >= 3);
        if (posterior_converged && evidence_sufficient && estimate_stable) {
            if (best_estimate_valid_ && best_cov_trace_ < cov_trace) {
                latest_estimate_ = best_estimate_;
            }
            saveResultsToFile(GSLResult::Success);
            return GSLResult::Success;
        }
    }

    return GSLResult::Running;
}

void SensorAwareSurgeCastPF::saveResultsToFile(GSLResult result) {
    if (pf_) latest_estimate_ = pf_->estimate();
    const double dx = latest_estimate_.mean.x - resultLogging.sourcePositionGT.x;
    const double dy = latest_estimate_.mean.y - resultLogging.sourcePositionGT.y;
    const double final_error_m = std::hypot(dx, dy);

    const double elapsed_s = (node->now() - startTime).seconds();
    const bool declared_success = result == GSLResult::Success;
    const bool timeout = result == GSLResult::Failure &&
                         elapsed_s >= resultLogging.maxSearchTime;

    if (use_sepf_) {
        if (pf_ && pf_updated_at_least_once_) {
            final_estimate_type_ = "sepf_mean";
        } else {
            final_estimate_type_ = "sepf_missing";
        }
    } else {
        final_estimate_type_ = "terminal_pose";
    }
    const std::string estimate_type = final_estimate_type_;

    std::ofstream output(audit_file_, std::ios::app);
    if (output.tellp() == 0) {
        output << "run_id,status,declared_success,timeout,estimate_type,"
               << "estimate_x,estimate_y,gt_x,gt_y,"
               << "final_error_m,localized_success_05m,localized_success_1m,"
               << "localized_success_2m,"
               << "use_sdbe,use_iasc,use_sepf,"
               << "p_hit,bout_count,raw_sample_count,raw_hit_count,"
               << "cov_trace,ess,sdbe_update_count,sepf_update_count,"
               << "iasc_goal_count,invalid_goal_count,planning_failure_count,"
               << "search_time_s\n";
    }
    output << std::setprecision(10)
           << "run" << ','
           << static_cast<int>(result) << ','
           << declared_success << ',' << timeout << ','
           << estimate_type << ','
           << latest_estimate_.mean.x << ',' << latest_estimate_.mean.y << ','
           << resultLogging.sourcePositionGT.x << ',' << resultLogging.sourcePositionGT.y << ','
           << final_error_m << ','
           << (final_error_m <= 0.5) << ',' << (final_error_m <= 1.0) << ','
           << (final_error_m <= 2.0) << ','
           << static_cast<int>(use_sdbe_) << ','
           << static_cast<int>(use_iasc_) << ','
           << static_cast<int>(use_sepf_) << ','
           << latest_evidence_.hit_probability << ',' << independent_bouts_ << ','
           << raw_sample_count_ << ',' << raw_hit_count_ << ','
           << latest_estimate_.covariance_trace << ','
           << latest_estimate_.effective_sample_size << ','
           << sdbe_update_count_ << ','
           << sepf_update_count_ << ','
           << iasc_goal_count_ << ',' << invalid_goal_count_ << ',' << planning_failure_count_ << ','
           << elapsed_s << '\n';
    output.close();

    Algorithm::saveResultsToFile(result);
}

}  // namespace GSL
