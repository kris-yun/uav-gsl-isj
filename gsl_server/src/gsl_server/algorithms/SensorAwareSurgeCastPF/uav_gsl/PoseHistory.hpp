#pragma once

#include "uav_gsl/Common.hpp"

#include <deque>
#include <stdexcept>

namespace uav_gsl {

class PoseHistory {
public:
    struct Sample {
        double time_s{0.0};
        Vec2 position{};
    };

    explicit PoseHistory(double horizon_s = 15.0) : horizon_s_(horizon_s) {
        if (horizon_s_ <= 0.0) throw std::invalid_argument("pose-history horizon must be positive");
    }

    void clear() { samples_.clear(); }

    void push(double time_s, const Vec2& position) {
        if (!std::isfinite(time_s) || !finite(position)) {
            throw std::invalid_argument("pose history requires finite samples");
        }
        if (!samples_.empty() && time_s < samples_.back().time_s) {
            throw std::invalid_argument("pose-history timestamps must be monotonic");
        }
        samples_.push_back({time_s, position});
        while (!samples_.empty() && time_s - samples_.front().time_s > horizon_s_) {
            samples_.pop_front();
        }
    }

    Vec2 interpolate(double query_time_s) const {
        if (samples_.empty()) throw std::runtime_error("pose history is empty");
        if (query_time_s <= samples_.front().time_s) return samples_.front().position;
        if (query_time_s >= samples_.back().time_s) return samples_.back().position;
        for (std::size_t i = 1; i < samples_.size(); ++i) {
            if (samples_[i].time_s >= query_time_s) {
                const auto& a = samples_[i - 1];
                const auto& b = samples_[i];
                const double span = b.time_s - a.time_s;
                if (span <= 1e-12) return b.position;
                const double ratio = (query_time_s - a.time_s) / span;
                return a.position * (1.0 - ratio) + b.position * ratio;
            }
        }
        return samples_.back().position;
    }

    Vec2 delayCompensated(double measurement_time_s, double delay_s) const {
        return interpolate(measurement_time_s - std::max(0.0, delay_s));
    }

private:
    double horizon_s_;
    std::deque<Sample> samples_;
};

}  // namespace uav_gsl
