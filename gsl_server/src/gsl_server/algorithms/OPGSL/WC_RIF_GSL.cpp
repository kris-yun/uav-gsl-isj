// WC_RIF_GSL.cpp - Wind-Conditioned Robust Intermittency Filter for GSL
#include <fstream>
#include "WC_RIF_GSL.hpp"
#include "gsl_server/core/GSLResult.hpp"
#include <gsl_server/algorithms/Common/States/WaitForMapState.hpp>
#include <gsl_server/algorithms/Common/States/WaitForGasState.hpp>
#include <gsl_server/algorithms/Common/States/StopAndMeasureState.hpp>
#include "gsl_server/core/Logging.hpp"
#include "gsl_server/core/Vectors.hpp"
#include "gsl_server/algorithms/Common/Utils/Math.hpp"
#include "gsl_server/algorithms/Common/Utils/RosUtils.hpp"
#include <cmath>
#include <queue>
#include <iomanip>

namespace GSL {

WC_RIF_GSL::WC_RIF_GSL(std::shared_ptr<rclcpp::Node> _node) : Algorithm(_node) {}

void WC_RIF_GSL::declareParameters() {
    Algorithm::declareParameters();
    n_cells_ = getParam<int>("wcrif.grid.n_cells", 40);
    resolution_ = getParam<double>("wcrif.grid.resolution", 0.5);
    map_half_size_ = n_cells_ * resolution_ / 2.0f;
    sigma_base_ = getParam<double>("wcrif.sigma_base", 0.3);
    beta_wind_ = getParam<double>("wcrif.beta_wind", 0.5);
    alpha_intermittency_ = getParam<double>("wcrif.alpha_intermittency", 0.3);
    gamma_entropy_ = getParam<double>("wcrif.gamma_entropy", 0.1);
    convergence_min_time_ = getParam<double>("wcrif.convergence.min_time", 60.0);
    convergence_min_hits_ = getParam<int>("wcrif.convergence.min_hits", 10);
    wind_convention_upwind_ = getParam<bool>("wcrif.wind_convention_upwind", true);
    forward_kappa_ = getParam<float>("wcrif.forward_kappa", 0.01f);
    forward_delta_ = getParam<float>("wcrif.forward_delta", 0.1f);
    forward_alpha_ = getParam<float>("wcrif.forward_alpha", 10.0f);
    cusum_delta_ = getParam<float>("wcrif.cusum_delta", 0.005f);
    cusum_threshold_ = getParam<float>("wcrif.cusum_threshold", 0.05f);
    grid_origin_x_ = getParam<float>("wcrif.grid.origin_x", 0.0f);
    grid_origin_y_ = getParam<float>("wcrif.grid.origin_y", 0.0f);
}

void WC_RIF_GSL::Initialize() {
    int N = n_cells_;
    log_belief_ = Eigen::MatrixXf::Zero(N, N);
    log_belief_.setConstant(-std::log(float(N * N)));
    grid_x_.resize(N, N);
    grid_y_.resize(N, N);
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            grid_x_(i, j) = i * resolution_ + grid_origin_x_;
            grid_y_(i, j) = j * resolution_ + grid_origin_y_;
        }
    }

    waitForMapState = std::make_unique<WaitForMapState>(this);
    waitForGasState = std::make_unique<WaitForGasState>(this);
    stopAndMeasureState = std::make_unique<StopAndMeasureState>(this);
    movingState = std::make_unique<MovingStateWC_RIF>(this);

    Algorithm::Initialize();
    stateMachine.forceSetState(waitForMapState.get());
    visit_count_ = std::vector<std::vector<int>>(n_cells_, std::vector<int>(n_cells_, 0));
    need_next_goal_ = false;

    GSL_INFO("WC-RIF-GSL initialized: Cauchy kernel + wind-conditioned sigma + intermittency weighting");
}

void WC_RIF_GSL::OnUpdate() {
    Algorithm::OnUpdate();

    if (need_next_goal_) {
        need_next_goal_ = false;
        double now = node->now().seconds();
        if (last_update_time_ > 0) elapsed_time_ += float(now - last_update_time_);
        last_update_time_ = now;
        movingState->chooseGoalAndMove();
    }
}

void WC_RIF_GSL::OnCompleteNavigation(GSLResult result, State* previousState) {
    stateMachine.forceSetState(stopAndMeasureState.get());
}

