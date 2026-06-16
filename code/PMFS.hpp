#pragma once
#include <gsl_server/algorithms/Common/Algorithm.hpp>

#include <gsl_server/algorithms/PMFS/internal/HitProbability.hpp>
#include <gsl_server/algorithms/PMFS/internal/Settings.hpp>
#include <gsl_server/algorithms/PMFS/internal/PublishersAndSubscribers.hpp>
#include <gsl_server/algorithms/PMFS/internal/HitProbKernel.hpp>
#include <gsl_server/algorithms/PMFS/internal/Simulations.hpp>
#include <gsl_server/algorithms/PMFS/internal/UI.hpp>
#include <gsl_server/algorithms/PMFS/internal/VisibilityMap.hpp>
#include <gsl_server/algorithms/PMFS/MovingStatePMFS.hpp>

#include <gsl_server/core/ConditionalMacros.hpp>
#include <uav_gsl_review/EvidenceGate.hpp>
#include <uav_gsl_review/DirectionalDeconvRefiner.hpp>
#include <uav_gsl_review/ReliabilityGate.hpp>
#include <gsl_server/pwc/PwcCorrector.hpp>

namespace GSL
{
    class PMFS : public Algorithm
    {
        friend class MovingStatePMFS;
        friend class PMFS_internal::Simulations;
        friend struct PMFS_internal::SimulationSource;
#ifdef USE_GUI
        friend class PMFS_internal::UI;
#endif
        using HashSet = std::unordered_set<Vector2Int>;

        using HitProbability = PMFS_internal::HitProbability;
        using HitProbKernel = PMFS_internal::HitProbKernel;

    public:
        PMFS(std::shared_ptr<rclcpp::Node> _node);
        void Initialize() override;
        void OnUpdate() override;

    protected:
        void declareParameters() override;
        void onGetMap(const nav_msgs::msg::OccupancyGrid::SharedPtr msg) override;
        void processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection) override;
        GSLResult checkSourceFound() override;
        void saveResultsToFile(GSLResult result) override;
        void OnCompleteNavigation(GSLResult result, State* previousState) override;
        float gasCallback(olfaction_msgs::msg::GasSensor::SharedPtr msg) override;

        template <typename T>
        Grid2D<T> AsGrid(std::vector<T>& vec)
        {
            return Grid2D<T>(vec, occupancy, gridMetadata);
        }

        //-------------Core-------------
        Grid2DMetadata gridMetadata;
        std::vector<double> sourceProbability;
        std::vector<HitProbability> hitProbability;
        std::vector<Occupancy> occupancy;
        std::vector<Vector2> estimatedWindVectors;

        PMFS_internal::Simulations simulations;

        //-------------WCC State-------------
        std::vector<double> prevSourceProbability;
        // Peak-Gas Position Tracker (PGPT)
        double peakGasConcentration = 0.0;
        Vector2 peakGasPosition = {0, 0};
        bool hasPeakGas = false;
        
        // HCE/PSDE/SDR hit statistics. These are collected only when their flags are enabled.
        double hce_weighted_x = 0.0;
        double hce_weighted_y = 0.0;
        double hce_weight_mass = 0.0;
        double hce_weighted_x2 = 0.0;  // sum(C_i * x_i^2)
        double hce_weighted_y2 = 0.0;  // sum(C_i * y_i^2)
        double hce_wind_sin_accum = 0.0;
        double hce_wind_cos_accum = 0.0;
        double hce_wind_speed_accum = 0.0;
        int hce_hit_count = 0;
        bool hceRefinementDone = false;
        bool hceRefinementActive = false;
        Vector3 hceRefinedTarget = {0, 0, 0};

        // ADC: Adaptive Dwell Control state
        int adc_total_detections = 0;
        int adc_total_samples = 0;

        // SET: Sequential Evidence Testing state
        int set_hit_count = 0;
        int set_total_count = 0;
        int set_consecutive_hits = 0;
        bool set_tracking_approved = false;

        // FRG: Fault-Reactive Guard state
        int frg_no_hit_streak = 0;
        bool frg_recovery_active = false;
        int frg_recovery_steps_left = 0;
        int frg_recovery_phase = 0; // 0=go to last hit, 1=spiral
        Vector2 frg_last_hit_pos = {0, 0};
        bool frg_has_last_hit = false;
        double frg_spiral_angle = 0.0;

        //-------------Data-------------
        PMFS_internal::Settings settings;
        PMFS_internal::PublishersAndSubscribers pubs;

        //-------------Utils-------------
        bool paused = false;
        std::optional<VisibilityMap> visibilityMap;
        uint iterationsCounter;
        double last_concentration{0.0};
        double last_windSpeed{0.0};
        double last_windDirection{0.0};

        // BWE wind-smoothing state. Class members avoid cross-run contamination.
        bool bwe_initialized{false};
        double bwe_ema_sin{0.0};
        double bwe_ema_cos{1.0};
        double bwe_ema_speed{0.0};
        int number_of_updates{0};


        // PWC: Plume Wind Correction
        std::unique_ptr<uav_gsl_pwc::PwcCorrector> pwcCorrector_;

        // TDC: Temporal Deconvolution state
        double tdc_ema_dCdt{0.0};  // EMA-smoothed derivative for noise robustness
        // MTI: MOX Temporal Integration state
        double mti_ema_concentration{0.0};
        int mti_extra_hits_{0};
        double tdc_prev_concentration{0.0};
        int total_gas_detections_{0};
        // Raw hit positions (before TDC modification) for SDR
        std::vector<std::pair<double,double>> raw_hit_positions_;
        std::vector<double> raw_hit_concentrations_;
        // Raw peak gas (pre-TDC)
        double raw_peakGasConcentration{0.0};
        Vector2 raw_peakGasPosition{0,0};
        bool raw_hasPeakGas{false};
        int raw_hce_hit_count{0};
        std::vector<double> mhc_cleaned_;

        // PSDE legacy state
        double mac_estimated_distance{-1.0};

        // ASA: Accumulated Source probability Averaging (temporal ensemble)
        std::vector<double> asa_accumulated_map_;
        int asa_update_count_{0};

        // HSPB: vote grid for visualization/debug
        std::vector<double> hspb_vote_grid_;


        // Review innovation module state (EGS, DIRL, RGC)
        std::vector<uav_gsl_review::HitSample> review_hit_archive_;
        double review_first_hit_time_s{-1.0};
        std::string review_last_egs_reason_{"disabled"};
        bool review_last_egs_allow_{false};
        std::string review_last_rgc_reason_{"disabled"};
        double review_last_dirl_x_{std::numeric_limits<double>::quiet_NaN()};
        double review_last_dirl_y_{std::numeric_limits<double>::quiet_NaN()};
        double review_last_dirl_peak_ratio_{0.0};
        double review_last_dirl_entropy_{1.0};
        bool review_last_dirl_valid_{false};
        IF_GUI(PMFS_internal::UI ui;)
    };
} // namespace GSL
