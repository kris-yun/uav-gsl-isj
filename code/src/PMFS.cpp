#include "gsl_server/algorithms/Common/States/ManualNavigation.hpp"
#include <angles/angles.h>
#include <gsl_server/algorithms/Common/Utils/Math.hpp>
#include <gsl_server/algorithms/Common/Utils/Pointers.hpp>
#include <gsl_server/algorithms/PMFS/PMFS.hpp>
#include <cmath>
#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>
#include <gsl_server/algorithms/PMFS/PMFSViz.hpp>
#include <gsl_server/algorithms/PMFS/MovingStatePMFS.hpp>

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

        // PWC: Initialize Plume Wind Correction (moved from processGasAndWindMeasurements)
        {
            uav_gsl_pwc::Config pcfg;
            pcfg.enabled = settings.pwc.enabled;
            pcfg.beta = settings.pwc.beta;
            pcfg.max_correction = settings.pwc.max_correction;
            pcfg.min_wind = settings.pwc.min_wind;
            pcfg.use_adaptive = settings.pwc.use_adaptive;
            pcfg.plume_scale_factor = settings.pwc.plume_scale_factor;
            pcfg.log_file = settings.pwc.log_file;
            pwcCorrector_ = std::make_unique<uav_gsl_pwc::PwcCorrector>(pcfg);
            GSL_INFO("[PWC] Init in Initialize() enabled={} beta={}", pcfg.enabled, pcfg.beta);
        }
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
        settings.movement.frontierWeight = getParam<double>("frontierWeight", 0.0);
        settings.movement.edeWeight = getParam<double>("edeWeight", 0.0);
        // ADC: Adaptive Dwell Control (medical CT adaptive exposure)
        settings.movement.adc_enabled = getParam<bool>("adc_enabled", false);
        settings.movement.adc_low_threshold = getParam<double>("adc_low_threshold", 0.3);
        settings.movement.adc_mid_threshold = getParam<double>("adc_mid_threshold", 0.6);
        settings.movement.adc_low_speed_factor = getParam<double>("adc_low_speed_factor", 0.5);
        settings.movement.adc_mid_speed_factor = getParam<double>("adc_mid_speed_factor", 0.75);
        // SET: Sequential Evidence Testing (clinical trials SPRT)
        settings.movement.set_enabled = getParam<bool>("set_enabled", false);
        settings.movement.set_min_evidence_count = getParam<int>("set_min_evidence_count", 10);
        settings.movement.set_confidence_threshold = getParam<double>("set_confidence_threshold", 0.4);
        settings.movement.set_consecutive_hits_required = getParam<int>("set_consecutive_hits_required", 3);
        // FRG: Fault-Reactive Guard (spacecraft fault-tolerant control)
        settings.movement.frg_enabled = getParam<bool>("frg_enabled", false);
        settings.movement.frg_plume_loss_threshold = getParam<int>("frg_plume_loss_threshold", 5);
        settings.movement.frg_recovery_radius = getParam<double>("frg_recovery_radius", 1.5);
        settings.movement.frg_max_recovery_steps = getParam<int>("frg_max_recovery_steps", 10);
        settings.movement.frg_crosswind_step = getParam<double>("frg_crosswind_step", 0.8);

        // PWC: Plume Wind Correction (atmospheric pollution source inversion)
        settings.pwc.enabled = getParam<bool>("pwc_enabled", false);
        settings.pwc.beta = getParam<double>("pwc_beta", 0.5);
        settings.pwc.max_correction = getParam<double>("pwc_max_correction", 5.0);
        settings.pwc.min_wind = getParam<double>("pwc_min_wind", 0.005);
        settings.pwc.use_adaptive = getParam<bool>("pwc_use_adaptive", true);
        settings.pwc.plume_scale_factor = getParam<double>("pwc_plume_scale_factor", 1.0);
        settings.pwc.log_file = getParam<std::string>("pwc_log_file", "/tmp/pwc_log.csv");
        // TDC: Temporal Deconvolution Correction (medical CT Richardson-Lucy)
        settings.tdc.enabled = getParam<bool>("tdc_enabled", false);
        settings.tdc.iterations = getParam<int>("tdc_iterations", 5);
        settings.tdc.tau = getParam<double>("tdc_tau", 15.0);
        settings.tdc.damping = getParam<double>("tdc_damping", 0.8);
        settings.tdc.sharpen_strength = getParam<double>("tdc_sharpen_strength", 0.5);
        // MAC: Multi-Altitude Constraint (meteorological sounding profile)
        settings.mac.enabled = getParam<bool>("mac_enabled", false);
        settings.simulation.sdr_enabled = getParam<bool>("sdr_enabled", false);
        settings.mac.flight_height = getParam<double>("mac_flight_height", 1.0);
        settings.mac.source_height = getParam<double>("mac_source_height", 0.0);
        settings.mac.stability_class = getParam<int>("mac_stability_class", 3);
        settings.mac.max_distance_weight = getParam<double>("mac_max_distance_weight", 6.0);
        GSL_INFO("[PARAM] mdw={:.2f}", settings.mac.max_distance_weight);
        settings.mac.distance_sigma = getParam<double>("mac_distance_sigma", 2.0);

        settings.visualization.markers_height = getParam<double>("markers_height", 0);
        IF_GUI(settings.visualization.headless = getParam<bool>("headless", false));
    }

    void PMFS::onGetMap(OccupancyGrid::SharedPtr msg)
    {
        Algorithm::onGetMap(msg);

        int scale = getParam<int>("scale", 65); // scale for dynamic map reduction
        PMFSLib::InitMetadata(gridMetadata, map, scale);

        hitProbability.resize(gridMetadata.dimensions.x * gridMetadata.dimensions.y);
        sourceProbability.resize(gridMetadata.dimensions.x * gridMetadata.dimensions.y);
        occupancy.resize(gridMetadata.dimensions.x * gridMetadata.dimensions.y);

        visibilityMap.emplace(gridMetadata.dimensions.x, gridMetadata.dimensions.y,
                              std::max(settings.movement.openMoveSetExpasion, settings.hitProbability.localEstimationWindowSize));

        GridUtils::reduceOccupancyMap(map.data, map.info.width, occupancy, gridMetadata);
        PMFSLib::InitializeMap(
            Grid2D<HitProbability>(
                hitProbability,
                occupancy,
                gridMetadata),
            simulations,
            *visibilityMap,
            currentCoordinates());

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
        last_concentration = concentration;
        last_windSpeed = windSpeed;
        last_windDirection = windDirection;

        // WRANF mid-navigation update: accumulate gas hits during flight
        if (movingState) {
            auto* pmfs_moving = dynamic_cast<MovingStatePMFS*>(movingState.get());
            if (pmfs_moving) {
                pmfs_moving->updateWranfMidNavigation();
            }
        }


        // TDC: Temporal Deconvolution Correction (medical CT Richardson-Lucy deconvolution)
        // MOX sensors have ~15s response delay; correct measured concentration for sharper signal
        if (settings.tdc.enabled)
        {
            double dt = 2.0; // approx sensor callback interval
            double dCdt = (concentration - tdc_prev_concentration) / std::max(dt, 0.1);
            // First-order inverse filter: C_true ~ C_meas + tau * dC/dt
            double corrected = concentration + settings.tdc.tau * dCdt * settings.tdc.damping;
            corrected = std::max(0.0, corrected);
            // Blend with original to avoid overshoot
            concentration = (1.0 - settings.tdc.sharpen_strength) * concentration 
                          + settings.tdc.sharpen_strength * corrected;
            GSL_INFO("[TDC] raw={:.4f} corrected={:.4f} dC/dt={:.6f}", 
                     concentration, corrected, dCdt);
            tdc_prev_concentration = concentration;
        }
        // ============================================================
        // BWE: Bayesian Wind Estimator
        // From Bayesian inference / meteorological data assimilation.
        // Smooths wind direction using EMA with gas-detection weighting.
        // Fixes GMRF non-convergence by providing stable wind estimates.
        // ============================================================
        {
            static double bwe_ema_sin = 0.0;
            static double bwe_ema_cos = 1.0;
            static double bwe_ema_speed = 0.0;
            static bool bwe_initialized = false;
            static const double bwe_alpha = 0.15;  // EMA smoothing factor
            static const double bwe_alpha_fast = 0.4; // faster adaptation when gas detected

            double alpha = bwe_alpha;
            // When gas detected, trust current reading more (faster adaptation)
            if (concentration > thresholdGas) alpha = bwe_alpha_fast;

            if (!bwe_initialized) {
                bwe_ema_sin = std::sin(windDirection);
                bwe_ema_cos = std::cos(windDirection);
                bwe_ema_speed = windSpeed;
                bwe_initialized = true;
            } else {
                bwe_ema_sin = (1.0 - alpha) * bwe_ema_sin + alpha * std::sin(windDirection);
                bwe_ema_cos = (1.0 - alpha) * bwe_ema_cos + alpha * std::cos(windDirection);
                bwe_ema_speed = (1.0 - alpha) * bwe_ema_speed + alpha * windSpeed;
            }

            double bwe_direction = std::atan2(bwe_ema_sin, bwe_ema_cos);
            double bwe_speed = std::max(bwe_ema_speed, 0.01);

            // Replace raw wind with BWE-filtered wind for hit probability estimation
            windDirection = bwe_direction;
            windSpeed = bwe_speed;

            static int bwe_log_count = 0;
            if (bwe_log_count++ % 10 == 0) {
                GSL_INFO("[BWE] wind_dir={:.2f}->raw={:.2f} speed={:.2f}->raw={:.2f} alpha={:.2f} conc={:.3f}",
                         bwe_direction, last_windDirection, bwe_speed, last_windSpeed, alpha, concentration);
            }
        }

        static int number_of_updates = 0;
        GSL_INFO_COLOR(fmt::terminal_color::cyan, "[DEBUG-H03] ENTER processGasAndWindMeasurements updates={} conc={}", number_of_updates, concentration);

        // Update the gas presence map
        //  ------------------------------
        Vector2Int robotGridPos = gridMetadata.coordinatesToIndices(currentRobotPosition);
        GSL_INFO_COLOR(fmt::terminal_color::cyan, "[DEBUG-H03] robotPos=({}, {}) gridPos=({}, {}) gridDim=({}, {})",
                       currentRobotPosition.x, currentRobotPosition.y,
                       robotGridPos.x, robotGridPos.y,
                       gridMetadata.dimensions.x, gridMetadata.dimensions.y);

        // Bounds check: skip update if robot is outside grid
        if (robotGridPos.x < 0 || robotGridPos.y < 0 ||
            robotGridPos.x >= gridMetadata.dimensions.x || robotGridPos.y >= gridMetadata.dimensions.y)
        {
            GSL_WARN("Robot at gridPos=({}, {}) is OUT OF BOUNDS (grid {}x{}). Skipping measurement update.",
                     robotGridPos.x, robotGridPos.y, gridMetadata.dimensions.x, gridMetadata.dimensions.y);
        }
        else
        {

        Grid2D<HitProbability> grid(hitProbability, occupancy, gridMetadata);
        GSL_INFO_COLOR(fmt::terminal_color::cyan, "[DEBUG-H03] Grid created, calling EstimateHitProbabilities");
        if (concentration > thresholdGas)
        {
            // Gas & wind
            PMFSLib::EstimateHitProbabilities(grid, *visibilityMap, settings.hitProbability, true, windDirection, windSpeed,
                                              robotGridPos);
            GSL_INFO_COLOR(fmt::terminal_color::yellow, "GAS HIT");
        }
        else
        {
            // Nothing
            GSL_INFO_COLOR(fmt::terminal_color::cyan, "[DEBUG-H03] Before EstimateHitProbabilities (NOTHING)");
            PMFSLib::EstimateHitProbabilities(grid, *visibilityMap, settings.hitProbability, false, windDirection, windSpeed,
                                              robotGridPos);
            GSL_INFO_COLOR(fmt::terminal_color::cyan, "[DEBUG-H03] After EstimateHitProbabilities");
            GSL_INFO_COLOR(fmt::terminal_color::yellow, "NOTHING ");
        }

        } // end bounds check

        GSL_INFO_COLOR(fmt::terminal_color::cyan, "[DEBUG-H03] Before EstimateWind");
        // Update the wind estimations
        //  ------------------------------
        // PGPT: Track peak gas position
        if (concentration > peakGasConcentration)
        {
            peakGasConcentration = concentration;
            peakGasPosition = currentRobotPosition;
            hasPeakGas = true;
            GSL_INFO("PGPT: New peak gas {:.4f} at ({:.2f}, {:.2f})", concentration, peakGasPosition.x, peakGasPosition.y);
        }
        
        // HCE: Accumulate weighted hit positions for centroid estimation
        // Inspired by sensor network localization (Niewiadomska-Szynkiewicz, IEEE TWC 2014)
        // Gas hits are "sensor readings" whose centroid, corrected for wind bias,
        // approximates the source location
        if (concentration > 0.001)
        {
            hce_weighted_x += concentration * currentRobotPosition.x;
            hce_weighted_y += concentration * currentRobotPosition.y;
            hce_weight_mass += concentration;
            hce_wind_sin_accum += std::sin(windDirection);
            hce_wind_cos_accum += std::cos(windDirection);
            hce_wind_speed_accum += windSpeed;
            hce_hit_count++;

        // MAC: Inline source estimation during search
        // Boost probability at MAC-estimated source to guide goal selection
        if (settings.mac.enabled && hce_hit_count >= 5 && hce_hit_count % 3 == 0)
        {
            double avg_wind = hce_wind_speed_accum / std::max(1, hce_hit_count);
            avg_wind = std::max(avg_wind, 0.001);
            double avg_wdir = std::atan2(hce_wind_sin_accum / std::max(1, hce_hit_count),
                                            hce_wind_cos_accum / std::max(1, hce_hit_count));
            static const double Cz_t[] = {0.0, 0.3974, 0.2751, 0.2093, 0.1542, 0.1164, 0.0825};
            static const double Dz_t[] = {0.0, 0.8697, 0.8949, 0.9087, 0.9193, 0.9257, 0.9290};
            int sc = std::max(1, std::min(6, settings.mac.stability_class));
            double h_eff = std::max(settings.mac.flight_height - settings.mac.source_height, 0.1);
            double centroid_x = hce_weighted_x / hce_weight_mass;
            double centroid_y = hce_weighted_y / hce_weight_mass;
            double spread = 0.0;
            if (hasPeakGas)
                spread = std::sqrt(std::pow(centroid_x - peakGasPosition.x, 2) +
                                   std::pow(centroid_y - peakGasPosition.y, 2));
            double sigma_z = std::max(0.1, std::min(spread, 3.0));
            double C_ratio = Cz_t[sc] / std::pow(h_eff, Dz_t[sc]);
            double d_est = std::pow(sigma_z / C_ratio, 1.0 / Dz_t[sc]);
            d_est = std::max(0.5, std::min(d_est, 6.0));  // hardcoded: launch param not passing
            if (d_est > 0.5)
            {
                double wx = avg_wind * std::cos(avg_wdir);
                double wy = avg_wind * std::sin(avg_wdir);
                double ws = std::sqrt(wx*wx + wy*wy);
                double dx = (ws > 0.01) ? wx / ws : 0;
                double dy = (ws > 0.01) ? wy / ws : 0;
                if (std::abs(dx) > 0.001 || std::abs(dy) > 0.001)
                {
                    double mx = centroid_x + dx * d_est;
                    double my = centroid_y + dy * d_est;
                    auto idx = gridMetadata.coordinatesToIndices(mx, my);
                    int ci = std::max(0, std::min((int)gridMetadata.dimensions.x - 1, idx.x));
                    int ri = std::max(0, std::min((int)gridMetadata.dimensions.y - 1, idx.y));
                    double bw = 0.01 * std::min((double)hce_hit_count / 10.0, 1.0);
                    for (int di = -2; di <= 2; di++)
                        for (int dj = -2; dj <= 2; dj++) {
                            int ni = ci + di, nj = ri + dj;
                            if (ni >= 0 && ni < (int)gridMetadata.dimensions.x &&
                                nj >= 0 && nj < (int)gridMetadata.dimensions.y) {
                                int ni2 = nj * gridMetadata.dimensions.x + ni;
                                if (occupancy[ni2] == Occupancy::Free)
                                    sourceProbability[ni2] += bw;
                            }
                        }
                    double total = 0;
                    for (size_t i = 0; i < sourceProbability.size(); i++)
                        if (occupancy[i] == Occupancy::Free) total += sourceProbability[i];
                    if (total > 0)
                        for (size_t i = 0; i < sourceProbability.size(); i++)
                            if (occupancy[i] == Occupancy::Free) sourceProbability[i] /= total;
                    GSL_INFO("[MAC-inline] hits={} d={:.2f} boost=({:.2f},{:.2f}) w={:.4f}",
                             hce_hit_count, d_est, mx, my, bw);
                }
            }
        }
        }

        // ADC: Track gas hit rate for adaptive dwell control
        adc_total_samples++;
        if (concentration > thresholdGas)
            adc_total_detections++;

        // SET: Accumulate sequential evidence for tracking decision
        if (settings.movement.set_enabled)
        {
            set_total_count++;
            if (concentration > thresholdGas)
            {
                set_hit_count++;
                set_consecutive_hits++;
                if (set_consecutive_hits >= settings.movement.set_consecutive_hits_required &&
                    set_total_count >= settings.movement.set_min_evidence_count)
                {
                    double hit_ratio = (double)set_hit_count / set_total_count;
                    if (hit_ratio >= settings.movement.set_confidence_threshold)
                        set_tracking_approved = true;
                }
            }
            else
            {
                set_consecutive_hits = 0;
            }
        }

        // FRG: Track plume loss for fault-reactive guard
        if (settings.movement.frg_enabled)
        {
            if (concentration > thresholdGas)
            {
                frg_no_hit_streak = 0;
                frg_last_hit_pos = Vector2{currentRobotPosition.x, currentRobotPosition.y};
                frg_has_last_hit = true;
            }
            else
            {
                frg_no_hit_streak++;
            }
        }

        PMFSLib::EstimateWind(settings.simulation.useWindGroundTruth,
                              Grid2D<Vector2>(estimatedWindVectors, occupancy, gridMetadata),
                              node,
                              pubs.gmrfWind
                                  IF_GADEN(, pubs.groundTruthWind));

        // If we have already taken enough measurements in this position, process them and get ready to move to the next location
        // ------------------------------
        number_of_updates++;
        if (number_of_updates >= settings.hitProbability.maxUpdatesPerStop)
        {
            number_of_updates = 0;

            // Simulations are slow, so we only run them every few positions, when the map has had time to meaningfully change
            //----------------------------------------
            bool timeToSimulate = settings.simulation.stepsBetweenSourceUpdates >= 0 &&
                                  iterationsCounter >= settings.movement.initialExplorationMoves &&
                                  iterationsCounter % settings.simulation.stepsBetweenSourceUpdates == 0;
            if (timeToSimulate)
            {
                // simulations.compareRefineFractions();
                simulations.updateSourceProbability(settings.simulation.refineFraction);
            }

            // Movement
            movingState->chooseGoalAndMove();

            iterationsCounter++;
        }
        else
            stateMachine.forceResetState(stopAndMeasureState.get());

        // Visualization
        PMFSViz::ShowHitProb(Grid2D<HitProbability>(hitProbability, occupancy, gridMetadata), settings.visualization, pubs);
        PMFSViz::ShowSourceProb(Grid2D<double>(sourceProbability, occupancy, gridMetadata), settings.visualization, pubs);
        PMFSViz::PlotWindVectors(Grid2D<Vector2>(estimatedWindVectors, occupancy, gridMetadata), settings.visualization, pubs);
    }

    float PMFS::gasCallback(olfaction_msgs::msg::GasSensor::SharedPtr msg)
    {
        float ppm = Algorithm::gasCallback(msg);
        IF_GUI(ui.addConcentrationReading(ppm));
        return ppm;
    }

} // namespace GSL