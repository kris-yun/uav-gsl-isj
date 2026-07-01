// WC_RIF_GSL.hpp - Wind-Conditioned Robust Intermittency Filter for GSL
#include <Eigen/Sparse>
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
    float grid_origin_x_ = 0.0f;
    float grid_origin_y_ = 0.0f;

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
    float latest_wind_speed_ = 0.0f;
    float latest_gas_ = 0.0f;
    int gas_hit_count_ = 0;
    std::deque<int> hit_history_;
    std::deque<std::pair<float,float>> map_history_;  // MAP position history
    std::deque<std::pair<float,float>> recent_positions_;
    std::vector<std::vector<int>> visit_count_;
    // Advection-diffusion forward model
    Eigen::SparseMatrix<float> forward_L_;  // operator matrix
    bool forward_model_initialized_ = false;
    float forward_kappa_ = 0.01f;  // diffusion coefficient
    float forward_delta_ = 0.1f;   // decay rate
    float forward_alpha_ = 10.0f;  // hit sensitivity
    std::deque<float> entropy_history_;
    std::deque<float> surprise_history_;
    // BOCPD runlength posterior
    static constexpr int kRMax = 100;
    std::vector<Eigen::MatrixXf> bocpd_beliefs_; // one belief per runlength
    std::vector<float> bocpd_weights_;            // posterior weight per runlength
    float bocpd_hazard_ = 0.01f;                  // prior changepoint rate (1/step)  // stuck detection
    int stability_window_ = 20;  // steps to check stability
    float stability_threshold_ = 0.5f;  // meters - converged if MAP moves less than this
    static constexpr int kWindowSize = 10;

    // Convergence
    float convergence_min_time_ = 30.0f;
    int convergence_min_hits_ = 5;

    // Navigation
    double last_update_time_ = 0.0;
    bool need_next_goal_ = false;
    bool timed_out_ = false;
    bool wind_convention_upwind_ = false; // false=VGR(downwind), true=GADEN(upwind)
    // CUSUM adaptive detection
    float cusum_sum_ = 0.0f;
    float cusum_delta_ = 0.005f; // slack parameter
    float cusum_threshold_ = 0.05f; // detection threshold
    float cusum_decay_ = 0.95f; // exponential decay for CUSUM
    bool results_saved_ = false;
    std::mt19937 rng_{std::random_device{}()};
    // MHT re-seeding state
    int map_stuck_counter_ = 0;
    float prev_map_x_ = 0.0f, prev_map_y_ = 0.0f;
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
    void initForwardModel();
    Eigen::VectorXf solveAdjoint(const Eigen::SparseMatrix<float>& L, int obs_idx);
    std::vector<std::vector<float>> computeGeodesicDistances(float ox, float oy);
};

} // namespace GSL