void WC_RIF_GSL::processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection) {
    latest_gas_ = float(concentration);
    // windDirection convention: VGR gives downwind (blowing TO), GADEN gives upwind (coming FROM)
    // We need downwind direction for the plume model, so negate if upwind convention
    float wind_dir = windDirection;
    if (wind_convention_upwind_) wind_dir += M_PI; // convert upwind to downwind
    latest_wind_x_ = float(windSpeed * std::cos(wind_dir));
    latest_wind_y_ = float(windSpeed * std::sin(wind_dir));
    latest_wind_speed_ = float(windSpeed);

    // Low wind: use smoothed default
    if (std::sqrt(latest_wind_x_*latest_wind_x_ + latest_wind_y_*latest_wind_y_) < 0.05f) {
        latest_wind_x_ = 0.1f;
        latest_wind_y_ = 0.05f;
    }

    // CUSUM adaptive detection: accumulate deviations from baseline
    // More robust than fixed threshold under varying background concentrations
    cusum_sum_ = cusum_decay_ * cusum_sum_ + float(concentration) - cusum_delta_;
    cusum_sum_ = std::max(0.0f, cusum_sum_);
    bool hit = cusum_sum_ > cusum_threshold_;
    if (hit) gas_hit_count_++;
    hit_history_.push_back(hit ? 1 : 0);
    if (hit_history_.size() > kWindowSize) hit_history_.pop_front();

    // BOCPD Runlength Posterior (Adams & MacKay style)
    // Maintains K hypotheses at different runlengths, weighted by posterior
    // No thresholds, no per-dataset parameters - self-adapting
    auto geo_dist = computeGeodesicDistances(currentRobotPosition.x, currentRobotPosition.y);
    float hit_sigma = sigma_base_ * 3.0f;
    float miss_sigma = 1.0f;

    // Forward model belief update: analysis-by-synthesis
    // Compute predicted concentration at sensor for each candidate source
    // using advection-diffusion forward model, then update belief
    if (!forward_model_initialized_ || latest_wind_speed_ > 0.01f) {
        initForwardModel(); // rebuild when wind changes
    }

    // Find sensor grid position
    int si = int((currentRobotPosition.x - grid_origin_x_) / resolution_);
    int sj = int((currentRobotPosition.y - grid_origin_y_) / resolution_);
    si = std::max(0, std::min(n_cells_ - 1, si));
    sj = std::max(0, std::min(n_cells_ - 1, sj));
    int obs_idx = si * n_cells_ + sj;

    // Solve adjoint: g[s] = predicted concentration at sensor when source at s
    Eigen::VectorXf g = solveAdjoint(forward_L_, obs_idx);

    Eigen::MatrixXf obs_like(n_cells_, n_cells_);
    for (int i = 0; i < n_cells_; ++i) {
        for (int j = 0; j < n_cells_; ++j) {
            int sidx = i * n_cells_ + j;
            float pred_conc = std::max(g(sidx), 0.0f);

            if (hit) {
                // p(hit | source at s) = 1 - exp(-alpha * predicted_concentration)
                float p = 1.0f - std::exp(-forward_alpha_ * pred_conc);
                obs_like(i, j) = std::max(p, 1e-10f);
            } else {
                // p(void | source at s) = exp(-alpha * predicted_concentration)
                float p = std::exp(-forward_alpha_ * pred_conc);
                obs_like(i, j) = std::max(p, 1e-10f);
            }
        }
    }

    // Initialize BOCPD on first call
    if (bocpd_beliefs_.empty()) {
        bocpd_beliefs_.resize(kRMax + 1);
        bocpd_weights_.resize(kRMax + 1, 0.0f);
        for (int r = 0; r <= kRMax; ++r) {
            bocpd_beliefs_[r] = Eigen::MatrixXf::Constant(n_cells_, n_cells_, -std::log(float(n_cells_ * n_cells_)));
        }
        bocpd_weights_[0] = 1.0f; // start with r=0 (just reset)
    }

    // Step 1: Compute predictive probability for each runlength
    std::vector<float> pred_prob(kRMax + 1, 0.0f);
    for (int r = 0; r <= kRMax; ++r) {
        if (bocpd_weights_[r] < 1e-12f) continue;
        // sum_s b_r(s) * obs_like(s)
        float log_sum = -1e10f;
        for (int i = 0; i < n_cells_; ++i) {
            for (int j = 0; j < n_cells_; ++j) {
                float log_val = bocpd_beliefs_[r](i, j) + std::log(obs_like(i, j));
                log_sum = std::max(log_sum, log_val);
            }
        }
        // LogSumExp for numerical stability
        float sum_exp = 0.0f;
        for (int i = 0; i < n_cells_; ++i) {
            for (int j = 0; j < n_cells_; ++j) {
                float log_val = bocpd_beliefs_[r](i, j) + std::log(obs_like(i, j));
                sum_exp += std::exp(log_val - log_sum);
            }
        }
        pred_prob[r] = bocpd_weights_[r] * std::exp(log_sum + std::log(sum_exp));
    }

    // Step 2: Grow runlengths (r -> r+1) and spawn new r=0
    std::vector<float> new_weights(kRMax + 1, 0.0f);
    std::vector<Eigen::MatrixXf> new_beliefs(kRMax + 1);

    // r=0 branch: reset to uniform prior * obs_like
    new_beliefs[0] = Eigen::MatrixXf::Constant(n_cells_, n_cells_, -std::log(float(n_cells_ * n_cells_)));
    float r0_sum = 0.0f;
    for (int i = 0; i < n_cells_; ++i)
        for (int j = 0; j < n_cells_; ++j) {
            new_beliefs[0](i, j) += std::log(obs_like(i, j));
            r0_sum += std::exp(new_beliefs[0](i, j));
        }
    new_beliefs[0].array() -= std::log(r0_sum);
    float total_pred = 0.0f;
    for (float p : pred_prob) total_pred += p;

    // Dilution fix: boost r=0 when hit is far from current MAP
    // This makes BOCPD respond faster to new evidence in unexplored areas
    float est_x, est_y;
    getMAP(est_x, est_y);
    float dx_hit = currentRobotPosition.x - est_x;
    float dy_hit = currentRobotPosition.y - est_y;
    float dist_from_map = std::sqrt(dx_hit*dx_hit + dy_hit*dy_hit);
    float boost = 1.0f;
    if (hit && dist_from_map > 2.0f) {
        // Hit far from MAP: strong evidence of regime change, boost r=0
        boost = 1.0f + 3.0f * (dist_from_map - 2.0f) / 5.0f; // up to 4x boost
        boost = std::min(boost, 5.0f);
        GSL_INFO("BOCPD dilution fix: hit at dist={:.1f} from MAP, r=0 boost={:.1f}", dist_from_map, boost);
    }
    new_weights[0] = total_pred * bocpd_hazard_ * boost;

    // Growth branches: r -> r+1
    for (int r = 0; r < kRMax; ++r) {
        if (bocpd_weights_[r] < 1e-12f) continue;
        new_beliefs[r + 1] = bocpd_beliefs_[r];
        for (int i = 0; i < n_cells_; ++i)
            for (int j = 0; j < n_cells_; ++j)
                new_beliefs[r + 1](i, j) += std::log(obs_like(i, j));
        // Normalize
        float s = 0.0f;
        for (int i = 0; i < n_cells_; ++i)
            for (int j = 0; j < n_cells_; ++j)
                s += std::exp(new_beliefs[r + 1](i, j));
        new_beliefs[r + 1].array() -= std::log(s + 1e-10f);
        new_weights[r + 1] = pred_prob[r] * (1.0f - bocpd_hazard_);
    }

    // Step 3: Normalize weights
    float w_sum = 0.0f;
    for (float w : new_weights) w_sum += w;
    for (float& w : new_weights) w /= (w_sum + 1e-10f);

    // Step 4: Compute model-averaged belief
    log_belief_.setConstant(0.0f);
    for (int r = 0; r <= kRMax; ++r) {
        if (new_weights[r] < 1e-12f) continue;
        for (int i = 0; i < n_cells_; ++i)
            for (int j = 0; j < n_cells_; ++j)
                log_belief_(i, j) += new_weights[r] * std::exp(new_beliefs[r](i, j));
    }
    // Convert back to log space
    for (int i = 0; i < n_cells_; ++i)
        for (int j = 0; j < n_cells_; ++j)
            log_belief_(i, j) = std::log(std::max(log_belief_(i, j), 1e-10f));

    // Diagnostic: log per-branch MAP when robot is in source area (Y > 3)
    if (currentRobotPosition.y > 3.0f) {
        for (int r = 0; r <= kRMax; ++r) {
            if (new_weights[r] < 0.01f) continue; // only log significant branches
            float br_best = -1e10f; int br_i = 0, br_j = 0;
            for (int i = 0; i < n_cells_; ++i)
                for (int j = 0; j < n_cells_; ++j)
                    if (new_beliefs[r](i, j) > br_best) { br_best = new_beliefs[r](i, j); br_i = i; br_j = j; }
            GSL_INFO("BOCPD branch r={} weight={:.3f} MAP=({:.2f},{:.2f})", r, new_weights[r],
                     grid_x_(br_i, br_j), grid_y_(br_i, br_j));
        }
    }

    // Update state
    bocpd_beliefs_ = new_beliefs;
    bocpd_weights_ = new_weights;

    normalize();
    updateProximityResults();

    // Update visit count for current cell
    int vi = int((currentRobotPosition.x - grid_origin_x_) / resolution_);
    int vj = int((currentRobotPosition.y - grid_origin_y_) / resolution_);
    if (vi >= 0 && vi < n_cells_ && vj >= 0 && vj < n_cells_) {
        visit_count_[vi][vj]++;
    }

    need_next_goal_ = true;
    step_count_++;
}

