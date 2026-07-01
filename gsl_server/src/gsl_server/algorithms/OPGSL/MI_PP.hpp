// MI_PP.hpp - Mutual Information Path Planning for Gas Source Localization
// Cross-domain origin: Sensor network optimization (Schur-MI, IROS 2026)
// Physical basis: Gas plumes have wind-dependent spatial correlation
// Mathematical basis: MI(X;Y) = H(X) - H(X|Y), path-level information gain

#pragma once
#include <Eigen/Dense>
#include <vector>
#include <cmath>
#include <algorithm>
#include <random>

namespace GSL {
namespace MI_PP {

struct WindField {
    float wx, wy;  // wind direction (normalized)
    float ws;      // wind speed (m/s)
};

// Gaussian plume observation model
// P(z=1 | source=s, sensor=x, wind) = Q * exp(-d_cross²/(2σ_y²)) * exp(-d_along²/(2σ_z²))
// where d_cross = distance perpendicular to wind, d_along = distance along wind
class PlumeObservationModel {
public:
    struct Config {
        float Q = 1.0f;           // source emission rate
        float sigma_y = 0.8f;     // cross-wind spread
        float sigma_z = 0.4f;     // vertical spread
        float min_wind = 0.1f;    // minimum wind speed for model
        float noise_std = 0.05f;  // observation noise
    };

    void init(const Config& cfg) { cfg_ = cfg; }

    // Compute P(hit | source=s, sensor=x, wind)
    float hitProbability(float sx, float sy, float sensor_x, float sensor_y,
                         const WindField& wind) const {
        float dx = sensor_x - sx;
        float dy = sensor_y - sy;
        float dist = std::sqrt(dx*dx + dy*dy) + 0.01f;

        // Wind direction
        float ws = std::max(wind.ws, cfg_.min_wind);
        float wx = wind.wx / (std::sqrt(wind.wx*wind.wx + wind.wy*wind.wy) + 1e-6f);
        float wy = wind.wy / (std::sqrt(wind.wx*wind.wx + wind.wy*wind.wy) + 1e-6f);

        // Downwind distance (positive = sensor is downwind of source)
        float d_down = dx * wx + dy * wy;

        // Crosswind distance
        float d_cross = std::abs(dx * wy - dy * wx);

        // Gaussian plume model
        float sigma_y_val = sigma_y_val = cfg_.sigma_y * std::sqrt(std::max(d_down, 0.01f));
        float sigma_z_val = sigma_z_val = cfg_.sigma_z * std::sqrt(std::max(d_down, 0.01f));

        float p = cfg_.Q / (2.0f * M_PI * sigma_y_val * sigma_z_val * ws) *
                  std::exp(-d_cross*d_cross / (2.0f * sigma_y_val*sigma_y_val));

        return std::min(std::max(p, 0.0f), 0.99f);
    }

private:
    Config cfg_;
};

// Grid-based Bayesian belief over source location
class SourceBelief {
public:
    struct Config {
        int n_cells = 40;
        float resolution = 0.5f;
        float map_half_size = 10.0f;
    };

    void init(const Config& cfg) {
        cfg_ = cfg;
        log_belief_ = Eigen::MatrixXf::Zero(cfg.n_cells, cfg.n_cells);
        log_belief_.setConstant(-std::log(float(cfg.n_cells * cfg.n_cells)));
    }

    // Update belief with new observation
    void update(float gas_reading, float sensor_x, float sensor_y,
                const WindField& wind, const PlumeObservationModel& model) {
        for (int i = 0; i < cfg_.n_cells; ++i) {
            for (int j = 0; j < cfg_.n_cells; ++j) {
                float sx, sy;
                gridToWorld(i, j, sx, sy);
                float p_hit = model.hitProbability(sx, sy, sensor_x, sensor_y, wind);

                // Log-likelihood update
                float log_lik;
                if (gas_reading > 0.01f) {
                    log_lik = std::log(p_hit + 1e-10f);
                } else {
                    log_lik = std::log(1.0f - p_hit + 1e-10f);
                }
                log_belief_(i, j) += log_lik;
            }
        }
        normalize();
    }

