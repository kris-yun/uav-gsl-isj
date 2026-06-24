#include "OPGSL.hpp"
#include "gsl_server/core/GSLResult.hpp"
#include <gsl_server/algorithms/Common/States/WaitForMapState.hpp>
#include <gsl_server/algorithms/Common/States/WaitForGasState.hpp>
#include <gsl_server/algorithms/Common/States/StopAndMeasureState.hpp>
#include "gsl_server/core/Logging.hpp"
#include "gsl_server/core/Vectors.hpp"
#include "gsl_server/algorithms/Common/Utils/Math.hpp"
#include "gsl_server/algorithms/Common/Utils/RosUtils.hpp"
#include <angles/angles.h>
#include <cmath>
#include <iomanip>
#include <limits>
#include <numeric>

namespace GSL {

void GridPosteriorOP::init(const Config& cfg) {
    cfg_ = cfg;
    int N = cfg.n_cells;
    log_posterior_.resize(N, N);
    log_posterior_.setConstant(-std::log(float(N * N)));
    grid_x_.resize(N, N);
    grid_y_.resize(N, N);
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            grid_x_(i, j) = i * cfg.resolution - cfg.map_half_size;
            grid_y_(i, j) = j * cfg.resolution - cfg.map_half_size;
        }
    }
}

int GridPosteriorOP::posToGridX(float x) const {
    int g = static_cast<int>((x + cfg_.map_half_size) / cfg_.resolution);
    return std::max(0, std::min(g, cfg_.n_cells - 1));
}

int GridPosteriorOP::posToGridY(float y) const {
    int g = static_cast<int>((y + cfg_.map_half_size) / cfg_.resolution);
    return std::max(0, std::min(g, cfg_.n_cells - 1));
}

void GridPosteriorOP::gridToPos(int gx, int gy, float& px, float& py) const {
    px = gx * cfg_.resolution - cfg_.map_half_size;
    py = gy * cfg_.resolution - cfg_.map_half_size;
}

void GridPosteriorOP::getEstimate(float& ex, float& ey) const {
    int best_i = 0, best_j = 0;
    float best_val = log_posterior_(0, 0);
    int N = cfg_.n_cells;
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            if (log_posterior_(i, j) > best_val) {
                best_val = log_posterior_(i, j);
                best_i = i;
                best_j = j;
            }
        }
    }
    gridToPos(best_i, best_j, ex, ey);
}

void GridPosteriorOP::normalize() {
    float max_log = log_posterior_.maxCoeff();
    log_posterior_.array() -= max_log;
    float log_sum = std::log(log_posterior_.array().exp().sum());
    log_posterior_.array() -= log_sum;
}