// Compute geodesic distances from (ox, oy) to all grid cells via BFS through free space
std::vector<std::vector<float>> WC_RIF_GSL::computeGeodesicDistances(float ox, float oy) {
    std::vector<std::vector<float>> dist(n_cells_, std::vector<float>(n_cells_, 1e6f));
    std::vector<std::vector<bool>> visited(n_cells_, std::vector<bool>(n_cells_, false));

    int si = int((ox - grid_origin_x_) / resolution_);
    int sj = int((oy - grid_origin_y_) / resolution_);
    si = std::max(0, std::min(n_cells_ - 1, si));
    sj = std::max(0, std::min(n_cells_ - 1, sj));

    // Check if origin cell is free
    Vector2 origin_pos(grid_x_(si, sj), grid_y_(si, sj));
    if (!isPointInsideMapBounds(origin_pos) || !isPointFree(origin_pos)) {
        return dist; // return all large distances
    }

    // BFS queue: (i, j, distance)
    std::queue<std::tuple<int,int,float>> bfs;
    bfs.push({si, sj, 0.0f});
    visited[si][sj] = true;
    dist[si][sj] = 0.0f;

    while (!bfs.empty()) {
        auto [ci, cj, cd] = bfs.front();
        bfs.pop();

        // 8-connected neighbors
        for (int di = -1; di <= 1; di++) {
            for (int dj = -1; dj <= 1; dj++) {
                if (di == 0 && dj == 0) continue;
                int ni = ci + di;
                int nj = cj + dj;
                if (ni < 0 || ni >= n_cells_ || nj < 0 || nj >= n_cells_) continue;
                if (visited[ni][nj]) continue;

                float nx = grid_x_(ni, nj);
                float ny = grid_y_(ni, nj);
                Vector2 npos(nx, ny);
                if (!isPointInsideMapBounds(npos) || !isPointFree(npos)) continue;

                float step = (di != 0 && dj != 0) ? 1.414f * resolution_ : resolution_;
                float nd = cd + step;
                if (nd < 6.0f) { // limit search radius to 6m
                    visited[ni][nj] = true;
                    dist[ni][nj] = nd;
                    bfs.push({ni, nj, nd});
                }
            }
        }
    }
    return dist;
}


