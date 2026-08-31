#pragma once
#include <gsl_server/algorithms/Common/Algorithm.hpp>
#include <string>
#include <filesystem>
#include <fstream>
#include <unordered_map>

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

        void initializeCPIR();
        void recordCPIRRawSample(float measuredPpm);
        void finalizeCPIRPhysicalStop();
        void applyCPIRPosterior(uint64_t sourceUpdateId, double simTime);

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

        // Causal Physical Intervention Reachability (M1 only).  This state is
        // unreachable in the authoritative OFF mode.
        struct CPIRSample
        {
            int timeIndex = -1;
            size_t nativeCellIndex = 0;
            int stopIndex = -1;
            int stopSampleIndex = -1;
        };
        bool cpirEnabled = false;
        std::string cpirLookupRoot;
        std::string cpirAuditDirectory;
        std::vector<CPIRSample> cpirTrace;
        std::vector<unsigned char> cpirObservedStopHit;
        bool cpirStopActive = false;
        int cpirCurrentStopIndex = -1;
        int cpirCurrentStopSamples = 0;
        bool cpirCurrentObservedHit = false;
        int cpirLastTimeIndex = -1;
        size_t cpirProcessedSamples = 0;
        size_t cpirCellCount = 0;
        size_t cpirCarrierCount = 0;
        static constexpr size_t cpirMemberCount = 8;
        static constexpr size_t cpirTimeCount = 1500;
        std::unordered_map<size_t, size_t> cpirNativeCellToStream;
        std::vector<std::string> cpirCarrierIds;
        std::unordered_map<std::string, size_t> cpirCarrierToIndex;
        std::vector<std::filesystem::path> cpirWorldPaths;
        std::unordered_map<size_t, std::vector<float>> cpirCellCache;
        std::vector<double> cpirSensorState;
        std::vector<float> cpirDelayOne;
        std::vector<float> cpirDelayTwo;
        std::vector<std::vector<unsigned char>> cpirPredictedStopHit;
        std::ofstream cpirUpdateAudit;

        IF_GUI(PMFS_internal::UI ui;)
    };
} // namespace GSL
