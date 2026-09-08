#include "gsl_server/algorithms/Common/States/ManualNavigation.hpp"
#include <angles/angles.h>
#include <gsl_server/algorithms/Common/Utils/Math.hpp>
#include <gsl_server/algorithms/Common/Utils/Pointers.hpp>
#include <gsl_server/algorithms/PMFS/PMFS.hpp>
#include <fstream>
#include <filesystem>
#include <iomanip>
#include <cmath>
#include <stdexcept>
#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>
#include <gsl_server/algorithms/PMFS/PMFSViz.hpp>

// Initialization
namespace GSL
{
    using WindEstimation = gmrf_msgs::srv::WindEstimation;
    PMFS::PMFS(std::shared_ptr<rclcpp::Node> _node)
        : Algorithm(_node),
          simulations(Grid2D<HitProbability>(hitProbability, occupancy, gridMetadata),
                      Grid2D<double>(sourceProbability, occupancy, gridMetadata),
                      Grid2D<Vector2>(estimatedWindVectors, occupancy, gridMetadata),
                      settings.simulation),
          pubs(node->get_clock())
              IF_GUI(, ui(this))
    {}

    // A lot of the initialization is done inside of the map callback, rather than here. That is because we need to know the map beforehand
    void PMFS::Initialize()
    {
        Algorithm::Initialize();
        PMFSLib::InitializePublishers(pubs, node);

#if USE_GUI
        if (!settings.visualization.headless)
            ui.run();
#endif

        iterationsCounter = 0;

        waitForGasState = std::make_unique<WaitForGasState>(this);
        waitForMapState = std::make_unique<WaitForMapState>(this);
        waitForMapState->shouldWaitForGas = false;

        stopAndMeasureState = std::make_unique<StopAndMeasureState>(this);
#if DISABLE_NAVIGATION
        movingState = std::make_unique<ManualNavigationState>(this);
#else
        movingState = std::make_unique<MovingStatePMFS>(this);
#endif
        stateMachine.forceSetState(waitForMapState.get());
    }