void WC_RIF_GSL::initForwardModel() {
    // Build advection-diffusion operator L on free cells
    // L = -kappa * laplacian + div(u*) + delta * I
    int N = n_cells_ * n_cells_;
    std::vector<Eigen::Triplet<float>> triplets;
    float h2 = resolution_ * resolution_;
    float kappa = forward_kappa_;
    float delta = forward_delta_;

    for (int i = 0; i < n_cells_; ++i) {
        for (int j = 0; j < n_cells_; ++j) {
            int idx = i * n_cells_ + j;
            Vector2 cell_pos(grid_x_(i, j), grid_y_(i, j));
            if (!isPointInsideMapBounds(cell_pos) || !isPointFree(cell_pos)) {
                // Obstacle cell: identity (concentration = 0)
                triplets.push_back(Eigen::Triplet<float>(idx, idx, 1.0f));
                continue;
            }

            int degree = 0;
            float adv_out = 0.0f;

            for (int di = -1; di <= 1; di++) {
                for (int dj = -1; dj <= 1; dj++) {
                    if (di == 0 && dj == 0) continue;
                    if (di != 0 && dj != 0) continue; // 4-connected
                    int ni = i + di, nj = j + dj;
                    if (ni < 0 || ni >= n_cells_ || nj < 0 || nj >= n_cells_) continue;
                    Vector2 npos(grid_x_(ni, nj), grid_y_(ni, nj));
                    if (!isPointInsideMapBounds(npos) || !isPointFree(npos)) continue;

                    degree++;
                    int nidx = ni * n_cells_ + nj;
                    // Diffusion
                    triplets.push_back(Eigen::Triplet<float>(idx, nidx, -kappa / h2));
                    // Advection (upwind)
                    float adv = (latest_wind_x_ * di + latest_wind_y_ * dj) / (2.0f * resolution_);
                    if (adv > 0) {
                        triplets.push_back(Eigen::Triplet<float>(idx, nidx, -adv));
                        adv_out += adv;
                    }
                }
            }
            // Diagonal
            triplets.push_back(Eigen::Triplet<float>(idx, idx, delta + kappa * degree / h2 + adv_out));
        }
    }

    forward_L_.resize(N, N);
    forward_L_.setFromTriplets(triplets.begin(), triplets.end());
    forward_model_initialized_ = true;
    GSL_INFO("Forward model initialized: {}x{} operator", N, N);
}

