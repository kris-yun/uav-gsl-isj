#include "gsl_server/algorithms/Common/Grid2D.hpp"
#include "gsl_server/algorithms/Common/Utils/Math.hpp"
#include <fstream>
#include <cmath>
#include <algorithm>
#include <deque>
#include <numeric>
#include <limits>
#include <gsl_server/algorithms/PMFS/PMFS.hpp>


// ---- Review module adapters (EGS/DIRL/RGC) ----
#include <uav_gsl_review/EvidenceGate.hpp>
#include <uav_gsl_review/DirectionalDeconvRefiner.hpp>
#include <uav_gsl_review/ReliabilityGate.hpp>

static uav_gsl_review::GridSpec makeReviewGrid(const GSL::Grid2DMetadata& meta) {
    uav_gsl_review::GridSpec g;
    g.width = meta.dimensions.x;
    g.height = meta.dimensions.y;
    g.resolution = meta.cellSize;
    g.origin_x = meta.origin.x;
    g.origin_y = meta.origin.y;
    return g;
}

static std::vector<int> makeFreeMask(const std::vector<GSL::Occupancy>& occupancy) {
    std::vector<int> mask(occupancy.size(), 0);
    for (size_t i = 0; i < occupancy.size(); ++i) {
        mask[i] = (occupancy[i] == GSL::Occupancy::Free) ? 1 : 0;
    }
    return mask;
}

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



    //========================================
    static bool fileIsEmptyOrMissing(const std::string& path)
    {
        std::ifstream in(path);
        return !in.good() || in.peek() == std::ifstream::traits_type::eof();
    }


    //========================================
    // MHC: Morphological Hit-map Cleanup
    //   Concept from image processing morphology (Serra, 1982).
    //   Opening removes isolated noise hits; closing fills gaps in hit clusters.
    //   Applied to the binary hit map before SDR deconvolution.
    //========================================
    static std::vector<double> morphOpen(const std::vector<double>& src, int W, int H,
                                         const std::vector<Occupancy>& occ, int radius)
    {
        // Erosion: min in neighborhood
        std::vector<double> eroded(W * H, 0.0);
        for (int j = 0; j < H; j++)
            for (int i = 0; i < W; i++) {
                int idx = j * W + i;
                if (occ[idx] != Occupancy::Free) continue;
                double minVal = src[idx];
                for (int dj = -radius; dj <= radius; dj++)
                    for (int di = -radius; di <= radius; di++) {
                        int ni = i + di, nj = j + dj;
                        if (ni >= 0 && ni < W && nj >= 0 && nj < H) {
                            int nidx = nj * W + ni;
                            if (occ[nidx] == Occupancy::Free)
                                minVal = std::min(minVal, src[nidx]);
                        }
                    }
                eroded[idx] = minVal;
            }
        // Dilation: max in neighborhood
        std::vector<double> opened(W * H, 0.0);
        for (int j = 0; j < H; j++)
            for (int i = 0; i < W; i++) {
                int idx = j * W + i;
                if (occ[idx] != Occupancy::Free) continue;
                double maxVal = eroded[idx];
                for (int dj = -radius; dj <= radius; dj++)
                    for (int di = -radius; di <= radius; di++) {
                        int ni = i + di, nj = j + dj;
                        if (ni >= 0 && ni < W && nj >= 0 && nj < H) {
                            int nidx = nj * W + ni;
                            if (occ[nidx] == Occupancy::Free)
                                maxVal = std::max(maxVal, eroded[nidx]);
                        }
                    }
                opened[idx] = maxVal;
            }
        return opened;
    }

    struct PsdeEstimate
    {
        bool valid{false};
        double x{0.0};
        double y{0.0};
        double distance{0.0};
        double spread{0.0};
        double sigma_z{0.0};
        double avg_wind{0.0};
        double avg_wdir{0.0};
        double centroid_x{0.0};
        double centroid_y{0.0};
    };

    static PsdeEstimate computePsdeEstimate(const PMFS_internal::Settings& settings,
                                            int hce_hit_count,
                                            double hce_weight_mass,
                                            double hce_weighted_x,
                                            double hce_weighted_y,
                                            double hce_weighted_x2,
                                            double hce_weighted_y2,
                                            double hce_wind_sin_accum,
                                            double hce_wind_cos_accum,
                                            double hce_wind_speed_accum,
                                            bool hasPeakGas,
                                            const Vector2& peakGasPosition,
                                            const Vector2& fallbackDirectionTarget)
    {
        PsdeEstimate out;
        if (hce_hit_count < settings.mac.min_hits || hce_weight_mass <= 0.0 || !hasPeakGas)
            return out;

        static const double Cz_table[] = {0.0, 0.3974, 0.2751, 0.2093, 0.1542, 0.1164, 0.0825};
        static const double Dz_table[] = {0.0, 0.8697, 0.8949, 0.9087, 0.9193, 0.9257, 0.9290};
        const int sc = std::max(1, std::min(6, settings.mac.stability_class));
        const double Cz = Cz_table[sc];
        const double Dz = Dz_table[sc];
        const double h_eff = std::max(settings.mac.flight_height - settings.mac.source_height, 0.1);

        out.centroid_x = hce_weighted_x / hce_weight_mass;
        out.centroid_y = hce_weighted_y / hce_weight_mass;
        // Paper formula: RMS distance of all hits from centroid
        // sigma_obs = sqrt( E[X^2] - E[X]^2 ) = sqrt( sum(C*x^2)/M - (sum(C*x)/M)^2 )
        const double var_x = std::max(0.0, hce_weighted_x2 / hce_weight_mass - out.centroid_x * out.centroid_x);
        const double var_y = std::max(0.0, hce_weighted_y2 / hce_weight_mass - out.centroid_y * out.centroid_y);
        out.spread = std::sqrt(var_x + var_y);  // RMS spatial dispersion

        const double hit_density = 1.0;  // Removed arbitrary scaling; sigma_obs is already physical
        out.sigma_z = std::max(0.1, std::min(out.spread * hit_density, settings.mac.sigma_z_max));
        const double C_ratio = Cz / std::pow(h_eff, Dz);
        if (C_ratio <= 0.0 || !std::isfinite(C_ratio))
            return out;

        const double d_raw = std::pow(out.sigma_z / C_ratio, 1.0 / Dz);
        if (!std::isfinite(d_raw))
            return out;
        out.distance = std::max(settings.mac.min_distance, std::min(d_raw, settings.mac.max_distance_weight));

        out.avg_wind = std::max(hce_wind_speed_accum / std::max(1, hce_hit_count), 0.001);
        out.avg_wdir = std::atan2(hce_wind_sin_accum / std::max(1, hce_hit_count),
                                  hce_wind_cos_accum / std::max(1, hce_hit_count));
        const double wind_x = out.avg_wind * std::cos(out.avg_wdir);
        const double wind_y = out.avg_wind * std::sin(out.avg_wdir);
        const double ws = std::sqrt(wind_x * wind_x + wind_y * wind_y);

        double dir_x = 0.0;
        double dir_y = 0.0;
        if (ws > 0.01)
        {
            const double upwind_sign = settings.mac.wind_vector_is_flow_to ? -1.0 : 1.0;
            dir_x = upwind_sign * wind_x / ws;
            dir_y = upwind_sign * wind_y / ws;
        }
        else
        {
            dir_x = fallbackDirectionTarget.x - out.centroid_x;
            dir_y = fallbackDirectionTarget.y - out.centroid_y;
            const double norm = std::sqrt(dir_x * dir_x + dir_y * dir_y);
            if (norm > 0.01)
            {
                dir_x /= norm;
                dir_y /= norm;
            }
        }

        if (std::abs(dir_x) <= 0.001 && std::abs(dir_y) <= 0.001)
            return out;

        out.x = out.centroid_x + dir_x * out.distance;
        out.y = out.centroid_y + dir_y * out.distance;
        out.valid = std::isfinite(out.x) && std::isfinite(out.y);
        return out;
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

        bool pmfsConvergencePass = (variance < settings.declaration.threshold && megPass && wccPass);

        // EGS: Evidence-Gated Safeguard - reject false declarations when evidence is weak
        if (settings.review.egs_enabled && pmfsConvergencePass) {
            auto reviewGrid = makeReviewGrid(gridMetadata);
            auto reviewFreeMask = makeFreeMask(occupancy);

            uav_gsl_review::EvidenceGateConfig ecfg;
            ecfg.min_iterations = settings.review.egs_min_iterations;
            ecfg.min_hit_count = settings.review.egs_min_hit_count;
            ecfg.min_hit_mass = settings.review.egs_min_hit_mass;
            ecfg.min_hit_bbox_diag_m = settings.review.egs_min_hit_bbox_diag_m;
            ecfg.min_wind_coherence = settings.review.egs_min_wind_coherence;
            ecfg.max_posterior_entropy_norm = settings.review.egs_max_entropy_norm;
            ecfg.min_posterior_peak_ratio = settings.review.egs_min_posterior_peak_ratio;
            ecfg.reject_no_hit_convergence = settings.review.egs_reject_no_hit_convergence;

            uav_gsl_review::EvidenceGate gate(ecfg);
            auto summary = gate.summarize(sourceProbability, reviewFreeMask, reviewGrid, review_hit_archive_, iterationsCounter);
            auto decision = gate.decide(summary, true);
            review_last_egs_reason_ = decision.reason;
            review_last_egs_allow_ = decision.allow_declaration;

            if (!decision.allow_declaration) {
                GSL_INFO("[EGS] Rejecting PMFS declaration: {} (hits={} mass={:.4f} bbox={:.2f})",
                         decision.reason, summary.hit_count, summary.hit_mass, summary.hit_bbox_diag_m);
                return GSLResult::Running;
            }
            GSL_INFO("[EGS] Allowing declaration: {}", decision.reason);
        }

        if (pmfsConvergencePass) {
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
        const double mapVar = Utils::Variance(Grid2D<double>(sourceProbability, occupancy, gridMetadata));

        // 0) ASA: use accumulated temporal average for final estimate
        if (settings.simulation.asa_enabled && !asa_accumulated_map_.empty() && asa_update_count_ > 0)
        {
            sourceProbability = asa_accumulated_map_;
            GSL_INFO("[ASA-final] using accumulated average over {} updates", asa_update_count_);
        }

        // 1) Base PMFS source estimate. This is the clean map-based estimate.
        Vector2 mapEstimate;
        Vector2 sourceLocationAll;
        if (settings.declaration.useWRSD)
        {
            mapEstimate = refineSourceLocation(sourceProbability, occupancy, gridMetadata);
            sourceLocationAll = Utils::ExpectedValue(Grid2D<double>(sourceProbability, occupancy, gridMetadata), 1);
        }
        else
        {
            sourceLocationAll = Utils::ExpectedValue(Grid2D<double>(sourceProbability, occupancy, gridMetadata), 1);
            mapEstimate = Utils::ExpectedValue(Grid2D<double>(sourceProbability, occupancy, gridMetadata), 0.05);
        }

        Vector2 sourceLocation = mapEstimate;
        std::string selectedEstimator = settings.declaration.useWRSD ? "pmfs_wrsd" : "pmfs_expected";

        double hce_x = std::numeric_limits<double>::quiet_NaN();
        double hce_y = std::numeric_limits<double>::quiet_NaN();
        if (hce_weight_mass > 0.0)
        {
            hce_x = hce_weighted_x / hce_weight_mass;
            hce_y = hce_weighted_y / hce_weight_mass;
        }

        // 2) Optional PGPT/HCE fallback. Disabled in baseline unless explicitly enabled.
        if (settings.method.pgpt_enabled && hasPeakGas &&
            mapVar > settings.declaration.threshold * 2.0 && peakGasConcentration > thresholdGas)
        {
            sourceLocation = peakGasPosition;
            selectedEstimator = "pgpt";
            GSL_INFO("[PGPT-final] using peak gas ({:.2f},{:.2f}) map_var={:.3f}",
                     peakGasPosition.x, peakGasPosition.y, mapVar);
        }

        if (settings.method.hce_enabled && hce_weight_mass > 0.0 && hce_hit_count >= settings.mac.min_hits &&
            mapVar > settings.declaration.threshold)
        {
            sourceLocation = Vector2{hce_x, hce_y};
            selectedEstimator = "hce";
            GSL_INFO("[HCE-final] using centroid ({:.2f},{:.2f}) hits={} map_var={:.3f}",
                     hce_x, hce_y, hce_hit_count, mapVar);
        }

        // 3) Optional PSDE final estimator. No GT is used here.
        PsdeEstimate psde = computePsdeEstimate(settings,
                                                hce_hit_count,
                                                hce_weight_mass,
                                                hce_weighted_x,
                                                hce_weighted_y,
                                                hce_weighted_x2,
                                                hce_weighted_y2,
                                                hce_wind_sin_accum,
                                                hce_wind_cos_accum,
                                                hce_wind_speed_accum,
                                                hasPeakGas,
                                                peakGasPosition,
                                                sourceLocation);
        if (settings.method.psde_final_enabled && psde.valid)
        {
            GSL_INFO("[PSDE-final] centroid=({:.2f},{:.2f}) spread={:.2f} sigma_z={:.2f} d={:.2f} est=({:.2f},{:.2f})",
                     psde.centroid_x, psde.centroid_y, psde.spread, psde.sigma_z, psde.distance, psde.x, psde.y);
            sourceLocation.x = psde.x;
            sourceLocation.y = psde.y;
            selectedEstimator = "psde_final";
            mac_estimated_distance = psde.distance;
        }


        // 3b) Optional SPW final estimator. Matched-filter weighting of sourceProbability by hitMap.
        if (settings.simulation.spw_enabled && hasPeakGas &&
            iterationsCounter >= (uint)settings.simulation.spw_min_updates)
        {
            const int W = gridMetadata.dimensions.x;
            const int H = gridMetadata.dimensions.y;
            std::vector<double> weighted(W * H, 0.0);
            double total = 0.0;
            const double gamma = settings.simulation.spw_gamma;

            // Build a normalized hit-likelihood map from peak gas position
            // Using Gaussian blob centered at peak gas location
            // Use raw (pre-TDC) peak for SDR blob construction
            const Vector2& sdr_peak = raw_hasPeakGas ? raw_peakGasPosition : peakGasPosition;
            const double sdr_peak_conc = raw_hasPeakGas ? raw_peakGasConcentration : peakGasConcentration;
            auto pidx = gridMetadata.coordinatesToIndices(sdr_peak);
            int pi = std::max(0, std::min(W - 1, pidx.x));
            int pj = std::max(0, std::min(H - 1, pidx.y));
            std::vector<double> hitLikelihood(W * H, 1e-8);
            const int radius = 8;
            for (int dj = -radius; dj <= radius; dj++)
                for (int di = -radius; di <= radius; di++) {
                    int ni = pi + di, nj = pj + dj;
                    if (ni >= 0 && ni < W && nj >= 0 && nj < H) {
                        int idx = nj * W + ni;
                        if (occupancy[idx] == Occupancy::Free) {
                            double d2 = (di * di + dj * dj) / std::max(1.0, (double)(radius * radius / 4.0));
                            hitLikelihood[idx] = peakGasConcentration * std::exp(-0.5 * d2) + 1e-8;
                        }
                    }
                }

            // Element-wise: weighted = sourceProb * hitLikelihood^gamma
            for (int idx = 0; idx < W * H; idx++) {
                if (occupancy[idx] != Occupancy::Free) continue;
                weighted[idx] = sourceProbability[idx] * std::pow(hitLikelihood[idx], gamma);
                total += weighted[idx];
            }

            if (total > 0.0) {
                // Normalize and find peak
                double maxVal = 0.0;
                int peakIdx = 0;
                for (int idx = 0; idx < W * H; idx++) {
                    if (occupancy[idx] != Occupancy::Free) continue;
                    weighted[idx] /= total;
                    if (weighted[idx] > maxVal) { maxVal = weighted[idx]; peakIdx = idx; }
                }
                Vector2 spwEst = gridMetadata.indicesToCoordinates(peakIdx % W, peakIdx / W);
                sourceLocation = spwEst;
                selectedEstimator = "spw";
                GSL_INFO("[SPW-final] est=({:.2f},{:.2f}) gamma={:.2f}", spwEst.x, spwEst.y, gamma);
            }
        }

        // 4) Optional SDR final estimator. No GT gate is used; only non-GT confidence criteria are allowed.
        double sdr_x = std::numeric_limits<double>::quiet_NaN();
        double sdr_y = std::numeric_limits<double>::quiet_NaN();
        double sdr_peak_ratio = 0.0;
        if (settings.simulation.sdr_enabled && hce_hit_count >= settings.simulation.sdr_min_hits && (raw_hasPeakGas || hasPeakGas))
        {
            int W = gridMetadata.dimensions.x;
            int H = gridMetadata.dimensions.y;
            std::vector<double> hitMap(W * H, 0.0);

            // Use raw (pre-TDC) peak for SDR blob construction
            const Vector2& sdr_peak = raw_hasPeakGas ? raw_peakGasPosition : peakGasPosition;
            const double sdr_peak_conc = raw_hasPeakGas ? raw_peakGasConcentration : peakGasConcentration;
            auto pidx = gridMetadata.coordinatesToIndices(sdr_peak);
            int pi = std::max(0, std::min(W - 1, pidx.x));
            int pj = std::max(0, std::min(H - 1, pidx.y));
            const int blob_radius = std::max(1, (int)std::ceil(settings.simulation.sdr_blob_radius));
            for (int di = -blob_radius; di <= blob_radius; di++) {
                for (int dj = -blob_radius; dj <= blob_radius; dj++) {
                    int ni = pi + di, nj = pj + dj;
                    if (ni >= 0 && ni < W && nj >= 0 && nj < H) {
                        int idx = nj * W + ni;
                        if (occupancy[idx] == Occupancy::Free) {
                            double d2 = di * di + dj * dj;
                            hitMap[idx] += sdr_peak_conc * std::exp(-d2 / std::max(1.0, settings.simulation.sdr_blob_radius));
                        }
                    }
                }
            }

            // MHC: adaptive morphological cleanup. Skip when hits are sparse.
            if (settings.simulation.mhc_enabled && hce_hit_count >= 10) {
                int nonzero = 0;
                for (int idx = 0; idx < W * H; idx++)
                    if (occupancy[idx] == Occupancy::Free && hitMap[idx] > 1e-10) nonzero++;
                int mr = (nonzero > 10) ? std::max(1, settings.simulation.mhc_open_radius) : 0;
                if (mr > 0) {
                    hitMap = morphOpen(hitMap, W, H, occupancy, mr);
                    GSL_INFO("[MHC-adapt] cleaned {} cells radius={}", nonzero, mr);
                } else {
                    GSL_INFO("[MHC-adapt] skipped ({} cells)", nonzero);
                }
            }

            const double avg_wdir = std::atan2(hce_wind_sin_accum / std::max(1, hce_hit_count),
                                               hce_wind_cos_accum / std::max(1, hce_hit_count));
            const double cos_w = std::cos(avg_wdir), sin_w = std::sin(avg_wdir);
            int K = std::max(3, settings.simulation.sdr_psf_size);
            if (K % 2 == 0) K += 1;
            int K2 = K / 2;
            std::vector<double> psf(K * K, 0.0);
            double psf_sum = 0.0;
            for (int di = -K2; di <= K2; di++) {
                for (int dj = -K2; dj <= K2; dj++) {
                    const double along = di * cos_w + dj * sin_w;
                    const double across = -di * sin_w + dj * cos_w;
                    const double sigma_along = (along < 0) ? 3.0 : 1.0;
                    const double sigma_across = 1.5;
                    const double val = std::exp(-0.5 * (along * along / (sigma_along * sigma_along) +
                                                        across * across / (sigma_across * sigma_across)));
                    psf[(dj + K2) * K + (di + K2)] = val;
                    psf_sum += val;
                }
            }
            if (psf_sum > 0.0)
                for (auto& p : psf) p /= psf_sum;

            std::vector<double> refined = hitMap;
            for (int rl = 0; rl < settings.simulation.sdr_rl_iterations; rl++) {
                std::vector<double> conv(W * H, 0.0);
                for (int j = 0; j < H; j++) {
                    for (int i = 0; i < W; i++) {
                        int idx = j * W + i;
                        if (occupancy[idx] != Occupancy::Free) continue;
                        double v = 0.0;
                        for (int dk = -K2; dk <= K2; dk++)
                            for (int dl = -K2; dl <= K2; dl++) {
                                int ni = i + dk, nj = j + dl;
                                if (ni >= 0 && ni < W && nj >= 0 && nj < H) {
                                    int nidx = nj * W + ni;
                                    v += refined[nidx] * psf[(dl + K2) * K + (dk + K2)];
                                }
                            }
                        conv[idx] = v;
                    }
                }
                for (int idx = 0; idx < W * H; idx++) {
                    if (occupancy[idx] != Occupancy::Free) continue;
                    if (conv[idx] > 1e-10) refined[idx] *= hitMap[idx] / conv[idx];
                }
            }

            double maxVal = 0.0;
            double sumVal = 0.0;
            int peakIdx = 0;
            for (int idx = 0; idx < W * H; idx++) {
                if (occupancy[idx] != Occupancy::Free) continue;
                sumVal += std::max(0.0, refined[idx]);
                if (refined[idx] > maxVal) {
                    maxVal = refined[idx];
                    peakIdx = idx;
                }
            }
            sdr_peak_ratio = (sumVal > 0.0) ? maxVal / sumVal : 0.0;
            if (maxVal > 0.0 && sdr_peak_ratio >= settings.simulation.sdr_min_peak_mass_ratio) {
                Vector2 sdrEst = gridMetadata.indicesToCoordinates(peakIdx % W, peakIdx / W);
                sdr_x = sdrEst.x;
                sdr_y = sdrEst.y;
                // ITS: Inertia Tensor Selection. From astronomical image analysis.
                // Computes eccentricity of hit distribution to adaptively control SDR.
                // Circular hits (near source) -> skip SDR. Elongated (far source) -> use SDR.
                if (raw_hce_hit_count >= 5) {
                    double cx = 0.0, cy = 0.0;
                    for (auto& p : raw_hit_positions_) { cx += p.first; cy += p.second; }
                    int n = raw_hit_positions_.size();
                    cx /= n; cy /= n;
                    double mxx = 0.0, myy = 0.0, mxy = 0.0;
                    for (auto& p : raw_hit_positions_) {
                        double dx = p.first - cx, dy = p.second - cy;
                        mxx += dx * dx;
                        myy += dy * dy;
                        mxy += dx * dy;
                    }
                    mxx /= n; myy /= n; mxy /= n;
                    double trace = mxx + myy;
                    double det = mxx * myy - mxy * mxy;
                    double disc = std::sqrt(std::max(0.0, trace * trace / 4.0 - det));
                    double lambda1 = trace / 2.0 + disc;
                    double lambda2 = trace / 2.0 - disc;
                    double ecc = (lambda1 > 1e-10) ? std::sqrt(1.0 - lambda2 / lambda1) : 0.0;
                    const double ecc_threshold = 0.7;
                    // Continuous blend: w=ecc interpolates between baseline and SDR.
                    // ecc~0 (circular) -> keep baseline; ecc~1 (elongated) -> use SDR.
                    double total_var = mxx + myy;
                    double var_norm = std::min(1.0, total_var / 9.0);
                    double w = ecc * var_norm;
                    sourceLocation.x = (1.0 - w) * sourceLocation.x + w * sdrEst.x;
                    sourceLocation.y = (1.0 - w) * sourceLocation.y + w * sdrEst.y;
                    selectedEstimator = "its_blend";
                    GSL_INFO("[ITS] blend: ecc={:.3f} var={:.3f} varN={:.3f} w={:.3f} est=({:.2f},{:.2f})", ecc, total_var, var_norm, w, sourceLocation.x, sourceLocation.y);
                }
            }
        }

        // 5) Optional PWC as a final post-processing correction. No GT is used.
        if (pwcCorrector_ && pwcCorrector_->config().enabled)
        {
            int src_i = gridMetadata.coordinatesToIndices(sourceLocation).x;
            int src_j = gridMetadata.coordinatesToIndices(sourceLocation).y;
            src_i = std::max(0, std::min((int)gridMetadata.dimensions.x - 1, src_i));
            src_j = std::max(0, std::min((int)gridMetadata.dimensions.y - 1, src_j));
            int src_idx = src_j * gridMetadata.dimensions.x + src_i;

            double wind_x = 0.0, wind_y = 0.0;
            if (src_idx >= 0 && src_idx < (int)estimatedWindVectors.size()) {
                wind_x = estimatedWindVectors[src_idx].x;
                wind_y = estimatedWindVectors[src_idx].y;
            }
            if (std::abs(wind_x) < 1e-6 && std::abs(wind_y) < 1e-6) {
                wind_x = last_windSpeed * std::cos(last_windDirection);
                wind_y = last_windSpeed * std::sin(last_windDirection);
            }

            const double plume_spread = std::sqrt(std::max(0.0, mapVar));
            auto pwc_out = pwcCorrector_->correct(sourceLocation.x, sourceLocation.y, wind_x, wind_y, plume_spread);
            if (pwc_out.applied) {
                GSL_INFO("[PWC-final] ({:.2f},{:.2f})->({:.2f},{:.2f}) wind=({:.4f},{:.4f}) corr={:.3f}",
                         sourceLocation.x, sourceLocation.y, pwc_out.corrected_x, pwc_out.corrected_y,
                         wind_x, wind_y, pwc_out.correction_distance);
                sourceLocation.x = pwc_out.corrected_x;
                sourceLocation.y = pwc_out.corrected_y;
                selectedEstimator += "+pwc";
            }
        }


        // ---- Review M2 DIRL: Directional Inverse Restoration Layer ----
        uav_gsl_review::GridSpec rgrid = makeReviewGrid(gridMetadata);
        std::vector<int> rfreeMask = makeFreeMask(occupancy);

        uav_gsl_review::CandidateEstimate pmfsCand;
        pmfsCand.name = selectedEstimator;
        pmfsCand.xy = {sourceLocation.x, sourceLocation.y};
        pmfsCand.valid = true;

        uav_gsl_review::CandidateEstimate peakCand;
        peakCand.name = "peak_gas";
        peakCand.xy = {static_cast<double>(raw_peakGasPosition.x), static_cast<double>(raw_peakGasPosition.y)};
        peakCand.valid = raw_hasPeakGas;

        uav_gsl_review::CandidateEstimate centroidCand;
        centroidCand.name = "hit_centroid";
        centroidCand.valid = false;
        if (!review_hit_archive_.empty()) {
            double sx = 0.0, sy = 0.0, m = 0.0;
            for (const auto& h : review_hit_archive_) {
                double w = std::max(0.0, h.concentration);
                sx += w * h.x;
                sy += w * h.y;
                m += w;
            }
            if (m > 1e-12) {
                centroidCand.xy = {sx / m, sy / m};
                centroidCand.valid = true;
            }
        }

        uav_gsl_review::DirectionalDeconvResult dirlResult;
        if (settings.review.dirl_enabled) {
            uav_gsl_review::DirectionalDeconvConfig dcfg;
            dcfg.min_hits = settings.review.dirl_min_hits;
            dcfg.min_concentration = settings.review.dirl_min_concentration;
            dcfg.rl_iterations = settings.review.dirl_rl_iterations;
            dcfg.psf_size = settings.review.dirl_psf_size;
            dcfg.sigma_upwind_cells = settings.review.dirl_sigma_upwind_cells;
            dcfg.sigma_downwind_cells = settings.review.dirl_sigma_downwind_cells;
            dcfg.sigma_crosswind_cells = settings.review.dirl_sigma_crosswind_cells;
            dcfg.hit_splat_radius_cells = settings.review.dirl_hit_splat_radius_cells;
            dcfg.hit_splat_sigma_cells = settings.review.dirl_hit_splat_sigma_cells;
            dcfg.hit_weight_exponent = settings.review.dirl_hit_weight_exponent;
            dcfg.pmfs_prior_power = settings.review.dirl_pmfs_prior_power;
            dcfg.wind_vector_is_flow_to = settings.mac.wind_vector_is_flow_to;
            dcfg.min_wind_speed = settings.review.dirl_min_wind_speed;
            dcfg.min_peak_mass_ratio = settings.review.dirl_min_peak_mass_ratio;
            dcfg.max_entropy_norm = settings.review.dirl_max_entropy_norm;

            uav_gsl_review::DirectionalDeconvRefiner refiner(dcfg);
            dirlResult = refiner.refine(sourceProbability, rfreeMask, rgrid, review_hit_archive_);

            review_last_dirl_x_ = dirlResult.valid ? dirlResult.peak_estimate.x : std::numeric_limits<double>::quiet_NaN();
            review_last_dirl_y_ = dirlResult.valid ? dirlResult.peak_estimate.y : std::numeric_limits<double>::quiet_NaN();
            review_last_dirl_peak_ratio_ = dirlResult.peak_mass_ratio;
            review_last_dirl_entropy_ = dirlResult.entropy_norm;
            review_last_dirl_valid_ = dirlResult.valid;

            if (settings.review.review_modules_verbose) {
                GSL_INFO("[DIRL] valid={} reason={} peak=({:.2f},{:.2f}) ratio={:.4f} entropy={:.4f} hits={} windC={:.3f}",
                         dirlResult.valid, dirlResult.reason,
                         dirlResult.peak_estimate.x, dirlResult.peak_estimate.y,
                         dirlResult.peak_mass_ratio, dirlResult.entropy_norm,
                         dirlResult.hit_count, dirlResult.wind_coherence);
            }
        }

        // ---- Review M3 RGC: Reliability-Gated Correction ----
        if (settings.review.rgc_enabled) {
            uav_gsl_review::EvidenceGate eg;
            auto evidence = eg.summarize(sourceProbability, rfreeMask, rgrid, review_hit_archive_, iterationsCounter);

            uav_gsl_review::ReliabilityGateConfig rcfg;
            rcfg.dirl_min_hits = settings.review.rgc_dirl_min_hits;
            rcfg.dirl_min_wind_coherence = settings.review.rgc_dirl_min_wind_coherence;
            rcfg.dirl_min_peak_mass_ratio = settings.review.rgc_dirl_min_peak_mass_ratio;
            rcfg.max_dirl_pmfs_disagreement_m = settings.review.rgc_max_dirl_pmfs_disagreement_m;
            rcfg.weak_evidence_max_correction_m = settings.review.rgc_weak_evidence_max_correction_m;
            rcfg.allow_blend = settings.review.rgc_allow_blend;
            rcfg.min_blend_weight = settings.review.rgc_min_blend_weight;
            rcfg.max_blend_weight = settings.review.rgc_max_blend_weight;

            uav_gsl_review::ReliabilityGate rgc(rcfg);
            auto rgcDecision = rgc.select(evidence, pmfsCand, peakCand, centroidCand, dirlResult);

            sourceLocation.x = rgcDecision.fused_xy.x;
            sourceLocation.y = rgcDecision.fused_xy.y;
            selectedEstimator = rgcDecision.selected.name;
            review_last_rgc_reason_ = rgcDecision.reason;

            if (settings.review.review_modules_verbose) {
                GSL_INFO("[RGC] selected={} reason={} fused=({:.2f},{:.2f}) blend_w={:.3f}",
                         rgcDecision.selected.name, rgcDecision.reason,
                         rgcDecision.fused_xy.x, rgcDecision.fused_xy.y, rgcDecision.blend_weight);
            }
        }
        else if (settings.review.dirl_enabled && dirlResult.valid) {
            // Without RGC, directly use DIRL estimate
            sourceLocation.x = dirlResult.peak_estimate.x;
            sourceLocation.y = dirlResult.peak_estimate.y;
            selectedEstimator = "dirl_allhits";
        }

        // Final metrics are computed only after the final estimate is fixed.
        const double error = sqrt(pow(resultLogging.sourcePositionGT.x - sourceLocation.x, 2) +
                                  pow(resultLogging.sourcePositionGT.y - sourceLocation.y, 2));
        const double errorAll = sqrt(pow(resultLogging.sourcePositionGT.x - sourceLocationAll.x, 2) +
                                     pow(resultLogging.sourcePositionGT.y - sourceLocationAll.y, 2));
        const char* status = (result == GSLResult::Success) ? "SUCCESS" : "FAILED";

        std::string resultString = fmt::format("RESULT: status={}, method={}, t={:.2f}, err={:.3f}, estimator={}, WCC={}, WRSD={}",
                                               status, settings.method.method_id, search_t, error, selectedEstimator,
                                               settings.declaration.useWCC, settings.declaration.useWRSD);
        GSL_INFO_COLOR(fmt::terminal_color::blue, "{}", resultString);

        // Legacy server output retained for compatibility with existing benchmark_runner parsing:
        // [FAILED] navigationTime search_t errorAll error iterations variance
        if (resultLogging.resultsFile != "")
        {
            std::ofstream file;
            file.open(resultLogging.resultsFile, std::ios_base::app);
            if (result != GSLResult::Success)
                file << "FAILED ";
            file << resultLogging.navigationTime << " " << search_t << " " << errorAll << " " << error << " "
                 << iterationsCounter << " " << mapVar << "\n";
            file.close();

            // Audit CSV: richer, headered, and safe for statistical analysis. GT appears only here,
            // after final estimate has been fixed.
            const std::string auditPath = resultLogging.resultsFile + ".audit.csv";
            const bool needHeader = fileIsEmptyOrMissing(auditPath);
            std::ofstream audit(auditPath, std::ios_base::app);
            if (audit.good())
            {
                if (needHeader)
                {
                    audit << "status,method_id,search_time_s,navigation_time_s,iterations,variance,"
                          << "final_error_m,error_expected_m,final_x,final_y,map_x,map_y,expected_x,expected_y,"
                          << "selected_estimator,pwc_enabled,psde_online_enabled,psde_final_enabled,sdr_enabled,"
                          << "bwe_enabled,pgpt_enabled,hce_enabled,hce_hit_count,hce_x,hce_y,peak_gas,peak_x,peak_y,"
                          << "psde_valid,psde_distance_m,psde_spread_m,psde_sigma_z,psde_x,psde_y,sdr_x,sdr_y,sdr_peak_ratio,"
                          << "gt_x,gt_y\n";
                }
                audit << status << "," << settings.method.method_id << "," << search_t << ","
                      << resultLogging.navigationTime << "," << iterationsCounter << "," << mapVar << ","
                      << error << "," << errorAll << "," << sourceLocation.x << "," << sourceLocation.y << ","
                      << mapEstimate.x << "," << mapEstimate.y << "," << sourceLocationAll.x << "," << sourceLocationAll.y << ","
                      << selectedEstimator << "," << (settings.pwc.enabled ? 1 : 0) << ","
                      << (settings.method.psde_online_enabled ? 1 : 0) << ","
                      << (settings.method.psde_final_enabled ? 1 : 0) << ","
                      << (settings.simulation.sdr_enabled ? 1 : 0) << ","
                      << (settings.method.bwe_enabled ? 1 : 0) << ","
                      << (settings.method.pgpt_enabled ? 1 : 0) << ","
                      << (settings.method.hce_enabled ? 1 : 0) << ","
                      << hce_hit_count << "," << hce_x << "," << hce_y << ","
                      << peakGasConcentration << "," << (hasPeakGas ? peakGasPosition.x : std::numeric_limits<double>::quiet_NaN()) << ","
                      << (hasPeakGas ? peakGasPosition.y : std::numeric_limits<double>::quiet_NaN()) << ","
                      << (psde.valid ? 1 : 0) << "," << psde.distance << "," << psde.spread << "," << psde.sigma_z << ","
                      << (psde.valid ? psde.x : std::numeric_limits<double>::quiet_NaN()) << ","
                      << (psde.valid ? psde.y : std::numeric_limits<double>::quiet_NaN()) << ","
                      << sdr_x << "," << sdr_y << "," << sdr_peak_ratio << ","
                      << resultLogging.sourcePositionGT.x << "," << resultLogging.sourcePositionGT.y << "\n";
            }
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
