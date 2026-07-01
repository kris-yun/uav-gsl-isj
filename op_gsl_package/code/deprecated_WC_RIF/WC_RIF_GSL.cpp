// WC_RIF_GSL.cpp - Wind-Conditioned Robust Intermittency Filter for GSL
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
    convergence_min_time_ = getParam<double>("wcrif.convergence.min_time", 30.0);
    convergence_min_hits_ = getParam<int>("wcrif.convergence.min_hits", 5);
}

void WC_RIF_GSL::Initialize() {
    int N = n_cells_;
    log_belief_ = Eigen::MatrixXf::Zero(N, N);
    log_belief_.setConstant(-std::log(float(N * N)));
    grid_x_.resize(N, N);
    grid_y_.resize(N, N);
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            grid_x_(i, j) = i * resolution_ - map_half_size_;
            grid_y_(i, j) = j * resolution_ - map_half_size_;
        }
    }

    waitForMapState = std::make_unique<WaitForMapState>(this);
    waitForGasState = std::make_unique<WaitForGasState>(this);
    stopAndMeasureState = std::make_unique<StopAndMeasureState>(this);
    movingState = std::make_unique<MovingStateWC_RIF>(this);

    Algorithm::Initialize();
    stateMachine.forceSetState(waitForMapState.get());
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

        auto check = checkSourceFound();
        if (check != GSLResult::Running) {
            saveResultsToFile(check);
            return;
        }
        movingState->chooseGoalAndMove();
    }
}

void WC_RIF_GSL::OnCompleteNavigation(GSLResult result, State* previousState) {
    stateMachine.forceSetState(stopAndMeasureState.get());
}