Eigen::VectorXf WC_RIF_GSL::solveAdjoint(const Eigen::SparseMatrix<float>& L, int obs_idx) {
    // Solve L^T * g = delta_{obs_idx}
    // g[s] = predicted concentration at obs position when source is at s
    int N = L.rows();
    Eigen::VectorXf rhs = Eigen::VectorXf::Zero(N);
    rhs(obs_idx) = 1.0f;

    // Use sparse LU decomposition
    Eigen::SparseMatrix<float> LT = L.transpose();
    Eigen::SparseLU<Eigen::SparseMatrix<float>> solver;
    solver.compute(LT);
    if (solver.info() != Eigen::Success) {
        GSL_ERROR("Adjoint LU decomposition failed");
        return Eigen::VectorXf::Zero(N);
    }
    Eigen::VectorXf g = solver.solve(rhs);
    // Clamp negative values (numerical artifacts)
    for (int i = 0; i < N; i++) {
        if (g(i) < 0) g(i) = 0;
    }
    return g;
}
GSLResult WC_RIF_GSL::checkSourceFound() {
    // Use wall time for timeout (not elapsed_time_ which depends on state machine)
    double wall_elapsed = (node->now() - startTime).seconds();
    if (wall_elapsed >= resultLogging.maxSearchTime) {
        float est_x, est_y;
        getMAP(est_x, est_y);
        float Ax = est_x - resultLogging.sourcePositionGT.x;
        float Ay = est_y - resultLogging.sourcePositionGT.y;
        float err = std::sqrt(Ax*Ax + Ay*Ay);
        GSL_INFO("WC-RIF timeout: MAP=({:.2f},{:.2f}) error={:.2f} hits={} wall_t={:.1f}", est_x, est_y, err, gas_hit_count_, wall_elapsed);
        currentResult = (err < 1.0f) ? GSLResult::Success : GSLResult::Failure;
        saveResultsToFile(currentResult);
        return currentResult;
    }

    // Adaptive convergence: MAP stability check
    {
        float est_x, est_y;
        getMAP(est_x, est_y);
        map_history_.push_back({est_x, est_y});
        if (map_history_.size() > (size_t)stability_window_) map_history_.pop_front();

        if (map_history_.size() >= (size_t)stability_window_ && gas_hit_count_ >= convergence_min_hits_) {
            float max_movement = 0.0f;
            for (size_t i = 1; i < map_history_.size(); ++i) {
                float dx_m = map_history_[i].first - map_history_[i-1].first;
                float dy_m = map_history_[i].second - map_history_[i-1].second;
                float movement = std::sqrt(dx_m*dx_m + dy_m*dy_m);
                max_movement = std::max(max_movement, movement);
            }
            if (max_movement < stability_threshold_) {
                // MAP is stable - report final estimate, no premature convergence
                GSL_INFO("WC-RIF MAP stable: MAP=({:.2f},{:.2f}) max_move={:.3f} hits={} elapsed={:.1f}",
                        est_x, est_y, max_movement, gas_hit_count_, elapsed_time_);
            }
        }
    }
    return GSLResult::Running;
}

