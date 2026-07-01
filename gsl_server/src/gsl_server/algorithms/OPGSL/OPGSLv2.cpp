// OPGSLv2.cpp - Clean implementation based on Python prototype
#include "OPGSLv2.hpp"
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

OPGSLv2::OPGSLv2(std::shared_ptr<rclcpp::Node> _node) : Algorithm(_node) {}

void OPGSLv2::declareParameters() {
    Algorithm::declareParameters();
    n_cells_ = getParam<int>("opgsl.grid.n_cells", 40);
    resolution_ = getParam<double>("opgsl.grid.resolution", 0.5);
    map_half_size_ = n_cells_ * resolution_ / 2.0f;
    convergence_entropy_threshold_ = getParam<double>("opgsl.convergence.entropy_threshold", 5.0);
    convergence_min_bouts_ = getParam<int>("opgsl.convergence.min_bouts", 5);
    convergence_stable_steps_ = getParam<int>("opgsl.convergence.stable_steps", 5);
    convergence_min_time_ = getParam<double>("opgsl.convergence.min_time", 30.0);
}

void OPGSLv2::Initialize() {
    // Initialize field estimator
    field_cfg_.n_cells = n_cells_;
    field_cfg_.resolution = resolution_;
    field_cfg_.map_half_size = map_half_size_;
    field_cfg_.bandwidth = 1.5f;
    field_cfg_.max_observations = 200;
    field_estimator_.init(field_cfg_);

    // Initialize info gain
    ig_cfg_.exploration_weight = 0.3f;
    ig_cfg_.wind_bonus = 0.5f;
    ig_cfg_.uncertainty_weight = 0.4f;
    info_gain_.init(ig_cfg_);

    // State machine
    waitForMapState = std::make_unique<WaitForMapState>(this);
    waitForGasState = std::make_unique<WaitForGasState>(this);
    stopAndMeasureState = std::make_unique<StopAndMeasureState>(this);
    movingState = std::make_unique<MovingStateOPGSLv2>(this);

    Algorithm::Initialize();
    stateMachine.forceSetState(waitForMapState.get());

    // Init state
    prev_gas_ = 0.0f;
    run_length_ = 0.8f;
    run_direction_x_ = 0.0f;
    run_direction_y_ = -1.0f;
    max_step_ = 1.0f;
    max_run_steps_ = 8;
    need_next_goal_ = false;

    GSL_INFO("OPGSLv2 initialized: grid={}x{} res={:.1f}m", n_cells_, n_cells_, resolution_);
}

void OPGSLv2::OnUpdate() {
    Algorithm::OnUpdate();

    if (need_next_goal_) {
        need_next_goal_ = false;

        double now = node->now().seconds();
        if (last_update_time_ > 0) elapsed_time_ += static_cast<float>(now - last_update_time_);
        last_update_time_ = now;

        auto check = checkSourceFound();
        if (check != GSLResult::Running) {
            GSL_INFO("OPGSLv2: search complete, result={}", (int)check);
            saveResultsToFile(check);
            return;
        }

        GSL_INFO("OPGSLv2: selecting next goal (hits={} elapsed={:.1f}s)", gas_hit_count_, elapsed_time_);
        movingState->chooseGoalAndMove();
    }
}

void OPGSLv2::OnCompleteNavigation(GSLResult result, State* previousState) {
    stateMachine.forceSetState(stopAndMeasureState.get());
}

void OPGSLv2::processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection) {
    latest_gas_ = static_cast<float>(concentration);
    latest_wind_speed_ = static_cast<float>(windSpeed);
    latest_wind_x_ = static_cast<float>(windSpeed * std::cos(windDirection));
    latest_wind_y_ = static_cast<float>(windSpeed * std::sin(windDirection));

    wind_dir_history_.push_back(static_cast<float>(windDirection));
    if (wind_dir_history_.size() > kWindHistorySize) wind_dir_history_.pop_front();

    // Low wind: use smoothed direction
    if (latest_wind_speed_ < 0.05f && !wind_dir_history_.empty()) {
        float sd = smoothWindDirection();
        latest_wind_x_ = 0.1f * std::cos(sd);
        latest_wind_y_ = 0.1f * std::sin(sd);
        latest_wind_speed_ = 0.1f;
    }

    if (concentration > 0.01) gas_hit_count_++;

    // Add to field estimator
    field_estimator_.addObservation(
        static_cast<float>(concentration),
        currentRobotPosition.x, currentRobotPosition.y,
        latest_wind_x_, latest_wind_y_,
        elapsed_time_
    );

    need_next_goal_ = true;
}

