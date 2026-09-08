#pragma once
#include <gsl_server/algorithms/Common/Utils/NQAQuadtree.hpp>
#include <gsl_server/algorithms/PMFS/internal/HitProbability.hpp>
#include <gsl_server/algorithms/PMFS/internal/Settings.hpp>
#include <gsl_server/algorithms/PMFS/internal/VisibilityMap.hpp>
#include <opencv2/core.hpp>
#include <geometry_msgs/msg/pose.hpp>
#include <array>
#include <string>
#include <mutex>
#include <memory>
#include <cstdint>
#include "gsl_server/algorithms/PMFS/internal/EventKeyedRng.hpp"

namespace GSL
{
    class PMFS;
}

namespace GSL::PMFS_internal
{

    struct TadmPriorParameters
    {
        std::array<double, 3> mu{};
        std::array<double, 9> lambda{};
        double sigma2 = 0.0;
        int setId = 0;
    };

    struct Filament
    {
        Vector2 position;
    };

    struct SimulationSource
    {
        enum Mode
        {
            Quadtree,
            Point
        };

        const Mode mode;
        const Utils::NQA::Node* nqaNode;
        const Vector2 point;
        const Grid2DMetadata& metadata;
        const EventKeyedTransportRng* keyedRng = nullptr;
        mutable Vector2 firstSampledPoint = Vector2(0, 0);
        mutable bool firstSampledPointValid = false;
        mutable uint64_t pointDrawIndex = 0;

        SimulationSource(const Vector2& _point, const Grid2DMetadata& _metadata,
                         const EventKeyedTransportRng* _keyedRng = nullptr)
            : mode(Mode::Point), nqaNode(nullptr), point(_point), metadata(_metadata), keyedRng(_keyedRng)
        {}
        SimulationSource(const Utils::NQA::Node* _node, const Grid2DMetadata& _metadata,
                         const EventKeyedTransportRng* _keyedRng = nullptr)
            : mode(Mode::Quadtree), nqaNode(_node), point(0, 0), metadata(_metadata), keyedRng(_keyedRng)
        {}

        Vector2 getPoint() const;
        Vector2 firstSampledSourcePoint() const { return firstSampledPoint; }
    };

    class Simulations
    {
        using HashSet = std::unordered_set<Vector2Int>;

    public:
        struct SimulationResult
        {
            bool valid = false;
            std::vector<float> hitMap;
            std::vector<std::vector<float>> transportMemberHitMaps;
            long double sourceProb = 0.0L;
            Utils::NQA::Node* leaf = nullptr;
        };

    public:
        Simulations(Grid2D<HitProbability> _measuredHitProb, Grid2D<double> _sourceProb, Grid2D<Vector2> _wind,
                    const PMFS_internal::SimulationSettings& _settings)
            : settings(_settings), measuredHitProb(_measuredHitProb), sourceProb(_sourceProb), wind(_wind)
        {}