void WC_RIF_GSL::saveResultsToFile(GSLResult result) {
    // Use MAP error for the RESULT IS line, not robot-to-source distance
    float est_x, est_y;
    getMAP(est_x, est_y);
    float Ax = est_x - resultLogging.sourcePositionGT.x;
    float Ay = est_y - resultLogging.sourcePositionGT.y;
    float map_err = std::sqrt(Ax*Ax + Ay*Ay);

    GSLResult map_result = (map_err < 1.0f) ? GSLResult::Success : GSLResult::Failure;
    currentResult = map_result;

    double search_t = (node->now() - startTime).seconds();
    std::string result_string = fmt::format("RESULT IS: Success={}, Search_d=0, Nav_d={:.2}, Search_t={:.2}, Nav_t=0",
        (int)map_result, map_err, search_t);
    GSL_INFO("{}", result_string);

    updateProximityResults(true);
    std::ofstream output_file(resultLogging.resultsFile, std::ios_base::app);
    if (output_file.is_open()) {
        output_file << "---------------------------------------------------\n";
        for (const auto& prox : resultLogging.proximityResult)
            output_file << prox.time << " " << prox.distance << "\n";
        output_file.close();
    }
}

// ========== Internal Methods ==========

float WC_RIF_GSL::computeHitProbability(float sx, float sy, float sensor_x, float sensor_y, float wx, float wy) const {
    // Robust hit probability: distance decay + wind upwind bias
    // Does not depend on Gaussian plume model (fails with obstacles)
    float dx = sensor_x - sx;
    float dy = sensor_y - sy;
    float dist = std::sqrt(dx*dx + dy*dy) + 0.01f;

    // Distance decay: closer cells get higher base probability
    float p_dist = std::exp(-dist * dist / (2.0f * 4.0f * 4.0f)); // sigma=4m

    // Wind upwind bias: source is likely upwind of sensor
    float ws = std::sqrt(wx*wx + wy*wy) + 1e-6f;
    float wnx = wx / ws;
    float wny = wy / ws;
    // dx,dy points from source_candidate to sensor
    // upwind means source is against wind direction
    float upwind_alignment = (dx * wnx + dy * wny) / dist; // positive when source is upwind
    float p_wind = 0.5f + 0.5f * std::max(upwind_alignment, 0.0f); // 0.5 to 1.0

    float p = p_dist * p_wind;
    return std::min(std::max(p, 0.01f), 0.99f);
}

float WC_RIF_GSL::computeWindAlignment(float sx, float sy, float sensor_x, float sensor_y, float wx, float wy) const {
    float dx = sensor_x - sx;
    float dy = sensor_y - sy;
    float dist = std::sqrt(dx*dx + dy*dy) + 0.01f;
    float ws = std::sqrt(wx*wx + wy*wy) + 1e-6f;
    return (dx * wx + dy * wy) / (dist * ws);
}

float WC_RIF_GSL::cauchyKernel(float d, float sigma) const {
    return 1.0f / (M_PI * (1.0f + (d/sigma) * (d/sigma)));
}

float WC_RIF_GSL::computeHitRate() const {
    if (hit_history_.empty()) return 0.0f;
    int sum = 0;
    for (int h : hit_history_) sum += h;
    return float(sum) / hit_history_.size();
}

float WC_RIF_GSL::entropy() const {
    float H = 0.0f;
    Eigen::ArrayXXf p = log_belief_.array().exp();
    p /= p.sum();
    H = -(p * log_belief_.array()).sum();
    return H;
}

void WC_RIF_GSL::normalize() {
    float max_log = log_belief_.maxCoeff();
    log_belief_.array() -= max_log;
    float log_sum = std::log(log_belief_.array().exp().sum());
    log_belief_.array() -= log_sum;
}

