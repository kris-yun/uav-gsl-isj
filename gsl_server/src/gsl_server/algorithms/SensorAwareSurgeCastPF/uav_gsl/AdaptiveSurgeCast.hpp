#pragma once

#include "uav_gsl/Common.hpp"

#include <cmath>
#include <cstdint>
#include <limits>
#include <string>

namespace uav_gsl {

// Intermittency-Adaptive Surge-Cast (IASC)
class AdaptiveSurgeCast {
public:
    enum class Mode { Surge, Cast, Explore };

    struct Config {
        bool input_wind_is_flow_to{true};
        double reliable_hit_probability{0.65};
        double weak_hit_probability{0.35};
        double minimum_wind_speed{0.05};
        double minimum_wind_concentration{0.45};
        double surge_min_step_m{0.5};
        double surge_max_step_m{2.0};
        double cast_min_step_m{0.6};
        double cast_max_step_m{4.0};
        double cast_growth_time_s{12.0};
        double plume_memory_s{25.0};
        int maximum_casts_before_explore{8};
        double explore_step_m{2.5};
        double posterior_spread_reference_m{3.0};
    };

    struct Input {
        double time_s{0.0};
        double hit_probability{0.0};
        double evidence_confidence{0.0};
        double wind_speed{0.0};
        double wind_direction_rad{0.0};
        double wind_concentration{0.0};
        double posterior_spread_m{1.0};
    };

    struct Decision {
        Mode mode{Mode::Explore};
        double heading_rad{0.0};
        double step_m{0.0};
        int cast_index{0};
        std::string reason;
    };

    AdaptiveSurgeCast() : AdaptiveSurgeCast(Config{}) {}

    explicit AdaptiveSurgeCast(const Config& config) : config_(config) {
        validateConfig();
    }

    void reset() {
        initialized_ = false;
        last_time_s_ = 0.0;
        last_reliable_hit_time_s_ = -std::numeric_limits<double>::infinity();
        last_upwind_rad_ = 0.0;
        cast_index_ = 0;
        exploration_index_ = 0;
    }

    Decision decide(const Input& input) {
        validateInput(input);
        if (!initialized_) {
            initialized_ = true;
            last_time_s_ = input.time_s;
        }
        if (input.time_s < last_time_s_) {
            throw std::invalid_argument("policy timestamps must be monotonic");
        }
        last_time_s_ = input.time_s;

        const bool wind_reliable = input.wind_speed >= config_.minimum_wind_speed &&
                                   input.wind_concentration >= config_.minimum_wind_concentration;
        if (wind_reliable) {
            const double flow_to = config_.input_wind_is_flow_to
                                       ? input.wind_direction_rad
                                       : wrapAngle(input.wind_direction_rad + kPi);
            last_upwind_rad_ = wrapAngle(flow_to + kPi);
        }

        if (wind_reliable && input.hit_probability >= config_.reliable_hit_probability) {
            last_reliable_hit_time_s_ = input.time_s;
            cast_index_ = 0;
            const double evidence = clamp(input.hit_probability *
                                              (0.5 + 0.5 * input.evidence_confidence),
                                          0.0,
                                          1.0);
            const double step = config_.surge_min_step_m +
                                evidence * (config_.surge_max_step_m - config_.surge_min_step_m);
            return {Mode::Surge, last_upwind_rad_, step, cast_index_,
                    "reliable bout and coherent wind"};
        }

        const double since_hit = input.time_s - last_reliable_hit_time_s_;
        if (wind_reliable && std::isfinite(since_hit) &&
            since_hit <= config_.plume_memory_s &&
            cast_index_ < config_.maximum_casts_before_explore) {
            const int pair_index = cast_index_ / 2;
            const int side = (cast_index_ % 2 == 0) ? 1 : -1;
            const double growth = clamp(since_hit / config_.cast_growth_time_s, 0.0, 1.0);
            const double spread_factor = clamp(input.posterior_spread_m /
                                                   config_.posterior_spread_reference_m,
                                               0.5,
                                               2.0);
            double step = config_.cast_min_step_m +
                          growth * (config_.cast_max_step_m - config_.cast_min_step_m);
            step *= (1.0 + 0.15 * pair_index) * spread_factor;
            step = clamp(step, config_.cast_min_step_m, config_.cast_max_step_m);
            const double heading = wrapAngle(last_upwind_rad_ + side * kPi / 2.0);
            const int emitted_index = cast_index_;
            ++cast_index_;
            return {Mode::Cast, heading, step, emitted_index,
                    "plume-loss recovery with expanding crosswind search"};
        }

        // Deterministic low-discrepancy exploration: reproducible and scene-independent.
        constexpr double golden_angle = 2.39996322972865332;
        const double heading = wrapAngle(exploration_index_ * golden_angle);
        ++exploration_index_;
        cast_index_ = 0;
        const double uncertainty_factor = clamp(input.posterior_spread_m /
                                                    config_.posterior_spread_reference_m,
                                                0.7,
                                                1.5);
        return {Mode::Explore,
                heading,
                config_.explore_step_m * uncertainty_factor,
                0,
                wind_reliable ? "plume memory expired" : "wind evidence unreliable"};
    }

private:
    Config config_;
    bool initialized_{false};
    double last_time_s_{0.0};
    double last_reliable_hit_time_s_{-std::numeric_limits<double>::infinity()};
    double last_upwind_rad_{0.0};
    int cast_index_{0};
    std::uint64_t exploration_index_{0};

    void validateConfig() const {
        if (!(0.0 <= config_.weak_hit_probability &&
              config_.weak_hit_probability < config_.reliable_hit_probability &&
              config_.reliable_hit_probability <= 1.0)) {
            throw std::invalid_argument("hit-probability thresholds are invalid");
        }
        if (config_.surge_min_step_m <= 0.0 ||
            config_.surge_max_step_m < config_.surge_min_step_m ||
            config_.cast_min_step_m <= 0.0 ||
            config_.cast_max_step_m < config_.cast_min_step_m ||
            config_.explore_step_m <= 0.0 ||
            config_.maximum_casts_before_explore < 1) {
            throw std::invalid_argument("movement configuration is invalid");
        }
    }

    static void validateInput(const Input& input) {
        if (!std::isfinite(input.time_s) || !std::isfinite(input.hit_probability) ||
            !std::isfinite(input.evidence_confidence) || !std::isfinite(input.wind_speed) ||
            !std::isfinite(input.wind_direction_rad) ||
            !std::isfinite(input.wind_concentration) ||
            !std::isfinite(input.posterior_spread_m)) {
            throw std::invalid_argument("policy input must be finite");
        }
    }
};

}  // namespace uav_gsl