    // Compute entropy H[source | D_t]
    float entropy() const {
        float H = 0.0f;
        for (int i = 0; i < cfg_.n_cells; ++i) {
            for (int j = 0; j < cfg_.n_cells; ++j) {
                float p = std::exp(log_belief_(i, j));
                if (p > 1e-10f) H -= p * log_belief_(i, j);
            }
        }
        return H;
    }

    // Compute expected entropy after hypothetical observation at (x, y)
    // E_z[H[source | D_t, z]] = P(hit) * H[source | D_t, hit] + P(miss) * H[source | D_t, miss]
    float expectedEntropyAfterObservation(float x, float y,
                                          const WindField& wind,
                                          const PlumeObservationModel& model) const {
        // Compute P(hit) = Σ_s b(s) * P(hit|s, x, wind)
        float p_hit_total = 0.0f;
        for (int i = 0; i < cfg_.n_cells; ++i) {
            for (int j = 0; j < cfg_.n_cells; ++j) {
                float sx, sy;
                gridToWorld(i, j, sx, sy);
                float b = std::exp(log_belief_(i, j));
                float p_hit = model.hitProbability(sx, sy, x, y, wind);
                p_hit_total += b * p_hit;
            }
        }
        p_hit_total = std::min(std::max(p_hit_total, 0.01f), 0.99f);

        // Compute posterior entropy if hit
        Eigen::MatrixXf log_post_hit = log_belief_;
        Eigen::MatrixXf log_post_miss = log_belief_;
        for (int i = 0; i < cfg_.n_cells; ++i) {
            for (int j = 0; j < cfg_.n_cells; ++j) {
                float sx, sy;
                gridToWorld(i, j, sx, sy);
                float p_hit = model.hitProbability(sx, sy, x, y, wind);
                log_post_hit(i, j) += std::log(p_hit + 1e-10f);
                log_post_miss(i, j) += std::log(1.0f - p_hit + 1e-10f);
            }
        }

        float H_hit = computeEntropy(log_post_hit);
        float H_miss = computeEntropy(log_post_miss);

        return p_hit_total * H_hit + (1.0f - p_hit_total) * H_miss;
    }

    // Get MAP estimate
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
        gridToWorld(best_i, best_j, x, y);
    }

    // Get posterior probability at grid cell
    float getProb(int i, int j) const {
        return std::exp(log_belief_(i, j));
    }

    int nCells() const { return cfg_.n_cells; }
    float resolution() const { return cfg_.resolution; }

private:
    Config cfg_;
    Eigen::MatrixXf log_belief_;

    void gridToWorld(int i, int j, float& x, float& y) const {
        x = i * cfg_.resolution - cfg_.map_half_size;
        y = j * cfg_.resolution - cfg_.map_half_size;
    }

    void normalize() {
        float max_log = log_belief_.maxCoeff();
        log_belief_.array() -= max_log;
        float log_sum = std::log((log_belief_.array().exp()).sum());
        log_belief_.array() -= log_sum;
    }

    float computeEntropy(const Eigen::MatrixXf& log_belief) const {
        float H = 0.0f;
        float max_log = log_belief.maxCoeff();
        Eigen::MatrixXf normalized = log_belief; normalized.array() -= max_log;;
        float log_sum = std::log((normalized.array().exp()).sum());
        normalized.array() -= log_sum;

        for (int i = 0; i < cfg_.n_cells; ++i) {
            for (int j = 0; j < cfg_.n_cells; ++j) {
                float p = std::exp(normalized(i, j));
                if (p > 1e-10f) H -= p * normalized(i, j);
            }
        }
        return H;
    }
};

// MI Path Planner
class MIPathPlanner {
public:
    struct Config {
        int n_candidates = 20;      // number of candidate waypoints to evaluate
        float step_size = 1.0f;     // meters per step
        int horizon = 5;            // planning horizon (steps ahead)
        float wind_bonus = 0.3f;    // bonus for downwind exploration
    };