    void PMFS::declareParameters()
    {
        Algorithm::declareParameters();
        PMFSLib::GetHitProbabilitySettings(*this, settings.hitProbability);
        PMFSLib::GetSimulationSettings(*this, settings.simulation);
        PMFSLib::GetDeclarationSettings(*this, settings.declaration);

        // number of cells in each direction that we add to the open move set in each step
        settings.movement.openMoveSetExpasion = getParam<int>("openMoveSetExpasion", 5);
        settings.movement.explorationProbability = getParam<double>("explorationProbability", 0.1);
        settings.movement.initialExplorationMoves = getParam<int>("initialExplorationMoves", 5);
        settings.movement.distanceWeight = getParam<double>("distanceWeight", 0.1);

        settings.visualization.markers_height = getParam<double>("markers_height", 0);
        hoverForwardExportEnabled = getParam<bool>("hover_forward_export_enabled", false);
        hoverForwardExportCompleteGrid = getParam<bool>("hover_forward_export_complete_grid", false);
        hoverForwardExportEveryMeasurement = getParam<bool>("hover_forward_export_every_measurement", false);
        hoverForwardExportContinuousExposure = getParam<bool>("hover_forward_export_continuous_exposure", false);
        hoverForwardExportDirectory = getParam<std::string>("hover_forward_export_directory", "");
        p2ShadowEnabled = getParam<bool>("p2_shadow_enabled", false);
        p2ShadowDirectory = getParam<std::string>("p2_shadow_directory", "");
        p2ShadowGlobalSeed = getParam<int64_t>("p2_global_seed", 0);
        p2ShadowReplicas = getParam<int>("p2_shadow_replicas", 0);
        p2ShadowTransportSubstream = getParam<int64_t>("p2_transport_substream", 0x5053465354524E53LL);
        tadmEnabled = getParam<bool>("tadm_enabled", false);
        pfdiMode = getParam<std::string>("pfdi_mode", tadmEnabled ? "joint" : "off");
        jointSourceExchangeDir = getParam<std::string>("joint_source_exchange_dir", "");
        if (!jointSourceExchangeDir.empty())
        {
            jointRunId = getParam<std::string>("run_uuid", "unknown");
            if (pfdiMode != "off" || tadmEnabled || jointRunId == "unknown" || jointRunId.empty() ||
                jointRunId.find_first_of(" \t\r\n") != std::string::npos ||
                !std::filesystem::path(jointSourceExchangeDir).is_absolute() ||
                !std::filesystem::is_directory(jointSourceExchangeDir) ||
                !std::filesystem::is_empty(jointSourceExchangeDir))
                throw std::invalid_argument("JOINT_REQUIRES_EXCLUSIVE_OFF_MODE_AND_FRESH_ABSOLUTE_EXCHANGE");
        }
        if (pfdiMode != "off" && pfdiMode != "cer_m1" && pfdiMode != "cer_m1_m2" &&
            pfdiMode != "cer_ratio_m1" && pfdiMode != "cer_ratio_m1_m2" &&
            pfdiMode != "cer_core_m1" && pfdiMode != "cer_core_seq_m1" &&
            pfdiMode != "cpir_m1" && pfdiMode != "cpir_a1" && pfdiMode != "cpir_a2" &&
            pfdiMode != "cpir_a3" && pfdiMode != "cpir_m1_m3" && pfdiMode != "ctpi_f00" && pfdiMode != "ctpi_f01" && pfdiMode != "ctpi_f10" &&
            pfdiMode != "ctpi_f11" && pfdiMode != "sd" && pfdiMode != "tadm" && pfdiMode != "joint" &&
            pfdiMode != "al" && pfdiMode != "pc_aci" && pfdiMode != "me_aci" && pfdiMode != "me_aci_shadow" &&
            pfdiMode != "ec_edcl" && pfdiMode != "ec_edcl_shadow")
            throw std::invalid_argument("pfdi_mode must be off, cer_m1, cer_m1_m2, cer_ratio_m1, cer_ratio_m1_m2, cer_core_m1, cer_core_seq_m1, cpir_m1, cpir_a1, cpir_a2, cpir_a3, cpir_m1_m3, ctpi_f00, ctpi_f01, ctpi_f10, ctpi_f11, sd, tadm, joint, al, pc_aci, me_aci, me_aci_shadow, ec_edcl, or ec_edcl_shadow");
        eventEvidenceEnabled = pfdiMode == "cer_m1" || pfdiMode == "cer_m1_m2" ||
                               pfdiMode == "cer_ratio_m1" || pfdiMode == "cer_ratio_m1_m2" ||
                               pfdiMode == "cer_core_m1" || pfdiMode == "cer_core_seq_m1";
        eventEvidenceContrastiveRatio = pfdiMode == "cer_ratio_m1" || pfdiMode == "cer_ratio_m1_m2" ||
                                        pfdiMode == "cer_core_m1" || pfdiMode == "cer_core_seq_m1";
        eventEvidenceCenteredLogOdds = pfdiMode == "cer_core_m1" || pfdiMode == "cer_core_seq_m1";
        eventEvidenceSequentialAssimilation = pfdiMode == "cer_core_seq_m1";
        eventEvidenceTransportReplicas = (pfdiMode == "cer_m1_m2" || pfdiMode == "cer_ratio_m1_m2") ? 3 : 1;
        ctpiPlannerEnabled = pfdiMode == "ctpi_f10" || pfdiMode == "ctpi_f11";
        ctpiTSDCEnabled = pfdiMode == "ctpi_f01" || pfdiMode == "ctpi_f11";
        cpirEnabled = pfdiMode == "cpir_m1" || pfdiMode == "cpir_a1" || pfdiMode == "cpir_a2" || pfdiMode == "cpir_a3" || pfdiMode == "cpir_m1_m3" ||
                      pfdiMode == "ctpi_f00" || pfdiMode == "ctpi_f01" || pfdiMode == "ctpi_f10" || pfdiMode == "ctpi_f11";
        tadmEnabled = pfdiMode != "off" && !cpirEnabled && !eventEvidenceEnabled;
        if (cpirEnabled)
        {
            const int settleSamples = getParam<int>("measurement_settle_samples", -1);
            const int blockSamples = getParam<int>("measurement_block_samples", -1);
            if (settleSamples != 0 || blockSamples <= 0 ||
                settings.hitProbability.maxUpdatesPerStop * blockSamples != 80)
                throw std::invalid_argument(
                    "CPIR requires measurement_settle_samples=0 and "
                    "maxUpdatesPerStop*measurement_block_samples=80");
            if (std::abs(settings.simulation.deltaTime - 0.2) > 1.0e-12)
                throw std::invalid_argument("CPIR requires deltaTime=0.2");
            if (std::abs(thresholdGas - 0.1) > 1.0e-12)
                throw std::invalid_argument("CPIR requires th_gas_present=0.1");
        }
        cpirLookupRoot = getParam<std::string>("cpir_lookup_root", "");
        cpirAuditDirectory = getParam<std::string>("cpir_audit_directory", "");
        posteriorGuidanceWeight = std::clamp(getParam<double>("posterior_guidance_weight", 0.0), 0.0, 1.0);
        if (cpirEnabled && std::abs(posteriorGuidanceWeight) > 1.0e-12)
            throw std::invalid_argument("CPIR/CTPI posterior_guidance_weight must remain 0; CTPI M3 has its own frozen information planner");
        ctpiHorizontalSpeedMps = getParam<double>("ctpi_m3_horizontal_speed_mps", 0.4);
        if (ctpiPlannerEnabled && std::abs(ctpiHorizontalSpeedMps - 0.4) > 1.0e-12)
            throw std::invalid_argument("CTPI M3 horizontal speed is frozen at 0.4 m/s");
        tadmDirectory = getParam<std::string>("tadm_directory", "");
        tadmPriorSet = getParam<int>("tadm_prior_set", 0);
        tadmGlobalSeed = getParam<int64_t>("tadm_global_seed", 0);
        tadmReplicas = getParam<int>("tadm_replicas", 4);
        tadmTransportSubstream = getParam<int64_t>("tadm_transport_substream", 0x5441444D54524E53LL);
        contextBankExportEnabled = getParam<bool>("context_bank_export_enabled", false);
        contextBankExportDirectory = getParam<std::string>("context_bank_export_directory", "");
        IF_GUI(settings.visualization.headless = getParam<bool>("headless", false));
    }