void GridPosteriorOP::update(float gas_reading, float robot_x, float robot_y,
                              float wind_x, float wind_y) {
    int N = cfg_.n_cells;
    float wind_speed = std::sqrt(wind_x * wind_x + wind_y * wind_y);
    float wind_dir = std::atan2(wind_y, wind_x);
    int r = std::max(1, static_cast<int>(cfg_.sense_radius_m / cfg_.resolution));
    int cx = posToGridX(robot_x);
    int cy = posToGridY(robot_y);
    int sx_min = std::max(0, cx - r);
    int sx_max = std::min(N - 1, cx + r);
    int sy_min = std::max(0, cy - r);
    int sy_max = std::min(N - 1, cy + r);
    int rows = sx_max - sx_min + 1;
    int cols = sy_max - sy_min + 1;

    // Use concrete ArrayXXf to avoid expression template issues
    Eigen::ArrayXXf dx = grid_x_.block(sx_min, sy_min, rows, cols).array() - robot_x;
    Eigen::ArrayXXf dy = grid_y_.block(sx_min, sy_min, rows, cols).array() - robot_y;
    Eigen::ArrayXXf dist = (dx.square() + dy.square() + 0.01f).sqrt();

    float cos_w = std::cos(wind_dir);
    float sin_w = std::sin(wind_dir);
    Eigen::ArrayXXf x_wind = dx * cos_w + dy * sin_w;
    Eigen::ArrayXXf y_wind = -dx * sin_w + dy * cos_w;
    Eigen::ArrayXXf x_pos = x_wind.max(0.01f);
    Eigen::ArrayXXf sigma_y = (cfg_.sigma_y_a * x_pos.pow(cfg_.sigma_y_b)).max(0.1f);
    Eigen::ArrayXXf sigma_z = (cfg_.sigma_z_a * x_pos.pow(cfg_.sigma_z_b)).max(0.05f);

    float u = std::max(wind_speed, cfg_.min_wind_speed);

    // Z-term: account for UAV height above source
    float dz = cfg_.uav_height_z - cfg_.source_height_z;
    Eigen::ArrayXXf z_penalty = (dz * dz) / (2.0f * sigma_z.square() + 0.01f);
    Eigen::ArrayXXf log_C = std::log(cfg_.source_rate_Q)
               - (2.0f * 3.14159f * sigma_y * sigma_z * u).log()
               - (y_wind.square() / (2.0f * sigma_y.square()))
               - z_penalty;
    // Upwind/downwind mask: softer penalty for upwind cells
    // Low wind speed -> more isotropic (less upwind penalty)
    float upwind_weight = 0.15f + 0.25f * std::exp(-wind_speed * 5.0f);
    Eigen::ArrayXXf downwind = (x_wind > 0).cast<float>();
    log_C = log_C + (downwind * (1.0f - upwind_weight) + upwind_weight).log();

    // Gaussian log-likelihood for continuous concentration (not Poisson)
    Eigen::ArrayXXf C_pred = log_C.exp().max(1e-10f);
    Eigen::ArrayXXf log_lik;
    if (gas_reading > cfg_.detection_threshold) {
        // Log-normal likelihood: log(gas) ~ N(log(C_pred), sigma_obs^2)
        float log_gas = std::log(gas_reading + 1e-6f);
        Eigen::ArrayXXf log_C_arr = C_pred.max(1e-10f).log();
        float sigma_obs = 0.5f;  // observation noise in log-space
        Eigen::ArrayXXf residual = log_gas - log_C_arr;
        log_lik = -0.5f * residual.square() / (sigma_obs * sigma_obs);
        // Slight distance penalty to prefer nearer sources
        log_lik -= 0.02f * dist;
    } else {
        // No gas detected: slight negative evidence
        log_lik = -0.05f * C_pred;
    }
    log_posterior_.block(sx_min, sy_min, rows, cols) += log_lik.matrix();
    normalize();
}

float GridPosteriorOP::entropy() const {
    Eigen::ArrayXXf p = log_posterior_.array().exp();
    p /= p.sum();
    return -(p * log_posterior_.array()).sum();
}

float GridPosteriorOP::covarianceTrace() const {
    float ex, ey;
    getEstimate(ex, ey);
    Eigen::ArrayXXf p = log_posterior_.array().exp();
    p /= p.sum();
    float var_x = 0, var_y = 0;
    int N = cfg_.n_cells;
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            float px = grid_x_(i, j) - ex;
            float py = grid_y_(i, j) - ey;
            float w = p(i, j);
            var_x += w * px * px;
            var_y += w * py * py;
        }
    }
    return var_x + var_y;
}

void OPSolverOP::init(const Config& cfg) { cfg_ = cfg; }

float OPSolverOP::informationGain(const GridPosteriorOP& posterior,
                                   int gx, int gy,
                                   float robot_x, float robot_y) const {
    float px, py;
    posterior.gridToPos(gx, gy, px, py);
    float dx = px - robot_x;
    float dy = py - robot_y;
    float dist = std::sqrt(dx * dx + dy * dy) + 0.1f;
    const auto& lp = posterior.logPosterior();
    float p = std::exp(lp(gx, gy));
    // Variance-weighted information gain: p*(1-p) peaks at p=0.5 (maximum uncertainty)
    // This encourages exploration of uncertain regions, not just high-posterior regions
    float ig = p * (1.0f - p) / (1.0f + 0.3f * dist);
    // Add bonus for high-posterior cells to maintain exploitation
    ig += 0.3f * p / (1.0f + 0.5f * dist);
    return ig;
}

