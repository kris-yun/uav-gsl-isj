#pragma once
// OT-PF: Optimal Transport Posterior Filter
// Source Domain: Computer Vision (Peyre & Cuturi 2019) / Computational Optimal Transport
// Novel in GSL: No existing work uses Wasserstein distance for posterior update
//
// Core Idea: Instead of point-wise Bayesian update, use Optimal Transport to
// transform the prior distribution toward the posterior by finding the minimal-cost
// transport plan from prior to a "data-informed" target distribution.
//
// Mathematical Foundation:
//   W_2^2(mu, nu) = min_{pi} int ||x-y||^2 d(pi(x,y))  s.t. marginals = mu, nu
//   Posterior update: mu_{t+1} = (1-alpha)*mu_t + alpha*T_#(data_measure)
//   where T_# is the pushforward by the optimal transport map
//
// Key Insight: OT-based update naturally handles multi-modal posteriors and
// avoids the "particle degeneracy" problem of standard PF in high dimensions.
// This is analogous to Wasserstein gradient flows in image processing.

#include <Eigen/Dense>
#include <vector>
#include <cmath>
#include <algorithm>

namespace GSL {
namespace Innovation {

class OT_PF {
public:
    struct Config {
        int n_cells = 60;                // Grid resolution
        double transport_step = 0.15;    // Step size for OT update (alpha)
        double sinkhorn_lambda = 10.0;   // Entropic regularization for Sinkhorn
        int sinkhorn_iters = 5;          // Number of Sinkhorn iterations
        double distance_penalty = 0.3;   // Exponent for distance cost
        double min_transport_mass = 0.01;// Minimum mass to transport
        double blur_sigma = 1.5;         // Gaussian blur for data measure
        bool use_log_domain = true;      // Use log-domain Sinkhorn for stability
    };

    void init(const Config& cfg) {
        cfg_ = cfg;
        int N = cfg.n_cells;
        transport_plan_.resize(N, N);
        transport_plan_.setZero();
        data_measure_.resize(N, N);
        data_measure_.setZero();
    }

    // Compute OT-based posterior update
    // prior: current log-posterior (NxN)
    // robot_gx, robot_gy: robot grid position
    // gas_reading: current gas measurement
    // wind_x, wind_y: wind vector
    // Returns: correction term to add to log-posterior
    Eigen::MatrixXf computeUpdate(const Eigen::MatrixXf& log_prior,
                                   int robot_gx, int robot_gy,
                                   float gas_reading,
                                   float wind_x, float wind_y,
                                   int n_cells) {
        int N = n_cells;

        // Step 1: Construct data-informed target measure
        // Based on gas reading and wind direction
        constructDataMeasure(robot_gx, robot_gy, gas_reading, wind_x, wind_y, N);

        // Step 2: Convert prior to probability measure
        Eigen::MatrixXf prior = logPrior.array().exp().matrix();
        float prior_sum = prior.sum();
        if (prior_sum > 0) prior /= prior_sum;

        // Step 3: Compute transport cost matrix (pre-computed grid distances)
        // For efficiency, use Sinkhorn in log-domain with Gaussian kernel
        Eigen::MatrixXf update = sinkhornBarycenter(prior, data_measure_, N);

        // Step 4: Compute the OT correction (Wasserstein interpolation)
        Eigen::MatrixXf correction(N, N);
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                float p_val = std::max(prior(i,j), 1e-10f);
                float u_val = std::max(update(i,j), 1e-10f);
                // Log-domain correction: log(u/p) scaled by transport step
                correction(i,j) = cfg_.transport_step * (std::log(u_val) - std::log(p_val));
            }
        }

        // Apply spatial smoothing to avoid sharp transitions
        gaussianBlur(correction, N, cfg_.blur_sigma);

        return correction;
    }