float OPGSLv2::smoothWindDirection() const {
    if (wind_dir_history_.empty()) return 0;
    float ss = 0, cs = 0;
    for (float d : wind_dir_history_) {
        ss += std::sin(d); cs += std::cos(d);
    }
    return std::atan2(ss / wind_dir_history_.size(), cs / wind_dir_history_.size());
}

GSLResult OPGSLv2::checkSourceFound() {
    // Timeout
    if (elapsed_time_ >= resultLogging.maxSearchTime) {
        auto centroid = field_estimator_.computeWeightedCentroid();
        float est_x = centroid.x, est_y = centroid.y;
        GSL_INFO("OPGSLv2 timeout: centroid=({:.2f},{:.2f}) gas_hits={}", est_x, est_y, gas_hit_count_);
        if (gas_hit_count_ >= 2) {
            currentResult = GSLResult::Success;
            return GSLResult::Success;
        }
        return GSLResult::Failure;
    }

    // Early convergence
    if (elapsed_time_ > convergence_min_time_ && gas_hit_count_ >= convergence_min_bouts_) {
        auto c = field_estimator_.computeWeightedCentroid();
        if (c.weight_sum > 1e-6f) {
            float dx = c.x - currentRobotPosition.x;
            float dy = c.y - currentRobotPosition.y;
            float dist = std::sqrt(dx*dx + dy*dy);
            float conc = (c.spread > 0.01f) ? (1.0f / (1.0f + c.spread)) : 0.0f;

            if (conc > 0.4f && dist < 1.5f) {
                GSL_INFO("OPGSLv2 early convergence: centroid=({:.2f},{:.2f}) conc={:.2f} dist={:.2f}",
                        c.x, c.y, conc, dist);
                currentResult = GSLResult::Success;
                return GSLResult::Success;
            }
        }
    }

    return GSLResult::Running;
}

void OPGSLv2::saveResultsToFile(GSLResult result) {
    Algorithm::saveResultsToFile(result);
}

void OPGSLv2::clipToMapBounds(float& x, float& y) const {
    float m = 0.5f, h = map_half_size_;
    x = std::max(-h+m, std::min(h-m, x));
    y = std::max(-h+m, std::min(h-m, y));
}

// ========== Navigation ==========

void OPGSLv2::exploreStep(float& best_x, float& best_y) {
    // No gas detected: golden angle exploration downwind
    info_gain_.exploreGoldenAngle(
        best_x, best_y,
        currentRobotPosition.x, currentRobotPosition.y,
        latest_wind_x_, latest_wind_y_,
        0.8f, step_count_, map_half_size_
    );
    clipToMapBounds(best_x, best_y);
}

void OPGSLv2::chemotaxisStep(float& best_x, float& best_y) {
    float cx = currentRobotPosition.x, cy = currentRobotPosition.y;
    auto centroid = field_estimator_.computeWeightedCentroid();

    if (centroid.weight_sum > 1e-6f) {
        float ex = centroid.x, ey = centroid.y;
        float dx = ex - cx, dy = ey - cy;
        float dist = std::sqrt(dx*dx + dy*dy);
        float grad = latest_gas_ - prev_gas_;

        if (dist > 0.5f) {
            // Move toward centroid
            float step = std::min(max_step_, dist * 0.4f);
            best_x = cx + (dx/dist) * step;
            best_y = cy + (dy/dist) * step;
        } else if (grad > 0.001f) {
            // Near centroid, gradient positive: continue in same direction
            best_x = cx + run_direction_x_ * 0.3f;
            best_y = cy + run_direction_y_ * 0.3f;
        } else {
            // Near centroid, no gradient: random walk
            std::mt19937 rng(std::random_device{}());
            float ang = std::uniform_real_distribution<float>(0, 2*M_PI)(rng);
            run_direction_x_ = std::cos(ang);
            run_direction_y_ = std::sin(ang);
            best_x = cx + run_direction_x_ * 0.3f;
            best_y = cy + run_direction_y_ * 0.3f;
        }

        GSL_INFO("CHEMOTAX step={} target=({:.2f},{:.2f}) centroid=({:.2f},{:.2f}) dist={:.2f} hits={}",
                step_count_, best_x, best_y, ex, ey, dist, gas_hit_count_);
    } else {
        // No field estimate: explore
        exploreStep(best_x, best_y);
    }

    clipToMapBounds(best_x, best_y);
    prev_gas_ = latest_gas_;
}

