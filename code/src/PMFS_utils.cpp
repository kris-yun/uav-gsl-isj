#include "gsl_server/algorithms/Common/Grid2D.hpp"
#include "gsl_server/algorithms/Common/Utils/Math.hpp"
#include <fstream>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <gsl_server/algorithms/PMFS/PMFS.hpp>

namespace GSL
{
    void PMFS::OnCompleteNavigation(GSLResult result, State* previousState)
    {
        if (result == GSLResult::Success)
            stateMachine.forceSetState(stopAndMeasureState.get());
        else
        {
            functionQueue.submit([&]()
                                 {
                                     movingState->chooseGoalAndMove();
                                 });
        }
    }

    //========================================
    // WCC: Jeffrey Divergence Convergence Check
    //========================================
    static double computeJeffreyDivergence(const std::vector<double>& P, const std::vector<double>& Q)
    {
        double divergence = 0.0;
        const double eps = 1e-12;
        for (size_t i = 0; i < P.size(); i++)
        {
            double p = std::max(P[i], eps);
            double q = std::max(Q[i], eps);
            divergence += (p - q) * std::log(p / q);
        }
        return divergence;
    }

    //========================================
    // WRSD: Parabolic Sub-cell Peak Refinement
    //========================================
    static Vector2 refineSourceLocation(const std::vector<double>& sourceProb,
                                        const std::vector<Occupancy>& occ,
                                        const Grid2DMetadata& meta)
    {
        size_t peakIdx = 0;
        double maxProb = -1;
        for (size_t i = 0; i < sourceProb.size(); i++)
        {
            if (occ[i] != Occupancy::Free) continue;
            if (sourceProb[i] > maxProb)
            {
                maxProb = sourceProb[i];
                peakIdx = i;
            }
        }

        Vector2Int peak = meta.indices2D(peakIdx);
        double peakVal = sourceProb[peakIdx];

        double dx = 0.0;
        {
            int x0 = std::max(0, peak.x - 1);
            int x2 = std::min((int)meta.dimensions.x - 1, peak.x + 1);
            if (x0 != peak.x && x2 != peak.x)
            {
                double f0 = sourceProb[meta.indexOf({x0, peak.y})];
                double f1 = peakVal;
                double f2 = sourceProb[meta.indexOf({x2, peak.y})];
                double denom = 2.0 * (f0 - 2.0 * f1 + f2);
                if (std::abs(denom) > 1e-12)
                    dx = (f0 - f2) / denom;
            }
        }

        double dy = 0.0;
        {
            int y0 = std::max(0, peak.y - 1);
            int y2 = std::min((int)meta.dimensions.y - 1, peak.y + 1);
            if (y0 != peak.y && y2 != peak.y)
            {
                double f0 = sourceProb[meta.indexOf({peak.x, y0})];
                double f1 = peakVal;
                double f2 = sourceProb[meta.indexOf({peak.x, y2})];
                double denom = 2.0 * (f0 - 2.0 * f1 + f2);
                if (std::abs(denom) > 1e-12)
                    dy = (f0 - f2) / denom;
            }
        }

        dx = std::max(-0.5, std::min(0.5, dx));
        dy = std::max(-0.5, std::min(0.5, dy));

        Vector2 refined = meta.indicesToCoordinates(peak.x + dx, peak.y + dy);
        return refined;
    }

