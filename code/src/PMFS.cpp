#include "gsl_server/algorithms/Common/States/ManualNavigation.hpp"
#include <angles/angles.h>
#include <gsl_server/algorithms/Common/Utils/Math.hpp>
#include <gsl_server/algorithms/Common/Utils/Pointers.hpp>
#include <gsl_server/algorithms/PMFS/PMFS.hpp>
#include <gsl_server/algorithms/PMFS/modules/BaprHspb.hpp>
#include <cmath>
#include <algorithm>
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
        number_of_updates = 0;

        // Reset all method state explicitly. Avoid static state and cross-run contamination.
        peakGasConcentration = 0.0;
        peakGasPosition = {0, 0};
        hasPeakGas = false;
        hce_weighted_x = 0.0;
        hce_weighted_y = 0.0;
        hce_weight_mass = 0.0;
        hce_weighted_x2 = 0.0;
        hce_weighted_y2 = 0.0;
        hce_wind_sin_accum = 0.0;
        hce_wind_cos_accum = 0.0;
        hce_wind_speed_accum = 0.0;
        hce_hit_count = 0;
        hceRefinementDone = false;
        hceRefinementActive = false;
        hceRefinedTarget = {0, 0, 0};
        tdc_prev_concentration = 0.0;
        mac_estimated_distance = -1.0;
        bwe_initialized = false;
        bwe_ema_sin = 0.0;
        bwe_ema_cos = 1.0;
        bwe_ema_speed = 0.0;

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
            pcfg.wind_vector_is_flow_to = settings.pwc.wind_vector_is_flow_to;
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

        // Method-control flags. All default OFF: clean baseline unless launch explicitly enables a module.
        settings.method.method_id = getParam<std::string>("method_id", "baseline");
        settings.method.bwe_enabled = getParam<bool>("bwe_enabled", false);
        settings.method.pgpt_enabled = getParam<bool>("pgpt_enabled", false);
        settings.method.hce_enabled = getParam<bool>("hce_enabled", false);
        settings.method.hce_min_concentration = getParam<double>("hce_min_concentration", 0.001);
        settings.method.bwe_alpha = getParam<double>("bwe_alpha", 0.15);
        settings.method.bwe_alpha_fast = getParam<double>("bwe_alpha_fast", 0.40);
        settings.method.bwe_min_speed = getParam<double>("bwe_min_speed", 0.01);
        settings.method.gt_debug_logging = getParam<bool>("gt_debug_logging", false);
        settings.method.verbose_debug = getParam<bool>("verbose_debug", false);

        // Legacy optional modules: keep disabled unless explicitly ablated.
        settings.movement.adc_enabled = getParam<bool>("adc_enabled", false);
        settings.movement.adc_low_threshold = getParam<double>("adc_low_threshold", 0.3);
        settings.movement.adc_mid_threshold = getParam<double>("adc_mid_threshold", 0.6);
        settings.movement.adc_low_speed_factor = getParam<double>("adc_low_speed_factor", 0.5);
        settings.movement.adc_mid_speed_factor = getParam<double>("adc_mid_speed_factor", 0.75);
        settings.movement.set_enabled = getParam<bool>("set_enabled", false);
        settings.movement.set_min_evidence_count = getParam<int>("set_min_evidence_count", 10);
        settings.movement.set_confidence_threshold = getParam<double>("set_confidence_threshold", 0.4);
        settings.movement.set_consecutive_hits_required = getParam<int>("set_consecutive_hits_required", 3);
        settings.movement.frg_enabled = getParam<bool>("frg_enabled", false);
        settings.movement.frg_plume_loss_threshold = getParam<int>("frg_plume_loss_threshold", 5);
        settings.movement.frg_recovery_radius = getParam<double>("frg_recovery_radius", 1.5);
        settings.movement.frg_max_recovery_steps = getParam<int>("frg_max_recovery_steps", 10);
        settings.movement.frg_crosswind_step = getParam<double>("frg_crosswind_step", 0.8);

        // PWC: post-processing source-estimate correction.
        settings.pwc.enabled = getParam<bool>("pwc_enabled", false);
        settings.pwc.beta = getParam<double>("pwc_beta", 0.5);
        settings.pwc.max_correction = getParam<double>("pwc_max_correction", 5.0);
        settings.pwc.min_wind = getParam<double>("pwc_min_wind", 0.01);
        settings.pwc.use_adaptive = getParam<bool>("pwc_use_adaptive", true);
        settings.pwc.plume_scale_factor = getParam<double>("pwc_plume_scale_factor", 1.0);
        settings.pwc.wind_vector_is_flow_to = getParam<bool>("wind_vector_is_flow_to", true);
        settings.pwc.log_file = getParam<std::string>("pwc_log_file", "");

        // TDC: disabled by default. Requires timestamp-based validation before use in the paper.
        settings.tdc.enabled = getParam<bool>("tdc_enabled", false);
        settings.tdc.iterations = getParam<int>("tdc_iterations", 5);
        settings.tdc.tau = getParam<double>("tdc_tau", 15.0);
        settings.tdc.damping = getParam<double>("tdc_damping", 0.8);
        settings.tdc.sharpen_strength = getParam<double>("tdc_sharpen_strength", 0.5);

        // PSDE. Keep legacy mac_enabled compatibility, but expose online/final effects separately.
        const bool legacy_mac_enabled = getParam<bool>("mac_enabled", false);
        settings.mac.enabled = legacy_mac_enabled;
        settings.method.psde_online_enabled = getParam<bool>("psde_online_enabled", legacy_mac_enabled);
        settings.method.psde_final_enabled = getParam<bool>("psde_final_enabled", legacy_mac_enabled);
        settings.simulation.sdr_enabled = getParam<bool>("sdr_enabled", false);
        settings.mac.flight_height = getParam<double>("mac_flight_height", 1.0);
        settings.mac.source_height = getParam<double>("mac_source_height", 0.0);
        settings.mac.stability_class = getParam<int>("mac_stability_class", 3);
        settings.mac.min_distance = getParam<double>("mac_min_distance", 0.5);
        settings.mac.max_distance_weight = getParam<double>("mac_max_distance_weight", 6.0);
        settings.mac.distance_sigma = getParam<double>("mac_distance_sigma", 2.0);
        settings.mac.sigma_z_max = getParam<double>("mac_sigma_z_max", 3.0);
        settings.mac.min_hits = getParam<int>("mac_min_hits", 5);
        settings.mac.online_update_stride = getParam<int>("mac_online_update_stride", 3);
        settings.mac.online_boost_weight = getParam<double>("mac_online_boost_weight", 0.01);
        settings.mac.wind_vector_is_flow_to = getParam<bool>("wind_vector_is_flow_to", true);

        settings.simulation.sdr_rl_iterations = getParam<int>("sdr_rl_iterations", 10);
        settings.simulation.sdr_psf_size = getParam<int>("sdr_psf_size", 7);
        settings.simulation.sdr_blob_radius = getParam<double>("sdr_blob_radius", 4.5);
        settings.simulation.sdr_min_hits = getParam<int>("sdr_min_hits", 5);
        settings.simulation.sdr_min_peak_mass_ratio = getParam<double>("sdr_min_peak_mass_ratio", 0.0);

        // BAPR params
        settings.simulation.bapr_enabled = getParam<bool>("bapr_enabled", false);
        settings.simulation.bapr_wall_penalty = getParam<double>("bapr_wall_penalty", 2.0);
        settings.simulation.bapr_wall_distance = getParam<double>("bapr_wall_distance", 2.0);
        settings.simulation.bapr_sigmoid_steepness = getParam<double>("bapr_sigmoid_steepness", 3.0);
        settings.simulation.bapr_dtf_radius = getParam<int>("bapr_dtf_radius", 10);

        // HSPB params
        settings.simulation.hspb_enabled = getParam<bool>("hspb_enabled", false);
        settings.simulation.hspb_min_hits = getParam<int>("hspb_min_hits", 3);
        settings.simulation.hspb_distance_scale = getParam<double>("hspb_distance_scale", 1.0);
        settings.simulation.hspb_angular_spread = getParam<double>("hspb_angular_spread", 0.35);
        settings.simulation.hspb_kernel_radius = getParam<int>("hspb_kernel_radius", 3);

        GSL_INFO("[METHOD] id={} BWE={} PGPT={} HCE={} PWC={} PSDE_online={} PSDE_final={} SDR={} wind_flow_to={}",
                 settings.method.method_id, settings.method.bwe_enabled, settings.method.pgpt_enabled,
                 settings.method.hce_enabled, settings.pwc.enabled, settings.method.psde_online_enabled,
                 settings.method.psde_final_enabled, settings.simulation.sdr_enabled,
                 settings.mac.wind_vector_is_flow_to);

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
        // Keep the online baseline clean: BWE/PGPT/HCE/PSDE/SDR are inactive unless their
        // corresponding flags are explicitly enabled by launch.
        const double raw_concentration = concentration;
        const double raw_wind_speed = windSpeed;
        const double raw_wind_direction = windDirection;

        if (movingState) {
            auto* pmfs_moving = dynamic_cast<MovingStatePMFS*>(movingState.get());
            if (pmfs_moving) {
                pmfs_moving->updateWranfMidNavigation();
            }
        }

        // TDC: first-order inverse filter. Disabled by default; use only in dedicated delay experiments.
        if (settings.tdc.enabled)
        {
            const double dt = std::max(settings.simulation.deltaTime, 0.1);
            const double dCdt = (concentration - tdc_prev_concentration) / dt;
            const double corrected = std::max(0.0, concentration + settings.tdc.tau * dCdt * settings.tdc.damping);
            concentration = (1.0 - settings.tdc.sharpen_strength) * concentration
                          + settings.tdc.sharpen_strength * corrected;
            tdc_prev_concentration = concentration;
            if (settings.method.verbose_debug)
                GSL_INFO("[TDC] raw={:.4f} corrected={:.4f} dCdt={:.6f}", raw_concentration, concentration, dCdt);
        }

        // BWE: optional EMA wind smoother. It is not Bayesian; it is ablated separately.
        if (settings.method.bwe_enabled)
        {
            double alpha = settings.method.bwe_alpha;
            if (concentration > thresholdGas)
                alpha = settings.method.bwe_alpha_fast;

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

            windDirection = std::atan2(bwe_ema_sin, bwe_ema_cos);
            windSpeed = std::max(bwe_ema_speed, settings.method.bwe_min_speed);
        }

        last_concentration = concentration;
        last_windSpeed = windSpeed;
        last_windDirection = windDirection;

        Vector2Int robotGridPos = gridMetadata.coordinatesToIndices(currentRobotPosition);
        if (robotGridPos.x < 0 || robotGridPos.y < 0 ||
            robotGridPos.x >= gridMetadata.dimensions.x || robotGridPos.y >= gridMetadata.dimensions.y)
        {
            GSL_WARN("Robot at gridPos=({}, {}) is outside grid ({}x{}). Skipping measurement update.",
                     robotGridPos.x, robotGridPos.y, gridMetadata.dimensions.x, gridMetadata.dimensions.y);
        }
        else
        {
            Grid2D<HitProbability> grid(hitProbability, occupancy, gridMetadata);
            const bool gas_hit = concentration > thresholdGas;
            PMFSLib::EstimateHitProbabilities(grid, *visibilityMap, settings.hitProbability, gas_hit,
                                              windDirection, windSpeed, robotGridPos);
            if (settings.method.verbose_debug)
                GSL_INFO("[MEAS] rawC={:.4f} C={:.4f} rawWind=({:.3f},{:.3f}) wind=({:.3f},{:.3f}) hit={}",
                         raw_concentration, concentration, raw_wind_speed, raw_wind_direction,
                         windSpeed, windDirection, gas_hit);
        }

        const bool need_peak = settings.method.pgpt_enabled || settings.method.hce_enabled ||
                               settings.method.psde_online_enabled || settings.method.psde_final_enabled ||
                               settings.simulation.sdr_enabled || settings.pwc.enabled ||
                               settings.simulation.hspb_enabled;
        const bool need_hit_stats = settings.method.hce_enabled || settings.method.psde_online_enabled ||
                                    settings.method.psde_final_enabled || settings.simulation.sdr_enabled ||
                                    settings.simulation.hspb_enabled;

        if (need_peak && concentration > settings.method.hce_min_concentration && concentration > peakGasConcentration)
        {
            peakGasConcentration = concentration;
            peakGasPosition = currentRobotPosition;
            hasPeakGas = true;
            if (settings.method.verbose_debug)
                GSL_INFO("[PGPT] peak gas {:.4f} at ({:.2f},{:.2f})", concentration, peakGasPosition.x, peakGasPosition.y);
        }

        if (need_hit_stats && concentration > settings.method.hce_min_concentration)
        {
            hce_weighted_x += concentration * currentRobotPosition.x;
            hce_weighted_y += concentration * currentRobotPosition.y;
            hce_weight_mass += concentration;
            hce_weighted_x2 += concentration * currentRobotPosition.x * currentRobotPosition.x;
            hce_weighted_y2 += concentration * currentRobotPosition.y * currentRobotPosition.y;
            hce_wind_sin_accum += std::sin(windDirection);
            hce_wind_cos_accum += std::cos(windDirection);
            hce_wind_speed_accum += windSpeed;
            hce_hit_count++;

            // PSDE-online: optional online probability boost. This is separated from the final
            // post-processing replacement so path effects can be tested cleanly.
            if (settings.method.psde_online_enabled && hce_hit_count >= settings.mac.min_hits &&
                settings.mac.online_update_stride > 0 && hce_hit_count % settings.mac.online_update_stride == 0 &&
                hce_weight_mass > 0.0)
            {
                static const double Cz_t[] = {0.0, 0.3974, 0.2751, 0.2093, 0.1542, 0.1164, 0.0825};
                static const double Dz_t[] = {0.0, 0.8697, 0.8949, 0.9087, 0.9193, 0.9257, 0.9290};
                const int sc = std::max(1, std::min(6, settings.mac.stability_class));
                const double h_eff = std::max(settings.mac.flight_height - settings.mac.source_height, 0.1);
                const double centroid_x = hce_weighted_x / hce_weight_mass;
                const double centroid_y = hce_weighted_y / hce_weight_mass;
                double spread = 0.0;
                if (hasPeakGas)
                    spread = std::sqrt(std::pow(centroid_x - peakGasPosition.x, 2) +
                                       std::pow(centroid_y - peakGasPosition.y, 2));
                const double hit_density = std::min(std::sqrt((double)hce_hit_count) / 5.0, 1.0);
                const double sigma_z = std::max(0.1, std::min(spread * hit_density, settings.mac.sigma_z_max));
                const double C_ratio = Cz_t[sc] / std::pow(h_eff, Dz_t[sc]);
                const double d_raw = std::pow(sigma_z / C_ratio, 1.0 / Dz_t[sc]);
                const double d_est = std::max(settings.mac.min_distance, std::min(d_raw, settings.mac.max_distance_weight));

                const double avg_wind = std::max(hce_wind_speed_accum / std::max(1, hce_hit_count), 0.001);
                const double avg_wdir = std::atan2(hce_wind_sin_accum / std::max(1, hce_hit_count),
                                                   hce_wind_cos_accum / std::max(1, hce_hit_count));
                const double wx = avg_wind * std::cos(avg_wdir);
                const double wy = avg_wind * std::sin(avg_wdir);
                const double ws = std::sqrt(wx * wx + wy * wy);

                if (ws > 0.01 && d_est > settings.mac.min_distance)
                {
                    const double upwind_sign = settings.mac.wind_vector_is_flow_to ? -1.0 : 1.0;
                    const double mx = centroid_x + upwind_sign * (wx / ws) * d_est;
                    const double my = centroid_y + upwind_sign * (wy / ws) * d_est;
                    auto idx = gridMetadata.coordinatesToIndices(mx, my);
                    const int ci = std::max(0, std::min((int)gridMetadata.dimensions.x - 1, idx.x));
                    const int ri = std::max(0, std::min((int)gridMetadata.dimensions.y - 1, idx.y));
                    const double bw = settings.mac.online_boost_weight * std::min((double)hce_hit_count / 10.0, 1.0);
                    for (int di = -2; di <= 2; di++)
                        for (int dj = -2; dj <= 2; dj++) {
                            const int ni = ci + di, nj = ri + dj;
                            if (ni >= 0 && ni < (int)gridMetadata.dimensions.x &&
                                nj >= 0 && nj < (int)gridMetadata.dimensions.y) {
                                const int nidx = nj * gridMetadata.dimensions.x + ni;
                                if (occupancy[nidx] == Occupancy::Free)
                                    sourceProbability[nidx] += bw;
                            }
                        }
                    double total = 0.0;
                    for (size_t i = 0; i < sourceProbability.size(); i++)
                        if (occupancy[i] == Occupancy::Free) total += sourceProbability[i];
                    if (total > 0.0)
                        for (size_t i = 0; i < sourceProbability.size(); i++)
                            if (occupancy[i] == Occupancy::Free) sourceProbability[i] /= total;
                    GSL_INFO("[PSDE-online] hits={} spread={:.2f} d={:.2f} boost=({:.2f},{:.2f}) w={:.4f}",
                             hce_hit_count, spread, d_est, mx, my, bw);
                }
            }
        }

        // Optional legacy controllers. They remain disabled in the clean ablation matrix.
        adc_total_samples++;
        if (concentration > thresholdGas)
            adc_total_detections++;

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
                    const double hit_ratio = (double)set_hit_count / set_total_count;
                    if (hit_ratio >= settings.movement.set_confidence_threshold)
                        set_tracking_approved = true;
                }
            }
            else
            {
                set_consecutive_hits = 0;
            }
        }

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

        number_of_updates++;
        if (number_of_updates >= settings.hitProbability.maxUpdatesPerStop)
        {
            number_of_updates = 0;

            const bool timeToSimulate = settings.simulation.stepsBetweenSourceUpdates >= 0 &&
                                        iterationsCounter >= settings.movement.initialExplorationMoves &&
                                        iterationsCounter % settings.simulation.stepsBetweenSourceUpdates == 0;
            if (timeToSimulate)
            {
                simulations.updateSourceProbability(settings.simulation.refineFraction);

                // BAPR: reshape sourceProbability to penalize wall-adjacent peaks
                if (settings.simulation.bapr_enabled) {
                    applyBAPR(sourceProbability, occupancy, gridMetadata,
                              settings.simulation, bapr_distance_field_, bapr_dtf_computed_);
                    GSL_INFO("[BAPR-online] reshaped sourceProbability, iter={}", iterationsCounter);
                }
            }

            movingState->chooseGoalAndMove();
            iterationsCounter++;
        }
        else
            stateMachine.forceResetState(stopAndMeasureState.get());

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