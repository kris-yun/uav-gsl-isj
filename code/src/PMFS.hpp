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
        
        // HCE: Hit Centroid Estimator (sensor network localization)
        double hce_weighted_x = 0.0;
        double hce_weighted_y = 0.0;
        double hce_weight_mass = 0.0;
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

        // PWC: Plume Wind Correction
        std::unique_ptr<uav_gsl_pwc::PwcCorrector> pwcCorrector_;

        // TDC: Temporal Deconvolution state
        double tdc_prev_concentration{0.0};

        // MAC: Multi-Altitude Constraint state
        double mac_estimated_distance{-1.0};

        IF_GUI(PMFS_internal::UI ui;)
    };
} // namespace GSL