void WC_RIF_GSL::getMAP(float& x, float& y) const {
    int best_i = 0, best_j = 0;
    float best_val = log_belief_(0, 0);
    for (int i = 0; i < n_cells_; ++i) {
        for (int j = 0; j < n_cells_; ++j) {
            if (log_belief_(i, j) > best_val) {
                best_val = log_belief_(i, j);
                best_i = i; best_j = j;
            }
        }
    }
    x = grid_x_(best_i, best_j);
    y = grid_y_(best_i, best_j);
}

void WC_RIF_GSL::clipToMapBounds(float& x, float& y) const {
    float m = 0.5f;
    x = std::max(grid_origin_x_ + m, std::min(grid_origin_x_ + n_cells_ * resolution_ - m, x));
    y = std::max(grid_origin_y_ + m, std::min(grid_origin_y_ + n_cells_ * resolution_ - m, y));
}

void WC_RIF_GSL::exploreStep(float& tx, float& ty) {
    // Wind-relative golden angle exploration
    float wind_norm = std::sqrt(latest_wind_x_*latest_wind_x_ + latest_wind_y_*latest_wind_y_) + 1e-6f;
    float wx = latest_wind_x_ / wind_norm;
    float wy = latest_wind_y_ / wind_norm;
    float golden_angle = 2.39996f;
    float angle = golden_angle * step_count_;
    float base_angle = std::atan2(-wy, -wx);
    float explore_angle = base_angle + angle;
    tx = currentRobotPosition.x + 0.8f * std::cos(explore_angle);
    ty = currentRobotPosition.y + 0.8f * std::sin(explore_angle);
    clipToMapBounds(tx, ty);
}

// ========== MovingState ==========

MovingStateWC_RIF::MovingStateWC_RIF(Algorithm* _algorithm) : MovingState(_algorithm) {
    wcrif_ = dynamic_cast<WC_RIF_GSL*>(_algorithm);
}

NavigateToPose::Goal MovingStateWC_RIF::posToGoal(float x, float y) {
    NavigateToPose::Goal g;
    g.pose.header.frame_id = "map";
    g.pose.header.stamp = wcrif_->node->now();
    g.pose.pose.position.x = x;
    g.pose.pose.position.y = y;
    g.pose.pose.position.z = 1.0f;
    g.pose.pose.orientation.w = 1.0f;
    return g;
}