    void PMFS::onGetMap(OccupancyGrid::SharedPtr msg)
    {
        Algorithm::onGetMap(msg);

        int scale = getParam<int>("scale", 65); // scale for dynamic map reduction
        {
            int fc=0, oc=0;
            for (size_t i=0; i<map.data.size(); i++) {
                if (map.data[i]==0) fc++;
                else if (map.data[i]==100) oc++;
            }
            GSL_INFO("[MAP-DEBUG] {}x{} res={:.4f} free={} obs={} unk={} origin=({:.2f},{:.2f})",
                map.info.width, map.info.height, map.info.resolution, fc, oc, (int)map.data.size()-fc-oc,
                map.info.origin.position.x, map.info.origin.position.y);
        }
        PMFSLib::InitMetadata(gridMetadata, map, scale);

        hitProbability.resize(gridMetadata.dimensions.x * gridMetadata.dimensions.y);
        sourceProbability.resize(gridMetadata.dimensions.x * gridMetadata.dimensions.y);
        occupancy.resize(gridMetadata.dimensions.x * gridMetadata.dimensions.y);

        visibilityMap.emplace(gridMetadata.dimensions.x, gridMetadata.dimensions.y,
                              std::max(settings.movement.openMoveSetExpasion, settings.hitProbability.localEstimationWindowSize));

        GridUtils::reduceOccupancyMap(map.data, map.info.width, occupancy, gridMetadata);
        // PMFS_GEOMETRY_EXPORT_C5_V3: opt-in, geometry-only gate evidence.
        const auto geometryExportDir = getParam<std::string>("geometry_export_dir", "");
        const auto exportGeometry = [&](const std::string& stage, const std::vector<Occupancy>& cells) {
            if (geometryExportDir.empty()) return;
            namespace fs = std::filesystem;
            fs::create_directories(geometryExportDir);
            std::ofstream data(fs::path(geometryExportDir) / (stage + "_occupancy.bin"), std::ios::binary);
            for (const auto value : cells) {
                const uint8_t byte = value == Occupancy::Free ? 1 : 0;
                data.write(reinterpret_cast<const char*>(&byte), 1);
            }
            std::ofstream meta(fs::path(geometryExportDir) / (stage + "_meta.json"));
            meta << std::setprecision(12)
                 << "{\n  \"width\": " << gridMetadata.dimensions.x
                 << ",\n  \"height\": " << gridMetadata.dimensions.y
                 << ",\n  \"resolution\": " << gridMetadata.cellSize
                 << ",\n  \"origin_x\": " << gridMetadata.origin.x
                 << ",\n  \"origin_y\": " << gridMetadata.origin.y
                 << ",\n  \"scale\": " << gridMetadata.scale << "\n}\n";
        };
        if (!geometryExportDir.empty()) {
            namespace fs = std::filesystem;
            fs::create_directories(geometryExportDir);
            std::ofstream raw(fs::path(geometryExportDir) / "raw_map.bin", std::ios::binary);
            raw.write(reinterpret_cast<const char*>(map.data.data()), map.data.size());
            std::ofstream rawMeta(fs::path(geometryExportDir) / "raw_map_meta.json");
            rawMeta << std::setprecision(12)
                    << "{\n  \"width\": " << map.info.width
                    << ",\n  \"height\": " << map.info.height
                    << ",\n  \"resolution\": " << map.info.resolution
                    << ",\n  \"origin_x\": " << map.info.origin.position.x
                    << ",\n  \"origin_y\": " << map.info.origin.position.y
                    << ",\n  \"scale\": " << gridMetadata.scale << "\n}\n";
            exportGeometry("reduced", occupancy);
        }
        PMFSLib::InitializeMap(
            Grid2D<HitProbability>(
                hitProbability,
                occupancy,
                gridMetadata),
            simulations,
            *visibilityMap,
            currentCoordinates());

        if (!geometryExportDir.empty()) {
            exportGeometry("pruned", occupancy);
            exportGeometry("k1", occupancy);
            std::ofstream leaves(std::filesystem::path(geometryExportDir) / "quadtree_leaves.csv");
            leaves << "origin_x,origin_y,size_x,size_y,value\n";
            for (const auto& leaf : simulations.QTleaves)
                leaves << leaf.origin.x << ',' << leaf.origin.y << ',' << leaf.size.x << ',' << leaf.size.y << ',' << int(leaf.value) << '\n';
        }

        simulations.configureReadOnlyForwardExport(
            hoverForwardExportEnabled,
            hoverForwardExportDirectory,
            getParam<std::string>("run_uuid", "unknown"),
            getParam<std::string>("hover_forward_pmfs_parameters_hash", "UNSET"),
            getParam<std::string>("hover_forward_map_hash", "UNSET"),
            getParam<std::string>("hover_forward_wind_hash", "UNSET"),
             getParam<std::string>("hover_forward_code_hash", "UNSET"));
        simulations.configureP2Shadow(
            p2ShadowEnabled,
            p2ShadowDirectory,
            getParam<std::string>("run_uuid", "unknown"),
            p2ShadowGlobalSeed,
            p2ShadowReplicas,
            p2ShadowTransportSubstream);
        simulations.configureTADM(
            tadmEnabled,
            tadmDirectory,
            getParam<std::string>("run_uuid", "unknown"),
            tadmPriorSet,
            tadmGlobalSeed,
            tadmReplicas,
            tadmTransportSubstream,
            pfdiMode);
        simulations.configureContextBankExport(
            contextBankExportEnabled,
            contextBankExportDirectory,
            getParam<std::string>("run_uuid", "unknown"));
        // Native PMFS forward simulations run in OpenMP workers.  Bind their
        // source-point and transport draws to (seed, source-update) instead
        // of thread-local RNG state so OFF/ON pairs have a reproducible
        // native contract independent of worker scheduling.
        simulations.configureNativeDeterminism(
            static_cast<uint64_t>(getParam<int64_t>("seed", 0)),
            0x4E4154495645504DULL);
        simulations.configureEventEvidence(eventEvidenceEnabled, eventEvidenceTransportReplicas,
                                           eventEvidenceContrastiveRatio,
                                           eventEvidenceCenteredLogOdds,
                                           eventEvidenceSequentialAssimilation);

        if (cpirEnabled)
            initializeCPIR();
        if (ctpiPlannerEnabled)
        {
            namespace fs = std::filesystem;
            fs::create_directories(cpirAuditDirectory);
            ctpiM3Audit.open(fs::path(cpirAuditDirectory) / "ctpi_m3_action_audit.csv",
                             std::ios::out | std::ios::trunc);
            if (!ctpiM3Audit)
                throw std::runtime_error("CTPI_M3_AUDIT_OPEN");
            ctpiM3Audit << "decision_id,sim_time,mode,decision_sensor_state_ppm,candidate_count,native_goal_x,native_goal_y,native_info_nats,selected_goal_x,selected_goal_y,selected_info_nats,selected_travel_m,prediction_horizon_start_index,action_changed\n";
        }

        // set all variables to the prior probability
        for (HitProbability& h : hitProbability)
            h.setProbability(settings.hitProbability.prior);

        for (double& p : sourceProbability)
            p = 1.0 / gridMetadata.numFreeCells;

        // the wind estimation stuff requires spinning, so it must be done through the function queue
        functionQueue.submit([this]()
                             {
                                 Grid2D<Vector2> windGrid(estimatedWindVectors, occupancy, gridMetadata);
                                 PMFSLib::InitializeWindPredictions(*this,
                                                                    settings.simulation,
                                                                    windGrid,
                                                                    pubs.gmrfWind.request
                                                                        IF_GADEN(, pubs.groundTruthWind.request));
                                 PMFSLib::EstimateWind(settings.simulation.useWindGroundTruth, windGrid, node, pubs.gmrfWind IF_GADEN(, pubs.groundTruthWind));
                                 stateMachine.forceSetState(stopAndMeasureState.get());
                             });
    }

} // namespace GSL

