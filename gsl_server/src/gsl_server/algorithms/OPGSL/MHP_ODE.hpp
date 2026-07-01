#pragma once
// MHP-ODE: Multi-type Hawkes Process with ODE Intensity
// Source Domain: Seismology (Ogata 1988) / Neuroscience (Reynaud-Bouret et al. 2014)
// Novel in GSL: No existing work models gas hits as self-exciting point processes
//
// Core Idea: Gas hits form a temporal point process where each hit EXCITES nearby
// future hits (plume clustering effect). The excitation kernel encodes source distance:
//   - Near source: strong, fast-decaying excitation (high alpha, high beta)
//   - Far source: weak, slow-decaying excitation (low alpha, low beta)
//
// Mathematical Foundation (Hawkes Process):
//   lambda(t) = mu + sum_{t_i < t} alpha * exp(-beta * (t - t_i))
//   where:
//     mu: baseline intensity (background gas)
//     alpha: excitation magnitude (plume strength)
//     beta: decay rate (turbulence mixing)
//     branching ratio: n = alpha/beta (must be < 1 for stationarity)
//
// Source Distance Estimation:
//   The branching ratio n decreases with distance from source.
//   n(d) ~ n_0 * exp(-d/d_char)  where d_char is characteristic plume length.
//   By estimating n from hit times, we infer source distance.
//
// Key Innovation: This turns GSL from "estimate source position from concentration"
// to "estimate source position from the STATISTICAL STRUCTURE of detection events".
// This is a fundamentally different observation model.

#include <deque>
#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <Eigen/Dense>

namespace GSL {
namespace Innovation {

class MHP_ODE {
public:
    struct Config {
        double baseline_prior = 0.1;      // Prior for baseline mu
        double alpha_prior = 0.5;         // Prior for excitation alpha
        double beta_prior = 1.0;          // Prior for decay beta
        double learning_rate = 0.01;      // Gradient step size
        int max_events = 200;             // Max events to store
        double min_dt = 0.01;             // Minimum time between events
        double spatial_bins = 20;         // Number of spatial intensity bins
        double intensity_decay = 0.95;    // Decay for old events
        double branching_threshold = 0.3; // Threshold for "excited" state
        double max_alpha = 5.0;           // Maximum excitation
        double distance_char_length = 5.0;// Characteristic distance for branching decay
    };

    struct Event {
        double time;
        double gas_reading;
        int spatial_bin;  // Which spatial bin (discretized direction)
        double weight;
    };

    struct HawkesParams {
        double mu = 0.1;     // Baseline intensity
        double alpha = 0.5;  // Excitation
        double beta = 1.0;   // Decay
        double branching_ratio = 0.0;  // alpha/beta
    };

    struct InferenceResult {
        HawkesParams params;
        double estimated_distance = -1.0;  // Estimated distance to source
        double excitation_score = 0.0;     // Score [0,1] for exploration guidance
        double log_likelihood = 0.0;
        double intensity_now = 0.0;        // Current estimated intensity
        bool is_excited = false;           // Whether in excited state
        int n_events = 0;
        double convergence_rate = 0.0;     // How fast intensity is decaying
    };

    void init(const Config& cfg) {
        cfg_ = cfg;
        events_.clear();
        params_.mu = cfg.baseline_prior;
        params_.alpha = cfg.alpha_prior;
        params_.beta = cfg.beta_prior;
        params_.branching_ratio = params_.alpha / params_.beta;
        result_ = InferenceResult();
    }

    // Record a gas hit event
    InferenceResult recordHit(double gas_reading, double timestamp,
                               int robot_gx, int robot_gy,
                               int n_cells) {
        // Assign spatial bin based on robot position
        int bin = computeSpatialBin(robot_gx, robot_gy, n_cells);

        Event evt;
        evt.time = timestamp;
        evt.gas_reading = gas_reading;
        evt.spatial_bin = bin;
        evt.weight = 1.0;

        events_.push_back(evt);
        if (events_.size() > cfg_.max_events) {
            events_.pop_front();
        }

        // Fit Hawkes parameters via online gradient ascent on log-likelihood
        if (events_.size() >= 5) {
            fitHawkes();
        }

        updateResult();
        return result_;
    }

    // Get current intensity at time t (for prediction)
    double getIntensity(double t) const {
        double intensity = params_.mu;
        for (const auto& evt : events_) {
            double dt = t - evt.time;
            if (dt > 0) {
                intensity += params_.alpha * std::exp(-params_.beta * dt) * evt.weight;
            }
        }
        return intensity;
    }

    // Get exploration guidance: where to look next
    // Returns grid score based on Hawkes spatial-temporal intensity
    double getExplorationScore(int gx, int gy, int n_cells, double current_time) const {
        int bin = computeSpatialBin(gx, gy, n_cells);

        // Base score from temporal intensity
        double temporal_score = getIntensity(current_time);

        // Spatial score: prefer bins with more events
        double spatial_score = 0.0;
        for (const auto& evt : events_) {
            if (evt.spatial_bin == bin) {
                double dt = current_time - evt.time;
                if (dt > 0) {
                    spatial_score += evt.weight * std::exp(-params_.beta * dt);
                }
            }
        }

        // Combine: high intensity + spatial match = good exploration target
        double score = 0.5 * temporal_score + 0.5 * spatial_score;

        // Excited state bonus: when branching ratio is high, gas clustering is active
        if (result_.is_excited) {
            score *= 1.5;
        }

        return score;
    }