// ========== MovingState ==========

MovingStateOPGSLv2::MovingStateOPGSLv2(Algorithm* _algorithm)
    : MovingState(_algorithm) {
    opgsl_ = dynamic_cast<OPGSLv2*>(_algorithm);
}

NavigateToPose::Goal MovingStateOPGSLv2::posToGoal(float x, float y) {
    NavigateToPose::Goal g;
    g.pose.header.frame_id = "map";
    g.pose.header.stamp = opgsl_->node->now();
    g.pose.pose.position.x = x;
    g.pose.pose.position.y = y;
    g.pose.pose.position.z = 1.0f;
    g.pose.pose.orientation.w = 1.0f;
    return g;
}

void MovingStateOPGSLv2::chooseGoalAndMove() {
    if (!opgsl_) { GSL_ERROR("OPGSLv2 pointer null"); return; }

    opgsl_->step_count_++;

    double now = opgsl_->node->now().seconds();
    if (opgsl_->last_update_time_ > 0)
        opgsl_->elapsed_time_ += static_cast<float>(now - opgsl_->last_update_time_);
    opgsl_->last_update_time_ = now;

    // Choose strategy based on gas detection
    float tx, ty;
    if (opgsl_->gas_hit_count_ == 0) {
        opgsl_->exploreStep(tx, ty);
    } else {
        opgsl_->chemotaxisStep(tx, ty);
    }

    GSL_INFO("OPGSLv2 step={} target=({:.2f},{:.2f}) gas_hits={} elapsed={:.1f}",
            opgsl_->step_count_, tx, ty, opgsl_->gas_hit_count_, opgsl_->elapsed_time_);

    // Navigate
    float cx = opgsl_->currentRobotPosition.x, cy = opgsl_->currentRobotPosition.y;
    auto goal = posToGoal(tx, ty);

    if (checkGoal(goal)) { sendGoal(goal); return; }

    // Fallback: try shorter steps
    float dx = tx - cx, dy = ty - cy;
    float d = std::sqrt(dx*dx + dy*dy);
    if (d > 0.1f) {
        float dirx = dx/d, diry = dy/d;
        float fa[] = {0.75f, 0.5f, 0.3f, 0.2f};
        for (float f : fa) {
            float fx = cx + dirx * d * f;
            float fy = cy + diry * d * f;
            opgsl_->clipToMapBounds(fx, fy);
            auto fg = posToGoal(fx, fy);
            if (checkGoal(fg)) { sendGoal(fg); return; }
        }
    }

    // Last resort: random
    std::mt19937 rng(std::random_device{}());
    for (int i = 0; i < 8; i++) {
        float ang = std::uniform_real_distribution<float>(0, 2*M_PI)(rng);
        float dist = std::uniform_real_distribution<float>(0.3f, 1.5f)(rng);
        float rx = cx + dist * std::cos(ang);
        float ry = cy + dist * std::sin(ang);
        opgsl_->clipToMapBounds(rx, ry);
        auto rg = posToGoal(rx, ry);
        if (checkGoal(rg)) { sendGoal(rg); return; }
    }

    GSL_ERROR("OPGSLv2 ALL fallbacks failed!");
}

void MovingStateOPGSLv2::Fail() {
    if (!opgsl_) return;
    std::mt19937 rng(std::random_device{}());
    float ang = std::uniform_real_distribution<float>(0, 2*M_PI)(rng);
    float nx = opgsl_->currentRobotPosition.x + 1.5f * std::cos(ang);
    float ny = opgsl_->currentRobotPosition.y + 1.5f * std::sin(ang);
    opgsl_->clipToMapBounds(nx, ny);
    auto goal = posToGoal(nx, ny);
    if (checkGoal(goal)) sendGoal(goal);
}

} // namespace GSL
