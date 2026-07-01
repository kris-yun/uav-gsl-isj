#pragma once
// UCB-Explore: Upper Confidence Bound exploration strategy
// Inspired by multi-armed bandit theory (Auer et al. 2002, Bubeck & Cesa-Bianchi 2012)
// and Bayesian optimization acquisition functions
// Purpose: Principled exploration-exploitation tradeoff for path planning

#include <cmath>
#include <vector>
#include <algorithm>
#include <Eigen/Dense>

namespace GSL {
namespace Innovation {

class UCB_Explore {
public:
    struct Config {
        float ucb_c = 2.0f;              // UCB exploration parameter
        float min_variance = 0.01f;      // Minimum variance to prevent division by zero
        float novelty_bonus = 0.3f;      // Bonus for unvisited regions
        float decay_factor = 0.95f;      // Decay for visit counts
    };

    void init(const Config& cfg, int n_cells) {
        cfg_ = cfg;
        n_cells_ = n_cells;
        visit_counts_ = Eigen::MatrixXf::Zero(n_cells, n_cells);
        cumulative_reward_ = Eigen::MatrixXf::Zero(n_cells, n_cells);
        total_visits_ = 0;
    }

    struct Score {
        float ucb_value;
        float posterior_term;    // exploitation
        float uncertainty_term;  // exploration
        float novelty_term;     // unvisited bonus
    };

    Score scoreCell(int gx, int gy, float log_posterior, float grid_x, float grid_y,
                    float robot_x, float robot_y) const {
        Score s;

        float p = std::exp(log_posterior);
        float dist = std::sqrt((grid_x - robot_x) * (grid_x - robot_x) +
                               (grid_y - robot_y) * (grid_y - robot_y)) + 0.1f;

        // Exploitation: posterior probability weighted by distance
        s.posterior_term = p / (1.0f + 0.3f * dist);

        // Exploration: uncertainty bonus (UCB-style)
        // High variance in visit counts = high uncertainty
        float visits = visit_counts_(gx, gy) + 1.0f;
        s.uncertainty_term = cfg_.ucb_c * std::sqrt(std::log(total_visits_ + 1.0f) / visits);

        // Novelty: bonus for unvisited cells
        s.novelty_term = (visits < 2.0f) ? cfg_.novelty_bonus / (1.0f + 0.2f * dist) : 0.0f;

        // UCB = exploitation + exploration + novelty
        s.ucb_value = s.posterior_term + s.uncertainty_term + s.novelty_term;

        return s;
    }

    void recordVisit(int gx, int gy, float reward) {
        if (gx >= 0 && gx < n_cells_ && gy >= 0 && gy < n_cells_) {
            visit_counts_(gx, gy) += 1.0f;
            cumulative_reward_(gx, gy) += reward;
            total_visits_++;
        }
    }

    void decayAll() {
        visit_counts_ *= cfg_.decay_factor;
        cumulative_reward_ *= cfg_.decay_factor;
    }

    float getVisitCount(int gx, int gy) const {
        return visit_counts_(gx, gy);
    }

private:
    Config cfg_;
    int n_cells_ = 0;
    Eigen::MatrixXf visit_counts_;
    Eigen::MatrixXf cumulative_reward_;
    int total_visits_ = 0;
};

} // namespace Innovation
} // namespace GSL
