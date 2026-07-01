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
    NavigateToPose::Goal posToGoal(float x, float y, float z);
};

class OPGSL : public Algorithm {
    friend class MovingStateOPGSL;
public:
    explicit OPGSL(std::shared_ptr<rclcpp::Node> _node);
    void Initialize() override;

    // 3D Altitude phases
    enum class AltPhase { EXPLORE, CALIBRATE, TRACK };

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
    bool use_levy_ = true;
    bool use_bout_ = true;
    bool use_adaptive_step_ = true;

    // General state
    int step_count_ = 0;
    float elapsed_time_ = 0.0f;
    float latest_wind_x_ = 0.0f, latest_wind_y_ = 0.0f, latest_wind_speed_ = 0.0f;
    float latest_gas_ = 0.0f;
    int gas_hit_count_ = 0;
    float last_hit_x_ = 0.0f, last_hit_y_ = 0.0f;
    float best_hit_x_ = 0.0f, best_hit_y_ = 0.0f, best_hit_conc_ = 0.0f;
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

    // ============================================================
    // 3D Adaptive Altitude Controller
    // ============================================================

    // Phase state
    AltPhase alt_phase_ = AltPhase::EXPLORE;
    float current_altitude_ = 0.3f;  // current flight altitude (z)

    // Altitude bounds
    float z_min_ = 0.0f;     // minimum altitude
    float z_max_ = 3.0f;     // maximum altitude

    // --- ESC (Extremum Seeking Control) for gradient tracking ---
    struct ESCState {
        float z_hat = 0.3f;       // center estimate
        float omega = 0.5f;       // perturbation frequency (rad/step)
        float amplitude = 0.8f;   // perturbation amplitude
        float amplitude_init = 0.8f;
        float lambda = 0.02f;     // amplitude decay rate
        float K = 0.3f;           // update gain
        float alpha_h = 0.3f;     // high-pass filter coefficient
        float alpha_l = 0.7f;     // low-pass filter coefficient
        float eta = 0.0f;         // high-pass filter state
        float G_hat = 0.0f;       // low-pass filtered gradient estimate
        float prev_y = 0.0f;      // previous measurement
        int t = 0;                // time step counter
        float z_min = 0.0f;
        float z_max = 3.0f;

        float getZ() const {
            return z_hat + amplitude * std::sin(omega * static_cast<float>(t));
        }

        void update(float measurement) {
            t++;
            // High-pass filter: remove DC component
            eta = alpha_h * (eta + measurement - prev_y);
            // Demodulate: extract gradient
            float a_safe = std::max(amplitude, 0.01f);
            float demod = eta * std::sin(omega * static_cast<float>(t)) * (2.0f / a_safe);
            // Low-pass filter: smooth gradient estimate
            G_hat = alpha_l * G_hat + (1.0f - alpha_l) * demod;
            // Update center estimate (gradient ascent)
            z_hat += K * G_hat;
            z_hat = std::clamp(z_hat, z_min, z_max);
            // Decay amplitude
            amplitude *= (1.0f - lambda);
            amplitude = std::max(amplitude, 0.01f);
            prev_y = measurement;
        }

        void reset(float z_init, float z_lo, float z_hi) {
            z_hat = z_init;
            z_min = z_lo; z_max = z_hi;
            amplitude = amplitude_init;
            eta = 0.0f; G_hat = 0.0f; prev_y = 0.0f; t = 0;
        }
    };
    ESCState esc_;

    // --- Lévy height exploration ---
    float levyHeight(float z_current);
    int levy_height_step_remaining_ = 0;
    float levy_height_target_ = 0.3f;

    // --- Significant Layer scanning (WMO radiosonde) ---
    struct LayerPoint {
        float z;
        float concentration;
    };
    std::vector<LayerPoint> layer_profile_;    // measured concentration profile
    std::vector<float> significant_layers_;     // detected significant layer altitudes
    bool calibration_active_ = false;
    int calibration_step_ = 0;
    std::vector<float> calibration_z_sequence_;  // z positions to visit during calibration
    int calibration_index_ = 0;
    float best_calibrated_z_ = 0.3f;

    void startCalibration();
    void significantLayerRecursion(float z_lo, float c_lo, float z_hi, float c_hi,
                                    float threshold, std::vector<LayerPoint>& profile);
    void processCalibrationMeasurement(float z, float concentration);

    // --- Altitude posterior with temporal decay ---
    static constexpr int kNumZBins = 28;  // [0.0, 3.0] in 0.1m steps
    float z_posterior_[28] = {0};          // log-posterior
    float z_decay_rate_ = 0.01f;          // temporal decay rate gamma
    void updateAltitudePosterior(float z, float concentration);
    float getPosteriorBestZ() const;

    // --- MaxConc-z baseline (reviewer criticism #5) ---
    struct ZConcRecord {
        float z;
        float concentration;
        float time;
    };
    std::deque<ZConcRecord> z_conc_history_;
    int max_conc_window_ = 20;
    float maxConcAltitude() const;

    // --- Phase management ---
    int consecutive_miss_threshold_ = 10;  // go back to EXPLORE after N misses
    void updateAltitudePhase(float concentration);
    float selectTargetAltitude();

    // --- Ablation toggles ---
    bool use_esc_altitude_ = true;     // ESC gradient tracking
    bool use_levy_altitude_ = true;    // Lévy height exploration
    bool use_layer_scan_ = true;       // Significant layer scanning
    bool use_altitude_decay_ = true;   // Posterior temporal decay

    // --- Logging ---
    void logAltitudeState();
};
} // namespace GSL