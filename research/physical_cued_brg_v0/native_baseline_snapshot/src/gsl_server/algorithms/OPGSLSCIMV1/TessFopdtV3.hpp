#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <deque>
#include <stdexcept>
#include <vector>

namespace tessv3 {

struct InputSegment {
    double duration = 0.0;
    double value = 0.0;
};

// Exact state for a first-order-plus-dead-time system under piecewise-constant
// input. `history` stores the input issued during the last dead_time seconds,
// oldest first. Its total duration is kept equal to dead_time (up to floating
// point tolerance), so delayed inputs are propagated without the common but
// incorrect `max(0, dt-L)` shortcut.
struct FopdtState {
    double output = 0.0;
    double last_input = 0.0;
    double dead_time = 0.0;
    std::deque<InputSegment> history;
};

inline void mergeBack(std::deque<InputSegment>& segments, const InputSegment& segment) {
    if (!(segment.duration > 0.0)) return;
    if (!segments.empty() && std::abs(segments.back().value - segment.value) <= 1e-15) {
        segments.back().duration += segment.duration;
    } else {
        segments.push_back(segment);
    }
}

inline double historyDuration(const std::deque<InputSegment>& history) {
    double total = 0.0;
    for (const auto& segment : history) total += segment.duration;
    return total;
}

inline FopdtState makeFopdtState(double initial_output, double initial_input,
                                 double dead_time) {
    if (!std::isfinite(initial_output) || !std::isfinite(initial_input) || dead_time < 0.0) {
        throw std::invalid_argument("invalid FOPDT initial state");
    }
    FopdtState state;
    state.output = initial_output;
    state.last_input = initial_input;
    state.dead_time = dead_time;
    if (dead_time > 0.0) state.history.push_back({dead_time, initial_input});
    return state;
}

inline void exactFirstOrderStep(double& output, double delayed_input, double duration,
                                double tau_seconds) {
    if (!(duration > 0.0)) return;
    if (!(tau_seconds > 0.0) || !std::isfinite(tau_seconds)) {
        throw std::invalid_argument("tau_seconds must be positive");
    }
    const double alpha = std::exp(-duration / tau_seconds);
    output = delayed_input + (output - delayed_input) * alpha;
}

inline void trimHistoryToDeadTime(FopdtState& state) {
    if (state.dead_time <= 0.0) {
        state.history.clear();
        return;
    }
    double total = historyDuration(state.history);
    while (!state.history.empty() && total - state.history.front().duration >= state.dead_time - 1e-12) {
        total -= state.history.front().duration;
        state.history.pop_front();
    }
    if (!state.history.empty() && total > state.dead_time + 1e-12) {
        const double excess = total - state.dead_time;
        state.history.front().duration -= excess;
        total -= excess;
    }
    if (total < state.dead_time - 1e-12) {
        state.history.push_front({state.dead_time - total, state.last_input});
    }
}

inline void advanceFopdtSegment(FopdtState& state, double new_input, double duration,
                                double tau_seconds) {
    if (!std::isfinite(new_input) || new_input < 0.0 || !std::isfinite(duration) || duration < 0.0) {
        throw std::invalid_argument("invalid FOPDT input segment");
    }
    if (!(duration > 0.0)) {
        state.last_input = new_input;
        return;
    }

    if (state.dead_time <= 0.0) {
        exactFirstOrderStep(state.output, new_input, duration, tau_seconds);
        state.last_input = new_input;
        return;
    }

    // The delayed driving signal over the next `duration` seconds is the first
    // `duration` seconds of [past-L,past] followed by the newly issued input.
    std::deque<InputSegment> timeline = state.history;
    mergeBack(timeline, {duration, new_input});
    double remaining = duration;
    for (const auto& segment : timeline) {
        if (!(remaining > 0.0)) break;
        const double chunk = std::min(remaining, segment.duration);
        exactFirstOrderStep(state.output, segment.value, chunk, tau_seconds);
        remaining -= chunk;
    }
    if (remaining > 1e-10) {
        // This can only occur if a malformed external state had insufficient
        // history. Continue with the oldest physically available input rather
        // than silently shortening the exposure interval.
        exactFirstOrderStep(state.output, state.last_input, remaining, tau_seconds);
    }

    mergeBack(state.history, {duration, new_input});
    state.last_input = new_input;
    trimHistoryToDeadTime(state);
}

inline void advanceFopdt(FopdtState& state, const std::vector<InputSegment>& segments,
                         double tau_seconds) {
    for (const auto& segment : segments) {
        advanceFopdtSegment(state, segment.value, segment.duration, tau_seconds);
    }
}

inline double totalDuration(const std::vector<InputSegment>& segments) {
    double total = 0.0;
    for (const auto& segment : segments) total += std::max(0.0, segment.duration);
    return total;
}

}  // namespace tessv3
