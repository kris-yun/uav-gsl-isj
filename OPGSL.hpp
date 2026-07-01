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
#include "WATS_GSL.hpp"

namespace GSL {
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
    void OnCompleteNavigation(GSLResult result, State* previousState) override;
private:
    // Core modules (WR-SFE + WA-IG)
    WATS::WR_SFE field_estimator_;
    WATS::WR_SFE::Config field_cfg_;
    WATS::WA_IG info_gain_;
    WATS::WA_IG::Config ig_cfg_;

    // Innovation module toggles
    bool use_levy_ = true;          // Module 1: Levy Flight exploration
    bool use_bout_ = true;          // Module 2: Bout-level detection
    bool use_adaptive_step_ = true; // Module 3: Adaptive step size

    // General state
    int step_count_ = 0;
    float elapsed_time_ = 0.0f;
    float latest_wind_x_ = 0.0f, latest_wind_y_ = 0.0f, latest_wind_speed_ = 0.0f;
    float latest_gas_ = 0.0f;
    int gas_hit_count_ = 0;
    float last_hit_x_ = 0.0f, last_hit_y_ = 0.0f;
    int consecutive_misses_ = 0;
    float last_hit_time_ = 0.0f;
    float southernmost_hit_y_ = 1e6f, southernmost_hit_x_ = 0.0f;
    float northernmost_hit_y_ = -1e6f;
    float westernmost_hit_x_ = 1e6f, easternmost_hit_x_ = -1e6f;
    int total_measurements_ = 0;

    // Grid config
    int n_cells_ = 40;
    float resolution_ = 0.5f, map_half_size_ = 10.0f;

    // Chemotaxis state
    float prev_gas_ = 0.0f, run_length_ = 0.8f;
    float run_direction_x_ = 0.0f, run_direction_y_ = -1.0f;
    int run_steps_remaining_ = 0, tumble_count_ = 0;
    float gradient_threshold_ = 0.002f, max_step_ = 1.0f;
    int max_run_steps_ = 8;

    // Convergence
    float convergence_min_time_ = 15.0f, convergence_entropy_threshold_ = 5.0f;
    int convergence_min_bouts_ = 2, convergence_stable_steps_ = 5, stable_steps_count_ = 0;

    // Wind history
    std::deque<float> wind_dir_history_;
    static constexpr int kWindHistorySize = 10;

    // Module 1: Levy Flight state
    int levy_step_remaining_ = 0;
    float levy_angle_ = 0.0f;

    // Module 2: Bout-Level state
    bool bout_active_ = false;
    float bout_start_time_ = 0.0f;
    float bout_peak_conc_ = 0.0f;
    int bout_count_ = 0;
    float time_since_last_bout_ = 0.0f;

    // Module 3: Adaptive Step state
    float step_size_ = 0.8f;
    float prev_gradient_mag_ = 0.0f;

    // Misc
    std::string audit_file_;
    std::ofstream audit_stream_;
    std::mt19937 rng_;
    double last_update_time_ = 0.0;
    bool need_next_goal_ = false;

    float smoothWindDirection() const;
    void clipToMapBounds(float& x, float& y) const;
    void infotaxisStep(float& best_x, float& best_y);
    void levyExploration(float& best_x, float& best_y, float cx, float cy);
};
} // namespace GSL