// Core
namespace GSL
{
    using HashSet = std::unordered_set<Vector2Int>;

    void PMFS::OnUpdate()
    {
        if (!paused)
            Algorithm::OnUpdate();


        // Update visualization
        PMFSViz::ShowHitProb(Grid2D<HitProbability>(hitProbability, occupancy, gridMetadata), settings.visualization, pubs);
        PMFSViz::ShowSourceProb(Grid2D<double>(sourceProbability, occupancy, gridMetadata), settings.visualization, pubs);
    }

    void PMFS::processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection)
    {
        static int number_of_updates = 0;
        // G2-M1 v3: record the per-stop downwind direction for the bank-free
        // time-varying plume kernel.
        if (cpirEnabled)
        {
            cpirWindHistoryU.push_back(std::cos(windDirection));
            cpirWindHistoryV.push_back(std::sin(windDirection));
        }

        // Update the gas presence map
        //  ------------------------------
        Grid2D<HitProbability> grid(hitProbability, occupancy, gridMetadata);
        if (concentration > thresholdGas)
        {
            // Gas & wind
            PMFSLib::EstimateHitProbabilities(grid, *visibilityMap, settings.hitProbability, true, windDirection, windSpeed,
                                              gridMetadata.coordinatesToIndices(currentRobotPosition));
            GSL_INFO_COLOR(fmt::terminal_color::yellow, "GAS HIT");
        }
        else
        {
            // Nothing
            PMFSLib::EstimateHitProbabilities(grid, *visibilityMap, settings.hitProbability, false, windDirection, windSpeed,
                                              gridMetadata.coordinatesToIndices(currentRobotPosition));
            GSL_INFO_COLOR(fmt::terminal_color::yellow, "NOTHING ");
        }

        // Preserve one completed StopAndMeasure block event before PMFS
        // spatial smoothing.  A9 consumes this analytic transport view
        // without reading source truth or changing the native map update.
        if (tadmEnabled && (pfdiMode == "pc_aci" || pfdiMode == "ec_edcl" || pfdiMode == "ec_edcl_shadow" ||
                            pfdiMode == "me_aci" || pfdiMode == "me_aci_shadow"))
            simulations.recordPCACIEvent(
                Vector2(currentRobotPosition.x, currentRobotPosition.y),
                concentration > thresholdGas,
                concentration, thresholdGas, windSpeed, windDirection,
                ++completedMeasurementBlockId,
                (node->now() - startTime).seconds());

        // Update the wind estimations
        //  ------------------------------
        PMFSLib::EstimateWind(settings.simulation.useWindGroundTruth,
                              Grid2D<Vector2>(estimatedWindVectors, occupancy, gridMetadata),
                              node,
                              pubs.gmrfWind
                                  IF_GADEN(, pubs.groundTruthWind));

        // Read-only HOVER basis export: exactly the existing PMFS point-source simulator
        // over the frozen free-space grid for this completed measurement block.  It is
        // deliberately before PMFS scoring, does not read PMFS state, and changes no
        // planner, posterior, or stopping transition.
        if (hoverForwardExportEnabled && hoverForwardExportEveryMeasurement)
            simulations.exportCompletePointCandidateGrid(hoverForwardExportContinuousExposure);

        // One completed StopAndMeasure block is one causal observation. Record
        // it before the slower source-update cadence; never count its spatial
        // PMFS propagation as additional observations.
        if (eventEvidenceEnabled)
            simulations.recordEventEvidence(Vector2(currentRobotPosition.x, currentRobotPosition.y),
                                            concentration > thresholdGas,
                                            concentration, thresholdGas,
                                            ++completedMeasurementBlockId);

        // If we have already taken enough measurements in this position, process them and get ready to move to the next location
        // ------------------------------
        number_of_updates++;
        if (number_of_updates >= settings.hitProbability.maxUpdatesPerStop)
        {
            number_of_updates = 0;
            if (cpirEnabled)
                finalizeCPIRPhysicalStop();

            // Simulations are slow, so we only run them every few positions, when the map has had time to meaningfully change
            //----------------------------------------
            bool timeToSimulate = settings.simulation.stepsBetweenSourceUpdates >= 0 &&
                                  iterationsCounter >= settings.movement.initialExplorationMoves &&
                                  iterationsCounter % settings.simulation.stepsBetweenSourceUpdates == 0;
            if (timeToSimulate)
            {
                // simulations.compareRefineFractions();
                ++p2SourceUpdateId;
                const double sourceUpdateSimTime = (node->now() - startTime).seconds();
                if (!jointSourceExchangeDir.empty())
                    requestJointPosterior(p2SourceUpdateId);
                simulations.setNativeSourceUpdateId(p2SourceUpdateId);
                if (tadmEnabled)
                    simulations.beginTADMUpdate(p2SourceUpdateId, sourceUpdateSimTime);
                if (contextBankExportEnabled)
                    simulations.beginContextBankUpdate(p2SourceUpdateId, sourceUpdateSimTime);
                if (cpirEnabled)
                {
                    // CPIR replaces only the source-inference channel.  The
                    // existing PMFS controller still requires a freshly
                    // simulated predictive state (resultsFirstLevel and
                    // varianceOfHitProb) to evaluate information gain.  Run
                    // the native update first, retain its planner-side forward
                    // products, then overwrite the transient native posterior
                    // with the CPIR posterior before the controller sees it.
                    // This keeps planning truth-blind and prevents a stale/zero
                    // variance map without multiplying the native source
                    // likelihood into the CPIR posterior.
                    simulations.updateSourceProbability(settings.simulation.refineFraction);
                    if (simulations.varianceOfHitProb.size() != sourceProbability.size())
                        throw std::runtime_error("CPIR_PLANNER_VARIANCE_SIZE");
                    bool anyPositivePlannerVariance = false;
                    for (size_t cell = 0; cell < simulations.varianceOfHitProb.size(); ++cell)
                    {
                        if (occupancy[cell] != Occupancy::Free)
                            continue;
                        const double value = simulations.varianceOfHitProb[cell];
                        if (!(std::isfinite(value) && value >= 0.0))
                            throw std::runtime_error("CPIR_PLANNER_VARIANCE_INVALID");
                        anyPositivePlannerVariance = anyPositivePlannerVariance || value > 0.0;
                    }
                    if (!anyPositivePlannerVariance || simulations.resultsFirstLevel.empty())
                        throw std::runtime_error("CPIR_PLANNER_FORWARD_STATE_EMPTY");
                    applyCPIRPosterior(p2SourceUpdateId, sourceUpdateSimTime);
                    GSL_INFO("CPIR planner refresh {} PASS: native forward products retained, CPIR source posterior restored",
                             p2SourceUpdateId);
                }
                else
                    simulations.updateSourceProbability(settings.simulation.refineFraction);
                // Keep native forward products for the existing controller,
                // but do not multiply native compatibility into joint evidence.
                if (!jointSourceExchangeDir.empty())
                    applyJointPosterior(p2SourceUpdateId);
                if (contextBankExportEnabled)
                {
                    simulations.exportContextBankState(
                        p2SourceUpdateId,
                        sourceUpdateSimTime,
                        contextBankPreviousSimTime < 0 ? -1.0 : sourceUpdateSimTime - contextBankPreviousSimTime,
                        currentRobotPose.pose.pose);
                    contextBankPreviousSimTime = sourceUpdateSimTime;
                }
                if (p2ShadowEnabled)
                    simulations.exportP2PredictiveEnsembleSnapshot(p2SourceUpdateId, sourceUpdateSimTime);
                if (hoverForwardExportCompleteGrid && !hoverForwardExportCompleteGridDone)
                    hoverForwardExportCompleteGridDone = simulations.exportCompletePointCandidateGrid(hoverForwardExportContinuousExposure);
            }

            // Movement
            movingState->chooseGoalAndMove();

            iterationsCounter++;
        }
        else
            stateMachine.forceResetState(stopAndMeasureState.get());

        // Source estimate logging (read-only, does not affect algorithm)
        static std::ofstream seTraceFile;
        static bool seTraceInit = false;
        static int seCycleCount = 0;
        if (!seTraceInit) {
            std::string sePath = getParam<std::string>("source_estimate_trace_file", "");
            if (!sePath.empty()) {
                seTraceFile.open(sePath, std::ios::out | std::ios::trunc);
                if (seTraceFile.is_open()) {
                    seTraceFile << "run_uuid,measurement_cycle_id,sim_time,method,estimate_available,"
                        << "estimate_semantics,estimate_x,estimate_y,estimate_z,"
                        << "posterior_entropy,posterior_variance,covariance_trace,"
                        << "candidate_count,particle_ess,source_declared,declaration_reason,"
                        << "stop_variance_threshold,would_declare_source,"
                        << "actual_stop_triggered,algorithm_declared_success\n";
                    seTraceInit = true;
                }
            }
        }
        if (seTraceInit && seTraceFile.is_open()) {
            seCycleCount++;
            // Find MAP cell
            double maxProb = -1;
            int mapIdx = -1;
            for (int i = 0; i < (int)sourceProbability.size(); i++) {
                if (occupancy[i] == Occupancy::Free && sourceProbability[i] > maxProb) {
                    maxProb = sourceProbability[i];
                    mapIdx = i;
                }
            }
            // Compute entropy
            double entropy = 0;
            int candidateCount = 0;
            for (int i = 0; i < (int)sourceProbability.size(); i++) {
                if (occupancy[i] == Occupancy::Free && sourceProbability[i] > 0) {
                    entropy -= sourceProbability[i] * std::log(sourceProbability[i] + 1e-30);
                    if (sourceProbability[i] > 1.0 / gridMetadata.numFreeCells * 2)
                        candidateCount++;
                }
            }
            double simTime = (node->now() - startTime).seconds();
            std::string runUUID = getParam<std::string>("run_uuid", "unknown");
            // Compute weighted posterior variance
            double mean_x = 0, mean_y = 0;
            double total_prob = 0;
            for (int i = 0; i < (int)sourceProbability.size(); i++) {
                if (occupancy[i] == Occupancy::Free && sourceProbability[i] > 0) {
                    Vector2 coords = gridMetadata.indexToCoordinates(i);
                    mean_x += sourceProbability[i] * coords.x;
                    mean_y += sourceProbability[i] * coords.y;
                    total_prob += sourceProbability[i];
                }
            }
            if (total_prob > 0) { mean_x /= total_prob; mean_y /= total_prob; }
            double var_x = 0, var_y = 0;
            for (int i = 0; i < (int)sourceProbability.size(); i++) {
                if (occupancy[i] == Occupancy::Free && sourceProbability[i] > 0) {
                    Vector2 coords = gridMetadata.indexToCoordinates(i);
                    var_x += sourceProbability[i] * (coords.x - mean_x) * (coords.x - mean_x);
                    var_y += sourceProbability[i] * (coords.y - mean_y) * (coords.y - mean_y);
                }
            }
            if (total_prob > 0) { var_x /= total_prob; var_y /= total_prob; }
            double posterior_variance = var_x + var_y;  // trace of 2D covariance

            // Diagnostic stopping check
            double stop_thr = getParam<double>("convergence_thr", 1.5);
            bool would_declare = (posterior_variance < stop_thr) && (seCycleCount >= getParam<int>("minExplorationIterations", 3));

            if (mapIdx >= 0) {
                Vector2 mapCoords = gridMetadata.indexToCoordinates(mapIdx);
                seTraceFile << runUUID << "," << seCycleCount << "," << simTime << ",PMFS,"
                    << "true,POSTERIOR_MAP,"
                    << mapCoords.x << "," << mapCoords.y << "," << 0.0 << ","
                    << entropy << "," << posterior_variance << "," << 0.0 << ","
                    << candidateCount << ",0.0,"
                    << (would_declare ? "true" : "false") << ","
                    << (would_declare ? "variance_below_threshold" : "none") << ","
                    << stop_thr << "," << (would_declare ? "true" : "false") << ","
                    << "false," << (would_declare ? "true" : "false") << "\n";
            } else {
                seTraceFile << runUUID << "," << seCycleCount << "," << simTime << ",PMFS,"
                    << "false,POSTERIOR_MAP,"
                    << "NA,NA,NA,"
                    << "NA,NA,NA,"
                    << "NA,NA,false,none,"
                    << "NA,NA,false,false\n";
            }
            seTraceFile.flush();
        }

        // Visualization
        PMFSViz::ShowHitProb(Grid2D<HitProbability>(hitProbability, occupancy, gridMetadata), settings.visualization, pubs);
        PMFSViz::ShowSourceProb(Grid2D<double>(sourceProbability, occupancy, gridMetadata), settings.visualization, pubs);
        PMFSViz::PlotWindVectors(Grid2D<Vector2>(estimatedWindVectors, occupancy, gridMetadata), settings.visualization, pubs);
    }

    float PMFS::gasCallback(olfaction_msgs::msg::GasSensor::SharedPtr msg)
    {
        float ppm = Algorithm::gasCallback(msg);
        if (!jointSourceExchangeDir.empty())
        {
            if (msg->header.stamp.sec < 0 || msg->header.stamp.nanosec >= 1000000000U)
                throw std::runtime_error("JOINT_INVALID_GAS_STAMP");
            const uint64_t stamp = static_cast<uint64_t>(msg->header.stamp.sec) * 1000000000ULL + msg->header.stamp.nanosec;
            if (stamp < jointLatestStampNs)
                throw std::runtime_error("JOINT_NONMONOTONE_GAS_STAMP");
            jointLatestStampNs = stamp;
        }
        if (ctpiPlannerEnabled)
            ctpiLatestMeasuredPpm = ppm;
        if (cpirEnabled)
            recordCPIRRawSample(ppm,
                msg->header.stamp.sec + static_cast<double>(msg->header.stamp.nanosec) * 1e-9);
        IF_GUI(ui.addConcentrationReading(ppm));
        return ppm;
    }

} // namespace GSL
