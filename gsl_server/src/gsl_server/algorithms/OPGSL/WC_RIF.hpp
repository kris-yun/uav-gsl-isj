// WC-RIF.hpp - Wind-Conditioned Robust Intermittency Filter
// Origin: Robust statistics (Ge Quanbo MCC, IEEE TSP 2025)
// Innovation: Cauchy kernel + wind-conditioned bandwidth + intermittency weighting
//
// Key insight: MOX sensor noise is heavy-tailed (non-Gaussian).
// Standard Bayesian update uses Gaussian likelihood → vulnerable to outliers.
// WC-RIF uses Cauchy kernel → robust to outlier readings.
//
// Wind-conditioning: downwind observations are more reliable → larger sigma (more trust)
//                   upwind observations are less reliable → smaller sigma (more skeptical)
//
// Intermittency: consecutive hits are more reliable than isolated hits

#pragma once
#include <Eigen/Dense>
#include <vector>
#include <cmath>
#include <algorithm>
#include <deque>

namespace GSL {
namespace WC_RIF {

struct Config {
    int n_cells = 40;
    float resolution = 0.5f;
    float map_half_size = 10.0f;

    // Cauchy kernel parameters
    float sigma_base = 0.3f;        // base kernel bandwidth
    float beta_wind = 0.5f;         // wind-conditioning strength
    float alpha_intermittency = 0.3f; // intermittency sensitivity
    float gamma_entropy = 0.1f;     // entropy adaptation rate

    // Plume model (for hit probability computation)
    float Q = 1.0f;                 // source emission rate
    float sigma_y = 0.8f;           // cross-wind spread
    float sigma_z = 0.4f;           // vertical spread
    float min_wind = 0.1f;          // minimum wind speed
};

class WCRIFEstimator {
public:
    void init(const Config& cfg) {
        cfg_ = cfg;
        int N = cfg.n_cells;
        log_belief_ = Eigen::MatrixXf::Zero(N, N);
        log_belief_.setConstant(-std::log(float(N * N)));

        // Precompute grid coordinates
        grid_x_.resize(N, N);
        grid_y_.resize(N, N);
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                grid_x_(i, j) = i * cfg.resolution - cfg.map_half_size;
                grid_y_(i, j) = j * cfg.resolution - cfg.map_half_size;
            }
        }
    }

    // Main update: WC-RIF belief update
    void update(float gas_reading, float robot_x, float robot_y,
                float wind_x, float wind_y, float elapsed_time) {
        bool hit = gas_reading > 0.01f;
        if (hit) gas_hits_++;

        // Track intermittency
        hit_history_.push_back(hit ? 1 : 0);
        if (hit_history_.size() > kWindowSize) hit_history_.pop_front();

        // Compute intermittency weight
        float hit_rate = computeHitRate();
        float w_inter = (1.0f - cfg_.alpha_intermittency) + cfg_.alpha_intermittency * hit_rate;

        // Adaptive sigma based on current entropy
        float H = entropy();
        float H_max = std::log(float(cfg_.n_cells * cfg_.n_cells));
        float sigma_adaptive = cfg_.sigma_base * (1.0f + cfg_.gamma_entropy * H / H_max);

        // Update belief for each grid cell
        for (int i = 0; i < cfg_.n_cells; ++i) {
            for (int j = 0; j < cfg_.n_cells; ++j) {
                float sx = grid_x_(i, j);
                float sy = grid_y_(i, j);

                // Wind alignment: +1 = downwind, -1 = upwind
                float alignment = computeWindAlignment(sx, sy, robot_x, robot_y, wind_x, wind_y);

                // Wind-conditioned sigma
                float sigma_eff = sigma_adaptive * (1.0f + cfg_.beta_wind * alignment);

                // Expected hit probability (Gaussian plume model)
                float p_hit = computeHitProbability(sx, sy, robot_x, robot_y, wind_x, wind_y);

                // Observation residual
                float residual = hit ? std::abs(1.0f - p_hit) : std::abs(0.0f - p_hit);

                // WC-RIF update: Cauchy kernel (robust to outliers)
                float kernel_val = cauchyKernel(residual, sigma_eff);

                // Weighted update
                float log_update;
                if (hit) {
                    log_update = std::log(std::max(kernel_val * w_inter, 1e-10f));
                } else {
                    float miss_weight = (1.0f - kernel_val) * w_inter + (1.0f - w_inter) * 0.5f;
                    log_update = std::log(std::max(miss_weight, 1e-10f));
                }
                log_belief_(i, j) += log_update;
            }
        }
        normalize();
    }