OPSolverOP::Path OPSolverOP::solve(const GridPosteriorOP& posterior,
                                    float cur_x, float cur_y,
                                    float remaining_time,
                                    const std::set<std::pair<int,int>>& visited) {
    Path result;
    int N = posterior.nCells();
    float budget = remaining_time * cfg_.uav_speed;

    struct Cand { int gx, gy; float ig; };
    std::vector<Cand> candidates;
    int search_r = std::min(15, N / 4);
    int cx = posterior.posToGridX(cur_x);
    int cy = posterior.posToGridY(cur_y);

    for (int ddx = -search_r; ddx <= search_r; ++ddx) {
        for (int ddy = -search_r; ddy <= search_r; ++ddy) {
            int gx = cx + ddx;
            int gy = cy + ddy;
            if (gx < 0 || gx >= N || gy < 0 || gy >= N) continue;
            float d = std::sqrt(float(ddx * ddx + ddy * ddy)) * 1.0f;
            if (d > budget || d < 0.5f) continue;
            float ig = informationGain(posterior, gx, gy, cur_x, cur_y);
            if (visited.find({gx, gy}) == visited.end())
                ig *= (1.0f + cfg_.exploration_bonus);
            candidates.push_back({gx, gy, ig});
        }
    }

    std::sort(candidates.begin(), candidates.end(),
              [](const Cand& a, const Cand& b) { return a.ig > b.ig; });
    int K = std::min(static_cast<int>(candidates.size()), cfg_.max_waypoints * 3);
    candidates.resize(K);

    std::set<std::pair<int,int>> used;
    float pos_x = cur_x, pos_y = cur_y;
    float remaining = budget;

    for (int iter = 0; iter < cfg_.max_waypoints && !candidates.empty(); ++iter) {
        float best_ratio = -1.0f;
        int best_idx = -1;
        for (int i = 0; i < static_cast<int>(candidates.size()); ++i) {
            auto& c = candidates[i];
            if (used.count({c.gx, c.gy})) continue;
            float wpx, wpy;
            posterior.gridToPos(c.gx, c.gy, wpx, wpy);
            float travel = std::sqrt((wpx - pos_x) * (wpx - pos_x) +
                                     (wpy - pos_y) * (wpy - pos_y));
            if (travel > remaining || travel < 0.1f) continue;
            float ratio = c.ig / travel;
            if (ratio > best_ratio) { best_ratio = ratio; best_idx = i; }
        }
        if (best_idx < 0) break;
        auto& best = candidates[best_idx];
        float wpx, wpy;
        posterior.gridToPos(best.gx, best.gy, wpx, wpy);
        result.waypoints.push_back({wpx, wpy});
        result.total_reward += best.ig;
        float travel = std::sqrt((wpx - pos_x) * (wpx - pos_x) +
                                 (wpy - pos_y) * (wpy - pos_y));
        result.total_cost += travel / cfg_.uav_speed;
        used.insert({best.gx, best.gy});
        pos_x = wpx;
        pos_y = wpy;
        remaining -= travel;
    }
    return result;
}

void OPSolverOP::infotaxisStep(const GridPosteriorOP& posterior,
                                float robot_x, float robot_y,
                                float wind_x, float wind_y,
                                float& best_x, float& best_y) {
    // Step size scales with grid resolution
    float step = std::max(cfg_.sense_radius_m * 0.3f, 2.0f);
    const float dirs[9][2] = {{1,0},{-1,0},{0,1},{0,-1},{1,1},{1,-1},{-1,1},{-1,-1},{0,0}};
    float best_ig = -1e9f;
    best_x = robot_x;
    best_y = robot_y;
    for (int d = 0; d < 9; ++d) {
        float nx = robot_x + dirs[d][0] * step;
        float ny = robot_y + dirs[d][1] * step;
        int gx = posterior.posToGridX(nx);
        int gy = posterior.posToGridY(ny);
        float ig = informationGain(posterior, gx, gy, robot_x, robot_y);
        if (ig > best_ig) { best_ig = ig; best_x = nx; best_y = ny; }
    }
}