        void initializeMap(const std::vector<std::vector<uint8_t>>& occupancyMap);
        void configureNativeDeterminism(uint64_t globalSeed, uint64_t transportSubstream);
        void setNativeSourceUpdateId(uint64_t sourceUpdateId);
        void configureEventEvidence(bool enabled, int transportReplicas, bool contrastiveRatio = false,
                                    bool centeredLogOdds = false,
                                    bool sequentialAssimilation = false);
        void recordEventEvidence(const Vector2& position, bool hit, double concentration,
                                 double threshold, uint64_t blockId);
        void updateSourceProbability(float refineFraction);
        void makeSimulationImage(const SimulationSource& source);
        // Read-only HOVER export: uses the unmodified PMFS filament simulator.
        // It never reads or writes the PMFS score, posterior, planner, or stop state.
        void configureReadOnlyForwardExport(bool enabled, const std::string& directory, const std::string& runUUID,
                                            const std::string& pmfsParametersHash, const std::string& mapHash,
                                            const std::string& windHash, const std::string& codeHash);
        bool exportCompletePointCandidateGrid(bool exportContinuousExposure = false);
        void configureP2Shadow(bool enabled, const std::string& directory, const std::string& runUUID,
                               uint64_t globalSeed, int replicas, uint64_t transportSubstream);
        void exportP2PredictiveEnsembleSnapshot(uint64_t sourceUpdateId, double simTime);
        void configureTADM(bool enabled, const std::string& directory, const std::string& runUUID,
                           int priorSet, uint64_t globalSeed, int replicas, uint64_t transportSubstream,
                           const std::string& mode = "joint");
        // Record one completed, pre-map hit/miss block and its sensing
        // location.  PC-ACI freezes these block views at each source update.
        void recordPCACIEvent(const Vector2& position, bool hit,
                              double concentration, double threshold,
                              double windSpeed, double windDirection,
                              uint64_t blockId = 0, double simTime = 0.0);
        void beginTADMUpdate(uint64_t sourceUpdateId, double simTime);
        void configureContextBankExport(bool enabled, const std::string& directory, const std::string& runUUID);
        void beginContextBankUpdate(uint64_t sourceUpdateId, double simTime);
        void exportContextBankState(uint64_t sourceUpdateId, double simTime, double timeSincePreviousUpdate,
                                    const geometry_msgs::msg::Pose& robotPose);
        double probabilitySingleFrequency(double measured, double simulated) const;
        double probabilityFromSingleCell(HitProbability measured, double simulated) const;
        long double sourceProbFromMaps(const Grid2D<HitProbability>& hitRandomVariable, const std::vector<float>& hitMap) const;
        long double sourceProbFromEvents(const std::vector<float>& hitMap) const;
        // Isolated fixed-context replay entrypoint. This exposes only the
        // existing PMFS forward kernel; it cannot read or modify a posterior.
        void runPointForwardReplay(const Vector2& point, std::vector<float>& hitMap,
                                   int timesteps, float deltaTime, float noiseSTDev,
                                   EventKeyedTransportRng* transportRng = nullptr) const;

        std::vector<std::vector<Utils::NQA::Node*>> mapSegmentation;
        std::unique_ptr<Utils::NQA::Quadtree> quadtree;
        std::vector<Utils::NQA::Node> QTleaves;
        std::vector<double> varianceOfHitProb; // calculated from the simulations, used for movement
        std::vector<SimulationResult> resultsFirstLevel;
        VisibilityMap* visibilityMap;

    protected:

        struct LeafScore
        {
            long double score;
            Utils::NQA::Node* leaf;
        };

        std::vector<long double> sourceProbInternal; // calculated from the simulations, used for movement
        const PMFS_internal::SimulationSettings& settings;
        Grid2D<HitProbability> measuredHitProb;
        Grid2D<double> sourceProb;
        Grid2D<Vector2> wind;
        struct EventEvidence
        {
            size_t cell;
            bool hit;
            double concentration;
            double threshold;
            uint64_t blockId;
        };
        bool eventEvidenceEnabled = false;
        bool eventEvidenceContrastiveRatio = false;
        bool eventEvidenceCenteredLogOdds = false;
        bool eventEvidenceSequentialAssimilation = false;
        int eventEvidenceTransportReplicas = 1;
        std::vector<EventEvidence> eventEvidence;
        // Member-specific, candidate-invariant context.  Legacy M1R stores an
        // arithmetic probability mean; CORE M1C stores a mean log-odds so a
        // candidate-common additive nuisance cancels exactly.
        std::vector<std::vector<long double>> eventEvidenceContext;
        size_t eventEvidenceCommittedCount = 0;
        size_t eventEvidenceWindowStart = 0;
        std::vector<long double> eventEvidenceSequentialPosterior;
        bool eventEvidenceSequentialPosteriorValid = false;
        cv::Mat freeSpaceMask;

        bool readOnlyForwardExportEnabled = false;
        std::string readOnlyForwardExportDirectory;
        std::string readOnlyForwardExportRunUUID;
        std::string readOnlyForwardExportPMFSParametersHash;
        std::string readOnlyForwardExportMapHash;
        std::string readOnlyForwardExportWindHash;
        std::string readOnlyForwardExportCodeHash;
        size_t readOnlyForwardExportSnapshot = 0;
        std::string readOnlyForwardExportCurrentDirectory;
        std::mutex readOnlyForwardExportMutex;

        bool contextBankExportEnabled = false;
        std::string contextBankExportDirectory;
        std::string contextBankExportRunUUID;
        uint64_t contextBankSourceUpdateId = 0;
        double contextBankSimTime = 0.0;
        size_t contextBankNativeSimulationCount = 0;
        double contextBankWallStartEpoch = 0.0;
        double contextBankWallEndEpoch = 0.0;