    // Getters
    void getMAP(float& x, float& y) const {
        int best_i = 0, best_j = 0;
        float best_val = log_belief_(0, 0);
        for (int i = 0; i < cfg_.n_cells; ++i) {
            for (int j = 0; j < cfg_.n_cells; ++j) {
                if (log_belief_(i, j) > best_val) {
                    best_val = log_belief_(i, j);
                    best_i = i; best_j = j;
                }
            }
        }
        x = grid_x_(best_i, best_j);
        y = grid_y_(best_i, best_j);
    }

    float entropy() const {
        float H = 0.0f;
        Eigen::ArrayXXf p = log_belief_.array().exp();
        p /= p.sum();
        H = -(p * log_belief_.array()).sum();
        return H;
    }

    int gasHits() const { return gas_hits_; }

    void reset() {
        log_belief_.setConstant(-std::log(float(cfg_.n_cells * cfg_.n_cells)));
        gas_hits_ = 0;
        hit_history_.clear();
    }

private:
    Config cfg_;
    Eigen::MatrixXf log_belief_;
    Eigen::MatrixXf grid_x_, grid_y_;
    int gas_hits_ = 0;
    std::deque<int> hit_history_;
    static constexpr int kWindowSize = 10;

    float computeHitProbability(float sx, float sy, float sensor_x, float sensor_y,
                                 float wind_x, float wind_y) const {
        float dx = sensor_x - sx;
        float dy = sensor_y - sy;
        float dist = std::sqrt(dx*dx + dy*dy) + 0.01f;

        float ws = std::max(std::sqrt(wind_x*wind_x + wind_y*wind_y), cfg_.min_wind);
        float wnx = wind_x / (std::sqrt(wind_x*wind_x + wind_y*wind_y) + 1e-6f);
        float wny = wind_y / (std::sqrt(wind_x*wind_x + wind_y*wind_y) + 1e-6f);

        float d_down = dx * wnx + dy * wny;
        float d_cross = std::abs(dx * wny - dy * wnx);

        float sy_val = cfg_.sigma_y * std::sqrt(std::max(d_down, 0.01f));
        float sz_val = cfg_.sigma_z * std::sqrt(std::max(d_down, 0.01f));

        float p = cfg_.Q / (2.0f * M_PI * sy_val * sz_val * ws) *
                  std::exp(-d_cross*d_cross / (2.0f * sy_val*sy_val));
        return std::min(std::max(p, 0.0f), 0.99f);
    }

    float computeWindAlignment(float sx, float sy, float sensor_x, float sensor_y,
                                float wind_x, float wind_y) const {
        float dx = sensor_x - sx;
        float dy = sensor_y - sy;
        float dist = std::sqrt(dx*dx + dy*dy) + 0.01f;
        float ws = std::sqrt(wind_x*wind_x + wind_y*wind_y) + 1e-6f;
        return (dx * wind_x + dy * wind_y) / (dist * ws);
    }

    float cauchyKernel(float d, float sigma) const {
        return 1.0f / (M_PI * (1.0f + (d/sigma) * (d/sigma)));
    }

    float computeHitRate() const {
        if (hit_history_.empty()) return 0.0f;
        int sum = 0;
        for (int h : hit_history_) sum += h;
        return float(sum) / hit_history_.size();
    }

    void normalize() {
        float max_log = log_belief_.maxCoeff();
        log_belief_.array() -= max_log;
        float log_sum = std::log(log_belief_.array().exp().sum());
        log_belief_.array() -= log_sum;
    }
};

} // namespace WC_RIF
} // namespace GSL