MovingStateOPGSL::MovingStateOPGSL(Algorithm* _algorithm)
    : MovingState(_algorithm)
{
    opgsl_ = dynamic_cast<OPGSL*>(_algorithm);
}

NavigateToPose::Goal MovingStateOPGSL::posToGoal(float x, float y) {
    NavigateToPose::Goal goal;
    goal.pose.header.frame_id = "map";
    goal.pose.header.stamp = opgsl_->node->now();
    goal.pose.pose.position.x = x;
    goal.pose.pose.position.y = y;
    goal.pose.pose.position.z = 0.0;
    goal.pose.pose.orientation.w = 1.0;
    return goal;
}

void MovingStateOPGSL::chooseGoalAndMove() {
    if (!opgsl_) { GSL_ERROR("OPGSL pointer null"); return; }

    opgsl_->step_count_++;
    double now = opgsl_->node->now().seconds();
    if (opgsl_->last_update_time_ > 0) {
        opgsl_->elapsed_time_ += static_cast<float>(now - opgsl_->last_update_time_);
    }
    opgsl_->last_update_time_ = now;
    float remaining = opgsl_->resultLogging.maxSearchTime - opgsl_->elapsed_time_;
    if (remaining < 0) remaining = 0;

    int gcx = opgsl_->grid_.posToGridX(opgsl_->currentRobotPosition.x);
    int gcy = opgsl_->grid_.posToGridY(opgsl_->currentRobotPosition.y);
    opgsl_->visited_cells_.insert({gcx, gcy});

    opgsl_->grid_.update(opgsl_->latest_gas_,
                         opgsl_->currentRobotPosition.x,
                         opgsl_->currentRobotPosition.y,
                         opgsl_->latest_wind_x_,
                         opgsl_->latest_wind_y_);

    float target_x, target_y;
    bool got_target = false;

    if (!opgsl_->current_path_.waypoints.empty() &&
        opgsl_->waypoint_idx_ < static_cast<int>(opgsl_->current_path_.waypoints.size())) {
        auto& wp = opgsl_->current_path_.waypoints[opgsl_->waypoint_idx_];
        float dist_to_wp = std::sqrt(
            (wp.first - opgsl_->currentRobotPosition.x) * (wp.first - opgsl_->currentRobotPosition.x) +
            (wp.second - opgsl_->currentRobotPosition.y) * (wp.second - opgsl_->currentRobotPosition.y));
        if (dist_to_wp < 1.0f) {
            opgsl_->waypoint_idx_++;
            // Do NOT set got_target here; let replan handle next waypoint
        } else {
            // Still heading to current waypoint
            target_x = wp.first;
            target_y = wp.second;
            got_target = true;
        }
    }

    if (!got_target || opgsl_->step_count_ % opgsl_->solver_cfg_.replan_interval == 0) {
        opgsl_->current_path_ = opgsl_->solver_.solve(
            opgsl_->grid_, opgsl_->currentRobotPosition.x,
            opgsl_->currentRobotPosition.y, remaining, opgsl_->visited_cells_);
        opgsl_->waypoint_idx_ = 0;

        if (!opgsl_->current_path_.waypoints.empty()) {
            auto& wp = opgsl_->current_path_.waypoints[0];
            target_x = wp.first;
            target_y = wp.second;
            got_target = true;
        }
    }

    if (!got_target) {
        opgsl_->solver_.infotaxisStep(
            opgsl_->grid_, opgsl_->currentRobotPosition.x,
            opgsl_->currentRobotPosition.y,
            opgsl_->latest_wind_x_, opgsl_->latest_wind_y_,
            target_x, target_y);
        got_target = true;
    }

    float half = opgsl_->grid_cfg_.map_half_size - 1.0f;
    target_x = std::max(-half, std::min(half, target_x));
    target_y = std::max(-half, std::min(half, target_y));

    Vector2 target_vec(target_x, target_y);
    if (!opgsl_->isPointFree(target_vec)) {
        float offsets[][2] = {{1,0},{-1,0},{0,1},{0,-1},{1,1},{-1,-1}};
        bool found = false;
        for (auto& off : offsets) {
            Vector2 alt(target_x + off[0], target_y + off[1]);
            if (opgsl_->isPointFree(alt)) {
                target_x = alt.x;
                target_y = alt.y;
                found = true;
                break;
            }
        }
        if (!found) {
            Fail();
            return;
        }
    }

    auto goal = posToGoal(target_x, target_y);
    if (checkGoal(goal)) {
        sendGoal(goal);
    } else {
        Fail();
    }
}