    const InferenceResult& result() const { return result_; }

private:
    void fitHawkes() {
        int n = events_.size();
        double total_time = events_.back().time - events_.front().time;
        if (total_time < 1.0) return;

        // Online gradient ascent on log-likelihood
        // L = sum_i log(lambda(t_i)) - integral lambda(t) dt
        // dL/dmu = sum_i 1/lambda(t_i) - T
        // dL/dalpha = sum_i [sum_{j<i} exp(-beta*(t_i-t_j))] / lambda(t_i) - sum_i (1-exp(-beta*(T-t_i)))/beta
        // dL/dbeta = sum_i [sum_{j<i} alpha*(t_i-t_j)*exp(-beta*(t_i-t_j))] / lambda(t_i) - ...

        double ll = 0.0;
        double grad_mu = 0.0, grad_alpha = 0.0, grad_beta = 0.0;

        for (int i = 0; i < n; ++i) {
            double ti = events_[i].time;

            // Compute conditional intensity at ti
            double lambda_i = params_.mu;
            double sum_excitation = 0.0;
            double sum_time_weighted = 0.0;

            for (int j = 0; j < i; ++j) {
                double dt = ti - events_[j].time;
                if (dt > cfg_.min_dt) {
                    double kern = params_.alpha * std::exp(-params_.beta * dt) * events_[j].weight;
                    lambda_i += kern;
                    sum_excitation += kern;
                    sum_time_weighted += dt * kern;
                }
            }

            if (lambda_i < 1e-10) lambda_i = 1e-10;

            ll += std::log(lambda_i);

            // Gradients
            grad_mu += 1.0 / lambda_i;
            grad_alpha += sum_excitation / (params_.alpha * lambda_i);
            grad_beta += sum_time_weighted / lambda_i;
        }

        // Integral term
        double T = total_time;
        grad_mu -= T;

        double integral_alpha = 0.0;
        double integral_beta = 0.0;
        for (const auto& evt : events_) {
            double remaining = T - (evt.time - events_.front().time);
            if (remaining > 0) {
                integral_alpha += (1.0 - std::exp(-params_.beta * remaining)) / params_.beta;
                integral_beta += params_.alpha * remaining * std::exp(-params_.beta * remaining) / params_.beta;
            }
        }
        grad_alpha -= integral_alpha;
        grad_beta -= integral_beta;

        // Update parameters
        double lr = cfg_.learning_rate;
        params_.mu = std::max(0.001, params_.mu + lr * grad_mu);
        params_.alpha = std::max(0.01, std::min(cfg_.max_alpha, params_.alpha + lr * grad_alpha));
        params_.beta = std::max(0.1, params_.beta + lr * grad_beta);

        // Ensure stationarity: alpha < beta
        if (params_.alpha >= params_.beta * 0.95) {
            params_.alpha = params_.beta * 0.9;
        }

        params_.branching_ratio = params_.alpha / params_.beta;
        result_.log_likelihood = ll;
    }

    void updateResult() {
        result_.params = params_;
        result_.n_events = events_.size();

        // Current intensity
        double current_time = events_.empty() ? 0.0 : events_.back().time;
        result_.intensity_now = getIntensity(current_time);

        // Excited state: high branching ratio + recent events
        result_.is_excited = (params_.branching_ratio > cfg_.branching_threshold) &&
                             (result_.intensity_now > params_.mu * 2.0);

        // Distance estimation from branching ratio
        // n(d) = n_0 * exp(-d/d_char) => d = d_char * log(n_0/n)
        if (params_.branching_ratio > 0.01) {
            double n_0 = 0.9;  // Max possible branching ratio near source
            double d = cfg_.distance_char_length * std::log(n_0 / params_.branching_ratio);
            result_.estimated_distance = std::max(0.0, std::min(d, 20.0));
        }

        // Excitation score: maps to [0, 1] for exploration
        result_.excitation_score = std::min(1.0, params_.branching_ratio * 2.0);

        // Convergence rate: how fast intensity is decaying
        if (events_.size() >= 2) {
            double t1 = events_[events_.size()-2].time;
            double t2 = events_.back().time;
            double i1 = getIntensity(t1);
            double i2 = getIntensity(t2);
            if (i1 > 0) {
                result_.convergence_rate = (i2 - i1) / (t2 - t1 + 1e-6);
            }
        }
    }

    int computeSpatialBin(int gx, int gy, int n_cells) const {
        // Discretize position into spatial bins
        double angle = std::atan2(gy - n_cells/2.0, gx - n_cells/2.0);
        int bin = static_cast<int>((angle + M_PI) / (2 * M_PI) * cfg_.spatial_bins);
        return std::max(0, std::min(bin, static_cast<int>(cfg_.spatial_bins) - 1));
    }

    Config cfg_;
    std::deque<Event> events_;
    HawkesParams params_;
    InferenceResult result_;
};

} // namespace Innovation
} // namespace GSL
