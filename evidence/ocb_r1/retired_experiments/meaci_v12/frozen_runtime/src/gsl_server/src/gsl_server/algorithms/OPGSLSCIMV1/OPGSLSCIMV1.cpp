#include "TransportModel.hpp"
#include "OPGSLSCIMV1.hpp"

#include <gsl_server/algorithms/Common/States/StopAndMeasureState.hpp>
#include <gsl_server/algorithms/Common/States/WaitForGasState.hpp>
#include <gsl_server/algorithms/Common/States/WaitForMapState.hpp>
#include <gsl_server/core/Logging.hpp>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <exception>
#include <filesystem>
#include <functional>
#include <iomanip>
#include <limits>
#include <numeric>
#include <set>
#include <sstream>
#include <stdexcept>
#include <utility>

namespace GSL {
namespace {

class ScopeExit {
public:
    explicit ScopeExit(std::function<void()> callback)
        : callback_(std::move(callback)) {}
    ScopeExit(const ScopeExit&) = delete;
    ScopeExit& operator=(const ScopeExit&) = delete;
    ~ScopeExit() { callback_(); }

private:
    std::function<void()> callback_;
};

void ensureParentDirectory(const std::string& file_path) {
    if (file_path.empty()) return;
    const std::filesystem::path path(file_path);
    if (path.has_parent_path()) std::filesystem::create_directories(path.parent_path());
}

std::int64_t coordinateKey(double x, double y, double z, double resolution) {
    const double safe = std::max(resolution, 1e-3);
    const auto ix = static_cast<std::int64_t>(std::llround(x / safe));
    const auto iy = static_cast<std::int64_t>(std::llround(y / safe));
    const auto iz = static_cast<std::int64_t>(std::llround(z / safe));
    return (ix * 73856093LL) ^ (iy * 19349663LL) ^ (iz * 83492791LL);
}

}  // namespace

OPGSLSCIMV1::OPGSLSCIMV1(std::shared_ptr<rclcpp::Node> node)
    : Algorithm(std::move(node)) {}

void OPGSLSCIMV1::declareParameters() {
    Algorithm::declareParameters();
    runtime_config_.scientific_mode = getParam<bool>("opgsl.v3.scientific_mode", true);
    runtime_config_.grid_nx = getParam<int>("opgsl.v3.grid.nx", 30);
    runtime_config_.grid_ny = getParam<int>("opgsl.v3.grid.ny", 30);
    runtime_config_.grid_nz = getParam<int>("opgsl.v3.grid.nz", 1);
    runtime_config_.source_z_min = getParam<double>("opgsl.v3.grid.source_z_min", 0.0);
    runtime_config_.source_z_max = getParam<double>("opgsl.v3.grid.source_z_max", 0.0);
    runtime_config_.nominal_flight_height = getParam<double>("opgsl.v3.flight.nominal_height", 0.3);
    runtime_config_.min_flight_height = getParam<double>("opgsl.v3.flight.min_height", runtime_config_.nominal_flight_height);
    runtime_config_.max_flight_height = getParam<double>("opgsl.v3.flight.max_height", runtime_config_.nominal_flight_height);
    runtime_config_.angular_samples = getParam<int>("opgsl.v3.actions.angular_samples", 16);
    runtime_config_.radial_samples = getParam<int>("opgsl.v3.actions.radial_samples", 2);
    runtime_config_.min_action_radius = getParam<double>("opgsl.v3.actions.min_radius", 0.6);
    runtime_config_.max_action_radius = getParam<double>("opgsl.v3.actions.max_radius", 1.8);
    runtime_config_.max_steps = getParam<int>("opgsl.v3.max_steps", 300);
    runtime_config_.seed = getParam<int>("opgsl.v3.seed", 0);
    runtime_config_.m1_intercept = getParam<double>("opgsl.scim.m1_intercept", runtime_config_.m1_intercept);
    runtime_config_.m1_distance_decay = getParam<double>("opgsl.scim.m1_distance_decay", runtime_config_.m1_distance_decay);
    runtime_config_.cell_size = getParam<double>("opgsl.scim.cell_size", 1.0);
    runtime_config_.cell_size_fallback = getParam<bool>("opgsl.scim.cell_size_fallback", false);
    runtime_config_.min_history = getParam<int>("opgsl.scim.min_history", 4);
    runtime_config_.enable_ncl = getParam<bool>("opgsl.scim.enable_ncl", false);
    runtime_config_.candidate_cap = getParam<int>("opgsl.scim.candidate_cap", 64);
    runtime_config_.verifier_enabled = getParam<bool>("opgsl.scim.verifier_enabled", false);
    runtime_config_.navigation_timeout_seconds = getParam<double>(
        "opgsl.scim.navigation_timeout_seconds", 6.0);
    runtime_config_.force_first_batch_unreachable = getParam<bool>(
        "opgsl.scim.test.force_first_batch_unreachable", false);
    runtime_config_.require_compute_path_check = getParam<bool>(
        "opgsl.scim.navigation.require_compute_path_check", false);
    runtime_config_.raiom_mode = getParam<std::string>("raiom.mode", "M0");
    runtime_config_.grtom_enabled = getParam<bool>("grtom.enabled", runtime_config_.raiom_mode != "M0");
    runtime_config_.snoed_enabled = getParam<bool>("snoed.enabled", runtime_config_.raiom_mode == "M2-SNOED");
    runtime_config_.qams_enabled = getParam<bool>("qams.enabled", false);
    runtime_config_.snoed_tau_seconds = getParam<double>("raiom.snoed.tau_seconds", 2.0);
    runtime_config_.snoed_dead_time_seconds = getParam<double>("raiom.snoed.dead_time_seconds", 0.2);
    runtime_config_.tess_enabled = getParam<bool>("opgsl.scim.use_tess", false);
    runtime_config_.tess_shadow_only = getParam<bool>("opgsl.scim.tess_shadow_only", true);
    runtime_config_.tess_takeover_enabled = getParam<bool>("opgsl.scim.tess_takeover_enabled", false);
    runtime_config_.tess_profile_estimate_enabled = getParam<bool>("opgsl.scim.tess_profile_estimate_enabled", false);
    runtime_config_.tess_active_stop = getParam<bool>("opgsl.scim.tess_active_stop", false);
    runtime_config_.tess_use_qam = getParam<bool>("opgsl.scim.tess_use_qam", false);
    runtime_config_.tess_max_competitors = getParam<int>("opgsl.scim.tess_max_competitors", 4);
    runtime_config_.tess_log_variance_floor = getParam<double>("opgsl.scim.tess_log_variance_floor", 1e-4);
    runtime_config_.tess_model_discrepancy_variance = getParam<double>("opgsl.scim.tess_model_discrepancy_variance", 0.05);
    runtime_config_.tess_model_discrepancy_provenance = getParam<std::string>(
        "opgsl.scim.tess_model_discrepancy_provenance", "FROZEN_GLOBAL_PILOT_V1");
    runtime_config_.tess_max_navigation_seconds = getParam<double>(
        "opgsl.scim.tess_max_navigation_seconds", runtime_config_.navigation_timeout_seconds);
    tess_common_model_discrepancy_variance_ = std::max(0.0, runtime_config_.tess_model_discrepancy_variance);
    runtime_config_.tess_min_corrected = getParam<double>("opgsl.scim.tess_min_corrected_concentration", 1e-6);
    runtime_config_.tess_min_effective_samples = getParam<int>("opgsl.scim.tess_min_effective_samples", 3);
    runtime_config_.tess_tau_seconds = getParam<double>("opgsl.scim.tess_tau_seconds", 1.2);
    runtime_config_.tess_dead_time_seconds = getParam<double>("opgsl.scim.tess_dead_time_seconds", 0.4);
    runtime_config_.tess_p_valid_min = getParam<double>("opgsl.scim.tess_p_valid_min", 0.5);
    runtime_config_.tess_warmup_blocks = getParam<int>("opgsl.scim.tess_warmup_blocks", 8);
    runtime_config_.tess_candidate_nms_radius_m = getParam<double>("opgsl.scim.tess_candidate_nms_radius_m", 1.0);
    runtime_config_.tess_takeover_absolute_margin = getParam<double>("opgsl.scim.tess_takeover_absolute_margin", 1e-6);
    runtime_config_.tess_takeover_relative_margin = getParam<double>("opgsl.scim.tess_takeover_relative_margin", 0.05);
    runtime_config_.tess_duration_slack_seconds = getParam<double>("opgsl.scim.tess_duration_slack_seconds", 0.5);
    runtime_config_.tess_profile_prior_power = getParam<double>("opgsl.scim.tess_profile_prior_power", 0.0);
    runtime_config_.tess_linear_drift = getParam<bool>("opgsl.scim.tess_linear_drift", false);
    runtime_config_.tess_background_concentration = getParam<double>("opgsl.scim.tess_background_concentration", 0.0);
    runtime_config_.tess_scenario_log_wind_step = getParam<double>("opgsl.scim.tess_scenario_log_wind_step", 0.10);
    runtime_config_.tess_scenario_log_diffusion_step = getParam<double>("opgsl.scim.tess_scenario_log_diffusion_step", 0.10);
    runtime_config_.transport_graph_spacing_cells = getParam<int>("opgsl.scim.transport_graph_spacing_cells", 5);
    const bool requested_transport = getParam<bool>("opgsl.scim.use_transport_model", runtime_config_.grtom_enabled);
    use_transport_model_ = runtime_config_.grtom_enabled || requested_transport || runtime_config_.tess_enabled;

    planner_config_.horizontal_speed_mps = getParam<double>("opgsl.v3.platform.horizontal_speed_mps", 0.4);
    planner_config_.vertical_speed_mps = getParam<double>("opgsl.v3.platform.vertical_speed_mps", 0.2);
    planner_config_.measurement_dwell_seconds = getParam<double>("stop_and_measure_time", 2.0);
    planner_config_.vertical_actions_requested = false;
    verification_config_.credible_mass = getParam<double>("opgsl.v3.stop.credible_mass", 0.90);
    verification_config_.target_credible_radius_m = getParam<double>("opgsl.v3.stop.target_credible_radius_m", 1.5);

    run_uuid_ = getParam<std::string>("run_uuid", "opgsl_scim_v1");
    source_estimate_trace_file_ = getParam<std::string>("source_estimate_trace_file", "");
    evidence_trace_file_ = getParam<std::string>("opgsl.v3.trace.evidence", "");
    planner_trace_file_ = getParam<std::string>("opgsl.v3.trace.planner", "");
    stop_trace_file_ = getParam<std::string>("opgsl.v3.trace.stop", "");
    parameter_snapshot_file_ = getParam<std::string>("opgsl.v3.trace.parameter_snapshot", "");
    candidate_trace_file_ = getParam<std::string>("opgsl.v3.trace.candidate", "");
    scim_memory_trace_file_ = getParam<std::string>("opgsl.scim.trace.memory", "");
    scim_contrast_trace_file_ = getParam<std::string>("opgsl.scim.trace.contrast", "");
    scim_action_trace_file_ = getParam<std::string>("opgsl.scim.trace.action", "");
    action_validity_trace_file_ = getParam<std::string>("raiom.trace.action_validity", "");
    declaration_trace_file_ = getParam<std::string>("raiom.trace.declaration", "");
    tess_block_trace_file_ = getParam<std::string>("opgsl.scim.tess.trace.blocks", "");
    tess_source_trace_file_ = getParam<std::string>("opgsl.scim.tess.trace.source", "");
    tess_decision_trace_file_ = getParam<std::string>("opgsl.scim.tess.trace.decision", "");
    tess_pair_detail_trace_file_ = getParam<std::string>("opgsl.scim.tess.trace.pair", "");
    tess_reject_trace_file_ = getParam<std::string>("opgsl.scim.tess.trace.reject", "");
    tess_region_trace_file_ = getParam<std::string>("opgsl.scim.tess.trace.region", "");
    candidate_trace_top_k_ = std::max(1, getParam<int>("opgsl.v3.trace.top_k", 10));

    observation_model_.model_id = 1;
    observation_model_.nominal = true;
    observation_model_.prior_weight = 1.0;
    observation_model_.isotropic_intercept = runtime_config_.m1_intercept;
    observation_model_.isotropic_distance_decay = runtime_config_.m1_distance_decay;
    observation_model_.wind_intercept = runtime_config_.m1_intercept;
    observation_model_.downwind_distance_decay = 1.0;
    observation_model_.upstream_distance_decay = 1.0;
    observation_model_.crosswind_squared_decay = 1.0;
    observation_model_.vertical_squared_decay = 1.0;
    observation_model_.wind_noise_speed_sigma = getParam<double>("opgsl.scim.wind_noise_sigma", 0.2);
    double miss_w = getParam<double>("opgsl.scim.miss_weight", 1.0);
    posterior_.miss_weight = miss_w;
    posterior_.use_adaptive_pd = getParam<bool>("opgsl.scim.use_adaptive_pd", false);
    posterior_.pd_estimator.sigma = getParam<double>("opgsl.scim.pd_sigma", 3.0);
    if (posterior_.use_adaptive_pd) GSL_INFO("OPGSLSCIMV1: adaptive p_d enabled, sigma={}", posterior_.pd_estimator.sigma);
    posterior_.cat_delta = getParam<double>("opgsl.scim.cat_delta", 0.0);
    posterior_.cat_gamma = getParam<double>("opgsl.scim.cat_gamma", 2.0);
    posterior_.cat_alpha_min = getParam<double>("opgsl.scim.cat_alpha_min", 0.3);
    if (posterior_.cat_delta > 0.0) GSL_INFO("OPGSLSCIMV1: CAT enabled, delta={}, gamma={}, alpha_min={}", posterior_.cat_delta, posterior_.cat_gamma, posterior_.cat_alpha_min);

    GSL_INFO("OPGSLSCIMV1: miss_weight=%%f", miss_w);
    scientific_trace_valid_ = true;
}

void OPGSLSCIMV1::Initialize() {
    waitForMapState = std::make_unique<WaitForMapState>(this);
    waitForGasState = std::make_unique<WaitForGasState>(this);
    stopAndMeasureState = std::make_unique<StopAndMeasureState>(this);
    movingState = std::make_unique<MovingStateOPGSLSCIMV1>(this);
    Algorithm::Initialize();
    planner_busy_pub_ = node->create_publisher<std_msgs::msg::Bool>("opgsl_planner_busy", 1);
    simulation_pause_client_ =
        node->create_client<std_srvs::srv::SetBool>("set_simulation_paused");
    rng_.seed(static_cast<std::mt19937::result_type>(runtime_config_.seed));
    initializeTraceFiles();
    writeParameterSnapshot();
    stateMachine.forceSetState(waitForMapState.get());
}

void OPGSLSCIMV1::onGetMap(const OccupancyGrid::SharedPtr msg) {
    Algorithm::onGetMap(msg);
    map_received_ = true;
    initializePosteriorFromMap();
    stateMachine.forceResetState(stopAndMeasureState.get());
}

std::vector<bool> OPGSLSCIMV1::buildSourceValidityMask(const OPGSLV3::GridSpec& spec) {
    const double dx = (spec.x_max - spec.x_min) / static_cast<double>(spec.nx);
    const double dy = (spec.y_max - spec.y_min) / static_cast<double>(spec.ny);
    std::vector<bool> mask(static_cast<std::size_t>(spec.nx) * spec.ny * spec.nz, false);
    std::size_t index = 0;
    for (int i = 0; i < spec.nx; ++i) {
        for (int j = 0; j < spec.ny; ++j) {
            const bool free = isPointFree(Vector2(
                spec.x_min + (static_cast<double>(i) + 0.5) * dx,
                spec.y_min + (static_cast<double>(j) + 0.5) * dy));
            for (int k = 0; k < spec.nz; ++k) mask[index++] = free;
        }
    }
    return mask;
}

void OPGSLSCIMV1::initializePosteriorFromMap() {
    if (posterior_initialized_) return;
    if (!map_received_ || map.info.width == 0 || map.info.height == 0 || map.info.resolution <= 0.0) {
        throw std::runtime_error("Cannot initialize SCIM posterior without a valid map");
    }
    OPGSLV3::GridSpec spec;
    spec.nx = runtime_config_.grid_nx; spec.ny = runtime_config_.grid_ny; spec.nz = runtime_config_.grid_nz;
    spec.x_min = map.info.origin.position.x;
    spec.x_max = spec.x_min + static_cast<double>(map.info.width) * map.info.resolution;
    spec.y_min = map.info.origin.position.y;
    spec.y_max = spec.y_min + static_cast<double>(map.info.height) * map.info.resolution;
    spec.z_min = runtime_config_.source_z_min;
    spec.z_max = runtime_config_.grid_nz > 1 ? runtime_config_.source_z_max : runtime_config_.source_z_min;
    const auto mask = buildSourceValidityMask(spec);
    std::ostringstream descriptor;
    descriptor << std::setprecision(17) << spec.nx << ',' << spec.ny << ',' << spec.nz << ','
               << spec.x_min << ',' << spec.x_max << ',' << spec.y_min << ',' << spec.y_max;
    for (const bool value : mask) descriptor << (value ? '1' : '0');
    source_grid_hash_ = stableTraceHash(descriptor.str());
    posterior_.initialize(spec, mask, observation_model_, runtime_config_.enable_ncl);
    spatial_planner_.initialize(spec.x_min, spec.x_max, spec.y_min, spec.y_max,
                                runtime_config_.cell_size,
                                static_cast<std::size_t>(std::max(2, runtime_config_.min_history)),
                                static_cast<std::size_t>(std::max(2, runtime_config_.candidate_cap)));
        if (use_transport_model_) {
        std::vector<int8_t> occ(map.info.width * map.info.height);
        for (int ii = 0; ii < map.info.width * map.info.height; ++ii) {
            // Unknown occupancy is not valid transport/free space.
            occ[ii] = map.data[ii] == 0 ? 0 : 1;
        }
        transport_graph.buildFromGrid(occ.data(), map.info.width, map.info.height,
            map.info.origin.position.x, map.info.origin.position.y, map.info.resolution,
            std::max(1, runtime_config_.transport_graph_spacing_cells));
        transport_initialized_ = transport_graph.n_nodes > 0 && !transport_graph.edges.empty();
        if (!transport_initialized_) {
            GSL_ERROR("OPGSLSCIMV1: transport graph construction failed (nodes={}, edges={})",
                      transport_graph.n_nodes, transport_graph.edges.size());
        } else {
            GSL_INFO("OPGSLSCIMV1: RAIOM transport nodes={} edges={} components={}",
                     transport_graph.n_nodes, transport_graph.edges.size(), transport_graph.countComponents());
        }
    }
    posterior_initialized_ = true;
    GSL_INFO("OPGSLSCIMV1: valid_sources={} cell_size={} candidate_cap={}",
             posterior_.validSourceCount(), runtime_config_.cell_size, runtime_config_.candidate_cap);
}

OPGSLV3::ObservationContext OPGSLSCIMV1::makeObservationContext(
    double x, double y, double z, double concentration) const {
    OPGSLV3::ObservationContext context;
    context.sensor_x = x; context.sensor_y = y; context.sensor_z = z;
    context.wind_x = latest_wind_x_; context.wind_y = latest_wind_y_; context.wind_z = 0.0;
    context.wind_speed = latest_wind_speed_; context.concentration = concentration;
    context.detection_threshold = thresholdGas;
    return context;
}

void OPGSLSCIMV1::processGasAndWindMeasurements(double concentration,
                                                double windSpeed,
                                                double windDirection) {
    if (source_declared_) return;
    // Freeze simulation time before any posterior, transport, TESS or planner
    // work begins.  Pausing only inside planFeasibleActions is too late:
    // transport/profile refresh can consume scheduler-dependent replay ticks.
    acquireDeterministicPlannerPause();
    ScopeExit pause_guard([this]() { releaseDeterministicPlannerPause(); });
    if (!posterior_initialized_) initializePosteriorFromMap();
    elapsed_time_ = (node->now() - startTime).seconds();
    latest_concentration_ = concentration;
    latest_wind_speed_ = std::max(0.0, windSpeed);
    latest_wind_x_ = latest_wind_speed_ * std::cos(windDirection);
    latest_wind_y_ = latest_wind_speed_ * std::sin(windDirection);
    const double z = clipToFlightBounds(std::isfinite(currentRobotPose.pose.pose.position.z)
        ? currentRobotPose.pose.pose.position.z : runtime_config_.nominal_flight_height);
    const auto observation = makeObservationContext(currentRobotPosition.x, currentRobotPosition.y,
                                                    z, latest_concentration_);
    recordTessMeasurementBlock(latest_concentration_);
    const bool detected = latest_concentration_ > thresholdGas;
    const double omega = spatial_planner_.omegaAt(observation.sensor_x, observation.sensor_y);
    const double predictive = posterior_.predictiveHitProbability(observation);
    const auto pre_map = posterior_.mapProbabilities();
    writeCandidateTrace(observation, detected, pre_map, predictive);
    if (use_transport_model_ && transport_initialized_) {
        const auto A = transport_graph.buildMatrix(transport_params, latest_wind_x_, latest_wind_y_);
        const int sensor_node = transport_graph.nearestVisibleNode(currentRobotPosition.x, currentRobotPosition.y);
        std::vector<int> source_nodes; source_nodes.reserve(posterior_.validSourceCount());
        bool source_mapping_valid = sensor_node >= 0;
        for (std::size_t k = 0; k < posterior_.validSourceCount(); ++k) {
            const auto src = posterior_.sourceAtValidIndex(k);
            const int source_node = transport_graph.nearestVisibleNode(src.x, src.y);
            source_mapping_valid = source_mapping_valid && source_node >= 0;
            source_nodes.push_back(source_node);
        }
        std::vector<double> concentrations;
        raiom::SolverDiagnostics transport_diag;
        if (source_mapping_valid) {
            transport_diag = transport_graph.solveSensorAdjoint(
                A, sensor_node, source_nodes, transport_params.Q_source, concentrations);
        }
        if (transport_diag.success) {
            posterior_.precomputed_q.resize(source_nodes.size());
            for (std::size_t k = 0; k < source_nodes.size(); ++k)
                posterior_.precomputed_q[k] = raiom::concentrationToQ(concentrations[k], transport_params);
        }
    }
    const auto diagnostics = posterior_.update(observation, detected, omega);
        posterior_.clearPrecomputedQ();
    last_update_diagnostics_.detected = detected;
    last_update_diagnostics_.predictive_hit_probability = diagnostics.predictive_hit_probability;
    last_update_diagnostics_.source_brier = std::pow((detected ? 1.0 : 0.0) - predictive, 2.0);
    last_update_diagnostics_.source_nll = detected ? -std::log(predictive) : -std::log1p(-predictive);
    last_update_diagnostics_.entropy_before = diagnostics.map_entropy;
    last_update_diagnostics_.entropy_after = diagnostics.map_entropy;
    last_update_diagnostics_.normalization_error = 0.0;
    ++measurement_count_;
    detected ? ++hit_count_ : ++miss_count_;
    // Record detection for adaptive p_d
    if (posterior_.use_adaptive_pd) {
        posterior_.pd_estimator.record(currentRobotPosition.x, currentRobotPosition.y, detected ? 1 : 0);
    }

    markVisited(observation.sensor_x, observation.sensor_y, observation.sensor_z);
    const double discrimination = spatial_planner_.discrimination(observation, posterior_, observation_model_);
    spatial_planner_.recordExecuted(observation, detected, discrimination, elapsed_time_);
    if (runtime_config_.tess_enabled) refreshTessProfiles();
    const auto map_summary = posterior_.mapSummary(verification_config_.credible_mass);
    const auto confidence_summary = posterior_.confidenceSummary(verification_config_.credible_mass);
    writeEvidenceTrace(map_summary, confidence_summary);
    writeSourceEstimateTrace(map_summary, confidence_summary);
    writeSCIMMemoryTrace();
    writeSCIMContrastTrace();
    const GSLResult result = checkSourceFound();
    if (result != GSLResult::Running) {
        currentResult = result; source_declared_ = true;
        writeStopTrace(map_summary, confidence_summary, "budget_or_step_failure", result);
        saveResultsToFile(result); return;
    }
    movingState->chooseGoalAndMove();
}

GSLResult OPGSLSCIMV1::checkSourceFound() {
    elapsed_time_ = (node->now() - startTime).seconds();
    // A planner retry limit is not a scientific terminal condition.  The only
    // automatic completion in this fixed-budget protocol is elapsed time.
    if (elapsed_time_ >= resultLogging.maxSearchTime) {
        end_reason_ = "TIME_BUDGET_REACHED";
        return GSLResult::Failure;
    }
    return GSLResult::Running;
}

void OPGSLSCIMV1::forceSimulationTimeBudgetReached() {
    if (end_reason_ == "TIME_BUDGET_REACHED") return;
    end_reason_ = "TIME_BUDGET_REACHED";
    source_declared_ = true;
    currentResult = GSLResult::Failure;
    elapsed_time_ = (node->now() - startTime).seconds();
    saveResultsToFile(GSLResult::Failure);
}

std::vector<OPGSLV3::FeasibleAction> OPGSLSCIMV1::generateRecoveryActions() {
    std::vector<OPGSLV3::FeasibleAction> actions;
    if (!posterior_initialized_ || !map_received_) return actions;
    const double z = clipToFlightBounds(std::isfinite(currentRobotPose.pose.pose.position.z)
        ? currentRobotPose.pose.pose.position.z : runtime_config_.nominal_flight_height);
    const double resolution = std::max(0.05, static_cast<double>(map.info.resolution));
    std::set<std::int64_t> seen;
    const auto append = [&](double x, double y) {
        if (!isPointInsideSensorSafeBounds(x, y)) {
            writeActionValidityTrace(x, y, z, false, "MEASUREMENT_INVALID"); return;
        }
        if (!isPointFree(Vector2(x, y))) {
            writeActionValidityTrace(x, y, z, false, "OCCUPIED"); return;
        }
        const auto key = coordinateKey(x, y, z, resolution);
        if (!seen.insert(key).second) {
            writeActionValidityTrace(x, y, z, false, "MEASUREMENT_INVALID"); return;
        }
        OPGSLV3::FeasibleAction action;
        action.x = x; action.y = y; action.z = z;
        action.type = OPGSLV3::ActionType::PlanarTraverse;
        action.visit_count = visitCount(x, y, z);
        actions.push_back(action);
        writeActionValidityTrace(x, y, z, true, "VALID");
    };
    // Radius is progressively reduced after the normal candidate set is
    // exhausted; every angular candidate is retained for reachability checks.
    for (const double radius : {runtime_config_.min_action_radius * 0.75,
                                runtime_config_.min_action_radius * 0.40,
                                resolution}) {
        for (int a = 0; a < std::max(8, runtime_config_.angular_samples); ++a) {
            const double angle = 2.0 * OPGSLV3::kPi * static_cast<double>(a) /
                static_cast<double>(std::max(8, runtime_config_.angular_samples));
            append(currentRobotPosition.x + radius * std::cos(angle),
                   currentRobotPosition.y + radius * std::sin(angle));
        }
    }
    // A completed navigation is a verified reachable frontier; preserve it as
    // the final recovery tier without creating a measurement episode.
    for (const auto& frontier : verified_frontiers_) append(frontier.x, frontier.y);
    return actions;
}

std::vector<OPGSLV3::FeasibleAction> OPGSLSCIMV1::generateMapFeasibleActions() {
    std::vector<OPGSLV3::FeasibleAction> actions;
    if (!posterior_initialized_ || !map_received_) return actions;
    const double z = clipToFlightBounds(std::isfinite(currentRobotPose.pose.pose.position.z)
        ? currentRobotPose.pose.pose.position.z : runtime_config_.nominal_flight_height);
    std::set<std::int64_t> seen;
    const double resolution = std::max(0.05, static_cast<double>(map.info.resolution));
    for (int r = 0; r < std::max(1, runtime_config_.radial_samples); ++r) {
        const double fraction = runtime_config_.radial_samples <= 1 ? 1.0 :
            static_cast<double>(r) / static_cast<double>(runtime_config_.radial_samples - 1);
        const double radius = runtime_config_.min_action_radius + fraction *
            (runtime_config_.max_action_radius - runtime_config_.min_action_radius);
        for (int a = 0; a < std::max(1, runtime_config_.angular_samples); ++a) {
            const double angle = 2.0 * OPGSLV3::kPi * static_cast<double>(a) /
                                 static_cast<double>(std::max(1, runtime_config_.angular_samples));
            const double x = currentRobotPosition.x + radius * std::cos(angle);
            const double y = currentRobotPosition.y + radius * std::sin(angle);
            if (!isPointInsideSensorSafeBounds(x, y)) {
                writeActionValidityTrace(x, y, z, false, "MEASUREMENT_INVALID");
                continue;
            }
            if (!isPointFree(Vector2(x, y))) {
                writeActionValidityTrace(x, y, z, false, "OCCUPIED");
                continue;
            }
            const auto key = coordinateKey(x, y, z, resolution);
            if (!seen.insert(key).second) {
                writeActionValidityTrace(x, y, z, false, "MEASUREMENT_INVALID");
                continue;
            }
            OPGSLV3::FeasibleAction action;
            action.x = x; action.y = y; action.z = z;
            action.type = OPGSLV3::ActionType::PlanarTraverse;
            action.visit_count = visitCount(x, y, z);
            actions.push_back(action);
            writeActionValidityTrace(x, y, z, true, "VALID");
        }
    }
    return actions;
}

void OPGSLSCIMV1::ensureTessModelInitialized() {
    if (tess_model_initialized_) return;
    if (!posterior_initialized_ || !transport_initialized_ || transport_graph.n_nodes <= 0) return;

    tess_all_source_indices_.resize(posterior_.validSourceCount());
    std::iota(tess_all_source_indices_.begin(), tess_all_source_indices_.end(), 0U);
    tess_source_to_unique_.resize(tess_all_source_indices_.size());
    std::unordered_map<int, std::size_t> unique_lookup;
    for (std::size_t source = 0; source < tess_all_source_indices_.size(); ++source) {
        const auto point = posterior_.sourceAtValidIndex(source);
        const int node_id = transport_graph.nearestVisibleNode(point.x, point.y);
        if (node_id < 0) {
            GSL_ERROR("OPGSLSCIMV1 TESS-V4: source candidate {} cannot map to visible transport node", source);
            tess_model_initialized_ = false;
            return;
        }
        auto [iterator, inserted] = unique_lookup.emplace(node_id, tess_unique_source_nodes_.size());
        if (inserted) tess_unique_source_nodes_.push_back(node_id);
        tess_source_to_unique_[source] = iterator->second;
    }

    const auto scenarios = makeTessPhysicsScenarios(0.0, 0.0);
    tess_fopdt_bank_.assign(scenarios.size(),
        std::vector<tessv3::FopdtState>(tess_unique_source_nodes_.size()));
    const double floor = std::max(runtime_config_.tess_min_corrected, 1e-12);
    for (auto& scenario_bank : tess_fopdt_bank_) {
        for (auto& state : scenario_bank) {
            state = tessv3::makeFopdtState(floor, floor, runtime_config_.tess_dead_time_seconds);
        }
    }
    tess_model_initialized_ = true;
    GSL_INFO("OPGSLSCIMV1 TESS-V4: sources={} unique_transport_sources={} scenarios={}",
             tess_all_source_indices_.size(), tess_unique_source_nodes_.size(), scenarios.size());
}

std::vector<OPGSLSCIMV1::TessPhysicsScenario> OPGSLSCIMV1::makeTessPhysicsScenarios(
    double wind_x, double wind_y) const {
    const double wind_step = std::max(0.0, runtime_config_.tess_scenario_log_wind_step);
    const double diffusion_step = std::max(0.0, runtime_config_.tess_scenario_log_diffusion_step);
    const double wind_low = std::exp(-wind_step);
    const double wind_high = std::exp(wind_step);
    const double diffusion_low = std::exp(-diffusion_step);
    const double diffusion_high = std::exp(diffusion_step);

    std::vector<TessPhysicsScenario> scenarios;
    scenarios.reserve(5);
    scenarios.push_back({"nominal", transport_params, wind_x, wind_y});
    scenarios.push_back({"wind_low", transport_params, wind_low * wind_x, wind_low * wind_y});
    scenarios.push_back({"wind_high", transport_params, wind_high * wind_x, wind_high * wind_y});
    auto low_d = transport_params;
    low_d.D *= diffusion_low;
    scenarios.push_back({"diffusion_low", low_d, wind_x, wind_y});
    auto high_d = transport_params;
    high_d.D *= diffusion_high;
    scenarios.push_back({"diffusion_high", high_d, wind_x, wind_y});
    return scenarios;
}

bool OPGSLSCIMV1::solveTessScenarioFields(
    const std::vector<TessPhysicsScenario>& scenarios,
    std::vector<Eigen::MatrixXd>& fields, double* worst_residual) const {
    fields.clear();
    if (!transport_initialized_ || tess_unique_source_nodes_.empty() || scenarios.empty()) return false;
    fields.reserve(scenarios.size());
    double maximum_residual = 0.0;
    for (const auto& scenario : scenarios) {
        const auto matrix = transport_graph.buildMatrix(scenario.params, scenario.wind_x, scenario.wind_y);
        Eigen::MatrixXd field;
        const auto diagnostic = transport_graph.solveSteadyStateBatch(
            matrix, tess_unique_source_nodes_, scenario.params.Q_source, field);
        maximum_residual = std::max(maximum_residual, diagnostic.residual);
        if (!diagnostic.success || field.rows() != transport_graph.n_nodes ||
            field.cols() != static_cast<int>(tess_unique_source_nodes_.size())) {
            if (worst_residual) *worst_residual = maximum_residual;
            return false;
        }
        field = field.cwiseMax(0.0);
        fields.push_back(std::move(field));
    }
    if (worst_residual) *worst_residual = maximum_residual;
    return true;
}

std::vector<tessv3::InputSegment> OPGSLSCIMV1::makeTessExposureSegments(
    const Eigen::MatrixXd& field, int unique_source_column,
    double start_x, double start_y, double goal_x, double goal_y,
    double travel_seconds, double dwell_seconds) const {
    std::vector<tessv3::InputSegment> segments;
    if (unique_source_column < 0 || unique_source_column >= field.cols()) return segments;
    const auto path = transport_graph.shortestPathNodes(start_x, start_y, goal_x, goal_y);
    if (path.empty()) return segments;
    const double floor = std::max(runtime_config_.tess_min_corrected, 1e-12);
    const double path_length = transport_graph.pathLength(path);
    if (travel_seconds > 0.0) {
        if (path.size() == 1 || !(path_length > 0.0)) {
            const double value = std::max(floor, field(path.front(), unique_source_column));
            segments.push_back({travel_seconds, value});
        } else {
            for (std::size_t k = 1; k < path.size(); ++k) {
                const auto& left = transport_graph.nodes.at(static_cast<std::size_t>(path[k - 1]));
                const auto& right = transport_graph.nodes.at(static_cast<std::size_t>(path[k]));
                const double edge_length = std::hypot(right.cx - left.cx, right.cy - left.cy);
                const double duration = travel_seconds * edge_length / path_length;
                const double value = std::max(floor, 0.5 *
                    (field(path[k - 1], unique_source_column) + field(path[k], unique_source_column)));
                if (duration > 0.0) segments.push_back({duration, value});
            }
        }
    }
    if (dwell_seconds > 0.0) {
        const int endpoint = path.back();
        const double value = std::max(floor, field(endpoint, unique_source_column));
        segments.push_back({dwell_seconds, value});
    }
    return segments;
}

bool OPGSLSCIMV1::updateTessPhysicalModel(TessEpisode& episode) {
    ensureTessModelInitialized();
    if (!tess_model_initialized_) return false;
    const auto scenarios = makeTessPhysicsScenarios(episode.wind_x, episode.wind_y);
    std::vector<Eigen::MatrixXd> fields;
    double residual = 0.0;
    if (!solveTessScenarioFields(scenarios, fields, &residual) ||
        !std::isfinite(residual) || residual >= 1e-8) {
        return false;
    }

    // Transactional state update: a failed candidate/path/FOPDT computation
    // must never partially advance the persistent sensor-memory bank.
    auto next_bank = tess_fopdt_bank_;
    std::vector<std::vector<double>> next_signature(
        scenarios.size(), std::vector<double>(tess_unique_source_nodes_.size(), 0.0));
    const double floor = std::max(runtime_config_.tess_min_corrected, 1e-12);
    const TessEpisode* previous = nullptr;
    for (auto iterator = tess_episodes_.rbegin(); iterator != tess_episodes_.rend(); ++iterator) {
        if (iterator->model_valid) { previous = &(*iterator); break; }
    }
    const double total_interval = previous ? std::max(0.0, episode.sim_time - previous->sim_time) : 0.0;
    const double dwell = previous ? std::min(planner_config_.measurement_dwell_seconds, total_interval)
                                  : planner_config_.measurement_dwell_seconds;
    const double travel = previous ? std::max(0.0, total_interval - dwell) : 0.0;
    const double start_x = previous ? previous->x : episode.x;
    const double start_y = previous ? previous->y : episode.y;

    try {
        for (std::size_t h = 0; h < scenarios.size(); ++h) {
            for (std::size_t unique = 0; unique < tess_unique_source_nodes_.size(); ++unique) {
                const int endpoint = transport_graph.nearestVisibleNode(episode.x, episode.y);
                if (endpoint < 0) return false;
                const double endpoint_target = std::max(floor, fields[h](endpoint, static_cast<int>(unique)));
                if (!previous) {
                    // At process start the sensor is assumed equilibrated to the
                    // background floor, not magically to the unknown endpoint
                    // concentration.  The first dwell then evolves the exact
                    // dead-time state toward the physical endpoint input.
                    next_bank[h][unique] = tessv3::makeFopdtState(
                        floor, floor, runtime_config_.tess_dead_time_seconds);
                    if (dwell > 0.0) {
                        tessv3::advanceFopdtSegment(next_bank[h][unique], endpoint_target,
                                                   dwell, runtime_config_.tess_tau_seconds);
                    }
                } else {
                    const auto segments = makeTessExposureSegments(
                        fields[h], static_cast<int>(unique), start_x, start_y,
                        episode.x, episode.y, travel, dwell);
                    if (segments.empty() && total_interval > 0.0) return false;
                    tessv3::advanceFopdt(next_bank[h][unique], segments,
                                         runtime_config_.tess_tau_seconds);
                }
                const double output = next_bank[h][unique].output;
                if (!std::isfinite(output) || output < 0.0) return false;
                next_signature[h][unique] = std::log(std::max(floor, output));
            }
        }
    } catch (const std::exception& error) {
        GSL_WARN("OPGSLSCIMV1 TESS-V3 FOPDT update rejected: {}", error.what());
        return false;
    }

    tess_fopdt_bank_ = std::move(next_bank);
    episode.predicted_log_signature = std::move(next_signature);
    tess_cached_physical_scenarios_ = scenarios;
    tess_cached_fields_ = fields;
    tess_cached_wind_x_ = episode.wind_x;
    tess_cached_wind_y_ = episode.wind_y;
    tess_field_cache_valid_ = true;
    episode.model_valid = true;
    return true;
}

void OPGSLSCIMV1::recordTessMeasurementBlock(double concentration) {
    if (!runtime_config_.tess_enabled) return;
    tessv3::BlockConfig config;
    config.min_corrected = runtime_config_.tess_min_corrected;
    config.min_effective_samples = runtime_config_.tess_min_effective_samples;
    config.log_variance_floor = runtime_config_.tess_log_variance_floor;
    std::vector<tessv3::Sample> samples;
    if (const auto* state = dynamic_cast<const StopAndMeasureState*>(stopAndMeasureState.get())) {
        for (const float value : state->gasSamples()) samples.push_back({static_cast<double>(value)});
    }
    auto block = tessv3::finalizeBlock(samples, runtime_config_.tess_background_concentration,
                                       true, config);
    const double z = clipToFlightBounds(currentRobotPose.pose.pose.position.z);
    TessEpisode episode{block, currentRobotPosition.x, currentRobotPosition.y, z,
                        elapsed_time_, latest_wind_x_, latest_wind_y_};
    if (!updateTessPhysicalModel(episode) && episode.block.accepted) {
        episode.block.accepted = false;
        episode.block.reason = "MODEL_PREDICTION_FAILED";
    }
    tess_episodes_.push_back(std::move(episode));
    const auto& stored = tess_episodes_.back();
    if (stored.block.accepted) {
        tess_invalid_block_streak_ = 0;
    } else if (++tess_invalid_block_streak_ >= 2) {
        tess_pause_cycles_ = 2;
    }

    if (tess_block_stream_.is_open()) {
        tess_block_stream_ << std::fixed << std::setprecision(12) << run_uuid_ << ','
            << tess_episodes_.size() << ',' << elapsed_time_ << ',' << stored.block.raw_mean << ','
            << stored.block.background << ',' << stored.block.corrected << ',' << stored.block.log_value << ','
            << stored.block.log_variance << ',' << stored.block.weight << ',' << stored.block.raw_samples << ','
            << stored.block.effective_samples << ',' << stored.block.lag1_correlation << ','
            << (stored.block.accepted ? 1 : 0) << ',' << stored.block.reason << ','
            << currentRobotPosition.x << ',' << currentRobotPosition.y << ',' << z << ','
            << latest_wind_x_ << ',' << latest_wind_y_ << ',' << (stored.model_valid ? 1 : 0) << '\n';
        tess_block_stream_.flush();
    }
    if (tess_reject_stream_.is_open()) {
        const bool positive = std::isfinite(stored.block.corrected) &&
            stored.block.corrected >= runtime_config_.tess_min_corrected;
        const bool saturation_pass = stored.block.reason != "SATURATED";
        const bool sample_pass = stored.block.effective_samples >= runtime_config_.tess_min_effective_samples;
        tess_reject_stream_ << std::fixed << std::setprecision(12) << run_uuid_ << ',' << elapsed_time_ << ','
            << step_count_ << ',' << samples.size() << ",1,1,1," << (positive ? 1 : 0) << ','
            << (saturation_pass ? 1 : 0) << ',' << (sample_pass ? 1 : 0) << ','
            << (stored.model_valid ? 1 : 0) << ',' << (stored.block.accepted ? 1 : 0) << ','
            << stored.block.reason << ",NA," << stored.block.corrected << '\n';
        tess_reject_stream_.flush();
    }
}

OPGSLSCIMV1::TessEstimateSummary OPGSLSCIMV1::computeTessEstimate(
    const std::vector<double>& marginal) const {
    TessEstimateSummary output;
    if (marginal.size() != posterior_.validSourceCount() || marginal.empty()) return output;
    std::vector<double> node_mass(tess_unique_source_nodes_.size(), 0.0);
    for (std::size_t source = 0; source < marginal.size(); ++source) {
        node_mass[tess_source_to_unique_[source]] += marginal[source];
    }
    const auto best_node_iterator = std::max_element(node_mass.begin(), node_mass.end());
    if (best_node_iterator == node_mass.end() || !(*best_node_iterator > 0.0)) return output;
    const std::size_t best_node = static_cast<std::size_t>(std::distance(node_mass.begin(), best_node_iterator));
    double mass = 0.0, x = 0.0, y = 0.0, z = 0.0;
    for (std::size_t source = 0; source < marginal.size(); ++source) {
        if (tess_source_to_unique_[source] != best_node) continue;
        const auto point = posterior_.sourceAtValidIndex(source);
        mass += marginal[source];
        x += marginal[source] * point.x;
        y += marginal[source] * point.y;
        z += marginal[source] * point.z;
    }
    if (!(mass > 0.0)) return output;
    x /= mass; y /= mass; z /= mass;
    std::size_t representative = 0;
    double representative_distance = std::numeric_limits<double>::infinity();
    for (std::size_t source = 0; source < marginal.size(); ++source) {
        if (tess_source_to_unique_[source] != best_node) continue;
        const auto point = posterior_.sourceAtValidIndex(source);
        const double distance = std::hypot(point.x - x, point.y - y);
        if (distance < representative_distance) {
            representative_distance = distance;
            representative = source;
        }
    }
    std::vector<std::pair<double, double>> radius_mass;
    radius_mass.reserve(marginal.size());
    for (std::size_t source = 0; source < marginal.size(); ++source) {
        const auto point = posterior_.sourceAtValidIndex(source);
        radius_mass.push_back({std::hypot(point.x - x, point.y - y), marginal[source]});
    }
    std::sort(radius_mass.begin(), radius_mass.end());
    double accumulated = 0.0;
    double radius = 0.0;
    for (const auto& [candidate_radius, candidate_mass] : radius_mass) {
        accumulated += candidate_mass;
        radius = candidate_radius;
        if (accumulated >= verification_config_.credible_mass) break;
    }
    output.available = true;
    output.x = x; output.y = y; output.z = z;
    output.entropy = tessv3::entropy(node_mass);
    output.credible_radius = radius;
    output.map_probability = *best_node_iterator;
    output.map_source_index = representative;
    return output;
}

bool OPGSLSCIMV1::refreshTessProfiles() {
    if (!runtime_config_.tess_enabled) return false;
    ensureTessModelInitialized();
    if (!tess_model_initialized_) return false;
    std::vector<const TessEpisode*> accepted;
    for (const auto& episode : tess_episodes_) {
        if (episode.block.accepted && episode.model_valid) accepted.push_back(&episode);
    }
    const std::size_t minimum = runtime_config_.tess_linear_drift ? 3U : 2U;
    if (accepted.size() < minimum) return false;

    std::vector<double> observed, weights, times;
    observed.reserve(accepted.size());
    weights.reserve(accepted.size());
    times.reserve(accepted.size());

    // TESS-V4 uses one frozen, source/House/action/method-independent model
    // discrepancy scale.  It is never re-estimated from the active candidate
    // mixture because that would conflate source ambiguity with model error.
    tess_common_model_discrepancy_variance_ = std::max(
        0.0, runtime_config_.tess_model_discrepancy_variance);
    for (const auto* episode : accepted) {
        observed.push_back(episode->block.log_value);
        times.push_back(episode->sim_time);
        const double total_variance = episode->block.log_variance +
                                      tess_common_model_discrepancy_variance_;
        weights.push_back(1.0 / std::max(1e-12, total_variance));
    }

    const auto time_normalization = tessv4::normalizeTimes(times, weights);
    const auto prior = posterior_.mapProbabilities();
    const std::size_t scenario_count = accepted.front()->predicted_log_signature.size();
    std::vector<tessv4::ScenarioProfile> profiles;
    profiles.reserve(scenario_count);
    for (std::size_t h = 0; h < scenario_count; ++h) {
        std::vector<std::vector<double>> model(posterior_.validSourceCount(),
                                               std::vector<double>(accepted.size(), 0.0));
        for (std::size_t source = 0; source < posterior_.validSourceCount(); ++source) {
            const std::size_t unique = tess_source_to_unique_[source];
            for (std::size_t k = 0; k < accepted.size(); ++k) {
                if (h >= accepted[k]->predicted_log_signature.size() ||
                    unique >= accepted[k]->predicted_log_signature[h].size()) return false;
                model[source][k] = accepted[k]->predicted_log_signature[h][unique];
            }
        }
        auto profile = tessv4::profileScenario(observed, model, time_normalization.history,
                                               weights, runtime_config_.tess_linear_drift,
                                               prior, runtime_config_.tess_profile_prior_power);
        if (!profile.valid) return false;
        profiles.push_back(std::move(profile));
    }
    auto marginal = tessv4::modelAverageSourceWeights(profiles);
    if (marginal.size() != posterior_.validSourceCount()) return false;
    tess_scenario_profiles_ = std::move(profiles);
    tess_marginal_profile_weights_ = std::move(marginal);
    tess_profile_blocks_ = static_cast<int>(accepted.size());
    tess_estimate_ = computeTessEstimate(tess_marginal_profile_weights_);

    if (tess_source_stream_.is_open()) {
        std::vector<std::size_t> order(tess_marginal_profile_weights_.size());
        std::iota(order.begin(), order.end(), 0U);
        std::stable_sort(order.begin(), order.end(), [&](std::size_t left, std::size_t right) {
            return tess_marginal_profile_weights_[left] > tess_marginal_profile_weights_[right];
        });
        const std::size_t log_count = std::min<std::size_t>(20, order.size());
        for (std::size_t rank = 0; rank < log_count; ++rank) {
            const auto source = order[rank];
            const auto point = posterior_.sourceAtValidIndex(source);
            for (std::size_t h = 0; h < tess_scenario_profiles_.size(); ++h) {
                tess_source_stream_ << std::fixed << std::setprecision(12) << run_uuid_ << ','
                    << measurement_count_ << ',' << h << ',' << source << ',' << point.x << ',' << point.y << ','
                    << prior[source] << ',' << tess_scenario_profiles_[h].candidate[source].objective << ','
                    << tess_scenario_profiles_[h].source_weight[source] << ','
                    << tess_marginal_profile_weights_[source] << ',' << rank + 1 << ','
                    << (source == tess_estimate_.map_source_index ? 1 : 0) << ',' << accepted.size() << '\n';
            }
        }
        tess_source_stream_.flush();
    }
    return tess_estimate_.available;
}

bool OPGSLSCIMV1::applyPathMetricsToDecision(SCIM::PlannerDecision& decision) {
    if (!transport_initialized_ || decision.ranked.empty()) return false;
    const double speed = std::max(1e-6, planner_config_.horizontal_speed_mps);
    const double dwell = std::max(0.0, planner_config_.measurement_dwell_seconds);
    for (auto& score : decision.ranked) {
        const double old_numerator = (std::isfinite(score.utility) && std::isfinite(score.cycle_time))
            ? score.utility * score.cycle_time : 0.0;
        const auto path = transport_graph.shortestPathNodes(
            currentRobotPosition.x, currentRobotPosition.y,
            score.action.x, score.action.y);
        score.path_valid = false;
        if (path.empty()) {
            writeActionValidityTrace(score.action.x, score.action.y, score.action.z, false,
                                     "TESS_GRAPH_NO_PATH");
            continue;
        }
        double path_length = transport_graph.pathLength(path);
        const auto& first = transport_graph.nodes.at(static_cast<std::size_t>(path.front()));
        const auto& last = transport_graph.nodes.at(static_cast<std::size_t>(path.back()));
        path_length += std::hypot(first.cx - currentRobotPosition.x,
                                  first.cy - currentRobotPosition.y);
        path_length += std::hypot(score.action.x - last.cx,
                                  score.action.y - last.cy);
        const double navigation_seconds = path_length / speed;
        if (!std::isfinite(path_length) || !std::isfinite(navigation_seconds) ||
            navigation_seconds > runtime_config_.tess_max_navigation_seconds) {
            writeActionValidityTrace(score.action.x, score.action.y, score.action.z, false,
                                     "TESS_GRAPH_NAV_TIME_EXCEEDED");
            continue;
        }
        score.path_length = path_length;
        score.predicted_navigation_seconds = navigation_seconds;
        score.path_valid = true;
        writeActionValidityTrace(score.action.x, score.action.y, score.action.z, true,
                                 "TESS_GRAPH_PATH_VALID");
        score.cycle_time = navigation_seconds + dwell;
        score.utility = old_numerator / std::max(score.cycle_time, 1e-9);
    }
    decision.ranked.erase(std::remove_if(decision.ranked.begin(), decision.ranked.end(),
        [](const SCIM::ActionScore& score) { return !score.path_valid; }), decision.ranked.end());
    std::stable_sort(decision.ranked.begin(), decision.ranked.end(),
        [](const SCIM::ActionScore& lhs, const SCIM::ActionScore& rhs) {
            if (std::abs(lhs.utility - rhs.utility) > 1e-12) return lhs.utility > rhs.utility;
            if (lhs.action.visit_count != rhs.action.visit_count) return lhs.action.visit_count < rhs.action.visit_count;
            return lhs.cycle_time < rhs.cycle_time;
        });
    for (auto& score : decision.ranked) score.selected = false;
    if (decision.ranked.empty()) {
        decision.selected.reset();
        decision.reason = "NO_PATH_VALID_ACTION";
        return false;
    }
    decision.ranked.front().selected = true;
    decision.selected = decision.ranked.front();
    return true;
}

bool OPGSLSCIMV1::buildTessFuturePredictions(
    const SCIM::PlannerDecision& decision,
    const tessv4::RegionPartition& partition,
    std::vector<tessv4::Scenario>& scenarios,
    std::vector<tessv4::ActionMeta>& action_meta,
    std::vector<tessv4::Point2>& region_xy,
    std::vector<double>& history_time_basis,
    std::vector<double>& history_weight,
    double& future_variance) const {
    if (!tess_model_initialized_ || !partition.valid || partition.regions.size() < 2 ||
        decision.ranked.empty() || tess_scenario_profiles_.empty()) return false;
    std::vector<const TessEpisode*> accepted;
    for (const auto& episode : tess_episodes_) {
        if (episode.block.accepted && episode.model_valid) accepted.push_back(&episode);
    }
    if (accepted.size() < 2) return false;

    std::vector<double> observed, times, sensor_variances;
    observed.reserve(accepted.size());
    times.reserve(accepted.size());
    sensor_variances.reserve(accepted.size());
    for (const auto* episode : accepted) {
        observed.push_back(episode->block.log_value);
        const double total_variance = episode->block.log_variance +
                                      tess_common_model_discrepancy_variance_;
        history_weight.push_back(1.0 / std::max(1e-12, total_variance));
        sensor_variances.push_back(episode->block.log_variance);
        times.push_back(episode->sim_time);
    }
    const auto time_normalization = tessv4::normalizeTimes(times, history_weight);
    history_time_basis = time_normalization.history;
    std::sort(sensor_variances.begin(), sensor_variances.end());
    const double future_sensor_variance = std::max(
        runtime_config_.tess_log_variance_floor,
        sensor_variances[sensor_variances.size() / 2]);
    future_variance = future_sensor_variance + tess_common_model_discrepancy_variance_;

    region_xy.reserve(partition.regions.size());
    for (const auto& region : partition.regions) region_xy.push_back(region.centroid);

    action_meta.reserve(decision.ranked.size());
    for (std::size_t a = 0; a < decision.ranked.size(); ++a) {
        const auto& action = decision.ranked[a];
        tessv4::ActionMeta meta;
        meta.id = static_cast<int>(a);
        meta.hard_valid = action.path_valid;
        meta.path_length = action.path_length;
        meta.navigation_seconds = action.predicted_navigation_seconds;
        meta.dwell_seconds = planner_config_.measurement_dwell_seconds;
        meta.duration = action.cycle_time;
        meta.revisit = action.action.visit_count;
        meta.future_time_basis = time_normalization.transform(elapsed_time_ + action.cycle_time);
        meta.future_sensor_log_variance = future_sensor_variance;
        meta.shared_model_log_variance = tess_common_model_discrepancy_variance_;
        meta.future_log_variance = future_variance;
        action_meta.push_back(meta);
    }

    const auto physical_scenarios = makeTessPhysicsScenarios(latest_wind_x_, latest_wind_y_);
    std::vector<Eigen::MatrixXd> computed_fields;
    const bool cache_matches = tess_field_cache_valid_ &&
        std::abs(tess_cached_wind_x_ - latest_wind_x_) <= 1e-12 &&
        std::abs(tess_cached_wind_y_ - latest_wind_y_) <= 1e-12 &&
        tess_cached_fields_.size() == physical_scenarios.size();
    const std::vector<Eigen::MatrixXd>* fields = &tess_cached_fields_;
    if (!cache_matches) {
        if (!solveTessScenarioFields(physical_scenarios, computed_fields)) return false;
        fields = &computed_fields;
    }

    const std::size_t full_source_count = posterior_.validSourceCount();
    const std::size_t region_count = partition.regions.size();
    scenarios.assign(physical_scenarios.size(), tessv4::Scenario{});
    for (std::size_t h = 0; h < scenarios.size(); ++h) {
        if (h >= tess_scenario_profiles_.size() ||
            tess_scenario_profiles_[h].source_weight.size() != full_source_count) return false;
        auto& scenario = scenarios[h];
        scenario.history_by_region.assign(region_count,
            std::vector<double>(accepted.size(), 0.0));
        scenario.region_mass.assign(region_count, 0.0);
        scenario.region_profile.assign(region_count, tessv4::ProfileResult{});

        for (std::size_t region_id = 0; region_id < region_count; ++region_id) {
            const auto& region = partition.regions[region_id];
            double mass = 0.0;
            for (const auto source : region.members) {
                mass += tess_scenario_profiles_[h].source_weight[source];
            }
            scenario.region_mass[region_id] = mass;
            if (mass > 0.0) {
                for (const auto source : region.members) {
                    const double source_mass = tess_scenario_profiles_[h].source_weight[source];
                    const std::size_t unique = tess_source_to_unique_[source];
                    for (std::size_t k = 0; k < accepted.size(); ++k) {
                        scenario.history_by_region[region_id][k] += source_mass *
                            accepted[k]->predicted_log_signature[h][unique] / mass;
                    }
                }
            } else {
                // Numerically zero-mass regions do not affect the objective;
                // use an arithmetic fingerprint solely to keep dimensions valid.
                for (const auto source : region.members) {
                    const std::size_t unique = tess_source_to_unique_[source];
                    for (std::size_t k = 0; k < accepted.size(); ++k) {
                        scenario.history_by_region[region_id][k] +=
                            accepted[k]->predicted_log_signature[h][unique] /
                            static_cast<double>(region.members.size());
                    }
                }
            }
            scenario.region_profile[region_id] = tessv4::candidateProfile(
                observed, scenario.history_by_region[region_id], history_time_basis,
                history_weight, runtime_config_.tess_linear_drift);
            if (!scenario.region_profile[region_id].valid) return false;
        }
        const double region_mass_sum = std::accumulate(
            scenario.region_mass.begin(), scenario.region_mass.end(), 0.0);
        if (std::abs(region_mass_sum - 1.0) > 1e-10) return false;

        scenario.future_log_by_action.assign(decision.ranked.size(),
            std::vector<double>(region_count, 0.0));
        scenario.future_raw_by_action.assign(decision.ranked.size(),
            std::vector<double>(region_count, 0.0));
        scenario.valid_probability_by_action.assign(decision.ranked.size(), 0.0);
        scenario.support_by_action.assign(decision.ranked.size(),
            std::vector<bool>(region_count, true));

        for (std::size_t a = 0; a < decision.ranked.size(); ++a) {
            if (!action_meta[a].hard_valid) {
                std::fill(scenario.support_by_action[a].begin(),
                          scenario.support_by_action[a].end(), false);
                continue;
            }
            const auto& action = decision.ranked[a];
            const double travel = action_meta[a].navigation_seconds;
            const double dwell = action_meta[a].dwell_seconds;
            std::vector<double> unique_raw(tess_unique_source_nodes_.size(), 0.0);
            std::vector<double> unique_log(tess_unique_source_nodes_.size(), 0.0);
            std::vector<bool> unique_support(tess_unique_source_nodes_.size(), true);
            for (std::size_t unique = 0; unique < tess_unique_source_nodes_.size(); ++unique) {
                auto cloned = tess_fopdt_bank_[h][unique];
                const auto segments = makeTessExposureSegments((*fields)[h], static_cast<int>(unique),
                    currentRobotPosition.x, currentRobotPosition.y,
                    action.action.x, action.action.y, travel, dwell);
                if (segments.empty() && action_meta[a].duration > 0.0) {
                    unique_support[unique] = false;
                    continue;
                }
                tessv3::advanceFopdt(cloned, segments, runtime_config_.tess_tau_seconds);
                if (!std::isfinite(cloned.output) || cloned.output < 0.0) {
                    unique_support[unique] = false;
                    continue;
                }
                unique_raw[unique] = cloned.output;
                unique_log[unique] = std::log(std::max(
                    runtime_config_.tess_min_corrected, cloned.output));
            }

            // Exact all-source probability of obtaining a valid block.  No
            // top-k truncation and no regional mean approximation is used.
            double valid_probability = 0.0;
            for (std::size_t source = 0; source < full_source_count; ++source) {
                const std::size_t unique = tess_source_to_unique_[source];
                if (!unique_support[unique]) continue;
                const auto& source_profile = tess_scenario_profiles_[h].candidate[source];
                if (!source_profile.valid) return false;
                const double mu_log = unique_log[unique] + source_profile.eta[0] +
                    (source_profile.dim == 2
                        ? source_profile.eta[1] * action_meta[a].future_time_basis : 0.0);
                valid_probability += tess_scenario_profiles_[h].source_weight[source] *
                    tessv4::validBlockProbability(mu_log, action_meta[a].future_log_variance,
                                                  runtime_config_.tess_min_corrected);
            }
            scenario.valid_probability_by_action[a] = std::clamp(valid_probability, 0.0, 1.0);

            for (std::size_t region_id = 0; region_id < region_count; ++region_id) {
                const auto& region = partition.regions[region_id];
                const double mass = scenario.region_mass[region_id];
                double supported_mass = 0.0;
                if (mass > 0.0) {
                    for (const auto source : region.members) {
                        const double source_mass = tess_scenario_profiles_[h].source_weight[source];
                        const std::size_t unique = tess_source_to_unique_[source];
                        if (!unique_support[unique]) continue;
                        supported_mass += source_mass;
                        scenario.future_raw_by_action[a][region_id] +=
                            source_mass * unique_raw[unique] / mass;
                        scenario.future_log_by_action[a][region_id] +=
                            source_mass * unique_log[unique] / mass;
                    }
                    scenario.support_by_action[a][region_id] =
                        supported_mass >= mass * (1.0 - 1e-12);
                } else {
                    std::size_t supported_count = 0;
                    for (const auto source : region.members) {
                        const std::size_t unique = tess_source_to_unique_[source];
                        if (!unique_support[unique]) continue;
                        ++supported_count;
                        scenario.future_raw_by_action[a][region_id] +=
                            unique_raw[unique] / static_cast<double>(region.members.size());
                        scenario.future_log_by_action[a][region_id] +=
                            unique_log[unique] / static_cast<double>(region.members.size());
                    }
                    scenario.support_by_action[a][region_id] = supported_count == region.members.size();
                }
            }
        }
    }
    return true;
}

bool OPGSLSCIMV1::applyTessOrdering(SCIM::PlannerDecision& decision) {
    if (!runtime_config_.tess_enabled || !transport_initialized_ || decision.ranked.empty()) return false;
    if (!tess_estimate_.available && !refreshTessProfiles()) return false;

    std::vector<const TessEpisode*> accepted;
    for (const auto& episode : tess_episodes_) {
        if (episode.block.accepted && episode.model_valid) accepted.push_back(&episode);
    }
    if (accepted.size() < 2 || tess_marginal_profile_weights_.size() != posterior_.validSourceCount()) {
        return false;
    }

    // TESS-V4 closes the former top-k mass leak by assigning every source
    // candidate to one of a small number of spatial regions.  Region masses
    // are retained exactly instead of renormalising a truncated ~1% tail.
    std::vector<tessv4::Point2> all_xy;
    all_xy.reserve(posterior_.validSourceCount());
    for (std::size_t source = 0; source < posterior_.validSourceCount(); ++source) {
        const auto point = posterior_.sourceAtValidIndex(source);
        all_xy.push_back({point.x, point.y});
    }
    const std::size_t maximum_regions = static_cast<std::size_t>(
        std::max(2, runtime_config_.tess_max_competitors + 1));
    const auto partition = tessv4::buildMassPreservingRegions(
        tess_marginal_profile_weights_, all_xy, maximum_regions);
    if (!partition.valid || partition.regions.size() < 2 ||
        std::abs(partition.total_mass - 1.0) > 1e-10) {
        return false;
    }

    std::vector<tessv4::Scenario> scenarios;
    std::vector<tessv4::ActionMeta> action_meta;
    std::vector<tessv4::Point2> region_xy;
    std::vector<double> history_time_basis, history_weight;
    double future_variance = 0.0;
    if (!buildTessFuturePredictions(decision, partition, scenarios, action_meta,
                                    region_xy, history_time_basis, history_weight,
                                    future_variance)) {
        return false;
    }

    std::vector<tessv4::ActionScore> scores;
    scores.reserve(action_meta.size());
    for (const auto& action : action_meta) {
        scores.push_back(tessv4::evaluateAction(
            scenarios, region_xy, history_time_basis, history_weight, action,
            runtime_config_.tess_linear_drift, runtime_config_.tess_min_corrected));
    }
    if (scores.empty() || !scores.front().supported) return false;

    const int original_id = 0;
    int best_id = original_id;
    double best_rate = scores.front().robust_gain_rate;
    const double original_rate = scores.front().robust_gain_rate;
    const double original_duration = action_meta.front().duration;
    const bool warm = accepted.size() >= static_cast<std::size_t>(
        std::max(2, runtime_config_.tess_warmup_blocks));
    const bool paused = tess_pause_cycles_ > 0;
    if (tess_pause_cycles_ > 0) --tess_pause_cycles_;

    if (warm && !paused) {
        for (std::size_t a = 1; a < scores.size(); ++a) {
            const bool legal = scores[a].supported && scores[a].robust_gain_rate > 0.0 &&
                scores[a].robust_valid_probability >= runtime_config_.tess_p_valid_min &&
                action_meta[a].duration <= original_duration + runtime_config_.tess_duration_slack_seconds;
            if (legal && scores[a].robust_gain_rate > best_rate) {
                best_id = static_cast<int>(a);
                best_rate = scores[a].robust_gain_rate;
            }
        }
    }
    const double required_margin = std::max(
        runtime_config_.tess_takeover_absolute_margin,
        runtime_config_.tess_takeover_relative_margin * std::abs(original_rate));
    const bool better_than_original = best_id != original_id &&
        best_rate - original_rate > required_margin;
    const bool actual_takeover = runtime_config_.tess_takeover_enabled && better_than_original;
    if (best_rate > 0.0) ++tess_positive_gain_cycles_;
    ++tess_selected_cycles_;
    if (better_than_original) ++tess_different_cycles_;
    if (actual_takeover) ++tess_takeover_cycles_;

    // Region diagnostics expose the complete probability accounting for every
    // physical scenario.  The sum must remain one in every cycle.
    if (tess_region_stream_.is_open()) {
        for (std::size_t h = 0; h < scenarios.size(); ++h) {
            for (std::size_t region = 0; region < partition.regions.size(); ++region) {
                const auto& descriptor = partition.regions[region];
                tess_region_stream_ << std::fixed << std::setprecision(12)
                    << run_uuid_ << ',' << measurement_count_ << ',' << elapsed_time_ << ','
                    << h << ',' << region << ',' << scenarios[h].region_mass[region] << ','
                    << descriptor.centroid.x << ',' << descriptor.centroid.y << ','
                    << descriptor.members.size() << ',' << partition.total_mass << ','
                    << tess_common_model_discrepancy_variance_ << '\n';
            }
        }
        tess_region_stream_.flush();
    }

    for (std::size_t a = 0; a < scores.size(); ++a) {
        const auto& score = scores[a];
        const auto& ranked_action = decision.ranked[a];
        const auto& action = ranked_action.action;
        const bool legal = score.supported && score.robust_gain_rate > 0.0 &&
            score.robust_valid_probability >= runtime_config_.tess_p_valid_min &&
            action_meta[a].duration <= original_duration + runtime_config_.tess_duration_slack_seconds;
        if (tess_decision_stream_.is_open()) {
            tess_decision_stream_ << std::fixed << std::setprecision(12) << run_uuid_ << ','
                << measurement_count_ << ',' << elapsed_time_ << ',' << a << ','
                << action.x << ',' << action.y << ',' << action.z << ','
                << (a == 0 ? 1 : 0) << ',' << (static_cast<int>(a) == best_id ? 1 : 0) << ','
                << ((actual_takeover && static_cast<int>(a) == best_id) ? 1 : 0) << ','
                << (runtime_config_.tess_takeover_enabled ? 0 : 1) << ',' << (score.supported ? 1 : 0) << ','
                << (legal ? 1 : 0) << ',' << (warm ? 1 : 0) << ',' << (paused ? 1 : 0) << ','
                << score.robust_pair_gain << ',' << score.robust_valid_probability << ','
                << score.robust_expected_gain << ',' << score.robust_gain_rate << ','
                << original_rate << ',' << required_margin << ',' << action_meta[a].duration << ','
                << action_meta[a].path_length << ',' << action_meta[a].navigation_seconds << ','
                << action_meta[a].future_sensor_log_variance << ','
                << action_meta[a].shared_model_log_variance << ','
                << action_meta[a].future_log_variance << ','
                << partition.regions.size() << ',' << partition.total_mass << ','
                << tess_last_planner_runtime_ms_ << ',' << tess_common_model_discrepancy_variance_ << ','
                << tess_takeover_cycles_ << ',' << tess_selected_cycles_ << ','
                << tess_different_cycles_ << ',' << tess_positive_gain_cycles_ << '\n';
        }
    }
    if (tess_pair_detail_stream_.is_open()) {
        std::vector<int> action_ids{original_id};
        if (best_id != original_id) action_ids.push_back(best_id);
        for (const int action_id : action_ids) {
            if (action_id < 0 || static_cast<std::size_t>(action_id) >= scores.size()) continue;
            for (std::size_t h = 0; h < scores[action_id].scenario.size(); ++h) {
                for (const auto& pair : scores[action_id].scenario[h].pairs) {
                    tess_pair_detail_stream_ << std::fixed << std::setprecision(12) << run_uuid_ << ','
                        << measurement_count_ << ',' << action_id << ',' << h << ','
                        << pair.left << ',' << pair.right << ','
                        << pair.source_pair_weight << ',' << pair.spatial_distance_squared << ','
                        << pair.current_separation << ',' << pair.separation_increment << ','
                        << pair.error_reduction << ',' << pair.weighted_gain << ','
                        << pair.innovation << ',' << scores[action_id].scenario[h].region_mass_sum << '\n';
                }
            }
        }
        tess_pair_detail_stream_.flush();
    }
    if (tess_decision_stream_.is_open()) tess_decision_stream_.flush();

    if (!actual_takeover) return true;
    std::iter_swap(decision.ranked.begin(), decision.ranked.begin() + best_id);
    for (auto& score : decision.ranked) score.selected = false;
    decision.ranked.front().selected = true;
    decision.selected = decision.ranked.front();
    decision.reason = "tess_v4_mass_preserving_profile_gain_rate";
    return true;
}


bool OPGSLSCIMV1::applySnoedBundleOrdering(SCIM::PlannerDecision& decision) {
    if (!transport_initialized_ || decision.ranked.size() < 3) return false;
    const auto probabilities = posterior_.mapProbabilities();
    std::vector<std::size_t> order(probabilities.size());
    std::iota(order.begin(), order.end(), 0U);
    std::stable_sort(order.begin(), order.end(), [&probabilities](std::size_t lhs, std::size_t rhs) {
        return probabilities[lhs] > probabilities[rhs];
    });
    if (order.size() > static_cast<std::size_t>(runtime_config_.candidate_cap))
        order.resize(static_cast<std::size_t>(runtime_config_.candidate_cap));
    std::vector<std::size_t> candidates;
    double selected_mass = 0.0;
    for (const auto index : order) {
        candidates.push_back(index); selected_mass += probabilities[index];
        if (selected_mass >= 0.90 && candidates.size() >= 2) break;
    }
    if (candidates.size() < 2) return false;
    std::vector<int> source_nodes; source_nodes.reserve(candidates.size());
    Eigen::VectorXd weights(static_cast<int>(candidates.size()));
    for (std::size_t c = 0; c < candidates.size(); ++c) {
        const auto source = posterior_.sourceAtValidIndex(candidates[c]);
        source_nodes.push_back(transport_graph.nearestVisibleNode(source.x, source.y));
        weights(static_cast<int>(c)) = probabilities[candidates[c]];
    }
    weights /= std::max(1e-12, weights.sum());
    std::vector<std::array<double, 2>> action_points;
    action_points.reserve(decision.ranked.size());
    for (const auto& score : decision.ranked) action_points.push_back({score.action.x, score.action.y});
    const auto diag = transport_graph.buildActionPredictionCube(
        action_points, source_nodes, transport_params, latest_wind_x_, latest_wind_y_, last_action_cube_);
    if (!diag.success || last_action_cube_.q.size() != decision.ranked.size()) return false;
    if (runtime_config_.raiom_mode == "M2-KL" || runtime_config_.raiom_mode == "M2-NF") {
        for (std::size_t a = 0; a < decision.ranked.size(); ++a) {
            const double numerator = runtime_config_.raiom_mode == "M2-KL"
                ? raiom::SparseNuisanceOrthogonalPlanner::coupledKL(last_action_cube_.q[a], weights)
                : raiom::SparseNuisanceOrthogonalPlanner::nominalFisher(
                    last_action_cube_.q[a], last_action_cube_.dq_ds[a], weights);
            decision.ranked[a].discrimination = numerator;
            decision.ranked[a].utility = numerator / std::max(1e-6, decision.ranked[a].cycle_time);
        }
        std::stable_sort(decision.ranked.begin(), decision.ranked.end(), [](const SCIM::ActionScore& lhs,
                                                                            const SCIM::ActionScore& rhs) {
            if (std::abs(lhs.utility - rhs.utility) > 1e-12) return lhs.utility > rhs.utility;
            return lhs.cycle_time < rhs.cycle_time;
        });
        for (auto& score : decision.ranked) score.selected = false;
        decision.selected = decision.ranked.front();
        decision.selected->selected = true;
        decision.ranked.front().selected = true;
        decision.reason = runtime_config_.raiom_mode == "M2-KL"
            ? "raiom_coupled_kl" : "raiom_nominal_fisher";
        return true;
    }
    std::vector<double> utility(decision.ranked.size(), -std::numeric_limits<double>::infinity());
    for (std::size_t i = 0; i + 2 < decision.ranked.size(); ++i) {
        const std::array<int, 3> bundle{{static_cast<int>(i), static_cast<int>(i + 1), static_cast<int>(i + 2)}};
        const std::array<double, 3> cycles{{decision.ranked[i].cycle_time,
            decision.ranked[i + 1].cycle_time, decision.ranked[i + 2].cycle_time}};
        const auto score = raiom::SparseNuisanceOrthogonalPlanner::scoreOrderedBundle(
            last_action_cube_, bundle, weights, cycles, runtime_config_.snoed_tau_seconds,
            runtime_config_.snoed_dead_time_seconds);
        utility[i] = score.utility;
        decision.ranked[i].utility = score.utility;
        decision.ranked[i].discrimination = score.gamma;
    }
    std::stable_sort(decision.ranked.begin(), decision.ranked.end(), [](const SCIM::ActionScore& lhs,
                                                                        const SCIM::ActionScore& rhs) {
        if (std::abs(lhs.utility - rhs.utility) > 1e-12) return lhs.utility > rhs.utility;
        return lhs.cycle_time < rhs.cycle_time;
    });
    for (auto& score : decision.ranked) score.selected = false;
    decision.selected = decision.ranked.front();
    decision.selected->selected = true;
    decision.ranked.front().selected = true;
    decision.reason = "raiom_snoed_ordered_fopdt_bundle";
    return true;
}

SCIM::PlannerDecision OPGSLSCIMV1::planFeasibleActions(
    const std::vector<OPGSLV3::FeasibleAction>& actions) {
    const auto context = makeObservationContext(currentRobotPosition.x, currentRobotPosition.y,
                                                clipToFlightBounds(currentRobotPose.pose.pose.position.z), 0.0);
    const auto planner_started = std::chrono::steady_clock::now();
    acquireDeterministicPlannerPause();
    ScopeExit pause_guard([this]() { releaseDeterministicPlannerPause(); });
    auto decision = spatial_planner_.choose(actions, currentRobotPosition.x, currentRobotPosition.y,
                                   context.sensor_z, context, posterior_, observation_model_,
                                   planner_config_.horizontal_speed_mps,
                                   planner_config_.vertical_speed_mps,
                                   planner_config_.measurement_dwell_seconds);
    // The base and TESS arms share the same graph-reachable action set and the
    // same path-derived time budget.  This removes endpoint-only feasibility
    // and Euclidean-cycle-time confounding from the paired experiment.
    if (transport_initialized_ && !applyPathMetricsToDecision(decision)) {
        tess_last_planner_runtime_ms_ = std::chrono::duration<double, std::milli>(
            std::chrono::steady_clock::now() - planner_started).count();
        return decision;
    }
    if (runtime_config_.tess_enabled) {
        applyTessOrdering(decision);
    } else if ((runtime_config_.snoed_enabled && runtime_config_.raiom_mode == "M2-SNOED") || runtime_config_.raiom_mode == "M2-KL" ||
        runtime_config_.raiom_mode == "M2-NF") applySnoedBundleOrdering(decision);
    tess_last_planner_runtime_ms_ = std::chrono::duration<double, std::milli>(
        std::chrono::steady_clock::now() - planner_started).count();
    return decision;
}

void OPGSLSCIMV1::acquireDeterministicPlannerPause() {
    if (planner_pause_depth_ > 0) {
        ++planner_pause_depth_;
        return;
    }
    if (!simulation_pause_client_ ||
        !simulation_pause_client_->wait_for_service(std::chrono::seconds(2))) {
        throw std::runtime_error("deterministic planner pause service unavailable");
    }
    auto request = std::make_shared<std_srvs::srv::SetBool::Request>();
    request->data = true;
    auto future = simulation_pause_client_->async_send_request(request);
    const auto result = rclcpp::spin_until_future_complete(
        node, future, std::chrono::seconds(2));
    if (result != rclcpp::FutureReturnCode::SUCCESS) {
        throw std::runtime_error("deterministic planner pause request timed out");
    }
    const auto response = future.get();
    if (!response || !response->success) {
        throw std::runtime_error("deterministic planner pause request rejected");
    }
    planner_pause_depth_ = 1;
    if (planner_busy_pub_) {
        std_msgs::msg::Bool message;
        message.data = true;
        planner_busy_pub_->publish(message);
    }
}

void OPGSLSCIMV1::releaseDeterministicPlannerPause() noexcept {
    if (planner_pause_depth_ <= 0) return;
    --planner_pause_depth_;
    if (planner_pause_depth_ > 0) return;
    if (planner_busy_pub_) {
        std_msgs::msg::Bool message;
        message.data = false;
        planner_busy_pub_->publish(message);
    }
    try {
        if (!simulation_pause_client_ ||
            !simulation_pause_client_->wait_for_service(std::chrono::seconds(2))) {
            GSL_ERROR("deterministic planner resume service unavailable");
            return;
        }
        auto request = std::make_shared<std_srvs::srv::SetBool::Request>();
        request->data = false;
        auto future = simulation_pause_client_->async_send_request(request);
        const auto result = rclcpp::spin_until_future_complete(
            node, future, std::chrono::seconds(2));
        if (result != rclcpp::FutureReturnCode::SUCCESS) {
            GSL_ERROR("deterministic planner resume request timed out");
            return;
        }
        const auto response = future.get();
        if (!response || !response->success) {
            GSL_ERROR("deterministic planner resume request rejected");
        }
    } catch (const std::exception& error) {
        GSL_ERROR("deterministic planner resume exception: {}", error.what());
    }
}

int OPGSLSCIMV1::visitCount(double x, double y, double z) const {
    const auto it = visit_counts_.find(visitKey(x, y, z));
    return it == visit_counts_.end() ? 0 : it->second;
}

void OPGSLSCIMV1::markVisited(double x, double y, double z) {
    ++visit_counts_[visitKey(x, y, z)];
}

std::int64_t OPGSLSCIMV1::visitKey(double x, double y, double z) const {
    return coordinateKey(x, y, z, 0.25);
}

bool OPGSLSCIMV1::isPointInsideSensorSafeBounds(double x, double y) const {
    // Occupancy maps and GADEN's 3-D sensor grid describe the same footprint,
    // but their serialized floating-point extents can differ by a few ULPs.
    // A candidate on the nominal upper edge can therefore pass the map's
    // half-open check yet map to index == dimension in /frame_query.  Keep a
    // small sub-cell margin so every dispatched goal remains measurable.
    const double resolution = std::max(0.05, static_cast<double>(map.info.resolution));
    const double margin = std::max(1e-3, 0.01 * resolution);
    const double min_x = map.info.origin.position.x + margin;
    const double min_y = map.info.origin.position.y + margin;
    const double max_x = map.info.origin.position.x +
        static_cast<double>(map.info.width) * map.info.resolution - margin;
    const double max_y = map.info.origin.position.y +
        static_cast<double>(map.info.height) * map.info.resolution - margin;
    return x >= min_x && x < max_x && y >= min_y && y < max_y;
}

double OPGSLSCIMV1::clipToFlightBounds(double z) const {
    return std::clamp(z, runtime_config_.min_flight_height, runtime_config_.max_flight_height);
}

void OPGSLSCIMV1::saveResultsToFile(GSLResult result) {
    // Algorithm::HasEnded() invokes this virtual method before OnUpdate() on
    // the final scheduler turn.  Canonicalize that path to the same explicit
    // time-budget completion rather than emitting an unlabelled result.
    elapsed_time_ = (node->now() - startTime).seconds();
    if (end_reason_ == "RUNNING" && elapsed_time_ >= resultLogging.maxSearchTime) {
        end_reason_ = "TIME_BUDGET_REACHED";
    }
    const bool legal_end = end_reason_ == "TIME_BUDGET_REACHED" ||
        end_reason_ == "SOURCE_DECLARED";
    if (resultLogging.resultsFile.empty() || !posterior_initialized_ || !legal_end) return;
    ensureParentDirectory(resultLogging.resultsFile);
    const auto map_summary = posterior_.mapSummary(verification_config_.credible_mass);
    const auto conf_summary = posterior_.confidenceSummary(verification_config_.credible_mass);
    const bool use_tess_estimate = runtime_config_.tess_enabled && runtime_config_.tess_profile_estimate_enabled &&
        tess_estimate_.available && tess_profile_blocks_ >= runtime_config_.tess_warmup_blocks;
    const double result_x = use_tess_estimate ? tess_estimate_.x : map_summary.map.x;
    const double result_y = use_tess_estimate ? tess_estimate_.y : map_summary.map.y;
    const double result_z = use_tess_estimate ? tess_estimate_.z : map_summary.map.z;
    const double result_entropy = use_tess_estimate ? tess_estimate_.entropy : map_summary.entropy;
    const double result_radius = use_tess_estimate ? tess_estimate_.credible_radius : conf_summary.credible_radius;
    const bool header = !std::filesystem::exists(resultLogging.resultsFile) ||
        std::filesystem::file_size(resultLogging.resultsFile) == 0;
    std::ofstream out(resultLogging.resultsFile, std::ios::out | std::ios::app);
    if (!out.is_open()) return;
    if (header) out << "run_uuid,result,elapsed_time,steps,measurements,hits,misses,map_x,map_y,map_z,"
        "map_entropy,confidence_entropy,credible_radius,confidence_coverage_placeholder,"
        "unique_cells,effective_hits,scientific_trace_valid,reason,valid,end_reason,success_declared,posterior_concentrated,verification_required,verification_started,verification_completed,verification_bundle_gamma,verification_profile_margin,verification_measurement_valid,declaration_block_reason,abstention_reason\n";
    out << std::fixed << std::setprecision(17) << run_uuid_ << ',' << static_cast<int>(result) << ','
        << elapsed_time_ << ',' << step_count_ << ',' << measurement_count_ << ',' << hit_count_ << ','
        << miss_count_ << ',' << result_x << ',' << result_y << ',' << result_z << ','
        << result_entropy << ',' << (use_tess_estimate ? tess_estimate_.entropy : conf_summary.entropy) << ',' << result_radius << ','
        << 0.0 << ',' << spatial_planner_.uniqueCells() << ',' << spatial_planner_.effectiveHits() << ','
        << (scientific_trace_valid_ ? 1 : 0) << ",verification_required,true," << end_reason_
        << ",0,0,1,0,0,0,0,0,INDEPENDENT_VERIFICATION_NOT_COMPLETED,"
        << (hit_count_ == 0 ? "UNOBSERVABLE_WITHIN_BUDGET" : "VERIFICATION_NOT_COMPLETED") << '\n';
    writeDeclarationTrace(map_summary, conf_summary,
        hit_count_ == 0 ? "UNOBSERVABLE_WITHIN_BUDGET" : "VERIFICATION_NOT_COMPLETED");
}

void OPGSLSCIMV1::OnUpdate() {
    if (!source_declared_ && posterior_initialized_ && checkSourceFound() != GSLResult::Running) {
        currentResult = GSLResult::Failure;
        source_declared_ = true;
        const auto map_summary = posterior_.mapSummary(verification_config_.credible_mass);
        const auto confidence_summary = posterior_.confidenceSummary(verification_config_.credible_mass);
        writeStopTrace(map_summary, confidence_summary, end_reason_, currentResult);
        saveResultsToFile(currentResult);
        return;
    }
    Algorithm::OnUpdate();
}

void OPGSLSCIMV1::OnCompleteNavigation(GSLResult result, State* previousState) {
    (void)previousState;
    if (result == GSLResult::Success) {
        const double z = clipToFlightBounds(std::isfinite(currentRobotPose.pose.pose.position.z)
            ? currentRobotPose.pose.pose.position.z : runtime_config_.nominal_flight_height);
        if (isPointInsideMapBounds(Vector2(currentRobotPosition.x, currentRobotPosition.y)) &&
            isPointFree(Vector2(currentRobotPosition.x, currentRobotPosition.y))) {
            verified_frontiers_.push_back({currentRobotPosition.x, currentRobotPosition.y, z,
                                           OPGSLV3::ActionType::PlanarTraverse,
                                           visitCount(currentRobotPosition.x, currentRobotPosition.y, z)});
        }
        stateMachine.forceResetState(stopAndMeasureState.get());
        return;
    }
    // A failed/cancelled navigation is not an observation.  Replan without
    // injecting gas evidence or terminating the protocol early.
    if (auto* moving = dynamic_cast<MovingStateOPGSLSCIMV1*>(movingState.get())) {
        moving->requestReplan();
    }
}

std::string OPGSLSCIMV1::stableTraceHash(const std::string& value) {
    std::uint64_t hash = 1469598103934665603ULL;
    for (const unsigned char byte : value) { hash ^= byte; hash *= 1099511628211ULL; }
    std::ostringstream stream; stream << std::hex << std::setw(16) << std::setfill('0') << hash;
    return stream.str();
}

void OPGSLSCIMV1::initializeTraceFiles() {
    const auto open = [](const std::string& path, std::ofstream& stream, const std::string& header) {
        if (path.empty()) return;
        ensureParentDirectory(path); stream.open(path, std::ios::out | std::ios::trunc);
        if (stream.is_open()) stream << header << '\n';
    };
    open(source_estimate_trace_file_, source_estimate_stream_,
         "run_uuid,cycle,sim_time,method,estimate_available,estimate_semantics,map_x,map_y,map_z,map_entropy,confidence_entropy,credible_mass,credible_radius,map_probability,confidence_probability,verified,scientific_trace_valid,reason");
    open(evidence_trace_file_, evidence_stream_,
         "run_uuid,cycle,sim_time,concentration,detected,wind_speed,predictive_q,omega,map_entropy,confidence_entropy,source_brier,source_nll");
    open(planner_trace_file_, planner_stream_,
         "run_uuid,step,sim_time,rank,selected,x,y,z,target_cell,mode,qbar,D,J_cell,A_cell,omega_cell,DeltaA,DeltaI,cycle_time,utility,reason");
    open(stop_trace_file_, stop_stream_, "run_uuid,cycle,sim_time,decision,result,map_x,map_y,map_z,map_entropy,confidence_entropy,credible_radius,reason");
    open(candidate_trace_file_, candidate_trace_stream_,
         "run_uuid,cycle_id,sim_time,pose_x,pose_y,pose_z,wind_x,wind_y,wind_z,wind_speed,event,candidate_id,candidate_x,candidate_y,candidate_z,preupdate_posterior,predictive_q_candidate,loglik_increment_candidate,marginal_predictive_q,candidate_rank_preupdate,is_top_k,source_grid_hash,observation_model_hash");
    open(scim_memory_trace_file_, scim_memory_stream_,
         "run_uuid,cycle,sim_time,unique_cells,effective_hits,cell_id,visit_episodes,contrast_iact,omega,J_cell,A_cell,correlation_estimable");
    open(scim_contrast_trace_file_, scim_contrast_stream_,
         "run_uuid,cycle,sim_time,cell_id,contrast_iact,omega,contrast_value,J_cell,A_cell,correlation_estimable");
    open(scim_action_trace_file_, scim_action_stream_,
         "run_uuid,step,sim_time,x,y,z,target_cell,mode,qbar,D,J_cell,A_cell,omega_cell,DeltaA,DeltaI,cycle_time,utility,selected,realized_MAP_change,realized_rank_change,realized_entropy_change");
    open(action_validity_trace_file_, action_validity_stream_,
         "run_uuid,action_id,sim_time,x,y,z,accepted,rejection_reason,action_reliability,height,wall_clearance,settle_duration,sensor_intake_position");
    open(declaration_trace_file_, declaration_stream_,
         "run_uuid,sim_time,success_declared,declaration_cycle,declaration_position_x,declaration_position_y,posterior_concentrated,verification_required,verification_started,verification_completed,verification_bundle_gamma,verification_profile_margin,verification_measurement_valid,declaration_block_reason,abstention_reason");
    open(tess_block_trace_file_, tess_block_stream_,
         "run_uuid,cycle,sim_time,mean_concentration,background,corrected,log_value,log_variance,weight,raw_samples,effective_samples,lag1_correlation,accepted,reason,pose_x,pose_y,pose_z,wind_x,wind_y,model_valid");
    open(tess_source_trace_file_, tess_source_stream_,
         "run_uuid,cycle,scenario_id,candidate_id,candidate_x,candidate_y,legacy_posterior,profile_objective,scenario_profile_weight,marginal_profile_weight,profile_rank,is_profile_map,accepted_blocks");
    open(tess_decision_trace_file_, tess_decision_stream_,
         "run_uuid,cycle,sim_time,action_id,x,y,z,original_selected,tess_selected,actual_takeover,shadow_only,supported,legal,warmup_pass,paused,robust_pair_gain,robust_p_valid,robust_expected_gain,robust_gain_rate,original_gain_rate,required_margin,cycle_time,path_length,navigation_seconds,future_sensor_log_variance,shared_model_log_variance,future_total_log_variance,region_count,region_mass_sum,planner_runtime_ms,model_discrepancy_variance,takeover_cycles,tess_evaluated_cycles,different_from_original_cycles,positive_gain_cycles");
    open(tess_pair_detail_trace_file_, tess_pair_detail_stream_,
         "run_uuid,cycle,action_id,scenario_id,left_region,right_region,pair_weight,distance_squared,current_separation,separation_increment,error_reduction,weighted_gain,innovation,region_mass_sum");
    open(tess_region_trace_file_, tess_region_stream_,
         "run_uuid,cycle,sim_time,scenario_id,region_id,scenario_mass,centroid_x,centroid_y,member_count,marginal_mass_sum,shared_model_log_variance");
    open(tess_reject_trace_file_, tess_reject_stream_,
         "run_uuid,timestamp,action_id,raw_sample_count,settle_pass,pose_stability_pass,background_pass,positive_concentration_pass,saturation_pass,effective_sample_pass,model_prediction_pass,accepted,reject_reason,predicted_p_valid,actual_c_plus");
}

void OPGSLSCIMV1::writeParameterSnapshot() const {
    if (parameter_snapshot_file_.empty()) return;
    ensureParentDirectory(parameter_snapshot_file_);
    std::ofstream out(parameter_snapshot_file_, std::ios::out | std::ios::trunc);
    if (!out.is_open()) return;
    out << "run_uuid=" << run_uuid_ << '\n'
        << "algorithm=OPGSL_SCIM_V1\n"
        << "m1_intercept=" << runtime_config_.m1_intercept << '\n'
        << "m1_distance_decay=" << runtime_config_.m1_distance_decay << '\n'
        << "cell_size=" << runtime_config_.cell_size << '\n'
        << "cell_size_fallback=" << (runtime_config_.cell_size_fallback ? 1 : 0) << '\n'
        << "min_history=" << runtime_config_.min_history << '\n'
        << "candidate_cap=" << runtime_config_.candidate_cap << '\n'
        << "raiom_mode=" << runtime_config_.raiom_mode << '\n'
        << "raiom_transport_enabled=" << (use_transport_model_ ? 1 : 0) << '\n'
        << "grtom_enabled=" << (runtime_config_.grtom_enabled ? 1 : 0) << '\n'
        << "snoed_enabled=" << (runtime_config_.snoed_enabled ? 1 : 0) << '\n'
        << "qams_enabled=" << (runtime_config_.qams_enabled ? 1 : 0) << '\n'
        << "raiom_snoed_tau_seconds=" << runtime_config_.snoed_tau_seconds << '\n'
        << "raiom_snoed_dead_time_seconds=" << runtime_config_.snoed_dead_time_seconds << '\n'
        << "tess_enabled=" << (runtime_config_.tess_enabled ? 1 : 0) << '\n'
        << "tess_shadow_only=" << (runtime_config_.tess_shadow_only ? 1 : 0) << '\n'
        << "tess_takeover_enabled=" << (runtime_config_.tess_takeover_enabled ? 1 : 0) << '\n'
        << "tess_profile_estimate_enabled=" << (runtime_config_.tess_profile_estimate_enabled ? 1 : 0) << '\n'
        << "tess_model_discrepancy_variance=" << runtime_config_.tess_model_discrepancy_variance << '\n'
        << "tess_model_discrepancy_provenance=" << runtime_config_.tess_model_discrepancy_provenance << '\n'
        << "tess_max_navigation_seconds=" << runtime_config_.tess_max_navigation_seconds << '\n'
        << "tess_active_stop=" << (runtime_config_.tess_active_stop ? 1 : 0) << '\n'
        << "tess_use_qam=" << (runtime_config_.tess_use_qam ? 1 : 0) << '\n'
        << "tess_version=V4_MASS_PRESERVING_PATH_CONSTRAINED\n"
        << "tess_nuisance_basis=" << (runtime_config_.tess_linear_drift ? "constant_linear_time" : "constant") << '\n'
        << "tess_max_competitors=" << runtime_config_.tess_max_competitors << '\n'
        << "tess_log_variance_floor=" << runtime_config_.tess_log_variance_floor << '\n'
        << "tess_min_corrected_concentration=" << runtime_config_.tess_min_corrected << '\n'
        << "tess_min_effective_samples=" << runtime_config_.tess_min_effective_samples << '\n'
        << "tess_tau_seconds=" << runtime_config_.tess_tau_seconds << '\n'
        << "tess_dead_time_seconds=" << runtime_config_.tess_dead_time_seconds << '\n'
        << "tess_p_valid_min=" << runtime_config_.tess_p_valid_min << '\n'
        << "tess_warmup_blocks=" << runtime_config_.tess_warmup_blocks << '\n'
        << "tess_candidate_nms_radius_m=" << runtime_config_.tess_candidate_nms_radius_m << '\n'
        << "tess_takeover_absolute_margin=" << runtime_config_.tess_takeover_absolute_margin << '\n'
        << "tess_takeover_relative_margin=" << runtime_config_.tess_takeover_relative_margin << '\n'
        << "tess_duration_slack_seconds=" << runtime_config_.tess_duration_slack_seconds << '\n'
        << "tess_profile_prior_power=" << runtime_config_.tess_profile_prior_power << '\n'
        << "tess_linear_drift=" << (runtime_config_.tess_linear_drift ? 1 : 0) << '\n'
        << "tess_background_concentration=" << runtime_config_.tess_background_concentration << '\n'
        << "tess_scenario_log_wind_step=" << runtime_config_.tess_scenario_log_wind_step << '\n'
        << "tess_scenario_log_diffusion_step=" << runtime_config_.tess_scenario_log_diffusion_step << '\n'
        << "transport_graph_spacing_cells=" << runtime_config_.transport_graph_spacing_cells << '\n'
        << "enable_ncl=" << (runtime_config_.enable_ncl ? 1 : 0) << '\n'
        << "navigation_timeout_seconds=" << runtime_config_.navigation_timeout_seconds << '\n'
        << "vertical_enabled=0\nverifier_enabled=0\ntruth_free=1\n";
}

void OPGSLSCIMV1::writeEvidenceTrace(const OPGSLV3::PosteriorSummary& map_summary,
                                     const OPGSLV3::PosteriorSummary& confidence_summary) {
    if (!evidence_stream_.is_open()) return;
    const double omega = spatial_planner_.omegaAt(currentRobotPosition.x, currentRobotPosition.y);
    evidence_stream_ << std::fixed << std::setprecision(17) << run_uuid_ << ',' << measurement_count_ << ','
        << elapsed_time_ << ',' << latest_concentration_ << ',' << (latest_concentration_ > thresholdGas ? 1 : 0) << ','
        << latest_wind_speed_ << ',' << last_update_diagnostics_.predictive_hit_probability << ',' << omega << ','
        << map_summary.entropy << ',' << confidence_summary.entropy << ',' << last_update_diagnostics_.source_brier << ','
        << last_update_diagnostics_.source_nll << '\n';
}

void OPGSLSCIMV1::writeCandidateTrace(const OPGSLV3::ObservationContext& observation,
                                      bool detected, const std::vector<double>& preupdate_map,
                                      double marginal_predictive_q) {
    if (!candidate_trace_stream_.is_open()) return;
    std::vector<std::size_t> order(preupdate_map.size()); std::iota(order.begin(), order.end(), 0U);
    std::stable_sort(order.begin(), order.end(), [&preupdate_map](auto lhs, auto rhs) {
        return preupdate_map[lhs] > preupdate_map[rhs];
    });
    std::vector<std::size_t> rank(preupdate_map.size(), 0U);
    for (std::size_t i = 0; i < order.size(); ++i) rank[order[i]] = i + 1U;
    candidate_trace_stream_ << std::fixed << std::setprecision(17);
    for (std::size_t i = 0; i < posterior_.validSourceCount(); ++i) {
        // This is an observational diagnostic, not posterior state.  The
        // configured top-k contract prevents a high-rate simulator from
        // exhausting disk and invalidating an otherwise legal run.
        if (rank[i] > static_cast<std::size_t>(candidate_trace_top_k_)) continue;
        const auto source = posterior_.sourceAtValidIndex(i);
        const double q = OPGSLV3::ObservationModelEnsemble::hitProbability(observation_model_, source, observation);
        const double ell = detected ? std::log(q) : std::log1p(-q);
        candidate_trace_stream_ << run_uuid_ << ',' << measurement_count_ + 1 << ',' << elapsed_time_ << ','
            << observation.sensor_x << ',' << observation.sensor_y << ',' << observation.sensor_z << ','
            << observation.wind_x << ',' << observation.wind_y << ',' << observation.wind_z << ','
            << observation.wind_speed << ',' << (detected ? 1 : 0) << ',' << i << ',' << source.x << ','
            << source.y << ',' << source.z << ',' << preupdate_map[i] << ',' << q << ',' << ell << ','
            << marginal_predictive_q << ',' << rank[i] << ',' << (rank[i] <= static_cast<std::size_t>(candidate_trace_top_k_) ? 1 : 0) << ','
            << source_grid_hash_ << ",SCIM_M1\n";
    }
}

void OPGSLSCIMV1::writeSourceEstimateTrace(const OPGSLV3::PosteriorSummary& map_summary,
                                           const OPGSLV3::PosteriorSummary& confidence_summary) {
    if (!source_estimate_stream_.is_open()) return;
    const bool use_tess_estimate = runtime_config_.tess_enabled && runtime_config_.tess_profile_estimate_enabled &&
        tess_estimate_.available && tess_profile_blocks_ >= runtime_config_.tess_warmup_blocks;
    const double x = use_tess_estimate ? tess_estimate_.x : map_summary.map.x;
    const double y = use_tess_estimate ? tess_estimate_.y : map_summary.map.y;
    const double z = use_tess_estimate ? tess_estimate_.z : map_summary.map.z;
    const double map_entropy = use_tess_estimate ? tess_estimate_.entropy : map_summary.entropy;
    const double confidence_entropy = use_tess_estimate ? tess_estimate_.entropy : confidence_summary.entropy;
    const double credible_radius = use_tess_estimate ? tess_estimate_.credible_radius : confidence_summary.credible_radius;
    const double map_probability = use_tess_estimate ? tess_estimate_.map_probability : map_summary.map_probability;
    const char* method = use_tess_estimate ? "TESS_V3" : "OPGSL_SCIM_V1";
    const char* semantics = use_tess_estimate ? "PROFILE_LIKELIHOOD_MODEL_AVERAGED"
                                               : "DUAL_MAP_AND_CONFIDENCE_POSTERIOR";
    source_estimate_stream_ << std::fixed << std::setprecision(9) << run_uuid_ << ',' << measurement_count_ << ','
        << elapsed_time_ << ',' << method << ",1," << semantics << ','
        << x << ',' << y << ',' << z << ',' << map_entropy << ','
        << confidence_entropy << ',' << verification_config_.credible_mass << ',' << credible_radius << ','
        << map_probability << ',' << map_probability << ",0,1,"
        << (use_tess_estimate ? "tess_profile_estimate" : "verifier_disabled") << '\n';
}

void OPGSLSCIMV1::writePlannerTrace(const SCIM::ActionScore& score, bool selected,
                                    int rank, const SCIM::PlannerDecision& decision) {
    if (!planner_stream_.is_open()) return;
    planner_stream_ << std::fixed << std::setprecision(17) << run_uuid_ << ',' << step_count_ << ',' << elapsed_time_ << ','
        << rank << ',' << (selected ? 1 : 0) << ',' << score.action.x << ',' << score.action.y << ',' << score.action.z << ','
        << score.target_cell << ',' << decision.mode << ',' << score.qbar << ',' << score.discrimination << ',' << score.j_cell << ','
        << score.a_cell << ',' << score.omega_cell << ',' << score.delta_a << ',' << score.delta_i << ',' << score.cycle_time << ','
        << score.utility << ',' << decision.reason << '\n';
}

void OPGSLSCIMV1::writeStopTrace(const OPGSLV3::PosteriorSummary& map_summary,
                                 const OPGSLV3::PosteriorSummary& confidence_summary,
                                 const std::string& decision, GSLResult result) {
    if (!stop_stream_.is_open() || stop_trace_written_) return;
    const bool use_tess_estimate = runtime_config_.tess_enabled && runtime_config_.tess_profile_estimate_enabled &&
        tess_estimate_.available && tess_profile_blocks_ >= runtime_config_.tess_warmup_blocks;
    const double x = use_tess_estimate ? tess_estimate_.x : map_summary.map.x;
    const double y = use_tess_estimate ? tess_estimate_.y : map_summary.map.y;
    const double z = use_tess_estimate ? tess_estimate_.z : map_summary.map.z;
    const double map_entropy = use_tess_estimate ? tess_estimate_.entropy : map_summary.entropy;
    const double confidence_entropy = use_tess_estimate ? tess_estimate_.entropy : confidence_summary.entropy;
    const double radius = use_tess_estimate ? tess_estimate_.credible_radius : confidence_summary.credible_radius;
    stop_stream_ << std::fixed << std::setprecision(17) << run_uuid_ << ',' << measurement_count_ << ',' << elapsed_time_ << ','
        << decision << ',' << static_cast<int>(result) << ',' << x << ',' << y << ',' << z << ','
        << map_entropy << ',' << confidence_entropy << ',' << radius << ','
        << (use_tess_estimate ? "tess_profile_estimate" : "verifier_disabled") << '\n';
    stop_trace_written_ = true;
}

void OPGSLSCIMV1::writeSCIMMemoryTrace() {
    if (!scim_memory_stream_.is_open()) return;
    for (const auto& cell : spatial_planner_.snapshots()) {
        scim_memory_stream_ << std::fixed << std::setprecision(17) << run_uuid_ << ',' << measurement_count_ << ','
            << elapsed_time_ << ',' << spatial_planner_.uniqueCells() << ',' << spatial_planner_.effectiveHits() << ','
            << cell.cell_id << ',' << cell.visit_episodes << ',' << cell.contrast_iact << ',' << cell.omega << ','
            << cell.accumulated_discrimination << ',' << cell.acquisition_exposure << ',' << (cell.correlation_estimable ? 1 : 0) << '\n';
    }
    scim_memory_stream_.flush();
}

void OPGSLSCIMV1::writeSCIMContrastTrace() {
    if (!scim_contrast_stream_.is_open()) return;
    for (const auto& cell : spatial_planner_.snapshots()) {
        scim_contrast_stream_ << std::fixed << std::setprecision(17) << run_uuid_ << ',' << measurement_count_ << ','
            << elapsed_time_ << ',' << cell.cell_id << ',' << cell.contrast_iact << ',' << cell.omega << ','
            << cell.accumulated_discrimination << ',' << cell.accumulated_discrimination << ','
            << cell.acquisition_exposure << ',' << (cell.correlation_estimable ? 1 : 0) << '\n';
    }
    scim_contrast_stream_.flush();
}

void OPGSLSCIMV1::writeSCIMActionTrace(const SCIM::ActionScore& score, bool selected,
                                       const std::string& mode) {
    if (!scim_action_stream_.is_open()) return;
    scim_action_stream_ << std::fixed << std::setprecision(17) << run_uuid_ << ',' << step_count_ << ',' << elapsed_time_ << ','
        << score.action.x << ',' << score.action.y << ',' << score.action.z << ',' << score.target_cell << ',' << mode << ','
        << score.qbar << ',' << score.discrimination << ',' << score.j_cell << ',' << score.a_cell << ',' << score.omega_cell << ','
        << score.delta_a << ',' << score.delta_i << ',' << score.cycle_time << ',' << score.utility << ',' << (selected ? 1 : 0)
        << ",NA,NA,NA\n";
    scim_action_stream_.flush();
}

void OPGSLSCIMV1::writeActionValidityTrace(double x, double y, double z, bool accepted,
                                           const std::string& reason) {
    if (!action_validity_stream_.is_open()) return;
    const auto id = coordinateKey(x, y, z, std::max(0.05, static_cast<double>(map.info.resolution)));
    action_validity_stream_ << std::fixed << std::setprecision(9) << run_uuid_ << ',' << id << ','
        << elapsed_time_ << ',' << x << ',' << y << ',' << z << ',' << (accepted ? 1 : 0) << ','
        << reason << ",1," << z << ",NA," << planner_config_.measurement_dwell_seconds
        << ",base_link\n";
    action_validity_stream_.flush();
}

void OPGSLSCIMV1::writeDeclarationTrace(const OPGSLV3::PosteriorSummary& map_summary,
                                        const OPGSLV3::PosteriorSummary& confidence_summary,
                                        const std::string& abstention_reason) {
    if (!declaration_stream_.is_open()) return;
    const bool posterior_concentrated = confidence_summary.credible_radius > 0.0 &&
        confidence_summary.credible_radius <= 2.0;
    const bool use_tess_estimate = runtime_config_.tess_enabled && runtime_config_.tess_profile_estimate_enabled &&
        tess_estimate_.available && tess_profile_blocks_ >= runtime_config_.tess_warmup_blocks;
    const double declaration_x = use_tess_estimate ? tess_estimate_.x : map_summary.map.x;
    const double declaration_y = use_tess_estimate ? tess_estimate_.y : map_summary.map.y;
    declaration_stream_ << std::fixed << std::setprecision(9) << run_uuid_ << ',' << elapsed_time_
        << ",0," << measurement_count_ << ',' << declaration_x << ',' << declaration_y << ','
        << (posterior_concentrated ? 1 : 0)
        << ",1,0,0,0,0,0,INDEPENDENT_VERIFICATION_NOT_COMPLETED," << abstention_reason << '\n';
    declaration_stream_.flush();
}

MovingStateOPGSLSCIMV1::MovingStateOPGSLSCIMV1(Algorithm* algorithm)
    : MovingState(algorithm), scim_(dynamic_cast<OPGSLSCIMV1*>(algorithm)) {}

void MovingStateOPGSLSCIMV1::OnUpdate() {
    if (!scim_) return;
    // The fixed simulation-time budget must remain enforceable while a
    // NavigateToPose action is pending.  Previously it was checked only on a
    // completed measurement callback, allowing a stalled navigation state to
    // overrun the budget after planner pause/resume.
    if (scim_->checkSourceFound() != GSLResult::Running) {
        scim_->currentResult = GSLResult::Failure;
        scim_->saveResultsToFile(GSLResult::Failure);
        return;
    }
    if (replan_required_) {
        if (replan_wait_ticks_-- > 0) return;
        replan_required_ = false;
        chooseGoalAndMove();
        return;
    }
    if (!currentGoal.has_value()) return;
    const double elapsed = goal_timer_active_ ?
        (scim_->node->now() - goal_sent_time_).seconds() : 0.0;
    if (elapsed <= active_navigation_timeout_seconds_) return;
    GSL_WARN("OPGSLSCIMV1 navigation timeout after {:.3f}s; cancel and reselect", elapsed);
    nav_client->async_cancel_all_goals();
    currentGoal.reset();
    goal_timer_active_ = false;
    requestReplan();
}

void MovingStateOPGSLSCIMV1::requestReplan() {
    // Give Nav2 cancellation/state callbacks one scheduler turn before a new
    // goal is considered.  This is REPLAN_REQUIRED, never a terminal result.
    replan_required_ = true;
    replan_wait_ticks_ = 1;
}

NavigateToPose::Goal MovingStateOPGSLSCIMV1::posToGoal(double x, double y, double z) const {
    NavigateToPose::Goal goal; goal.pose.header.frame_id = "map";
    if (scim_) goal.pose.header.stamp = scim_->node->now();
    goal.pose.pose.position.x = x; goal.pose.pose.position.y = y; goal.pose.pose.position.z = z;
    goal.pose.pose.orientation.w = 1.0; return goal;
}

void MovingStateOPGSLSCIMV1::chooseGoalAndMove() {
    if (!scim_) return;
    ++scim_->step_count_;
    scim_->elapsed_time_ = (scim_->node->now() - scim_->startTime).seconds();
    auto actions = scim_->generateMapFeasibleActions();
    if (scim_->runtime_config_.force_first_batch_unreachable && scim_->step_count_ == 1) {
        GSL_INFO("OPGSLSCIMV1 regression: first candidate batch forced unreachable");
        actions.clear();
    }
    auto decision = scim_->planFeasibleActions(actions);
    if (decision.ranked.empty()) {
        actions = scim_->generateRecoveryActions();
        decision = scim_->planFeasibleActions(actions);
    }
    scim_->last_planner_decision_ = decision;
    if (decision.ranked.empty()) {
        GSL_WARN("OPGSLSCIMV1 REPLAN_REQUIRED: no reachable candidate after recovery: {}", decision.reason);
        requestReplan();
        return;
    }
    if (decision.inactive_warning) {
        GSL_WARN("OPGSLSCIMV1 spatial-memory diagnostic inactive; retaining all feasible candidates: {}", decision.reason);
    }
    std::optional<std::size_t> accepted_rank;
    // The VGR bridge supplies NavigateToPose but not ComputePathToPose.  When
    // that optional planning action is absent, all candidates have already
    // passed the complete occupancy/free-space filter in the generator; send
    // the best of that complete set to the active navigation action instead of
    // mistaking a missing auxiliary planner for an unreachable map target.
    const bool path_service_ready = scim_->runtime_config_.require_compute_path_check &&
        make_plan_client->action_server_is_ready();
    if (!path_service_ready && nav_client->action_server_is_ready()) {
        accepted_rank = 0;
        GSL_WARN("OPGSLSCIMV1 map-free navigation protocol active after full candidate filtering");
    } else {
        for (std::size_t i = 0; i < decision.ranked.size(); ++i) {
            const auto goal = posToGoal(decision.ranked[i].action.x, decision.ranked[i].action.y,
                                        decision.ranked[i].action.z);
            if (checkGoal(goal)) { accepted_rank = i; break; }
        }
    }
    if (!accepted_rank.has_value() && nav_client->action_server_is_ready()) {
        // Every ranked candidate has been checked.  A ComputePathToPose action
        // that accepts but never returns is an infrastructure limitation of
        // this bridge, not evidence that free-map candidates are unreachable.
        accepted_rank = 0;
        GSL_WARN("OPGSLSCIMV1 ComputePathToPose rejected all candidates; dispatching verified map-free fallback");
    }
    const bool accepted = accepted_rank.has_value();
    const auto& selected = decision.ranked[accepted ? *accepted_rank : 0U];
    scim_->writeSCIMActionTrace(selected, accepted, decision.mode);
    for (std::size_t i = 0; i < decision.ranked.size(); ++i) {
        scim_->writePlannerTrace(decision.ranked[i], accepted && i == *accepted_rank,
                                 static_cast<int>(i), decision);
    }
    if (accepted) {
        const double predicted_navigation = selected.path_valid &&
            std::isfinite(selected.predicted_navigation_seconds)
            ? selected.predicted_navigation_seconds
            : selected.cycle_time - scim_->planner_config_.measurement_dwell_seconds;
        active_navigation_timeout_seconds_ = std::max(
            scim_->runtime_config_.navigation_timeout_seconds,
            2.0 * std::max(0.0, predicted_navigation) + 2.0);
        sendGoal(posToGoal(selected.action.x, selected.action.y, selected.action.z));
        goal_sent_time_ = scim_->node->now();
        goal_timer_active_ = true;
        return;
    }
    GSL_WARN("OPGSLSCIMV1 REPLAN_REQUIRED: all candidates rejected; no gas evidence or terminal result emitted");
    requestReplan();
}

void MovingStateOPGSLSCIMV1::Fail() {
    if (scim_) {
        GSL_WARN("OPGSLSCIMV1 navigation action failed; reselecting a feasible goal");
        currentGoal.reset();
        goal_timer_active_ = false;
        scim_->OnCompleteNavigation(GSLResult::Failure, previousState);
    }
}

}  // namespace GSL