        struct P2ShadowCandidate
        {
            std::string stableID;
            Vector2 point;
            long double nativeScore = 0.0L;
            std::array<int, 4> rect{0, 0, 1, 1};
            bool persistentCarrier = false;
            // One native forward realization is retained as a deterministic
            // physical carrier for candidates that were outside the prior
            // SD 95% replica budget.  It is never used as a scoring replica;
            // it only prevents missing history from being treated as an
            // impossible temporal hypothesis in the next window.
            std::shared_ptr<const std::vector<float>> nativeHitMap;
        };
        bool p2ShadowEnabled = false;
        std::string p2ShadowDirectory;
        std::string p2ShadowRunUUID;
        uint64_t p2ShadowGlobalSeed = 0;
        int p2ShadowReplicas = 0;
        uint64_t p2ShadowTransportSubstream = 0;
        std::vector<P2ShadowCandidate> p2LastEvaluatedCandidates;
        // PC-SD-TFEI uses a deterministic physical carrier instead of the
        // adaptive PMFS quadtree leaves.  The flag is set per isolated binary
        // and never changes the frozen OFF path.
        bool persistentCarrierMode = false;
        std::mutex p2ShadowMutex;
        std::unordered_map<std::string, std::shared_ptr<std::vector<float>>> nativeCandidateHitMaps;
        std::mutex nativeCandidateHitMapsMutex;

        bool tadmEnabled = false;
        std::string pfdiMode = "off";
        std::string tadmDirectory;
        std::string tadmRunUUID;
        TadmPriorParameters tadmPrior;
        uint64_t tadmGlobalSeed = 0;
        int tadmReplicas = 0;
        uint64_t tadmTransportSubstream = 0;
        uint64_t tadmSourceUpdateId = 0;
        uint64_t nativeRandomSeed = 0;
        uint64_t nativeSourceUpdateId = 0;
        uint64_t nativeTransportSubstream = 0x4E4154495645504DULL;
        bool nativeDeterministicRng = false;
        double tadmSimTime = 0.0;
        // SD-TFEI support expansion is a sequential inference decision.  A
        // single stochastic plume realization may produce a coherent but
        // wrong basin, so global rescue requires the same module basin to be
        // confirmed in two consecutive source-update windows.
        bool sdPreviousModuleTopValid = false;
        Vector2 sdPreviousModuleTop = Vector2(0, 0);
        std::array<int, 4> sdPreviousModuleRect{0, 0, 1, 1};
        uint64_t sdPreviousModuleUpdateId = 0;
        int sdTemporalConfirmationCount = 0;
        // First-difference SD-TFEI history.  Adaptive quadtree leaves can
        // change IDs while representing the same physical source location;
        // the online implementation therefore keeps both the exact ID bank
        // and a deterministic physical-grid registration bank.
        bool sdTemporalHistoryValid = false;
        bool sdTemporalDifferenceActive = false;
        uint64_t sdPreviousInferenceUpdateId = 0;
        std::vector<double> sdPreviousObserved;
        std::vector<char> sdPreviousSupportMask;
        // PC-ACI sequential posterior state.  The previous normalized
        // source posterior is the only prior allowed in the next update;
        // the current native posterior is never multiplied by the ACI
        // likelihood on the same observation.
        // PC-ACI owns a causal state that is independent of the native PMFS
        // planner posterior.  A rejected update must never contaminate this
        // state with the current native posterior.
        bool pcAciCausalStateAvailable = false;
        uint64_t pcAciLastAcceptedUpdateId = 0;
        bool pcAciAcceptedThisUpdate = false;
        std::vector<long double> pcAciCausalPosteriorGrid;
        // Explicit geometry-only design prior; never copied from native PMFS.
        std::vector<long double> pcAciDesignPriorGrid;
        std::vector<long double> pcAciIncomingNativePriorSnapshot;
        bool pcAciA9DesignWarmupSeen = false;
        struct PCAciEvent
        {
            Vector2 position;
            double hit = 0.0;
            double concentration = 0.0;
            double threshold = 0.1;
            double windSpeed = 0.0;
            double windDirection = 0.0;
            uint64_t blockId = 0;
            double simTime = 0.0;
        };
        std::vector<PCAciEvent> pcAciPendingEvents;
        std::vector<PCAciEvent> pcAciActiveEvents;
        // Truth-blind sequential evidence savings for ME-ACI.  Events from an
        // abstained window remain here until temporal and spatial
        // identifiability are jointly satisfied.
        std::vector<PCAciEvent> meAciEvidenceReservoir;
        struct MEAciRouteState
        {
            std::array<double, 64> memory{};
            std::array<double, 64> cumulativeLogLikelihood{};
            std::array<double, 64> previousTime{};
            std::array<unsigned char, 64> initialized{};
        };
        std::unordered_map<std::string, MEAciRouteState> meAciRouteStates;
        std::unordered_map<std::string, double> pcAciPreviousTransportRank;
        std::vector<std::string> pcAciPreviousTopSupport;
        int pcAciTemporalReplicationStreak = 0;
        std::unordered_map<std::string, double> pcAciCumulativeHoughRank;
        std::unordered_map<std::string, double> pcAciCumulativeIntensityRank;
        uint64_t pcAciTomographyWindowCount = 0;
        // Ensemble-calibrated EC-ECDL history.  Rows are indexed by the
        // frozen persistent carrier and replica identity; coordinates are
        // appended only after every mathematical validity audit passes.
        bool ecEdclHistoryValid = false;
        std::vector<std::string> ecEdclCarrierIds;
        std::vector<int> ecEdclBlockDimensions;
        std::vector<std::vector<double>> ecEdclCalibrationHistory;
        std::vector<std::vector<double>> ecEdclScoringResidualHistory;
        std::vector<double> ecEdclCumulativeMemberScores;
        std::vector<double> ecEdclPreviousCovariance;
        int ecEdclPreviousCovarianceDim = 0;
        // Physical-latent forecast--analysis history for the persistent
        // carrier.  The raw field and projected replica features are kept
        // separately from the native-logit history so the next update can
        // form a source-relative temporal increment.
        std::vector<float> sdPreviousObservedField;
        std::unordered_map<std::string, std::vector<std::vector<double>>> sdPreviousPhysicalReplicaFeatures;
        std::unordered_map<std::string, std::vector<std::vector<double>>> sdPreviousCandidateReplicas;
        std::unordered_map<std::string, std::vector<std::vector<double>>> sdPreviousCandidateReplicasByGrid;
        std::mutex tadmMutex;