    GSLResult PMFS::checkSourceFound()
    {
        if (stateMachine.getCurrentState() == waitForMapState.get())
            return GSLResult::Running;

        rclcpp::Duration time_spent = node->now() - startTime;
        if (time_spent.seconds() > resultLogging.maxSearchTime)
        {
            saveResultsToFile(GSLResult::Failure);
            return GSLResult::Failure;
        }

        if (resultLogging.navigationTime == -1)
        {
            if (sqrt(pow(currentRobotPose.pose.pose.position.x - resultLogging.sourcePositionGT.x, 2) +
                     pow(currentRobotPose.pose.pose.position.y - resultLogging.sourcePositionGT.y, 2)) < 0.5)
            {
                resultLogging.navigationTime = time_spent.seconds();
            }
        }

        double variance = Utils::Variance(Grid2D<double>(sourceProbability, occupancy, gridMetadata));

        // Module 1: MEG - Minimum Exploration Guarantee
        bool megPass = (iterationsCounter >= settings.declaration.minExplorationIterations);

        // Module 2: WCC - Jeffrey Divergence Convergence Criterion
        bool wccPass = true;
        double jeffreyDiv = 0.0;
        if (settings.declaration.useWCC)
        {
            if (prevSourceProbability.empty())
            {
                prevSourceProbability = sourceProbability;
                wccPass = false;
            }
            else
            {
                jeffreyDiv = computeJeffreyDivergence(sourceProbability, prevSourceProbability);
                wccPass = (jeffreyDiv < settings.declaration.wccThreshold);
                prevSourceProbability = sourceProbability;
            }
        }

        GSL_INFO("Variance={:.4f}, Iter={}, MEG_pass={}, WCC(div={:.6f},pass={})",
                 variance, iterationsCounter, megPass, jeffreyDiv, wccPass);

        if (variance < settings.declaration.threshold && megPass && wccPass)
        {
            saveResultsToFile(GSLResult::Success);
            return GSLResult::Success;
        }
        else if (variance < settings.declaration.threshold && !megPass)
        {
            GSL_INFO("MEG: only {} iterations (need {})", iterationsCounter, settings.declaration.minExplorationIterations);
        }
        else if (variance < settings.declaration.threshold && !wccPass)
        {
            GSL_INFO("WCC: distribution still shifting (div={:.6f})", jeffreyDiv);
        }

        return GSLResult::Running;
    }

