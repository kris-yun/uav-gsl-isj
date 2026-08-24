// LegacyM1ObservationModel implementation
// Bit-identical to ObservationModelEnsemble::hitProbability() in OPGSLScientificV31.hpp:182-221.

#include "LegacyM1ObservationModel.hpp"
#include <OPGSLScientificV31.hpp>  // for ObservationModelParameters, SourcePoint, ObservationContext
#include <cmath>
#include <sstream>
#include <iomanip>

namespace GSL::OPGSLV3 {

static double logistic(double x) {
    if (x >= 0.0) {
        const double z = std::exp(-x);
        return 1.0 / (1.0 + z);
    }
    const double z = std::exp(x);
    return z / (1.0 + z);
}

ObservationPrediction LegacyM1ObservationModel::predict(
    const SourcePoint& source,
    const ObservationContext& observation) const {

    // Reproduce OPGSLScientificV31.hpp:182-221 exactly.
    const double dx = observation.sensor_x - source.x;
    const double dy = observation.sensor_y - source.y;
    const double dz = observation.sensor_z - source.z;
    const double horizontal_distance = std::hypot(dx, dy);
    const double distance = std::sqrt(dx * dx + dy * dy + dz * dz);

    // Low-wind model: monotone radial attenuation.
    const double q_isotropic = logistic(
        params_.isotropic_intercept -
        params_.isotropic_distance_decay * distance);

    double q_wind = q_isotropic;
    const double wind_norm = std::hypot(observation.wind_x, observation.wind_y);
    if (wind_norm > 1e-12) {
        const double wx = observation.wind_x / wind_norm;
        const double wy = observation.wind_y / wind_norm;
        const double parallel = dx * wx + dy * wy;
        const double downwind = std::max(parallel, 0.0);
        const double upstream = std::max(-parallel, 0.0);
        const double crosswind_squared = std::max(
            0.0,
            horizontal_distance * horizontal_distance - parallel * parallel);

        q_wind = logistic(
            params_.wind_intercept -
            params_.downwind_distance_decay * downwind -
            params_.upstream_distance_decay * upstream -
            params_.crosswind_squared_decay * crosswind_squared -
            params_.vertical_squared_decay * dz * dz);
    }

    const double u = std::max(0.0, observation.wind_speed);
    const double sigma = std::max(params_.wind_noise_speed_sigma, 1e-12);
    const double reliability = (u * u) / (u * u + sigma * sigma);
    const double q = (1.0 - reliability) * q_isotropic + reliability * q_wind;

    // Clamp to same epsilon as original
    constexpr double kEps = 1e-9;
    const double q_clamped = std::clamp(q, kEps, 1.0 - kEps);

    ObservationPrediction pred;
    pred.q = q_clamped;
    pred.model_name = "LegacyM1";
    pred.model_hash = hash();
    return pred;
}

std::string LegacyM1ObservationModel::hash() const {
    // Stable hash from parameter values
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(6)
        << params_.isotropic_intercept << "|"
        << params_.isotropic_distance_decay << "|"
        << params_.wind_intercept << "|"
        << params_.downwind_distance_decay << "|"
        << params_.upstream_distance_decay << "|"
        << params_.crosswind_squared_decay << "|"
        << params_.vertical_squared_decay << "|"
        << params_.wind_noise_speed_sigma;
    // Simple FNV-1a hash
    std::uint64_t h = 14695981039346656037ULL;
    for (char c : oss.str()) {
        h ^= static_cast<std::uint64_t>(c);
        h *= 1099511628211ULL;
    }
    std::ostringstream result;
    result << std::hex << h;
    return result.str();
}

}  // namespace GSL::OPGSLV3