void MovingStateOPGSL::Fail() {
    float fx, fy;
    opgsl_->solver_.infotaxisStep(
        opgsl_->grid_, opgsl_->currentRobotPosition.x,
        opgsl_->currentRobotPosition.y,
        opgsl_->latest_wind_x_, opgsl_->latest_wind_y_, fx, fy);
    auto goal = posToGoal(fx, fy);
    if (checkGoal(goal)) {
        sendGoal(goal);
    } else {
        // Algorithm will timeout via HasEnded()
    }
}

OPGSL::OPGSL(std::shared_ptr<rclcpp::Node> _node)
    : Algorithm(_node)
{
    rng_.seed(42);
}

void OPGSL::declareParameters() {
    Algorithm::declareParameters();
    grid_cfg_.n_cells = getParam<int>("opgsl.grid.n_cells", 60);
    grid_cfg_.resolution = getParam<double>("opgsl.grid.resolution", 1.0);
    grid_cfg_.map_half_size = getParam<double>("opgsl.grid.map_half_size", 30.0);
    grid_cfg_.source_rate_Q = getParam<double>("opgsl.grid.source_rate_Q", 1.0);
    grid_cfg_.sigma_y_a = getParam<double>("opgsl.grid.sigma_y_a", 0.1);
    grid_cfg_.sigma_y_b = getParam<double>("opgsl.grid.sigma_y_b", 0.9);
    grid_cfg_.sigma_z_a = getParam<double>("opgsl.grid.sigma_z_a", 0.05);
    grid_cfg_.sigma_z_b = getParam<double>("opgsl.grid.sigma_z_b", 0.85);
    grid_cfg_.min_wind_speed = getParam<double>("opgsl.grid.min_wind_speed", 0.03);
    grid_cfg_.sense_radius_m = getParam<double>("opgsl.grid.sense_radius_m", 8.0);
    grid_cfg_.detection_threshold = getParam<double>("opgsl.grid.detection_threshold", 0.01);
    solver_cfg_.sense_radius_m = grid_cfg_.sense_radius_m;
    solver_cfg_.replan_interval = getParam<int>("opgsl.solver.replan_interval", 5);
    solver_cfg_.max_waypoints = getParam<int>("opgsl.solver.max_waypoints", 8);
    solver_cfg_.uav_speed = getParam<double>("opgsl.solver.uav_speed", 1.0);
    solver_cfg_.exploration_bonus = getParam<double>("opgsl.solver.exploration_bonus", 0.15);
    convergence_cov_threshold_ = getParam<double>("opgsl.convergence.cov_threshold", 2.0);
    convergence_min_bouts_ = getParam<int>("opgsl.convergence.min_bouts", 2);
    convergence_stable_steps_ = getParam<int>("opgsl.convergence.stable_steps", 5);
    convergence_min_time_ = getParam<double>("opgsl.convergence.min_time", 15.0);
    audit_file_ = getParam<std::string>("opgsl.audit_file", "opgsl_audit.csv");
}

