#pragma once
#include <gsl_server/algorithms/Common/Algorithm.hpp>
#include <string>

#include <gsl_server/algorithms/PMFS/internal/HitProbability.hpp>
#include <gsl_server/algorithms/PMFS/internal/Settings.hpp>
#include <gsl_server/algorithms/PMFS/internal/PublishersAndSubscribers.hpp>
#include <gsl_server/algorithms/PMFS/internal/HitProbKernel.hpp>
#include <gsl_server/algorithms/PMFS/internal/Simulations.hpp>
#include <gsl_server/algorithms/PMFS/internal/UI.hpp>
#include <gsl_server/algorithms/PMFS/internal/VisibilityMap.hpp>
#include <gsl_server/algorithms/PMFS/MovingStatePMFS.hpp>

#include <gsl_server/core/ConditionalMacros.hpp>

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

        //-------------Data-------------
        PMFS_internal::Settings settings;
        PMFS_internal::PublishersAndSubscribers pubs;

        //-------------Utils-------------
        bool paused = false;
        std::optional<VisibilityMap> visibilityMap;
        uint iterationsCounter;
        bool hoverForwardExportEnabled = false;
        bool hoverForwardExportCompleteGrid = false;
        bool hoverForwardExportEveryMeasurement = false;
        bool hoverForwardExportContinuousExposure = false;
        bool hoverForwardExportCompleteGridDone = false;
        std::string hoverForwardExportDirectory;
        bool p2ShadowEnabled = false;
        std::string p2ShadowDirectory;
        uint64_t p2ShadowGlobalSeed = 0;
        int p2ShadowReplicas = 0;
        uint64_t p2ShadowTransportSubstream = 0;
        uint64_t p2SourceUpdateId = 0;
        // Monotone completed StopAndMeasure block identity for the optional
        // PC-ACI/A9 event carrier.  It does not alter the native PMFS path.
        uint64_t completedMeasurementBlockId = 0;
        bool tadmEnabled = false;
        std::string pfdiMode = "off";
        std::string tnqcMode = "off";
        // Optional inference-to-control coupling.  The frozen OFF path keeps
        // this at zero; the protected ON path can use the PFDI posterior when
        // ranking the next measurement goal.
        double posteriorGuidanceWeight = 0.0;
        std::string tadmDirectory;
        int tadmPriorSet = 0;
        uint64_t tadmGlobalSeed = 0;
        int tadmReplicas = 0;
        uint64_t tadmTransportSubstream = 0;
        bool contextBankExportEnabled = false;
        std::string contextBankExportDirectory;
        double contextBankPreviousSimTime = -1.0;

        IF_GUI(PMFS_internal::UI ui;)
    };
} // namespace GSL
