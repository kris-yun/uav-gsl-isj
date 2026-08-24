#pragma once

// OPGSLScientificV31 Core V3 Scientific
// =============================================================================
// One coherent probabilistic chain:
//
//   grouped offline calibration -> monotone Bernoulli observation ensemble
//   -> joint source/model posterior -> exact source information-rate planning
//   -> bootstrap-conservative vertical action decision
//   -> anytime prequential Brier-skill verification against a non-spatial null.
//
// The mathematical core is intentionally kept in this single header so the
// formulas used by ROS, standalone tests, replay tools, and the paper cannot
// silently diverge. OPGSLScientificV31.cpp contains only CSV loading, ROS integration,
// feasible-action construction, tracing, and state-machine glue.
//
// Define OPGSL_CORE_STANDALONE before including this file to compile only the
// mathematical core without ROS 2 dependencies.

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <limits>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace GSL::OPGSLV3 {

constexpr double kPi = 3.141592653589793238462643383279502884;
constexpr double kLogTwo = 0.693147180559945309417232121458176568;
constexpr double kProbabilityEpsilon = 1e-9;

inline double clampProbability(double p) {
    return std::clamp(p, kProbabilityEpsilon, 1.0 - kProbabilityEpsilon);
}

inline double logistic(double x) {
    if (x >= 0.0) {
        const double z = std::exp(-x);
        return 1.0 / (1.0 + z);
    }
    const double z = std::exp(x);
    return z / (1.0 + z);
}

inline double logSumExp(const std::vector<double>& values) {
    if (values.empty()) {
        return -std::numeric_limits<double>::infinity();
    }
    const double maximum = *std::max_element(values.begin(), values.end());
    if (!std::isfinite(maximum)) {
        return maximum;
    }
    double sum = 0.0;
    for (const double value : values) {
        sum += std::exp(value - maximum);
    }
    return maximum + std::log(sum);
}

inline double binaryEntropy(double p) {
    p = clampProbability(p);
    return -p * std::log(p) - (1.0 - p) * std::log(1.0 - p);
}

struct SourcePoint {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

struct ObservationContext {
    double sensor_x = 0.0;
    double sensor_y = 0.0;
    double sensor_z = 0.0;
    // Wind vector points downwind in the map frame.
    double wind_x = 0.0;
    double wind_y = 0.0;
    double wind_z = 0.0;
    double wind_speed = 0.0;
    double concentration = 0.0;
    double detection_threshold = 0.1;
};

// Parameters are not chosen online. They are estimated by grouped maximum
// likelihood from independent calibration runs, with run-level bootstrap.
// Positive attenuation coefficients enforce the physically monotone structure.
struct ObservationModelParameters {
    int model_id = 0;
    bool nominal = false;
    // Prior mass used by the joint source/model posterior. Bootstrap models
    // approximate calibration uncertainty; the central nominal fit is retained
    // for a clean ablation and normally receives zero mass when bootstrap
    // replicates are available.
    double prior_weight = 1.0;

    double isotropic_intercept = -2.0;
    double isotropic_distance_decay = 1.0;

    double wind_intercept = -1.0;
    double downwind_distance_decay = 0.5;
    double upstream_distance_decay = 2.0;
    double crosswind_squared_decay = 0.5;
    double vertical_squared_decay = 0.5;

    // Standard deviation of wind-vector noise in m/s. The reliability
    // u^2/(u^2+sigma_u^2) follows inverse-variance signal/noise weighting.
    double wind_noise_speed_sigma = 0.1;
    // Reliability override: >= 0 => use this value, < 0 => compute from wind speed.
    double reliability_override = -1.0;
};

struct CalibrationMetadata {
    bool scientific_valid = false;
    bool vertical_feature_valid = false;
    int calibration_house_count = 0;
    int calibration_run_count = 0;
    double heldout_brier_skill_ci_low =
        -std::numeric_limits<double>::infinity();
    double vertical_brier_gain_ci_low =
        -std::numeric_limits<double>::infinity();
    std::string calibration_id;
};

class ObservationModelEnsemble {
public:
    void setModels(std::vector<ObservationModelParameters> models,
                   CalibrationMetadata metadata = {}) {
        if (models.empty()) {
            throw std::invalid_argument("Observation model ensemble cannot be empty");
        }
        for (const auto& model : models) {
            validate(model);
        }
        models_ = std::move(models);
        metadata_ = std::move(metadata);
    }

    const std::vector<ObservationModelParameters>& models() const noexcept {
        return models_;
    }
    const CalibrationMetadata& metadata() const noexcept { return metadata_; }
    std::vector<double> normalizedPriorWeights() const {
        if (models_.empty()) {
            return {};
        }
        std::vector<double> weights;
        weights.reserve(models_.size());
        double total = 0.0;
        for (const auto& model : models_) {
            const double weight = std::max(0.0, model.prior_weight);
            weights.push_back(weight);
            total += weight;
        }
        if (!(total > 0.0 && std::isfinite(total))) {
            throw std::invalid_argument(
                "At least one observation model must have positive finite prior weight");
        }
        for (double& weight : weights) {
            weight /= total;
        }
        return weights;
    }
    std::size_t size() const noexcept { return models_.size(); }
    bool empty() const noexcept { return models_.empty(); }

    double hitProbability(std::size_t model_index,
                          const SourcePoint& source,
                          const ObservationContext& observation) const {
        if (model_index >= models_.size()) {
            throw std::out_of_range("Observation model index out of range");
        }
        return hitProbability(models_[model_index], source, observation);
    }

    static double hitProbability(const ObservationModelParameters& model,
                                 const SourcePoint& source,
                                 const ObservationContext& observation) {
        const double dx = observation.sensor_x - source.x;
        const double dy = observation.sensor_y - source.y;
        const double dz = observation.sensor_z - source.z;
        const double horizontal_distance = std::hypot(dx, dy);
        const double distance = std::sqrt(dx * dx + dy * dy + dz * dz);

        // Low-wind model: monotone radial attenuation.
        const double q_isotropic = logistic(
            model.isotropic_intercept -
            model.isotropic_distance_decay * distance);

        double q_wind = q_isotropic;
        const double wind_norm = std::hypot(observation.wind_x,
                                            observation.wind_y);
        if (wind_norm > 1e-12) {
            const double wx = observation.wind_x / wind_norm;
            const double wy = observation.wind_y / wind_norm;
            const double parallel = dx * wx + dy * wy;
            const double downwind = std::max(parallel, 0.0);
            const double upstream = std::max(-parallel, 0.0);
            const double crosswind_squared = std::max(
                0.0,
                horizontal_distance * horizontal_distance -
                    parallel * parallel);

            q_wind = logistic(
                model.wind_intercept -
                model.downwind_distance_decay * downwind -
                model.upstream_distance_decay * upstream -
                model.crosswind_squared_decay * crosswind_squared -
                model.vertical_squared_decay * dz * dz);
        }

        const double u = std::max(0.0, observation.wind_speed);
        const double sigma = std::max(model.wind_noise_speed_sigma, 1e-12);
        const double reliability = (model.reliability_override >= 0.0) ? model.reliability_override : (u * u) / (u * u + sigma * sigma);
        const double q = (1.0 - reliability) * q_isotropic +
                         reliability * q_wind;
        return clampProbability(q);
    }

private:
    std::vector<ObservationModelParameters> models_;
    CalibrationMetadata metadata_;

    static void validate(const ObservationModelParameters& model) {
        const std::array<double, 6> positive = {
            model.isotropic_distance_decay,
            model.downwind_distance_decay,
            model.upstream_distance_decay,
            model.crosswind_squared_decay,
            model.vertical_squared_decay,
            model.wind_noise_speed_sigma};
        for (const double value : positive) {
            if (!(std::isfinite(value) && value > 0.0)) {
                throw std::invalid_argument(
                    "Observation attenuation and noise parameters must be finite and positive");
            }
        }
        if (!(std::isfinite(model.prior_weight) && model.prior_weight >= 0.0)) {
            throw std::invalid_argument("Observation-model prior weight must be finite and nonnegative");
        }
        if (!std::isfinite(model.isotropic_intercept) ||
            !std::isfinite(model.wind_intercept)) {
            throw std::invalid_argument("Observation intercepts must be finite");
        }
    }
};

struct GridSpec {
    int nx = 25;
    int ny = 25;
    int nz = 1;
    double x_min = -5.0;
    double x_max = 5.0;
    double y_min = -5.0;
    double y_max = 5.0;
    double z_min = 0.0;
    double z_max = 0.0;
};

struct PosteriorSummary {
    SourcePoint map;
    SourcePoint mean;
    double entropy = 0.0;
    double variance = 0.0;
    double effective_source_cells = 0.0;
    double credible_radius = std::numeric_limits<double>::infinity();
    double credible_mass = 0.90;
    double map_probability = 0.0;
    std::size_t valid_source_count = 0;
    std::vector<double> model_marginal;
};

struct UpdateDiagnostics {
    bool detected = false;
    double predictive_hit_probability = 0.5;
    double source_brier = 0.25;
    double source_nll = kLogTwo;
    double entropy_before = 0.0;
    double entropy_after = 0.0;
    double normalization_error = 0.0;
};

enum class EvidenceMode {
    ProperJoint,
    NominalOnly,
    LegacySamePolarity,
    HitOnly,
    MissOnly
};

// Approximate Bayesian marginalization of observation-model calibration
// uncertainty. The state is p(source, calibration_model | observations).
class JointSourceModelPosterior {
public:
    void initialize(const GridSpec& spec,
                    std::vector<bool> source_valid_mask,
                    std::vector<double> model_prior_weights) {
        validateSpec(spec);
        if (model_prior_weights.empty()) {
            throw std::invalid_argument("model_prior_weights cannot be empty");
        }
        double prior_sum = 0.0;
        for (const double weight : model_prior_weights) {
            if (!(std::isfinite(weight) && weight >= 0.0)) {
                throw std::invalid_argument(
                    "model prior weights must be finite and nonnegative");
            }
            prior_sum += weight;
        }
        if (!(prior_sum > 0.0 && std::isfinite(prior_sum))) {
            throw std::invalid_argument("model prior weights must have positive mass");
        }
        for (double& weight : model_prior_weights) {
            weight /= prior_sum;
        }
        spec_ = spec;
        model_count_ = model_prior_weights.size();
        model_prior_weights_ = std::move(model_prior_weights);
        dx_ = (spec_.x_max - spec_.x_min) /
              static_cast<double>(spec_.nx);
        dy_ = (spec_.y_max - spec_.y_min) /
              static_cast<double>(spec_.ny);
        dz_ = spec_.nz > 1
            ? (spec_.z_max - spec_.z_min) /
              static_cast<double>(spec_.nz)
            : 0.0;

        const std::size_t full_size = fullSourceCount();
        if (source_valid_mask.empty()) {
            source_valid_mask.assign(full_size, true);
        }
        if (source_valid_mask.size() != full_size) {
            throw std::invalid_argument("source_valid_mask size mismatch");
        }
        source_valid_mask_ = std::move(source_valid_mask);
        valid_full_indices_.clear();
        for (std::size_t i = 0; i < source_valid_mask_.size(); ++i) {
            if (source_valid_mask_[i]) {
                valid_full_indices_.push_back(i);
            }
        }
        if (valid_full_indices_.empty()) {
            throw std::invalid_argument("Source mask contains no valid cells");
        }

        log_joint_.assign(
            valid_full_indices_.size() * model_count_,
            -std::numeric_limits<double>::infinity());
        const double source_log_prior =
            -std::log(static_cast<double>(valid_full_indices_.size()));
        for (std::size_t s = 0; s < valid_full_indices_.size(); ++s) {
            for (std::size_t m = 0; m < model_count_; ++m) {
                if (model_prior_weights_[m] > 0.0) {
                    log_joint_[jointIndex(s, m)] = source_log_prior +
                        std::log(model_prior_weights_[m]);
                }
            }
        }
        initialized_ = true;
    }

    bool initialized() const noexcept { return initialized_; }
    std::size_t validSourceCount() const noexcept {
        return valid_full_indices_.size();
    }
    std::size_t modelCount() const noexcept { return model_count_; }
    const GridSpec& spec() const noexcept { return spec_; }

    SourcePoint sourceAtValidIndex(std::size_t valid_index) const {
        requireInitialized();
        if (valid_index >= valid_full_indices_.size()) {
            throw std::out_of_range("valid source index out of range");
        }
        return sourceAtFullIndex(valid_full_indices_[valid_index]);
    }

    std::vector<double> sourceMarginal() const {
        requireInitialized();
        std::vector<double> p(validSourceCount(), 0.0);
        for (std::size_t s = 0; s < validSourceCount(); ++s) {
            for (std::size_t m = 0; m < model_count_; ++m) {
                p[s] += std::exp(log_joint_[jointIndex(s, m)]);
            }
        }
        return p;
    }

    std::vector<double> modelMarginal() const {
        requireInitialized();
        std::vector<double> p(model_count_, 0.0);
        for (std::size_t m = 0; m < model_count_; ++m) {
            for (std::size_t s = 0; s < validSourceCount(); ++s) {
                p[m] += std::exp(log_joint_[jointIndex(s, m)]);
            }
        }
        return p;
    }

    double predictiveHitProbability(
        const ObservationContext& observation,
        const ObservationModelEnsemble& ensemble) const {
        requireCompatible(ensemble);
        double predictive = 0.0;
        for (std::size_t s = 0; s < validSourceCount(); ++s) {
            const SourcePoint source = sourceAtValidIndex(s);
            for (std::size_t m = 0; m < model_count_; ++m) {
                predictive += std::exp(log_joint_[jointIndex(s, m)]) *
                    ensemble.hitProbability(m, source, observation);
            }
        }
        return clampProbability(predictive);
    }

    UpdateDiagnostics update(const ObservationContext& observation,
                             const ObservationModelEnsemble& ensemble,
                             EvidenceMode mode = EvidenceMode::ProperJoint) {
        requireCompatible(ensemble);
        UpdateDiagnostics diagnostics;
        diagnostics.detected =
            observation.concentration > observation.detection_threshold;
        diagnostics.predictive_hit_probability =
            predictiveHitProbability(observation, ensemble);
        const double y = diagnostics.detected ? 1.0 : 0.0;
        diagnostics.source_brier = std::pow(
            y - diagnostics.predictive_hit_probability, 2.0);
        diagnostics.source_nll = diagnostics.detected
            ? -std::log(diagnostics.predictive_hit_probability)
            : -std::log(1.0 - diagnostics.predictive_hit_probability);
        diagnostics.entropy_before = summary().entropy;

        for (std::size_t s = 0; s < validSourceCount(); ++s) {
            const SourcePoint source = sourceAtValidIndex(s);
            for (std::size_t m = 0; m < model_count_; ++m) {
                double increment = 0.0;
                const double q = ensemble.hitProbability(m, source, observation);
                switch (mode) {
                    case EvidenceMode::ProperJoint:
                        increment = diagnostics.detected
                            ? std::log(q)
                            : std::log(1.0 - q);
                        break;
                    case EvidenceMode::NominalOnly:
                        if (m == 0) {
                            increment = diagnostics.detected
                                ? std::log(q)
                                : std::log(1.0 - q);
                        } else {
                            log_joint_[jointIndex(s, m)] =
                                -std::numeric_limits<double>::infinity();
                            continue;
                        }
                        break;
                    case EvidenceMode::LegacySamePolarity:
                        increment = (diagnostics.detected ? 1.0 : 0.3) *
                                    std::log(q);
                        break;
                    case EvidenceMode::HitOnly:
                        increment = diagnostics.detected ? std::log(q) : 0.0;
                        break;
                    case EvidenceMode::MissOnly:
                        increment = diagnostics.detected ? 0.0 :
                                    std::log(1.0 - q);
                        break;
                }
                log_joint_[jointIndex(s, m)] += increment;
            }
        }
        normalize();
        diagnostics.entropy_after = summary().entropy;
        double total = 0.0;
        for (const double lp : log_joint_) {
            total += std::exp(lp);
        }
        diagnostics.normalization_error = std::abs(total - 1.0);
        return diagnostics;
    }

    // Mutual information I(S;E|a,D), with calibration-model uncertainty
    // marginalized conditionally on each source.
    double expectedSourceInformationGain(
        const ObservationContext& action,
        const ObservationModelEnsemble& ensemble) const {
        requireCompatible(ensemble);
        const std::vector<double> p_source = sourceMarginal();
        double marginal_q = 0.0;
        double conditional_entropy = 0.0;
        for (std::size_t s = 0; s < validSourceCount(); ++s) {
            if (p_source[s] <= 0.0) {
                continue;
            }
            const SourcePoint source = sourceAtValidIndex(s);
            double q_given_source = 0.0;
            for (std::size_t m = 0; m < model_count_; ++m) {
                const double joint = std::exp(log_joint_[jointIndex(s, m)]);
                const double model_given_source = joint / p_source[s];
                q_given_source += model_given_source *
                    ensemble.hitProbability(m, source, action);
            }
            q_given_source = clampProbability(q_given_source);
            marginal_q += p_source[s] * q_given_source;
            conditional_entropy += p_source[s] *
                                   binaryEntropy(q_given_source);
        }
        return std::clamp(
            binaryEntropy(marginal_q) - conditional_entropy,
            0.0,
            kLogTwo);
    }

    // Information gain conditioned on a calibration-model sample. Used only
    // for the paired conservative vertical-action test.
    double expectedSourceInformationGainForModel(
        std::size_t model_index,
        const ObservationContext& action,
        const ObservationModelEnsemble& ensemble) const {
        requireCompatible(ensemble);
        if (model_index >= model_count_) {
            throw std::out_of_range("model index out of range");
        }
        const std::vector<double> p_model = modelMarginal();
        if (p_model[model_index] <= 0.0) {
            return 0.0;
        }
        double marginal_q = 0.0;
        double conditional_entropy = 0.0;
        for (std::size_t s = 0; s < validSourceCount(); ++s) {
            const double p_source_given_model =
                std::exp(log_joint_[jointIndex(s, model_index)]) /
                p_model[model_index];
            if (p_source_given_model <= 0.0) {
                continue;
            }
            const double q = ensemble.hitProbability(
                model_index, sourceAtValidIndex(s), action);
            marginal_q += p_source_given_model * q;
            conditional_entropy += p_source_given_model * binaryEntropy(q);
        }
        return std::clamp(
            binaryEntropy(marginal_q) - conditional_entropy,
            0.0,
            kLogTwo);
    }

    PosteriorSummary summary(double credible_mass = 0.90) const {
        requireInitialized();
        if (!(credible_mass > 0.0 && credible_mass < 1.0)) {
            throw std::invalid_argument("credible_mass must lie in (0,1)");
        }
        PosteriorSummary result;
        result.credible_mass = credible_mass;
        result.valid_source_count = validSourceCount();
        result.model_marginal = modelMarginal();
        const std::vector<double> p = sourceMarginal();

        std::size_t map_index = 0;
        double max_p = -1.0;
        double sum_sq = 0.0;
        for (std::size_t s = 0; s < validSourceCount(); ++s) {
            const SourcePoint point = sourceAtValidIndex(s);
            result.mean.x += p[s] * point.x;
            result.mean.y += p[s] * point.y;
            result.mean.z += p[s] * point.z;
            if (p[s] > 0.0) {
                result.entropy -= p[s] * std::log(p[s]);
            }
            sum_sq += p[s] * p[s];
            if (p[s] > max_p) {
                max_p = p[s];
                map_index = s;
            }
        }
        result.map = sourceAtValidIndex(map_index);
        result.map_probability = max_p;
        result.effective_source_cells = sum_sq > 0.0 ? 1.0 / sum_sq : 0.0;

        std::vector<std::pair<double, double>> radius_mass;
        radius_mass.reserve(validSourceCount());
        for (std::size_t s = 0; s < validSourceCount(); ++s) {
            const SourcePoint point = sourceAtValidIndex(s);
            const double dx = point.x - result.mean.x;
            const double dy = point.y - result.mean.y;
            const double dz = point.z - result.mean.z;
            const double squared = dx * dx + dy * dy + dz * dz;
            result.variance += p[s] * squared;
            radius_mass.emplace_back(std::sqrt(squared), p[s]);
        }
        std::sort(radius_mass.begin(), radius_mass.end());
        double cumulative = 0.0;
        for (const auto& [radius, mass] : radius_mass) {
            cumulative += mass;
            if (cumulative >= credible_mass) {
                result.credible_radius = radius;
                break;
            }
        }
        return result;
    }

    const std::vector<double>& logJoint() const noexcept { return log_joint_; }

private:
    GridSpec spec_;
    double dx_ = 0.0;
    double dy_ = 0.0;
    double dz_ = 0.0;
    std::size_t model_count_ = 0;
    std::vector<bool> source_valid_mask_;
    std::vector<std::size_t> valid_full_indices_;
    std::vector<double> log_joint_;
    std::vector<double> model_prior_weights_;
    bool initialized_ = false;

    std::size_t fullSourceCount() const {
        return static_cast<std::size_t>(spec_.nx) *
               static_cast<std::size_t>(spec_.ny) *
               static_cast<std::size_t>(spec_.nz);
    }

    std::size_t jointIndex(std::size_t source_index,
                           std::size_t model_index) const {
        return source_index * model_count_ + model_index;
    }

    SourcePoint sourceAtFullIndex(std::size_t index) const {
        const std::size_t plane = static_cast<std::size_t>(spec_.ny) *
                                  static_cast<std::size_t>(spec_.nz);
        const int i = static_cast<int>(index / plane);
        const std::size_t remainder = index % plane;
        const int j = static_cast<int>(remainder /
                                       static_cast<std::size_t>(spec_.nz));
        const int k = static_cast<int>(remainder %
                                       static_cast<std::size_t>(spec_.nz));
        SourcePoint source;
        source.x = spec_.x_min + (static_cast<double>(i) + 0.5) * dx_;
        source.y = spec_.y_min + (static_cast<double>(j) + 0.5) * dy_;
        source.z = spec_.nz > 1
            ? spec_.z_min + (static_cast<double>(k) + 0.5) * dz_
            : 0.5 * (spec_.z_min + spec_.z_max);
        return source;
    }

    void normalize() {
        const double normalizer = logSumExp(log_joint_);
        if (!std::isfinite(normalizer)) {
            throw std::runtime_error("Joint posterior normalization failed");
        }
        for (double& lp : log_joint_) {
            lp -= normalizer;
        }
    }

    void requireInitialized() const {
        if (!initialized_) {
            throw std::logic_error("JointSourceModelPosterior not initialized");
        }
    }

    void requireCompatible(const ObservationModelEnsemble& ensemble) const {
        requireInitialized();
        if (ensemble.size() != model_count_) {
            throw std::invalid_argument(
                "Observation model count does not match posterior model dimension");
        }
    }

    static void validateSpec(const GridSpec& spec) {
        if (spec.nx <= 0 || spec.ny <= 0 || spec.nz <= 0 ||
            !(spec.x_max > spec.x_min) ||
            !(spec.y_max > spec.y_min) ||
            (spec.nz > 1 && !(spec.z_max > spec.z_min))) {
            throw std::invalid_argument("Invalid source grid specification");
        }
    }
};

enum class ActionType {
    PlanarTraverse,
    VerticalProbe,
    ElevatedTraverse
};

inline const char* actionTypeName(ActionType type) {
    switch (type) {
        case ActionType::PlanarTraverse: return "planar_traverse";
        case ActionType::VerticalProbe: return "vertical_probe";
        case ActionType::ElevatedTraverse: return "elevated_traverse";
    }
    return "unknown";
}

struct FeasibleAction {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    ActionType type = ActionType::PlanarTraverse;
    int visit_count = 0;
};

struct ActionScore {
    FeasibleAction action;
    double horizontal_distance = 0.0;
    double vertical_distance = 0.0;
    double cycle_time_seconds = std::numeric_limits<double>::infinity();
    double expected_information_nats = 0.0;
    double expected_information_bits = 0.0;
    double information_rate_bits_per_second = 0.0;
    std::vector<double> model_information_rates;
};

struct PlannerConfig {
    double horizontal_speed_mps = 0.4;
    double vertical_speed_mps = 0.2;
    double measurement_dwell_seconds = 2.0;
    bool vertical_actions_requested = false;
    bool conservative_vertical_gate = true;
    double vertical_posterior_quantile = 0.05;
};

struct PlannerDecision {
    std::vector<ActionScore> ranked;
    std::optional<ActionScore> best_planar;
    std::optional<ActionScore> best_vertical;
    std::optional<ActionScore> selected;
    bool vertical_model_valid = false;
    bool vertical_gate_open = false;
    double vertical_rate_difference_lower_quantile =
        -std::numeric_limits<double>::infinity();
    std::string reason = "no_feasible_action";
};

class InformationRatePlanner {
public:
    explicit InformationRatePlanner(PlannerConfig config = {})
        : config_(config) {
        validateConfig();
    }

    void setConfig(const PlannerConfig& config) {
        config_ = config;
        validateConfig();
    }
    const PlannerConfig& config() const noexcept { return config_; }

    ActionScore score(const FeasibleAction& action,
                      double current_x,
                      double current_y,
                      double current_z,
                      const ObservationContext& current_context,
                      const JointSourceModelPosterior& posterior,
                      const ObservationModelEnsemble& ensemble) const {
        ActionScore score;
        score.action = action;
        score.horizontal_distance = std::hypot(
            action.x - current_x, action.y - current_y);
        score.vertical_distance = std::abs(action.z - current_z);
        score.cycle_time_seconds =
            score.horizontal_distance / config_.horizontal_speed_mps +
            score.vertical_distance / config_.vertical_speed_mps +
            config_.measurement_dwell_seconds;
        if (!(score.cycle_time_seconds > 0.0 &&
              std::isfinite(score.cycle_time_seconds))) {
            throw std::runtime_error("Non-positive action cycle time");
        }

        ObservationContext action_context = current_context;
        action_context.sensor_x = action.x;
        action_context.sensor_y = action.y;
        action_context.sensor_z = action.z;
        action_context.concentration = 0.0;

        score.expected_information_nats =
            posterior.expectedSourceInformationGain(action_context, ensemble);
        score.expected_information_bits =
            score.expected_information_nats / kLogTwo;
        score.information_rate_bits_per_second =
            score.expected_information_bits / score.cycle_time_seconds;

        score.model_information_rates.resize(ensemble.size(), 0.0);
        for (std::size_t m = 0; m < ensemble.size(); ++m) {
            const double info = posterior.expectedSourceInformationGainForModel(
                m, action_context, ensemble) / kLogTwo;
            score.model_information_rates[m] = info / score.cycle_time_seconds;
        }
        return score;
    }

    PlannerDecision choose(const std::vector<FeasibleAction>& feasible_actions,
                           double current_x,
                           double current_y,
                           double current_z,
                           const ObservationContext& current_context,
                           const JointSourceModelPosterior& posterior,
                           const ObservationModelEnsemble& ensemble) const {
        PlannerDecision decision;
        decision.vertical_model_valid =
            ensemble.metadata().vertical_feature_valid;
        if (feasible_actions.empty()) {
            return decision;
        }

        for (const auto& action : feasible_actions) {
            decision.ranked.push_back(score(
                action, current_x, current_y, current_z,
                current_context, posterior, ensemble));
        }
        std::stable_sort(decision.ranked.begin(), decision.ranked.end(),
            [](const ActionScore& lhs, const ActionScore& rhs) {
                const double scale = std::max({
                    1.0,
                    std::abs(lhs.information_rate_bits_per_second),
                    std::abs(rhs.information_rate_bits_per_second)});
                const double tolerance =
                    64.0 * std::numeric_limits<double>::epsilon() * scale;
                const double difference =
                    lhs.information_rate_bits_per_second -
                    rhs.information_rate_bits_per_second;
                if (std::abs(difference) > tolerance) {
                    return difference > 0.0;
                }
                if (lhs.action.visit_count != rhs.action.visit_count) {
                    return lhs.action.visit_count < rhs.action.visit_count;
                }
                return lhs.cycle_time_seconds < rhs.cycle_time_seconds;
            });

        for (const auto& candidate : decision.ranked) {
            const bool vertical = std::abs(candidate.action.z - current_z) > 1e-9;
            if (!vertical && !decision.best_planar.has_value()) {
                decision.best_planar = candidate;
            }
            if (vertical && !decision.best_vertical.has_value()) {
                decision.best_vertical = candidate;
            }
        }

        if (!decision.best_planar.has_value() &&
            !decision.best_vertical.has_value()) {
            return decision;
        }
        if (!decision.best_planar.has_value()) {
            decision.selected = decision.best_vertical;
            decision.reason = "vertical_only_feasible";
            decision.vertical_gate_open = true;
            return decision;
        }
        if (!config_.vertical_actions_requested ||
            !decision.best_vertical.has_value()) {
            decision.selected = decision.best_planar;
            decision.reason = config_.vertical_actions_requested
                ? "no_feasible_vertical_action"
                : "vertical_actions_disabled";
            return decision;
        }
        if (!decision.vertical_model_valid) {
            decision.selected = decision.best_planar;
            decision.reason = "vertical_model_not_validated";
            return decision;
        }
        if (!config_.conservative_vertical_gate) {
            decision.selected = decision.ranked.front();
            decision.vertical_gate_open =
                std::abs(decision.selected->action.z - current_z) > 1e-9;
            decision.reason = "mean_information_rate_ablation";
            return decision;
        }

        const std::vector<double> model_weights = posterior.modelMarginal();
        std::vector<std::pair<double, double>> weighted_differences;
        weighted_differences.reserve(ensemble.size());
        for (std::size_t m = 0; m < ensemble.size(); ++m) {
            const double difference =
                decision.best_vertical->model_information_rates[m] -
                decision.best_planar->model_information_rates[m];
            weighted_differences.emplace_back(difference, model_weights[m]);
        }
        decision.vertical_rate_difference_lower_quantile = weightedQuantile(
            weighted_differences, config_.vertical_posterior_quantile);
        decision.vertical_gate_open =
            decision.vertical_rate_difference_lower_quantile > 0.0;
        decision.selected = decision.vertical_gate_open
            ? decision.best_vertical
            : decision.best_planar;
        decision.reason = decision.vertical_gate_open
            ? "vertical_rate_advantage_supported"
            : "vertical_rate_advantage_not_supported";
        return decision;
    }

private:
    PlannerConfig config_;

    static double weightedQuantile(
        std::vector<std::pair<double, double>> values,
        double quantile) {
        if (values.empty()) {
            return -std::numeric_limits<double>::infinity();
        }
        std::sort(values.begin(), values.end(),
                  [](const auto& lhs, const auto& rhs) {
                      return lhs.first < rhs.first;
                  });
        double total_weight = 0.0;
        for (const auto& item : values) {
            total_weight += std::max(0.0, item.second);
        }
        if (total_weight <= 0.0) {
            return values.front().first;
        }
        const double target = std::clamp(quantile, 0.0, 1.0) * total_weight;
        double cumulative = 0.0;
        for (const auto& item : values) {
            cumulative += std::max(0.0, item.second);
            if (cumulative >= target) {
                return item.first;
            }
        }
        return values.back().first;
    }

    void validateConfig() const {
        if (!(config_.horizontal_speed_mps > 0.0) ||
            !(config_.vertical_speed_mps > 0.0) ||
            !(config_.measurement_dwell_seconds >= 0.0) ||
            !(config_.vertical_posterior_quantile > 0.0 &&
              config_.vertical_posterior_quantile < 0.5)) {
            throw std::invalid_argument("Invalid information-rate planner configuration");
        }
    }
};

struct VerificationConfig {
    // Application-level accuracy target, not a fitted statistical parameter.
    double target_credible_radius_m = 1.5;
    double credible_mass = 0.90;
    // Family-wise error budget for the anytime skill test.
    double alpha = 0.05;
    // Jeffreys prior for the non-spatial hit-rate null predictor.
    double null_prior_hit = 0.5;
    double null_prior_miss = 0.5;
};

struct VerificationStatus {
    bool posterior_concentrated = false;
    bool skill_positive = false;
    bool verified = false;
    int count = 0;
    int hits = 0;
    int misses = 0;
    double source_prediction = 0.5;
    double null_prediction = 0.5;
    double mean_brier_skill = 0.0;
    double brier_skill_lcb = -std::numeric_limits<double>::infinity();
    double cumulative_source_nll = 0.0;
    double cumulative_null_nll = 0.0;
    double credible_radius = std::numeric_limits<double>::infinity();
    std::string reason = "insufficient_predictive_evidence";
};

// Anytime test of whether the spatial source model predicts binary gas events
// better than a non-spatial Beta-Bernoulli hit-rate predictor. The Brier-skill
// increment lies in [-1,1]. Hoeffding-Azuma plus alpha-spending
// delta_n=6*alpha/(pi^2*n^2) yields a time-uniform lower confidence bound on
// the average conditional Brier skill.
class PrequentialSkillVerifier {
public:
    explicit PrequentialSkillVerifier(VerificationConfig config = {})
        : config_(config) {
        validateConfig();
    }

    void setConfig(const VerificationConfig& config) {
        config_ = config;
        validateConfig();
    }
    const VerificationConfig& config() const noexcept { return config_; }

    void reset() {
        count_ = 0;
        hits_ = 0;
        misses_ = 0;
        skill_sum_ = 0.0;
        source_nll_sum_ = 0.0;
        null_nll_sum_ = 0.0;
        last_source_prediction_ = 0.5;
        last_null_prediction_ = 0.5;
    }

    void observeBeforePosteriorUpdate(double source_prediction,
                                      bool detected) {
        last_source_prediction_ = clampProbability(source_prediction);
        last_null_prediction_ = clampProbability(
            (static_cast<double>(hits_) + config_.null_prior_hit) /
            (static_cast<double>(count_) +
             config_.null_prior_hit + config_.null_prior_miss));
        const double y = detected ? 1.0 : 0.0;
        const double source_brier = std::pow(y - last_source_prediction_, 2.0);
        const double null_brier = std::pow(y - last_null_prediction_, 2.0);
        skill_sum_ += null_brier - source_brier;

        source_nll_sum_ += detected
            ? -std::log(last_source_prediction_)
            : -std::log(1.0 - last_source_prediction_);
        null_nll_sum_ += detected
            ? -std::log(last_null_prediction_)
            : -std::log(1.0 - last_null_prediction_);

        ++count_;
        detected ? ++hits_ : ++misses_;
    }

    VerificationStatus evaluate(const PosteriorSummary& posterior) const {
        VerificationStatus status;
        status.count = count_;
        status.hits = hits_;
        status.misses = misses_;
        status.source_prediction = last_source_prediction_;
        status.null_prediction = last_null_prediction_;
        status.cumulative_source_nll = source_nll_sum_;
        status.cumulative_null_nll = null_nll_sum_;
        status.credible_radius = posterior.credible_radius;
        status.posterior_concentrated =
            posterior.credible_radius <= config_.target_credible_radius_m;

        if (count_ > 0) {
            status.mean_brier_skill = skill_sum_ /
                static_cast<double>(count_);
            const double n = static_cast<double>(count_);
            const double delta_n =
                6.0 * config_.alpha /
                (kPi * kPi * n * n);
            const double radius = std::sqrt(
                2.0 * std::log(1.0 / delta_n) / n);
            status.brier_skill_lcb = status.mean_brier_skill - radius;
            status.skill_positive = status.brier_skill_lcb > 0.0;
        }
        status.verified = status.posterior_concentrated &&
                          status.skill_positive;
        if (status.verified) {
            status.reason = "verified_spatial_skill_and_concentration";
        } else if (!status.posterior_concentrated) {
            status.reason = "posterior_not_concentrated";
        } else if (count_ == 0) {
            status.reason = "insufficient_predictive_evidence";
        } else {
            status.reason = "spatial_model_not_better_than_null";
        }
        return status;
    }

private:
    VerificationConfig config_;
    int count_ = 0;
    int hits_ = 0;
    int misses_ = 0;
    double skill_sum_ = 0.0;
    double source_nll_sum_ = 0.0;
    double null_nll_sum_ = 0.0;
    double last_source_prediction_ = 0.5;
    double last_null_prediction_ = 0.5;

    void validateConfig() const {
        if (!(config_.target_credible_radius_m > 0.0) ||
            !(config_.credible_mass > 0.0 && config_.credible_mass < 1.0) ||
            !(config_.alpha > 0.0 && config_.alpha < 0.5) ||
            !(config_.null_prior_hit > 0.0) ||
            !(config_.null_prior_miss > 0.0)) {
            throw std::invalid_argument("Invalid prequential verification configuration");
        }
    }
};

}  // namespace GSL::OPGSLV3

#ifndef OPGSL_CORE_STANDALONE

#include <gsl_server/algorithms/Common/Algorithm.hpp>
#include <gsl_server/algorithms/Common/States/MovingState.hpp>

#include <fstream>
#include <memory>
#include <random>
#include <unordered_map>

namespace GSL {

class OPGSLScientificV31;

class MovingStateOPGSLScientificV31 final : public MovingState {
public:
    explicit MovingStateOPGSLScientificV31(Algorithm* algorithm);
    void chooseGoalAndMove() override;

protected:
    void Fail() override;

private:
    OPGSLScientificV31* opgsl_ = nullptr;
    NavigateToPose::Goal posToGoal(double x, double y, double z) const;
};

class OPGSLScientificV31 final : public Algorithm {
    friend class MovingStateOPGSLScientificV31;

public:
    explicit OPGSLScientificV31(std::shared_ptr<rclcpp::Node> node);
    void Initialize() override;

protected:
    void declareParameters() override;
    void processGasAndWindMeasurements(double concentration,
                                       double windSpeed,
                                       double windDirection) override;
    GSLResult checkSourceFound() override;
    void saveResultsToFile(GSLResult result) override;
    void OnUpdate() override;
    void OnCompleteNavigation(GSLResult result, State* previousState) override;
    void onGetMap(const OccupancyGrid::SharedPtr msg) override;

private:
    struct RuntimeConfig {
        bool scientific_mode = true;
        std::string calibration_file;
        int grid_nx = 30;
        int grid_ny = 30;
        int grid_nz = 1;
        double source_z_min = 0.0;
        double source_z_max = 0.0;
        double nominal_flight_height = 0.3;
        double min_flight_height = 0.3;
        double max_flight_height = 0.3;
        double max_vertical_step = 0.3;
        int angular_samples = 16;
        int radial_samples = 2;
        double min_action_radius = 0.6;
        double max_action_radius = 1.8;
        bool include_vertical_probe = true;
        bool include_elevated_traverse = true;
        int vertical_samples_each_direction = 1;
        int max_steps = 300;
        int seed = 0;
        OPGSLV3::EvidenceMode evidence_mode =
            OPGSLV3::EvidenceMode::ProperJoint;
        bool use_skill_verifier = true;
        bool radius_only_stop_ablation = false;
    };

    RuntimeConfig runtime_config_;
    OPGSLV3::PlannerConfig planner_config_;
    OPGSLV3::VerificationConfig verification_config_;
    OPGSLV3::ObservationModelEnsemble observation_models_;
    OPGSLV3::JointSourceModelPosterior posterior_;
    OPGSLV3::InformationRatePlanner planner_;
    OPGSLV3::PrequentialSkillVerifier verifier_;

    bool map_received_ = false;
    bool posterior_initialized_ = false;
    bool source_declared_ = false;
    bool scientific_trace_valid_ = false;
    bool stop_trace_written_ = false;
    int step_count_ = 0;
    int measurement_count_ = 0;
    int hit_count_ = 0;
    int miss_count_ = 0;
    double elapsed_time_ = 0.0;
    double latest_concentration_ = 0.0;
    double latest_wind_speed_ = 0.0;
    double latest_wind_x_ = 0.0;
    double latest_wind_y_ = 0.0;

    OPGSLV3::UpdateDiagnostics last_update_diagnostics_;
    OPGSLV3::VerificationStatus last_verification_status_;
    OPGSLV3::PlannerDecision last_planner_decision_;

    std::mt19937 rng_;
    std::unordered_map<std::int64_t, int> visit_counts_;

    std::string run_uuid_;
    std::string source_estimate_trace_file_;
    std::string evidence_trace_file_;
    std::string planner_trace_file_;
    std::string stop_trace_file_;
    std::string parameter_snapshot_file_;
    std::ofstream source_estimate_stream_;
    std::ofstream evidence_stream_;
    std::ofstream planner_stream_;
    std::ofstream stop_stream_;

    void loadCalibrationArtifact();
    void initializePosteriorFromMap();
    std::vector<bool> buildSourceValidityMask(
        const OPGSLV3::GridSpec& spec);
    OPGSLV3::ObservationContext makeObservationContext(
        double sensor_x,
        double sensor_y,
        double sensor_z,
        double concentration) const;

    std::vector<OPGSLV3::FeasibleAction> generateMapFeasibleActions();
    OPGSLV3::PlannerDecision planFeasibleActions(
        const std::vector<OPGSLV3::FeasibleAction>& actions) const;
    int visitCount(double x, double y, double z) const;
    void markVisited(double x, double y, double z);
    std::int64_t visitKey(double x, double y, double z) const;

    double clipToFlightBounds(double z) const;
    void initializeTraceFiles();
    void writeParameterSnapshot() const;
    void writeEvidenceTrace(const OPGSLV3::PosteriorSummary& summary);
    void writeSourceEstimateTrace(const OPGSLV3::PosteriorSummary& summary);
    void writePlannerTrace(const OPGSLV3::ActionScore& score,
                           bool selected,
                           int rank,
                           const OPGSLV3::PlannerDecision& decision);
    void writeStopTrace(const OPGSLV3::PosteriorSummary& summary,
                        const std::string& decision,
                        GSLResult result);

    static OPGSLV3::EvidenceMode parseEvidenceMode(const std::string& mode);
    static std::string evidenceModeName(OPGSLV3::EvidenceMode mode);
};

}  // namespace GSL

#endif  // OPGSL_CORE_STANDALONE