void WC_RIF_GSL::processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection) {
    latest_gas_ = float(concentration);
    latest_wind_x_ = float(windSpeed * std::cos(windDirection));
    latest_wind_y_ = float(windSpeed * std::sin(windDirection));

    // Low wind: use smoothed default
    if (latest_wind_speed_ < 0.05f) {
        latest_wind_x_ = 0.1f;
        latest_wind_y_ = 0.05f;
    }

    bool hit = concentration > 0.01;
    if (hit) gas_hit_count_++;
    hit_history_.push_back(hit ? 1 : 0);
    if (hit_history_.size() > kWindowSize) hit_history_.pop_front();

    // WC-RIF belief update
    float hit_rate = computeHitRate();
    float w_inter = (1.0f - alpha_intermittency_) + alpha_intermittency_ * hit_rate;
    float H = entropy();
    float H_max = std::log(float(n_cells_ * n_cells_));
    float sigma_adaptive = sigma_base_ * (1.0f + gamma_entropy_ * H / H_max);

    for (int i = 0; i < n_cells_; ++i) {
        for (int j = 0; j < n_cells_; ++j) {
            float sx = grid_x_(i, j);
            float sy = grid_y_(i, j);
            float alignment = computeWindAlignment(sx, sy, currentRobotPosition.x, currentRobotPosition.y, latest_wind_x_, latest_wind_y_);
            float sigma_eff = sigma_adaptive * (1.0f + beta_wind_ * alignment);
            float p_hit = computeHitProbability(sx, sy, currentRobotPosition.x, currentRobotPosition.y, latest_wind_x_, latest_wind_y_);
            float residual = hit ? std::abs(1.0f - p_hit) : std::abs(0.0f - p_hit);
            float kernel_val = cauchyKernel(residual, sigma_eff);

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

    need_next_goal_ = true;
    step_count_++;
}

GSLResult WC_RIF_GSL::checkSourceFound() {
    if (elapsed_time_ >= resultLogging.maxSearchTime) {
        float est_x, est_y;
        getMAP(est_x, est_y);
        GSL_INFO("WC-RIF timeout: MAP=({:.2f},{:.2f}) hits={}", est_x, est_y, gas_hit_count_);
        if (gas_hit_count_ >= convergence_min_hits_) {
            currentResult = GSLResult::Success;
            return GSLResult::Success;
        }
        return GSLResult::Failure;
    }

    if (elapsed_time_ > convergence_min_time_ && gas_hit_count_ >= convergence_min_hits_) {
        float est_x, est_y;
        getMAP(est_x, est_y);
        float dx = est_x - currentRobotPosition.x;
        float dy = est_y - currentRobotPosition.y;
        float dist = std::sqrt(dx*dx + dy*dy);

        float H = entropy();
        float H_max = std::log(float(n_cells_ * n_cells_));
        float conc = 1.0f - H / H_max;  // normalized certainty

        if (conc > 0.3f && dist < 2.0f) {
            GSL_INFO("WC-RIF convergence: MAP=({:.2f},{:.2f}) dist={:.2f} conc={:.2f}", est_x, est_y, dist, conc);
            currentResult = GSLResult::Success;
            return GSLResult::Success;
        }
    }
    return GSLResult::Running;
}

void WC_RIF_GSL::saveResultsToFile(GSLResult result) {
    Algorithm::saveResultsToFile(result);
}

// ========== Internal Methods ==========

float WC_RIF_GSL::computeHitProbability(float sx, float sy, float sensor_x, float sensor_y, float wx, float wy) const {
    float dx = sensor_x - sx;
    float dy = sensor_y - sy;
    float dist = std::sqrt(dx*dx + dy*dy) + 0.01f;
    float ws = std::max(std::sqrt(wx*wx + wy*wy), min_wind_);
    float wnx = wx / (std::sqrt(wx*wx + wy*wy) + 1e-6f);
    float wny = wy / (std::sqrt(wx*wx + wy*wy) + 1e-6f);
    float d_down = dx * wnx + dy * wny;
    float d_cross = std::abs(dx * wny - dy * wnx);
    float sy_val = sigma_y_ * std::sqrt(std::max(d_down, 0.01f));
    float sz_val = sigma_z_ * std::sqrt(std::max(d_down, 0.01f));
    float p = Q_ / (2.0f * M_PI * sy_val * sz_val * ws) * std::exp(-d_cross*d_cross / (2.0f * sy_val*sy_val));
    return std::min(std::max(p, 0.0f), 0.99f);
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
    x = std::max(-map_half_size_ + m, std::min(map_half_size_ - m, x));
    y = std::max(-map_half_size_ + m, std::min(map_half_size_ - m, y));
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

    if (wcrif_->gas_hit_count_ == 0) {
        // No gas detected: explore downwind
        wcrif_->exploreStep(tx, ty);
    } else {
        // Gas detected: move toward MAP estimate with entropy-weighted exploration
        float est_x, est_y;
        wcrif_->getMAP(est_x, est_y);

        float H = wcrif_->entropy();
        float H_max = std::log(float(wcrif_->n_cells_ * wcrif_->n_cells_));
        float exploration = std::min(H / H_max, 1.0f);

        float angle_to_map = std::atan2(est_y - wcrif_->currentRobotPosition.y,
                                         est_x - wcrif_->currentRobotPosition.x);
        std::mt19937 rng(std::random_device{}());
        float random_angle = std::uniform_real_distribution<float>(0, 2*M_PI)(rng);
        float blend = (1 - exploration) * angle_to_map + exploration * random_angle;

        float step = std::min(wcrif_->max_step_, 0.5f);
        tx = wcrif_->currentRobotPosition.x + step * std::cos(blend);
        ty = wcrif_->currentRobotPosition.y + step * std::sin(blend);
    }

    wcrif_->clipToMapBounds(tx, ty);

    GSL_INFO("WC-RIF step={} target=({:.2f},{:.2f}) hits={} H={:.1f} elapsed={:.1f}",
            wcrif_->step_count_, tx, ty, wcrif_->gas_hit_count_, wcrif_->entropy(), wcrif_->elapsed_time_);

    // Navigate
    auto goal = posToGoal(tx, ty);
    if (checkGoal(goal)) { sendGoal(goal); return; }

    // Fallback: shorter step
    float dx = tx - wcrif_->currentRobotPosition.x;
    float dy = ty - wcrif_->currentRobotPosition.y;
    float d = std::sqrt(dx*dx + dy*dy);
    if (d > 0.1f) {
        float dirx = dx/d, diry = dy/d;
        for (float f : {0.75f, 0.5f, 0.3f}) {
            float fx = wcrif_->currentRobotPosition.x + dirx * d * f;
            float fy = wcrif_->currentRobotPosition.y + diry * d * f;
            wcrif_->clipToMapBounds(fx, fy);
            auto fg = posToGoal(fx, fy);
            if (checkGoal(fg)) { sendGoal(fg); return; }
        }
    }

    // Random fallback
    std::mt19937 rng(std::random_device{}());
    for (int i = 0; i < 8; i++) {
        float ang = std::uniform_real_distribution<float>(0, 2*M_PI)(rng);
        float dist = std::uniform_real_distribution<float>(0.3f, 1.0f)(rng);
        float rx = wcrif_->currentRobotPosition.x + dist * std::cos(ang);
        float ry = wcrif_->currentRobotPosition.y + dist * std::sin(ang);
        wcrif_->clipToMapBounds(rx, ry);
        auto rg = posToGoal(rx, ry);
        if (checkGoal(rg)) { sendGoal(rg); return; }
    }

    GSL_ERROR("WC-RIF ALL fallbacks failed!");
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
