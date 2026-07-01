// WC_RIF_GSL.hpp - Wind-Conditioned Robust Intermittency Filter for GSL
// Standalone algorithm: does NOT modify existing OPGSL
// Origin: Robust statistics (Ge Quanbo MCC, IEEE TSP 2025)
// Innovation: Cauchy kernel + wind-conditioned bandwidth + intermittency weighting

#pragma once
#include <gsl_server/algorithms/Common/Algorithm.hpp>
#include <gsl_server/algorithms/Common/States/MovingState.hpp>
#include <Eigen/Dense>
#include <deque>
#include <cmath>
#include <random>

namespace GSL {

class WC_RIF_GSL;

class MovingStateWC_RIF : public MovingState {
public:
    MovingStateWC_RIF(Algorithm* _algorithm);
    void chooseGoalAndMove() override;
protected:
    void Fail() override;
private:
    WC_RIF_GSL* wcrif_;
    NavigateToPose::Goal posToGoal(float x, float y);
};

class WC_RIF_GSL : public Algorithm {
    friend class MovingStateWC_RIF;
public:
    explicit WC_RIF_GSL(std::shared_ptr<rclcpp::Node> _node);
    void Initialize() override;
protected:
    void declareParameters() override;
    void processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection) override;
    GSLResult checkSourceFound() override;
    void saveResultsToFile(GSLResult result) override;
    void OnUpdate() override;
    void OnCompleteNavigation(GSLResult result, State* previousState) override;
private:
    // Grid
    int n_cells_ = 40;
    float resolution_ = 0.5f;
    float map_half_size_ = 10.0f;

    // WC-RIF parameters
    float sigma_base_ = 0.3f;
    float beta_wind_ = 0.5f;
    float alpha_intermittency_ = 0.3f;
    float gamma_entropy_ = 0.1f;

    // Plume model
    float Q_ = 1.0f;
    float sigma_y_ = 0.8f;
    float sigma_z_ = 0.4f;
    float min_wind_ = 0.1f;

    // Belief
    Eigen::MatrixXf log_belief_;
    Eigen::MatrixXf grid_x_, grid_y_;

    // State
    int step_count_ = 0;
    float elapsed_time_ = 0.0f;
    float latest_wind_x_ = 0.0f, latest_wind_y_ = 0.0f;
    float latest_gas_ = 0.0f;
    int gas_hit_count_ = 0;
    std::deque<int> hit_history_;
    static constexpr int kWindowSize = 10;

    // Convergence
    float convergence_min_time_ = 30.0f;
    int convergence_min_hits_ = 5;

    // Navigation
    double last_update_time_ = 0.0;
    bool need_next_goal_ = false;
    float max_step_ = 1.0f;

    // Internal methods
    float computeHitProbability(float sx, float sy, float sensor_x, float sensor_y, float wx, float wy) const;
    float computeWindAlignment(float sx, float sy, float sensor_x, float sensor_y, float wx, float wy) const;
    float cauchyKernel(float d, float sigma) const;
    float computeHitRate() const;
    float entropy() const;
    void normalize();
    void getMAP(float& x, float& y) const;
    void clipToMapBounds(float& x, float& y) const;
    void exploreStep(float& tx, float& ty);
};

} // namespace GSL