        void exportCandidateHitMap(const std::string& stableID, const Vector2& source, const std::vector<float>& hitMap);
        void exportNativeCandidateRecord(const std::string& stableID, const Vector2& source,
                                         const Vector2& nativeSourcePoint, long double sourceProb,
                                         const std::vector<float>& hitMap);
        void exportCandidateExposureMap(const std::string& stableID, const Vector2& source, const std::vector<float>& exposureMap);
        bool applyA9TvSdTfei();
        bool applyMEAci();
        bool applyEnsembleEcEdcl();
        bool applyTADMPosterior();

        SimulationResult runSimulation(std::vector<LeafScore>& nodes, size_t index);
        void initializeContrastiveEventContext(const std::vector<SimulationResult>& results);
        void applyContrastiveEventEvidence(std::vector<SimulationResult>& results,
                                           std::vector<LeafScore>& scores);
        long double sourceProbFromContrastiveEvents(
            const std::vector<std::vector<float>>& transportMemberHitMaps) const;
        void moveFilament(Filament& filament, Vector2Int& indices, float deltaTime, float noiseSTDev,
                          EventKeyedTransportRng* transportRng, uint64_t& drawIndex) const;
        void simulateSourceInPosition(const SimulationSource& source, std::vector<float>& hitMap, bool warmup,
                                      int timesteps, float deltaTime, float noiseSTDev,
                                      std::vector<float>* exposureMapBeforeNormalization = nullptr,
                                      EventKeyedTransportRng* transportRng = nullptr) const;
        bool filamentIsOutside(const Filament& filament) const;
        bool moveAlongPath(Vector2& beginning, const Vector2& end) const;

        void blurHitMap(cv::Mat& asImage) const;
        void displayImage(const std::vector<float>& hitMap, const std::string& imageName = "simResult") const;
    };
} // namespace GSL::PMFS_internal
