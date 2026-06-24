#pragma once
#include <gsl_server/algorithms/Common/Algorithm.hpp>
#include <gsl_server/algorithms/Common/States/MovingState.hpp>
#include <Eigen/Dense>
#include <vector>
#include <set>
#include <deque>
#include <fstream>
#include <cmath>
#include <algorithm>
#include <random>

namespace GSL {

class GridPosteriorOP {
public:
    struct Config {
        int n_cells = 60;
        float resolution = 1.0f;
        float map_half_size = 30.0f;
        float source_rate_Q = 1.0f;
        float sigma_y_a = 0.1f;
        float sigma_y_b = 0.9f;
        float sigma_z_a = 0.05f;
        float sigma_z_b = 0.85f;
        float min_wind_speed = 0.03f;
        float sense_radius_m = 8.0f;
        float detection_threshold = 0.01f;
        float uav_height_z = 1.0f;
        float source_height_z = 0.0f;
    };
    void init(const Config& cfg);
    void update(float gas_reading, float robot_x, float robot_y, float wind_x, float wind_y);
    void getEstimate(float& ex, float& ey) const;
    float entropy() const;
    float covarianceTrace() const;
    const Eigen::MatrixXf& logPosterior() const { return log_posterior_; }
    int nCells() const { return cfg_.n_cells; }
    int posToGridX(float x) const;
    int posToGridY(float y) const;
    void gridToPos(int gx, int gy, float& px, float& py) const;
private:
    void normalize();
    Config cfg_;
    Eigen::MatrixXf log_posterior_;
    Eigen::MatrixXf grid_x_, grid_y_;
};

class OPSolverOP {
public:
    struct Config {
        float sense_radius_m = 8.0f;
        int replan_interval = 5;
        int max_waypoints = 8;
        float uav_speed = 1.0f;
        float exploration_bonus = 0.15f;
    };
    struct Path {
        std::vector<std::pair<float,float>> waypoints;
        float total_reward = 0.0f;
        float total_cost = 0.0f;
    };
    void init(const Config& cfg);
    Path solve(const GridPosteriorOP& posterior, float cur_x, float cur_y,
               float remaining_time, const std::set<std::pair<int,int>>& visited);
    void infotaxisStep(const GridPosteriorOP& posterior, float robot_x, float robot_y,
                       float wind_x, float wind_y, float& best_x, float& best_y);
private:
    float informationGain(const GridPosteriorOP& posterior, int gx, int gy,
                          float robot_x, float robot_y) const;
    Config cfg_;
};

class OPGSL;
class MovingStateOPGSL : public MovingState {
public:
    MovingStateOPGSL(Algorithm* _algorithm);
    void chooseGoalAndMove() override;
protected:
    void Fail() override;
private:
    OPGSL* opgsl_;
    NavigateToPose::Goal posToGoal(float x, float y);
};

class OPGSL : public Algorithm {
    friend class MovingStateOPGSL;
public:
    explicit OPGSL(std::shared_ptr<rclcpp::Node> _node);
    void Initialize() override;
protected:
    void declareParameters() override;
    void processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection) override;
    GSLResult checkSourceFound() override;
    void saveResultsToFile(GSLResult result) override;
    void OnUpdate() override;
private:
    GridPosteriorOP grid_;
    GridPosteriorOP::Config grid_cfg_;
    OPSolverOP solver_;
    OPSolverOP::Config solver_cfg_;
    int step_count_ = 0;
    float elapsed_time_ = 0.0f;
    float latest_wind_x_ = 0.0f;
    float latest_wind_y_ = 0.0f;
    float latest_wind_speed_ = 0.0f;
    float latest_gas_ = 0.0f;
    int gas_hit_count_ = 0;
    int total_measurements_ = 0;
    std::set<std::pair<int,int>> visited_cells_;
    OPSolverOP::Path current_path_;
    int waypoint_idx_ = 0;
    float convergence_cov_threshold_ = 2.0f;
    int convergence_min_bouts_ = 2;
    int convergence_stable_steps_ = 5;
    float convergence_min_time_ = 15.0f;
    int stable_steps_count_ = 0;
    std::deque<float> wind_dir_history_;
    static constexpr int kWindHistorySize = 10;
    std::string audit_file_;
    std::ofstream audit_stream_;
    std::mt19937 rng_;
    double last_update_time_ = 0.0;
    void logAudit(const std::string& msg);
    float smoothWindDirection() const;
};

} // namespace GSL