    void init(const Config& cfg) { cfg_ = cfg; }

    struct Path {
        std::vector<std::pair<float,float>> waypoints;
        float total_mi;
    };

    // Plan best path given current belief, position, and wind
    Path planPath(const SourceBelief& belief, float cur_x, float cur_y,
                  const WindField& wind, const PlumeObservationModel& model,
                  float remaining_time, float uav_speed) const {
        Path best_path;
        best_path.total_mi = -1e9f;

        float budget = remaining_time * uav_speed;
        int N = belief.nCells();
        float res = belief.resolution();

        // Generate candidate waypoints
        std::vector<std::pair<float,float>> candidates;
        for (int di = -5; di <= 5; ++di) {
            for (int dj = -5; dj <= 5; ++dj) {
                if (di == 0 && dj == 0) continue;
                float x = cur_x + di * res;
                float y = cur_y + dj * res;
                float dist = std::sqrt(float(di*di + dj*dj)) * res;
                if (dist > 0.5f && dist <= budget) {
                    candidates.push_back({x, y});
                }
            }
        }

        // For each candidate, compute MI
        float H_current = belief.entropy();
        std::vector<std::pair<float, std::pair<float,float>>> scored;
        for (auto& [x, y] : candidates) {
            float H_after = belief.expectedEntropyAfterObservation(x, y, wind, model);
            float mi = H_current - H_after;

            // Wind bonus: prefer downwind exploration
            float dx = x - cur_x;
            float dy = y - cur_y;
            float dist = std::sqrt(dx*dx + dy*dy) + 0.01f;
            float alignment = (dx * wind.wx + dy * wind.wy) / (dist * (std::sqrt(wind.wx*wind.wx + wind.wy*wind.wy) + 1e-6f));
            if (alignment > 0) {
                mi += cfg_.wind_bonus * alignment * mi;
            }

            scored.push_back({mi, {x, y}});
        }

        // Sort by MI
        std::sort(scored.begin(), scored.end(),
                  [](auto& a, auto& b) { return a.first > b.first; });

        // Greedy path construction (like OP solver)
        float remaining = budget;
        float px = cur_x, py = cur_y;
        std::set<std::pair<int,int>> used;

        for (int step = 0; step < cfg_.horizon && !scored.empty(); ++step) {
            float best_mi = -1e9f;
            int best_idx = -1;

            for (size_t i = 0; i < scored.size(); ++i) {
                auto& [mi, pos] = scored[i];
                float dx = pos.first - px;
                float dy = pos.second - py;
                float travel = std::sqrt(dx*dx + dy*dy);

                int gi = int((pos.first + cfg_.step_size * 10) / cfg_.step_size);
                int gj = int((pos.second + cfg_.step_size * 10) / cfg_.step_size);
                if (used.count({gi, gj})) continue;

                if (travel > 0.1f && travel <= remaining) {
                    // MI per unit distance (efficiency)
                    float efficiency = mi / travel;
                    if (efficiency > best_mi) {
                        best_mi = efficiency;
                        best_idx = i;
                    }
                }
            }

            if (best_idx < 0) break;

            auto& [mi, pos] = scored[best_idx];
            float dx = pos.first - px;
            float dy = pos.second - py;
            float travel = std::sqrt(dx*dx + dy*dy);

            best_path.waypoints.push_back(pos);
            best_path.total_mi += mi;

            int gi = int((pos.first + cfg_.step_size * 10) / cfg_.step_size);
            int gj = int((pos.second + cfg_.step_size * 10) / cfg_.step_size);
            used.insert({gi, gj});

            px = pos.first;
            py = pos.second;
            remaining -= travel;
        }

        return best_path;
    }

private:
    Config cfg_;
};

} // namespace MI_PP
} // namespace GSL
