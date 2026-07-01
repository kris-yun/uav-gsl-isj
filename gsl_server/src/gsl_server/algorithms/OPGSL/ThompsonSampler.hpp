#pragma once
// Thompson Sampling Adaptive Exploration (TS-AE)
// Inspired by clinical trial design (Thompson 1933, Agrawal & Goyal 2012)
// and Bayesian optimization (Shahriari et al. 2016)
// Purpose: Bayes-optimal exploration-exploitation tradeoff

#include <Eigen/Dense>
#include <random>
#include <cmath>
#include <algorithm>

namespace GSL {
namespace Innovation {

class ThompsonSampler {
public:
    struct Config {
        int n_samples = 10;           // Number of Thompson samples per decision
        float temperature = 1.0f;     // Temperature for softmax
        float prior_weight = 0.1f;    // Weight of prior vs posterior
    };

    void init(const Config& cfg, int n_cells, unsigned seed = 42) {
        cfg_ = cfg;
        n_cells_ = n_cells;
        rng_.seed(seed);
    }

    // Sample a source location from the posterior and return the best next cell to visit
    struct SampleResult {
        int best_gx, best_gy;
        float score;
        float sampled_source_x, sampled_source_y;
    };

    SampleResult sampleAndScore(const Eigen::MatrixXf& log_posterior,
                                 int robot_gx, int robot_gy,
                                 const Eigen::MatrixXf& grid_x,
                                 const Eigen::MatrixXf& grid_y,
                                 float wind_x, float wind_y) {
        SampleResult result;
        result.score = -1e9f;
        result.best_gx = robot_gx;
        result.best_gy = robot_gy;

        int N = n_cells_;

        // Convert log posterior to probabilities
        Eigen::ArrayXXf prob = log_posterior.array().exp();
        prob /= prob.sum();

        // Flatten for sampling
        Eigen::ArrayXf flat = prob.reshaped();
        std::discrete_distribution<int> dist(flat.data(), flat.data() + flat.size());

        // Multiple Thompson samples
        for (int s = 0; s < cfg_.n_samples; ++s) {
            // Sample a source location from posterior
            int sampled_idx = dist(rng_);
            int src_gx = sampled_idx / N;
            int src_gy = sampled_idx % N;

            // Score all cells based on expected information gain given this sampled source
            for (int gx = std::max(0, robot_gx - 10); gx <= std::min(N-1, robot_gx + 10); ++gx) {
                for (int gy = std::max(0, robot_gy - 10); gy <= std::min(N-1, robot_gy + 10); ++gy) {
                    float dx = grid_x(gx, gy) - grid_x(src_gx, src_gy);
                    float dy = grid_y(gx, gy) - grid_y(src_gx, src_gy);
                    float dist_to_source = std::sqrt(dx*dx + dy*dy) + 0.1f;

                    // Expected gas detection probability at this cell given sampled source
                    float wind_dir = std::atan2(wind_y, wind_x);
                    float cos_w = std::cos(wind_dir);
                    float sin_w = std::sin(wind_dir);
                    float x_wind = dx * cos_w + dy * sin_w;
                    float detect_prob = (x_wind > 0) ? 0.8f : 0.1f;  // Downwind vs upwind

                    // Information gain: how much would visiting this cell tell us?
                    float current_p = prob(gx, gy);
                    float ig = detect_prob * (1.0f - current_p) / (1.0f + 0.3f * dist_to_source);

                    if (ig > result.score) {
                        result.score = ig;
                        result.best_gx = gx;
                        result.best_gy = gy;
                        result.sampled_source_x = grid_x(src_gx, src_gy);
                        result.sampled_source_y = grid_y(src_gx, src_gy);
                    }
                }
            }
        }

        return result;
    }

private:
    Config cfg_;
    int n_cells_ = 0;
    std::mt19937 rng_;
};

} // namespace Innovation
} // namespace GSL