void MovingStateWC_RIF::chooseGoalAndMove() {
    if (!wcrif_) { GSL_ERROR("WC_RIF_GSL pointer null"); return; }

    wcrif_->step_count_++;
    double now = wcrif_->node->now().seconds();
    if (wcrif_->last_update_time_ > 0)
        wcrif_->elapsed_time_ += float(now - wcrif_->last_update_time_);
    wcrif_->last_update_time_ = now;

    float tx, ty;

    // Two-phase exploration: Phase 1 random coverage, Phase 2 entropy + MAP
    bool use_entropy = (wcrif_->gas_hit_count_ >= 5 && wcrif_->step_count_ >= 50);

    if (!use_entropy) {
        // Phase 1: wind-relative golden angle exploration (broad coverage)
        wcrif_->exploreStep(tx, ty);
        float edx = tx - wcrif_->currentRobotPosition.x;
        float edy = ty - wcrif_->currentRobotPosition.y;
        float ed = std::sqrt(edx*edx + edy*edy) + 0.01f;
        float big_step = 0.8f;
        tx = wcrif_->currentRobotPosition.x + (edx/ed) * big_step;
        ty = wcrif_->currentRobotPosition.y + (edy/ed) * big_step;
    } else {
        // Phase 2: MAP navigation + upwind bias (exploitation)
        float est_x, est_y;
        wcrif_->getMAP(est_x, est_y);

        float dx_map = est_x - wcrif_->currentRobotPosition.x;
        float dy_map = est_y - wcrif_->currentRobotPosition.y;
        float dist_map = std::sqrt(dx_map*dx_map + dy_map*dy_map) + 0.01f;

        float wind_norm = std::sqrt(wcrif_->latest_wind_x_*wcrif_->latest_wind_x_ +
                                     wcrif_->latest_wind_y_*wcrif_->latest_wind_y_) + 1e-6f;
        float upwind_x = -wcrif_->latest_wind_x_ / wind_norm;
        float upwind_y = -wcrif_->latest_wind_y_ / wind_norm;

        float H = wcrif_->entropy();
        float H_max = std::log(float(wcrif_->n_cells_ * wcrif_->n_cells_));
        float exploration = std::min(H / H_max, 1.0f);

        float map_weight = 0.7f;
        float upwind_weight = 0.3f * exploration;

        float dir_x = map_weight * (dx_map / dist_map) + upwind_weight * upwind_x;
        float dir_y = map_weight * (dy_map / dist_map) + upwind_weight * upwind_y;
        float dir_norm = std::sqrt(dir_x*dir_x + dir_y*dir_y) + 1e-6f;
        dir_x /= dir_norm;
        dir_y /= dir_norm;

        float step;
        if (dist_map > 3.0f) step = std::min(dist_map * 0.6f, 2.0f);
        else if (dist_map > 1.0f) step = std::min(dist_map * 0.5f, 1.2f);
        else step = std::max(dist_map * 0.3f, 0.3f);

        tx = wcrif_->currentRobotPosition.x + step * dir_x;
        ty = wcrif_->currentRobotPosition.y + step * dir_y;
    }
    wcrif_->clipToMapBounds(tx, ty);

    GSL_INFO("WC-RIF step={} target=({:.2f},{:.2f}) hits={} H={:.1f} elapsed={:.1f}",
            wcrif_->step_count_, tx, ty, wcrif_->gas_hit_count_, wcrif_->entropy(), wcrif_->elapsed_time_);

    // Navigate
    auto goal = posToGoal(tx, ty);
    if (checkGoal(goal)) { sendGoal(goal); return; }

    // Fallback 1: shorter step, checking costmap
    float dx = tx - wcrif_->currentRobotPosition.x;
    float dy = ty - wcrif_->currentRobotPosition.y;
    float d = std::sqrt(dx*dx + dy*dy);
    if (d > 0.1f) {
        float dirx = dx/d, diry = dy/d;
        for (float f : {0.75f, 0.5f, 0.3f, 0.15f}) {
            float fx = wcrif_->currentRobotPosition.x + dirx * d * f;
            float fy = wcrif_->currentRobotPosition.y + diry * d * f;
            Vector2 fp(fx, fy);
            if (!wcrif_->isPointFree(fp)) continue;
            wcrif_->clipToMapBounds(fx, fy);
            auto fg = posToGoal(fx, fy);
            if (checkGoal(fg)) { sendGoal(fg); return; }
        }
    }

    // Fallback 2: scan nearby free cells on costmap
    {
        float best_dist = 1e9f;
        float best_x = wcrif_->currentRobotPosition.x, best_y = wcrif_->currentRobotPosition.y;
        float scan_radius = 1.5f;
        float step_size = 0.3f;
        for (float sx = -scan_radius; sx <= scan_radius; sx += step_size) {
            for (float sy = -scan_radius; sy <= scan_radius; sy += step_size) {
                float cx = wcrif_->currentRobotPosition.x + sx;
                float cy = wcrif_->currentRobotPosition.y + sy;
                Vector2 cp(cx, cy);
                if (!wcrif_->isPointFree(cp)) continue;
                float dd = sx*sx + sy*sy;
                if (dd < best_dist) { best_dist = dd; best_x = cx; best_y = cy; }
            }
        }
        if (best_dist < 1e8f) {
            auto fg = posToGoal(best_x, best_y);
            if (checkGoal(fg)) { sendGoal(fg); return; }
        }
    }

    // Fallback 3: use getRandomPoseInMap (costmap-aware)
    {
        auto rp = wcrif_->getRandomPoseInMap();
        auto rg = posToGoal(rp.pose.position.x, rp.pose.position.y);
        if (checkGoal(rg)) { sendGoal(rg); return; }
    }

    GSL_WARN("WCRIF ALL fallbacks failed - staying put");
}

void MovingStateWC_RIF::Fail() {
    if (!wcrif_) return;
    std::mt19937 rng(std::random_device{}());
    float ang = std::uniform_real_distribution<float>(0, 2*M_PI)(rng);
    float nx = wcrif_->currentRobotPosition.x + 1.5f * std::cos(ang);
    float ny = wcrif_->currentRobotPosition.y + 1.5f * std::sin(ang);
    wcrif_->clipToMapBounds(nx, ny);
    auto goal = posToGoal(nx, ny);
    if (checkGoal(goal)) sendGoal(goal);
}

} // namespace GSL