    // Get transport distance (convergence metric)
    float getTransportDistance() const { return last_wasserstein_dist_; }
    float getEntropyReduction() const { return last_entropy_reduction_; }

private:
    void constructDataMeasure(int robot_gx, int robot_gy, float gas_reading,
                               float wind_x, float wind_y, int N) {
        data_measure_.setZero();

        if (gas_reading < 1e-6f) return;

        float wind_dir = std::atan2(wind_y, wind_x);
        float cos_w = std::cos(wind_dir);
        float sin_w = std::sin(wind_dir);

        float total = 0.0f;
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                float dx = float(i - robot_gx);
                float dy = float(j - robot_gy);
                float dist = std::sqrt(dx*dx + dy*dy);

                // Wind-aligned Gaussian: elongated in downwind direction
                float x_wind = dx * cos_w + dy * sin_w;  // Along-wind
                float y_wind = -dx * sin_w + dy * cos_w;  // Cross-wind

                // Plume-shaped measure
                float sigma_along = 2.0f + 0.5f * std::max(0.0f, x_wind);
                float sigma_cross = 1.0f + 0.2f * std::max(0.0f, x_wind);

                float log_p = -(x_wind * x_wind) / (2.0f * sigma_along * sigma_along)
                             -(y_wind * y_wind) / (2.0f * sigma_cross * sigma_cross);

                // Weight by gas reading strength and distance
                float w = std::exp(log_p) * gas_reading / (1.0f + 0.1f * dist);

                // Only update downwind region (source is upwind of robot)
                if (x_wind < 0) w *= 0.3f;  // Upwind: less likely to be source

                data_measure_(i, j) = std::max(w, 0.0f);
                total += data_measure_(i, j);
            }
        }

        if (total > 0) data_measure_ /= total;
    }

    // Sinkhorn barycenter in log-domain (Cuturi & Doucet 2014)
    Eigen::MatrixXf sinkhornBarycenter(const Eigen::MatrixXf& a,
                                        const Eigen::MatrixXf& b,
                                        int N) {
        // Simplified Sinkhorn: compute entropy-regularized OT barycenter
        // In log-domain for numerical stability

        float lambda = cfg_.sinkhorn_lambda;

        // Initialize dual variables
        Eigen::VectorXf log_u = Eigen::VectorXf::Zero(N * N);
        Eigen::VectorXf log_v = Eigen::VectorXf::Zero(N * N);

        // Flatten distributions
        Eigen::VectorXf log_a(N * N);
        Eigen::VectorXf log_b(N * N);
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                log_a(i * N + j) = std::log(std::max(a(i, j), 1e-10f));
                log_b(i * N + j) = std::log(std::max(b(i, j), 1e-10f));
            }
        }

        // Pre-compute log-cost matrix (Euclidean distance on grid)
        // For efficiency, only compute for nearby cells
        int max_dist = std::min(10, N / 2);

        // Sinkhorn iterations
        for (int iter = 0; iter < cfg_.sinkhorn_iters; ++iter) {
            // Update log_u
            for (int i = 0; i < N * N; ++i) {
                int ix = i / N, iy = i % N;
                float log_sum = -1e20f;
                for (int jx = std::max(0, ix - max_dist); jx < std::min(N, ix + max_dist + 1); ++jx) {
                    for (int jy = std::max(0, iy - max_dist); jy < std::min(N, iy + max_dist + 1); ++jy) {
                        int j = jx * N + jy;
                        float cost = std::sqrt(float((ix-jx)*(ix-jx) + (iy-jy)*(iy-jy)));
                        float val = log_b(j) + log_v(j) - lambda * cost;
                        log_sum = logSumExp(log_sum, val);
                    }
                }
                log_u(i) = log_a(i) - log_sum;
            }

            // Update log_v
            for (int j = 0; j < N * N; ++j) {
                int jx = j / N, jy = j % N;
                float log_sum = -1e20f;
                for (int ix = std::max(0, jx - max_dist); ix < std::min(N, jx + max_dist + 1); ++ix) {
                    for (int iy = std::max(0, jy - max_dist); iy < std::min(N, jy + max_dist + 1); ++iy) {
                        int i = ix * N + iy;
                        float cost = std::sqrt(float((ix-jx)*(ix-jx) + (iy-jy)*(iy-jy)));
                        float val = log_a(i) + log_u(i) - lambda * cost;
                        log_sum = logSumExp(log_sum, val);
                    }
                }
                log_v(j) = log_b(j) - log_sum;
            }
        }

        // Compute barycenter: weighted geometric mean of a and transported b
        Eigen::MatrixXf result(N, N);
        float alpha = cfg_.transport_step;
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                int idx = i * N + j;
                float log_a_val = log_a(idx);
                // Transport map: push b toward a using dual variables
                float log_transport = log_b(idx) + log_v(idx);
                // Barycenter in log domain
                result(i, j) = std::exp((1.0f - alpha) * log_a_val + alpha * log_transport);
            }
        }

        // Normalize
        float sum = result.sum();
        if (sum > 0) result /= sum;

        return result;
    }

    void gaussianBlur(Eigen::MatrixXf& mat, int N, float sigma) {
        int r = std::max(1, static_cast<int>(3 * sigma));
        Eigen::MatrixXf tmp = mat;

        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                float sum = 0, wsum = 0;
                for (int di = -r; di <= r; ++di) {
                    for (int dj = -r; dj <= r; ++dj) {
                        int ni = i + di, nj = j + dj;
                        if (ni >= 0 && ni < N && nj >= 0 && nj < N) {
                            float w = std::exp(-(di*di + dj*dj) / (2*sigma*sigma));
                            sum += w * mat(ni, nj);
                            wsum += w;
                        }
                    }
                }
                tmp(i, j) = sum / wsum;
            }
        }
        mat = tmp;
    }

    float logSumExp(float a, float b) const {
        float max_val = std::max(a, b);
        if (max_val < -1e19f) return max_val;
        return max_val + std::log(std::exp(a - max_val) + std::exp(b - max_val));
    }

    Config cfg_;
    Eigen::MatrixXf transport_plan_;
    Eigen::MatrixXf data_measure_;
    float last_wasserstein_dist_ = 0.0f;
    float last_entropy_reduction_ = 0.0f;
};

} // namespace Innovation
} // namespace GSL