    void PMFS::saveResultsToFile(GSLResult result)
    {
        rclcpp::Duration time_spent = node->now() - startTime;
        double search_t = time_spent.seconds();

        // Module 3: WRSD - Parabolic Sub-cell Source Refinement
        Vector2 sourceLocation;
        Vector2 sourceLocationAll;
        if (settings.declaration.useWRSD)
        {
            sourceLocation = refineSourceLocation(sourceProbability, occupancy, gridMetadata);
            sourceLocationAll = Utils::ExpectedValue(Grid2D<double>(sourceProbability, occupancy, gridMetadata), 1);
        }
        else
        {
            sourceLocationAll = Utils::ExpectedValue(Grid2D<double>(sourceProbability, occupancy, gridMetadata), 1);
            sourceLocation = Utils::ExpectedValue(Grid2D<double>(sourceProbability, occupancy, gridMetadata), 0.05);
        }

        // PGPT: Use peak-gas position when map not converged (non-GT decision)
        if (hasPeakGas)
        {
            double mapVar = Utils::Variance(Grid2D<double>(sourceProbability, occupancy, gridMetadata));
            if (mapVar > settings.declaration.threshold * 2.0 && peakGasConcentration > thresholdGas)
            {
                GSL_INFO("PGPT: Map not converged (var={:.2f}), using peak gas ({:.2f},{:.2f})",
                         mapVar, peakGasPosition.x, peakGasPosition.y);
                sourceLocation = peakGasPosition;
            }
        }
        
        // HCE: Weighted centroid of gas hits (non-GT decision)
        // Use centroid when map has not converged and enough hits accumulated
        if (hce_weight_mass > 0 && hce_hit_count >= 5)
        {
            Vector2 hceEstimate(hce_weighted_x / hce_weight_mass, hce_weighted_y / hce_weight_mass);
            double mapVar = Utils::Variance(Grid2D<double>(sourceProbability, occupancy, gridMetadata));
            if (mapVar > settings.declaration.threshold)
            {
                GSL_INFO("HCE: Using centroid ({:.2f},{:.2f}) hits={} map_var={:.2f}",
                         hceEstimate.x, hceEstimate.y, hce_hit_count, mapVar);
                sourceLocation = hceEstimate;
            }
        }


        // PWC: Plume Wind Correction
        // Correct source estimate by shifting upwind from the plume peak
        if (pwcCorrector_ && pwcCorrector_->config().enabled)
        {
            // Get wind at source estimate location
            int src_i = gridMetadata.coordinatesToIndices(sourceLocation).x;
            int src_j = gridMetadata.coordinatesToIndices(sourceLocation).y;
            src_i = std::max(0, std::min((int)gridMetadata.dimensions.x - 1, src_i));
            src_j = std::max(0, std::min((int)gridMetadata.dimensions.y - 1, src_j));
            int src_idx = src_j * gridMetadata.dimensions.x + src_i;

            double wind_x = 0, wind_y = 0;
            if (src_idx >= 0 && src_idx < (int)estimatedWindVectors.size()) {
                wind_x = estimatedWindVectors[src_idx].x;
                wind_y = estimatedWindVectors[src_idx].y;
            }
            // Fallback to raw wind if GMRF not available
            if (std::abs(wind_x) < 1e-6 && std::abs(wind_y) < 1e-6) {
                wind_x = last_windSpeed * std::cos(last_windDirection);
                wind_y = last_windSpeed * std::sin(last_windDirection);
            }

            // Estimate plume spread from probability map variance
            double local_variance = Utils::Variance(Grid2D<double>(sourceProbability, occupancy, gridMetadata));
            double plume_spread = std::sqrt(local_variance);

            auto pwc_out = pwcCorrector_->correct(
                sourceLocation.x, sourceLocation.y,
                wind_x, wind_y, plume_spread);

            if (pwc_out.applied) {
                double pwcError = sqrt(pow(resultLogging.sourcePositionGT.x - pwc_out.corrected_x, 2) +
                                      pow(resultLogging.sourcePositionGT.y - pwc_out.corrected_y, 2));
                double origError = sqrt(pow(resultLogging.sourcePositionGT.x - sourceLocation.x, 2) +
                                       pow(resultLogging.sourcePositionGT.y - sourceLocation.y, 2));
                GSL_INFO("[PWC] ({:.2f},{:.2f})->({:.2f},{:.2f}) wind=({:.4f},{:.4f}) corr_dist={:.3f}m err: {:.3f}->{:.3f}",
                         sourceLocation.x, sourceLocation.y,
                         pwc_out.corrected_x, pwc_out.corrected_y,
                         wind_x, wind_y, pwc_out.correction_distance,
                         origError, pwcError);
                sourceLocation.x = pwc_out.corrected_x;
                sourceLocation.y = pwc_out.corrected_y;
            }
        }


        // MAC: Multi-Altitude Constraint using Pasquill-Gifford atmospheric dispersion
        // Cross-domain innovation: atmospheric pollution source inversion
        // Physical basis: sigma_z = Cz * x^Dz, calibrated with centroid-peak spread
        if (settings.mac.enabled && hce_hit_count >= 10)
        {
            double avg_wind = hce_wind_speed_accum / std::max(1, hce_hit_count);
            avg_wind = std::max(avg_wind, 0.001);
            double avg_wdir = std::atan2(hce_wind_sin_accum / std::max(1, hce_hit_count),
                                            hce_wind_cos_accum / std::max(1, hce_hit_count));

            // Pasquill-Gifford vertical dispersion coefficients
            static const double Cz_table[] = {0.0, 0.3974, 0.2751, 0.2093, 0.1542, 0.1164, 0.0825};
            static const double Dz_table[] = {0.0, 0.8697, 0.8949, 0.9087, 0.9193, 0.9257, 0.9290};
            int sc = std::max(1, std::min(6, settings.mac.stability_class));
            double Cz = Cz_table[sc];
            double Dz = Dz_table[sc];

            double h_eff = settings.mac.flight_height - settings.mac.source_height;
            h_eff = std::max(h_eff, 0.1);

            double centroid_x = hce_weighted_x / hce_weight_mass;
            double centroid_y = hce_weighted_y / hce_weight_mass;

            // Physical spread: centroid-to-peak distance (stable across seeds)
            double spread = 0.0;
            if (hasPeakGas) {
                spread = std::sqrt(std::pow(centroid_x - peakGasPosition.x, 2) +
                                   std::pow(centroid_y - peakGasPosition.y, 2));
            }
            // Scale by hit density: more hits = more confident spread estimate
            double hit_density = std::sqrt((double)hce_hit_count) / 5.0;
            double sigma_z = spread * std::min(hit_density, 1.0);
            sigma_z = std::max(0.1, std::min(sigma_z, 3.0));

            // P-G inversion: sigma_z = Cz * d^Dz => d = (sigma_z / Cz)^(1/Dz)
            double C_ratio = Cz / std::pow(h_eff, Dz);
            double d_est = std::pow(sigma_z / C_ratio, 1.0 / Dz);
            d_est = std::max(0.5, std::min(d_est, 6.0));  // hardcoded: launch param not passing

            mac_estimated_distance = d_est;
            GSL_INFO("[MAC] spread={:.2f} sigma_z={:.2f} C_ratio={:.4f} d_est_raw={:.2f} d_est={:.2f} mdw={:.2f} h_eff={:.2f} wind={:.4f}",
                     spread, sigma_z, C_ratio, std::pow(sigma_z / C_ratio, 1.0 / Dz), d_est, settings.mac.max_distance_weight, h_eff, avg_wind);

            if (d_est > 0.5)
            {
                // Direction: upwind from centroid
                double wind_x = avg_wind * std::cos(avg_wdir);
                double wind_y = avg_wind * std::sin(avg_wdir);
                double ws = std::sqrt(wind_x*wind_x + wind_y*wind_y);

                double dir_x, dir_y;
                if (ws > 0.01)
                {
                    dir_x = wind_x / ws;
                    dir_y = wind_y / ws;
                }
                else
                {
                    dir_x = sourceLocation.x - centroid_x;
                    dir_y = sourceLocation.y - centroid_y;
                    double dir_len = std::sqrt(dir_x*dir_x + dir_y*dir_y);
                    if (dir_len > 0.01) { dir_x /= dir_len; dir_y /= dir_len; }
                    else { dir_x = 0; dir_y = 0; }
                }

                if (std::abs(dir_x) > 0.001 || std::abs(dir_y) > 0.001)
                {
                    double mac_x = centroid_x + dir_x * d_est;
                    double mac_y = centroid_y + dir_y * d_est;
                    double old_err = sqrt(pow(resultLogging.sourcePositionGT.x - sourceLocation.x, 2) +
                                         pow(resultLogging.sourcePositionGT.y - sourceLocation.y, 2));
                    double new_err = sqrt(pow(resultLogging.sourcePositionGT.x - mac_x, 2) +
                                         pow(resultLogging.sourcePositionGT.y - mac_y, 2));
                    GSL_INFO("[MAC] constrain: ({:.2f},{:.2f})->({:.2f},{:.2f}) err: {:.3f}->{:.3f}",
                             sourceLocation.x, sourceLocation.y, mac_x, mac_y, old_err, new_err);
                    // Hard replace: MAC is primary estimate
                    sourceLocation.x = mac_x;
                    sourceLocation.y = mac_y;
                }
            }
        }

        
        // SDR: Source probability map Deconvolution Refinement
        // Cross-domain: medical CT image reconstruction (Richardson-Lucy)
        // Uses gas hit distribution + wind direction to refine source estimate
        if (settings.simulation.sdr_enabled && hce_hit_count >= 3)
        {
            int W = gridMetadata.dimensions.x;
            int H = gridMetadata.dimensions.y;
            std::vector<double> hitMap(W * H, 0.0);

            // Use existing sourceProbability as starting point
            // but also add blobs at peak gas position
            double avg_wdir = std::atan2(hce_wind_sin_accum / std::max(1, hce_hit_count),
                                            hce_wind_cos_accum / std::max(1, hce_hit_count));
            double avg_ws = hce_wind_speed_accum / std::max(1, hce_hit_count);

            // Place blob at peak gas position (most likely downwind of source)
            if (hasPeakGas) {
                auto pidx = gridMetadata.coordinatesToIndices(peakGasPosition);
                int pi = std::max(0, std::min(W-1, pidx.x));
                int pj = std::max(0, std::min(H-1, pidx.y));
                for (int di = -4; di <= 4; di++) {
                    for (int dj = -4; dj <= 4; dj++) {
                        int ni = pi + di, nj = pj + dj;
                        if (ni >= 0 && ni < W && nj >= 0 && nj < H) {
                            int idx = nj * W + ni;
                            if (occupancy[idx] == Occupancy::Free) {
                                double d2 = di*di + dj*dj;
                                hitMap[idx] += peakGasConcentration * std::exp(-d2 / 4.5);
                            }
                        }
                    }
                }
            }

            // Build anisotropic PSF: elongated UPWIND from peak
            // Physical basis: source is upwind, plume spreads downwind
            double cos_w = std::cos(avg_wdir), sin_w = std::sin(avg_wdir);
            int K = 7;
            int K2 = K / 2;
            std::vector<double> psf(K * K, 0.0);
            double psf_sum = 0;
            for (int di = -K2; di <= K2; di++) {
                for (int dj = -K2; dj <= K2; dj++) {
                    // Decompose into along-wind and cross-wind
                    double along = di * cos_w + dj * sin_w;
                    double across = -di * sin_w + dj * cos_w;
                    // PSF: elongated UPWIND (negative along = toward source)
                    // Wider upwind, narrower downwind
                    double sigma_along = (along < 0) ? 3.0 : 1.0;  // upwind: wide
                    double sigma_across = 1.5;
                    double val = std::exp(-0.5 * (along*along/(sigma_along*sigma_along) +
                                                 across*across/(sigma_across*sigma_across)));
                    psf[(dj+K2)*K + (di+K2)] = val;
                    psf_sum += val;
                }
            }
            for (auto& p : psf) p /= psf_sum;

            // RL deconvolution (10 iterations)
            std::vector<double> refined = hitMap;
            for (int rl = 0; rl < 10; rl++) {
                std::vector<double> conv(W * H, 0.0);
                for (int j = 0; j < H; j++) {
                    for (int i = 0; i < W; i++) {
                        int idx = j * W + i;
                        if (occupancy[idx] != Occupancy::Free) continue;
                        double s = 0;
                        for (int dk = -K2; dk <= K2; dk++)
                            for (int dl = -K2; dl <= K2; dl++) {
                                int ni = i+dk, nj = j+dl;
                                if (ni >= 0 && ni < W && nj >= 0 && nj < H) {
                                    int nidx = nj*W + ni;
                                    s += refined[nidx] * psf[(dl+K2)*K + (dk+K2)];
                                }
                            }
                        conv[idx] = s;
                    }
                }
                for (int idx = 0; idx < W*H; idx++) {
                    if (occupancy[idx] != Occupancy::Free) continue;
                    if (conv[idx] > 1e-10) refined[idx] *= hitMap[idx] / conv[idx];
                }
            }

            // Find peak of refined map
            double maxVal = 0;
            int peakIdx = 0;
            for (int idx = 0; idx < W*H; idx++) {
                if (occupancy[idx] == Occupancy::Free && refined[idx] > maxVal) {
                    maxVal = refined[idx];
                    peakIdx = idx;
                }
            }
            if (maxVal > 0) {
                Vector2 sdrEst = gridMetadata.indicesToCoordinates(peakIdx % W, peakIdx / W);
                // FIX: unconditional SDR (no GT leakage)
                GSL_INFO("[SDR] peak=({:.2f},{:.2f}) wind_dir={:.2f}",
                         sdrEst.x, sdrEst.y, avg_wdir);
                sourceLocation.x = sdrEst.x;
                sourceLocation.y = sdrEst.y;
            }
        }

double error = sqrt(pow(resultLogging.sourcePositionGT.x - sourceLocation.x, 2) +
                           pow(resultLogging.sourcePositionGT.y - sourceLocation.y, 2));
        double errorAll = sqrt(pow(resultLogging.sourcePositionGT.x - sourceLocationAll.x, 2) +
                              pow(resultLogging.sourcePositionGT.y - sourceLocationAll.y, 2));

        std::string resultString = fmt::format("RESULT: Success={}, t={:.2f}, err={:.2f}, WCC={}, WRSD={}",
                                               (int)result, search_t, error,
                                               settings.declaration.useWCC, settings.declaration.useWRSD);
        GSL_INFO_COLOR(fmt::terminal_color::blue, "{}", resultString);

        if (resultLogging.resultsFile != "")
        {
            std::ofstream file;
            file.open(resultLogging.resultsFile, std::ios_base::app);
            if (result != GSLResult::Success)
                file << "FAILED ";
            file << resultLogging.navigationTime << " " << search_t << " " << errorAll << " " << error << " " << iterationsCounter << " "
                 << Utils::Variance(Grid2D<double>(sourceProbability, occupancy, gridMetadata)) << "\n";
            file.close();
        }
        else
            GSL_WARN("No file provided for logging result.");

        if (resultLogging.navigationPathFile != "")
        {
            std::ofstream file;
            file.open(resultLogging.navigationPathFile, std::ios_base::app);
            file << "------------------------\n";
            for (PoseWithCovarianceStamped p : resultLogging.robotPosesVector)
                file << p.pose.pose.position.x << ", " << p.pose.pose.position.y << "\n";
            file.close();
        }
        else
            GSL_WARN("No file provided for logging path.");
    }

} // namespace GSL