void OPGSL::Initialize() {
    grid_.init(grid_cfg_);
    solver_.init(solver_cfg_);

    waitForMapState = std::make_unique<WaitForMapState>(this);
    waitForGasState = std::make_unique<WaitForGasState>(this);
    stopAndMeasureState = std::make_unique<StopAndMeasureState>(this);
    movingState = std::make_unique<MovingStateOPGSL>(this);

    Algorithm::Initialize();

    stateMachine.forceSetState(waitForMapState.get());
    if (!audit_file_.empty()) {
        audit_stream_.open(audit_file_);
        audit_stream_ << "step,time_s,gas,wind_speed,wind_dir,cov_trace,entropy,"
                      << "est_x,est_y,waypoints,hit_count,stable_steps" << std::endl;
    }
    GSL_INFO("OPGSL initialized: grid={}x{} res={:.1f}m", grid_cfg_.n_cells, grid_cfg_.n_cells, grid_cfg_.resolution);
}

void OPGSL::OnUpdate() {
    Algorithm::OnUpdate();
}

void OPGSL::processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection) {
    total_measurements_++;
    latest_gas_ = static_cast<float>(concentration);
    latest_wind_speed_ = static_cast<float>(windSpeed);
    latest_wind_x_ = static_cast<float>(windSpeed * std::cos(windDirection));
    latest_wind_y_ = static_cast<float>(windSpeed * std::sin(windDirection));
    wind_dir_history_.push_back(static_cast<float>(windDirection));
    if (wind_dir_history_.size() > kWindHistorySize)
        wind_dir_history_.pop_front();
    if (concentration > grid_cfg_.detection_threshold) {
        gas_hit_count_++;
    }
    logAudit("meas");

    // Compute goal via MovingState, then transition
    movingState->chooseGoalAndMove();
    stateMachine.forceSetState(movingState.get());
}

float OPGSL::smoothWindDirection() const {
    if (wind_dir_history_.empty()) return 0;
    float sin_sum = 0, cos_sum = 0;
    for (float d : wind_dir_history_) {
        sin_sum += std::sin(d);
        cos_sum += std::cos(d);
    }
    return std::atan2(sin_sum / wind_dir_history_.size(), cos_sum / wind_dir_history_.size());
}

void OPGSL::logAudit(const std::string& msg) {
    if (!audit_stream_.is_open()) return;
    float ex, ey;
    grid_.getEstimate(ex, ey);
    audit_stream_ << step_count_ << "," << elapsed_time_ << ","
                  << latest_gas_ << "," << latest_wind_speed_ << ","
                  << smoothWindDirection() << "," << grid_.covarianceTrace() << ","
                  << grid_.entropy() << "," << ex << "," << ey << ","
                  << current_path_.waypoints.size() << "," << gas_hit_count_ << ","
                  << stable_steps_count_ << std::endl;
}

GSLResult OPGSL::checkSourceFound() {
    if (elapsed_time_ < convergence_min_time_) return GSLResult::Running;
    if (gas_hit_count_ < convergence_min_bouts_) return GSLResult::Running;
    float cov = grid_.covarianceTrace();
    if (cov < convergence_cov_threshold_) {
        stable_steps_count_++;
    } else {
        stable_steps_count_ = 0;
    }
    if (stable_steps_count_ >= convergence_stable_steps_) {
        float ex, ey;
        grid_.getEstimate(ex, ey);
        float dist = std::sqrt(
            (ex - resultLogging.sourcePositionGT.x) * (ex - resultLogging.sourcePositionGT.x) +
            (ey - resultLogging.sourcePositionGT.y) * (ey - resultLogging.sourcePositionGT.y));
        GSL_INFO("OPGSL converged: estimate=({:.2f},{:.2f}) dist={:.2f}m cov={:.2f}", ex, ey, dist, cov);
        currentResult = GSLResult::Success;
        return GSLResult::Success;
    }
    if (elapsed_time_ >= resultLogging.maxSearchTime) {
        return GSLResult::Failure;
    }
    return GSLResult::Running;
}

void OPGSL::saveResultsToFile(GSLResult result) {
    float ex, ey;
    grid_.getEstimate(ex, ey);
    // Estimate stored in grid, printed to audit log
    if (audit_stream_.is_open()) {
        audit_stream_.close();
    }
    Algorithm::saveResultsToFile(result);
}

} // namespace GSL
