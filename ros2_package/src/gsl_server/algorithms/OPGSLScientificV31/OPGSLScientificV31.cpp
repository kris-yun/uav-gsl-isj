#include "OPGSLScientificV31.hpp"

#include <gsl_server/algorithms/Common/States/StopAndMeasureState.hpp>
#include <gsl_server/algorithms/Common/States/WaitForGasState.hpp>
#include <gsl_server/algorithms/Common/States/WaitForMapState.hpp>
#include <gsl_server/core/Logging.hpp>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <unordered_map>

namespace GSL {
namespace {

void ensureParentDirectory(const std::string& file_path) {
    if (file_path.empty()) {
        return;
    }
    const std::filesystem::path path(file_path);
    if (path.has_parent_path()) {
        std::filesystem::create_directories(path.parent_path());
    }
}

std::vector<std::string> splitCsvLine(const std::string& line) {
    std::vector<std::string> fields;
    std::string field;
    bool quoted = false;
    for (std::size_t i = 0; i < line.size(); ++i) {
        const char ch = line[i];
        if (ch == '"') {
            if (quoted && i + 1 < line.size() && line[i + 1] == '"') {
                field.push_back('"');
                ++i;
            } else {
                quoted = !quoted;
            }
        } else if (ch == ',' && !quoted) {
            fields.push_back(field);
            field.clear();
        } else {
            field.push_back(ch);
        }
    }
    fields.push_back(field);
    return fields;
}

std::string trim(std::string value) {
    const auto not_space = [](unsigned char ch) { return !std::isspace(ch); };
    value.erase(value.begin(),
                std::find_if(value.begin(), value.end(), not_space));
    value.erase(std::find_if(value.rbegin(), value.rend(), not_space).base(),
                value.end());
    return value;
}

bool parseBool(const std::string& text) {
    const std::string value = trim(text);
    return value == "1" || value == "true" || value == "TRUE" ||
           value == "yes" || value == "YES";
}

std::unordered_map<std::string, std::size_t> headerIndex(
    const std::vector<std::string>& header) {
    std::unordered_map<std::string, std::size_t> index;
    for (std::size_t i = 0; i < header.size(); ++i) {
        index.emplace(trim(header[i]), i);
    }
    return index;
}

std::string fieldAt(const std::vector<std::string>& row,
                    const std::unordered_map<std::string, std::size_t>& index,
                    const std::string& name,
                    bool required = true) {
    const auto it = index.find(name);
    if (it == index.end() || it->second >= row.size()) {
        if (required) {
            throw std::runtime_error("Calibration CSV missing field: " + name);
        }
        return {};
    }
    return trim(row[it->second]);
}

double fieldDouble(const std::vector<std::string>& row,
                   const std::unordered_map<std::string, std::size_t>& index,
                   const std::string& name) {
    return std::stod(fieldAt(row, index, name));
}

int fieldInt(const std::vector<std::string>& row,
             const std::unordered_map<std::string, std::size_t>& index,
             const std::string& name) {
    return std::stoi(fieldAt(row, index, name));
}

std::int64_t coordinateKey(double x, double y, double z, double resolution) {
    const double safe = std::max(resolution, 1e-3);
    const auto ix = static_cast<std::int64_t>(std::llround(x / safe));
    const auto iy = static_cast<std::int64_t>(std::llround(y / safe));
    const auto iz = static_cast<std::int64_t>(std::llround(z / safe));
    return (ix * 73856093LL) ^ (iy * 19349663LL) ^ (iz * 83492791LL);
}

}  // namespace

OPGSLScientificV31::OPGSLScientificV31(std::shared_ptr<rclcpp::Node> node)
    : Algorithm(std::move(node)),
      planner_(planner_config_),
      verifier_(verification_config_) {}

void OPGSLScientificV31::declareParameters() {
    Algorithm::declareParameters();

    runtime_config_.scientific_mode = getParam<bool>(
        "opgsl.v3.scientific_mode", true);
    runtime_config_.calibration_file = getParam<std::string>(
        "opgsl.v3.calibration_file", "");
    runtime_config_.grid_nx = getParam<int>("opgsl.v3.grid.nx", 30);
    runtime_config_.grid_ny = getParam<int>("opgsl.v3.grid.ny", 30);
    runtime_config_.grid_nz = getParam<int>("opgsl.v3.grid.nz", 1);
    runtime_config_.source_z_min = getParam<double>(
        "opgsl.v3.grid.source_z_min", 0.0);
    runtime_config_.source_z_max = getParam<double>(
        "opgsl.v3.grid.source_z_max", 0.0);
    runtime_config_.nominal_flight_height = getParam<double>(
        "opgsl.v3.flight.nominal_height", 0.3);
    runtime_config_.min_flight_height = getParam<double>(
        "opgsl.v3.flight.min_height", runtime_config_.nominal_flight_height);
    runtime_config_.max_flight_height = getParam<double>(
        "opgsl.v3.flight.max_height", runtime_config_.nominal_flight_height);
    runtime_config_.max_vertical_step = getParam<double>(
        "opgsl.v3.flight.max_vertical_step", 0.3);
    runtime_config_.angular_samples = getParam<int>(
        "opgsl.v3.actions.angular_samples", 16);
    runtime_config_.radial_samples = getParam<int>(
        "opgsl.v3.actions.radial_samples", 2);
    runtime_config_.min_action_radius = getParam<double>(
        "opgsl.v3.actions.min_radius", 0.6);
    runtime_config_.max_action_radius = getParam<double>(
        "opgsl.v3.actions.max_radius", 1.8);
    runtime_config_.include_vertical_probe = getParam<bool>(
        "opgsl.v3.actions.include_vertical_probe", true);
    runtime_config_.include_elevated_traverse = getParam<bool>(
        "opgsl.v3.actions.include_elevated_traverse", true);
    runtime_config_.vertical_samples_each_direction = getParam<int>(
        "opgsl.v3.actions.vertical_samples_each_direction", 1);
    runtime_config_.max_steps = getParam<int>("opgsl.v3.max_steps", 300);
    runtime_config_.seed = getParam<int>("opgsl.v3.seed", 0);
    runtime_config_.evidence_mode = parseEvidenceMode(getParam<std::string>(
        "opgsl.v3.ablation.evidence_mode", "proper_joint"));
    runtime_config_.use_skill_verifier = getParam<bool>(
        "opgsl.v3.ablation.use_skill_verifier", true);
    runtime_config_.radius_only_stop_ablation = getParam<bool>(
        "opgsl.v3.ablation.radius_only_stop", false);

    planner_config_.horizontal_speed_mps = getParam<double>(
        "opgsl.v3.platform.horizontal_speed_mps", 0.4);
    planner_config_.vertical_speed_mps = getParam<double>(
        "opgsl.v3.platform.vertical_speed_mps", 0.2);
    planner_config_.measurement_dwell_seconds = getParam<double>(
        "stop_and_measure_time", 2.0);
    planner_config_.vertical_actions_requested = getParam<bool>(
        "opgsl.v3.actions.enable_vertical", false);
    planner_config_.conservative_vertical_gate = getParam<bool>(
        "opgsl.v3.ablation.conservative_vertical_gate", true);
    planner_config_.vertical_posterior_quantile = getParam<double>(
        "opgsl.v3.actions.vertical_model_lower_quantile", 0.05);

    verification_config_.target_credible_radius_m = getParam<double>(
        "opgsl.v3.stop.target_credible_radius_m", 1.5);
    verification_config_.credible_mass = getParam<double>(
        "opgsl.v3.stop.credible_mass", 0.90);
    verification_config_.alpha = getParam<double>(
        "opgsl.v3.statistics.alpha", 0.05);
    verification_config_.null_prior_hit = getParam<double>(
        "opgsl.v3.stop.null_prior_hit", 0.5);
    verification_config_.null_prior_miss = getParam<double>(
        "opgsl.v3.stop.null_prior_miss", 0.5);

    run_uuid_ = getParam<std::string>("run_uuid", "opgsl_core_v3");
    source_estimate_trace_file_ = getParam<std::string>(
        "source_estimate_trace_file", "");
    evidence_trace_file_ = getParam<std::string>(
        "opgsl.v3.trace.evidence", "");
    planner_trace_file_ = getParam<std::string>(
        "opgsl.v3.trace.planner", "");
    stop_trace_file_ = getParam<std::string>(
        "opgsl.v3.trace.stop", "");
    parameter_snapshot_file_ = getParam<std::string>(
        "opgsl.v3.trace.parameter_snapshot", "");

    loadCalibrationArtifact();
    planner_.setConfig(planner_config_);
    verifier_.setConfig(verification_config_);

    GSL_INFO(
        "OPGSLScientificV31 V3: calibration={} models={} scientific_valid={} vertical_valid={} "
        "grid={}x{}x{} evidence={} vertical_requested={} alpha={:.3f}",
        observation_models_.metadata().calibration_id,
        observation_models_.size(),
        observation_models_.metadata().scientific_valid,
        observation_models_.metadata().vertical_feature_valid,
        runtime_config_.grid_nx,
        runtime_config_.grid_ny,
        runtime_config_.grid_nz,
        evidenceModeName(runtime_config_.evidence_mode),
        planner_config_.vertical_actions_requested,
        verification_config_.alpha);
}

void OPGSLScientificV31::loadCalibrationArtifact() {
    std::vector<OPGSLV3::ObservationModelParameters> models;
    OPGSLV3::CalibrationMetadata metadata;

    if (!runtime_config_.calibration_file.empty()) {
        std::ifstream input(runtime_config_.calibration_file);
        if (!input.is_open()) {
            throw std::runtime_error(
                "Cannot open OPGSLScientificV31 calibration artifact: " +
                runtime_config_.calibration_file);
        }
        std::string line;
        if (!std::getline(input, line)) {
            throw std::runtime_error("Calibration CSV is empty");
        }
        const auto header = splitCsvLine(line);
        const auto index = headerIndex(header);
        while (std::getline(input, line)) {
            if (trim(line).empty()) {
                continue;
            }
            const auto row = splitCsvLine(line);
            OPGSLV3::ObservationModelParameters model;
            model.model_id = fieldInt(row, index, "model_id");
            model.nominal = parseBool(fieldAt(row, index, "is_nominal"));
            const std::string prior_text = fieldAt(
                row, index, "prior_weight", false);
            model.prior_weight = prior_text.empty() ? 1.0 : std::stod(prior_text);
            model.isotropic_intercept = fieldDouble(
                row, index, "isotropic_intercept");
            model.isotropic_distance_decay = fieldDouble(
                row, index, "isotropic_distance_decay");
            model.wind_intercept = fieldDouble(
                row, index, "wind_intercept");
            model.downwind_distance_decay = fieldDouble(
                row, index, "downwind_distance_decay");
            model.upstream_distance_decay = fieldDouble(
                row, index, "upstream_distance_decay");
            model.crosswind_squared_decay = fieldDouble(
                row, index, "crosswind_squared_decay");
            model.vertical_squared_decay = fieldDouble(
                row, index, "vertical_squared_decay");
            model.wind_noise_speed_sigma = fieldDouble(
                row, index, "wind_noise_speed_sigma");
            models.push_back(model);

            if (models.size() == 1 || model.nominal) {
                metadata.scientific_valid = parseBool(fieldAt(
                    row, index, "scientific_valid"));
                metadata.vertical_feature_valid = parseBool(fieldAt(
                    row, index, "vertical_feature_valid"));
                metadata.calibration_house_count = fieldInt(
                    row, index, "calibration_house_count");
                metadata.calibration_run_count = fieldInt(
                    row, index, "calibration_run_count");
                metadata.heldout_brier_skill_ci_low = fieldDouble(
                    row, index, "heldout_brier_skill_ci_low");
                metadata.vertical_brier_gain_ci_low = fieldDouble(
                    row, index, "vertical_brier_gain_ci_low");
                metadata.calibration_id = fieldAt(
                    row, index, "calibration_id");
            }
        }
        std::stable_sort(models.begin(), models.end(),
            [](const auto& lhs, const auto& rhs) {
                if (lhs.nominal != rhs.nominal) {
                    return lhs.nominal;
                }
                return lhs.model_id < rhs.model_id;
            });
    }

    if (models.empty()) {
        if (runtime_config_.scientific_mode) {
            throw std::runtime_error(
                "Scientific mode requires a grouped calibration CSV. "
                "Run calibration/fit_grouped_evidence_calibration.py first.");
        }
        OPGSLV3::ObservationModelParameters smoke;
        smoke.nominal = true;
        models.push_back(smoke);
        metadata.scientific_valid = false;
        metadata.vertical_feature_valid = false;
        metadata.calibration_id = "SMOKE_ONLY_UNCALIBRATED";
        GSL_WARN(
            "OPGSLScientificV31 V3 is using uncalibrated smoke parameters. "
            "The run MUST be marked scientific_trace_valid=false.");
    }

    observation_models_.setModels(std::move(models), metadata);
    if (runtime_config_.scientific_mode && !metadata.scientific_valid) {
        throw std::runtime_error(
            "Calibration artifact failed its grouped held-out Brier-skill gate");
    }
    scientific_trace_valid_ = runtime_config_.scientific_mode &&
                              metadata.scientific_valid;
}

void OPGSLScientificV31::Initialize() {
    waitForMapState = std::make_unique<WaitForMapState>(this);
    waitForGasState = std::make_unique<WaitForGasState>(this);
    stopAndMeasureState = std::make_unique<StopAndMeasureState>(this);
    movingState = std::make_unique<MovingStateOPGSLScientificV31>(this);

    Algorithm::Initialize();
    rng_.seed(static_cast<std::mt19937::result_type>(runtime_config_.seed));
    verifier_.reset();
    initializeTraceFiles();
    writeParameterSnapshot();
    stateMachine.forceSetState(waitForMapState.get());
}

void OPGSLScientificV31::onGetMap(const OccupancyGrid::SharedPtr msg) {
    Algorithm::onGetMap(msg);
    map_received_ = true;
    initializePosteriorFromMap();
    stateMachine.forceResetState(stopAndMeasureState.get());
}

std::vector<bool> OPGSLScientificV31::buildSourceValidityMask(
    const OPGSLV3::GridSpec& spec) {
    const double dx = (spec.x_max - spec.x_min) /
                      static_cast<double>(spec.nx);
    const double dy = (spec.y_max - spec.y_min) /
                      static_cast<double>(spec.ny);
    std::vector<bool> mask(
        static_cast<std::size_t>(spec.nx) *
        static_cast<std::size_t>(spec.ny) *
        static_cast<std::size_t>(spec.nz),
        false);
    std::size_t index = 0;
    for (int i = 0; i < spec.nx; ++i) {
        for (int j = 0; j < spec.ny; ++j) {
            const double x = spec.x_min + (static_cast<double>(i) + 0.5) * dx;
            const double y = spec.y_min + (static_cast<double>(j) + 0.5) * dy;
            const bool free = isPointFree(Vector2(x, y));
            for (int k = 0; k < spec.nz; ++k) {
                mask[index++] = free;
            }
        }
    }
    return mask;
}

void OPGSLScientificV31::initializePosteriorFromMap() {
    if (posterior_initialized_) {
        return;
    }
    if (!map_received_ || map.info.width == 0 || map.info.height == 0 ||
        map.info.resolution <= 0.0) {
        throw std::runtime_error("Cannot initialize OPGSLScientificV31 posterior without a valid map");
    }
    OPGSLV3::GridSpec spec;
    spec.nx = runtime_config_.grid_nx;
    spec.ny = runtime_config_.grid_ny;
    spec.nz = runtime_config_.grid_nz;
    spec.x_min = map.info.origin.position.x;
    spec.x_max = map.info.origin.position.x +
        static_cast<double>(map.info.width) * map.info.resolution;
    spec.y_min = map.info.origin.position.y;
    spec.y_max = map.info.origin.position.y +
        static_cast<double>(map.info.height) * map.info.resolution;
    spec.z_min = runtime_config_.source_z_min;
    spec.z_max = runtime_config_.grid_nz > 1
        ? runtime_config_.source_z_max
        : runtime_config_.source_z_min;

    auto mask = buildSourceValidityMask(spec);
    std::vector<double> model_priors = observation_models_.normalizedPriorWeights();
    if (runtime_config_.evidence_mode == OPGSLV3::EvidenceMode::NominalOnly) {
        model_priors.assign(observation_models_.size(), 0.0);
        model_priors.front() = 1.0;
    }
    posterior_.initialize(spec, std::move(mask), std::move(model_priors));
    posterior_initialized_ = true;
    GSL_INFO(
        "OPGSLScientificV31 V3 posterior: valid_sources={} models={} joint_states={}",
        posterior_.validSourceCount(), posterior_.modelCount(),
        posterior_.validSourceCount() * posterior_.modelCount());
}

OPGSLV3::ObservationContext OPGSLScientificV31::makeObservationContext(
    double sensor_x,
    double sensor_y,
    double sensor_z,
    double concentration) const {
    OPGSLV3::ObservationContext context;
    context.sensor_x = sensor_x;
    context.sensor_y = sensor_y;
    context.sensor_z = sensor_z;
    context.wind_x = latest_wind_x_;
    context.wind_y = latest_wind_y_;
    context.wind_z = 0.0;
    context.wind_speed = latest_wind_speed_;
    context.concentration = concentration;
    context.detection_threshold = thresholdGas;
    return context;
}

void OPGSLScientificV31::processGasAndWindMeasurements(double concentration,
                                           double windSpeed,
                                           double windDirection) {
    if (source_declared_) {
        return;
    }
    if (!posterior_initialized_) {
        initializePosteriorFromMap();
    }
    elapsed_time_ = (node->now() - startTime).seconds();
    latest_concentration_ = concentration;
    latest_wind_speed_ = std::max(0.0, windSpeed);
    latest_wind_x_ = latest_wind_speed_ * std::cos(windDirection);
    latest_wind_y_ = latest_wind_speed_ * std::sin(windDirection);

    const double pose_z = clipToFlightBounds(
        std::isfinite(currentRobotPose.pose.pose.position.z)
            ? currentRobotPose.pose.pose.position.z
            : runtime_config_.nominal_flight_height);
    const auto observation = makeObservationContext(
        currentRobotPosition.x,
        currentRobotPosition.y,
        pose_z,
        latest_concentration_);
    const bool detected = latest_concentration_ > thresholdGas;

    const double predictive = posterior_.predictiveHitProbability(
        observation, observation_models_);
    verifier_.observeBeforePosteriorUpdate(predictive, detected);
    last_update_diagnostics_ = posterior_.update(
        observation, observation_models_, runtime_config_.evidence_mode);
    ++measurement_count_;
    detected ? ++hit_count_ : ++miss_count_;
    markVisited(observation.sensor_x, observation.sensor_y, observation.sensor_z);

    const auto summary = posterior_.summary(verification_config_.credible_mass);
    last_verification_status_ = verifier_.evaluate(summary);
    writeEvidenceTrace(summary);
    writeSourceEstimateTrace(summary);

    const GSLResult result = checkSourceFound();
    if (result != GSLResult::Running) {
        currentResult = result;
        source_declared_ = true;
        writeStopTrace(summary,
            result == GSLResult::Success ? last_verification_status_.reason
                                         : "budget_or_step_failure",
            result);
        saveResultsToFile(result);
        return;
    }
    movingState->chooseGoalAndMove();
}

GSLResult OPGSLScientificV31::checkSourceFound() {
    elapsed_time_ = (node->now() - startTime).seconds();
    if (elapsed_time_ >= resultLogging.maxSearchTime ||
        step_count_ >= runtime_config_.max_steps) {
        return GSLResult::Failure;
    }
    if (!posterior_initialized_) {
        return GSLResult::Running;
    }
    const auto summary = posterior_.summary(verification_config_.credible_mass);
    if (runtime_config_.radius_only_stop_ablation) {
        return summary.credible_radius <=
               verification_config_.target_credible_radius_m
            ? GSLResult::Success
            : GSLResult::Running;
    }
    if (!runtime_config_.use_skill_verifier) {
        return GSLResult::Running;
    }
    return last_verification_status_.verified
        ? GSLResult::Success
        : GSLResult::Running;
}

std::vector<OPGSLV3::FeasibleAction> OPGSLScientificV31::generateMapFeasibleActions() {
    std::vector<OPGSLV3::FeasibleAction> actions;
    if (!posterior_initialized_ || !map_received_) {
        return actions;
    }
    const double current_x = currentRobotPosition.x;
    const double current_y = currentRobotPosition.y;
    const double current_z = clipToFlightBounds(
        std::isfinite(currentRobotPose.pose.pose.position.z)
            ? currentRobotPose.pose.pose.position.z
            : runtime_config_.nominal_flight_height);

    std::vector<double> heights{current_z};
    if (planner_config_.vertical_actions_requested) {
        for (int step = 1;
             step <= std::max(1, runtime_config_.vertical_samples_each_direction);
             ++step) {
            const double dz = runtime_config_.max_vertical_step *
                              static_cast<double>(step);
            heights.push_back(clipToFlightBounds(current_z - dz));
            heights.push_back(clipToFlightBounds(current_z + dz));
        }
    }
    std::sort(heights.begin(), heights.end());
    heights.erase(std::unique(heights.begin(), heights.end(),
        [](double lhs, double rhs) {
            return std::abs(lhs - rhs) <= 1e-9;
        }), heights.end());

    std::set<std::int64_t> seen;
    const double key_resolution = std::max(
        0.05, static_cast<double>(map.info.resolution));
    const auto add_action = [&](double x, double y, double z,
                                OPGSLV3::ActionType type,
                                auto& output) {
        Vector2 point(x, y);
        if (!isPointInsideMapBounds(point) || !isPointFree(point)) {
            return;
        }
        z = clipToFlightBounds(z);
        const auto key = coordinateKey(x, y, z, key_resolution);
        if (!seen.insert(key).second) {
            return;
        }
        OPGSLV3::FeasibleAction action;
        action.x = x;
        action.y = y;
        action.z = z;
        action.type = type;
        action.visit_count = visitCount(x, y, z);
        output.push_back(action);
    };

    for (const double height : heights) {
        const bool changed = std::abs(height - current_z) > 1e-9;
        if (changed && runtime_config_.include_vertical_probe) {
            add_action(current_x, current_y, height,
                       OPGSLV3::ActionType::VerticalProbe, actions);
        }
        if (changed && !runtime_config_.include_elevated_traverse) {
            continue;
        }
        for (int r = 0; r < std::max(1, runtime_config_.radial_samples); ++r) {
            const double fraction = runtime_config_.radial_samples <= 1
                ? 1.0
                : static_cast<double>(r) /
                  static_cast<double>(runtime_config_.radial_samples - 1);
            const double radius = runtime_config_.min_action_radius +
                fraction * (runtime_config_.max_action_radius -
                            runtime_config_.min_action_radius);
            for (int a = 0; a < std::max(1, runtime_config_.angular_samples); ++a) {
                const double angle = 2.0 * OPGSLV3::kPi *
                    static_cast<double>(a) /
                    static_cast<double>(std::max(1, runtime_config_.angular_samples));
                add_action(
                    current_x + radius * std::cos(angle),
                    current_y + radius * std::sin(angle),
                    height,
                    changed ? OPGSLV3::ActionType::ElevatedTraverse
                            : OPGSLV3::ActionType::PlanarTraverse,
                    actions);
            }
        }
    }
    return actions;
}

OPGSLV3::PlannerDecision OPGSLScientificV31::planFeasibleActions(
    const std::vector<OPGSLV3::FeasibleAction>& actions) const {
    if (!posterior_initialized_) {
        return {};
    }
    const double current_z = clipToFlightBounds(
        std::isfinite(currentRobotPose.pose.pose.position.z)
            ? currentRobotPose.pose.pose.position.z
            : runtime_config_.nominal_flight_height);
    const auto context = makeObservationContext(
        currentRobotPosition.x,
        currentRobotPosition.y,
        current_z,
        0.0);
    return planner_.choose(
        actions,
        currentRobotPosition.x,
        currentRobotPosition.y,
        current_z,
        context,
        posterior_,
        observation_models_);
}

std::int64_t OPGSLScientificV31::visitKey(double x, double y, double z) const {
    const double resolution = map.info.resolution > 0.0
        ? map.info.resolution
        : 0.5;
    return coordinateKey(x, y, z, resolution);
}

int OPGSLScientificV31::visitCount(double x, double y, double z) const {
    const auto it = visit_counts_.find(visitKey(x, y, z));
    return it == visit_counts_.end() ? 0 : it->second;
}

void OPGSLScientificV31::markVisited(double x, double y, double z) {
    ++visit_counts_[visitKey(x, y, z)];
}

double OPGSLScientificV31::clipToFlightBounds(double z) const {
    if (!std::isfinite(z)) {
        z = runtime_config_.nominal_flight_height;
    }
    if (!planner_config_.vertical_actions_requested) {
        return runtime_config_.nominal_flight_height;
    }
    return std::clamp(z,
                      runtime_config_.min_flight_height,
                      runtime_config_.max_flight_height);
}

void OPGSLScientificV31::saveResultsToFile(GSLResult result) {
    OPGSLV3::PosteriorSummary summary;
    if (posterior_initialized_) {
        summary = posterior_.summary(verification_config_.credible_mass);
    }
    // The base state machine can terminate on the search budget without
    // passing through checkSourceFound(). Preserve one terminal stop record
    // for that path; this is trace bookkeeping and does not alter the result.
    if (!stop_trace_written_) {
        writeStopTrace(summary, "terminal_result", result);
    }
    GSL_INFO(
        "OPGSLScientificV31 V3 result={} MAP=({:.3f},{:.3f},{:.3f}) radius={:.3f} "
        "skill_lcb={:.6f} measurements={} scientific_valid={}",
        static_cast<int>(result),
        summary.map.x, summary.map.y, summary.map.z,
        summary.credible_radius,
        last_verification_status_.brier_skill_lcb,
        measurement_count_, scientific_trace_valid_);

    if (!resultLogging.resultsFile.empty()) {
        ensureParentDirectory(resultLogging.resultsFile);
        const bool header = !std::filesystem::exists(resultLogging.resultsFile) ||
            std::filesystem::file_size(resultLogging.resultsFile) == 0;
        std::ofstream output(resultLogging.resultsFile,
                             std::ios::out | std::ios::app);
        if (output.is_open()) {
            if (header) {
                output << "run_uuid,result,elapsed_time,steps,measurements,hits,misses,"
                          "map_x,map_y,map_z,entropy,variance,credible_radius,"
                          "mean_brier_skill,brier_skill_lcb,verified,scientific_trace_valid,reason\n";
            }
            output << std::fixed << std::setprecision(9)
                   << run_uuid_ << ',' << static_cast<int>(result) << ','
                   << elapsed_time_ << ',' << step_count_ << ','
                   << measurement_count_ << ',' << hit_count_ << ',' << miss_count_ << ','
                   << summary.map.x << ',' << summary.map.y << ',' << summary.map.z << ','
                   << summary.entropy << ',' << summary.variance << ','
                   << summary.credible_radius << ','
                   << last_verification_status_.mean_brier_skill << ','
                   << last_verification_status_.brier_skill_lcb << ','
                   << (last_verification_status_.verified ? 1 : 0) << ','
                   << (scientific_trace_valid_ ? 1 : 0) << ','
                   << last_verification_status_.reason << '\n';
        }
    }
}

void OPGSLScientificV31::OnUpdate() {
    Algorithm::OnUpdate();
}

void OPGSLScientificV31::OnCompleteNavigation(GSLResult result, State* previousState) {
    (void)result;
    (void)previousState;
    stateMachine.forceResetState(stopAndMeasureState.get());
}

void OPGSLScientificV31::initializeTraceFiles() {
    const auto open = [](const std::string& path,
                         std::ofstream& stream,
                         const std::string& header) {
        if (path.empty()) {
            return;
        }
        ensureParentDirectory(path);
        stream.open(path, std::ios::out | std::ios::trunc);
        if (stream.is_open()) {
            stream << header << '\n';
        }
    };
    open(source_estimate_trace_file_, source_estimate_stream_,
         "run_uuid,cycle,sim_time,method,estimate_available,estimate_semantics,"
         "map_x,map_y,map_z,entropy,variance,credible_mass,credible_radius,"
         "map_probability,model_count,verified,scientific_trace_valid,reason");
    open(evidence_trace_file_, evidence_stream_,
         "run_uuid,cycle,sim_time,evidence_mode,concentration,detected,wind_speed,"
         "predictive_q,source_brier,source_nll,entropy_before,entropy_after,"
         "normalization_error,null_q,mean_brier_skill,brier_skill_lcb,"
         "source_nll_sum,null_nll_sum,reason");
    open(planner_trace_file_, planner_stream_,
         "run_uuid,step,sim_time,rank,selected,x,y,z,action_type,visit_count,"
         "horizontal_distance,vertical_distance,cycle_time_s,eig_nats,eig_bits,"
         "information_rate_bps,vertical_model_valid,vertical_gate_open,"
         "vertical_rate_difference_lower_quantile,decision_reason");
    open(stop_trace_file_, stop_stream_,
         "run_uuid,cycle,sim_time,decision,result,posterior_concentrated,"
         "skill_positive,verified,count,hits,misses,mean_brier_skill,"
         "brier_skill_lcb,credible_radius,map_x,map_y,map_z,reason");
}

void OPGSLScientificV31::writeParameterSnapshot() const {
    if (parameter_snapshot_file_.empty()) {
        return;
    }
    ensureParentDirectory(parameter_snapshot_file_);
    std::ofstream out(parameter_snapshot_file_, std::ios::out | std::ios::trunc);
    if (!out.is_open()) {
        return;
    }
    out << "run_uuid=" << run_uuid_ << '\n'
        << "scientific_mode=" << runtime_config_.scientific_mode << '\n'
        << "calibration_file=" << runtime_config_.calibration_file << '\n'
        << "calibration_id=" << observation_models_.metadata().calibration_id << '\n'
        << "calibration_scientific_valid="
        << observation_models_.metadata().scientific_valid << '\n'
        << "vertical_feature_valid="
        << observation_models_.metadata().vertical_feature_valid << '\n'
        << "calibration_house_count="
        << observation_models_.metadata().calibration_house_count << '\n'
        << "calibration_run_count="
        << observation_models_.metadata().calibration_run_count << '\n'
        << "model_count=" << observation_models_.size() << '\n'
        << "grid=" << runtime_config_.grid_nx << 'x'
        << runtime_config_.grid_ny << 'x' << runtime_config_.grid_nz << '\n'
        << "horizontal_speed_mps=" << planner_config_.horizontal_speed_mps << '\n'
        << "vertical_speed_mps=" << planner_config_.vertical_speed_mps << '\n'
        << "measurement_dwell_seconds="
        << planner_config_.measurement_dwell_seconds << '\n'
        << "target_credible_radius_m="
        << verification_config_.target_credible_radius_m << '\n'
        << "credible_mass=" << verification_config_.credible_mass << '\n'
        << "skill_alpha=" << verification_config_.alpha << '\n'
        << "vertical_model_lower_quantile="
        << planner_config_.vertical_posterior_quantile << '\n'
        << "vertical_actions_requested="
        << planner_config_.vertical_actions_requested << '\n'
        << "min_flight_height=" << runtime_config_.min_flight_height << '\n'
        << "max_flight_height=" << runtime_config_.max_flight_height << '\n'
        << "max_vertical_step=" << runtime_config_.max_vertical_step << '\n'
        << "angular_samples=" << runtime_config_.angular_samples << '\n'
        << "radial_samples=" << runtime_config_.radial_samples << '\n'
        << "min_action_radius=" << runtime_config_.min_action_radius << '\n'
        << "max_action_radius=" << runtime_config_.max_action_radius << '\n'
        << "evidence_mode=" << evidenceModeName(runtime_config_.evidence_mode) << '\n';
}

void OPGSLScientificV31::writeEvidenceTrace(const OPGSLV3::PosteriorSummary& summary) {
    (void)summary;
    if (!evidence_stream_.is_open()) {
        return;
    }
    evidence_stream_ << std::fixed << std::setprecision(9)
        << run_uuid_ << ',' << measurement_count_ << ',' << elapsed_time_ << ','
        << evidenceModeName(runtime_config_.evidence_mode) << ','
        << latest_concentration_ << ','
        << (latest_concentration_ > thresholdGas ? 1 : 0) << ','
        << latest_wind_speed_ << ','
        << last_update_diagnostics_.predictive_hit_probability << ','
        << last_update_diagnostics_.source_brier << ','
        << last_update_diagnostics_.source_nll << ','
        << last_update_diagnostics_.entropy_before << ','
        << last_update_diagnostics_.entropy_after << ','
        << last_update_diagnostics_.normalization_error << ','
        << last_verification_status_.null_prediction << ','
        << last_verification_status_.mean_brier_skill << ','
        << last_verification_status_.brier_skill_lcb << ','
        << last_verification_status_.cumulative_source_nll << ','
        << last_verification_status_.cumulative_null_nll << ','
        << last_verification_status_.reason << '\n';
    evidence_stream_.flush();
}

void OPGSLScientificV31::writeSourceEstimateTrace(const OPGSLV3::PosteriorSummary& summary) {
    if (!source_estimate_stream_.is_open()) {
        return;
    }
    source_estimate_stream_ << std::fixed << std::setprecision(9)
        << run_uuid_ << ',' << measurement_count_ << ',' << elapsed_time_ << ','
        << "OPGSL_CORE_V3,1,JOINT_SOURCE_MODEL_POSTERIOR_MAP,"
        << summary.map.x << ',' << summary.map.y << ',' << summary.map.z << ','
        << summary.entropy << ',' << summary.variance << ','
        << summary.credible_mass << ',' << summary.credible_radius << ','
        << summary.map_probability << ',' << summary.model_marginal.size() << ','
        << (last_verification_status_.verified ? 1 : 0) << ','
        << (scientific_trace_valid_ ? 1 : 0) << ','
        << last_verification_status_.reason << '\n';
    source_estimate_stream_.flush();
}

void OPGSLScientificV31::writePlannerTrace(const OPGSLV3::ActionScore& score,
                              bool selected,
                              int rank,
                              const OPGSLV3::PlannerDecision& decision) {
    if (!planner_stream_.is_open()) {
        return;
    }
    planner_stream_ << std::fixed << std::setprecision(9)
        << run_uuid_ << ',' << step_count_ << ',' << elapsed_time_ << ','
        << rank << ',' << (selected ? 1 : 0) << ','
        << score.action.x << ',' << score.action.y << ',' << score.action.z << ','
        << OPGSLV3::actionTypeName(score.action.type) << ','
        << score.action.visit_count << ','
        << score.horizontal_distance << ',' << score.vertical_distance << ','
        << score.cycle_time_seconds << ','
        << score.expected_information_nats << ','
        << score.expected_information_bits << ','
        << score.information_rate_bits_per_second << ','
        << (decision.vertical_model_valid ? 1 : 0) << ','
        << (decision.vertical_gate_open ? 1 : 0) << ','
        << decision.vertical_rate_difference_lower_quantile << ','
        << decision.reason << '\n';
    planner_stream_.flush();
}

void OPGSLScientificV31::writeStopTrace(const OPGSLV3::PosteriorSummary& summary,
                           const std::string& decision,
                           GSLResult result) {
    if (!stop_stream_.is_open()) {
        return;
    }
    stop_stream_ << std::fixed << std::setprecision(9)
        << run_uuid_ << ',' << measurement_count_ << ',' << elapsed_time_ << ','
        << decision << ',' << static_cast<int>(result) << ','
        << (last_verification_status_.posterior_concentrated ? 1 : 0) << ','
        << (last_verification_status_.skill_positive ? 1 : 0) << ','
        << (last_verification_status_.verified ? 1 : 0) << ','
        << last_verification_status_.count << ','
        << last_verification_status_.hits << ','
        << last_verification_status_.misses << ','
        << last_verification_status_.mean_brier_skill << ','
        << last_verification_status_.brier_skill_lcb << ','
        << summary.credible_radius << ','
        << summary.map.x << ',' << summary.map.y << ',' << summary.map.z << ','
        << last_verification_status_.reason << '\n';
    stop_stream_.flush();
    stop_trace_written_ = true;
}

OPGSLV3::EvidenceMode OPGSLScientificV31::parseEvidenceMode(const std::string& mode) {
    if (mode == "proper_joint") return OPGSLV3::EvidenceMode::ProperJoint;
    if (mode == "nominal_only") return OPGSLV3::EvidenceMode::NominalOnly;
    if (mode == "legacy_same_polarity") return OPGSLV3::EvidenceMode::LegacySamePolarity;
    if (mode == "hit_only") return OPGSLV3::EvidenceMode::HitOnly;
    if (mode == "miss_only") return OPGSLV3::EvidenceMode::MissOnly;
    throw std::invalid_argument("Unknown OPGSLScientificV31 V3 evidence mode: " + mode);
}

std::string OPGSLScientificV31::evidenceModeName(OPGSLV3::EvidenceMode mode) {
    switch (mode) {
        case OPGSLV3::EvidenceMode::ProperJoint: return "proper_joint";
        case OPGSLV3::EvidenceMode::NominalOnly: return "nominal_only";
        case OPGSLV3::EvidenceMode::LegacySamePolarity: return "legacy_same_polarity";
        case OPGSLV3::EvidenceMode::HitOnly: return "hit_only";
        case OPGSLV3::EvidenceMode::MissOnly: return "miss_only";
    }
    return "unknown";
}

MovingStateOPGSLScientificV31::MovingStateOPGSLScientificV31(Algorithm* algorithm)
    : MovingState(algorithm), opgsl_(dynamic_cast<OPGSLScientificV31*>(algorithm)) {}

NavigateToPose::Goal MovingStateOPGSLScientificV31::posToGoal(
    double x, double y, double z) const {
    NavigateToPose::Goal goal;
    goal.pose.header.frame_id = "map";
    if (opgsl_) {
        goal.pose.header.stamp = opgsl_->node->now();
    }
    goal.pose.pose.position.x = x;
    goal.pose.pose.position.y = y;
    goal.pose.pose.position.z = z;
    goal.pose.pose.orientation.w = 1.0;
    return goal;
}

void MovingStateOPGSLScientificV31::chooseGoalAndMove() {
    if (!opgsl_) {
        GSL_ERROR("OPGSLScientificV31 V3 moving state has null algorithm pointer");
        return;
    }
    ++opgsl_->step_count_;
    opgsl_->elapsed_time_ = (opgsl_->node->now() - opgsl_->startTime).seconds();

    auto actions = opgsl_->generateMapFeasibleActions();
    int rejected_rank = 0;
    while (!actions.empty()) {
        auto decision = opgsl_->planFeasibleActions(actions);
        opgsl_->last_planner_decision_ = decision;
        if (!decision.selected.has_value()) {
            break;
        }
        const auto selected = *decision.selected;
        const auto goal = posToGoal(
            selected.action.x,
            selected.action.y,
            selected.action.z);
        const bool accepted = checkGoal(goal);
        for (std::size_t i = 0; i < decision.ranked.size(); ++i) {
            const auto& item = decision.ranked[i];
            const bool is_selected =
                std::abs(item.action.x - selected.action.x) <= 1e-9 &&
                std::abs(item.action.y - selected.action.y) <= 1e-9 &&
                std::abs(item.action.z - selected.action.z) <= 1e-9;
            opgsl_->writePlannerTrace(item, is_selected && accepted,
                                      static_cast<int>(i), decision);
        }
        if (accepted) {
            GSL_INFO(
                "OPGSLScientificV31 V3 step={} goal=({:.2f},{:.2f},{:.2f}) type={} "
                "rate={:.6f} bit/s vertical_lower_quantile={:.6f} reason={}",
                opgsl_->step_count_,
                selected.action.x, selected.action.y, selected.action.z,
                OPGSLV3::actionTypeName(selected.action.type),
                selected.information_rate_bits_per_second,
                decision.vertical_rate_difference_lower_quantile,
                decision.reason);
            sendGoal(goal);
            return;
        }

        // Remove the rejected action and recompute all rankings. The executed
        // action is therefore always evaluated at the exact feasible pose.
        actions.erase(std::remove_if(actions.begin(), actions.end(),
            [&](const OPGSLV3::FeasibleAction& action) {
                return std::abs(action.x - selected.action.x) <= 1e-9 &&
                       std::abs(action.y - selected.action.y) <= 1e-9 &&
                       std::abs(action.z - selected.action.z) <= 1e-9;
            }), actions.end());
        ++rejected_rank;
        if (rejected_rank > 32) {
            break;
        }
    }
    GSL_ERROR("OPGSLScientificV31 V3 found no navigation-feasible information action");
    opgsl_->currentResult = GSLResult::Failure;
}

void MovingStateOPGSLScientificV31::Fail() {
    if (opgsl_) {
        GSL_ERROR("OPGSLScientificV31 V3 navigation action failed; run marked failure");
        opgsl_->currentResult = GSLResult::Failure;
    }
}

}  // namespace GSL

