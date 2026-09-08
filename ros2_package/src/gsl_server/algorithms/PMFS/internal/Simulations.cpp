#include "gsl_server/algorithms/PMFS/internal/HitProbability.hpp"
#include <cstddef>
#include <gsl_server/algorithms/Common/Utils/Math.hpp>
#include <gsl_server/algorithms/Common/Utils/Time.hpp>
#include <gsl_server/algorithms/PMFS/PMFS.hpp>
#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>
#include <gsl_server/algorithms/PMFS/internal/Simulations.hpp>
#include <gsl_server/algorithms/PMFS/internal/MEACIParams.hpp>
#include <gsl_server/core/Logging.hpp>

#include <opencv2/core/hal/interface.h>
#include <opencv2/core/saturate.hpp>
#include <opencv2/core/types.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <Eigen/Dense>
#include <Eigen/Eigenvalues>

#include <fstream>
#include <cmath>
#include <limits>
#include <array>
#include <algorithm>
#include <chrono>
#include <filesystem>
#include <unordered_set>
#include <unordered_map>
#include <numeric>
#include <tuple>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <cstdlib>

#include <DDA/DDA.h>
#include <gsl_server/core/Profiling.hpp>

namespace GSL::PMFS_internal
{
    namespace NQA = Utils::NQA;
    using HashSet = std::unordered_set<Vector2Int>;

    namespace
    {
        // Peter J. Acklam's rational approximation for Phi^{-1}.  The
        // approximation is deterministic and more than sufficient for the
        // finite candidate ranks used by the A7 copula channel.
        double normalQuantile(double probability)
        {
            const double p = std::clamp(probability, 1e-12, 1.0 - 1e-12);
            constexpr double a1 = -3.969683028665376e+01;
            constexpr double a2 =  2.209460984245205e+02;
            constexpr double a3 = -2.759285104469687e+02;
            constexpr double a4 =  1.383577518672690e+02;
            constexpr double a5 = -3.066479806614716e+01;
            constexpr double a6 =  2.506628277459239e+00;
            constexpr double b1 = -5.447609879822406e+01;
            constexpr double b2 =  1.615858368580409e+02;
            constexpr double b3 = -1.556989798598866e+02;
            constexpr double b4 =  6.680131188771972e+01;
            constexpr double b5 = -1.328068155288572e+01;
            constexpr double c1 = -7.784894002430293e-03;
            constexpr double c2 = -3.223964580411365e-01;
            constexpr double c3 = -2.400758277161838e+00;
            constexpr double c4 = -2.549732539343734e+00;
            constexpr double c5 =  4.374664141464968e+00;
            constexpr double c6 =  2.938163982698783e+00;
            constexpr double d1 =  7.784695709041462e-03;
            constexpr double d2 =  3.224671290700398e-01;
            constexpr double d3 =  2.445134137142996e+00;
            constexpr double d4 =  3.754408661907416e+00;
            constexpr double low = 0.02425;
            constexpr double high = 1.0 - low;
            if (p < low)
            {
                const double q = std::sqrt(-2.0 * std::log(p));
                return (((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6) /
                       ((((d1*q+d2)*q+d3)*q+d4)*q+1.0);
            }
            if (p > high)
            {
                const double q = std::sqrt(-2.0 * std::log(1.0-p));
                return -(((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6) /
                        ((((d1*q+d2)*q+d3)*q+d4)*q+1.0);
            }
            const double q = p - 0.5;
            const double r = q * q;
            return (((((a1*r+a2)*r+a3)*r+a4)*r+a5)*r+a6)*q /
                   (((((b1*r+b2)*r+b3)*r+b4)*r+b5)*r+1.0);
        }

        std::string p2StableID(const NQA::Node* node)
        {
            return fmt::format("quadtree_{}_{}_{}_{}", node->origin.x, node->origin.y, node->size.x, node->size.y);
        }

        std::array<double, 8> p2Summary(const Grid2D<HitProbability>& grid, const std::vector<float>* simulated)
        {
            std::vector<double> values;
            values.reserve(grid.data.size());
            for (size_t i = 0; i < grid.data.size(); ++i)
            {
                if (grid.occupancy[i] != Occupancy::Free || grid.data[i].confidence <= 0)
                    continue;
                values.push_back(simulated ? static_cast<double>((*simulated)[i]) : grid.data[i].probability());
            }

            std::array<double, 8> result{};
            if (values.empty())
            {
                result.fill(std::numeric_limits<double>::quiet_NaN());
                return result;
            }
            std::sort(values.begin(), values.end());
            const double sum = std::accumulate(values.begin(), values.end(), 0.0);
            result[0] = sum / static_cast<double>(values.size());
            double sq = 0.0;
            for (const double value : values)
                sq += (value - result[0]) * (value - result[0]);
            result[1] = std::sqrt(sq / static_cast<double>(values.size()));
            result[2] = values.back();
            const auto quantile = [&values](double q)
            {
                const double position = q * static_cast<double>(values.size() - 1);
                const size_t lower = static_cast<size_t>(position);
                const size_t upper = std::min(lower + 1, values.size() - 1);
                const double fraction = position - static_cast<double>(lower);
                return values[lower] + fraction * (values[upper] - values[lower]);
            };
            result[3] = quantile(0.50);
            result[4] = quantile(0.75);
            result[5] = quantile(0.90);
            result[6] = quantile(0.95);
            result[7] = static_cast<double>(std::count_if(values.begin(), values.end(), [](double value) { return value > 0.0; })) /
                        static_cast<double>(values.size());
            return result;
        }

        void p2WriteSummary(std::ofstream& out, const std::array<double, 8>& summary)
        {
            for (double value : summary)
                out << ',' << std::setprecision(17) << value;
        }

        double wallEpochSeconds()
        {
            return std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();
        }

        struct TadmMat3
        {
            double a[3][3]{};
        };

        TadmMat3 tadmFromArray(const std::array<double, 9>& values)
        {
            TadmMat3 out;
            for (int i = 0; i < 3; ++i)
                for (int j = 0; j < 3; ++j)
                    out.a[i][j] = values[static_cast<size_t>(3 * i + j)];
            return out;
        }

        double tadmDet(const TadmMat3& m)
        {
            return m.a[0][0] * (m.a[1][1] * m.a[2][2] - m.a[1][2] * m.a[2][1])
                 - m.a[0][1] * (m.a[1][0] * m.a[2][2] - m.a[1][2] * m.a[2][0])
                 + m.a[0][2] * (m.a[1][0] * m.a[2][1] - m.a[1][1] * m.a[2][0]);
        }

        TadmMat3 tadmInverse(const TadmMat3& m)
        {
            const double det = tadmDet(m);
            if (!(std::isfinite(det) && std::abs(det) > 1e-14))
                throw std::runtime_error("TADM 3x3 matrix is singular");
            TadmMat3 out;
            out.a[0][0] = (m.a[1][1] * m.a[2][2] - m.a[1][2] * m.a[2][1]) / det;
            out.a[0][1] = (m.a[0][2] * m.a[2][1] - m.a[0][1] * m.a[2][2]) / det;
            out.a[0][2] = (m.a[0][1] * m.a[1][2] - m.a[0][2] * m.a[1][1]) / det;
            out.a[1][0] = (m.a[1][2] * m.a[2][0] - m.a[1][0] * m.a[2][2]) / det;
            out.a[1][1] = (m.a[0][0] * m.a[2][2] - m.a[0][2] * m.a[2][0]) / det;
            out.a[1][2] = (m.a[0][2] * m.a[1][0] - m.a[0][0] * m.a[1][2]) / det;
            out.a[2][0] = (m.a[1][0] * m.a[2][1] - m.a[1][1] * m.a[2][0]) / det;
            out.a[2][1] = (m.a[0][1] * m.a[2][0] - m.a[0][0] * m.a[2][1]) / det;
            out.a[2][2] = (m.a[0][0] * m.a[1][1] - m.a[0][1] * m.a[1][0]) / det;
            return out;
        }

        double tadmLogit(double value)
        {
            constexpr double eps = 0.5 / 201.0; // frozen N_RECORD=200 contract
            const double p = std::clamp(value, eps, 1.0 - eps);
            return std::log(p / (1.0 - p));
        }


        double tadmLogMarginal(const std::vector<double>& discrepancy,
                               const std::vector<std::array<double, 3>>& basis,
                               const std::vector<double>& weights,
                               const TadmPriorParameters& prior)
        {
            if (discrepancy.empty() || discrepancy.size() != basis.size() || discrepancy.size() != weights.size())
                throw std::runtime_error("TADM support vectors have inconsistent sizes");
            if (!(prior.sigma2 > 0.0) || !std::isfinite(prior.sigma2))
                throw std::runtime_error("TADM sigma2 is invalid");

            const TadmMat3 lambda = tadmFromArray(prior.lambda);
            const double logdetLambda = tadmDet(lambda) > 0.0 ? std::log(tadmDet(lambda)) : -INFINITY;
            if (!std::isfinite(logdetLambda))
                throw std::runtime_error("TADM prior covariance is not positive definite");
            const TadmMat3 lambdaInv = tadmInverse(lambda);
            TadmMat3 A = lambdaInv;
            double quad0 = 0.0;
            double q[3]{};
            for (size_t i = 0; i < discrepancy.size(); ++i)
            {
                const double w = weights[i];
                if (!(w > 0.0) || !std::isfinite(w))
                    throw std::runtime_error("TADM confidence weight is invalid");
                const double dinv = w / prior.sigma2;
                const double r = discrepancy[i] - (basis[i][0] * prior.mu[0] + basis[i][1] * prior.mu[1] + basis[i][2] * prior.mu[2]);
                quad0 += dinv * r * r;
                for (int a = 0; a < 3; ++a)
                {
                    q[a] += basis[i][a] * dinv * r;
                    for (int b = 0; b < 3; ++b)
                        A.a[a][b] += basis[i][a] * dinv * basis[i][b];
                }
            }
            const double detA = tadmDet(A);
            if (!(std::isfinite(detA) && detA > 0.0))
                throw std::runtime_error("TADM Woodbury matrix is not positive definite");
            const TadmMat3 Ainv = tadmInverse(A);
            double qAq = 0.0;
            for (int a = 0; a < 3; ++a)
                for (int b = 0; b < 3; ++b)
                    qAq += q[a] * Ainv.a[a][b] * q[b];

            double logdetD = 0.0;
            for (const double w : weights)
                logdetD += std::log(prior.sigma2 / w);
            const double quad = quad0 - qAq;
            return -0.5 * (quad + logdetD + logdetLambda + std::log(detA) +
                           static_cast<double>(discrepancy.size()) * std::log(2.0 * M_PI));
        }

        std::array<int, 4> tadmParseCandidateID(const std::string& id)
        {
            const std::string prefix = "quadtree_";
            if (id.rfind(prefix, 0) != 0)
                throw std::runtime_error("TADM candidate id does not use quadtree contract");
            std::stringstream stream(id.substr(prefix.size()));
            std::array<int, 4> values{};
            char separator = 0;
            for (int i = 0; i < 4; ++i)
            {
                if (!(stream >> values[static_cast<size_t>(i)]))
                    throw std::runtime_error("TADM candidate id is malformed");
                if (i < 3 && (!(stream >> separator) || separator != '_'))
                    throw std::runtime_error("TADM candidate id separator is malformed");
            }
            return values;
        }
    }

    // We have a long list of pre-calculated random values for Speeeeeeeeeeeeeeeeed
    static thread_local Utils::PrecalculatedGaussian<2500> gaussian;

    static void weighted_incremental_variance(double value, double weight, double& mean, double& weight_sum, double& weight_squared_sum,
                                              double& variance)
    {
        // Updating Mean and Variance Estimates: An Improved Method D.H.D. West 1979
        // A zero-posterior source hypothesis contributes no mass.  Skipping it
        // is mathematically exact and avoids the undefined 0 / 0 update when
        // it is the first hypothesis encountered for a prediction cell.
        if (weight == 0.0)
            return;
        weight_sum = weight_sum + weight;
        weight_squared_sum = weight_squared_sum + weight * weight;
        double mean_old = mean;
        mean = mean_old + (weight / weight_sum) * (value - mean_old);
        variance = variance + weight * (value - mean_old) * (value - mean);
    }

    // create the occupancy Quadtree
    void Simulations::initializeMap(const std::vector<std::vector<uint8_t>>& occupancyMap)
    {
        ZoneScoped;
        quadtree = std::make_unique<Utils::NQA::Quadtree>(occupancyMap);
        QTleaves = quadtree->fusedLeaves(settings.maxRegionSize);

        mapSegmentation.resize(occupancyMap.size(), std::vector<Utils::NQA::Node*>(occupancyMap[0].size(), nullptr));

        GSL_INFO("Number of cells after fusing quadtree: {0}", QTleaves.size());
        // generate the image of indices so you can map a cell in the map to the corresponding leaf of the quatree
        for (int i = 0; i < QTleaves.size(); i++)
        {
            Utils::NQA::Node& node = QTleaves[i];
            Vector2Int start = node.origin;
            Vector2Int end = node.origin + node.size;

            for (int r = start.x; r < end.x; r++)
            {
                for (int c = start.y; c < end.y; c++)
                {
                    GSL_ASSERT_MSG(mapSegmentation[r][c] == nullptr, "fused cells are overlapping");
                    mapSegmentation[r][c] = &node;
                }
            }
        }
        sourceProbInternal.resize(sourceProb.data.size(), 0.0);
        pcAciCausalPosteriorGrid.assign(sourceProb.data.size(), 0.0L);
        pcAciDesignPriorGrid.assign(sourceProb.data.size(), 0.0L);
        pcAciIncomingNativePriorSnapshot.assign(sourceProb.data.size(), 0.0L);
        pcAciCausalStateAvailable = false;
        pcAciLastAcceptedUpdateId = 0;
        pcAciAcceptedThisUpdate = false;
        pcAciA9DesignWarmupSeen = false;

        size_t freeCountForDesignPrior = 0;
        for (size_t cell = 0; cell < measuredHitProb.occupancy.size(); ++cell)
            if (measuredHitProb.occupancy[cell] == Occupancy::Free)
                ++freeCountForDesignPrior;
        if (freeCountForDesignPrior > 0)
        {
            const long double uniform = 1.0L / static_cast<long double>(freeCountForDesignPrior);
            for (size_t cell = 0; cell < measuredHitProb.occupancy.size(); ++cell)
                if (measuredHitProb.occupancy[cell] == Occupancy::Free)
                    pcAciDesignPriorGrid[cell] = uniform;
        }

        // we want to have the occupancy mask as a cv image so we can correct the blur later
        freeSpaceMask = cv::Mat(
            cv::Size(measuredHitProb.metadata.dimensions.x, measuredHitProb.metadata.dimensions.y),
            CV_32F,
            cv::Scalar(0, 0, 0));

        for (int j = 0; j < measuredHitProb.metadata.dimensions.y; j++)
        {
            for (int i = 0; i < measuredHitProb.metadata.dimensions.x; i++)
            {
                if (measuredHitProb.freeAt(i, j))
                    freeSpaceMask.at<float>(j, i) = 1;
            }
        }
    }

    void Simulations::configureNativeDeterminism(uint64_t globalSeed, uint64_t transportSubstream)
    {
        nativeRandomSeed = globalSeed;
        nativeTransportSubstream = transportSubstream;
        nativeDeterministicRng = true;
    }

    void Simulations::setNativeSourceUpdateId(uint64_t sourceUpdateId)
    {
        nativeSourceUpdateId = sourceUpdateId;
    }

    void Simulations::configureEventEvidence(bool enabled, int transportReplicas, bool contrastiveRatio)
    {
        if (transportReplicas < 1 || transportReplicas > 8)
            throw std::invalid_argument("CER_TRANSPORT_REPLICA_RANGE");
        eventEvidenceEnabled = enabled;
        eventEvidenceContrastiveRatio = enabled && contrastiveRatio;
        eventEvidenceTransportReplicas = transportReplicas;
        eventEvidence.clear();
        eventEvidenceContextProbability.clear();
    }

    void Simulations::recordEventEvidence(const Vector2& position, bool hit, double concentration,
                                          double threshold, uint64_t blockId)
    {
        if (!eventEvidenceEnabled)
            return;
        const Vector2Int indices = measuredHitProb.metadata.coordinatesToIndices(position);
        if (!measuredHitProb.metadata.indicesInBounds(indices) || !measuredHitProb.freeAt(indices))
            throw std::runtime_error("CER_EVENT_OUTSIDE_FREE_SUPPORT");
        if (blockId == 0 || (!eventEvidence.empty() && blockId <= eventEvidence.back().blockId))
            throw std::runtime_error("CER_EVENT_BLOCK_NOT_MONOTONE");
        if (!(std::isfinite(concentration) && concentration >= 0.0 &&
              std::isfinite(threshold) && threshold > 0.0))
            throw std::runtime_error("CER_EVENT_SENSOR_VALUE_INVALID");
        eventEvidence.push_back(EventEvidence{measuredHitProb.metadata.indexOf(indices), hit,
                                              concentration, threshold, blockId});
    }

    void Simulations::updateSourceProbability(float refineFraction)
    {
        ZoneScoped;
        // This flag describes the current update only.  History is committed
        // after scoring, so the post-commit update id cannot identify that
        // the likelihood just computed was a first difference.
        sdTemporalDifferenceActive = false;
        GSL_INFO_COLOR(fmt::terminal_color::yellow, "Started simulations. Might take a while!");
        Utils::Time::Stopwatch stopwatch;
        if (contextBankExportEnabled)
            contextBankWallStartEpoch = wallEpochSeconds();
        std::vector<NQA::Node> localCopyLeaves = QTleaves;
        p2LastEvaluatedCandidates.clear();
        {
            std::lock_guard<std::mutex> guard(nativeCandidateHitMapsMutex);
            nativeCandidateHitMaps.clear();
        }
        std::unordered_set<std::string> p2CandidateIDs;
        const auto recordP2Candidates = [&](const std::vector<LeafScore>& candidateScores)
        {
            if (!p2ShadowEnabled && !tadmEnabled)
                return;
            for (const LeafScore& item : candidateScores)
            {
                NQA::Node* node = item.leaf;
                if (node == nullptr || node->value != 1)
                    continue;
                const std::string stableID = p2StableID(node);
                if (!p2CandidateIDs.insert(stableID).second)
                    continue;
                const Vector2 point = measuredHitProb.metadata.indicesToCoordinates(
                    node->origin.x + node->size.x / 2, node->origin.y + node->size.y / 2);
                std::shared_ptr<const std::vector<float>> nativeHitMap;
                {
                    std::lock_guard<std::mutex> guard(nativeCandidateHitMapsMutex);
                    const auto it = nativeCandidateHitMaps.find(stableID);
                    if (it != nativeCandidateHitMaps.end())
                        nativeHitMap = it->second;
                }
                P2ShadowCandidate candidate;
                candidate.stableID = stableID;
                candidate.point = point;
                candidate.nativeScore = item.score;
                candidate.rect = {node->origin.x, node->origin.y, node->size.x, node->size.y};
                candidate.persistentCarrier = false;
                candidate.nativeHitMap = std::move(nativeHitMap);
                p2LastEvaluatedCandidates.push_back(std::move(candidate));
            }
        };

        // first, coarse simulation based on the quadtree decomposition of the map
        //------------------------------------------------------------------------
        //------------------------------------------------------------------------

        // store the score of each region to figure out which ones are worth subdividing for finer simulation
        std::vector<LeafScore> scores(localCopyLeaves.size());
        for (int leafIndex = 0; leafIndex < scores.size(); leafIndex++)
            scores[leafIndex].leaf = &localCopyLeaves[leafIndex];

        // this is used to calculate how much the state of this cell depends on where the source is. It is used for the movemente strategy
        struct VarianceCalculationData
        {
            double mean = 0;
            double weight_sum = 0;
            double weight_squared_sum = 0;
            double variance = 0;
        };
        std::vector<VarianceCalculationData> varianceCalculationData(measuredHitProb.data.size());

        int numberOfSimulations = 0;
        resultsFirstLevel.clear();
        resultsFirstLevel.reserve(scores.size());
// iterate over the leaves of the quadtree, doing one simulation for each and calculating how well it fits our measured gas map
#pragma omp parallel for schedule(dynamic)
        for (int leafIndex = 0; leafIndex < scores.size(); leafIndex++)
        {
            SimulationResult result = runSimulation(scores, leafIndex);
            if (!result.valid)
                continue;

// update the information for the variance calulation
#pragma omp critical
            {
                resultsFirstLevel.push_back(result);
                numberOfSimulations++;
                if (!eventEvidenceContrastiveRatio)
                {
                    for (int cell = 0; cell < result.hitMap.size(); cell++)
                    {
                        auto& var = varianceCalculationData[cell];
                        weighted_incremental_variance(result.hitMap[cell],
                                                      result.sourceProb,
                                                      var.mean,
                                                      var.weight_sum,
                                                      var.weight_squared_sum,
                                                      var.variance);
                    }
                }
            }
        }

        if (eventEvidenceContrastiveRatio)
        {
            initializeContrastiveEventContext(resultsFirstLevel);
            applyContrastiveEventEvidence(resultsFirstLevel, scores);
            for (const SimulationResult& result : resultsFirstLevel)
            {
                if (!result.valid)
                    continue;
                for (size_t cell = 0; cell < result.hitMap.size(); ++cell)
                {
                    auto& var = varianceCalculationData[cell];
                    weighted_incremental_variance(result.hitMap[cell], result.sourceProb,
                                                  var.mean, var.weight_sum,
                                                  var.weight_squared_sum, var.variance);
                }
            }
        }

        recordP2Candidates(scores);

// update the variance thing (for the movement strategy)
        size_t zeroWeightVarianceCells = 0;
#pragma omp parallel for reduction(+ : zeroWeightVarianceCells)
        for (int cellI = 0; cellI < measuredHitProb.data.size(); cellI++)
        {
            if (measuredHitProb.occupancy[cellI] == Occupancy::Free)
            {
                const auto& statistics = varianceCalculationData[cellI];
                if (statistics.weight_sum > 0.0)
                    varianceOfHitProb[cellI] = statistics.variance / statistics.weight_sum;
                else
                {
                    // With no posterior mass, this cell has no
                    // posterior-weighted predictive dispersion.
                    varianceOfHitProb[cellI] = 0.0;
                    ++zeroWeightVarianceCells;
                }
            }
        }
        if (zeroWeightVarianceCells > 0)
            GSL_INFO("[CTPI-DIAG] planner variance zero-mass cells={}", zeroWeightVarianceCells);

        GSL_TRACE("First simulation level done");

        // RC2 qualification diagnostics only.  This is an isolated binary
        // audit hook; it does not alter PMFS state or score calculation.
        size_t finiteSourceProbInternal = 0;
        long double sumSourceProbInternal = 0.0L;
        long double minSourceProbInternal = std::numeric_limits<long double>::infinity();
        long double maxSourceProbInternal = -std::numeric_limits<long double>::infinity();
        for (const long double value : sourceProbInternal)
        {
            if (!std::isfinite(static_cast<double>(value)))
                continue;
            ++finiteSourceProbInternal;
            sumSourceProbInternal += value;
            minSourceProbInternal = std::min(minSourceProbInternal, value);
            maxSourceProbInternal = std::max(maxSourceProbInternal, value);
        }
        size_t finiteVarianceOfHitProb = 0;
        for (const double value : varianceOfHitProb)
            if (std::isfinite(value))
                ++finiteVarianceOfHitProb;
        GSL_INFO("[RC2-DIAG] scores_size={} refineFraction={} refine_product={} valid_first_level={} "
                 "sum_sourceProbInternal_before_norm={} min_sourceProbInternal_before_norm={} "
                 "max_sourceProbInternal_before_norm={} finite_sourceProbInternal={} "
                 "finite_varianceOfHitProb={}",
                 scores.size(), refineFraction, scores.size() * refineFraction,
                 resultsFirstLevel.size(), static_cast<double>(sumSourceProbInternal),
                 static_cast<double>(minSourceProbInternal), static_cast<double>(maxSourceProbInternal),
                 finiteSourceProbInternal, finiteVarianceOfHitProb);
        // now, finer simulation where it is deemed relevant
        //------------------------------------------------------
        //------------------------------------------------------

        int numberOfLevelsSimulated = 1;
        // Choose the most interesting quadtree leaves (the ones with the best result in the previous iteration) and subdivide them to do more
        // simulations. Keep going until none of the leaves can be subdivided any more
        while (scores.size() > 0)
        {
            std::sort(scores.begin(), scores.end(), [](LeafScore result1, LeafScore result2)
                      {
                          return result1.score > result2.score;
                      });

            // subdivide the good cells and add the children to the list of cells to simulate
            std::vector<LeafScore> newLevel;
            for (int leafIndex = 0; leafIndex < scores.size() * refineFraction; leafIndex++)
            {
                NQA::Node* leaf = scores[leafIndex].leaf;
                bool hasChildren = leaf->subdivide();
                if (hasChildren)
                {
                    for (int childI = 0; childI < 4; childI++)
                        if (leaf->children[childI])
                            newLevel.push_back({0, (leaf->children[childI]).get()});
                }
            }
            scores = newLevel;

            numberOfLevelsSimulated++;
            numberOfSimulations += scores.size();

// run the simulations of the new level and get scores for each node
            std::vector<SimulationResult> levelResults(scores.size());
#pragma omp parallel for schedule(dynamic)
            for (int leafIndex = 0; leafIndex < scores.size(); leafIndex++)
                levelResults[leafIndex] = runSimulation(scores, leafIndex);

            if (eventEvidenceContrastiveRatio)
                applyContrastiveEventEvidence(levelResults, scores);

            recordP2Candidates(scores);

            GSL_TRACE("Simulation level {} done", numberOfLevelsSimulated);
        }

        GSL_INFO("Number of levels in the simulation: {0}", numberOfLevelsSimulated);
        GSL_INFO("Total number of simulations: {0}", numberOfSimulations);

        // PC-SD-TFEI carrier construction.  The native PMFS quadtree remains
        // the frozen background/planner computation above.  Only the
        // proposed SD likelihood sees this deterministic physical carrier:
        // fixed 2x2 map cells, rebuilt from occupancy geometry at every
        // update with identical IDs.  This removes policy-induced leaf
        // correspondence and preserves sub-metre spatial resolution without
        // reading truth or copying the native posterior ordering.
        persistentCarrierMode = false;
        if (tadmEnabled && (pfdiMode == "sd" || pfdiMode == "al" || pfdiMode == "pc_aci" || pfdiMode == "me_aci" || pfdiMode == "me_aci_shadow" ||
                            pfdiMode == "ec_edcl" || pfdiMode == "ec_edcl_shadow"))
        {
            constexpr int carrierStride = 2;
            std::vector<P2ShadowCandidate> carriers;
            const int width = measuredHitProb.metadata.dimensions.x;
            const int height = measuredHitProb.metadata.dimensions.y;
            carriers.reserve(static_cast<size_t>((width + carrierStride - 1) / carrierStride) *
                             static_cast<size_t>((height + carrierStride - 1) / carrierStride));
            for (int i = 0; i < width; i += carrierStride)
            {
                for (int j = 0; j < height; j += carrierStride)
                {
                    const int sx = std::min(carrierStride, width - i);
                    const int sy = std::min(carrierStride, height - j);
                    int freeCount = 0;
                    Vector2 pointSum(0.0f, 0.0f);
                    for (int x = i; x < i + sx; ++x)
                        for (int y = j; y < j + sy; ++y)
                        {
                            const size_t cell = measuredHitProb.metadata.indexOf({x, y});
                            if (measuredHitProb.occupancy[cell] != Occupancy::Free)
                                continue;
                            pointSum += measuredHitProb.metadata.indexToCoordinates(cell);
                            ++freeCount;
                        }
                    if (freeCount == 0)
                        continue;
                    P2ShadowCandidate carrier;
                    carrier.stableID = fmt::format("quadtree_{}_{}_{}_{}", i, j, sx, sy);
                    carrier.point = pointSum / static_cast<float>(freeCount);
                    // A9 persistent carriers are geometry-only.  Native
                    // posterior mass must not enter the source bank,
                    // support gate, eigenbasis, or causal prior.
                    carrier.nativeScore = 0.0L;
                    carrier.rect = {i, j, sx, sy};
                    carrier.persistentCarrier = true;
                    carriers.push_back(std::move(carrier));
                }
            }
            p2LastEvaluatedCandidates = std::move(carriers);
            persistentCarrierMode = !p2LastEvaluatedCandidates.empty();
            GSL_INFO("PFDI PC-SD-TFEI persistent physical carrier: stride_cells={}, carriers={}, native_quadtree_candidates={}, fixed_ids=true",
                     carrierStride, p2LastEvaluatedCandidates.size(), p2CandidateIDs.size());
        }

        if (tadmEnabled && !applyTADMPosterior())
            throw std::runtime_error("TADM online scoring failed; refusing native fallback");

        Utils::NormalizeDistributionLong(
            sourceProbInternal,
            sourceProb.occupancy);

        for (size_t i = 0; i < sourceProb.data.size(); i++)
            sourceProb.data[i] = (double)sourceProbInternal[i];

        size_t finiteNormalized = 0;
        long double normalizedSum = 0.0L;
        for (const double value : sourceProb.data)
        {
            if (!std::isfinite(value))
                continue;
            ++finiteNormalized;
            normalizedSum += value;
        }
        GSL_INFO("[RC2-DIAG] normalized_finite_count={} normalized_sum={}",
                 finiteNormalized, static_cast<double>(normalizedSum));

        if ((pfdiMode == "pc_aci" || pfdiMode == "me_aci") && pcAciAcceptedThisUpdate)
        {
            // Only an accepted causal update advances the independent causal
            // state.  Native PMFS values produced after a rejected gate are
            // deliberately excluded from the next causal prior.
            pcAciCausalPosteriorGrid = sourceProbInternal;
            pcAciCausalStateAvailable = true;
            pcAciLastAcceptedUpdateId = tadmSourceUpdateId;
        }

        GSL_INFO("Time ellapsed in simulation = {} s", stopwatch.ellapsed());
        if (contextBankExportEnabled)
        {
            contextBankNativeSimulationCount = static_cast<size_t>(numberOfSimulations);
            contextBankWallEndEpoch = wallEpochSeconds();
        }
    }

    Simulations::SimulationResult Simulations::runSimulation(std::vector<LeafScore>& scores, size_t index)
    {
        SimulationResult result{.valid = false};
        NQA::Node* node = scores[index].leaf;
        if (node->value != 1)
            return result;

        result.valid = true;
        result.leaf = node;
        result.hitMap.resize(measuredHitProb.data.size(), 0.0);

        long double mixtureScore = 0.0L;
        const int replicas = eventEvidenceEnabled ? eventEvidenceTransportReplicas : 1;
        std::vector<float> memberMap(result.hitMap.size(), 0.0f);
        Vector2 firstSampledSourcePoint(0.0f, 0.0f);
        for (int replica = 0; replica < replicas; ++replica)
        {
            std::fill(memberMap.begin(), memberMap.end(), 0.0f);
            EventKeyedTransportRng nativeRng(EventKey{nativeRandomSeed, nativeSourceUpdateId,
                static_cast<uint64_t>(replica), nativeTransportSubstream});
            SimulationSource memberSource(node, measuredHitProb.metadata, nativeDeterministicRng ? &nativeRng : nullptr);
            simulateSourceInPosition(memberSource, memberMap, true, settings.iterationsToRecord, settings.deltaTime,
                                     settings.noiseSTDev, nullptr, nativeDeterministicRng ? &nativeRng : nullptr);
            for (size_t i = 0; i < memberMap.size(); ++i)
                result.hitMap[i] += memberMap[i] / static_cast<float>(replicas);
            if (eventEvidenceContrastiveRatio)
                result.transportMemberHitMaps.push_back(memberMap);
            else
                mixtureScore += (eventEvidenceEnabled ? sourceProbFromEvents(memberMap)
                                                       : sourceProbFromMaps(measuredHitProb, memberMap)) /
                                static_cast<long double>(replicas);
            if (replica == 0)
                firstSampledSourcePoint = memberSource.firstSampledSourcePoint();
        }

        if (settings.blurSigmaX > 0 || settings.blurSigmaY > 0)
        {
            cv::Mat asImage(result.hitMap);
            asImage = asImage.reshape(1, measuredHitProb.metadata.dimensions.y);
            blurHitMap(asImage);
        }

        // This write-only hook is intentionally before score construction. It
        // exports the exact map that PMFS has already simulated, without
        // exposing score/posterior/planner state to the adapter.
        const Vector2 candidatePoint = measuredHitProb.metadata.indicesToCoordinates(
            node->origin.x + node->size.x / 2, node->origin.y + node->size.y / 2);
        const std::string stableID = p2StableID(node);
        {
            auto nativeHitMap = std::make_shared<std::vector<float>>(result.hitMap);
            std::lock_guard<std::mutex> guard(nativeCandidateHitMapsMutex);
            nativeCandidateHitMaps[stableID] = std::move(nativeHitMap);
        }
        exportCandidateHitMap(stableID, candidatePoint, result.hitMap);

        result.sourceProb = eventEvidenceContrastiveRatio ? 1.0L : mixtureScore;
        exportNativeCandidateRecord(stableID, candidatePoint, firstSampledSourcePoint, result.sourceProb, result.hitMap);

        scores[index].score = result.sourceProb;

        // assign this probability to all cells that fall inside this region
        for (int cellI = node->origin.x; cellI < (node->origin.x + node->size.x); cellI++)
            for (int cellJ = node->origin.y; cellJ < (node->origin.y + node->size.y); cellJ++)
                sourceProbInternal[sourceProb.metadata.indexOf({cellI, cellJ})] = result.sourceProb;
        return result;
    }

    void Simulations::configureReadOnlyForwardExport(bool enabled, const std::string& directory, const std::string& runUUID,
                                                      const std::string& pmfsParametersHash, const std::string& mapHash,
                                                      const std::string& windHash, const std::string& codeHash)
    {
        readOnlyForwardExportEnabled = enabled;
        readOnlyForwardExportDirectory = directory;
        readOnlyForwardExportRunUUID = runUUID;
        readOnlyForwardExportPMFSParametersHash = pmfsParametersHash;
        readOnlyForwardExportMapHash = mapHash;
        readOnlyForwardExportWindHash = windHash;
        readOnlyForwardExportCodeHash = codeHash;
        readOnlyForwardExportCurrentDirectory = readOnlyForwardExportDirectory;
    }

    void Simulations::configureContextBankExport(bool enabled, const std::string& directory, const std::string& runUUID)
    {
        contextBankExportEnabled = enabled && !directory.empty();
        contextBankExportDirectory = directory;
        contextBankExportRunUUID = runUUID;
        if (!contextBankExportEnabled)
            return;
        std::filesystem::create_directories(contextBankExportDirectory);
        std::ofstream contract(contextBankExportDirectory + "/context_bank_contract.json", std::ios::out | std::ios::trunc);
        contract << "{\n"
                 << "  \"export_only\": true,\n"
                 << "  \"p2_shadow_enabled\": false,\n"
                 << "  \"native_forward_maps\": true,\n"
                 << "  \"native_source_point\": \"first_sampled_point_if_recoverable\",\n"
                 << "  \"support\": \"occupancy_free_and_confidence_gt_zero\"\n"
                 << "}\n";
    }

    void Simulations::beginContextBankUpdate(uint64_t sourceUpdateId, double simTime)
    {
        if (!contextBankExportEnabled)
            return;
        contextBankSourceUpdateId = sourceUpdateId;
        contextBankSimTime = simTime;
        readOnlyForwardExportSnapshot = static_cast<size_t>(sourceUpdateId);
        readOnlyForwardExportCurrentDirectory = fmt::format("{}/source_update_{:04}", contextBankExportDirectory, sourceUpdateId);
        std::filesystem::create_directories(readOnlyForwardExportCurrentDirectory + "/candidate_maps");
        std::ofstream manifest(readOnlyForwardExportCurrentDirectory + "/candidate_manifest.csv", std::ios::out | std::ios::trunc);
        manifest << "run_uuid,source_update_id,candidate_id,origin_i,origin_j,size_i,size_j,center_x,center_y,native_source_x,native_source_y,native_score,hit_map_file\n";
        std::ofstream alignment(readOnlyForwardExportCurrentDirectory + "/candidate_support_alignment.csv", std::ios::out | std::ios::trunc);
        alignment << "candidate_id,cell_index,grid_i,grid_j,x,y,measured_probability,measured_confidence,simulated_hit_probability,absolute_residual\n";
    }

    void Simulations::exportContextBankState(uint64_t sourceUpdateId, double simTime, double timeSincePreviousUpdate,
                                             const geometry_msgs::msg::Pose& robotPose)
    {
        if (!contextBankExportEnabled)
            return;
        const std::string directory = readOnlyForwardExportCurrentDirectory;
        std::filesystem::create_directories(directory);

        std::ofstream measured(directory + "/measured_hit_probability.csv", std::ios::out | std::ios::trunc);
        measured << "cell_index,grid_i,grid_j,x,y,occupancy,probability,logOdds,confidence,omega,distanceFromRobot,originalPropagationDirection_x,originalPropagationDirection_y\n";
        for (size_t i = 0; i < measuredHitProb.data.size(); ++i)
        {
            const Vector2Int ij = measuredHitProb.metadata.indices2D(i);
            const Vector2 xy = measuredHitProb.metadata.indexToCoordinates(i);
            const auto& h = measuredHitProb.data[i];
            measured << i << ',' << ij.x << ',' << ij.y << ',' << std::setprecision(17) << xy.x << ',' << xy.y << ','
                     << (measuredHitProb.occupancy[i] == Occupancy::Free ? "Free" : "Obstacle") << ','
                     << Utils::logOddsToProbability(h.logOdds) << ',' << h.logOdds << ',' << h.confidence << ',' << h.omega << ',' << h.distanceFromRobot << ','
                     << h.originalPropagationDirection.x << ',' << h.originalPropagationDirection.y << '\n';
        }

        std::ofstream estimatedWind(directory + "/estimated_wind.csv", std::ios::out | std::ios::trunc);
        estimatedWind << "cell_index,x,y,wind_x,wind_y\n";
        for (size_t i = 0; i < wind.data.size(); ++i)
        {
            if (wind.occupancy[i] != Occupancy::Free)
                continue;
            const Vector2 xy = wind.metadata.indexToCoordinates(i);
            estimatedWind << i << ',' << std::setprecision(17) << xy.x << ',' << xy.y << ',' << wind.data[i].x << ',' << wind.data[i].y << '\n';
        }

        std::ofstream posterior(directory + "/source_posterior.csv", std::ios::out | std::ios::trunc);
        posterior << "cell_index,x,y,source_probability\n";
        for (size_t i = 0; i < sourceProb.data.size(); ++i)
        {
            if (sourceProb.occupancy[i] != Occupancy::Free)
                continue;
            const Vector2 xy = sourceProb.metadata.indexToCoordinates(i);
            posterior << i << ',' << std::setprecision(17) << xy.x << ',' << xy.y << ',' << sourceProb.data[i] << '\n';
        }

        std::ofstream timing(contextBankExportDirectory + "/source_update_timing.csv", std::ios::out | std::ios::app);
        if (timing.tellp() == 0)
            timing << "run_uuid,source_update_id,sim_time,time_since_previous_update,wall_start_epoch,wall_end_epoch,native_candidate_count,native_forward_simulation_count,native_update_wall_s,robot_x,robot_y,robot_z,robot_yaw,grid_width,grid_height,cell_size,origin_x,origin_y\n";
        const double robotYaw = std::atan2(2.0 * (robotPose.orientation.w * robotPose.orientation.z + robotPose.orientation.x * robotPose.orientation.y),
                                           1.0 - 2.0 * (robotPose.orientation.y * robotPose.orientation.y + robotPose.orientation.z * robotPose.orientation.z));
        timing << contextBankExportRunUUID << ',' << sourceUpdateId << ',' << std::setprecision(17) << simTime << ',' << timeSincePreviousUpdate << ','
               << contextBankWallStartEpoch << ',' << contextBankWallEndEpoch << ',' << contextBankNativeSimulationCount << ','
               << contextBankNativeSimulationCount << ',' << (contextBankWallEndEpoch - contextBankWallStartEpoch) << ','
               << robotPose.position.x << ',' << robotPose.position.y << ',' << robotPose.position.z << ','
               << robotYaw << ',' << measuredHitProb.metadata.dimensions.x << ',' << measuredHitProb.metadata.dimensions.y << ','
               << measuredHitProb.metadata.cellSize << ',' << measuredHitProb.metadata.origin.x << ',' << measuredHitProb.metadata.origin.y << '\n';
        timing.flush();
    }

    void Simulations::exportNativeCandidateRecord(const std::string& stableID, const Vector2& source,
                                                  const Vector2& nativeSourcePoint, long double sourceProb,
                                                  const std::vector<float>& hitMap)
    {
        if (!contextBankExportEnabled)
            return;
        std::lock_guard<std::mutex> guard(readOnlyForwardExportMutex);
        const std::string directory = readOnlyForwardExportCurrentDirectory;
        const std::string mapFile = fmt::format("{}/candidate_maps/snapshot_{:06}_{}.f32", directory,
                                                readOnlyForwardExportSnapshot, stableID);
        std::ofstream manifest(directory + "/candidate_manifest.csv", std::ios::out | std::ios::app);
        const auto parse = [&stableID](int field)
        {
            std::vector<int> values;
            std::string current;
            std::stringstream stream(stableID.substr(std::string("quadtree_").size()));
            while (std::getline(stream, current, '_'))
                values.push_back(std::stoi(current));
            return values.at(field);
        };
        manifest << contextBankExportRunUUID << ',' << contextBankSourceUpdateId << ',' << stableID << ','
                 << parse(0) << ',' << parse(1) << ',' << parse(2) << ',' << parse(3) << ',' << std::setprecision(17)
                 << source.x << ',' << source.y << ',' << nativeSourcePoint.x << ',' << nativeSourcePoint.y << ','
                 << static_cast<double>(sourceProb) << ',' << mapFile << '\n';

        std::ofstream alignment(directory + "/candidate_support_alignment.csv", std::ios::out | std::ios::app);
        for (size_t i = 0; i < measuredHitProb.data.size(); ++i)
        {
            if (measuredHitProb.occupancy[i] != Occupancy::Free || measuredHitProb.data[i].confidence <= 0)
                continue;
            const Vector2Int ij = measuredHitProb.metadata.indices2D(i);
            const Vector2 xy = measuredHitProb.metadata.indexToCoordinates(i);
            const double measured = measuredHitProb.data[i].probability();
            alignment << stableID << ',' << i << ',' << ij.x << ',' << ij.y << ',' << std::setprecision(17) << xy.x << ',' << xy.y << ','
                      << measured << ',' << measuredHitProb.data[i].confidence << ',' << hitMap[i] << ',' << std::abs(measured - hitMap[i]) << '\n';
        }
    }

    void Simulations::configureP2Shadow(bool enabled, const std::string& directory, const std::string& runUUID,
                                        uint64_t globalSeed, int replicas, uint64_t transportSubstream)
    {
        p2ShadowEnabled = enabled && !directory.empty() && replicas > 0;
        p2ShadowDirectory = directory;
        p2ShadowRunUUID = runUUID;
        p2ShadowGlobalSeed = globalSeed;
        p2ShadowReplicas = replicas;
        p2ShadowTransportSubstream = transportSubstream;
        if (!p2ShadowEnabled)
            return;

        std::filesystem::create_directories(p2ShadowDirectory);
        std::ofstream contract(p2ShadowDirectory + "/p2_shadow_contract.json", std::ios::out | std::ios::trunc);
        contract << "{\n"
                 << "  \"contract\": \"event-keyed-replica-rng-candidate-shared-transport-crn\",\n"
                 << "  \"key\": [\"global_seed\",\"source_update_id\",\"replica_id\",\"transport_substream\"],\n"
                 << "  \"candidate_id_in_transport_key\": false,\n"
                 << "  \"global_seed\": " << p2ShadowGlobalSeed << ",\n"
                 << "  \"replicas\": " << p2ShadowReplicas << ",\n"
                 << "  \"transport_substream\": " << p2ShadowTransportSubstream << ",\n"
                 << "  \"candidate_point\": \"node_center\",\n"
                 << "  \"support\": \"occupancy_free_and_confidence_gt_zero\",\n"
                 << "  \"summary\": [\"mean\",\"std_population\",\"max\",\"q50\",\"q75\",\"q90\",\"q95\",\"fraction_gt_zero\"]\n"
                 << "}\n";
    }

    void Simulations::exportP2PredictiveEnsembleSnapshot(uint64_t sourceUpdateId, double simTime)
    {
        if (!p2ShadowEnabled || p2LastEvaluatedCandidates.empty())
            return;

        std::lock_guard<std::mutex> guard(p2ShadowMutex);
        std::filesystem::create_directories(p2ShadowDirectory);
        const std::string observationPath = p2ShadowDirectory + "/p2_shadow_observation.csv";
        const std::string candidatePath = p2ShadowDirectory + "/p2_shadow_candidates.csv";
        const std::string replicaPath = p2ShadowDirectory + "/p2_shadow_replicas.csv";

        std::ofstream observation(observationPath, std::ios::out | std::ios::app);
        if (observation.tellp() == 0)
            observation << "run_uuid,source_update_id,sim_time,support_count,obs_mean,obs_std,obs_max,obs_q50,obs_q75,obs_q90,obs_q95,obs_fraction_gt_zero\n";
        const auto observedSummary = p2Summary(measuredHitProb, nullptr);
        size_t supportCount = 0;
        for (size_t i = 0; i < measuredHitProb.data.size(); ++i)
            if (measuredHitProb.occupancy[i] == Occupancy::Free && measuredHitProb.data[i].confidence > 0)
                ++supportCount;
        observation << p2ShadowRunUUID << ',' << sourceUpdateId << ',' << std::setprecision(17) << simTime << ',' << supportCount;
        p2WriteSummary(observation, observedSummary);
        observation << '\n';

        std::ofstream candidates(candidatePath, std::ios::out | std::ios::app);
        if (candidates.tellp() == 0)
            candidates << "run_uuid,source_update_id,sim_time,candidate_id,source_x,source_y,native_score,candidate_replica_count\n";
        std::ofstream replicas(replicaPath, std::ios::out | std::ios::app);
        if (replicas.tellp() == 0)
            replicas << "run_uuid,source_update_id,sim_time,candidate_id,source_x,source_y,replica_id,global_seed,transport_substream,wall_ms,summary_mean,summary_std,summary_max,summary_q50,summary_q75,summary_q90,summary_q95,summary_fraction_gt_zero,c0p_score\n";

        for (const P2ShadowCandidate& candidate : p2LastEvaluatedCandidates)
        {
            candidates << p2ShadowRunUUID << ',' << sourceUpdateId << ',' << std::setprecision(17) << simTime << ','
                       << candidate.stableID << ',' << candidate.point.x << ',' << candidate.point.y << ','
                       << static_cast<double>(candidate.nativeScore) << ',' << p2ShadowReplicas << '\n';
            for (int replica = 0; replica < p2ShadowReplicas; ++replica)
            {
                const EventKey key{p2ShadowGlobalSeed, sourceUpdateId, static_cast<uint64_t>(replica), p2ShadowTransportSubstream};
                EventKeyedTransportRng transportRng(key);
                std::vector<float> hitMap(measuredHitProb.data.size(), 0.0f);
                const auto start = std::chrono::steady_clock::now();
                simulateSourceInPosition(SimulationSource(candidate.point, measuredHitProb.metadata), hitMap, true,
                                         settings.iterationsToRecord, settings.deltaTime, settings.noiseSTDev, nullptr, &transportRng);
                if (settings.blurSigmaX > 0 || settings.blurSigmaY > 0)
                {
                    cv::Mat asImage(hitMap);
                    asImage = asImage.reshape(1, measuredHitProb.metadata.dimensions.y);
                    blurHitMap(asImage);
                }
                const auto end = std::chrono::steady_clock::now();
                const double elapsedMs = std::chrono::duration<double, std::milli>(end - start).count();
                const auto summary = p2Summary(measuredHitProb, &hitMap);
                const long double c0pScore = sourceProbFromMaps(measuredHitProb, hitMap);
                replicas << p2ShadowRunUUID << ',' << sourceUpdateId << ',' << std::setprecision(17) << simTime << ','
                         << candidate.stableID << ',' << candidate.point.x << ',' << candidate.point.y << ',' << replica << ','
                         << p2ShadowGlobalSeed << ',' << p2ShadowTransportSubstream << ',' << elapsedMs;
                p2WriteSummary(replicas, summary);
                replicas << ',' << static_cast<double>(c0pScore) << '\n';
            }
        }
        observation.flush();
        candidates.flush();
        replicas.flush();
        GSL_INFO("P2 predictive shadow update {}: {} candidates x {} replicas", sourceUpdateId,
                 p2LastEvaluatedCandidates.size(), p2ShadowReplicas);
    }

    void Simulations::configureTADM(bool enabled, const std::string& directory, const std::string& runUUID,
                                    int priorSet, uint64_t globalSeed, int replicas, uint64_t transportSubstream,
                                    const std::string& mode)
    {
        tadmEnabled = enabled && !directory.empty() && replicas > 0 && (priorSet == 0 || priorSet == 1);
        pfdiMode = tadmEnabled ? mode : "off";
        if (pfdiMode != "sd" && pfdiMode != "tadm" && pfdiMode != "joint" && pfdiMode != "al" &&
            pfdiMode != "pc_aci" && pfdiMode != "me_aci" && pfdiMode != "me_aci_shadow" && pfdiMode != "ec_edcl" && pfdiMode != "ec_edcl_shadow")
            pfdiMode = "joint";
        tadmDirectory = directory;
        tadmRunUUID = runUUID;
        tadmGlobalSeed = globalSeed;
        tadmReplicas = replicas;
        tadmTransportSubstream = transportSubstream;
        tadmPrior.setId = priorSet;

        // These are the frozen K=4 cross-family calibration priors from the
        // offline TADM contract.  Set 0 is the H01 calibration prior; set 1 is
        // the H02 calibration prior.  No run-time observation is used here.
        if (priorSet == 1)
        {
            tadmPrior.mu = {0.202423445484406, -0.42451530047240893, -0.1553240944536439};
            tadmPrior.lambda = {
                1.795337539886964, 0.0022388792734640457, 0.4908015469313151,
                0.0022388792734640457, 0.14238736282392211, -0.04352991809521523,
                0.49080154693131506, -0.04352991809521523, 0.1806451191338588};
            tadmPrior.sigma2 = 2.039509708298329;
        }
        else
        {
            tadmPrior.mu = {-3.2448401795579316, -0.9958268577267531, -0.20065977692506648};
            tadmPrior.lambda = {
                1.8898276679919506, 0.2894302485359064, 0.01188924745757729,
                0.2894302485359064, 0.07691324290471029, -0.06053258308194314,
                0.01188924745757729, -0.060532583081943134, 0.13595202084809915};
            tadmPrior.sigma2 = 2.580076382818459;
        }

        if (!tadmEnabled)
            return;
        std::filesystem::create_directories(tadmDirectory);
        std::ofstream contract(tadmDirectory + "/tadm_contract.json", std::ios::out | std::ios::trunc);
        if (pfdiMode == "me_aci" || pfdiMode == "me_aci_shadow")
        {
            contract << "{\n"
                     << "  \"method\": \"ME-ACI-v1.0-frozen\",\n"
                     << "  \"source_prior\": \"uniform_free_cell_geometry_only\",\n"
                     << "  \"operator\": \"seven_tap_convex_logit_causal_memory_hurdle\",\n"
                     << "  \"transport_members\": 8,\n"
                     << "  \"model_error_members\": 8,\n"
                     << "  \"route_identity\": \"persistent_R_by_B_route_prefix\",\n"
                     << "  \"marginalization\": \"single_logmeanexp_over_R_by_B\",\n"
                     << "  \"candidate_id_in_rng_key\": false,\n"
                     << "  \"native_posterior_in_prior\": false,\n"
                     << "  \"truth_at_inference\": false,\n"
                     << "  \"parameter_sha256\": \"" << kMEAciParameterSHA256 << "\"\n"
                     << "}\n";
            return;
        }
        if (pfdiMode == "ec_edcl" || pfdiMode == "ec_edcl_shadow")
        {
            contract << std::setprecision(17)
                     << "{\n"
                     << "  \"method\": \"Ensemble-Calibrated-EC-ECDL-v1.0-corrected\",\n"
                     << "  \"mode\": \"" << pfdiMode << "\",\n"
                     << "  \"physical_response\": \"candidate_by_replica_simulateSourceInPosition_then_completed_block_sampling_and_Hellinger_normalization\",\n"
                     << "  \"factorization\": \"generalized_eigenchannels_Cs_over_Ceta_calibration_bank_only\",\n"
                     << "  \"history_ledger\": \"exact_Schur_conditional_increment_with_online_equals_batch_audit\",\n"
                     << "  \"nuisance_marginalization\": \"route_identity_preserved_then_logmeanexp_once\",\n"
                     << "  \"history_covariance_denominator\": \"S_times_Jc_minus_1_source_average_within_source_covariance\",\n"
                     << "  \"history_covariance_ridge\": 1e-10,\n"
                     << "  \"calibration_replicas\": 4,\n"
                     << "  \"scoring_replicas\": 4,\n"
                     << "  \"transport_epoch\": 0,\n"
                     << "  \"candidate_id_in_rng_key\": false,\n"
                     << "  \"prior\": \"uniform_free_cell_geometry_only\",\n"
                     << "  \"native_posterior_in_causal_prior\": false,\n"
                     << "  \"truth_at_inference\": false,\n"
                     << "  \"alpha_temperature_trust_region_rescue_support_truncation\": false\n"
                     << "}\n";
            return;
        }
        contract << std::setprecision(17)
                 << "{\n"
                 << "  \"method\": \"A9-TV-SD-TFEI-online-v2.1-modified-t\",\n"
                  << "  \"mode\": \"" << pfdiMode << "\",\n"
                 << "  \"formula\": \"completed-block analytic transport profile with Hellinger generalized eigenchannels and covariance-marginalized modified-t mixture relative evidence\",\n"
                 << "  \"fusion\": \"explicit_uniform_design_prior_times_qualified_joint_A9_Bayes_factor\",\n"
                  << "  \"calibration\": \"3 fixed cone spreads times 3 fixed dilution exponents integrated equally; no truth or House selection\",\n"
                 << "  \"basis\": [\"1(shared_intercept)\",\"(x-s)dot(u_hat)\",\"(x-s)dot(u_hat_perp)\"],\n"
                 << "  \"compatibility_gate\": \"replica_kl_bounded_trust_region: coherent_shift_allowed_with_disagreement_shrinkage\",\n"
                 << "  \"prior_set\": " << tadmPrior.setId << ",\n"
                 << "  \"global_seed\": " << tadmGlobalSeed << ",\n"
                  << "  \"calibration_replicas\": " << tadmReplicas << ",\n"
                  << "  \"scoring_replicas\": " << tadmReplicas << ",\n"
                 << "  \"transport_substream\": " << tadmTransportSubstream << ",\n"
                 << "  \"candidate_id_in_rng_key\": false,\n"
                 << "  \"pc_aci_transport_coupling\": \"analytic source-relative event geometry\",\n"
                 << "  \"pc_aci_transport_key\": [\"event_position\",\"event_wind_direction\",\"candidate_position\"],\n"
                 << "  \"pc_aci_causal_prior\": \"independent_hold_on_reject\",\n"
                 << "  \"pc_aci_initial_prior_origin\": \"explicit_uniform_free_cell_design_prior\",\n"
                 << "  \"pc_aci_carrier_frame\": \"fixed_world_coordinates\",\n"
                 << "  \"pc_aci_scoring_covariance\": \"common_four_fold_delete_one_completed_block_jackknife_Omega\",\n"
                 << "  \"pc_aci_source_operator\": \"single_analytic_bounded_upwind_crosswind_dilution_profile\",\n"
                 << "  \"pc_aci_temporal_operator\": \"first_D_valid_design_window_warmup_hold_then_current_only_when_outcome_LOO_qualified\",\n"
                 << "  \"pc_aci_maturation\": \"first_D_valid_design_window_warmup_then_current_only_when_outcome_LOO_qualified_and_scores_finite\",\n"
                 << "  \"pc_aci_transport_phase\": \"not_applicable_no_forward_plume_simulation\",\n"
                 << "  \"pc_aci_observation_operator\": \"completed_block_position_time_wind_hit_concentration\",\n"
                 << "  \"pc_aci_carrier\": \"position_direction_completed_block_Hellinger_profile_geometry_only\",\n"
                 << "  \"score_transform\": \"M_metric_Hellinger_coordinates_9_component_Sellentin_Heavens_modified_t_mixture_J4\",\n"
                 << "  \"pc_aci_predictive_family\": \"covariance_marginalized_modified_t_J4_nu_J_minus_d_scale_J_minus_1_over_nu_Omega\",\n"
                 << "  \"pc_aci_covariance_marginalization\": \"working_form_using_correlated_four_fold_jackknife_replicas_not_independent_iid_samples\",\n"
                 << "  \"calibration_truth_at_inference\": false,\n"
                 << "  \"candidate_set\": \"geometry_only_persistent_free_cell_carriers\",\n"
                 << "  \"pc_aci_outcome_LOO\": \"fixed_full_basis_and_Omega_with_fold_deleted_profile_renormalization\",\n"
                 << "  \"pc_aci_design_deletion\": \"diagnostic_only_never_an_acceptance_gate\",\n"
                 << "  \"pc_aci_native_isolation\": \"causal_posterior_never_initializes_from_post_native_or_pre_native_snapshot\",\n"
                 << "  \"pc_aci_candidate_artifact_boundary\": \"runtime_p2LastEvaluatedCandidates_are_not_joined_to_context_bank_manifest\",\n"
                 << "  \"pc_aci_numeric_audit\": \"omega_eigenvalues_condition_logdet_candidate_mass_cell_mass_hashes\"\n"
                 << "}\n";
    }

    void Simulations::recordPCACIEvent(const Vector2& position, bool hit,
                                       double concentration, double threshold,
                                       double windSpeed, double windDirection,
                                       uint64_t blockId, double simTime)
    {
        if (!tadmEnabled || (pfdiMode != "pc_aci" && pfdiMode != "me_aci" && pfdiMode != "me_aci_shadow" && pfdiMode != "ec_edcl" && pfdiMode != "ec_edcl_shadow"))
            return;
        pcAciPendingEvents.push_back(PCAciEvent{
            position, hit ? 1.0 : 0.0, concentration, threshold, windSpeed, windDirection,
            blockId, simTime});
    }

    void Simulations::beginTADMUpdate(uint64_t sourceUpdateId, double simTime)
    {
        if (!tadmEnabled)
            return;
        tadmSourceUpdateId = sourceUpdateId;
        tadmSimTime = simTime;
        std::filesystem::create_directories(tadmDirectory);
        if (pfdiMode == "pc_aci" || pfdiMode == "me_aci" || pfdiMode == "me_aci_shadow" || pfdiMode == "ec_edcl" || pfdiMode == "ec_edcl_shadow")
        {
            // Freeze exactly the raw events acquired since the previous
            // source update.  Subsequent measurements accumulate in a new
            // buffer and cannot leak into this inference window.
            pcAciActiveEvents = std::move(pcAciPendingEvents);
            pcAciPendingEvents.clear();
            if ((pfdiMode == "me_aci" || pfdiMode == "me_aci_shadow") &&
                !meAciEvidenceReservoir.empty())
            {
                std::vector<PCAciEvent> accumulated = std::move(meAciEvidenceReservoir);
                accumulated.insert(accumulated.end(),
                                   std::make_move_iterator(pcAciActiveEvents.begin()),
                                   std::make_move_iterator(pcAciActiveEvents.end()));
                pcAciActiveEvents = std::move(accumulated);
            }
            pcAciAcceptedThisUpdate = false;
            pcAciIncomingNativePriorSnapshot.assign(sourceProb.data.size(), 0.0L);
            long double liveMass = 0.0L;
            size_t freeCount = 0;
            for (size_t cell = 0; cell < sourceProb.data.size(); ++cell)
            {
                if (sourceProb.occupancy[cell] != Occupancy::Free)
                    continue;
                ++freeCount;
                const double value = sourceProb.data[cell];
                if (std::isfinite(value) && value > 0.0)
                {
                    pcAciIncomingNativePriorSnapshot[cell] = static_cast<long double>(value);
                    liveMass += static_cast<long double>(value);
                }
            }
            if (liveMass > 0.0L && std::isfinite(static_cast<double>(liveMass)))
            {
                for (size_t cell = 0; cell < pcAciIncomingNativePriorSnapshot.size(); ++cell)
                    if (sourceProb.occupancy[cell] == Occupancy::Free)
                        pcAciIncomingNativePriorSnapshot[cell] /= liveMass;
            }
            else if (freeCount > 0)
            {
                const long double uniform = 1.0L / static_cast<long double>(freeCount);
                for (size_t cell = 0; cell < pcAciIncomingNativePriorSnapshot.size(); ++cell)
                    if (sourceProb.occupancy[cell] == Occupancy::Free)
                        pcAciIncomingNativePriorSnapshot[cell] = uniform;
            }
            if (!pcAciCausalStateAvailable && freeCount > 0)
            {
                // A9 starts from an explicit geometry-only design prior.  The
                // native pre-update snapshot is retained only as a shadow
                // diagnostic and is never allowed to initialize the causal
                // transport posterior.
                pcAciCausalPosteriorGrid = pcAciDesignPriorGrid;
                pcAciCausalStateAvailable = true;
                GSL_INFO("PC-ACI initialized independent causal prior from explicit uniform design grid (free_cells={})",
                         freeCount);
            }
        }
    }

    bool Simulations::applyA9TvSdTfei()
    {
        const auto start = std::chrono::steady_clock::now();
        pcAciAcceptedThisUpdate = false;

        constexpr int foldCount = 4;
        constexpr int nuisanceCount = 9;
        constexpr double epsilonKernel = 1e-9;
        constexpr double epsilonCovariance = 1e-8;
        constexpr double epsilonChannel = 1e-8;
        constexpr std::array<double, 3> spreads{0.25, 0.5, 1.0};
        constexpr std::array<double, 3> dilutions{0.0, 0.5, 1.0};

        const size_t blockCount = pcAciActiveEvents.size();
        const int candidateCount = static_cast<int>(p2LastEvaluatedCandidates.size());
        auto neutral = [&](const std::string& reason) -> bool
        {
            GSL_WARN("A9 TV-SD-TFEI abstained update {}: reason={}, blocks={}, carriers={}",
                     tadmSourceUpdateId, reason, blockCount, candidateCount);
            if (!tadmDirectory.empty())
            {
                std::filesystem::create_directories(tadmDirectory);
                std::ofstream diagnostic(tadmDirectory + "/a9_tv_sd_tfei_diagnostic.csv", std::ios::out | std::ios::app);
                if (diagnostic.tellp() == 0)
                    diagnostic << "run_uuid,source_update_id,sim_time,blocks,carriers,reason,accepted,design_warmup_seen,loo_stable,channels,lambda1,design_rank,design_condition,design_principal_angle_max_deg,projector_error,elapsed_wall_s\n";
                diagnostic << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17)
                           << tadmSimTime << ',' << blockCount << ',' << candidateCount << ','
                           << reason << ",0," << (pcAciA9DesignWarmupSeen ? 1 : 0)
                           << ",0,0,0,0,inf,0,0," << std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count() << '\n';
            }
            return true;
        };

        if (blockCount < 8 || candidateCount <= 0)
            return neutral(blockCount < 8 ? "completed_block_count_below_8" : "empty_geometry_carrier");

        // D_b: completed-block design only.  Outcomes are not read until the
        // profile/eigensystem below has been fully constructed.
        Eigen::Matrix2d directionGram = Eigen::Matrix2d::Zero();
        double maximumAngle = 0.0;
        for (size_t i = 0; i < blockCount; ++i)
        {
            const auto& event = pcAciActiveEvents[i];
            const double ux = std::cos(event.windDirection);
            const double uy = std::sin(event.windDirection);
            directionGram(0, 0) += ux * ux;
            directionGram(0, 1) += ux * uy;
            directionGram(1, 0) += ux * uy;
            directionGram(1, 1) += uy * uy;
            for (size_t j = 0; j < i; ++j)
            {
                const double delta = std::abs(std::remainder(
                    event.windDirection - pcAciActiveEvents[j].windDirection,
                    2.0 * std::acos(-1.0)));
                maximumAngle = std::max(maximumAngle, std::min(delta, 2.0 * std::acos(-1.0) - delta));
            }
        }
        directionGram /= static_cast<double>(blockCount);
        Eigen::SelfAdjointEigenSolver<Eigen::Matrix2d> directionSolver(directionGram);
        if (directionSolver.info() != Eigen::Success)
            return neutral("direction_gram_solver_failed");
        const double directionMin = directionSolver.eigenvalues()(0);
        const double directionMax = directionSolver.eigenvalues()(1);
        const double directionCondition = directionMin > epsilonChannel
            ? directionMax / directionMin : std::numeric_limits<double>::infinity();
        if (!(directionMin > epsilonChannel) || directionCondition > 100.0 ||
            maximumAngle < 20.0 * std::acos(-1.0) / 180.0)
            return neutral("visibility_rank_gate_failed");

        const double cell = std::max(static_cast<double>(measuredHitProb.metadata.cellSize), 1e-9);
        // mu[candidate][nuisance][completed_block] is the analytic Hellinger
        // transport profile.  It is constructed from D only; hit/concentration
        // are deliberately absent from this bank.
        std::vector<std::vector<std::vector<double>>> mu(
            static_cast<size_t>(candidateCount),
            std::vector<std::vector<double>>(nuisanceCount,
                                              std::vector<double>(blockCount, 0.0)));
        for (int s = 0; s < candidateCount; ++s)
        {
            const Vector2 source = p2LastEvaluatedCandidates[static_cast<size_t>(s)].point;
            for (int r = 0; r < nuisanceCount; ++r)
            {
                const double spread = spreads[static_cast<size_t>(r / 3)];
                const double dilution = dilutions[static_cast<size_t>(r % 3)];
                std::vector<double> kernel(blockCount, epsilonKernel);
                double normalizer = 0.0;
                for (size_t i = 0; i < blockCount; ++i)
                {
                    const auto& event = pcAciActiveEvents[i];
                    const double ux = std::cos(event.windDirection);
                    const double uy = std::sin(event.windDirection);
                    const double dx = static_cast<double>(event.position.x - source.x);
                    const double dy = static_cast<double>(event.position.y - source.y);
                    const double downstream = dx * ux + dy * uy;
                    const double crosswind = -dx * uy + dy * ux;
                    if (downstream > 0.0)
                    {
                        const double width = cell + spread * downstream;
                        kernel[i] = std::exp(-0.5 * (crosswind / width) * (crosswind / width)) *
                            std::pow(1.0 + downstream / cell, -dilution) + epsilonKernel;
                    }
                    normalizer += kernel[i];
                }
                if (!(normalizer > 0.0) || !std::isfinite(normalizer))
                    return neutral("analytic_profile_normalization_failed");
                for (size_t i = 0; i < blockCount; ++i)
                    mu[static_cast<size_t>(s)][static_cast<size_t>(r)][i] =
                        2.0 * std::sqrt(std::max(kernel[i] / normalizer, epsilonKernel));
            }
        }

        Eigen::MatrixXd candidateMeans(candidateCount, static_cast<int>(blockCount));
        candidateMeans.setZero();
        for (int s = 0; s < candidateCount; ++s)
            for (int r = 0; r < nuisanceCount; ++r)
                for (size_t i = 0; i < blockCount; ++i)
                    candidateMeans(s, static_cast<int>(i)) +=
                        mu[static_cast<size_t>(s)][static_cast<size_t>(r)][i] /
                        static_cast<double>(nuisanceCount);

        const Eigen::RowVectorXd sourceMean = candidateMeans.colwise().mean();
        const Eigen::MatrixXd sourceCentered = candidateMeans.rowwise() - sourceMean;
        Eigen::MatrixXd sourceCovariance =
            (sourceCentered.transpose() * sourceCentered) /
            static_cast<double>(std::max(1, candidateCount));
        sourceCovariance = 0.5 * (sourceCovariance + sourceCovariance.transpose());

        Eigen::MatrixXd transportCovariance =
            Eigen::MatrixXd::Zero(static_cast<int>(blockCount), static_cast<int>(blockCount));
        for (int s = 0; s < candidateCount; ++s)
        {
            for (int r = 0; r < nuisanceCount; ++r)
            {
                Eigen::VectorXd delta(static_cast<int>(blockCount));
                for (size_t i = 0; i < blockCount; ++i)
                    delta(static_cast<int>(i)) = mu[static_cast<size_t>(s)][static_cast<size_t>(r)][i] -
                        candidateMeans(s, static_cast<int>(i));
                transportCovariance.noalias() += delta * delta.transpose() /
                    static_cast<double>(candidateCount * nuisanceCount);
            }
        }
        const double covarianceScale = std::max(
            transportCovariance.trace() / static_cast<double>(blockCount), 1e-9);
        const double covarianceFloor = std::max(covarianceScale * epsilonCovariance, epsilonCovariance);
        transportCovariance.diagonal().array() += covarianceFloor;
        transportCovariance = 0.5 * (transportCovariance + transportCovariance.transpose());

        Eigen::GeneralizedSelfAdjointEigenSolver<Eigen::MatrixXd> solver(
            sourceCovariance, transportCovariance);
        if (solver.info() != Eigen::Success)
            return neutral("hellinger_generalized_eigensolver_failed");
        std::vector<int> eligible;
        for (int index = static_cast<int>(blockCount) - 1; index >= 0; --index)
        {
            const double lambda = solver.eigenvalues()(index);
            if (std::isfinite(lambda) && lambda > 1.0)
                eligible.push_back(index);
        }
        if (eligible.empty())
            return neutral("no_lambda_above_one");

        const int channelCount = std::min(3, static_cast<int>(eligible.size()));
        Eigen::MatrixXd channels(static_cast<int>(blockCount), channelCount);
        for (int c = 0; c < channelCount; ++c)
            channels.col(c) = solver.eigenvectors().col(eligible[static_cast<size_t>(c)]);
        // Eigen's generalized self-adjoint solver normally returns
        // M-orthonormal vectors.  Re-normalize explicitly so the metric
        // projector and channel coordinates remain auditable.
        for (int c = 0; c < channelCount; ++c)
        {
            const double norm = std::sqrt(std::max(
                channels.col(c).dot(transportCovariance * channels.col(c)), epsilonChannel));
            channels.col(c) /= norm;
        }
        const Eigen::MatrixXd metricProjector = channels * channels.transpose() * transportCovariance;
        const double projectorError = (metricProjector * metricProjector - metricProjector).norm();

        // D-validity is deliberately outcome-blind.  It depends only on the
        // completed-block geometry bank, the generalized eigensystem/metric
        // projector, and persistent carrier coverage.  R_JK, Omega, LOO and
        // all hit/concentration weights are not consulted here.
        if (!std::isfinite(projectorError))
            return neutral("design_projector_nonfinite");
        bool fullCarrierCoverage = true;
        std::vector<char> coveredCells(measuredHitProb.data.size(), 0);
        for (const auto& candidate : p2LastEvaluatedCandidates)
        {
            const auto& rect = candidate.rect;
            for (int x = rect[0]; x < rect[0] + rect[2]; ++x)
                for (int y = rect[1]; y < rect[1] + rect[3]; ++y)
                {
                    if (x < 0 || y < 0 || x >= measuredHitProb.metadata.dimensions.x || y >= measuredHitProb.metadata.dimensions.y)
                        continue;
                    const size_t cellIndex = measuredHitProb.metadata.indexOf({x, y});
                    if (measuredHitProb.occupancy[cellIndex] == Occupancy::Free)
                        coveredCells[cellIndex] = 1;
                }
        }
        for (size_t cellIndex = 0; cellIndex < coveredCells.size(); ++cellIndex)
            if (measuredHitProb.occupancy[cellIndex] == Occupancy::Free && !coveredCells[cellIndex])
                fullCarrierCoverage = false;
        if (!fullCarrierCoverage)
            return neutral("carrier_coverage_failed");
        if (!pcAciA9DesignWarmupSeen)
        {
            // The first D-valid window establishes that the design operator
            // is usable, but it contributes no outcome score and no posterior
            // update.  This flag is set before any Y/outcome computation.
            pcAciA9DesignWarmupSeen = true;
            if (!tadmDirectory.empty())
            {
                std::filesystem::create_directories(tadmDirectory);
                std::ofstream diagnostic(tadmDirectory + "/a9_tv_sd_tfei_diagnostic.csv", std::ios::out | std::ios::app);
                if (diagnostic.tellp() == 0)
                    diagnostic << "run_uuid,source_update_id,sim_time,blocks,carriers,reason,accepted,design_warmup_seen,loo_stable,channels,lambda1,design_rank,design_condition,design_principal_angle_max_deg,projector_error,elapsed_wall_s\n";
                diagnostic << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17)
                           << tadmSimTime << ',' << blockCount << ',' << candidateCount
                           << ",design_warmup_hold,0,1,0," << channelCount << ','
                           << solver.eigenvalues()(eligible.front()) << ','
                           << (directionMin > epsilonChannel ? 2 : 1) << ',' << directionCondition
                           << ",0," << projectorError << ','
                           << std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count() << '\n';
            }
            return true;
        }

        // Y_b is read only after the outcome-independent design bank,
        // C_S/C_eta, eigenbasis and metric projector have been frozen.
        std::vector<double> weights(blockCount, 0.0);
        double weightSum = 0.0;
        int positiveBlocks = 0;
        for (size_t i = 0; i < blockCount; ++i)
        {
            const auto& event = pcAciActiveEvents[i];
            const double threshold = std::max(event.threshold, 1e-12);
            weights[i] = event.hit > 0.5
                ? std::log1p(std::max(event.concentration, 0.0) / threshold)
                : 0.0;
            if (weights[i] > 0.0)
            {
                weightSum += weights[i];
                ++positiveBlocks;
            }
        }
        if (positiveBlocks < 2 || !(weightSum > 0.0) || !std::isfinite(weightSum))
            return neutral("positive_outcome_weight_gate_failed");

        Eigen::VectorXd observedQ(static_cast<int>(blockCount));
        observedQ.setZero();
        for (size_t i = 0; i < blockCount; ++i)
            observedQ(static_cast<int>(i)) = weights[i] / weightSum;
        Eigen::VectorXd observedHellinger(static_cast<int>(blockCount));
        for (size_t i = 0; i < blockCount; ++i)
            observedHellinger(static_cast<int>(i)) = 2.0 * std::sqrt(std::max(observedQ(static_cast<int>(i)), 0.0));

        std::array<Eigen::VectorXd, foldCount> looHellinger;
        Eigen::VectorXd looCenter = Eigen::VectorXd::Zero(static_cast<int>(blockCount));
        for (int fold = 0; fold < foldCount; ++fold)
        {
            double foldWeight = 0.0;
            for (size_t i = 0; i < blockCount; ++i)
                if (static_cast<int>(pcAciActiveEvents[i].blockId % foldCount) != fold)
                    foldWeight += weights[i];
            if (!(foldWeight > 0.0) || !std::isfinite(foldWeight))
                return neutral("jackknife_fold_has_no_positive_weight");
            looHellinger[static_cast<size_t>(fold)] = Eigen::VectorXd::Zero(static_cast<int>(blockCount));
            for (size_t i = 0; i < blockCount; ++i)
                if (static_cast<int>(pcAciActiveEvents[i].blockId % foldCount) != fold)
                    looHellinger[static_cast<size_t>(fold)](static_cast<int>(i)) =
                        2.0 * std::sqrt(std::max(weights[i] / foldWeight, 0.0));
            looCenter += looHellinger[static_cast<size_t>(fold)] / static_cast<double>(foldCount);
        }
        Eigen::MatrixXd jackknifeCovariance = Eigen::MatrixXd::Zero(
            static_cast<int>(blockCount), static_cast<int>(blockCount));
        for (int fold = 0; fold < foldCount; ++fold)
        {
            const Eigen::VectorXd delta = looHellinger[static_cast<size_t>(fold)] - looCenter;
            jackknifeCovariance.noalias() += delta * delta.transpose();
        }
        jackknifeCovariance *= static_cast<double>(foldCount - 1) / static_cast<double>(foldCount);
        const double xScale = std::max(jackknifeCovariance.trace() / static_cast<double>(blockCount), 1e-9);
        jackknifeCovariance.diagonal().array() += std::max(xScale * epsilonCovariance, epsilonCovariance);
        const Eigen::MatrixXd omega = channels.transpose() * transportCovariance * jackknifeCovariance *
            transportCovariance * channels + epsilonChannel * Eigen::MatrixXd::Identity(channelCount, channelCount);
        Eigen::LDLT<Eigen::MatrixXd> omegaFactor(omega);
        if (omegaFactor.info() != Eigen::Success || (omegaFactor.vectorD().array() <= 0.0).any())
            return neutral("jackknife_channel_covariance_not_positive");
        const Eigen::MatrixXd omegaInverse = omegaFactor.solve(Eigen::MatrixXd::Identity(channelCount, channelCount));
        const double omegaLogdet = omegaFactor.vectorD().array().log().sum();
        Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> omegaEigenSolver(omega);
        double omegaEigenMin = std::numeric_limits<double>::quiet_NaN();
        double omegaEigenMax = std::numeric_limits<double>::quiet_NaN();
        double omegaCondition = std::numeric_limits<double>::quiet_NaN();
        if (omegaEigenSolver.info() == Eigen::Success)
        {
            omegaEigenMin = omegaEigenSolver.eigenvalues()(0);
            omegaEigenMax = omegaEigenSolver.eigenvalues()(channelCount - 1);
            if (omegaEigenMin > 0.0)
                omegaCondition = omegaEigenMax / omegaEigenMin;
        }
        constexpr double covarianceSampleCount = 4.0;
        if (!(covarianceSampleCount > static_cast<double>(channelCount)))
            return neutral("modified_t_requires_J_gt_d");
        const Eigen::VectorXd observedChannel = channels.transpose() *
            transportCovariance * (observedHellinger - sourceMean.transpose());

        auto sameSpatialBasin = [&](size_t a, size_t b)
        {
            if (a >= p2LastEvaluatedCandidates.size() || b >= p2LastEvaluatedCandidates.size())
                return false;
            const auto& ra = p2LastEvaluatedCandidates[a].rect;
            const auto& rb = p2LastEvaluatedCandidates[b].rect;
            const double radiusA = 0.5 * std::sqrt(static_cast<double>(std::max(1, ra[2] * ra[3]))) * cell;
            const double radiusB = 0.5 * std::sqrt(static_cast<double>(std::max(1, rb[2] * rb[3]))) * cell;
            return std::hypot(static_cast<double>(p2LastEvaluatedCandidates[a].point.x - p2LastEvaluatedCandidates[b].point.x),
                              static_cast<double>(p2LastEvaluatedCandidates[a].point.y - p2LastEvaluatedCandidates[b].point.y)) <=
                radiusA + radiusB + cell;
        };
        auto scoreAt = [&](const Eigen::VectorXd& observedChannelValue, int candidate, int omittedFold) -> double
        {
            std::vector<double> components;
            components.reserve(nuisanceCount);
            for (int r = 0; r < nuisanceCount; ++r)
            {
                Eigen::VectorXd candidateProfile(static_cast<int>(blockCount));
                candidateProfile.setZero();
                double profileMass = 0.0;
                for (size_t i = 0; i < blockCount; ++i)
                    if (omittedFold < 0 || static_cast<int>(pcAciActiveEvents[i].blockId % foldCount) != omittedFold)
                        profileMass += 0.25 * mu[static_cast<size_t>(candidate)][static_cast<size_t>(r)][i] *
                            mu[static_cast<size_t>(candidate)][static_cast<size_t>(r)][i];
                if (!(profileMass > 0.0) || !std::isfinite(profileMass))
                    return -std::numeric_limits<double>::infinity();
                for (size_t i = 0; i < blockCount; ++i)
                    if (omittedFold < 0 || static_cast<int>(pcAciActiveEvents[i].blockId % foldCount) != omittedFold)
                    {
                        const double pi = 0.25 * mu[static_cast<size_t>(candidate)][static_cast<size_t>(r)][i] *
                            mu[static_cast<size_t>(candidate)][static_cast<size_t>(r)][i] / profileMass;
                        candidateProfile(static_cast<int>(i)) = 2.0 * std::sqrt(std::max(pi, epsilonKernel));
                    }
                Eigen::VectorXd candidateChannel = channels.transpose() * transportCovariance *
                    (candidateProfile - sourceMean.transpose());
                const Eigen::VectorXd residual = observedChannelValue - candidateChannel;
                const double quadratic = residual.dot(omegaInverse * residual);
                const double value = std::lgamma(covarianceSampleCount / 2.0) -
                    std::lgamma((covarianceSampleCount - static_cast<double>(channelCount)) / 2.0) -
                    0.5 * static_cast<double>(channelCount) *
                        std::log(std::acos(-1.0) * (covarianceSampleCount - 1.0)) -
                    0.5 * omegaLogdet -
                    0.5 * covarianceSampleCount *
                        std::log1p(quadratic / (covarianceSampleCount - 1.0));
                components.push_back(value);
            }
            const double maximum = *std::max_element(components.begin(), components.end());
            double sum = 0.0;
            for (const double value : components)
                sum += std::exp(value - maximum);
            return maximum + std::log(sum / static_cast<double>(components.size()));
        };

        std::vector<double> fullScores(static_cast<size_t>(candidateCount), -INFINITY);
        for (int s = 0; s < candidateCount; ++s)
            fullScores[static_cast<size_t>(s)] = scoreAt(observedChannel, s, -1);
        const size_t fullTop = static_cast<size_t>(std::distance(
            fullScores.begin(), std::max_element(fullScores.begin(), fullScores.end())));

        int looAgreement = 0;
        std::vector<std::vector<double>> looScores(static_cast<size_t>(foldCount),
                                                   std::vector<double>(static_cast<size_t>(candidateCount), -INFINITY));
        for (int fold = 0; fold < foldCount; ++fold)
        {
            const Eigen::VectorXd looObserved = channels.transpose() * transportCovariance *
                (looHellinger[static_cast<size_t>(fold)] - sourceMean.transpose());
            for (int s = 0; s < candidateCount; ++s)
                looScores[static_cast<size_t>(fold)][static_cast<size_t>(s)] = scoreAt(looObserved, s, fold);
            const size_t looTop = static_cast<size_t>(std::distance(
                looScores[static_cast<size_t>(fold)].begin(),
                std::max_element(looScores[static_cast<size_t>(fold)].begin(),
                                 looScores[static_cast<size_t>(fold)].end())));
            if (sameSpatialBasin(fullTop, looTop))
                ++looAgreement;
        }
        const bool looStable = looAgreement >= 3;

        // Outcome-independent design-deletion diagnostic.  It is recorded but
        // never enters the source score or causal posterior.
        int designRankMin = 2;
        double designConditionMax = 0.0;
        double designPrincipalAngleMaxDeg = 0.0;
        const Eigen::Vector2d fullPrincipalDirection = directionSolver.eigenvectors().col(1);
        for (int fold = 0; fold < foldCount; ++fold)
        {
            Eigen::Matrix2d gram = Eigen::Matrix2d::Zero();
            int count = 0;
            for (size_t i = 0; i < blockCount; ++i)
                if (static_cast<int>(pcAciActiveEvents[i].blockId % foldCount) != fold)
                {
                    const double ux = std::cos(pcAciActiveEvents[i].windDirection);
                    const double uy = std::sin(pcAciActiveEvents[i].windDirection);
                    gram(0, 0) += ux * ux;
                    gram(0, 1) += ux * uy;
                    gram(1, 0) += ux * uy;
                    gram(1, 1) += uy * uy;
                    ++count;
                }
            if (count > 0)
                gram /= static_cast<double>(count);
            Eigen::SelfAdjointEigenSolver<Eigen::Matrix2d> foldSolver(gram);
            if (foldSolver.info() != Eigen::Success)
            {
                designRankMin = 0;
                designConditionMax = std::numeric_limits<double>::infinity();
                continue;
            }
            const double lo = foldSolver.eigenvalues()(0);
            const double hi = foldSolver.eigenvalues()(1);
            if (!(lo > epsilonChannel))
                designRankMin = 1;
            designConditionMax = std::max(designConditionMax,
                lo > epsilonChannel ? hi / lo : std::numeric_limits<double>::infinity());
            const Eigen::Vector2d foldPrincipalDirection = foldSolver.eigenvectors().col(1);
            const double cosine = std::min(1.0, std::max(0.0,
                std::abs(fullPrincipalDirection.dot(foldPrincipalDirection))));
            designPrincipalAngleMaxDeg = std::max(designPrincipalAngleMaxDeg,
                std::acos(cosine) * 180.0 / std::acos(-1.0));
        }

        const bool finiteFullScores = std::all_of(fullScores.begin(), fullScores.end(),
                                                  [](double value) { return std::isfinite(value); });
        const bool qualified = looStable && finiteFullScores;
        std::vector<double> posteriorScores = fullScores;
        bool accepted = qualified;
        std::string rejectReason;
        std::vector<long double> candidateMassAudit(static_cast<size_t>(candidateCount), 0.0L);
        std::vector<long double> posteriorMassAudit(static_cast<size_t>(candidateCount), 0.0L);
        std::vector<int> freeCountAudit(static_cast<size_t>(candidateCount), 0);
        long double cellPosteriorMassAudit = 0.0L;
        if (!qualified)
        {
            if (!looStable) rejectReason = "outcome_block_loo_unstable";
            else if (!finiteFullScores) rejectReason = "full_score_nonfinite";
            else rejectReason = "qualification_failed";
        }

        if (accepted && !pcAciCausalStateAvailable)
        {
            pcAciCausalPosteriorGrid = pcAciDesignPriorGrid;
            pcAciCausalStateAvailable = true;
        }
        if (accepted)
        {
            long double priorTotal = 0.0L;
            for (size_t cellIndex = 0; cellIndex < pcAciCausalPosteriorGrid.size(); ++cellIndex)
                if (measuredHitProb.occupancy[cellIndex] == Occupancy::Free)
                    priorTotal += std::max(pcAciCausalPosteriorGrid[cellIndex], 0.0L);
            if (!(priorTotal > 0.0L))
            {
                accepted = false;
                rejectReason = "causal_prior_zero_mass";
            }
            else
            {
                long double maxLog = -INFINITY;
                for (int s = 0; s < candidateCount; ++s)
                {
                    const auto& rect = p2LastEvaluatedCandidates[static_cast<size_t>(s)].rect;
                    for (int x = rect[0]; x < rect[0] + rect[2]; ++x)
                        for (int y = rect[1]; y < rect[1] + rect[3]; ++y)
                        {
                            if (x < 0 || y < 0 || x >= measuredHitProb.metadata.dimensions.x || y >= measuredHitProb.metadata.dimensions.y)
                                continue;
                            const size_t cellIndex = measuredHitProb.metadata.indexOf({x, y});
                            if (measuredHitProb.occupancy[cellIndex] != Occupancy::Free)
                                continue;
                            candidateMassAudit[static_cast<size_t>(s)] += std::max(pcAciCausalPosteriorGrid[cellIndex], 0.0L);
                            ++freeCountAudit[static_cast<size_t>(s)];
                        }
                    if (freeCountAudit[static_cast<size_t>(s)] <= 0 || !std::isfinite(fullScores[static_cast<size_t>(s)]))
                    {
                        accepted = false;
                        rejectReason = "candidate_coverage_or_score_invalid";
                        break;
                    }
                    if (!(candidateMassAudit[static_cast<size_t>(s)] > 0.0L) ||
                        !std::isfinite(static_cast<double>(candidateMassAudit[static_cast<size_t>(s)])))
                    {
                        accepted = false;
                        rejectReason = "candidate_prior_mass_nonpositive";
                        break;
                    }
                    maxLog = std::max(maxLog, std::log(candidateMassAudit[static_cast<size_t>(s)]) +
                        static_cast<long double>(posteriorScores[static_cast<size_t>(s)]));
                }
                if (accepted)
                {
                    long double total = 0.0L;
                    for (int s = 0; s < candidateCount; ++s)
                    {
                        posteriorMassAudit[static_cast<size_t>(s)] = std::exp(
                            std::log(candidateMassAudit[static_cast<size_t>(s)]) +
                            static_cast<long double>(posteriorScores[static_cast<size_t>(s)]) - maxLog);
                        total += posteriorMassAudit[static_cast<size_t>(s)];
                    }
                    if (!(total > 0.0L) || !std::isfinite(static_cast<double>(total)))
                    {
                        accepted = false;
                        rejectReason = "joint_bayes_factor_normalization_failed";
                    }
                    else
                    {
                        for (long double& value : posteriorMassAudit)
                            value /= total;
                        std::vector<int> bestArea(sourceProbInternal.size(), std::numeric_limits<int>::max());
                        std::vector<long double> cellPosterior(sourceProbInternal.size(), 0.0L);
                        size_t covered = 0;
                        for (int s = 0; s < candidateCount; ++s)
                        {
                            const auto& rect = p2LastEvaluatedCandidates[static_cast<size_t>(s)].rect;
                            const int area = rect[2] * rect[3];
                            const long double density = posteriorMassAudit[static_cast<size_t>(s)] /
                                static_cast<long double>(freeCountAudit[static_cast<size_t>(s)]);
                            for (int x = rect[0]; x < rect[0] + rect[2]; ++x)
                                for (int y = rect[1]; y < rect[1] + rect[3]; ++y)
                                {
                                    if (x < 0 || y < 0 || x >= measuredHitProb.metadata.dimensions.x || y >= measuredHitProb.metadata.dimensions.y)
                                        continue;
                                    const size_t cellIndex = measuredHitProb.metadata.indexOf({x, y});
                                    if (measuredHitProb.occupancy[cellIndex] != Occupancy::Free)
                                        continue;
                                    if (area <= bestArea[cellIndex])
                                    {
                                        if (bestArea[cellIndex] == std::numeric_limits<int>::max())
                                            ++covered;
                                        bestArea[cellIndex] = area;
                                        cellPosterior[cellIndex] = density;
                                    }
                                }
                        }
                        cellPosteriorMassAudit = 0.0L;
                        for (size_t cellIndex = 0; cellIndex < cellPosterior.size(); ++cellIndex)
                            if (measuredHitProb.occupancy[cellIndex] == Occupancy::Free)
                                cellPosteriorMassAudit += cellPosterior[cellIndex];
                        if (covered != measuredHitProb.metadata.numFreeCells)
                        {
                            accepted = false;
                            rejectReason = "candidate_rectangles_do_not_cover_free_grid";
                        }
                        else
                        {
                            for (size_t cellIndex = 0; cellIndex < sourceProbInternal.size(); ++cellIndex)
                                if (measuredHitProb.occupancy[cellIndex] == Occupancy::Free)
                                    sourceProbInternal[cellIndex] = cellPosterior[cellIndex];
                            pcAciAcceptedThisUpdate = true;
                            pcAciCausalPosteriorGrid = sourceProbInternal;
                            pcAciCausalStateAvailable = true;
                            pcAciLastAcceptedUpdateId = tadmSourceUpdateId;
                            rejectReason = "accepted";
                        }
                    }
                }
            }
        }

        if (!accepted && rejectReason.empty())
            rejectReason = "gate_rejected";
        GSL_INFO("A9 TV-SD-TFEI update {}: blocks={}, carriers={}, channels={}, lambda1={:.6f}, loo={}/{}, design_rank={}, design_condition={:.6g}, design_principal_angle_max_deg={:.3f}, projector_error={:.3g}, accepted={}, reason={}",
                 tadmSourceUpdateId, blockCount, candidateCount, channelCount,
                 solver.eigenvalues()(eligible.front()), looAgreement, foldCount,
                 designRankMin, designConditionMax, designPrincipalAngleMaxDeg,
                 projectorError, accepted, rejectReason);

        if (!tadmDirectory.empty())
        {
            std::filesystem::create_directories(tadmDirectory);
            const std::string tag = fmt::format("{:04d}", tadmSourceUpdateId);
            std::ofstream scores(tadmDirectory + "/a9_tv_sd_tfei_scores_" + tag + ".csv", std::ios::out | std::ios::trunc);
            scores << "run_uuid,source_update_id,sim_time,candidate_id,x,y,full_log_score,joint_log_score";
            for (int fold = 0; fold < foldCount; ++fold)
                scores << ",loo_fold_" << fold;
            scores << "\n";
            for (int s = 0; s < candidateCount; ++s)
            {
                const auto& candidate = p2LastEvaluatedCandidates[static_cast<size_t>(s)];
                scores << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17)
                       << tadmSimTime << ',' << candidate.stableID << ',' << candidate.point.x << ','
                       << candidate.point.y << ',' << fullScores[static_cast<size_t>(s)] << ','
                       << posteriorScores[static_cast<size_t>(s)];
                for (int fold = 0; fold < foldCount; ++fold)
                    scores << ',' << looScores[static_cast<size_t>(fold)][static_cast<size_t>(s)];
                scores << '\n';
            }
            scores.flush();
            if (qualified || accepted)
            {
                const auto fnv1a64 = [](const std::string& value) -> uint64_t
                {
                    uint64_t hash = 1469598103934665603ULL;
                    for (const unsigned char byte : value)
                    {
                        hash ^= static_cast<uint64_t>(byte);
                        hash *= 1099511628211ULL;
                    }
                    return hash;
                };
                const auto hex64 = [](uint64_t value) -> std::string
                {
                    std::ostringstream stream;
                    stream << std::hex << std::setw(16) << std::setfill('0') << value;
                    return stream.str();
                };
                std::ostringstream candidateIdInput;
                std::ostringstream scoreInput;
                candidateIdInput << std::setprecision(17);
                scoreInput << std::setprecision(17);
                for (int s = 0; s < candidateCount; ++s)
                {
                    const auto& candidate = p2LastEvaluatedCandidates[static_cast<size_t>(s)];
                    candidateIdInput << candidate.stableID << '\n';
                    scoreInput << candidate.stableID << ',' << fullScores[static_cast<size_t>(s)] << ','
                               << posteriorScores[static_cast<size_t>(s)] << '\n';
                }
                const std::string candidateIdHash = hex64(fnv1a64(candidateIdInput.str()));
                const std::string scoreHash = hex64(fnv1a64(scoreInput.str()));
                long double candidateMassSum = 0.0L;
                long double candidatePosteriorSum = 0.0L;
                for (int s = 0; s < candidateCount; ++s)
                {
                    candidateMassSum += candidateMassAudit[static_cast<size_t>(s)];
                    candidatePosteriorSum += posteriorMassAudit[static_cast<size_t>(s)];
                }
                const double omegaEigenMiddle = channelCount > 1 && omegaEigenSolver.info() == Eigen::Success
                    ? omegaEigenSolver.eigenvalues()(1) : std::numeric_limits<double>::quiet_NaN();
                const size_t auditTop = fullTop < static_cast<size_t>(candidateCount)
                    ? fullTop : 0;
                const auto& auditTopCandidate = p2LastEvaluatedCandidates[auditTop];
                const std::string summaryPath = tadmDirectory + "/a9_tv_sd_tfei_numeric_audit_" + tag + ".csv";
                std::ofstream summary(summaryPath, std::ios::out | std::ios::trunc);
                summary << "run_uuid,source_update_id,sim_time,blocks,carriers,accepted,qualified,loo_stable,channels,omega_eigen_min,omega_eigen_middle,omega_eigen_max,omega_condition,omega_logdet,candidate_prior_mass_sum,candidate_posterior_mass_sum,cell_posterior_mass,cell_mass_residual,top_candidate_id,top_candidate_prior_mass,top_candidate_posterior_mass,top_candidate_free_count,candidate_id_hash,score_hash,runtime_candidate_set_note\n";
                summary << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17)
                        << tadmSimTime << ',' << blockCount << ',' << candidateCount << ','
                        << (accepted ? 1 : 0) << ',' << (qualified ? 1 : 0) << ',' << (looStable ? 1 : 0)
                        << ',' << channelCount << ',' << omegaEigenMin << ',' << omegaEigenMiddle << ','
                        << omegaEigenMax << ',' << omegaCondition << ',' << omegaLogdet << ','
                        << candidateMassSum << ',' << candidatePosteriorSum << ',' << cellPosteriorMassAudit << ','
                        << (cellPosteriorMassAudit - 1.0L) << ',' << auditTopCandidate.stableID << ','
                        << candidateMassAudit[auditTop] << ',' << posteriorMassAudit[auditTop] << ','
                        << freeCountAudit[auditTop] << ',' << candidateIdHash << ',' << scoreHash
                        << ",p2LastEvaluatedCandidates_not_context_bank_manifest\n";
                summary.flush();

                const std::string candidateAuditPath = tadmDirectory + "/a9_tv_sd_tfei_candidate_mass_" + tag + ".csv";
                std::ofstream candidateAudit(candidateAuditPath, std::ios::out | std::ios::trunc);
                candidateAudit << "run_uuid,source_update_id,candidate_id,free_count,candidate_prior_mass,candidate_posterior_mass,full_log_score,joint_log_score,candidate_id_hash,score_hash\n";
                for (int s = 0; s < candidateCount; ++s)
                {
                    const auto& candidate = p2LastEvaluatedCandidates[static_cast<size_t>(s)];
                    candidateAudit << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << candidate.stableID << ','
                                   << freeCountAudit[static_cast<size_t>(s)] << ',' << std::setprecision(17)
                                   << candidateMassAudit[static_cast<size_t>(s)] << ','
                                   << posteriorMassAudit[static_cast<size_t>(s)] << ','
                                   << fullScores[static_cast<size_t>(s)] << ','
                                   << posteriorScores[static_cast<size_t>(s)] << ','
                                   << candidateIdHash << ',' << scoreHash << '\n';
                }
                candidateAudit.flush();
            }
            std::ofstream diagnostic(tadmDirectory + "/a9_tv_sd_tfei_diagnostic.csv", std::ios::out | std::ios::app);
            if (diagnostic.tellp() == 0)
                diagnostic << "run_uuid,source_update_id,sim_time,blocks,carriers,reason,accepted,design_warmup_seen,loo_stable,channels,lambda1,design_rank,design_condition,design_principal_angle_max_deg,projector_error,elapsed_wall_s\n";
            diagnostic << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17)
                       << tadmSimTime << ',' << blockCount << ',' << candidateCount << ',' << rejectReason << ','
                       << (accepted ? 1 : 0) << ',' << (pcAciA9DesignWarmupSeen ? 1 : 0) << ','
                       << (looStable ? 1 : 0) << ',' << channelCount << ','
                       << solver.eigenvalues()(eligible.front()) << ',' << designRankMin << ','
                       << designConditionMax << ',' << designPrincipalAngleMaxDeg << ','
                       << projectorError << ','
                       << std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count() << '\n';
            diagnostic.flush();
        }
        return true;
    }

    bool Simulations::applyEnsembleEcEdcl()
    {
        // Ensemble-Calibrated Eigenchannel / Exact Conditional Dependence
        // Ledger.  This path is deliberately independent of native PMFS
        // posterior ordering: native PMFS is retained only as a same-window
        // shadow comparator and, in ec_edcl mode, as the planner shell whose
        // source posterior is replaced after all mathematical audits pass.
        constexpr int calibrationReplicas = 4;
        constexpr int scoringReplicas = 4;
        constexpr int totalReplicas = calibrationReplicas + scoringReplicas;
        constexpr double responseFloor = 0.5 / 201.0;
        constexpr double covarianceRidge = 1e-10;
        const bool inject = pfdiMode == "ec_edcl";
        const int sourceCount = static_cast<int>(p2LastEvaluatedCandidates.size());
        const int eventCount = static_cast<int>(pcAciActiveEvents.size());
        if (sourceCount <= 0 || tadmReplicas != calibrationReplicas)
        {
            GSL_ERROR("EC-ECDL requires persistent carriers and exactly four calibration/scoring replicas; carriers={}, configured_replicas={}",
                      sourceCount, tadmReplicas);
            return false;
        }

        int positiveEvents = 0;
        std::vector<double> observedWeights(static_cast<size_t>(eventCount), 0.0);
        for (int i = 0; i < eventCount; ++i)
        {
            const PCAciEvent& event = pcAciActiveEvents[static_cast<size_t>(i)];
            if (event.hit <= 0.5)
                continue;
            ++positiveEvents;
            observedWeights[static_cast<size_t>(i)] = std::log1p(
                std::max(event.concentration, 0.0) /
                std::max(event.threshold, std::numeric_limits<double>::epsilon()));
        }
        const double observedWeightSum = std::accumulate(
            observedWeights.begin(), observedWeights.end(), 0.0);
        if (eventCount <= 0 || positiveEvents < 2 || !(observedWeightSum > 0.0))
        {
            if (!tadmDirectory.empty())
            {
                std::ofstream summary(tadmDirectory + "/ec_edcl_update_summary.csv", std::ios::out | std::ios::app);
                if (summary.tellp() == 0)
                    summary << "run_uuid,source_update_id,sim_time,status,inject,event_count,positive_events,source_count,channel_count,leading_lambda,k_dim,k_min_eigen,k_condition,projectivity_max_abs,online_batch_max_abs,online_batch_max_rel\n";
                summary << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17)
                        << tadmSimTime << ",ABSTAIN_OUTCOME," << (inject ? 1 : 0) << ','
                        << eventCount << ',' << positiveEvents << ',' << sourceCount
                        << ",0,nan,0,nan,nan,nan,nan,nan\n";
            }
            GSL_WARN("EC-ECDL abstained update {}: completed_events={}, positive_events={}",
                     tadmSourceUpdateId, eventCount, positiveEvents);
            return true;
        }

        // Validate the geometry-only carrier partition and record the native
        // same-window posterior before any possible EC-ECDL injection.
        std::vector<int> freeCellsPerSource(static_cast<size_t>(sourceCount), 0);
        std::vector<int> coverage(measuredHitProb.data.size(), 0);
        int totalFreeCells = 0;
        long double nativeTotal = 0.0L;
        std::vector<long double> nativeCarrierMass(static_cast<size_t>(sourceCount), 0.0L);
        for (size_t cell = 0; cell < measuredHitProb.data.size(); ++cell)
            if (measuredHitProb.occupancy[cell] == Occupancy::Free)
            {
                ++totalFreeCells;
                nativeTotal += std::max(sourceProbInternal[cell], 0.0L);
            }
        for (int s = 0; s < sourceCount; ++s)
        {
            const auto& rect = p2LastEvaluatedCandidates[static_cast<size_t>(s)].rect;
            for (int x = rect[0]; x < rect[0] + rect[2]; ++x)
                for (int y = rect[1]; y < rect[1] + rect[3]; ++y)
                {
                    const Vector2Int index{x, y};
                    if (!measuredHitProb.metadata.indicesInBounds(index))
                        continue;
                    const size_t cell = measuredHitProb.metadata.indexOf(index);
                    if (measuredHitProb.occupancy[cell] != Occupancy::Free)
                        continue;
                    ++coverage[cell];
                    ++freeCellsPerSource[static_cast<size_t>(s)];
                    nativeCarrierMass[static_cast<size_t>(s)] += std::max(sourceProbInternal[cell], 0.0L);
                }
        }
        for (size_t cell = 0; cell < coverage.size(); ++cell)
            if (measuredHitProb.occupancy[cell] == Occupancy::Free && coverage[cell] != 1)
            {
                GSL_ERROR("EC-ECDL persistent carrier coverage invalid at cell {}: multiplicity={}", cell, coverage[cell]);
                return false;
            }
        if (totalFreeCells <= 0 || nativeTotal <= 0.0L)
        {
            GSL_ERROR("EC-ECDL has no free geometry or finite native shadow mass");
            return false;
        }
        for (long double& value : nativeCarrierMass)
            value /= nativeTotal;

        // Outcome-blind physical bank.  A replica id fixes the exogenous
        // transport member across every candidate and source-update; source id
        // is intentionally absent from EventKey.
        std::vector<std::vector<std::vector<double>>> responses(
            static_cast<size_t>(sourceCount),
            std::vector<std::vector<double>>(static_cast<size_t>(totalReplicas),
                                             std::vector<double>(static_cast<size_t>(eventCount), responseFloor)));
        std::vector<std::vector<std::vector<double>>> rawProbabilities = responses;
        const auto physicalStart = std::chrono::steady_clock::now();
#pragma omp parallel for schedule(dynamic)
        for (int s = 0; s < sourceCount; ++s)
        {
            const auto& candidate = p2LastEvaluatedCandidates[static_cast<size_t>(s)];
            for (int replica = 0; replica < totalReplicas; ++replica)
            {
                const EventKey key{tadmGlobalSeed, 0ULL, static_cast<uint64_t>(replica), tadmTransportSubstream};
                EventKeyedTransportRng transportRng(key);
                std::vector<float> hitMap(measuredHitProb.data.size(), 0.0f);
                simulateSourceInPosition(SimulationSource(candidate.point, measuredHitProb.metadata), hitMap, true,
                                         settings.iterationsToRecord, settings.deltaTime, settings.noiseSTDev,
                                         nullptr, &transportRng);
                if (settings.blurSigmaX > 0 || settings.blurSigmaY > 0)
                {
                    cv::Mat asImage(hitMap);
                    asImage = asImage.reshape(1, measuredHitProb.metadata.dimensions.y);
                    blurHitMap(asImage);
                }
                double probabilitySum = 0.0;
                for (int i = 0; i < eventCount; ++i)
                {
                    const Vector2Int eventIndex = measuredHitProb.metadata.coordinatesToIndices(
                        pcAciActiveEvents[static_cast<size_t>(i)].position.x,
                        pcAciActiveEvents[static_cast<size_t>(i)].position.y);
                    double probability = responseFloor;
                    if (measuredHitProb.metadata.indicesInBounds(eventIndex))
                    {
                        const size_t cell = measuredHitProb.metadata.indexOf(eventIndex);
                        if (measuredHitProb.occupancy[cell] == Occupancy::Free)
                            probability = static_cast<double>(hitMap[cell]);
                    }
                    probability = std::clamp(probability, responseFloor, 1.0 - responseFloor);
                    rawProbabilities[static_cast<size_t>(s)][static_cast<size_t>(replica)][static_cast<size_t>(i)] = probability;
                    responses[static_cast<size_t>(s)][static_cast<size_t>(replica)][static_cast<size_t>(i)] = probability;
                    probabilitySum += probability + responseFloor;
                }
                if (!(probabilitySum > 0.0) || !std::isfinite(probabilitySum))
                    continue;
                for (int i = 0; i < eventCount; ++i)
                {
                    const double probability = responses[static_cast<size_t>(s)][static_cast<size_t>(replica)][static_cast<size_t>(i)];
                    responses[static_cast<size_t>(s)][static_cast<size_t>(replica)][static_cast<size_t>(i)] =
                        2.0 * std::sqrt((probability + responseFloor) / probabilitySum);
                }
            }
        }
        const double physicalWallSeconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - physicalStart).count();

        Eigen::VectorXd observed(eventCount);
        for (int i = 0; i < eventCount; ++i)
            observed(i) = 2.0 * std::sqrt(observedWeights[static_cast<size_t>(i)] / observedWeightSum);

        Eigen::MatrixXd calibrationMeans(sourceCount, eventCount);
        calibrationMeans.setZero();
        for (int s = 0; s < sourceCount; ++s)
            for (int k = 0; k < calibrationReplicas; ++k)
                for (int i = 0; i < eventCount; ++i)
                    calibrationMeans(s, i) += responses[static_cast<size_t>(s)][static_cast<size_t>(k)][static_cast<size_t>(i)] /
                        static_cast<double>(calibrationReplicas);
        const Eigen::RowVectorXd grandMean = calibrationMeans.colwise().mean();
        const Eigen::MatrixXd sourceCentered = calibrationMeans.rowwise() - grandMean;
        Eigen::MatrixXd sourceCovariance = sourceCentered.transpose() * sourceCentered /
            static_cast<double>(std::max(1, sourceCount - 1));
        Eigen::MatrixXd transportCovariance = Eigen::MatrixXd::Zero(eventCount, eventCount);
        for (int s = 0; s < sourceCount; ++s)
            for (int k = 0; k < calibrationReplicas; ++k)
            {
                Eigen::VectorXd deviation(eventCount);
                for (int i = 0; i < eventCount; ++i)
                    deviation(i) = responses[static_cast<size_t>(s)][static_cast<size_t>(k)][static_cast<size_t>(i)] -
                        calibrationMeans(s, i);
                transportCovariance.noalias() += deviation * deviation.transpose();
            }
        // This is a source-average of within-source sample covariances, not
        // S*J independent pseudo-replicates.  Common random numbers couple
        // sources but do not change this deterministic source-average target.
        transportCovariance /= static_cast<double>(sourceCount * (calibrationReplicas - 1));
        transportCovariance = 0.5 * (transportCovariance + transportCovariance.transpose());
        transportCovariance.diagonal().array() += covarianceRidge;
        sourceCovariance = 0.5 * (sourceCovariance + sourceCovariance.transpose());

        Eigen::GeneralizedSelfAdjointEigenSolver<Eigen::MatrixXd> solver(
            sourceCovariance, transportCovariance);
        if (solver.info() != Eigen::Success)
        {
            GSL_ERROR("EC-ECDL generalized eigenproblem failed");
            return false;
        }
        std::vector<int> selected;
        for (int i = eventCount - 1; i >= 0 && static_cast<int>(selected.size()) < 3; --i)
            if (std::isfinite(solver.eigenvalues()(i)) && solver.eigenvalues()(i) > 1.0)
                selected.push_back(i);
        if (selected.empty())
        {
            GSL_WARN("EC-ECDL abstained update {}: no source-informative physical eigenchannel, leading_lambda={}",
                     tadmSourceUpdateId, solver.eigenvalues()(eventCount - 1));
            return true;
        }
        const int channelCount = static_cast<int>(selected.size());
        Eigen::MatrixXd eigenvectors(eventCount, channelCount);
        for (int d = 0; d < channelCount; ++d)
            eigenvectors.col(d) = solver.eigenvectors().col(selected[static_cast<size_t>(d)]);
        const Eigen::MatrixXd projection = eigenvectors.transpose() * transportCovariance;
        const Eigen::VectorXd projectedObserved = projection * (observed - grandMean.transpose());

        std::vector<std::string> carrierIds;
        carrierIds.reserve(static_cast<size_t>(sourceCount));
        for (const auto& row : p2LastEvaluatedCandidates)
            carrierIds.push_back(row.stableID);
        if (ecEdclHistoryValid && carrierIds != ecEdclCarrierIds)
        {
            GSL_ERROR("EC-ECDL persistent carrier identity changed across source updates");
            return false;
        }

        const int oldDimension = std::accumulate(
            ecEdclBlockDimensions.begin(), ecEdclBlockDimensions.end(), 0);
        const int newDimension = oldDimension + channelCount;
        std::vector<std::vector<double>> calibrationHistory = ecEdclCalibrationHistory;
        std::vector<std::vector<double>> residualHistory = ecEdclScoringResidualHistory;
        std::vector<double> cumulativeScores = ecEdclCumulativeMemberScores;
        if (!ecEdclHistoryValid)
        {
            calibrationHistory.assign(static_cast<size_t>(sourceCount * calibrationReplicas), {});
            residualHistory.assign(static_cast<size_t>(sourceCount * scoringReplicas), {});
            cumulativeScores.assign(static_cast<size_t>(sourceCount * scoringReplicas), 0.0);
        }
        if (calibrationHistory.size() != static_cast<size_t>(sourceCount * calibrationReplicas) ||
            residualHistory.size() != static_cast<size_t>(sourceCount * scoringReplicas) ||
            cumulativeScores.size() != static_cast<size_t>(sourceCount * scoringReplicas))
        {
            GSL_ERROR("EC-ECDL history shape mismatch");
            return false;
        }

        for (int s = 0; s < sourceCount; ++s)
        {
            for (int k = 0; k < calibrationReplicas; ++k)
            {
                Eigen::VectorXd response(eventCount);
                for (int i = 0; i < eventCount; ++i)
                    response(i) = responses[static_cast<size_t>(s)][static_cast<size_t>(k)][static_cast<size_t>(i)] -
                        calibrationMeans(s, i);
                const Eigen::VectorXd projected = projection * response;
                auto& history = calibrationHistory[static_cast<size_t>(s * calibrationReplicas + k)];
                history.insert(history.end(), projected.data(), projected.data() + channelCount);
            }
            for (int m = 0; m < scoringReplicas; ++m)
            {
                Eigen::VectorXd response(eventCount);
                for (int i = 0; i < eventCount; ++i)
                    response(i) = responses[static_cast<size_t>(s)][static_cast<size_t>(calibrationReplicas + m)][static_cast<size_t>(i)] -
                        grandMean(i);
                const Eigen::VectorXd residual = projectedObserved - projection * response;
                auto& history = residualHistory[static_cast<size_t>(s * scoringReplicas + m)];
                history.insert(history.end(), residual.data(), residual.data() + channelCount);
            }
        }

        Eigen::MatrixXd historyCovariance = Eigen::MatrixXd::Zero(newDimension, newDimension);
        for (const auto& row : calibrationHistory)
        {
            if (static_cast<int>(row.size()) != newDimension)
            {
                GSL_ERROR("EC-ECDL calibration history coordinate mismatch");
                return false;
            }
            const Eigen::Map<const Eigen::VectorXd> value(row.data(), newDimension);
            historyCovariance.noalias() += value * value.transpose();
        }
        historyCovariance /= static_cast<double>(sourceCount * (calibrationReplicas - 1));
        historyCovariance = 0.5 * (historyCovariance + historyCovariance.transpose());
        // A single frozen absolute ridge preserves exact principal blocks.
        historyCovariance.diagonal().array() += covarianceRidge;
        double projectivityMaxAbs = 0.0;
        if (ecEdclHistoryValid)
        {
            if (ecEdclPreviousCovarianceDim != oldDimension ||
                ecEdclPreviousCovariance.size() != static_cast<size_t>(oldDimension * oldDimension))
            {
                GSL_ERROR("EC-ECDL previous covariance audit shape mismatch");
                return false;
            }
            for (int i = 0; i < oldDimension; ++i)
                for (int j = 0; j < oldDimension; ++j)
                    projectivityMaxAbs = std::max(projectivityMaxAbs, std::abs(
                        historyCovariance(i, j) -
                        ecEdclPreviousCovariance[static_cast<size_t>(i * oldDimension + j)]));
            if (projectivityMaxAbs > 1e-9)
            {
                GSL_ERROR("EC-ECDL projectivity audit failed: max_abs={}", projectivityMaxAbs);
                return false;
            }
        }
        Eigen::LLT<Eigen::MatrixXd> historyFactor(historyCovariance);
        if (historyFactor.info() != Eigen::Success)
        {
            GSL_ERROR("EC-ECDL history covariance is not SPD");
            return false;
        }
        Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> covarianceSpectrum(historyCovariance);
        if (covarianceSpectrum.info() != Eigen::Success || covarianceSpectrum.eigenvalues()(0) <= 0.0)
        {
            GSL_ERROR("EC-ECDL history covariance spectrum invalid");
            return false;
        }
        const double kMinEigen = covarianceSpectrum.eigenvalues()(0);
        const double kCondition = covarianceSpectrum.eigenvalues()(newDimension - 1) / kMinEigen;

        Eigen::MatrixXd conditionalCovariance;
        Eigen::MatrixXd historyToCurrent;
        Eigen::LLT<Eigen::MatrixXd> oldFactor;
        if (oldDimension == 0)
            conditionalCovariance = historyCovariance;
        else
        {
            const Eigen::MatrixXd oldCovariance = historyCovariance.topLeftCorner(oldDimension, oldDimension);
            const Eigen::MatrixXd crossCovariance = historyCovariance.topRightCorner(oldDimension, channelCount);
            oldFactor.compute(oldCovariance);
            if (oldFactor.info() != Eigen::Success)
            {
                GSL_ERROR("EC-ECDL historical principal block is not SPD");
                return false;
            }
            historyToCurrent = oldFactor.solve(crossCovariance);
            conditionalCovariance = historyCovariance.bottomRightCorner(channelCount, channelCount) -
                crossCovariance.transpose() * historyToCurrent;
            conditionalCovariance = 0.5 * (conditionalCovariance + conditionalCovariance.transpose());
        }
        Eigen::LLT<Eigen::MatrixXd> conditionalFactor(conditionalCovariance);
        if (conditionalFactor.info() != Eigen::Success)
        {
            GSL_ERROR("EC-ECDL Schur conditional covariance is not SPD");
            return false;
        }
        const double conditionalLogdet = 2.0 * conditionalFactor.matrixL().toDenseMatrix().diagonal().array().log().sum();
        const double fullLogdet = 2.0 * historyFactor.matrixL().toDenseMatrix().diagonal().array().log().sum();
        double maxExactAbs = 0.0;
        double maxExactRel = 0.0;
        std::vector<double> robustMin(static_cast<size_t>(sourceCount), std::numeric_limits<double>::infinity());
        std::vector<double> robustMax(static_cast<size_t>(sourceCount), -std::numeric_limits<double>::infinity());
        for (int s = 0; s < sourceCount; ++s)
            for (int m = 0; m < scoringReplicas; ++m)
            {
                const size_t member = static_cast<size_t>(s * scoringReplicas + m);
                const auto& history = residualHistory[member];
                if (static_cast<int>(history.size()) != newDimension)
                {
                    GSL_ERROR("EC-ECDL scoring history coordinate mismatch");
                    return false;
                }
                const Eigen::Map<const Eigen::VectorXd> fullResidual(history.data(), newDimension);
                Eigen::VectorXd conditionalResidual = fullResidual.tail(channelCount);
                if (oldDimension > 0)
                    conditionalResidual -= historyToCurrent.transpose() * fullResidual.head(oldDimension);
                const Eigen::VectorXd conditionalSolved = conditionalFactor.solve(conditionalResidual);
                const double increment = -0.5 *
                    (conditionalResidual.dot(conditionalSolved) + conditionalLogdet);
                cumulativeScores[member] += increment;
                const Eigen::VectorXd fullSolved = historyFactor.solve(fullResidual);
                const double batch = -0.5 * (fullResidual.dot(fullSolved) + fullLogdet);
                const double absolute = std::abs(cumulativeScores[member] - batch);
                const double relative = absolute / (1.0 + std::abs(batch));
                maxExactAbs = std::max(maxExactAbs, absolute);
                maxExactRel = std::max(maxExactRel, relative);
                robustMin[static_cast<size_t>(s)] = std::min(robustMin[static_cast<size_t>(s)], cumulativeScores[member]);
                robustMax[static_cast<size_t>(s)] = std::max(robustMax[static_cast<size_t>(s)], cumulativeScores[member]);
            }
        if (maxExactRel > 1e-8)
        {
            GSL_ERROR("EC-ECDL online=batch audit failed: max_abs={}, max_rel={}", maxExactAbs, maxExactRel);
            return false;
        }

        std::vector<double> marginalized(static_cast<size_t>(sourceCount), -INFINITY);
        std::vector<double> bernoulliMarginalized(static_cast<size_t>(sourceCount), -INFINITY);
        for (int s = 0; s < sourceCount; ++s)
        {
            double maximum = -INFINITY;
            for (int m = 0; m < scoringReplicas; ++m)
                maximum = std::max(maximum, cumulativeScores[static_cast<size_t>(s * scoringReplicas + m)]);
            double sum = 0.0;
            for (int m = 0; m < scoringReplicas; ++m)
                sum += std::exp(cumulativeScores[static_cast<size_t>(s * scoringReplicas + m)] - maximum);
            marginalized[static_cast<size_t>(s)] = maximum + std::log(sum / static_cast<double>(scoringReplicas));

            std::array<double, scoringReplicas> bernoulliScores{};
            double bernoulliMaximum = -INFINITY;
            for (int m = 0; m < scoringReplicas; ++m)
            {
                double value = 0.0;
                for (int i = 0; i < eventCount; ++i)
                {
                    const double probability = rawProbabilities[static_cast<size_t>(s)]
                        [static_cast<size_t>(calibrationReplicas + m)][static_cast<size_t>(i)];
                    const bool hit = pcAciActiveEvents[static_cast<size_t>(i)].hit > 0.5;
                    value += hit ? std::log(probability) : std::log1p(-probability);
                }
                bernoulliScores[static_cast<size_t>(m)] = value;
                bernoulliMaximum = std::max(bernoulliMaximum, value);
            }
            double bernoulliSum = 0.0;
            for (double value : bernoulliScores)
                bernoulliSum += std::exp(value - bernoulliMaximum);
            bernoulliMarginalized[static_cast<size_t>(s)] = bernoulliMaximum +
                std::log(bernoulliSum / static_cast<double>(scoringReplicas));
        }
        double logNormalizer = -INFINITY;
        std::vector<double> logMass(static_cast<size_t>(sourceCount), -INFINITY);
        for (int s = 0; s < sourceCount; ++s)
        {
            const double prior = static_cast<double>(freeCellsPerSource[static_cast<size_t>(s)]) /
                static_cast<double>(totalFreeCells);
            logMass[static_cast<size_t>(s)] = std::log(prior) + marginalized[static_cast<size_t>(s)];
            logNormalizer = std::max(logNormalizer, logMass[static_cast<size_t>(s)]);
        }
        double normalizer = 0.0;
        for (double value : logMass)
            normalizer += std::exp(value - logNormalizer);
        if (!(normalizer > 0.0) || !std::isfinite(normalizer))
        {
            GSL_ERROR("EC-ECDL posterior normalization failed");
            return false;
        }
        std::vector<long double> candidateMass(static_cast<size_t>(sourceCount), 0.0L);
        for (int s = 0; s < sourceCount; ++s)
            candidateMass[static_cast<size_t>(s)] = static_cast<long double>(
                std::exp(logMass[static_cast<size_t>(s)] - logNormalizer) / normalizer);

        double bernoulliLogNormalizer = -INFINITY;
        std::vector<double> bernoulliLogMass(static_cast<size_t>(sourceCount), -INFINITY);
        for (int s = 0; s < sourceCount; ++s)
        {
            const double prior = static_cast<double>(freeCellsPerSource[static_cast<size_t>(s)]) /
                static_cast<double>(totalFreeCells);
            bernoulliLogMass[static_cast<size_t>(s)] = std::log(prior) +
                bernoulliMarginalized[static_cast<size_t>(s)];
            bernoulliLogNormalizer = std::max(bernoulliLogNormalizer, bernoulliLogMass[static_cast<size_t>(s)]);
        }
        double bernoulliNormalizer = 0.0;
        for (double value : bernoulliLogMass)
            bernoulliNormalizer += std::exp(value - bernoulliLogNormalizer);
        std::vector<long double> bernoulliCandidateMass(static_cast<size_t>(sourceCount), 0.0L);
        for (int s = 0; s < sourceCount; ++s)
            bernoulliCandidateMass[static_cast<size_t>(s)] = static_cast<long double>(
                std::exp(bernoulliLogMass[static_cast<size_t>(s)] - bernoulliLogNormalizer) /
                bernoulliNormalizer);

        if (!tadmDirectory.empty())
        {
            std::ofstream candidates(tadmDirectory + "/ec_edcl_candidate_scores.csv", std::ios::out | std::ios::app);
            if (candidates.tellp() == 0)
                candidates << "run_uuid,source_update_id,sim_time,candidate_id,x,y,free_cells,native_shadow_mass,ec_edcl_mass,log_score,robust_min,robust_max,bernoulli_log_score,bernoulli_mass\n";
            for (int s = 0; s < sourceCount; ++s)
            {
                const auto& candidate = p2LastEvaluatedCandidates[static_cast<size_t>(s)];
                candidates << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17) << tadmSimTime << ','
                           << candidate.stableID << ',' << candidate.point.x << ',' << candidate.point.y << ','
                           << freeCellsPerSource[static_cast<size_t>(s)] << ','
                           << static_cast<double>(nativeCarrierMass[static_cast<size_t>(s)]) << ','
                           << static_cast<double>(candidateMass[static_cast<size_t>(s)]) << ','
                           << marginalized[static_cast<size_t>(s)] << ',' << robustMin[static_cast<size_t>(s)] << ','
                           << robustMax[static_cast<size_t>(s)] << ','
                           << bernoulliMarginalized[static_cast<size_t>(s)] << ','
                           << static_cast<double>(bernoulliCandidateMass[static_cast<size_t>(s)]) << '\n';
            }
            std::ofstream members(tadmDirectory + "/ec_edcl_member_ledger.csv", std::ios::out | std::ios::app);
            if (members.tellp() == 0)
                members << "run_uuid,source_update_id,candidate_id,scoring_replica,cumulative_log_score\n";
            for (int s = 0; s < sourceCount; ++s)
                for (int m = 0; m < scoringReplicas; ++m)
                    members << tadmRunUUID << ',' << tadmSourceUpdateId << ','
                            << p2LastEvaluatedCandidates[static_cast<size_t>(s)].stableID << ',' << m << ','
                            << std::setprecision(17) << cumulativeScores[static_cast<size_t>(s * scoringReplicas + m)] << '\n';
            std::ofstream summary(tadmDirectory + "/ec_edcl_update_summary.csv", std::ios::out | std::ios::app);
            if (summary.tellp() == 0)
                summary << "run_uuid,source_update_id,sim_time,status,inject,event_count,positive_events,source_count,channel_count,leading_lambda,k_dim,k_min_eigen,k_condition,projectivity_max_abs,online_batch_max_abs,online_batch_max_rel,physical_wall_s\n";
            summary << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17) << tadmSimTime
                    << ",VALID," << (inject ? 1 : 0) << ',' << eventCount << ',' << positiveEvents << ','
                    << sourceCount << ',' << channelCount << ',' << solver.eigenvalues()(eventCount - 1) << ','
                    << newDimension << ',' << kMinEigen << ',' << kCondition << ',' << projectivityMaxAbs << ','
                    << maxExactAbs << ',' << maxExactRel << ',' << physicalWallSeconds << '\n';
        }

        if (inject)
        {
            std::fill(sourceProbInternal.begin(), sourceProbInternal.end(), 0.0L);
            for (int s = 0; s < sourceCount; ++s)
            {
                const auto& rect = p2LastEvaluatedCandidates[static_cast<size_t>(s)].rect;
                const long double perCell = candidateMass[static_cast<size_t>(s)] /
                    static_cast<long double>(freeCellsPerSource[static_cast<size_t>(s)]);
                for (int x = rect[0]; x < rect[0] + rect[2]; ++x)
                    for (int y = rect[1]; y < rect[1] + rect[3]; ++y)
                    {
                        const Vector2Int index{x, y};
                        if (!measuredHitProb.metadata.indicesInBounds(index))
                            continue;
                        const size_t cell = measuredHitProb.metadata.indexOf(index);
                        if (measuredHitProb.occupancy[cell] == Occupancy::Free)
                            sourceProbInternal[cell] = perCell;
                    }
            }
        }

        ecEdclHistoryValid = true;
        ecEdclCarrierIds = std::move(carrierIds);
        ecEdclBlockDimensions.push_back(channelCount);
        ecEdclCalibrationHistory = std::move(calibrationHistory);
        ecEdclScoringResidualHistory = std::move(residualHistory);
        ecEdclCumulativeMemberScores = std::move(cumulativeScores);
        ecEdclPreviousCovarianceDim = newDimension;
        ecEdclPreviousCovariance.assign(static_cast<size_t>(newDimension * newDimension), 0.0);
        for (int i = 0; i < newDimension; ++i)
            for (int j = 0; j < newDimension; ++j)
                ecEdclPreviousCovariance[static_cast<size_t>(i * newDimension + j)] = historyCovariance(i, j);
        GSL_INFO("EC-ECDL valid update {}: events={}, positive={}, channels={}, carriers={}, K_dim={}, projectivity={}, exact_rel={}, inject={}, physical_wall_s={}",
                 tadmSourceUpdateId, eventCount, positiveEvents, channelCount, sourceCount, newDimension,
                 projectivityMaxAbs, maxExactRel, inject, physicalWallSeconds);
        return true;
    }

    bool Simulations::applyMEAci()
    {
        const bool inject = pfdiMode == "me_aci";
        constexpr int transportMembers = 0;
        constexpr int modelErrorMembers = 54;
        constexpr int robustBlocks = 5;
        constexpr double probabilityFloor = 1e-6;
        constexpr double responseTime = 1.2;
        constexpr double maxOffsetCells = 2.0;
        if (p2LastEvaluatedCandidates.empty())
        {
            GSL_ERROR("ME-ACI inverse-transport contract violation: empty candidate set");
            return false;
        }
        if (pcAciActiveEvents.empty())
        {
            pcAciAcceptedThisUpdate = false;
            GSL_WARN("ME-ACI update {} abstained: no completed observation events", tadmSourceUpdateId);
            return true;
        }

        // Audit boundary for inverse-transport development.  This is a
        // read-only export of the exact completed StopAndMeasure events seen
        // by inference; it is written before candidate scoring and contains
        // no source truth or posterior fields.
        std::filesystem::create_directories(tadmDirectory);
        const std::string eventTag = fmt::format("{:04d}", tadmSourceUpdateId);
        std::ofstream eventFile(tadmDirectory + "/meaci_events_update_" + eventTag + ".csv");
        eventFile << "source_update_id,event_index,block_id,sim_time,x,y,hit,concentration,threshold,wind_speed,wind_direction\n";
        for (size_t eventIndex = 0; eventIndex < pcAciActiveEvents.size(); ++eventIndex)
        {
            const PCAciEvent& event = pcAciActiveEvents[eventIndex];
            eventFile << tadmSourceUpdateId << ',' << eventIndex << ',' << event.blockId << ','
                      << std::setprecision(17) << event.simTime << ',' << event.position.x << ','
                      << event.position.y << ',' << event.hit << ',' << event.concentration << ','
                      << event.threshold << ',' << event.windSpeed << ',' << event.windDirection << '\n';
        }
        eventFile.flush();

        const auto foldCounts = [&](int parity)
        {
            std::array<int, 2> counts{0, 0};
            for (size_t eventIndex = 0; eventIndex < pcAciActiveEvents.size(); ++eventIndex)
            {
                if (static_cast<int>(eventIndex % 2) != parity)
                    continue;
                ++counts[0];
                counts[1] += pcAciActiveEvents[eventIndex].hit > 0.5 ? 1 : 0;
            }
            return counts;
        };
        const auto evenCounts = foldCounts(0);
        const auto oddCounts = foldCounts(1);
        std::vector<size_t> hitSiteCells;
        for (const PCAciEvent& event : pcAciActiveEvents)
        {
            if (event.hit <= 0.5)
                continue;
            const Vector2Int indices = measuredHitProb.metadata.coordinatesToIndices(
                event.position.x, event.position.y);
            if (!measuredHitProb.metadata.indicesInBounds(indices))
                continue;
            const size_t cell = measuredHitProb.metadata.indexOf(indices);
            if (std::find(hitSiteCells.begin(), hitSiteCells.end(), cell) == hitSiteCells.end())
                hitSiteCells.push_back(cell);
        }
        const bool temporallyIdentifiable =
            evenCounts[1] > 0 && evenCounts[1] < evenCounts[0] &&
            oddCounts[1] > 0 && oddCounts[1] < oddCounts[0];
        // One hit location cannot distinguish a persistent source footprint
        // from an intermittent plume encounter.  Requiring replication at a
        // second occupied grid location is the minimum truth-blind spatial
        // identifiability condition; no distance, likelihood, or posterior
        // threshold is tuned here.
        const bool spatiallyReplicated = hitSiteCells.size() >= 2;
        if (!temporallyIdentifiable || !spatiallyReplicated)
        {
            meAciEvidenceReservoir = pcAciActiveEvents;
            const bool carryPrevious = inject && pcAciLastAcceptedUpdateId > 0 &&
                pcAciCausalPosteriorGrid.size() == sourceProbInternal.size();
            if (carryPrevious)
                sourceProbInternal = pcAciCausalPosteriorGrid;
            pcAciAcceptedThisUpdate = false;
            std::ofstream abstention(tadmDirectory + "/meaci_abstention_update_" + eventTag + ".csv");
            abstention << "source_update_id,event_count,even_count,even_hits,odd_count,odd_hits,hit_site_count,reason,carried_previous_accepted_update\n";
            const char* reason = !temporallyIdentifiable
                ? "non_identifying_temporal_fold" : "single_hit_site_no_spatial_replication";
            abstention << tadmSourceUpdateId << ',' << pcAciActiveEvents.size() << ','
                       << evenCounts[0] << ',' << evenCounts[1] << ',' << oddCounts[0] << ','
                       << oddCounts[1] << ',' << hitSiteCells.size() << ',' << reason << ','
                       << (carryPrevious ? 1 : 0) << '\n';
            abstention.flush();
            GSL_WARN("ME-ACI inverse-transport update {} abstained: even={}/{}, odd={}/{}, hit_sites={}, reason={}, carried_previous={}",
                     tadmSourceUpdateId, evenCounts[1], evenCounts[0], oddCounts[1], oddCounts[0],
                     hitSiteCells.size(), reason, carryPrevious);
            return true;
        }

        const auto sigmoidStable = [](double value)
        {
            if (value >= 0.0)
                return 1.0 / (1.0 + std::exp(-std::min(value, 60.0)));
            const double e = std::exp(std::max(value, -60.0));
            return e / (1.0 + e);
        };
        const auto logitStable = [&](double probability)
        {
            const double p = std::clamp(probability, probabilityFloor, 1.0 - probabilityFloor);
            return std::log(p) - std::log1p(-p);
        };
        const auto sampleBilinear = [&](const std::vector<float>& map, double x, double y)
        {
            const double cellSize = static_cast<double>(measuredHitProb.metadata.cellSize);
            const double fx = (x - (static_cast<double>(measuredHitProb.metadata.origin.x) + 0.5 * cellSize)) / cellSize;
            const double fy = (y - (static_cast<double>(measuredHitProb.metadata.origin.y) + 0.5 * cellSize)) / cellSize;
            if (fx < 0.0 || fy < 0.0 || fx > measuredHitProb.metadata.dimensions.x - 1.0 ||
                fy > measuredHitProb.metadata.dimensions.y - 1.0)
                return 0.0;
            const int x0 = static_cast<int>(std::floor(fx));
            const int y0 = static_cast<int>(std::floor(fy));
            const int x1 = std::min(x0 + 1, measuredHitProb.metadata.dimensions.x - 1);
            const int y1 = std::min(y0 + 1, measuredHitProb.metadata.dimensions.y - 1);
            const double dx = fx - x0, dy = fy - y0;
            const auto at = [&](int ix, int iy)
            {
                return static_cast<double>(map[measuredHitProb.metadata.indexOf({ix, iy})]);
            };
            return std::clamp((1.0 - dx) * (1.0 - dy) * at(x0, y0) +
                              dx * (1.0 - dy) * at(x1, y0) +
                              (1.0 - dx) * dy * at(x0, y1) + dx * dy * at(x1, y1), 0.0, 1.0);
        };
        const auto eventTaps = [&](const std::vector<float>& map, const PCAciEvent& event)
        {
            std::array<double, 7> taps{};
            const double cellSize = static_cast<double>(measuredHitProb.metadata.cellSize);
            const double h = std::clamp(std::max(event.windSpeed, 0.0) * responseTime,
                                        0.5 * cellSize, maxOffsetCells * cellSize);
            const double ex = std::cos(event.windDirection), ey = std::sin(event.windDirection);
            const double px = -ey, py = ex;
            const double x = event.position.x, y = event.position.y;
            const std::array<std::array<double, 2>, 7> points{{
                {{x, y}},
                {{x - 0.5 * h * ex, y - 0.5 * h * ey}},
                {{x + 0.5 * h * ex, y + 0.5 * h * ey}},
                {{x - h * ex, y - h * ey}},
                {{x + h * ex, y + h * ey}},
                {{x + 0.5 * h * px, y + 0.5 * h * py}},
                {{x - 0.5 * h * px, y - 0.5 * h * py}}
            }};
            for (size_t j = 0; j < taps.size(); ++j)
                taps[j] = sampleBilinear(map, points[j][0], points[j][1]);
            return taps;
        };

        const size_t candidateCount = p2LastEvaluatedCandidates.size();
        std::vector<MEAciRouteState> nextStates(candidateCount);
        std::vector<double> rawLogEvidence(candidateCount, -INFINITY);
        std::vector<double> evenLogEvidence(candidateCount, -INFINITY);
        std::vector<double> oddLogEvidence(candidateCount, -INFINITY);
        std::vector<double> logEvidence(candidateCount, -INFINITY);
        std::vector<std::array<double, robustBlocks>> crossFitBlockScores(candidateCount);
        const auto simulationStart = std::chrono::steady_clock::now();

        constexpr std::array<double, 3> spreads{0.25, 0.5, 1.0};
        constexpr std::array<double, 3> decays{4.0, 8.0, 16.0};
        constexpr std::array<double, 2> upstreamPenalties{1.0, 2.0};
        constexpr std::array<double, 3> slopes{0.5, 1.0, 2.0};
        const double cell = std::max(static_cast<double>(measuredHitProb.metadata.cellSize), 1e-9);
        const auto logAddExp = [](double a, double b)
        {
            if (!std::isfinite(a)) return b;
            if (!std::isfinite(b)) return a;
            const double maximum = std::max(a, b);
            return maximum + std::log(std::exp(a - maximum) + std::exp(b - maximum));
        };
        const auto logMeanExp = [](const std::vector<double>& values)
        {
            const double maximum = *std::max_element(values.begin(), values.end());
            double total = 0.0;
            for (double value : values)
                total += std::exp(value - maximum);
            return maximum + std::log(total / static_cast<double>(values.size()));
        };
        const auto conditionalInverseScore = [&](const Vector2& source, int parity) -> double
        {
            int eventCount = 0;
            int hitCount = 0;
            for (size_t eventIndex = 0; eventIndex < pcAciActiveEvents.size(); ++eventIndex)
            {
                if (parity >= 0 && static_cast<int>(eventIndex % 2) != parity)
                    continue;
                ++eventCount;
                hitCount += pcAciActiveEvents[eventIndex].hit > 0.5 ? 1 : 0;
            }
            if (hitCount <= 0 || hitCount >= eventCount)
                return std::numeric_limits<double>::quiet_NaN();
            std::vector<double> componentScores;
            componentScores.reserve(spreads.size() * decays.size() *
                                    upstreamPenalties.size() * slopes.size());
            for (double spread : spreads)
                for (double decay : decays)
                    for (double upstreamPenalty : upstreamPenalties)
                    {
                        std::vector<double> bases;
                        std::vector<unsigned char> hits;
                        bases.reserve(static_cast<size_t>(eventCount));
                        hits.reserve(static_cast<size_t>(eventCount));
                        for (size_t eventIndex = 0; eventIndex < pcAciActiveEvents.size(); ++eventIndex)
                        {
                            if (parity >= 0 && static_cast<int>(eventIndex % 2) != parity)
                                continue;
                            const PCAciEvent& event = pcAciActiveEvents[eventIndex];
                            const double ux = std::cos(event.windDirection);
                            const double uy = std::sin(event.windDirection);
                            const double dx = static_cast<double>(event.position.x - source.x);
                            const double dy = static_cast<double>(event.position.y - source.y);
                            const double downstream = dx * ux + dy * uy;
                            const double crosswind = -dx * uy + dy * ux;
                            const double positiveDownstream = std::max(downstream, 0.0);
                            const double width = cell + spread * positiveDownstream;
                            bases.push_back(-0.5 * (crosswind / width) * (crosswind / width)
                                            - std::log1p(positiveDownstream / decay)
                                            - upstreamPenalty * std::max(-downstream, 0.0) / cell);
                            hits.push_back(event.hit > 0.5 ? 1 : 0);
                        }
                        for (double slope : slopes)
                        {
                            std::vector<double> dynamic(static_cast<size_t>(hitCount + 1),
                                                        -std::numeric_limits<double>::infinity());
                            dynamic[0] = 0.0;
                            double observed = 0.0;
                            for (int processed = 1; processed <= eventCount; ++processed)
                            {
                                const double psi = slope * bases[static_cast<size_t>(processed - 1)];
                                if (hits[static_cast<size_t>(processed - 1)] != 0)
                                    observed += psi;
                                for (int count = std::min(hitCount, processed); count >= 1; --count)
                                    dynamic[static_cast<size_t>(count)] = logAddExp(
                                        dynamic[static_cast<size_t>(count)],
                                        dynamic[static_cast<size_t>(count - 1)] + psi);
                            }
                            componentScores.push_back(observed - dynamic[static_cast<size_t>(hitCount)]);
                        }
                    }
            return logMeanExp(componentScores);
        };

#pragma omp parallel for schedule(dynamic)
        for (int candidateIndex = 0; candidateIndex < static_cast<int>(candidateCount); ++candidateIndex)
        {
            const Vector2 source = p2LastEvaluatedCandidates[static_cast<size_t>(candidateIndex)].point;
            rawLogEvidence[static_cast<size_t>(candidateIndex)] = conditionalInverseScore(source, -1);
            evenLogEvidence[static_cast<size_t>(candidateIndex)] = conditionalInverseScore(source, 0);
            oddLogEvidence[static_cast<size_t>(candidateIndex)] = conditionalInverseScore(source, 1);
        }
        const auto normalRanks = [&](const std::vector<double>& values)
        {
            std::vector<size_t> order(candidateCount);
            std::iota(order.begin(), order.end(), 0);
            std::sort(order.begin(), order.end(), [&](size_t a, size_t b)
            {
                if (values[a] != values[b]) return values[a] < values[b];
                return p2LastEvaluatedCandidates[a].stableID < p2LastEvaluatedCandidates[b].stableID;
            });
            std::vector<double> result(candidateCount, 0.0);
            size_t begin = 0;
            while (begin < candidateCount)
            {
                size_t end = begin + 1;
                while (end < candidateCount && std::abs(values[order[end]] - values[order[begin]]) <= 1e-12)
                    ++end;
                const double averageRank = 0.5 * (static_cast<double>(begin + 1) + static_cast<double>(end));
                const double z = normalQuantile((averageRank - 0.5) / static_cast<double>(candidateCount));
                for (size_t i = begin; i < end; ++i) result[order[i]] = z;
                begin = end;
            }
            return result;
        };
        const std::vector<double> evenRanks = normalRanks(evenLogEvidence);
        const std::vector<double> oddRanks = normalRanks(oddLogEvidence);
        for (size_t s = 0; s < candidateCount; ++s)
        {
            logEvidence[s] = (evenRanks[s] + oddRanks[s]) / std::sqrt(2.0);
            crossFitBlockScores[s] = {evenLogEvidence[s], oddLogEvidence[s],
                                      evenRanks[s], oddRanks[s], logEvidence[s]};
        }
        const double simulationWallSeconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - simulationStart).count();

        std::vector<long double> candidatePrior(candidateCount, 0.0L);
        std::vector<int> candidateFreeCount(candidateCount, 0);
        std::vector<long double> candidatePosterior(candidateCount, 0.0L);
        long double maxLogPosterior = -INFINITY;
        bool valid = true;
        for (size_t s = 0; s < candidateCount; ++s)
        {
            const auto& rect = p2LastEvaluatedCandidates[s].rect;
            for (int x = rect[0]; x < rect[0] + rect[2]; ++x)
                for (int y = rect[1]; y < rect[1] + rect[3]; ++y)
                {
                    if (x < 0 || y < 0 || x >= measuredHitProb.metadata.dimensions.x ||
                        y >= measuredHitProb.metadata.dimensions.y)
                        continue;
                    const size_t cell = measuredHitProb.metadata.indexOf({x, y});
                    if (measuredHitProb.occupancy[cell] != Occupancy::Free)
                        continue;
                    const auto& causalPrior = pcAciLastAcceptedUpdateId > 0
                        ? pcAciCausalPosteriorGrid : pcAciDesignPriorGrid;
                    candidatePrior[s] += std::max(causalPrior[cell], 0.0L);
                    ++candidateFreeCount[s];
                }
            if (!(candidatePrior[s] > 0.0L) || candidateFreeCount[s] <= 0 || !std::isfinite(logEvidence[s]))
            {
                valid = false;
                break;
            }
            maxLogPosterior = std::max(maxLogPosterior,
                std::log(candidatePrior[s]) + static_cast<long double>(logEvidence[s]));
        }
        if (!valid || !std::isfinite(static_cast<double>(maxLogPosterior)))
        {
            pcAciAcceptedThisUpdate = false;
            GSL_ERROR("ME-ACI update {} rejected: non-finite candidate evidence or geometry prior", tadmSourceUpdateId);
            return false;
        }
        long double posteriorTotal = 0.0L;
        for (size_t s = 0; s < candidateCount; ++s)
        {
            candidatePosterior[s] = std::exp(std::log(candidatePrior[s]) +
                static_cast<long double>(logEvidence[s]) - maxLogPosterior);
            posteriorTotal += candidatePosterior[s];
        }
        if (!(posteriorTotal > 0.0L) || !std::isfinite(static_cast<double>(posteriorTotal)))
            return false;
        for (long double& value : candidatePosterior)
            value /= posteriorTotal;

        std::vector<int> bestArea(sourceProbInternal.size(), std::numeric_limits<int>::max());
        std::vector<long double> cellPosterior(sourceProbInternal.size(), 0.0L);
        size_t coveredCells = 0;
        for (size_t s = 0; s < candidateCount; ++s)
        {
            const auto& rect = p2LastEvaluatedCandidates[s].rect;
            const int area = rect[2] * rect[3];
            const long double density = candidatePosterior[s] / candidateFreeCount[s];
            for (int x = rect[0]; x < rect[0] + rect[2]; ++x)
                for (int y = rect[1]; y < rect[1] + rect[3]; ++y)
                {
                    if (x < 0 || y < 0 || x >= measuredHitProb.metadata.dimensions.x ||
                        y >= measuredHitProb.metadata.dimensions.y)
                        continue;
                    const size_t cell = measuredHitProb.metadata.indexOf({x, y});
                    if (measuredHitProb.occupancy[cell] != Occupancy::Free || area > bestArea[cell])
                        continue;
                    if (bestArea[cell] == std::numeric_limits<int>::max())
                        ++coveredCells;
                    bestArea[cell] = area;
                    cellPosterior[cell] = density;
                }
        }
        if (coveredCells != measuredHitProb.metadata.numFreeCells)
        {
            pcAciAcceptedThisUpdate = false;
            GSL_ERROR("ME-ACI candidate rectangles cover {}/{} free cells", coveredCells,
                      measuredHitProb.metadata.numFreeCells);
            return false;
        }

        std::vector<long double> nativeShadow = sourceProbInternal;
        long double nativeShadowTotal = 0.0L;
        for (size_t cell = 0; cell < nativeShadow.size(); ++cell)
            if (measuredHitProb.occupancy[cell] == Occupancy::Free && nativeShadow[cell] > 0.0L &&
                std::isfinite(static_cast<double>(nativeShadow[cell])))
                nativeShadowTotal += nativeShadow[cell];
        if (nativeShadowTotal > 0.0L)
            for (size_t cell = 0; cell < nativeShadow.size(); ++cell)
                if (measuredHitProb.occupancy[cell] == Occupancy::Free)
                    nativeShadow[cell] = std::max(nativeShadow[cell], 0.0L) / nativeShadowTotal;

        long double previousTotal = 0.0L;
        for (size_t cell = 0; cell < pcAciCausalPosteriorGrid.size(); ++cell)
            if (measuredHitProb.occupancy[cell] == Occupancy::Free)
                previousTotal += std::max(pcAciCausalPosteriorGrid[cell], 0.0L);
        long double informationGain = 0.0L;
        for (size_t cell = 0; cell < sourceProbInternal.size(); ++cell)
        {
            if (measuredHitProb.occupancy[cell] != Occupancy::Free)
                continue;
            if (inject)
                sourceProbInternal[cell] = cellPosterior[cell];
            const long double previous = previousTotal > 0.0L
                ? std::max(pcAciCausalPosteriorGrid[cell] / previousTotal,
                           std::numeric_limits<long double>::min())
                : std::max(pcAciDesignPriorGrid[cell], std::numeric_limits<long double>::min());
            const long double current = std::max(cellPosterior[cell], std::numeric_limits<long double>::min());
            informationGain += current * std::log(current / previous);
        }
        for (size_t s = 0; s < candidateCount; ++s)
            meAciRouteStates[p2LastEvaluatedCandidates[s].stableID] = nextStates[s];
        pcAciAcceptedThisUpdate = inject;
        meAciEvidenceReservoir.clear();

        std::filesystem::create_directories(tadmDirectory);
        const std::string tag = fmt::format("{:04d}", tadmSourceUpdateId);
        std::vector<long double> nativeCandidateMass(candidateCount, 0.0L);
        for (size_t s = 0; s < candidateCount; ++s)
        {
            const auto& rect = p2LastEvaluatedCandidates[s].rect;
            for (int x = rect[0]; x < rect[0] + rect[2]; ++x)
                for (int y = rect[1]; y < rect[1] + rect[3]; ++y)
                {
                    if (x < 0 || y < 0 || x >= measuredHitProb.metadata.dimensions.x ||
                        y >= measuredHitProb.metadata.dimensions.y)
                        continue;
                    const size_t cell = measuredHitProb.metadata.indexOf({x, y});
                    if (measuredHitProb.occupancy[cell] == Occupancy::Free)
                        nativeCandidateMass[s] += std::max(nativeShadow[cell], 0.0L);
                }
        }
        std::ofstream scoreFile(tadmDirectory + "/meaci_candidate_scores_update_" + tag + ".csv");
        scoreFile << "source_update_id,candidate_id,x,y,geometry_prior_mass,native_shadow_mass,full_conditional_log_score,temporal_rank_channel,even_conditional_log_score,odd_conditional_log_score,even_normal_rank,odd_normal_rank,repeated_temporal_channel,posterior_mass\n";
        for (size_t s = 0; s < candidateCount; ++s)
        {
            scoreFile << tadmSourceUpdateId << ',' << p2LastEvaluatedCandidates[s].stableID << ','
                      << std::setprecision(17) << p2LastEvaluatedCandidates[s].point.x << ','
                      << p2LastEvaluatedCandidates[s].point.y << ',' << static_cast<double>(candidatePrior[s]) << ','
                      << static_cast<double>(nativeCandidateMass[s]) << ',' << rawLogEvidence[s] << ','
                      << logEvidence[s];
            for (double value : crossFitBlockScores[s])
                scoreFile << ',' << value;
            scoreFile << ',' << static_cast<double>(candidatePosterior[s]) << '\n';
        }
        scoreFile.flush();
        std::ofstream nativeFile(tadmDirectory + "/meaci_native_shadow_update_" + tag + ".csv");
        nativeFile << "source_update_id,x,y,source_probability,native_normalization_valid\n";
        for (size_t cell = 0; cell < nativeShadow.size(); ++cell)
            if (measuredHitProb.occupancy[cell] == Occupancy::Free)
            {
                const Vector2 xy = measuredHitProb.metadata.indexToCoordinates(cell);
                nativeFile << tadmSourceUpdateId << ',' << std::setprecision(17) << xy.x << ',' << xy.y << ','
                           << static_cast<double>(nativeShadow[cell]) << ',' << (nativeShadowTotal > 0.0L ? 1 : 0) << '\n';
            }
        nativeFile.flush();
        std::ofstream posteriorFile(tadmDirectory + "/meaci_source_posterior_update_" + tag + ".csv");
        posteriorFile << "source_update_id,x,y,source_probability\n";
        for (size_t cell = 0; cell < sourceProbInternal.size(); ++cell)
            if (measuredHitProb.occupancy[cell] == Occupancy::Free)
            {
                const Vector2 xy = measuredHitProb.metadata.indexToCoordinates(cell);
                posteriorFile << tadmSourceUpdateId << ',' << std::setprecision(17) << xy.x << ',' << xy.y << ','
                              << static_cast<double>(cellPosterior[cell]) << '\n';
            }
        posteriorFile.flush();
        std::ofstream summary(tadmDirectory + "/meaci_update_summary.csv", std::ios::out | std::ios::app);
        if (summary.tellp() == 0)
            summary << "run_uuid,source_update_id,event_count,candidate_count,transport_members,model_error_members,valid,inject,information_gain_kl,simulation_wall_s,parameter_sha256\n";
        summary << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << pcAciActiveEvents.size() << ','
                << candidateCount << ',' << transportMembers << ',' << modelErrorMembers << ",1," << (inject ? 1 : 0) << ','
                << std::setprecision(17) << static_cast<double>(informationGain) << ',' << simulationWallSeconds << ','
                << "inverse_transport_sequential_replication_v3" << '\n';
        summary.flush();
        GSL_INFO("ME-ACI inverse-transport valid update {}: inject={}, events={}, candidates={}, nuisance=54, temporal_folds=2, KL={:.6g}, wall_s={:.3f}",
                 tadmSourceUpdateId, inject, pcAciActiveEvents.size(), candidateCount,
                 static_cast<double>(informationGain), simulationWallSeconds);
        return true;
    }

    bool Simulations::applyTADMPosterior()
    {
        if (!tadmEnabled)
            return true;
        // A9 is a completed-block analytic carrier.  It intentionally runs
        // before the legacy candidate x replica forward-simulation path so
        // PC-ACI cannot silently fall back to the old Hough/rank/event-Gaussian
        // implementation.
        if (pfdiMode == "ec_edcl" || pfdiMode == "ec_edcl_shadow")
            return applyEnsembleEcEdcl();
        if (pfdiMode == "pc_aci")
            return applyA9TvSdTfei();
        if (pfdiMode == "me_aci" || pfdiMode == "me_aci_shadow")
            return applyMEAci();
        if (p2LastEvaluatedCandidates.empty() || tadmReplicas <= 0)
        {
            GSL_ERROR("TADM has no native candidate set or replicas");
            return false;
        }

        const auto start = std::chrono::steady_clock::now();
        std::vector<size_t> support;
        std::vector<double> observed;
        std::vector<double> weights;
        std::vector<Vector2> coordinates;
        support.reserve(measuredHitProb.data.size());
        for (size_t i = 0; i < measuredHitProb.data.size(); ++i)
        {
            if (measuredHitProb.occupancy[i] != Occupancy::Free || measuredHitProb.data[i].confidence <= 0.0)
                continue;
            support.push_back(i);
            observed.push_back(tadmLogit(measuredHitProb.data[i].probability()));
            weights.push_back(measuredHitProb.data[i].confidence);
            coordinates.push_back(measuredHitProb.metadata.indexToCoordinates(i));
        }
        if (support.empty())
        {
            GSL_ERROR("TADM has empty measured support");
            return false;
        }

        Vector2 weightedWind(0.0f, 0.0f);
        double weightSum = 0.0;
        for (size_t j = 0; j < support.size(); ++j)
        {
            weightedWind.x += static_cast<float>(weights[j] * wind.data[support[j]].x);
            weightedWind.y += static_cast<float>(weights[j] * wind.data[support[j]].y);
            weightSum += weights[j];
        }
        if (weightSum > 0.0)
        {
            weightedWind.x /= static_cast<float>(weightSum);
            weightedWind.y /= static_cast<float>(weightSum);
        }
        double windNorm = std::sqrt(static_cast<double>(weightedWind.x) * weightedWind.x +
                                    static_cast<double>(weightedWind.y) * weightedWind.y);
        if (!(windNorm > 1e-12))
        {
            weightedWind = Vector2(0.0f, 0.0f);
            for (size_t j = 0; j < support.size(); ++j)
            {
                weightedWind.x += static_cast<float>(weights[j] * measuredHitProb.data[support[j]].originalPropagationDirection.x);
                weightedWind.y += static_cast<float>(weights[j] * measuredHitProb.data[support[j]].originalPropagationDirection.y);
            }
            weightedWind.x /= static_cast<float>(weightSum);
            weightedWind.y /= static_cast<float>(weightSum);
            windNorm = std::sqrt(static_cast<double>(weightedWind.x) * weightedWind.x +
                                 static_cast<double>(weightedWind.y) * weightedWind.y);
        }
        if (!(windNorm > 1e-12))
        {
            weightedWind = Vector2(1.0f, 0.0f);
            windNorm = 1.0;
        }
        const double ux = weightedWind.x / windNorm;
        const double uy = weightedWind.y / windNorm;
        const double upx = -uy;
        const double upy = ux;
        // The causal PC-ACI carrier is expressed in a fixed world frame.  A
        // changing estimated wind frame would otherwise rotate the latent
        // coordinates between windows and manufacture a temporal increment.
        // The simulator and TADM transport basis continue to use ux/uy.
        const double carrierUx = pfdiMode == "pc_aci" ? 1.0 : ux;
        const double carrierUy = pfdiMode == "pc_aci" ? 0.0 : uy;
        const double carrierUpx = pfdiMode == "pc_aci" ? 0.0 : upx;
        const double carrierUpy = pfdiMode == "pc_aci" ? 1.0 : upy;
        const double transportHorizon = windNorm * static_cast<double>(settings.iterationsToRecord) * settings.deltaTime;
        const std::array<double, 5> phaseOffsets{
            -transportHorizon, -0.5 * transportHorizon, 0.0,
            0.5 * transportHorizon, transportHorizon};

        // These maps depend only on the frozen grid, wind direction and
        // simulator horizon.  Building them once per source update preserves
        // every sampled value while removing repeated coordinate-to-index
        // conversions from the candidate x replica x phase hot loop.
        std::array<std::vector<int>, 5> phaseSupportIndices;
        std::array<std::vector<int>, 5> phaseGridIndices;
        for (size_t phaseIndex = 0; phaseIndex < phaseOffsets.size(); ++phaseIndex)
        {
            phaseSupportIndices[phaseIndex].assign(support.size(), -1);
            phaseGridIndices[phaseIndex].assign(measuredHitProb.data.size(), -1);
            for (size_t j = 0; j < support.size(); ++j)
            {
                const Vector2& xy = coordinates[j];
                const double shiftedX = static_cast<double>(xy.x) - phaseOffsets[phaseIndex] * ux;
                const double shiftedY = static_cast<double>(xy.y) - phaseOffsets[phaseIndex] * uy;
                const Vector2Int shiftedIndex = measuredHitProb.metadata.coordinatesToIndices(
                    static_cast<float>(shiftedX), static_cast<float>(shiftedY));
                if (measuredHitProb.metadata.indicesInBounds(shiftedIndex))
                {
                    const size_t shiftedCell = measuredHitProb.metadata.indexOf(shiftedIndex);
                    if (measuredHitProb.occupancy[shiftedCell] == Occupancy::Free)
                        phaseSupportIndices[phaseIndex][j] = static_cast<int>(shiftedCell);
                }
            }
            for (size_t cell = 0; cell < measuredHitProb.data.size(); ++cell)
            {
                if (measuredHitProb.occupancy[cell] != Occupancy::Free)
                    continue;
                const Vector2 xy = measuredHitProb.metadata.indexToCoordinates(cell);
                const double shiftedX = static_cast<double>(xy.x) - phaseOffsets[phaseIndex] * ux;
                const double shiftedY = static_cast<double>(xy.y) - phaseOffsets[phaseIndex] * uy;
                const Vector2Int shiftedIndex = measuredHitProb.metadata.coordinatesToIndices(
                    static_cast<float>(shiftedX), static_cast<float>(shiftedY));
                if (measuredHitProb.metadata.indicesInBounds(shiftedIndex))
                {
                    const size_t shiftedCell = measuredHitProb.metadata.indexOf(shiftedIndex);
                    if (measuredHitProb.occupancy[shiftedCell] == Occupancy::Free)
                        phaseGridIndices[phaseIndex][cell] = static_cast<int>(shiftedCell);
                }
            }
        }

        // Sliced-Wasserstein, candidate-relative physical carrier.  Each
        // wind-frame projection is represented by weighted quantiles.  The
        // median retains candidate-relative displacement; centered quantiles
        // retain plume shape after a transport shift.  This is a fixed OT
        // tangent representation, not a learned gate or a House-specific
        // statistic.
        constexpr int slicedProjectionCount = 4;
        constexpr int slicedQuantileCount = 5;
        constexpr int physicalFeatureCount = slicedProjectionCount * slicedQuantileCount;
        const auto physicalFeatures = [&](const std::vector<float>* simulated, const Vector2& origin)
            -> std::array<double, physicalFeatureCount>
        {
            std::array<double, physicalFeatureCount> result{};
            const int width = measuredHitProb.metadata.dimensions.x;
            const int height = measuredHitProb.metadata.dimensions.y;
            if (width <= 0 || height <= 0 || static_cast<size_t>(width * height) != measuredHitProb.data.size())
                return result;
            std::vector<float> raw(measuredHitProb.data.size(), 0.0f);
            for (size_t i = 0; i < raw.size(); ++i)
                raw[i] = static_cast<float>(std::max(0.0, simulated != nullptr
                    ? static_cast<double>((*simulated)[i])
                    : static_cast<double>(measuredHitProb.data[i].probability())));
            const std::array<double, slicedProjectionCount> projectionAngles{
                0.0, 0.25 * std::acos(-1.0), 0.5 * std::acos(-1.0), 0.75 * std::acos(-1.0)};
            constexpr std::array<double, slicedQuantileCount> quantileLevels{0.1, 0.3, 0.5, 0.7, 0.9};
            for (int projection = 0; projection < slicedProjectionCount; ++projection)
            {
                const double angle = projectionAngles[static_cast<size_t>(projection)];
                const double ca = std::cos(angle);
                const double sa = std::sin(angle);
                std::vector<std::pair<double, double>> samples;
                samples.reserve(raw.size());
                double totalMass = 0.0;
                for (size_t i = 0; i < raw.size(); ++i)
                {
                    if (measuredHitProb.occupancy[i] != Occupancy::Free)
                        continue;
                    // Close the forward observation contract: both the live
                    // field and every candidate plume must pass through the
                    // same time-varying sensing/coverage operator H_t.  Using
                    // unit weight for a simulated full-field plume compares
                    // it with a path-sampled observed plume and makes source
                    // displacement compensate for an observation mismatch.
                    const double confidence = std::max(
                        static_cast<double>(measuredHitProb.data[i].confidence), 0.0);
                    const double mass = confidence * static_cast<double>(raw[i]);
                    if (!(mass > 0.0))
                        continue;
                    const Vector2 xy = measuredHitProb.metadata.indexToCoordinates(i);
                    const double dx = static_cast<double>(xy.x - origin.x);
                    const double dy = static_cast<double>(xy.y - origin.y);
                    const double along = dx * carrierUx + dy * carrierUy;
                    const double cross = dx * carrierUpx + dy * carrierUpy;
                    samples.emplace_back(along * ca + cross * sa, mass);
                    totalMass += mass;
                }
                if (!(totalMass > 1e-9) || samples.empty())
                    continue;
                std::sort(samples.begin(), samples.end(), [](const auto& a, const auto& b)
                          { return a.first < b.first; });
                std::array<double, slicedQuantileCount> quantiles{};
                for (int q = 0; q < slicedQuantileCount; ++q)
                {
                    const double target = quantileLevels[static_cast<size_t>(q)] * totalMass;
                    double cumulative = 0.0;
                    quantiles[static_cast<size_t>(q)] = samples.back().first;
                    for (const auto& sample : samples)
                    {
                        cumulative += sample.second;
                        if (cumulative >= target)
                        {
                            quantiles[static_cast<size_t>(q)] = sample.first;
                            break;
                        }
                    }
                }
                const double median = quantiles[2];
                const int offset = projection * slicedQuantileCount;
                result[static_cast<size_t>(offset)] = median;
                for (int q = 0; q < slicedQuantileCount - 1; ++q)
                    result[static_cast<size_t>(offset + 1 + q)] =
                        quantiles[static_cast<size_t>(q)] - median;
            }
            return result;
        };

        struct CandidateScore
        {
            std::string id;
            Vector2 point;
            long double nativeScore = 0.0L;
            double logScore = -INFINITY;
            double combinedLogScore = -INFINITY;
            std::array<int, 4> rect{};
            std::vector<std::vector<double>> weightedReplicaLogits;
            std::shared_ptr<const std::vector<float>> nativeHitMap;
            // Full scoring-bank log likelihoods are retained for the
            // truth-blind trust-region budget.  They are never used to read
            // the true source or to tune a House-specific weight.
            std::vector<double> replicaLogScores;
            std::vector<std::array<double, 3>> weightedBasis;
            // Keep an absolute physical feature bank separate from the
            // scoring bank.  On a consecutive forecast--analysis window the
            // latter is replaced by current-minus-previous features, while
            // the former is the state that must be committed for the next
            // window.  Reusing the differenced bank as history would compute
            // x_t-(x_{t-1}-x_{t-2}) on the following update.
            std::vector<std::array<double, physicalFeatureCount>> physicalAbsoluteReplicaFeatures;
            std::vector<std::array<double, physicalFeatureCount>> physicalReplicaFeatures;
            // Fixed, physics-derived transport-phase states.  PC-ACI never
            // selects one of these states from the observation; it integrates
            // all five in the posterior predictive likelihood.  Keeping the
            // full bank also prevents a phase chosen for scoring from leaking
            // into the source covariance/eigenchannel fit.
            std::vector<std::array<std::array<double, physicalFeatureCount>, 5>> physicalPhaseReplicaFeatures;
            std::vector<std::vector<double>> pcAciEventReplicaProbabilities;
            std::array<double, physicalFeatureCount> observedPhysicalFeatures{};
            std::vector<int> phaseBestIndex;
            std::vector<double> phaseTadmLogScores;
            bool physicalTemporalAvailable = false;
        };
        std::vector<CandidateScore> scored(p2LastEvaluatedCandidates.size());
        const int candidateCount = static_cast<int>(scored.size());
        // Register adaptive leaves by their physical source-grid coordinate.
        // Quadtree IDs are implementation details and may change after a
        // refinement; the SD temporal operator must compare the same source
        // location across windows, not the same tree spelling.  The key is
        // derived only from the frozen map cell size and candidate position.
        const double temporalGridCell = std::max(
            static_cast<double>(measuredHitProb.metadata.cellSize), 1e-9);
        const auto temporalGridKey = [&](const Vector2& point)
        {
            const long long gx = std::llround(static_cast<double>(point.x) / temporalGridCell);
            const long long gy = std::llround(static_cast<double>(point.y) / temporalGridCell);
            return fmt::format("{}:{}", gx, gy);
        };
        const auto previousReplicasFor = [&](const CandidateScore& row)
            -> const std::vector<std::vector<double>>*
        {
            const auto gridIt = sdPreviousCandidateReplicasByGrid.find(temporalGridKey(row.point));
            if (gridIt != sdPreviousCandidateReplicasByGrid.end() &&
                (gridIt->second.size() == static_cast<size_t>(2 * tadmReplicas) ||
                 gridIt->second.size() == 1))
                return &gridIt->second;
            const auto idIt = sdPreviousCandidateReplicas.find(row.id);
            if (idIt != sdPreviousCandidateReplicas.end() &&
                (idIt->second.size() == static_cast<size_t>(2 * tadmReplicas) ||
                 idIt->second.size() == 1))
                return &idIt->second;
            return nullptr;
        };
        const auto previousReplicaAt = [&](const std::vector<std::vector<double>>& bank, int replica)
            -> const std::vector<double>&
        {
            return bank.size() == 1 ? bank.front() : bank.at(static_cast<size_t>(replica));
        };
        // Compute the immutable native-support budget before launching the
        // expensive replica simulations, so the OpenMP workers can skip
        // candidates that the SD support contract would never allow to move.
        std::vector<char> sdComputeCandidate(static_cast<size_t>(candidateCount), 1);
        std::vector<int> covarianceCandidateIndices;
        covarianceCandidateIndices.reserve(static_cast<size_t>(candidateCount));
        if (pfdiMode == "sd" || pfdiMode == "pc_aci")
        {
            if (persistentCarrierMode)
            {
                std::fill(sdComputeCandidate.begin(), sdComputeCandidate.end(), 1);
                for (int s = 0; s < candidateCount; ++s)
                    covarianceCandidateIndices.push_back(s);
                GSL_INFO("PFDI PC-SD-TFEI carrier support: evaluated_carriers={}, native_quadtree_support_budget=not_used, fixed_physical_support=true",
                         covarianceCandidateIndices.size());
            }
            else
            {
            std::vector<int> nativeOrder(static_cast<size_t>(candidateCount));
            for (int s = 0; s < candidateCount; ++s)
                nativeOrder[static_cast<size_t>(s)] = s;
            std::sort(nativeOrder.begin(), nativeOrder.end(), [&](int a, int b)
                      {
                          const auto& ca = p2LastEvaluatedCandidates[static_cast<size_t>(a)];
                          const auto& cb = p2LastEvaluatedCandidates[static_cast<size_t>(b)];
                          if (ca.nativeScore != cb.nativeScore)
                              return ca.nativeScore > cb.nativeScore;
                          return ca.stableID < cb.stableID;
                      });
            long double nativeTotal = 0.0L;
            for (const auto& row : p2LastEvaluatedCandidates)
                nativeTotal += std::max(row.nativeScore, 0.0L);
            // Diagnostic-only full-support arm: test whether SD can recover
            // a basin that lies outside native PMFS's 95% mass.  This is
            // intentionally kept in a separate build and is not the frozen
            // online contract; the production arm uses 0.95.
            constexpr double diagnosticSupportMass = 0.95;
            long double cumulative = 0.0L;
            std::fill(sdComputeCandidate.begin(), sdComputeCandidate.end(), 0);
            for (const int s : nativeOrder)
            {
                sdComputeCandidate[static_cast<size_t>(s)] = 1;
                covarianceCandidateIndices.push_back(s);
                cumulative += std::max(p2LastEvaluatedCandidates[static_cast<size_t>(s)].nativeScore, 0.0L);
                if (!(nativeTotal > 0.0L) || cumulative >= diagnosticSupportMass * nativeTotal)
                    break;
            }
            if (covarianceCandidateIndices.size() < 3)
            {
                covarianceCandidateIndices.clear();
                std::fill(sdComputeCandidate.begin(), sdComputeCandidate.end(), 1);
                for (int s = 0; s < candidateCount; ++s)
                    covarianceCandidateIndices.push_back(s);
            }
            GSL_INFO("PFDI SD-TFEI support-budget: evaluated_candidates={}, native_candidates={}, target_mass={:.2f}, diagnostic_full_support=false",
                     covarianceCandidateIndices.size(), candidateCount, diagnosticSupportMass);
            }
        }
        else
        {
            for (int s = 0; s < candidateCount; ++s)
                covarianceCandidateIndices.push_back(s);
        }

        // The first persistent-carrier window establishes a forecast bank.
        // Subsequent consecutive windows use an observed forecast--analysis
        // increment, mirroring weak-constraint latent data assimilation.  It
        // prevents a simulator-wide static bias from being mistaken for a
        // temporal source channel.
        const bool temporalPhysicalWindow = (pfdiMode == "sd" || pfdiMode == "pc_aci") && persistentCarrierMode &&
            sdTemporalHistoryValid && sdPreviousInferenceUpdateId + 1 == tadmSourceUpdateId &&
            sdPreviousObservedField.size() == measuredHitProb.data.size() &&
            !sdPreviousPhysicalReplicaFeatures.empty();
        const auto candidateLoopStart = std::chrono::steady_clock::now();

        // Native PMFS already treats candidate forward simulations as
        // independent and evaluates them with OpenMP.  TADM replicas obey the
        // same event-keyed RNG contract, so candidates can be evaluated in
        // parallel without changing any per-candidate score or random stream.
        // The previous serial loop consumed 106--116 s for one H01 update and
        // invalidated the 120 s closed-loop budget.
#pragma omp parallel for schedule(dynamic)
        for (int candidateIndex = 0; candidateIndex < static_cast<int>(p2LastEvaluatedCandidates.size()); ++candidateIndex)
        {
            const P2ShadowCandidate& candidate = p2LastEvaluatedCandidates[static_cast<size_t>(candidateIndex)];
            CandidateScore row;
            row.id = candidate.stableID;
            row.point = candidate.point;
            row.nativeScore = candidate.nativeScore;
            row.nativeHitMap = candidate.nativeHitMap;
            row.rect = candidate.rect;
            row.observedPhysicalFeatures = physicalFeatures(nullptr, candidate.point);
            // Phase registration is performed in the absolute physical
            // state.  The temporal likelihood may later replace the
            // observed vector by an increment, but using that increment to
            // choose a phase would compare x_t^sim against y_t-y_{t-1}.
            const auto absoluteObservedPhysicalFeatures = row.observedPhysicalFeatures;
            const auto previousPhysicalIt = sdPreviousPhysicalReplicaFeatures.find(row.id);
            if (temporalPhysicalWindow && previousPhysicalIt != sdPreviousPhysicalReplicaFeatures.end() &&
                previousPhysicalIt->second.size() == static_cast<size_t>(2 * tadmReplicas))
            {
                // Anchored PC-ACI retains the absolute observed source
                // signature.  Temporal change enters only the nuisance
                // covariance below; subtracting it here cancels the stable
                // source fingerprint that C_s is meant to preserve.
                if (pfdiMode != "pc_aci")
                {
                    const auto previousObservedFeatures = physicalFeatures(&sdPreviousObservedField, candidate.point);
                    for (int d = 0; d < physicalFeatureCount; ++d)
                        row.observedPhysicalFeatures[static_cast<size_t>(d)] -= previousObservedFeatures[static_cast<size_t>(d)];
                }
                row.physicalTemporalAvailable = true;
            }
            if ((pfdiMode == "sd" || pfdiMode == "pc_aci") && !sdComputeCandidate[static_cast<size_t>(candidateIndex)])
            {
                // Outside native 95% support the SD factor is intentionally
                // absent; finalizeEvidence will retain the native PMFS
                // value and still use the complete rectangle cover.
                row.replicaLogScores.assign(static_cast<size_t>(2 * tadmReplicas), -INFINITY);
                scored[static_cast<size_t>(candidateIndex)] = std::move(row);
                continue;
            }
            // A7 PC-ACI deliberately does not instantiate the misspecified
            // PMFS candidate plume family.  Its analytic inverse-transport
            // event likelihood is evaluated after this lightweight carrier
            // registration loop.  Keeping nativeScore/rect here preserves
            // the exact candidate and grid-coverage contracts.
            if (pfdiMode == "pc_aci")
            {
                row.replicaLogScores.assign(static_cast<size_t>(2 * tadmReplicas), 0.0);
                scored[static_cast<size_t>(candidateIndex)] = std::move(row);
                continue;
            }
            std::vector<std::array<double, 3>> basis;
            row.weightedBasis.reserve(support.size());
            basis.reserve(support.size());
            for (size_t j = 0; j < coordinates.size(); ++j)
            {
                const Vector2& xy = coordinates[j];
                // A single intercept is shared by all candidates in this
                // update.  The transport coordinates are source-relative,
                // matching the frozen cross-house TADM calibration contract.
                const double dx = static_cast<double>(xy.x - candidate.point.x);
                const double dy = static_cast<double>(xy.y - candidate.point.y);
                const std::array<double, 3> value{1.0, dx * ux + dy * uy, dx * upx + dy * upy};
                basis.push_back(value);
                const double sqrtWeight = std::sqrt(weights[j]);
                row.weightedBasis.push_back({sqrtWeight * value[0], sqrtWeight * value[1], sqrtWeight * value[2]});
            }

            std::vector<double> replicaScores;
            // First bank is calibration-only; second bank is scoring-only.
            // The disjoint event-keyed streams prevent the online estimator
            // from using the same replicas to fit C_eta and score y.
            const int bankReplicaCount = 2 * tadmReplicas;
            replicaScores.reserve(static_cast<size_t>(bankReplicaCount));
            row.replicaLogScores.assign(static_cast<size_t>(bankReplicaCount), -INFINITY);
            row.physicalAbsoluteReplicaFeatures.reserve(static_cast<size_t>(bankReplicaCount));
            row.physicalReplicaFeatures.reserve(static_cast<size_t>(bankReplicaCount));
            row.physicalPhaseReplicaFeatures.reserve(static_cast<size_t>(bankReplicaCount));
            row.pcAciEventReplicaProbabilities.reserve(static_cast<size_t>(bankReplicaCount));
            row.phaseTadmLogScores.reserve(static_cast<size_t>(bankReplicaCount));
            for (int replica = 0; replica < bankReplicaCount; ++replica)
            {
                // PC-ACI uses common exogenous transport noise across source
                // updates.  Temporal differences then compare like with like
                // instead of subtracting two independent Monte-Carlo draws.
                const uint64_t transportEpoch = pfdiMode == "pc_aci" ? 0ULL : tadmSourceUpdateId;
                const EventKey key{tadmGlobalSeed, transportEpoch, static_cast<uint64_t>(replica), tadmTransportSubstream};
                EventKeyedTransportRng transportRng(key);
                std::vector<float> hitMap(measuredHitProb.data.size(), 0.0f);
                simulateSourceInPosition(SimulationSource(candidate.point, measuredHitProb.metadata), hitMap, true,
                                         settings.iterationsToRecord, settings.deltaTime, settings.noiseSTDev, nullptr, &transportRng);
                if (settings.blurSigmaX > 0 || settings.blurSigmaY > 0)
                {
                    cv::Mat asImage(hitMap);
                    asImage = asImage.reshape(1, measuredHitProb.metadata.dimensions.y);
                    blurHitMap(asImage);
                }
                if (pfdiMode == "pc_aci")
                {
                    constexpr double eventProbabilityFloor = 0.5 / 201.0;
                    std::vector<double> eventProbabilities;
                    eventProbabilities.reserve(pcAciActiveEvents.size());
                    for (const PCAciEvent& event : pcAciActiveEvents)
                    {
                        const Vector2Int eventIndex = measuredHitProb.metadata.coordinatesToIndices(
                            event.position.x, event.position.y);
                        double probability = eventProbabilityFloor;
                        if (measuredHitProb.metadata.indicesInBounds(eventIndex))
                        {
                            const size_t cell = measuredHitProb.metadata.indexOf(eventIndex);
                            if (measuredHitProb.occupancy[cell] == Occupancy::Free)
                                probability = static_cast<double>(hitMap[cell]);
                        }
                        eventProbabilities.push_back(std::clamp(
                            probability, eventProbabilityFloor, 1.0 - eventProbabilityFloor));
                    }
                    row.pcAciEventReplicaProbabilities.push_back(std::move(eventProbabilities));
                }
                std::vector<double> discrepancy;
                std::vector<double> weightedLogits;
                discrepancy.reserve(support.size());
                weightedLogits.reserve(support.size());
                for (size_t j = 0; j < support.size(); ++j)
                {
                    const double simulatedLogit = tadmLogit(static_cast<double>(hitMap[support[j]]));
                    discrepancy.push_back(observed[j] - simulatedLogit);
                    weightedLogits.push_back(std::sqrt(weights[j]) * simulatedLogit);
                }
                replicaScores.push_back(tadmLogMarginal(discrepancy, basis, weights, tadmPrior));
                row.weightedReplicaLogits.push_back(std::move(weightedLogits));

                // Transport-phase marginalized TADM score.  The fixed
                // phase grid is the physical simulator horizon, not a
                // House-specific tuning range.  It absorbs a plume's
                // wind-axis timing/position mismatch before the auxiliary
                // model-accuracy factor is formed.
                std::array<double, 5> phaseScores{};
                if (pfdiMode != "pc_aci")
                for (size_t phaseIndex = 0; phaseIndex < phaseOffsets.size(); ++phaseIndex)
                {
                    std::vector<double> phaseDiscrepancy;
                    phaseDiscrepancy.reserve(support.size());
                    for (size_t j = 0; j < support.size(); ++j)
                    {
                        double shiftedProbability = 0.0;
                        const int shiftedCell = phaseSupportIndices[phaseIndex][j];
                        if (shiftedCell >= 0)
                        {
                            shiftedProbability = static_cast<double>(hitMap[static_cast<size_t>(shiftedCell)]);
                        }
                        phaseDiscrepancy.push_back(
                            observed[j] - tadmLogit(shiftedProbability));
                    }
                    phaseScores[phaseIndex] = tadmLogMarginal(
                        phaseDiscrepancy, basis, weights, tadmPrior);
                }
                const double phaseMax = *std::max_element(phaseScores.begin(), phaseScores.end());
                double phaseSum = 0.0;
                for (const double value : phaseScores)
                    phaseSum += std::exp(value - phaseMax);
                row.phaseTadmLogScores.push_back(
                    phaseMax + std::log(phaseSum / static_cast<double>(phaseScores.size())));

                // Enumerate the complete fixed transport-phase state space.
                // Legacy SD may retain its observation-conditioned alignment,
                // but PC-ACI is trained on the zero-phase absolute source
                // anchor and later integrates all phase states predictively.
                double bestDistance = std::numeric_limits<double>::infinity();
                int bestPhase = 2;
                std::array<std::array<double, physicalFeatureCount>, 5> phaseFeatureSet{};
                std::array<double, physicalFeatureCount> bestFeatures{};
                for (size_t phaseIndex = 0; phaseIndex < phaseOffsets.size(); ++phaseIndex)
                {
                    std::vector<float> shiftedMap(hitMap.size(), 0.0f);
                    for (size_t i = 0; i < hitMap.size(); ++i)
                    {
                        const int shiftedCell = phaseGridIndices[phaseIndex][i];
                        if (shiftedCell >= 0)
                            shiftedMap[i] = hitMap[static_cast<size_t>(shiftedCell)];
                    }
                    const auto phaseFeatures = physicalFeatures(&shiftedMap, candidate.point);
                    phaseFeatureSet[phaseIndex] = phaseFeatures;
                    double distance = 0.0;
                    for (int d = 0; d < physicalFeatureCount; ++d)
                    {
                        const double scale = 1.0 + std::abs(absoluteObservedPhysicalFeatures[static_cast<size_t>(d)]);
                        const double delta = (phaseFeatures[static_cast<size_t>(d)] -
                                              absoluteObservedPhysicalFeatures[static_cast<size_t>(d)]) / scale;
                        distance += delta * delta;
                    }
                    if (distance < bestDistance)
                    {
                        bestDistance = distance;
                        bestPhase = static_cast<int>(phaseIndex);
                        bestFeatures = phaseFeatures;
                    }
                }
                if (pfdiMode == "pc_aci")
                {
                    // Index 2 is exactly zero transport offset.  It alone
                    // defines C_s and the temporal innovation history.
                    bestPhase = 2;
                    bestFeatures = phaseFeatureSet[2];
                }
                row.phaseBestIndex.push_back(bestPhase);
                row.physicalPhaseReplicaFeatures.push_back(phaseFeatureSet);
                const auto absoluteFeatures = bestFeatures;
                row.physicalAbsoluteReplicaFeatures.push_back(absoluteFeatures);
                if (pfdiMode != "pc_aci" && temporalPhysicalWindow && row.physicalTemporalAvailable &&
                    previousPhysicalIt != sdPreviousPhysicalReplicaFeatures.end() &&
                    previousPhysicalIt->second.size() == static_cast<size_t>(2 * tadmReplicas))
                {
                    const auto& previousFeature = previousPhysicalIt->second[static_cast<size_t>(replica)];
                    if (previousFeature.size() != static_cast<size_t>(physicalFeatureCount))
                        row.physicalTemporalAvailable = false;
                    else
                        for (int d = 0; d < physicalFeatureCount; ++d)
                            bestFeatures[static_cast<size_t>(d)] -= previousFeature[static_cast<size_t>(d)];
                }
                row.physicalReplicaFeatures.push_back(bestFeatures);
            }

            const double replicaMax = *std::max_element(replicaScores.begin(), replicaScores.end());
            double replicaSum = 0.0;
            for (const double value : replicaScores)
                replicaSum += std::exp(value - replicaMax);
            row.logScore = replicaMax + std::log(replicaSum / static_cast<double>(replicaScores.size()));
            scored[static_cast<size_t>(candidateIndex)] = std::move(row);
        }
        const double candidateLoopWallSeconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - candidateLoopStart).count();

        // Common online evidence finalizer for all factorial arms.  Native
        // PMFS evidence is always retained; the selected arm contributes an
        // additional likelihood factor in log space.
        double finalizedMaxLogScore = -INFINITY;
        double trustAlpha = 0.0;
        double trustKL = 0.0;
        double trustBudget = 0.0;
        double trustMeanShift = 0.0;
        double trustDisagreement = 0.0;
        double trustNativeSupportMass = 0.0;
        double trustFusedSupportMass = 0.0;
        double trustLeastReplicaShift = 0.0;
        bool trustActive = false;
        bool sdOutOfSupportNoRescue = false;
        bool sdGlobalRescue = false;
        bool sdTemporalConfirmation = false;
        // A temporal window is diagnostic until a consecutive window confirms
        // the same SD basin.  Keeping the pending window out of the posterior
        // is essential: a small KL move can still reorder near-tied native
        // candidates and change the closed-loop navigation path.
        bool sdTemporalPendingNoInfluence = false;
        bool sdStabilityGate = true;
        double sdReplicaTopAgreement = 1.0;
        // PC-ACI uses marginal evidence over the held-out scoring bank.  The
        // legacy per-replica argmax agreement remains a diagnostic only; it
        // is not a valid gate for a marginalized likelihood.
        bool marginalLooStable = false;
        bool pcAciNoIdentifiableChannel = false;
        size_t marginalTopIndex = std::numeric_limits<size_t>::max();
        std::vector<size_t> marginalLooTopIndices;
        std::vector<char> marginalLooSameBasin;
        double fullVsLooMaxLogBFShift = 0.0;
        const auto finalizeEvidence = [&]() -> bool
        {
            // A likelihood factor is allowed to alter the native PMFS
            // posterior only inside the native candidate support.  This is a
            // truth-blind Bayesian compatibility gate.  It is evaluated here,
            // after the selected arm has produced its final logScore (SD-only
            // and joint overwrite the initial TADM score).
            bool moduleAccepted = true;
            size_t moduleTopRank = std::numeric_limits<size_t>::max();
            long double nativeTotal = 0.0L;
            size_t moduleTop = std::numeric_limits<size_t>::max();
            double moduleTopScore = -INFINITY;
            for (size_t i = 0; i < scored.size(); ++i)
            {
                nativeTotal += std::max(scored[i].nativeScore, 0.0L);
                if (scored[i].logScore > moduleTopScore)
                {
                    moduleTopScore = scored[i].logScore;
                    moduleTop = i;
                }
            }
            std::vector<size_t> nativeOrder(scored.size());
            for (size_t i = 0; i < nativeOrder.size(); ++i)
                nativeOrder[i] = i;
            std::sort(nativeOrder.begin(), nativeOrder.end(), [&](size_t a, size_t b)
                      {
                          if (scored[a].nativeScore != scored[b].nativeScore)
                              return scored[a].nativeScore > scored[b].nativeScore;
                          return scored[a].id < scored[b].id;
                      });
            std::vector<char> nativeSupport(scored.size(), 0);
            long double cumulative = 0.0L;
            bool moduleAppliedToSupport = false;
            if (!(nativeTotal > 0.0L) || moduleTop == std::numeric_limits<size_t>::max() || !std::isfinite(moduleTopScore))
            {
                moduleAccepted = false;
            }
            else
            {
                for (size_t rank = 0; rank < nativeOrder.size(); ++rank)
                {
                    const size_t index = nativeOrder[rank];
                    nativeSupport[index] = 1;
                    cumulative += std::max(scored[index].nativeScore, 0.0L);
                    if (cumulative >= 0.95L * nativeTotal)
                        break;
            }
            if (persistentCarrierMode)
            {
                // The fixed physical carrier is the support contract for
                // PC-SD-TFEI.  Native PMFS mass is retained as a background
                // score, but it cannot silently delete a physical carrier
                // before its predictive likelihood is evaluated.
                std::fill(nativeSupport.begin(), nativeSupport.end(), 1);
                moduleAccepted = moduleTop != std::numeric_limits<size_t>::max() &&
                                 std::isfinite(moduleTopScore);
                moduleAppliedToSupport = false;
                for (const auto& row : scored)
                    if (std::isfinite(row.logScore))
                    {
                        moduleAppliedToSupport = true;
                        break;
                    }
            }
                moduleAccepted = nativeSupport[moduleTop] != 0;
                for (size_t rank = 0; rank < nativeOrder.size(); ++rank)
                    if (nativeOrder[rank] == moduleTop)
                    {
                        moduleTopRank = rank + 1;
                        break;
                    }
            }
            for (size_t i = 0; i < scored.size(); ++i)
                if (nativeSupport[i] != 0 && std::isfinite(scored[i].logScore))
                    moduleAppliedToSupport = true;
            if (pfdiMode == "sd" && !sdStabilityGate)
            {
                // For the fixed physical carrier this is a premise gate, not
                // merely a warning: without held-out predictive agreement,
                // a mixture factor is not a defensible source likelihood.
                // The native PMFS posterior is retained and the bank remains
                // diagnostic-only.  The adaptive/non-carrier arm keeps the
                // older trust-region diagnostic path below.
                GSL_WARN("PFDI SD-TFEI stability diagnostic: scoring-replica top agreement={:.3f} (< strict majority); trust-region budget will shrink fusion",
                         sdReplicaTopAgreement);
                if (persistentCarrierMode)
                {
                    sdOutOfSupportNoRescue = true;
                    trustActive = false;
                    trustAlpha = 0.0;
                    trustKL = 0.0;
                    moduleAccepted = false;
                    moduleAppliedToSupport = false;
                    GSL_WARN("PFDI PC-SD-TFEI premise gate: held-out predictive agreement below majority; physical mixture suppressed");
                }
            }
            // Replace the hard all-or-nothing support gate for the new SD
            // trust-region candidate.  The displacement budget is estimated
            // from the independent scoring replicas themselves; no truth or
            // House-specific temperature is used.  The old support gate is
            // retained below as the negative-control path when trust cannot
            // be calibrated.
            if (pfdiMode == "sd" && nativeTotal > 0.0L)
            {
                const size_t n = scored.size();
                // A replica-consistent top basin in one update is not enough
                // to license support expansion.  Require temporal persistence
                // across two consecutive source-update windows.  This is a
                // stateful sequential-inference gate, not a House-specific
                // performance threshold: the first window can only refine
                // the native support; the second confirms persistence.
                // The first absolute window is diagnostic-only and cannot
                // steer navigation.  Requiring its spatial module top to
                // persist into the next window therefore couples the
                // confirmation gate to a path that the SD module did not
                // control.  Once a consecutive temporal-difference window
                // exists, use its truth-blind held-out replica agreement as
                // the persistence certificate instead; the difference
                // likelihood already compares the two windows and the
                // candidate-overlap/common-support checks were applied when
                // constructing it.  Keep the spatial-basin test as the
                // fallback for non-difference SD updates.
                const bool temporalDifferenceReady =
                    sdTemporalDifferenceActive &&
                    sdStabilityGate;
                if (temporalDifferenceReady)
                {
                    sdTemporalConfirmationCount = 2;
                    sdTemporalConfirmation = true;
                }
                else if (!sdTemporalDifferenceActive &&
                         moduleTop != std::numeric_limits<size_t>::max())
                {
                    if (sdPreviousModuleTopValid &&
                        tadmSourceUpdateId == sdPreviousModuleUpdateId + 1)
                    {
                        const auto& previousRect = sdPreviousModuleRect;
                        const auto& currentRect = scored[moduleTop].rect;
                        const double previousRadius = 0.5 * std::sqrt(
                            static_cast<double>(std::max(1, previousRect[2] * previousRect[3]))) * measuredHitProb.metadata.cellSize;
                        const double currentRadius = 0.5 * std::sqrt(
                            static_cast<double>(std::max(1, currentRect[2] * currentRect[3]))) * measuredHitProb.metadata.cellSize;
                        const double basinRadius = previousRadius + currentRadius + measuredHitProb.metadata.cellSize;
                        const double dx = static_cast<double>(scored[moduleTop].point.x - sdPreviousModuleTop.x);
                        const double dy = static_cast<double>(scored[moduleTop].point.y - sdPreviousModuleTop.y);
                        sdTemporalConfirmation = std::hypot(dx, dy) <= basinRadius;
                        sdTemporalConfirmationCount = sdTemporalConfirmation
                            ? std::min(sdTemporalConfirmationCount + 1, 2)
                            : 0;
                    }
                    else
                    {
                        sdTemporalConfirmationCount = 1;
                    }
                    sdPreviousModuleTop = scored[moduleTop].point;
                    sdPreviousModuleRect = scored[moduleTop].rect;
                    sdPreviousModuleUpdateId = tadmSourceUpdateId;
                    sdPreviousModuleTopValid = true;
                }
                else if (sdTemporalDifferenceActive)
                {
                    // Once a physical forecast--analysis increment exists,
                    // do not fall back to absolute-window top continuity.
                    // That would accept a stable but unsupported basin even
                    // when held-out predictive realizations disagree.
                    sdTemporalConfirmationCount = 0;
                    sdPreviousModuleTopValid = false;
                }
                else
                {
                    sdTemporalConfirmationCount = 0;
                    sdPreviousModuleTopValid = false;
                }
                // A fixed physical carrier solves registration, not
                // reliability.  It must not bypass the sequential
                // confirmation gate: the first absolute window is a
                // calibration/diagnostic window and may not steer PMFS.
                sdTemporalConfirmation = sdTemporalConfirmationCount >= 2;
                sdTemporalPendingNoInfluence = !sdTemporalConfirmation;
                std::vector<double> nativeProb(n, 0.0);
                for (size_t i = 0; i < n; ++i)
                    nativeProb[i] = std::max(static_cast<double>(scored[i].nativeScore), 0.0) /
                                    static_cast<double>(nativeTotal);

                std::vector<std::vector<double>> replicaPosteriors;
                for (int k = tadmReplicas; k < 2 * tadmReplicas; ++k)
                {
                    double maxLog = -INFINITY;
                    for (size_t i = 0; i < n; ++i)
                        if (std::isfinite(scored[i].replicaLogScores[static_cast<size_t>(k)]))
                            maxLog = std::max(maxLog, std::log(std::max(nativeProb[i], 1e-300)) +
                                                       scored[i].replicaLogScores[static_cast<size_t>(k)]);
                    if (!std::isfinite(maxLog))
                        continue;
                    std::vector<double> posterior(n, 0.0);
                    double normalizer = 0.0;
                    for (size_t i = 0; i < n; ++i)
                    {
                        const double score = scored[i].replicaLogScores[static_cast<size_t>(k)];
                        if (!std::isfinite(score))
                            continue;
                        posterior[i] = std::exp(std::log(std::max(nativeProb[i], 1e-300)) + score - maxLog);
                        normalizer += posterior[i];
                    }
                    if (normalizer > 0.0 && std::isfinite(normalizer))
                    {
                        for (double& value : posterior)
                            value /= normalizer;
                        replicaPosteriors.push_back(std::move(posterior));
                    }
                }

                if (replicaPosteriors.size() >= 2)
                {
                    std::vector<double> replicaMean(n, 0.0);
                    for (const auto& posterior : replicaPosteriors)
                        for (size_t i = 0; i < n; ++i)
                            replicaMean[i] += posterior[i] / static_cast<double>(replicaPosteriors.size());
                    std::vector<double> replicaKL;
                    for (const auto& posterior : replicaPosteriors)
                    {
                        double kl = 0.0;
                        for (size_t i = 0; i < n; ++i)
                            if (posterior[i] > 0.0 && replicaMean[i] > 0.0)
                                kl += posterior[i] * std::log(posterior[i] / replicaMean[i]);
                        if (std::isfinite(kl))
                            replicaKL.push_back(std::max(0.0, kl));
                    }
                    if (replicaKL.size() >= 2)
                    {
                        trustLeastReplicaShift = INFINITY;
                        for (const auto& posterior : replicaPosteriors)
                        {
                            double shiftKL = 0.0;
                            for (size_t i = 0; i < n; ++i)
                                if (posterior[i] > 0.0 && nativeProb[i] > 0.0)
                                    shiftKL += posterior[i] * std::log(posterior[i] / nativeProb[i]);
                            if (std::isfinite(shiftKL))
                                trustLeastReplicaShift = std::min(trustLeastReplicaShift, std::max(0.0, shiftKL));
                        }
                        for (size_t i = 0; i < n; ++i)
                            if (replicaMean[i] > 0.0 && nativeProb[i] > 0.0)
                                trustMeanShift += replicaMean[i] * std::log(replicaMean[i] / nativeProb[i]);
                        trustMeanShift = std::max(0.0, trustMeanShift);
                        trustDisagreement = *std::max_element(replicaKL.begin(), replicaKL.end());
                        const double reliability = trustMeanShift > 1e-12
                            ? trustMeanShift / (trustMeanShift + trustDisagreement)
                            : 0.0;
                        // Intersection certificate: the fused posterior may
                        // not move farther from native PMFS than the least
                        // displaced independent scoring replica.  This is a
                        // conservative, truth-blind lower envelope rather
                        // than a hand-tuned temperature.
                        trustBudget = std::min(reliability * trustMeanShift, trustLeastReplicaShift);
                        trustNativeSupportMass = 0.0;
                        for (size_t i = 0; i < n; ++i)
                            if (nativeSupport[i] != 0)
                                trustNativeSupportMass += nativeProb[i];
                        // Support expansion is not a free consequence of a
                        // small KL step.  It is licensed only when the
                        // independent scoring replicas agree on the same
                        // source basin.  Conversely, an unstable module top
                        // outside native support is a hard no-rescue case:
                        // preserving mass inside a wrong native basin while
                        // reordering it is not evidence of source recovery.
                        // Set a provisional flag here; the final rescue
                        // certificate also requires non-zero native-support
                        // overlap after the full-alpha path is evaluated.
                        const bool temporalRescueCandidate = pfdiMode == "sd" &&
                            !moduleAccepted && sdStabilityGate && sdTemporalConfirmation;
                        const auto evaluatePath = [&](double alpha, double* supportMass) -> double
                        {
                            double maxLog = -INFINITY;
                            for (size_t i = 0; i < n; ++i)
                                if (std::isfinite(scored[i].logScore))
                                    maxLog = std::max(maxLog, std::log(std::max(nativeProb[i], 1e-300)) +
                                                               alpha * scored[i].logScore);
                            std::vector<double> posterior(n, 0.0);
                            double normalizer = 0.0;
                            for (size_t i = 0; i < n; ++i)
                            {
                                if (!std::isfinite(scored[i].logScore))
                                    continue;
                                posterior[i] = std::exp(std::log(std::max(nativeProb[i], 1e-300)) +
                                                        alpha * scored[i].logScore - maxLog);
                                normalizer += posterior[i];
                            }
                            if (!(normalizer > 0.0) || !std::isfinite(normalizer))
                                return INFINITY;
                            double kl = 0.0;
                            double mass = 0.0;
                            for (size_t i = 0; i < n; ++i)
                            {
                                posterior[i] /= normalizer;
                                if (nativeSupport[i] != 0)
                                    mass += posterior[i];
                                if (posterior[i] > 0.0 && nativeProb[i] > 0.0)
                                    kl += posterior[i] * std::log(posterior[i] / nativeProb[i]);
                            }
                            if (supportMass)
                                *supportMass = mass;
                            return std::isfinite(kl) ? std::max(0.0, kl) : INFINITY;
                        };
                        trustKL = evaluatePath(1.0, &trustFusedSupportMass);
                        sdGlobalRescue = temporalRescueCandidate && trustFusedSupportMass > 0.0;
                        const auto satisfiesSupportContract = [&](double supportMass) -> bool
                        {
                            return sdGlobalRescue || supportMass + 1e-12 >= trustNativeSupportMass;
                        };
                        if (trustKL <= trustBudget + 1e-12 && satisfiesSupportContract(trustFusedSupportMass))
                            trustAlpha = 1.0;
                        else
                        {
                            double low = 0.0;
                            double high = 1.0;
                            for (int iteration = 0; iteration < 50; ++iteration)
                            {
                                const double mid = 0.5 * (low + high);
                                double midSupportMass = 0.0;
                                if (evaluatePath(mid, &midSupportMass) <= trustBudget &&
                                    satisfiesSupportContract(midSupportMass))
                                    low = mid;
                                else
                                    high = mid;
                            }
                            trustAlpha = low;
                            trustKL = evaluatePath(trustAlpha, &trustFusedSupportMass);
                        }
                        trustActive = trustAlpha > 1e-6 && std::isfinite(trustAlpha) && std::isfinite(trustKL);
                    }
                }
            }

            if (pfdiMode == "sd" && !persistentCarrierMode && !moduleAccepted && !sdStabilityGate)
            {
                // A low-consensus module top outside native support cannot
                // be rescued by the trust-region power.  Retain the classic
                // PMFS posterior exactly; this is a truth-blind negative
                // control rather than a tuned fallback.
                sdOutOfSupportNoRescue = true;
                trustActive = false;
                trustAlpha = 0.0;
                trustKL = 0.0;
                moduleAppliedToSupport = false;
                GSL_WARN("PFDI SD-TFEI no-rescue: module top is outside native support and held-out replica basin agreement={:.3f}; native PMFS posterior retained",
                         sdReplicaTopAgreement);
            }

            if (pfdiMode == "sd" && sdTemporalPendingNoInfluence)
            {
                // Do not let a first or non-persistent window alter the PMFS
                // posterior.  It remains available for diagnostics and for
                // the next-window confirmation test, but it cannot change
                // candidate ordering or navigation before confirmation.
                trustActive = false;
                trustAlpha = 0.0;
                trustKL = 0.0;
                moduleAppliedToSupport = false;
                moduleAccepted = false;
                GSL_INFO("PFDI SD-TFEI temporal gate: confirmation=pending; diagnostic_only=true; native posterior retained");
            }

            // If the trust budget could not be formed and the diagnostic
            // stability check failed, never fall back to unrestricted SD
            // fusion.  The only safe fallback is support-truncated evidence.
            if (pfdiMode == "sd" && !persistentCarrierMode && !trustActive && !sdStabilityGate)
                moduleAccepted = false;

            int fusionMode = 0;
            if (sdTemporalPendingNoInfluence)
                fusionMode = 0;
            else if (trustActive)
            {
                fusionMode = 3;
                GSL_INFO("PFDI SD-TFEI trust-region fusion: alpha={:.6f}, KL={:.6f}, mean_shift={:.6f}, disagreement={:.6f}, least_replica_shift={:.6f}, budget={:.6f}, native_support_mass={:.6f}, fused_support_mass={:.6f}, support_mode={}",
                         trustAlpha, trustKL, trustMeanShift, trustDisagreement, trustLeastReplicaShift, trustBudget, trustNativeSupportMass, trustFusedSupportMass,
                         sdGlobalRescue ? "global_rescue" : "native_mass_preserved");
            }
            else if (moduleAccepted)
                fusionMode = 1;
            else if (moduleAppliedToSupport)
                fusionMode = 2;

            if (sdOutOfSupportNoRescue)
                fusionMode = 0;

            if (pfdiMode == "sd" && !persistentCarrierMode && !trustActive && !moduleAccepted)
            {
                if (moduleAppliedToSupport)
                    GSL_WARN("PFDI SD-TFEI support gate fallback: trust budget unavailable; evidence retained only inside native 95pct support");
                else
                    GSL_WARN("PFDI SD-TFEI compatibility gate rejected update: trust budget unavailable and no finite evidence in native support");
            }
            if (moduleAccepted)
                GSL_INFO("PFDI compatibility gate accepted {} module: native_rank={}/{}", pfdiMode, moduleTopRank, scored.size());
            else if (moduleAppliedToSupport)
                GSL_WARN("PFDI support-truncated fusion for {} module top: native_rank={}/{}; evidence applied only inside native 95pct support",
                         pfdiMode, moduleTopRank, scored.size());
            else
                GSL_WARN("PFDI compatibility gate rejected {} module: no finite evidence in native support; baseline posterior retained",
                         pfdiMode);

            double maxLogScore = -INFINITY;
            for (size_t i = 0; i < scored.size(); ++i)
            {
                CandidateScore& row = scored[i];
                const double native = std::max(static_cast<double>(row.nativeScore), 1e-300);
                const bool useModule = !sdTemporalPendingNoInfluence &&
                                       (fusionMode == 1 || (fusionMode == 2 && nativeSupport[i] != 0) ||
                                        (fusionMode == 3 && std::isfinite(row.logScore)));
                const double modulePower = fusionMode == 3 ? trustAlpha : 1.0;
                row.combinedLogScore = std::log(native) + (useModule ? modulePower * row.logScore : 0.0);
                maxLogScore = std::max(maxLogScore, row.combinedLogScore);
            }
            finalizedMaxLogScore = maxLogScore;

            std::ofstream scoreFile(tadmDirectory + "/tadm_source_update_scores.csv", std::ios::out | std::ios::app);
            if (scoreFile.tellp() == 0)
                scoreFile << "run_uuid,source_update_id,sim_time,candidate_id,source_x,source_y,native_score,tadm_log_score,combined_log_score,pfdi_gate_accepted,pfdi_fusion_mode,native_support_rank,tadm_calibration_replicas,tadm_scoring_replicas,trust_alpha,trust_kl,trust_mean_shift,trust_disagreement,trust_least_replica_shift,trust_budget,trust_native_support_mass,trust_fused_support_mass\n";
            for (const CandidateScore& row : scored)
                scoreFile << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17) << tadmSimTime << ','
                          << row.id << ',' << row.point.x << ',' << row.point.y << ','
                          << static_cast<double>(row.nativeScore) << ',' << row.logScore << ',' << row.combinedLogScore << ','
                          << (moduleAccepted ? 1 : 0) << ',' << fusionMode << ',' << moduleTopRank << ',' << tadmReplicas << ',' << tadmReplicas << ','
                          << trustAlpha << ',' << trustKL << ',' << trustMeanShift << ',' << trustDisagreement << ',' << trustLeastReplicaShift << ',' << trustBudget << ',' << trustNativeSupportMass << ',' << trustFusedSupportMass << '\n';
            scoreFile.flush();

            // Preserve the exact native PMFS posterior only when no finite
            // module evidence survives.  In support-truncated mode the
            // module is a trust-region refinement of the native posterior;
            // candidates outside its 95% mass retain their native evidence.
            if (fusionMode == 0)
                return true;

            std::vector<int> bestArea(sourceProbInternal.size(), std::numeric_limits<int>::max());
            std::vector<double> cellEvidence(sourceProbInternal.size(), 0.0);
            size_t assigned = 0;
            for (const CandidateScore& row : scored)
            {
                const int ox = row.rect[0];
                const int oy = row.rect[1];
                const int sx = row.rect[2];
                const int sy = row.rect[3];
                const int area = sx * sy;
                const double evidence = std::exp(row.combinedLogScore - maxLogScore);
                for (int x = ox; x < ox + sx; ++x)
                    for (int y = oy; y < oy + sy; ++y)
                    {
                        if (x < 0 || y < 0 || x >= measuredHitProb.metadata.dimensions.x || y >= measuredHitProb.metadata.dimensions.y)
                            continue;
                        const size_t index = measuredHitProb.metadata.indexOf({x, y});
                        if (measuredHitProb.occupancy[index] != Occupancy::Free)
                            continue;
                        if (area <= bestArea[index])
                        {
                            if (bestArea[index] == std::numeric_limits<int>::max())
                                ++assigned;
                            bestArea[index] = area;
                            cellEvidence[index] = evidence;
                        }
                    }
            }
            if (assigned == 0 || assigned < measuredHitProb.metadata.numFreeCells)
            {
                GSL_ERROR("TADM candidate rectangles do not cover all free source cells: {}/{}", assigned,
                          measuredHitProb.metadata.numFreeCells);
                return false;
            }
            for (size_t i = 0; i < sourceProbInternal.size(); ++i)
                if (measuredHitProb.occupancy[i] == Occupancy::Free)
                    sourceProbInternal[i] = cellEvidence[i];
            return true;
        };

        // PC-ACI is a sequential assimilative update, not a second
        // likelihood on the current native observation.  The first absolute
        // window only establishes the temporal carrier/history.  Once a
        // consecutive increment and the held-out replica gate are available,
        // the previous normalized grid posterior is used as the prior and
        // the current SD-TFEI increment is the sole new likelihood.
        const auto finalizePcAciSequential = [&]() -> bool
        {
            const bool priorReady = pcAciCausalStateAvailable &&
                pcAciCausalPosteriorGrid.size() == sourceProbInternal.size();
            const bool historyReady = sdTemporalHistoryValid && sdTemporalDifferenceActive;
            const bool gateReady = priorReady && historyReady && marginalLooStable && !scored.empty();
            std::string rejectReason;
            if (!priorReady) rejectReason = "independent_causal_prior_unavailable";
            else if (pcAciNoIdentifiableChannel) rejectReason = "no_identifiable_temporal_channel_abstain";
            else if (!historyReady) rejectReason = "first_absolute_window_diagnostic_only";
            else if (!marginalLooStable) rejectReason = "marginal_evidence_loo_unstable";
            else if (scored.empty()) rejectReason = "empty_candidate_bank";

            const std::vector<long double> nativeShadowRaw = sourceProbInternal;
            std::vector<long double> nativeShadow = nativeShadowRaw;
            long double nativeShadowTotal = 0.0L;
            for (size_t cell = 0; cell < nativeShadow.size(); ++cell)
                if (measuredHitProb.occupancy[cell] == Occupancy::Free &&
                    nativeShadow[cell] > 0.0L && std::isfinite(static_cast<double>(nativeShadow[cell])))
                    nativeShadowTotal += nativeShadow[cell];
            if (nativeShadowTotal > 0.0L)
                for (size_t cell = 0; cell < nativeShadow.size(); ++cell)
                    if (measuredHitProb.occupancy[cell] == Occupancy::Free)
                        nativeShadow[cell] = std::max(nativeShadow[cell], 0.0L) / nativeShadowTotal;

            long double priorEntropy = 0.0L;
            long double posteriorEntropy = 0.0L;
            long double informationGainKL = 0.0L;
            size_t coveredCells = 0;
            bool accepted = gateReady;
            std::vector<long double> candidateLogPrior(scored.size(), -INFINITY);
            std::vector<long double> candidateLogPosterior(scored.size(), -INFINITY);
            std::vector<int> candidateFreeCounts(scored.size(), 0);
            std::vector<long double> candidatePriorMass(scored.size(), 0.0L);
            std::vector<long double> candidatePosteriorMass(scored.size(), 0.0L);
            long double priorMassTotal = 0.0L;
            // A failed activation/history/stability gate is a complete
            // abstention.  Do not enter posterior arithmetic with placeholder
            // candidate scores, otherwise a later numerical check can
            // overwrite the scientifically meaningful abstention reason.
            if (accepted && priorReady)
            {
                for (size_t cell = 0; cell < sourceProbInternal.size(); ++cell)
                    if (measuredHitProb.occupancy[cell] == Occupancy::Free)
                    {
                        const long double p = std::max(pcAciCausalPosteriorGrid[cell], 0.0L);
                        priorMassTotal += p;
                        if (p > 0.0L && std::isfinite(static_cast<double>(p)))
                            priorEntropy -= p * std::log(p);
                    }
                if (!(priorMassTotal > 0.0L) || !std::isfinite(static_cast<double>(priorMassTotal)))
                {
                    accepted = false;
                    rejectReason = "independent_causal_prior_nonfinite_or_zero_mass";
                }
                else
                {
                    const auto rectanglePriorMass = [&](const CandidateScore& row, int& freeCount) -> long double
                    {
                        const int ox = row.rect[0], oy = row.rect[1];
                        const int sx = row.rect[2], sy = row.rect[3];
                        long double mass = 0.0L;
                        freeCount = 0;
                        for (int x = ox; x < ox + sx; ++x)
                            for (int y = oy; y < oy + sy; ++y)
                            {
                                if (x < 0 || y < 0 || x >= measuredHitProb.metadata.dimensions.x || y >= measuredHitProb.metadata.dimensions.y)
                                    continue;
                                const size_t cell = measuredHitProb.metadata.indexOf({x, y});
                                if (measuredHitProb.occupancy[cell] != Occupancy::Free)
                                    continue;
                                mass += std::max(pcAciCausalPosteriorGrid[cell], 0.0L);
                                ++freeCount;
                            }
                        return mass;
                    };
                    long double maxLogPosterior = -INFINITY;
                    for (size_t i = 0; i < scored.size(); ++i)
                    {
                        candidatePriorMass[i] = rectanglePriorMass(scored[i], candidateFreeCounts[i]);
                        if (candidateFreeCounts[i] <= 0 || !std::isfinite(scored[i].logScore))
                        {
                            accepted = false;
                            rejectReason = "candidate_prior_or_incremental_likelihood_invalid";
                            break;
                        }
                        // A long-double floor is purely a numerical support
                        // guard.  It is many orders below any representable
                        // PMFS probability and does not widen the posterior.
                        candidatePriorMass[i] = std::max(candidatePriorMass[i], std::numeric_limits<long double>::min());
                        candidateLogPrior[i] = std::log(candidatePriorMass[i]);
                        candidateLogPosterior[i] = candidateLogPrior[i] + static_cast<long double>(scored[i].logScore);
                        maxLogPosterior = std::max(maxLogPosterior, candidateLogPosterior[i]);
                    }
                    if (accepted && !std::isfinite(static_cast<double>(maxLogPosterior)))
                    {
                        accepted = false;
                        rejectReason = "incremental_likelihood_has_no_finite_mass";
                    }
                    if (accepted)
                    {
                        long double total = 0.0L;
                        for (size_t i = 0; i < candidatePosteriorMass.size(); ++i)
                        {
                            candidatePosteriorMass[i] = std::exp(candidateLogPosterior[i] - maxLogPosterior);
                            total += candidatePosteriorMass[i];
                        }
                        if (!(total > 0.0L) || !std::isfinite(static_cast<double>(total)))
                        {
                            accepted = false;
                            rejectReason = "posterior_normalization_failed";
                        }
                        else
                        {
                            for (long double& value : candidatePosteriorMass)
                                value /= total;
                            std::vector<int> bestArea(sourceProbInternal.size(), std::numeric_limits<int>::max());
                            std::vector<long double> cellPosterior(sourceProbInternal.size(), 0.0L);
                            for (size_t i = 0; i < scored.size(); ++i)
                            {
                                const int ox = scored[i].rect[0], oy = scored[i].rect[1];
                                const int sx = scored[i].rect[2], sy = scored[i].rect[3];
                                const int area = sx * sy;
                                const long double density = candidatePosteriorMass[i] /
                                    static_cast<long double>(candidateFreeCounts[i]);
                                for (int x = ox; x < ox + sx; ++x)
                                    for (int y = oy; y < oy + sy; ++y)
                                    {
                                        if (x < 0 || y < 0 || x >= measuredHitProb.metadata.dimensions.x || y >= measuredHitProb.metadata.dimensions.y)
                                            continue;
                                        const size_t cell = measuredHitProb.metadata.indexOf({x, y});
                                        if (measuredHitProb.occupancy[cell] != Occupancy::Free)
                                            continue;
                                        if (area <= bestArea[cell])
                                        {
                                            if (bestArea[cell] == std::numeric_limits<int>::max())
                                                ++coveredCells;
                                            bestArea[cell] = area;
                                            cellPosterior[cell] = density;
                                        }
                                    }
                            }
                            if (coveredCells != measuredHitProb.metadata.numFreeCells)
                            {
                                accepted = false;
                                rejectReason = "candidate_rectangles_do_not_cover_free_grid";
                            }
                            else
                            {
                                for (size_t cell = 0; cell < sourceProbInternal.size(); ++cell)
                                    if (measuredHitProb.occupancy[cell] == Occupancy::Free)
                                    {
                                        const long double p = std::max(cellPosterior[cell], 0.0L);
                                        sourceProbInternal[cell] = p;
                                        if (p > 0.0L && std::isfinite(static_cast<double>(p)))
                                        {
                                            posteriorEntropy -= p * std::log(p);
                                            const long double prior = std::max(
                                                pcAciCausalPosteriorGrid[cell], std::numeric_limits<long double>::min());
                                            informationGainKL += p * std::log(
                                                std::max(p, std::numeric_limits<long double>::min()) / prior);
                                        }
                                    }
                            }
                        }
                    }
                }
            }

            if (!accepted)
            {
                coveredCells = 0;
                // Native PMFS values are deliberately untouched on reject.
                GSL_WARN("PC-ACI rejected update {}: reason={}, prior_ready={}, history_ready={}, marginal_loo_stable={}; native posterior retained",
                         tadmSourceUpdateId, rejectReason, priorReady, historyReady, marginalLooStable);
            }
            else
            {
                rejectReason = "accepted";
                pcAciAcceptedThisUpdate = true;
                GSL_INFO("PC-ACI accepted update {}: prior=independent_causal_state, likelihood=copula_fused_spatiotemporal_tomography_increment, KL={:.6g}, prior_entropy={:.6g}, posterior_entropy={:.6g}",
                         tadmSourceUpdateId, static_cast<double>(informationGainKL),
                         static_cast<double>(priorEntropy), static_cast<double>(posteriorEntropy));
            }

            if (!tadmDirectory.empty())
            {
                std::filesystem::create_directories(tadmDirectory);
                const std::string updateTag = fmt::format("{:04d}", tadmSourceUpdateId);
                std::ofstream nativeFile(tadmDirectory + "/native_shadow_source_posterior_update_" + updateTag + ".csv",
                                         std::ios::out | std::ios::trunc);
                nativeFile << "source_update_id,x,y,source_probability,native_normalization_valid\n";
                for (size_t cell = 0; cell < nativeShadow.size(); ++cell)
                    if (measuredHitProb.occupancy[cell] == Occupancy::Free)
                    {
                        const Vector2 xy = measuredHitProb.metadata.indexToCoordinates(cell);
                        nativeFile << tadmSourceUpdateId << ',' << std::setprecision(17) << xy.x << ',' << xy.y << ','
                                   << static_cast<double>(nativeShadow[cell]) << ',' << (nativeShadowTotal > 0.0L ? 1 : 0) << '\n';
                    }
                nativeFile.flush();
                if (accepted)
                {
                    std::ofstream causalFile(tadmDirectory + "/causal_source_posterior_update_" + updateTag + ".csv",
                                             std::ios::out | std::ios::trunc);
                    causalFile << "source_update_id,x,y,source_probability\n";
                    for (size_t cell = 0; cell < sourceProbInternal.size(); ++cell)
                        if (measuredHitProb.occupancy[cell] == Occupancy::Free)
                        {
                            const Vector2 xy = measuredHitProb.metadata.indexToCoordinates(cell);
                            causalFile << tadmSourceUpdateId << ',' << std::setprecision(17) << xy.x << ',' << xy.y << ','
                                       << static_cast<double>(sourceProbInternal[cell]) << '\n';
                        }
                    causalFile.flush();
                }

                std::ofstream evidence(tadmDirectory + "/pc_aci_a3_candidate_evidence.csv", std::ios::out | std::ios::app);
                if (evidence.tellp() == 0)
                {
                    evidence << "run_uuid,source_update_id,sim_time,candidate_id,x,y,native_score,causal_log_likelihood,causal_log_prior_mass,causal_log_posterior_mass";
                    for (int k = 0; k < tadmReplicas; ++k)
                        evidence << ",scoring_replica_" << k;
                    evidence << ",marginal_loo_stable,aci_gate_accepted,aci_reject_reason\n";
                }
                for (size_t i = 0; i < scored.size(); ++i)
                {
                    evidence << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17) << tadmSimTime << ','
                             << scored[i].id << ',' << scored[i].point.x << ',' << scored[i].point.y << ','
                             << static_cast<double>(scored[i].nativeScore) << ',' << scored[i].logScore << ','
                             << static_cast<double>(candidateLogPrior[i]) << ','
                             << static_cast<double>(candidateLogPosterior[i]);
                    for (int k = 0; k < tadmReplicas; ++k)
                    {
                        const size_t scoringIndex = static_cast<size_t>(tadmReplicas + k);
                        const double value = scoringIndex < scored[i].replicaLogScores.size()
                            ? scored[i].replicaLogScores[scoringIndex] : -INFINITY;
                        evidence << ',' << value;
                    }
                    evidence << ',' << (marginalLooStable ? 1 : 0) << ',' << (accepted ? 1 : 0) << ',' << rejectReason << '\n';
                }
                evidence.flush();

                std::ofstream file(tadmDirectory + "/pc_aci_source_update_scores.csv", std::ios::out | std::ios::app);
                if (file.tellp() == 0)
                    file << "run_uuid,source_update_id,sim_time,mode,previous_prior_available,aci_history_ready,aci_gate_accepted,aci_reject_reason,replica_top_agreement,marginal_top_candidate,marginal_top_x,marginal_top_y,loo_top_candidate,loo_same_basin,marginal_loo_stable,full_vs_loo_max_logbf_shift,information_gain_kl,prior_entropy,posterior_entropy,covered_cells,free_cells,candidate_count,replica_count\n";
                std::string looTop;
                std::string looSame;
                for (size_t k = 0; k < marginalLooTopIndices.size(); ++k)
                {
                    if (k > 0) { looTop += ';'; looSame += ';'; }
                    if (marginalLooTopIndices[k] == std::numeric_limits<size_t>::max())
                        looTop += "NA";
                    else
                        looTop += scored[marginalLooTopIndices[k]].id;
                    looSame += marginalLooSameBasin[k] ? "1" : "0";
                }
                const std::string marginalTopCandidate =
                    marginalTopIndex == std::numeric_limits<size_t>::max() ? "NA" : scored[marginalTopIndex].id;
                const double marginalTopX = marginalTopIndex == std::numeric_limits<size_t>::max()
                    ? std::numeric_limits<double>::quiet_NaN() : scored[marginalTopIndex].point.x;
                const double marginalTopY = marginalTopIndex == std::numeric_limits<size_t>::max()
                    ? std::numeric_limits<double>::quiet_NaN() : scored[marginalTopIndex].point.y;
                file << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17) << tadmSimTime << ','
                     << "pc_aci," << (priorReady ? 1 : 0) << ',' << (historyReady ? 1 : 0) << ',' << (accepted ? 1 : 0) << ','
                     << rejectReason << ',' << sdReplicaTopAgreement << ',' << marginalTopCandidate << ',' << marginalTopX << ',' << marginalTopY << ','
                     << looTop << ',' << looSame << ',' << (marginalLooStable ? 1 : 0) << ',' << fullVsLooMaxLogBFShift << ','
                     << static_cast<double>(informationGainKL) << ',' << static_cast<double>(priorEntropy) << ','
                     << static_cast<double>(posteriorEntropy) << ',' << coveredCells << ',' << measuredHitProb.metadata.numFreeCells << ','
                     << scored.size() << ',' << tadmReplicas << '\n';
                file.flush();
            }
            return true;
        };

        // Event-channel SD-TFEI.  The smoothed PMFS probability field is an
        // inference product, not a raw observation, and comparing its shape
        // with a full simulated plume creates a circular likelihood.  This
        // branch instead applies the actual sequence of sensing locations to
        // every candidate realization and learns source-stable combinations
        // of those hit/miss events.
        if (pfdiMode == "pc_aci")
        {
            const int rc = tadmReplicas;
            const int eventCount = static_cast<int>(pcAciActiveEvents.size());
            // A8: cumulative spatiotemporal tomography eigenchannel.
            //
            // Every visited sensing site casts two complementary, analytic
            // inverse-transport votes over the fixed source grid:
            //   (1) a bounded upwind Hough cone identifies the cross-wind
            //       source direction; and
            //   (2) a conditional concentration profile identifies range
            //       while eliminating unknown source strength.
            // The two score fields are copula-normalized independently before
            // fusion.  This makes their numerical scales irrelevant and keeps
            // the method truth-blind.  The first identifiable window is held
            // as a causal calibration window.  At the second window, the two
            // held fields enter exactly once; later updates add only the new
            // window, so sequential Bayes never double-counts old evidence.
            if (eventCount > 0 && candidateCount > 0)
            {
                struct TomographySite
                {
                    Vector2 position{0.0f, 0.0f};
                    int count = 0;
                    int hits = 0;
                    double concentrationSum = 0.0;
                    double thresholdSum = 0.0;
                    double windXSum = 0.0;
                    double windYSum = 0.0;
                    double windSpeedSum = 0.0;
                };

                const double cell = std::max(
                    static_cast<double>(measuredHitProb.metadata.cellSize), 1e-9);
                std::vector<TomographySite> sites;
                for (const PCAciEvent& event : pcAciActiveEvents)
                {
                    size_t siteIndex = sites.size();
                    for (size_t i = 0; i < sites.size(); ++i)
                    {
                        const double dx = static_cast<double>(sites[i].position.x - event.position.x);
                        const double dy = static_cast<double>(sites[i].position.y - event.position.y);
                        if (std::hypot(dx, dy) <= 0.25 * cell)
                        {
                            siteIndex = i;
                            break;
                        }
                    }
                    if (siteIndex == sites.size())
                    {
                        TomographySite site;
                        site.position = event.position;
                        sites.push_back(site);
                    }
                    TomographySite& site = sites[siteIndex];
                    ++site.count;
                    site.hits += event.hit > 0.5 ? 1 : 0;
                    site.concentrationSum += std::max(event.concentration, 0.0);
                    site.thresholdSum += std::max(event.threshold, 1e-12);
                    const double speed = std::max(event.windSpeed, 0.0);
                    site.windXSum += speed * std::cos(event.windDirection);
                    site.windYSum += speed * std::sin(event.windDirection);
                    site.windSpeedSum += speed;
                }

                int hitSiteCount = 0;
                int informativeSiteCount = 0;
                for (const TomographySite& site : sites)
                {
                    const double windNorm = std::hypot(site.windXSum, site.windYSum);
                    if (site.hits > 0)
                        ++hitSiteCount;
                    if (site.hits > 0 && windNorm > 1e-9)
                        ++informativeSiteCount;
                }
                if (hitSiteCount < 3 || informativeSiteCount < 3)
                {
                    pcAciNoIdentifiableChannel = true;
                    marginalLooStable = false;
                    sdTemporalDifferenceActive = false;
                    GSL_WARN("PC-ACI A8 abstained update {}: sites={}, hit_sites={}, informative_sites={}; need at least three independent hit sites",
                             tadmSourceUpdateId, sites.size(), hitSiteCount, informativeSiteCount);
                    return finalizePcAciSequential();
                }

                const auto logMeanExp = [](const std::vector<double>& values)
                {
                    const double maximum = *std::max_element(values.begin(), values.end());
                    double sum = 0.0;
                    for (const double value : values)
                        sum += std::exp(value - maximum);
                    return maximum + std::log(sum / static_cast<double>(values.size()));
                };
                constexpr std::array<double, 3> spreads{0.25, 0.5, 1.0};
                constexpr std::array<double, 3> dilutions{0.0, 0.5, 1.0};
                std::vector<double> houghRaw(static_cast<size_t>(candidateCount), 0.0);
                std::vector<double> intensityRaw(static_cast<size_t>(candidateCount), 0.0);

                for (int s = 0; s < candidateCount; ++s)
                {
                    const Vector2 source = scored[static_cast<size_t>(s)].point;
                    double houghWeightedSum = 0.0;
                    double houghWeight = 0.0;
                    for (const TomographySite& site : sites)
                    {
                        if (site.hits <= 0)
                            continue;
                        const double windNorm = std::hypot(site.windXSum, site.windYSum);
                        if (!(windNorm > 1e-9))
                            continue;
                        const double uxEvent = site.windXSum / windNorm;
                        const double uyEvent = site.windYSum / windNorm;
                        const double dx = static_cast<double>(site.position.x - source.x);
                        const double dy = static_cast<double>(site.position.y - source.y);
                        const double downstream = dx * uxEvent + dy * uyEvent;
                        const double crosswind = -dx * uyEvent + dy * uxEvent;
                        const double hitFraction = static_cast<double>(site.hits) /
                            static_cast<double>(std::max(site.count, 1));
                        const double reliability = hitFraction * std::sqrt(static_cast<double>(site.count)) *
                            std::max(site.windSpeedSum / static_cast<double>(site.count), 1e-6);
                        double vote = 0.0;
                        if (downstream > 0.0)
                            for (const double spread : spreads)
                            {
                                const double width = cell + spread * downstream;
                                vote += std::exp(-0.5 * (crosswind / width) * (crosswind / width)) /
                                    static_cast<double>(spreads.size());
                            }
                        houghWeightedSum += reliability * vote;
                        houghWeight += reliability;
                    }
                    houghRaw[static_cast<size_t>(s)] = houghWeight > 0.0
                        ? houghWeightedSum / houghWeight : 0.0;

                    std::vector<double> nuisanceScores;
                    nuisanceScores.reserve(spreads.size() * dilutions.size());
                    for (const double spread : spreads)
                        for (const double dilution : dilutions)
                        {
                            std::vector<double> predicted;
                            std::vector<double> observedWeights;
                            predicted.reserve(sites.size());
                            observedWeights.reserve(sites.size());
                            for (const TomographySite& site : sites)
                            {
                                const double windNorm = std::hypot(site.windXSum, site.windYSum);
                                if (site.hits <= 0 || !(windNorm > 1e-9))
                                    continue;
                                const double uxEvent = site.windXSum / windNorm;
                                const double uyEvent = site.windYSum / windNorm;
                                const double dx = static_cast<double>(site.position.x - source.x);
                                const double dy = static_cast<double>(site.position.y - source.y);
                                const double downstream = dx * uxEvent + dy * uyEvent;
                                const double crosswind = -dx * uyEvent + dy * uxEvent;
                                double logIntensity = -40.0;
                                if (downstream > 0.0)
                                {
                                    const double width = cell + spread * downstream;
                                    logIntensity = -0.5 * (crosswind / width) * (crosswind / width) -
                                        dilution * std::log1p(downstream / cell);
                                }
                                const double meanConcentration = site.concentrationSum /
                                    static_cast<double>(std::max(site.count, 1));
                                const double meanThreshold = site.thresholdSum /
                                    static_cast<double>(std::max(site.count, 1));
                                predicted.push_back(logIntensity);
                                observedWeights.push_back(std::log1p(
                                    std::max(meanConcentration, 0.0) / std::max(meanThreshold, 1e-12)));
                            }
                            const double maxPredicted = *std::max_element(predicted.begin(), predicted.end());
                            double predictedNormalizer = 0.0;
                            double observedTotal = 0.0;
                            double conditionalScore = 0.0;
                            for (size_t i = 0; i < predicted.size(); ++i)
                            {
                                predictedNormalizer += std::exp(predicted[i] - maxPredicted);
                                observedTotal += observedWeights[i];
                                conditionalScore += observedWeights[i] * predicted[i];
                            }
                            conditionalScore -= observedTotal *
                                (maxPredicted + std::log(std::max(predictedNormalizer, 1e-300)));
                            nuisanceScores.push_back(conditionalScore);
                        }
                    intensityRaw[static_cast<size_t>(s)] = logMeanExp(nuisanceScores);
                }

                const auto copulaNormalRanks = [&](const std::vector<double>& raw)
                {
                    std::vector<size_t> order(raw.size());
                    std::iota(order.begin(), order.end(), 0);
                    std::sort(order.begin(), order.end(), [&](size_t a, size_t b)
                              {
                                  if (raw[a] != raw[b]) return raw[a] < raw[b];
                                  return scored[a].id < scored[b].id;
                              });
                    std::vector<double> ranks(raw.size(), 0.0);
                    size_t beginTie = 0;
                    while (beginTie < order.size())
                    {
                        size_t endTie = beginTie + 1;
                        while (endTie < order.size() &&
                               std::abs(raw[order[endTie]] - raw[order[beginTie]]) <= 1e-12)
                            ++endTie;
                        const double averageOneBasedRank =
                            0.5 * (static_cast<double>(beginTie + 1) + static_cast<double>(endTie));
                        const double probability =
                            (averageOneBasedRank - 0.5) / static_cast<double>(order.size());
                        const double rank = normalQuantile(probability);
                        for (size_t position = beginTie; position < endTie; ++position)
                            ranks[order[position]] = rank;
                        beginTie = endTie;
                    }
                    return ranks;
                };
                const std::vector<double> houghRank = copulaNormalRanks(houghRaw);
                const std::vector<double> intensityRank = copulaNormalRanks(intensityRaw);

                const uint64_t nextWindowCount = pcAciTomographyWindowCount + 1;
                for (int s = 0; s < candidateCount; ++s)
                {
                    const std::string key = temporalGridKey(scored[static_cast<size_t>(s)].point);
                    pcAciCumulativeHoughRank[key] += houghRank[static_cast<size_t>(s)];
                    pcAciCumulativeIntensityRank[key] += intensityRank[static_cast<size_t>(s)];
                    double channelScore = 0.0;
                    if (nextWindowCount == 2)
                        channelScore = (pcAciCumulativeHoughRank[key] +
                                        pcAciCumulativeIntensityRank[key]) / std::sqrt(2.0);
                    else if (nextWindowCount > 2)
                        channelScore = (houghRank[static_cast<size_t>(s)] +
                                        intensityRank[static_cast<size_t>(s)]) / std::sqrt(2.0);
                    scored[static_cast<size_t>(s)].logScore = channelScore;
                    std::fill(scored[static_cast<size_t>(s)].replicaLogScores.begin(),
                              scored[static_cast<size_t>(s)].replicaLogScores.end(), channelScore);
                }
                pcAciTomographyWindowCount = nextWindowCount;

                const size_t supportCount = std::max<size_t>(
                    1, static_cast<size_t>(std::ceil(0.1 * static_cast<double>(candidateCount))));
                std::vector<size_t> houghOrder(static_cast<size_t>(candidateCount));
                std::vector<size_t> intensityOrder(static_cast<size_t>(candidateCount));
                std::iota(houghOrder.begin(), houghOrder.end(), 0);
                std::iota(intensityOrder.begin(), intensityOrder.end(), 0);
                std::sort(houghOrder.begin(), houghOrder.end(), [&](size_t a, size_t b)
                          { return houghRank[a] != houghRank[b] ? houghRank[a] > houghRank[b] : scored[a].id < scored[b].id; });
                std::sort(intensityOrder.begin(), intensityOrder.end(), [&](size_t a, size_t b)
                          { return intensityRank[a] != intensityRank[b] ? intensityRank[a] > intensityRank[b] : scored[a].id < scored[b].id; });
                size_t channelOverlap = 0;
                for (size_t i = 0; i < supportCount; ++i)
                    if (std::find(intensityOrder.begin(), intensityOrder.begin() + supportCount,
                                  houghOrder[i]) != intensityOrder.begin() + supportCount)
                        ++channelOverlap;

                const bool mature = pcAciTomographyWindowCount >= 2;
                sdTemporalDifferenceActive = mature;
                sdTemporalHistoryValid = true;
                marginalLooStable = mature;
                sdStabilityGate = mature;
                sdReplicaTopAgreement = static_cast<double>(channelOverlap) /
                    static_cast<double>(supportCount);
                marginalTopIndex = static_cast<size_t>(std::distance(
                    scored.begin(), std::max_element(scored.begin(), scored.end(),
                        [](const CandidateScore& a, const CandidateScore& b)
                        { return a.logScore < b.logScore; })));
                marginalLooTopIndices.assign(static_cast<size_t>(rc), marginalTopIndex);
                marginalLooSameBasin.assign(static_cast<size_t>(rc), 1);
                fullVsLooMaxLogBFShift = 0.0;
                sdPreviousInferenceUpdateId = tadmSourceUpdateId;

                GSL_INFO("PC-ACI A8 spatiotemporal tomography update {}: events={}, sites={}, hit_sites={}, informative_sites={}, carriers={}, hough_intensity_top10_overlap={}/{}, accumulated_identifiable_windows={}, mature={}, analytic_no_forward_sim=true",
                         tadmSourceUpdateId, eventCount, sites.size(), hitSiteCount,
                         informativeSiteCount, candidateCount, channelOverlap, supportCount,
                         pcAciTomographyWindowCount, mature);
                if (!tadmDirectory.empty())
                {
                    std::ofstream profile(tadmDirectory + "/pc_aci_runtime_profile.csv", std::ios::out | std::ios::app);
                    if (profile.tellp() == 0)
                        profile << "run_uuid,source_update_id,sim_time,candidate_loop_wall_s,apply_total_wall_s,candidate_count,replica_count,physical_feature_count,temporal_window,marginal_loo_stable\n";
                    profile << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17)
                            << tadmSimTime << ',' << candidateLoopWallSeconds << ','
                            << std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count() << ','
                            << candidateCount << ',' << 0 << ',' << sites.size() << ','
                            << pcAciTomographyWindowCount << ',' << (marginalLooStable ? 1 : 0) << '\n';
                    profile.flush();
                }
                return finalizePcAciSequential();
            }
            // A7: conditional inverse-transport temporal eigenchannel.  It
            // removes the PMFS forward plume family from the source evidence,
            // conditions out the unknown emission/sensor intercept, and then
            // fuses only two consecutive copula-normalized rank windows.
            if (eventCount > 0 && candidateCount > 0)
            {
                int hitCount = 0;
                for (const PCAciEvent& event : pcAciActiveEvents)
                    hitCount += event.hit > 0.5 ? 1 : 0;
                if (hitCount <= 0 || hitCount >= eventCount)
                {
                    pcAciNoIdentifiableChannel = true;
                    marginalLooStable = false;
                    sdTemporalDifferenceActive = false;
                    GSL_WARN("PC-ACI A7 abstained update {}: conditional event count is non-identifying ({}/{})",
                             tadmSourceUpdateId, hitCount, eventCount);
                    return finalizePcAciSequential();
                }

                const auto logAddExp = [](double a, double b)
                {
                    if (!std::isfinite(a)) return b;
                    if (!std::isfinite(b)) return a;
                    const double maximum = std::max(a, b);
                    return maximum + std::log(std::exp(a - maximum) + std::exp(b - maximum));
                };
                const auto logMeanExp = [](const std::vector<double>& values)
                {
                    const double maximum = *std::max_element(values.begin(), values.end());
                    double sum = 0.0;
                    for (const double value : values)
                        sum += std::exp(value - maximum);
                    return maximum + std::log(sum / static_cast<double>(values.size()));
                };
                const double cell = std::max(
                    static_cast<double>(measuredHitProb.metadata.cellSize), 1e-9);
                constexpr std::array<double, 3> spreads{0.25, 0.5, 1.0};
                constexpr std::array<double, 3> decays{4.0, 8.0, 16.0};
                constexpr std::array<double, 2> upstreamPenalties{1.0, 2.0};
                constexpr std::array<double, 3> slopes{0.5, 1.0, 2.0};

                for (CandidateScore& row : scored)
                {
                    std::vector<double> componentScores;
                    componentScores.reserve(
                        spreads.size() * decays.size() * upstreamPenalties.size() * slopes.size());
                    for (const double spread : spreads)
                        for (const double decay : decays)
                            for (const double upstreamPenalty : upstreamPenalties)
                                for (const double slope : slopes)
                                {
                                    std::vector<double> dynamic(
                                        static_cast<size_t>(hitCount + 1),
                                        -std::numeric_limits<double>::infinity());
                                    dynamic[0] = 0.0;
                                    double observedSufficientStatistic = 0.0;
                                    int processed = 0;
                                    for (const PCAciEvent& event : pcAciActiveEvents)
                                    {
                                        const double uxEvent = std::cos(event.windDirection);
                                        const double uyEvent = std::sin(event.windDirection);
                                        const double dx = static_cast<double>(event.position.x - row.point.x);
                                        const double dy = static_cast<double>(event.position.y - row.point.y);
                                        const double downstream = dx * uxEvent + dy * uyEvent;
                                        const double crosswind = -dx * uyEvent + dy * uxEvent;
                                        const double positiveDownstream = std::max(downstream, 0.0);
                                        const double width = cell + spread * positiveDownstream;
                                        const double psi = slope * (
                                            -0.5 * (crosswind / width) * (crosswind / width)
                                            -std::log1p(positiveDownstream / decay)
                                            -upstreamPenalty * std::max(-downstream, 0.0) / cell);
                                        if (event.hit > 0.5)
                                            observedSufficientStatistic += psi;
                                        ++processed;
                                        const int upper = std::min(hitCount, processed);
                                        for (int count = upper; count >= 1; --count)
                                            dynamic[static_cast<size_t>(count)] = logAddExp(
                                                dynamic[static_cast<size_t>(count)],
                                                dynamic[static_cast<size_t>(count - 1)] + psi);
                                    }
                                    componentScores.push_back(
                                        observedSufficientStatistic - dynamic[static_cast<size_t>(hitCount)]);
                                }
                    row.logScore = logMeanExp(componentScores);
                }

                std::vector<size_t> scoreOrder(static_cast<size_t>(candidateCount));
                std::iota(scoreOrder.begin(), scoreOrder.end(), 0);
                std::sort(scoreOrder.begin(), scoreOrder.end(), [&](size_t a, size_t b)
                          {
                              if (scored[a].logScore != scored[b].logScore)
                                  return scored[a].logScore < scored[b].logScore;
                              return scored[a].id < scored[b].id;
                          });
                std::vector<double> currentRank(static_cast<size_t>(candidateCount), 0.0);
                size_t beginTie = 0;
                while (beginTie < scoreOrder.size())
                {
                    size_t endTie = beginTie + 1;
                    const double value = scored[scoreOrder[beginTie]].logScore;
                    while (endTie < scoreOrder.size() &&
                           std::abs(scored[scoreOrder[endTie]].logScore - value) <= 1e-12)
                        ++endTie;
                    const double averageOneBasedRank =
                        0.5 * (static_cast<double>(beginTie + 1) + static_cast<double>(endTie));
                    const double probability =
                        (averageOneBasedRank - 0.5) / static_cast<double>(candidateCount);
                    const double normalRank = normalQuantile(probability);
                    for (size_t position = beginTie; position < endTie; ++position)
                        currentRank[scoreOrder[position]] = normalRank;
                    beginTie = endTie;
                }

                bool previousAvailable = !pcAciPreviousTransportRank.empty();
                for (const CandidateScore& row : scored)
                    previousAvailable = previousAvailable &&
                        pcAciPreviousTransportRank.find(temporalGridKey(row.point)) !=
                            pcAciPreviousTransportRank.end();
                sdTemporalDifferenceActive = previousAvailable;
                for (int s = 0; s < candidateCount; ++s)
                {
                    const double previous = previousAvailable
                        ? pcAciPreviousTransportRank.at(temporalGridKey(scored[static_cast<size_t>(s)].point))
                        : currentRank[static_cast<size_t>(s)];
                    const double channelScore =
                        (previous + currentRank[static_cast<size_t>(s)]) / std::sqrt(2.0);
                    scored[static_cast<size_t>(s)].logScore = channelScore;
                    std::fill(scored[static_cast<size_t>(s)].replicaLogScores.begin(),
                              scored[static_cast<size_t>(s)].replicaLogScores.end(), channelScore);
                }

                const size_t supportCount = std::max<size_t>(
                    1, static_cast<size_t>(std::ceil(0.1 * static_cast<double>(candidateCount))));
                std::vector<size_t> descending(static_cast<size_t>(candidateCount));
                std::iota(descending.begin(), descending.end(), 0);
                std::sort(descending.begin(), descending.end(), [&](size_t a, size_t b)
                          {
                              if (currentRank[a] != currentRank[b])
                                  return currentRank[a] > currentRank[b];
                              return scored[a].id < scored[b].id;
                          });
                std::vector<std::string> currentTopSupport;
                currentTopSupport.reserve(supportCount);
                for (size_t i = 0; i < supportCount; ++i)
                    currentTopSupport.push_back(scored[descending[i]].id);
                size_t overlap = 0;
                for (const std::string& id : currentTopSupport)
                    if (std::find(pcAciPreviousTopSupport.begin(), pcAciPreviousTopSupport.end(), id) !=
                        pcAciPreviousTopSupport.end())
                        ++overlap;

                const auto logChoose = [](int n, int k)
                {
                    if (k < 0 || k > n)
                        return -std::numeric_limits<double>::infinity();
                    return std::lgamma(static_cast<double>(n + 1)) -
                           std::lgamma(static_cast<double>(k + 1)) -
                           std::lgamma(static_cast<double>(n - k + 1));
                };
                double replicationP = 1.0;
                if (previousAvailable && !pcAciPreviousTopSupport.empty())
                {
                    const int population = candidateCount;
                    const int selected = static_cast<int>(supportCount);
                    const int observedOverlap = static_cast<int>(overlap);
                    const double denominator = logChoose(population, selected);
                    std::vector<double> tail;
                    for (int x = observedOverlap; x <= selected; ++x)
                    {
                        if (x > selected || selected - x > population - selected)
                            continue;
                        tail.push_back(logChoose(selected, x) +
                                       logChoose(population - selected, selected - x) - denominator);
                    }
                    if (!tail.empty())
                    {
                        const double maximum = *std::max_element(tail.begin(), tail.end());
                        double sum = 0.0;
                        for (const double value : tail)
                            sum += std::exp(value - maximum);
                        replicationP = std::min(1.0, std::exp(maximum) * sum);
                    }
                }
                const bool replicationPass = previousAvailable && replicationP <= 0.01;
                pcAciTemporalReplicationStreak = replicationPass
                    ? pcAciTemporalReplicationStreak + 1 : 0;
                marginalLooStable = pcAciTemporalReplicationStreak >= 2;
                sdStabilityGate = marginalLooStable;
                sdReplicaTopAgreement = static_cast<double>(overlap) /
                    static_cast<double>(supportCount);

                marginalTopIndex = static_cast<size_t>(std::distance(
                    scored.begin(), std::max_element(scored.begin(), scored.end(),
                        [](const CandidateScore& a, const CandidateScore& b)
                        { return a.logScore < b.logScore; })));
                marginalLooTopIndices.assign(static_cast<size_t>(rc), marginalTopIndex);
                marginalLooSameBasin.assign(static_cast<size_t>(rc), 1);
                fullVsLooMaxLogBFShift = 0.0;

                pcAciPreviousTransportRank.clear();
                for (int s = 0; s < candidateCount; ++s)
                    pcAciPreviousTransportRank[temporalGridKey(scored[static_cast<size_t>(s)].point)] =
                        currentRank[static_cast<size_t>(s)];
                pcAciPreviousTopSupport = currentTopSupport;
                sdPreviousInferenceUpdateId = tadmSourceUpdateId;
                sdTemporalHistoryValid = true;

                GSL_INFO("PC-ACI A7 inverse-transport rank-channel update {}: events={}, hits={}, carriers={}, top10_overlap={}/{}, hypergeom_p={:.6g}, replication_pass={}, streak={}, mature={}, analytic_no_forward_sim=true",
                         tadmSourceUpdateId, eventCount, hitCount, candidateCount,
                         overlap, supportCount, replicationP, replicationPass,
                         pcAciTemporalReplicationStreak, marginalLooStable);
                if (!tadmDirectory.empty())
                {
                    std::ofstream profile(tadmDirectory + "/pc_aci_runtime_profile.csv", std::ios::out | std::ios::app);
                    if (profile.tellp() == 0)
                        profile << "run_uuid,source_update_id,sim_time,candidate_loop_wall_s,apply_total_wall_s,candidate_count,replica_count,physical_feature_count,temporal_window,marginal_loo_stable\n";
                    profile << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17)
                            << tadmSimTime << ',' << candidateLoopWallSeconds << ','
                            << std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count() << ','
                            << candidateCount << ',' << 0 << ',' << eventCount << ','
                            << (previousAvailable ? 1 : 0) << ',' << (marginalLooStable ? 1 : 0) << '\n';
                    profile.flush();
                }
                return finalizePcAciSequential();
            }
            const bool consecutiveEventWindow = sdTemporalHistoryValid &&
                sdPreviousInferenceUpdateId + 1 == tadmSourceUpdateId;
            sdTemporalDifferenceActive = consecutiveEventWindow;
            if (eventCount <= 0)
            {
                GSL_ERROR("PC-ACI event carrier has no raw events for source update {}", tadmSourceUpdateId);
                return false;
            }

            Eigen::MatrixXd eventMeans(candidateCount, eventCount);
            Eigen::MatrixXd eventWithin(candidateCount * rc, eventCount);
            Eigen::VectorXd bernoulliVariance = Eigen::VectorXd::Zero(eventCount);
            int eventSampleRow = 0;
            for (int s = 0; s < candidateCount; ++s)
            {
                const auto& bank = scored[static_cast<size_t>(s)].pcAciEventReplicaProbabilities;
                if (bank.size() != static_cast<size_t>(2 * rc))
                {
                    GSL_ERROR("PC-ACI event bank missing candidate {}", scored[static_cast<size_t>(s)].id);
                    return false;
                }
                eventMeans.row(s).setZero();
                for (int k = 0; k < rc; ++k)
                {
                    if (bank[static_cast<size_t>(k)].size() != static_cast<size_t>(eventCount))
                    {
                        GSL_ERROR("PC-ACI event vector length mismatch for candidate {} replica {}",
                                  scored[static_cast<size_t>(s)].id, k);
                        return false;
                    }
                    for (int j = 0; j < eventCount; ++j)
                    {
                        const double probability = bank[static_cast<size_t>(k)][static_cast<size_t>(j)];
                        eventMeans(s, j) += probability / static_cast<double>(rc);
                        bernoulliVariance(j) += probability * (1.0 - probability) /
                            static_cast<double>(candidateCount * rc);
                    }
                }
                for (int k = 0; k < rc; ++k, ++eventSampleRow)
                    for (int j = 0; j < eventCount; ++j)
                        eventWithin(eventSampleRow, j) =
                            bank[static_cast<size_t>(k)][static_cast<size_t>(j)] - eventMeans(s, j);
            }

            Eigen::MatrixXd eventTemporalCovariance =
                (eventWithin.transpose() * eventWithin) /
                static_cast<double>(std::max(1, eventSampleRow));
            eventTemporalCovariance.diagonal() += bernoulliVariance;
            const double eventScale = std::max(
                eventTemporalCovariance.trace() / static_cast<double>(eventCount), 1e-9);
            const double eventFloor = std::max(eventScale * 1e-6, 1e-9);
            eventTemporalCovariance.diagonal().array() += eventFloor;
            eventTemporalCovariance = 0.5 *
                (eventTemporalCovariance + eventTemporalCovariance.transpose());

            const Eigen::MatrixXd eventCentered =
                eventMeans.rowwise() - eventMeans.colwise().mean();
            Eigen::MatrixXd eventSourceCovariance =
                (eventCentered.transpose() * eventCentered) /
                static_cast<double>(std::max(1, candidateCount));
            eventSourceCovariance = 0.5 *
                (eventSourceCovariance + eventSourceCovariance.transpose());
            Eigen::GeneralizedSelfAdjointEigenSolver<Eigen::MatrixXd> eventSolver(
                eventSourceCovariance, eventTemporalCovariance);
            if (eventSolver.info() != Eigen::Success)
            {
                GSL_ERROR("PC-ACI event-channel generalized eigenproblem failed");
                return false;
            }

            std::vector<int> eligibleEventChannels;
            for (int index = eventCount - 1; index >= 0; --index)
            {
                const double eigenvalue = eventSolver.eigenvalues()(index);
                if (std::isfinite(eigenvalue) && eigenvalue > 1.0)
                    eligibleEventChannels.push_back(index);
            }
            if (eligibleEventChannels.empty())
            {
                pcAciNoIdentifiableChannel = true;
                marginalLooStable = false;
                for (auto& row : scored)
                {
                    row.logScore = 0.0;
                    for (double& value : row.replicaLogScores)
                        value = 0.0;
                }
                sdPreviousInferenceUpdateId = tadmSourceUpdateId;
                sdTemporalHistoryValid = true;
                GSL_WARN("PC-ACI event channel abstained update {}: events={}, leading_lambda={:.6f}",
                         tadmSourceUpdateId, eventCount, eventSolver.eigenvalues()(eventCount - 1));
                return finalizePcAciSequential();
            }

            const int eventChannelCount = std::min(
                {3, static_cast<int>(eligibleEventChannels.size()), std::max(1, rc - 1)});
            Eigen::MatrixXd eventChannels(eventCount, eventChannelCount);
            for (int channel = 0; channel < eventChannelCount; ++channel)
                eventChannels.col(channel) =
                    eventSolver.eigenvectors().col(eligibleEventChannels[static_cast<size_t>(channel)]);
            Eigen::MatrixXd eventLatentCovariance =
                eventChannels.transpose() * eventTemporalCovariance * eventChannels;
            eventLatentCovariance = 0.5 *
                (eventLatentCovariance + eventLatentCovariance.transpose());
            const double latentFloor = std::max(
                eventLatentCovariance.trace() /
                    static_cast<double>(eventChannelCount) * 1e-6,
                1e-9);
            eventLatentCovariance.diagonal().array() += latentFloor;
            Eigen::LDLT<Eigen::MatrixXd> eventLatentFactor(eventLatentCovariance);
            if (eventLatentFactor.info() != Eigen::Success ||
                (eventLatentFactor.vectorD().array() <= 0.0).any())
            {
                GSL_ERROR("PC-ACI event-channel latent covariance factorization failed");
                return false;
            }
            const Eigen::MatrixXd eventLatentInverse = eventLatentFactor.solve(
                Eigen::MatrixXd::Identity(eventChannelCount, eventChannelCount));
            const double eventLatentLogdet = eventLatentFactor.vectorD().array().log().sum();
            Eigen::VectorXd observedEvents(eventCount);
            for (int j = 0; j < eventCount; ++j)
                observedEvents(j) = pcAciActiveEvents[static_cast<size_t>(j)].hit;
            const Eigen::VectorXd observedEventChannel = eventChannels.transpose() * observedEvents;
            const double gaussianConstant =
                static_cast<double>(eventChannelCount) * std::log(2.0 * std::acos(-1.0));
            const auto logMeanExp = [](const std::vector<double>& values, int skip) -> double
            {
                double maximum = -std::numeric_limits<double>::infinity();
                int count = 0;
                for (int k = 0; k < static_cast<int>(values.size()); ++k)
                    if (k != skip && std::isfinite(values[static_cast<size_t>(k)]))
                    {
                        maximum = std::max(maximum, values[static_cast<size_t>(k)]);
                        ++count;
                    }
                if (count <= 0 || !std::isfinite(maximum))
                    return -std::numeric_limits<double>::infinity();
                double sum = 0.0;
                for (int k = 0; k < static_cast<int>(values.size()); ++k)
                    if (k != skip && std::isfinite(values[static_cast<size_t>(k)]))
                        sum += std::exp(values[static_cast<size_t>(k)] - maximum);
                return maximum + std::log(sum / static_cast<double>(count));
            };

            for (int s = 0; s < candidateCount; ++s)
            {
                std::vector<double> scoringScores;
                scoringScores.reserve(static_cast<size_t>(rc));
                const auto& bank = scored[static_cast<size_t>(s)].pcAciEventReplicaProbabilities;
                for (int k = rc; k < 2 * rc; ++k)
                {
                    const Eigen::VectorXd predicted = Eigen::Map<const Eigen::VectorXd>(
                        bank[static_cast<size_t>(k)].data(), eventCount);
                    const Eigen::VectorXd residual =
                        observedEventChannel - eventChannels.transpose() * predicted;
                    const double score = -0.5 *
                        (residual.dot(eventLatentInverse * residual) +
                         eventLatentLogdet + gaussianConstant);
                    scored[static_cast<size_t>(s)].replicaLogScores[static_cast<size_t>(k)] = score;
                    scoringScores.push_back(score);
                }
                scored[static_cast<size_t>(s)].logScore = logMeanExp(scoringScores, -1);
            }

            double scoreMaximum = -std::numeric_limits<double>::infinity();
            for (const auto& row : scored)
                scoreMaximum = std::max(scoreMaximum, row.logScore);
            double scoreSum = 0.0;
            for (const auto& row : scored)
                scoreSum += std::exp(row.logScore - scoreMaximum);
            const double scoreCenter = scoreMaximum +
                std::log(scoreSum / static_cast<double>(std::max(1, candidateCount)));
            for (auto& row : scored)
                row.logScore -= scoreCenter;

            std::vector<double> fullMarginal(static_cast<size_t>(candidateCount),
                                             -std::numeric_limits<double>::infinity());
            for (int s = 0; s < candidateCount; ++s)
            {
                const auto& allScores = scored[static_cast<size_t>(s)].replicaLogScores;
                const std::vector<double> scoring(allScores.begin() + rc, allScores.end());
                fullMarginal[static_cast<size_t>(s)] = logMeanExp(scoring, -1);
            }
            marginalTopIndex = static_cast<size_t>(std::distance(
                fullMarginal.begin(), std::max_element(fullMarginal.begin(), fullMarginal.end())));
            const auto sameSpatialBasin = [&](size_t a, size_t b)
            {
                if (a >= scored.size() || b >= scored.size())
                    return false;
                const auto& rectA = scored[a].rect;
                const auto& rectB = scored[b].rect;
                const double radiusA = 0.5 * std::sqrt(
                    static_cast<double>(std::max(1, rectA[2] * rectA[3]))) * measuredHitProb.metadata.cellSize;
                const double radiusB = 0.5 * std::sqrt(
                    static_cast<double>(std::max(1, rectB[2] * rectB[3]))) * measuredHitProb.metadata.cellSize;
                return std::hypot(
                    static_cast<double>(scored[a].point.x - scored[b].point.x),
                    static_cast<double>(scored[a].point.y - scored[b].point.y)) <=
                    radiusA + radiusB + measuredHitProb.metadata.cellSize;
            };
            marginalLooTopIndices.assign(static_cast<size_t>(rc),
                                         std::numeric_limits<size_t>::max());
            marginalLooSameBasin.assign(static_cast<size_t>(rc), 0);
            marginalLooStable = true;
            fullVsLooMaxLogBFShift = 0.0;
            for (int omitted = 0; omitted < rc; ++omitted)
            {
                size_t looTop = std::numeric_limits<size_t>::max();
                double looBest = -std::numeric_limits<double>::infinity();
                for (int s = 0; s < candidateCount; ++s)
                {
                    const auto& allScores = scored[static_cast<size_t>(s)].replicaLogScores;
                    const std::vector<double> scoring(allScores.begin() + rc, allScores.end());
                    const double loo = logMeanExp(scoring, omitted);
                    if (loo > looBest)
                    {
                        looBest = loo;
                        looTop = static_cast<size_t>(s);
                    }
                    if (std::isfinite(loo) && std::isfinite(fullMarginal[static_cast<size_t>(s)]))
                        fullVsLooMaxLogBFShift = std::max(
                            fullVsLooMaxLogBFShift,
                            std::abs(loo - fullMarginal[static_cast<size_t>(s)]));
                }
                marginalLooTopIndices[static_cast<size_t>(omitted)] = looTop;
                marginalLooSameBasin[static_cast<size_t>(omitted)] =
                    sameSpatialBasin(marginalTopIndex, looTop) ? 1 : 0;
                marginalLooStable = marginalLooStable &&
                    marginalLooSameBasin[static_cast<size_t>(omitted)] != 0;
            }
            int agreeingReplicas = 0;
            for (int k = rc; k < 2 * rc; ++k)
            {
                size_t replicaTop = 0;
                for (size_t s = 1; s < scored.size(); ++s)
                    if (scored[s].replicaLogScores[static_cast<size_t>(k)] >
                        scored[replicaTop].replicaLogScores[static_cast<size_t>(k)])
                        replicaTop = s;
                if (sameSpatialBasin(marginalTopIndex, replicaTop))
                    ++agreeingReplicas;
            }
            sdReplicaTopAgreement = static_cast<double>(agreeingReplicas) /
                static_cast<double>(rc);
            sdStabilityGate = sdReplicaTopAgreement > 0.5;
            sdPreviousInferenceUpdateId = tadmSourceUpdateId;
            sdTemporalHistoryValid = true;
            GSL_INFO("PC-ACI event-channel update {}: events={}, channels={}, leading_lambda={:.6f}, carriers={}, scoring_samples={}, top_agreement={:.3f}, loo_stable={}, raw_event_contract=true",
                     tadmSourceUpdateId, eventCount, eventChannelCount,
                     eventSolver.eigenvalues()(eventCount - 1), candidateCount, rc,
                     sdReplicaTopAgreement, marginalLooStable);
            if (!tadmDirectory.empty())
            {
                std::ofstream profile(tadmDirectory + "/pc_aci_runtime_profile.csv", std::ios::out | std::ios::app);
                if (profile.tellp() == 0)
                    profile << "run_uuid,source_update_id,sim_time,candidate_loop_wall_s,apply_total_wall_s,candidate_count,replica_count,physical_feature_count,temporal_window,marginal_loo_stable\n";
                profile << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17)
                        << tadmSimTime << ',' << candidateLoopWallSeconds << ','
                        << std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count() << ','
                        << candidateCount << ',' << rc << ',' << eventCount << ','
                        << (consecutiveEventWindow ? 1 : 0) << ',' << (marginalLooStable ? 1 : 0) << '\n';
                profile.flush();
            }
            return finalizePcAciSequential();
        }

        // PFDI protected likelihood.  The previous online block stopped at a
        // pooled within-replica covariance, so it never executed SD-TFEI's
        // source-contrast operator.  The shadow implementation now fits
        // C_s/C_eta from the calibration bank, solves the generalized
        // eigenproblem, protects the TADM span, and scores only on the fresh
        // scoring bank.
        const int p = static_cast<int>(support.size());
        const int replicaCount = tadmReplicas;
        const int covarianceCandidateCount = static_cast<int>(covarianceCandidateIndices.size());
        const int sampleCount = covarianceCandidateCount * replicaCount;
        Eigen::MatrixXd candidateMeans(covarianceCandidateCount, p);
        Eigen::MatrixXd within(sampleCount, p);
        int sampleRow = 0;
        for (int rowIndex = 0; rowIndex < covarianceCandidateCount; ++rowIndex)
        {
            const int s = covarianceCandidateIndices[static_cast<size_t>(rowIndex)];
            candidateMeans.row(rowIndex).setZero();
            for (int k = 0; k < replicaCount; ++k)
                for (int j = 0; j < p; ++j)
                    candidateMeans(rowIndex, j) += scored[static_cast<size_t>(s)].weightedReplicaLogits[static_cast<size_t>(k)][static_cast<size_t>(j)] / static_cast<double>(replicaCount);
            for (int k = 0; k < replicaCount; ++k, ++sampleRow)
                for (int j = 0; j < p; ++j)
                    within(sampleRow, j) = scored[static_cast<size_t>(s)].weightedReplicaLogits[static_cast<size_t>(k)][static_cast<size_t>(j)] - candidateMeans(rowIndex, j);
        }
        Eigen::MatrixXd empirical = (within.transpose() * within) / static_cast<double>(sampleCount);
        double covarianceMean = empirical.trace() / static_cast<double>(p);
        double covarianceSquareMean = empirical.squaredNorm() / static_cast<double>(p * p);
        double shrinkNumerator = covarianceSquareMean + covarianceMean * covarianceMean;
        double shrinkDenominator = (static_cast<double>(sampleCount) + 1.0) *
            (covarianceSquareMean - covarianceMean * covarianceMean / static_cast<double>(p));
        double shrinkage = shrinkDenominator <= 1e-12 ? 1.0 : std::min(shrinkNumerator / shrinkDenominator, 1.0);
        double covarianceFloor = std::max(covarianceMean * 1e-12, 1e-12);
        Eigen::MatrixXd transportCovariance = (1.0 - shrinkage) * empirical;
        transportCovariance.diagonal().array() += shrinkage * covarianceMean + covarianceFloor;

        if (pfdiMode == "tadm")
        {
            // TADM-only ablation aligned with the full-covariance reference:
            // transport covariance is retained as stochastic observation
            // noise, while the shared structural discrepancy is integrated in
            // the original weighted observation space.  Score the independent
            // scoring-bank mean once; do not log-mean-exp individual
            // realizations.
            const Eigen::MatrixXd baseCovariance = transportCovariance +
                                                    tadmPrior.sigma2 * Eigen::MatrixXd::Identity(p, p);
            Eigen::LDLT<Eigen::MatrixXd> baseFactor(baseCovariance);
            if (baseFactor.info() != Eigen::Success || (baseFactor.vectorD().array() <= 0.0).any())
            {
                GSL_ERROR("TADM-only full covariance factorization failed");
                return false;
            }
            const double logdetBase = baseFactor.vectorD().array().log().sum();
            Eigen::Matrix3d lambda;
            Eigen::Vector3d discrepancyMean;
            for (int i = 0; i < 3; ++i)
            {
                discrepancyMean(i) = tadmPrior.mu[static_cast<size_t>(i)];
                for (int j = 0; j < 3; ++j)
                    lambda(i, j) = tadmPrior.lambda[static_cast<size_t>(3 * i + j)];
            }
            Eigen::LDLT<Eigen::Matrix3d> lambdaFactor(lambda);
            if (lambdaFactor.info() != Eigen::Success || (lambdaFactor.vectorD().array() <= 0.0).any())
            {
                GSL_ERROR("TADM-only covariance factorization failed");
                return false;
            }
            const Eigen::Matrix3d lambdaInverse = lambdaFactor.solve(Eigen::Matrix3d::Identity());
            const double logdetLambda = lambdaFactor.vectorD().array().log().sum();
            Eigen::VectorXd observedWeighted(p);
            for (int j = 0; j < p; ++j)
                observedWeighted(j) = std::sqrt(weights[static_cast<size_t>(j)]) * observed[static_cast<size_t>(j)];
            for (int s = 0; s < candidateCount; ++s)
            {
                Eigen::MatrixXd weightedBasis(p, 3);
                Eigen::VectorXd scoringMean = Eigen::VectorXd::Zero(p);
                for (int j = 0; j < p; ++j)
                    for (int q = 0; q < 3; ++q)
                        weightedBasis(j, q) = scored[static_cast<size_t>(s)].weightedBasis[static_cast<size_t>(j)][static_cast<size_t>(q)];
                for (int k = replicaCount; k < 2 * replicaCount; ++k)
                    for (int j = 0; j < p; ++j)
                        scoringMean(j) += scored[static_cast<size_t>(s)].weightedReplicaLogits[static_cast<size_t>(k)][static_cast<size_t>(j)] /
                                          static_cast<double>(replicaCount);
                const Eigen::MatrixXd baseInverseBasis = baseFactor.solve(weightedBasis);
                const Eigen::Matrix3d woodbury = lambdaInverse + weightedBasis.transpose() * baseInverseBasis;
                Eigen::LDLT<Eigen::Matrix3d> woodburyFactor(woodbury);
                if (woodburyFactor.info() != Eigen::Success || (woodburyFactor.vectorD().array() <= 0.0).any())
                {
                    GSL_ERROR("TADM-only Woodbury factorization failed for candidate {}", scored[static_cast<size_t>(s)].id);
                    return false;
                }
                const double logdet = logdetBase + logdetLambda + woodburyFactor.vectorD().array().log().sum();
                const Eigen::VectorXd residual = observedWeighted - scoringMean - weightedBasis * discrepancyMean;
                const Eigen::VectorXd baseInverseResidual = baseFactor.solve(residual);
                const Eigen::Vector3d q = weightedBasis.transpose() * baseInverseResidual;
                const double quadratic = residual.dot(baseInverseResidual) - q.dot(woodburyFactor.solve(q));
                scored[static_cast<size_t>(s)].logScore = -0.5 * (quadratic + logdet + static_cast<double>(p) * std::log(2.0 * std::acos(-1.0)));
            }
            GSL_INFO("PFDI TADM-only full-covariance update {}: candidates={}, replicas={}, support={}",
                     tadmSourceUpdateId, scored.size(), tadmReplicas, p);
            return finalizeEvidence();
        }

        // Physics-consistent SD-TFEI arm.  The fixed-carrier variant uses a
        // low-dimensional physical latent state instead of the raw cell
        // logits.  This is the main-method likelihood: it retains the
        // source/temporal generalized eigenproblem, but makes the state
        // variables interpretable and lets the predictive covariance absorb
        // transport realization uncertainty.
        if ((pfdiMode == "sd" || pfdiMode == "al" || pfdiMode == "pc_aci") && persistentCarrierMode)
        {
            const int q = physicalFeatureCount;
            const int rc = replicaCount;
            const auto physicalInferenceBank = [&](int candidate) -> const auto&
            {
                const auto& row = scored[static_cast<size_t>(candidate)];
                return pfdiMode == "pc_aci"
                    ? row.physicalAbsoluteReplicaFeatures
                    : row.physicalReplicaFeatures;
            };
            if (temporalPhysicalWindow)
            {
                for (const auto& row : scored)
                    if (!row.physicalTemporalAvailable)
                    {
                        GSL_ERROR("SD-TFEI temporal physical bank missing candidate {}", row.id);
                        return false;
                    }
                GSL_INFO("PFDI SD-TFEI forecast-analysis increment: consecutive_update={}, previous_update={}, candidates={}, representation=sliced_wasserstein_transport_mixture",
                         tadmSourceUpdateId, sdPreviousInferenceUpdateId, candidateCount);
            }
            Eigen::MatrixXd physicalMeans(candidateCount, q);
            Eigen::MatrixXd physicalWithin(candidateCount * rc, q);
            int physicalSampleRow = 0;
            for (int s = 0; s < candidateCount; ++s)
            {
                physicalMeans.row(s).setZero();
                if (physicalInferenceBank(s).size() != static_cast<size_t>(2 * rc))
                {
                    GSL_ERROR("SD-TFEI physical latent bank missing candidate {}", scored[static_cast<size_t>(s)].id);
                    return false;
                }
                for (int k = 0; k < rc; ++k)
                    for (int d = 0; d < q; ++d)
                        physicalMeans(s, d) += physicalInferenceBank(s)[static_cast<size_t>(k)][static_cast<size_t>(d)] /
                            static_cast<double>(rc);
                for (int k = 0; k < rc; ++k, ++physicalSampleRow)
                    for (int d = 0; d < q; ++d)
                        physicalWithin(physicalSampleRow, d) =
                            physicalInferenceBank(s)[static_cast<size_t>(k)][static_cast<size_t>(d)] -
                            physicalMeans(s, d);
            }
            Eigen::MatrixXd physicalTemporalCovariance =
                (physicalWithin.transpose() * physicalWithin) /
                static_cast<double>(std::max(physicalSampleRow, 1));
            if (pfdiMode == "pc_aci" && temporalPhysicalWindow)
            {
                // Two-sample (Allan-style) temporal covariance: the absolute
                // source signature remains in C_s, while paired changes enter
                // only C_eta.  Only calibration replicas k < rc participate;
                // held-out scoring replicas remain prediction centers.
                Eigen::MatrixXd temporalInnovations = Eigen::MatrixXd::Zero(candidateCount * rc, q);
                int temporalRows = 0;
                const double inverseSqrtTwo = 1.0 / std::sqrt(2.0);
                for (int s = 0; s < candidateCount; ++s)
                {
                    const auto previousIt = sdPreviousPhysicalReplicaFeatures.find(
                        scored[static_cast<size_t>(s)].id);
                    if (previousIt == sdPreviousPhysicalReplicaFeatures.end() ||
                        previousIt->second.size() != static_cast<size_t>(2 * rc))
                        continue;
                    for (int k = 0; k < rc; ++k, ++temporalRows)
                        for (int d = 0; d < q; ++d)
                            temporalInnovations(temporalRows, d) = inverseSqrtTwo *
                                (scored[static_cast<size_t>(s)].physicalAbsoluteReplicaFeatures[static_cast<size_t>(k)][static_cast<size_t>(d)] -
                                 previousIt->second[static_cast<size_t>(k)][static_cast<size_t>(d)]);
                }
                if (temporalRows > 0)
                {
                    const Eigen::MatrixXd used = temporalInnovations.topRows(temporalRows);
                    physicalTemporalCovariance.noalias() +=
                        (used.transpose() * used) / static_cast<double>(temporalRows);
                }
            }
            physicalTemporalCovariance = 0.5 * (physicalTemporalCovariance + physicalTemporalCovariance.transpose());
            const double physicalMean = std::max(physicalTemporalCovariance.trace() / static_cast<double>(q), 1e-9);
            const double physicalFloor = std::max(physicalMean * 1e-6, 1e-9);
            physicalTemporalCovariance.diagonal().array() += physicalFloor;
            Eigen::MatrixXd physicalCentered = physicalMeans.rowwise() - physicalMeans.colwise().mean();
            Eigen::MatrixXd physicalSourceCovariance =
                (physicalCentered.transpose() * physicalCentered) /
                static_cast<double>(std::max(candidateCount, 1));
            physicalSourceCovariance = 0.5 * (physicalSourceCovariance + physicalSourceCovariance.transpose());
            Eigen::GeneralizedSelfAdjointEigenSolver<Eigen::MatrixXd> physicalSolver(
                physicalSourceCovariance, physicalTemporalCovariance);
            if (physicalSolver.info() != Eigen::Success)
            {
                GSL_ERROR("SD-TFEI physical latent generalized eigenproblem failed");
                return false;
            }
            std::vector<int> physicalEligible;
            double physicalEigenSum = 0.0;
            double physicalEigenSquareSum = 0.0;
            for (int eigenIndex = q - 1; eigenIndex >= 0; --eigenIndex)
            {
                const double eigenvalue = physicalSolver.eigenvalues()(eigenIndex);
                if (std::isfinite(eigenvalue) && eigenvalue > 1.0)
                {
                    physicalEligible.push_back(eigenIndex);
                    physicalEigenSum += eigenvalue;
                    physicalEigenSquareSum += eigenvalue * eigenvalue;
                }
            }
            if (physicalEligible.empty())
            {
                if (pfdiMode != "pc_aci")
                {
                    GSL_ERROR("SD-TFEI physical latent identifiability gate failed: no lambda > 1 channel");
                    return false;
                }
                // Absence of an identifiable source-over-temporal channel is
                // evidence of ignorance, not a process failure.  Emit a
                // neutral likelihood, hold the independent causal state and
                // native posterior, and advance only the temporal history so
                // a later informative window can be assessed.
                pcAciNoIdentifiableChannel = true;
                marginalLooStable = false;
                sdTemporalDifferenceActive = temporalPhysicalWindow;
                for (auto& row : scored)
                {
                    row.logScore = 0.0;
                    for (double& value : row.replicaLogScores)
                        value = 0.0;
                }
                sdPreviousObservedField.assign(measuredHitProb.data.size(), 0.0f);
                sdPreviousObserved.assign(measuredHitProb.data.size(), 0.0);
                sdPreviousSupportMask.assign(measuredHitProb.data.size(), 0);
                for (size_t cell = 0; cell < measuredHitProb.data.size(); ++cell)
                    sdPreviousObservedField[cell] = static_cast<float>(std::max(
                        static_cast<double>(measuredHitProb.data[cell].probability()), 0.0));
                for (size_t cell : support)
                {
                    sdPreviousObserved[cell] = std::sqrt(std::max(
                        static_cast<double>(measuredHitProb.data[cell].confidence), 0.0)) *
                        tadmLogit(static_cast<double>(measuredHitProb.data[cell].probability()));
                    sdPreviousSupportMask[cell] = 1;
                }
                sdPreviousPhysicalReplicaFeatures.clear();
                for (const auto& row : scored)
                {
                    std::vector<std::vector<double>> bank;
                    bank.reserve(row.physicalAbsoluteReplicaFeatures.size());
                    for (const auto& feature : row.physicalAbsoluteReplicaFeatures)
                        bank.emplace_back(feature.begin(), feature.end());
                    sdPreviousPhysicalReplicaFeatures.emplace(row.id, std::move(bank));
                }
                sdPreviousInferenceUpdateId = tadmSourceUpdateId;
                sdTemporalHistoryValid = true;
                GSL_WARN("PC-ACI abstained update {}: no lambda > 1 channel, leading_lambda={:.6f}; causal state held and temporal history advanced",
                         tadmSourceUpdateId, physicalSolver.eigenvalues()(q - 1));
                if (!tadmDirectory.empty())
                {
                    const auto now = std::chrono::steady_clock::now();
                    std::ofstream profile(tadmDirectory + "/pc_aci_runtime_profile.csv", std::ios::out | std::ios::app);
                    if (profile.tellp() == 0)
                        profile << "run_uuid,source_update_id,sim_time,candidate_loop_wall_s,apply_total_wall_s,candidate_count,replica_count,physical_feature_count,temporal_window,marginal_loo_stable\n";
                    profile << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17) << tadmSimTime << ','
                            << candidateLoopWallSeconds << ',' << std::chrono::duration<double>(now - start).count() << ','
                            << candidateCount << ',' << rc << ',' << physicalFeatureCount << ','
                            << (temporalPhysicalWindow ? 1 : 0) << ",0\n";
                }
                if (!finalizePcAciSequential())
                    return false;
                return true;
            }
            const double physicalParticipation = physicalEigenSquareSum > 0.0
                ? (physicalEigenSum * physicalEigenSum) / physicalEigenSquareSum
                : 1.0;
            const int physicalRankCap = std::max(1, rc - 1);
            const int physicalChannelCount = std::clamp(
                static_cast<int>(std::ceil(physicalParticipation)), 1,
                std::min(static_cast<int>(physicalEligible.size()), physicalRankCap));
            Eigen::MatrixXd physicalChannels(q, physicalChannelCount);
            for (int c = 0; c < physicalChannelCount; ++c)
                physicalChannels.col(c) = physicalSolver.eigenvectors().col(physicalEligible[static_cast<size_t>(c)]);
            const Eigen::MatrixXd globalLatentCovariance =
                physicalChannels.transpose() * physicalTemporalCovariance * physicalChannels;
            const double globalLatentTrace = std::max(globalLatentCovariance.trace(), 1e-9);
            const double latentFloor = std::max(globalLatentTrace * 1e-6, 1e-9);
            const double latentShrinkage = std::clamp(
                static_cast<double>(physicalChannelCount) /
                static_cast<double>(physicalChannelCount + std::max(1, rc - 1)), 0.0, 1.0);
            std::vector<Eigen::MatrixXd> latentInverse(static_cast<size_t>(candidateCount));
            std::vector<double> latentLogdet(static_cast<size_t>(candidateCount), 0.0);
            Eigen::MatrixXd pcAciPooledInverse;
            double pcAciPooledLogdet = 0.0;
            if (pfdiMode == "pc_aci")
            {
                Eigen::MatrixXd pooledCovariance = 0.5 *
                    (globalLatentCovariance + globalLatentCovariance.transpose());
                pooledCovariance.diagonal().array() += latentFloor;
                Eigen::LDLT<Eigen::MatrixXd> pooledFactor(pooledCovariance);
                if (pooledFactor.info() != Eigen::Success || (pooledFactor.vectorD().array() <= 0.0).any())
                {
                    GSL_ERROR("PC-ACI pooled calibration covariance factorization failed");
                    return false;
                }
                pcAciPooledInverse = pooledFactor.solve(
                    Eigen::MatrixXd::Identity(physicalChannelCount, physicalChannelCount));
                pcAciPooledLogdet = pooledFactor.vectorD().array().log().sum();
            }
            for (int s = 0; s < candidateCount; ++s)
            {
                if (pfdiMode == "pc_aci")
                {
                    // The scoring bank supplies predictive mixture centers
                    // only.  Its dispersion cannot leak back into covariance
                    // estimation; all candidates share the calibration-only
                    // nuisance covariance.
                    latentInverse[static_cast<size_t>(s)] = pcAciPooledInverse;
                    latentLogdet[static_cast<size_t>(s)] = pcAciPooledLogdet;
                }
                else
                {
                    std::vector<Eigen::VectorXd> scoringLatent;
                    scoringLatent.reserve(static_cast<size_t>(rc));
                    Eigen::VectorXd scoringMean = Eigen::VectorXd::Zero(physicalChannelCount);
                    for (int k = rc; k < 2 * rc; ++k)
                    {
                        Eigen::VectorXd feature(q);
                        for (int d = 0; d < q; ++d)
                            feature(d) = physicalInferenceBank(s)[static_cast<size_t>(k)][static_cast<size_t>(d)];
                        scoringLatent.push_back(physicalChannels.transpose() * feature);
                        scoringMean += scoringLatent.back() / static_cast<double>(rc);
                    }
                    Eigen::MatrixXd covariance = Eigen::MatrixXd::Zero(physicalChannelCount, physicalChannelCount);
                    for (const Eigen::VectorXd& value : scoringLatent)
                    {
                        const Eigen::VectorXd centered = value - scoringMean;
                        covariance.noalias() += centered * centered.transpose();
                    }
                    covariance /= static_cast<double>(std::max(1, rc - 1));
                    covariance = (1.0 - latentShrinkage) * covariance + latentShrinkage * globalLatentCovariance;
                    covariance = 0.5 * (covariance + covariance.transpose());
                    covariance.diagonal().array() += latentFloor;
                    Eigen::LDLT<Eigen::MatrixXd> factor(covariance);
                    if (factor.info() != Eigen::Success || (factor.vectorD().array() <= 0.0).any())
                    {
                        GSL_ERROR("SD-TFEI physical latent covariance factorization failed for candidate {}", scored[static_cast<size_t>(s)].id);
                        return false;
                    }
                    latentInverse[static_cast<size_t>(s)] = factor.solve(Eigen::MatrixXd::Identity(physicalChannelCount, physicalChannelCount));
                    latentLogdet[static_cast<size_t>(s)] = factor.vectorD().array().log().sum();
                }
                const Eigen::VectorXd observedLatent = Eigen::Map<const Eigen::VectorXd>(
                    scored[static_cast<size_t>(s)].observedPhysicalFeatures.data(), q);
                const Eigen::VectorXd observedChannel = physicalChannels.transpose() * observedLatent;
                // Transport realizations are a latent nuisance variable.  A
                // single Gaussian around their mean can invent a mode that
                // no realization actually supports, so the predictive
                // likelihood marginalizes the disjoint scoring bank with a
                // log-mean-exp mixture.  Calibration determines covariance;
                // scoring replicas only provide held-out predictive centers.
                const auto predictiveLogScore = [&](const std::array<double, physicalFeatureCount>& featureArray)
                {
                    const Eigen::VectorXd feature = Eigen::Map<const Eigen::VectorXd>(featureArray.data(), q);
                    const Eigen::VectorXd predictiveCenter = physicalChannels.transpose() * feature;
                    const Eigen::VectorXd residual = observedChannel - predictiveCenter;
                    return -0.5 *
                        (residual.dot(latentInverse[static_cast<size_t>(s)] * residual) +
                         latentLogdet[static_cast<size_t>(s)] +
                         static_cast<double>(physicalChannelCount) * std::log(2.0 * std::acos(-1.0)));
                };
                const auto stableLogMeanExp = [](const std::vector<double>& values)
                {
                    if (values.empty())
                        return -std::numeric_limits<double>::infinity();
                    const double maximum = *std::max_element(values.begin(), values.end());
                    double sum = 0.0;
                    for (const double value : values)
                        sum += std::exp(value - maximum);
                    return maximum + std::log(sum / static_cast<double>(values.size()));
                };
                std::vector<double> mixtureLogScores;
                mixtureLogScores.reserve(static_cast<size_t>(rc) * (pfdiMode == "pc_aci" ? phaseOffsets.size() : 1));
                for (int k = rc; k < 2 * rc; ++k)
                {
                    if (pfdiMode == "pc_aci")
                    {
                        const auto& phaseFeatures = scored[static_cast<size_t>(s)].physicalPhaseReplicaFeatures[static_cast<size_t>(k)];
                        for (const auto& feature : phaseFeatures)
                            mixtureLogScores.push_back(predictiveLogScore(feature));
                    }
                    else
                    {
                        mixtureLogScores.push_back(
                            predictiveLogScore(physicalInferenceBank(s)[static_cast<size_t>(k)]));
                    }
                }
                scored[static_cast<size_t>(s)].logScore = stableLogMeanExp(mixtureLogScores);
                // Export the same predictive physical-latent density for
                // each held-out scoring replica.  The finalizer uses these
                // disjoint scores to construct its truth-blind trust budget;
                // leaving them empty would turn a valid predictive bank into
                // an artificial support fallback.
                for (int k = rc; k < 2 * rc; ++k)
                {
                    // A held-out replica score must be a predictive score for
                    // the observation under that realization.  Scoring
                    // feature-minus-scoringMean only measures how typical a
                    // realization is within its own candidate bank and is
                    // independent of the observation; it makes
                    // top_agreement a bank-dispersion diagnostic rather than
                    // a truth-blind evidence-ordering test.
                    if (pfdiMode == "pc_aci")
                    {
                        std::vector<double> phaseLogScores;
                        phaseLogScores.reserve(phaseOffsets.size());
                        const auto& phaseFeatures = scored[static_cast<size_t>(s)].physicalPhaseReplicaFeatures[static_cast<size_t>(k)];
                        for (const auto& feature : phaseFeatures)
                            phaseLogScores.push_back(predictiveLogScore(feature));
                        scored[static_cast<size_t>(s)].replicaLogScores[static_cast<size_t>(k)] =
                            stableLogMeanExp(phaseLogScores);
                    }
                    else
                    {
                        scored[static_cast<size_t>(s)].replicaLogScores[static_cast<size_t>(k)] =
                            predictiveLogScore(physicalInferenceBank(s)[static_cast<size_t>(k)]);
                    }
                }
            }
            // Optional runtime-parity artifact.  It is disabled for normal
            // closed-loop runs because it is intentionally verbose; when
            // enabled it records the exact held-out carrier, replica,
            // physical feature vector and predictive log score needed for a
            // before/after semantics check.
            if (std::getenv("PFDI_RUNTIME_PARITY_EXPORT") != nullptr && !tadmDirectory.empty())
            {
                std::ofstream parity(tadmDirectory + "/pc_aci_runtime_parity.csv", std::ios::out | std::ios::trunc);
                parity << "source_update_id,candidate_id,replica_id,x,y";
                for (int d = 0; d < q; ++d)
                    parity << ",physical_feature_" << d;
                parity << ",log_score\n";
                for (int s = 0; s < candidateCount; ++s)
                    for (int k = rc; k < 2 * rc; ++k)
                    {
                        parity << tadmSourceUpdateId << ',' << scored[static_cast<size_t>(s)].id << ','
                               << (k - rc) << ',' << std::setprecision(17)
                               << scored[static_cast<size_t>(s)].point.x << ','
                               << scored[static_cast<size_t>(s)].point.y;
                        for (int d = 0; d < q; ++d)
                            parity << ',' << physicalInferenceBank(s)[static_cast<size_t>(k)][static_cast<size_t>(d)];
                        parity << ',' << scored[static_cast<size_t>(s)].replicaLogScores[static_cast<size_t>(k)] << '\n';
                    }
                parity.flush();
            }
            if (pfdiMode == "al")
            {
                // Accuracy-localized TADM: the calibration half estimates a
                // carrier-specific mismatch scale, while the scoring half
                // supplies a disjoint predictive mismatch.  The global
                // robust scale only fixes units; it is estimated from the
                // frozen bank and is not a House/seed tuning knob.
                std::vector<double> allCalibrationMismatch;
                allCalibrationMismatch.reserve(static_cast<size_t>(candidateCount * rc));
                std::vector<double> candidateMismatch(static_cast<size_t>(candidateCount), INFINITY);
                std::vector<double> candidateVariance(static_cast<size_t>(candidateCount), INFINITY);
                for (int s = 0; s < candidateCount; ++s)
                {
                    if (scored[static_cast<size_t>(s)].phaseTadmLogScores.size() != static_cast<size_t>(2 * rc))
                        continue;
                    std::vector<double> calibrationMismatch;
                    calibrationMismatch.reserve(static_cast<size_t>(rc));
                    for (int k = 0; k < rc; ++k)
                    {
                        const double mismatch = -scored[static_cast<size_t>(s)].phaseTadmLogScores[static_cast<size_t>(k)];
                        calibrationMismatch.push_back(mismatch);
                        allCalibrationMismatch.push_back(mismatch);
                    }
                    std::sort(calibrationMismatch.begin(), calibrationMismatch.end());
                    const double center = calibrationMismatch[calibrationMismatch.size() / 2];
                    std::vector<double> deviations;
                    deviations.reserve(calibrationMismatch.size());
                    for (const double mismatch : calibrationMismatch)
                        deviations.push_back(std::abs(mismatch - center));
                    std::sort(deviations.begin(), deviations.end());
                    const double mad = deviations[deviations.size() / 2];
                    double scoringMismatch = 0.0;
                    for (int k = rc; k < 2 * rc; ++k)
                        scoringMismatch -= scored[static_cast<size_t>(s)].phaseTadmLogScores[static_cast<size_t>(k)] /
                            static_cast<double>(rc);
                    candidateMismatch[static_cast<size_t>(s)] = scoringMismatch;
                    candidateVariance[static_cast<size_t>(s)] = std::max(mad * mad, 1.0);
                }
                if (!allCalibrationMismatch.empty())
                {
                    std::sort(allCalibrationMismatch.begin(), allCalibrationMismatch.end());
                    const double globalScale = std::max(allCalibrationMismatch[allCalibrationMismatch.size() / 2], 1.0);
                    for (int s = 0; s < candidateCount; ++s)
                        if (std::isfinite(candidateMismatch[static_cast<size_t>(s)]) &&
                            std::isfinite(candidateVariance[static_cast<size_t>(s)]))
                            scored[static_cast<size_t>(s)].logScore =
                                -candidateMismatch[static_cast<size_t>(s)] / globalScale -
                                0.5 * std::log(candidateVariance[static_cast<size_t>(s)]);
                    GSL_INFO("PFDI AL-TADM accuracy-localized update {}: carriers={}, global_mismatch_scale={:.6f}, phase_grid=transport_horizon_five_point, factor_pure=true",
                             tadmSourceUpdateId, candidateCount, globalScale);
                }
            }
            double physicalMax = -INFINITY;
            int physicalFinite = 0;
            for (const auto& row : scored)
                if (std::isfinite(row.logScore))
                {
                    physicalMax = std::max(physicalMax, row.logScore);
                    ++physicalFinite;
                }
            if (!(physicalFinite > 0) || !std::isfinite(physicalMax))
            {
                GSL_ERROR("SD-TFEI physical latent produced no finite candidate score");
                return false;
            }
            double physicalExpSum = 0.0;
            for (const auto& row : scored)
                if (std::isfinite(row.logScore))
                    physicalExpSum += std::exp(row.logScore - physicalMax);
            const double physicalLogMean = physicalMax + std::log(physicalExpSum / static_cast<double>(physicalFinite));
            for (auto& row : scored)
                if (std::isfinite(row.logScore))
                    row.logScore -= physicalLogMean;

            // Marginal-evidence leave-one-replica-out stability.  This is
            // the inference-consistent replacement for the old majority of
            // individual-replica argmaxes.  It uses only the disjoint scoring
            // bank and therefore remains truth blind.
            const auto logMeanExp = [](const std::vector<double>& values, int skip) -> double
            {
                double maximum = -INFINITY;
                int count = 0;
                for (int k = 0; k < static_cast<int>(values.size()); ++k)
                {
                    if (k == skip || !std::isfinite(values[static_cast<size_t>(k)]))
                        continue;
                    maximum = std::max(maximum, values[static_cast<size_t>(k)]);
                    ++count;
                }
                if (count <= 0 || !std::isfinite(maximum))
                    return -INFINITY;
                double sum = 0.0;
                for (int k = 0; k < static_cast<int>(values.size()); ++k)
                {
                    if (k == skip || !std::isfinite(values[static_cast<size_t>(k)]))
                        continue;
                    sum += std::exp(values[static_cast<size_t>(k)] - maximum);
                }
                return maximum + std::log(sum / static_cast<double>(count));
            };
            std::vector<double> fullMarginal(static_cast<size_t>(candidateCount), -INFINITY);
            for (int s = 0; s < candidateCount; ++s)
            {
                const auto& replicaScores = scored[static_cast<size_t>(s)].replicaLogScores;
                if (replicaScores.size() == static_cast<size_t>(2 * rc))
                {
                    std::vector<double> scoringScores(replicaScores.begin() + rc, replicaScores.end());
                    fullMarginal[static_cast<size_t>(s)] = logMeanExp(scoringScores, -1);
                }
            }
            marginalTopIndex = std::numeric_limits<size_t>::max();
            for (size_t s = 0; s < fullMarginal.size(); ++s)
                if (std::isfinite(fullMarginal[s]) &&
                    (marginalTopIndex == std::numeric_limits<size_t>::max() ||
                     fullMarginal[s] > fullMarginal[marginalTopIndex]))
                    marginalTopIndex = s;
            marginalLooTopIndices.assign(static_cast<size_t>(rc), std::numeric_limits<size_t>::max());
            marginalLooSameBasin.assign(static_cast<size_t>(rc), 0);
            fullVsLooMaxLogBFShift = 0.0;
            const auto sameSpatialBasin = [&](size_t a, size_t b)
            {
                if (a == std::numeric_limits<size_t>::max() || b == std::numeric_limits<size_t>::max())
                    return false;
                const auto& rectA = scored[a].rect;
                const auto& rectB = scored[b].rect;
                const double radiusA = 0.5 * std::sqrt(static_cast<double>(std::max(1, rectA[2] * rectA[3]))) * measuredHitProb.metadata.cellSize;
                const double radiusB = 0.5 * std::sqrt(static_cast<double>(std::max(1, rectB[2] * rectB[3]))) * measuredHitProb.metadata.cellSize;
                const double basinRadius = radiusA + radiusB + measuredHitProb.metadata.cellSize;
                return std::hypot(static_cast<double>(scored[a].point.x - scored[b].point.x),
                                  static_cast<double>(scored[a].point.y - scored[b].point.y)) <= basinRadius;
            };
            if (marginalTopIndex != std::numeric_limits<size_t>::max())
            {
                bool allStable = true;
                for (int omitted = 0; omitted < rc; ++omitted)
                {
                    size_t looTop = std::numeric_limits<size_t>::max();
                    double looBest = -INFINITY;
                    for (int s = 0; s < candidateCount; ++s)
                    {
                        const auto& replicaScores = scored[static_cast<size_t>(s)].replicaLogScores;
                        if (replicaScores.size() != static_cast<size_t>(2 * rc))
                            continue;
                        const std::vector<double> scoringScores(replicaScores.begin() + rc, replicaScores.end());
                        const double loo = logMeanExp(scoringScores, omitted);
                        if (std::isfinite(loo) && loo > looBest)
                        {
                            looBest = loo;
                            looTop = static_cast<size_t>(s);
                        }
                        if (std::isfinite(loo) && std::isfinite(fullMarginal[static_cast<size_t>(s)]))
                            fullVsLooMaxLogBFShift = std::max(
                                fullVsLooMaxLogBFShift,
                                std::abs(loo - fullMarginal[static_cast<size_t>(s)]));
                    }
                    marginalLooTopIndices[static_cast<size_t>(omitted)] = looTop;
                    marginalLooSameBasin[static_cast<size_t>(omitted)] = sameSpatialBasin(marginalTopIndex, looTop) ? 1 : 0;
                    allStable = allStable && marginalLooSameBasin[static_cast<size_t>(omitted)] != 0;
                }
                marginalLooStable = allStable;
            }
            size_t aggregateTop = 0;
            for (size_t s = 1; s < scored.size(); ++s)
                if (scored[s].logScore > scored[aggregateTop].logScore)
                    aggregateTop = s;
            int agreeingReplicas = 0;
            for (int k = rc; k < 2 * rc; ++k)
            {
                size_t replicaTop = aggregateTop;
                double replicaBest = -INFINITY;
                for (int s = 0; s < candidateCount; ++s)
                {
                    // For PC-ACI this is already the observation-predictive
                    // score marginalized over the complete transport-phase
                    // state space for replica k.  Recomputing it from the
                    // zero-phase anchor would make the stability gate test a
                    // different likelihood from the one that moves posterior.
                    double score = scored[static_cast<size_t>(s)].replicaLogScores[static_cast<size_t>(k)];
                    if (pfdiMode != "pc_aci")
                    {
                        Eigen::VectorXd feature(q);
                        for (int d = 0; d < q; ++d)
                            feature(d) = physicalInferenceBank(s)[static_cast<size_t>(k)][static_cast<size_t>(d)];
                        const Eigen::VectorXd observedFeature = Eigen::Map<const Eigen::VectorXd>(
                            scored[static_cast<size_t>(s)].observedPhysicalFeatures.data(), q);
                        const Eigen::VectorXd observedChannel = physicalChannels.transpose() * observedFeature;
                        const Eigen::VectorXd residual = observedChannel - physicalChannels.transpose() * feature;
                        score = -0.5 *
                            (residual.dot(latentInverse[static_cast<size_t>(s)] * residual) +
                             latentLogdet[static_cast<size_t>(s)] +
                             static_cast<double>(physicalChannelCount) * std::log(2.0 * std::acos(-1.0)));
                    }
                    if (score > replicaBest)
                    {
                        replicaBest = score;
                        replicaTop = static_cast<size_t>(s);
                    }
                }
                const auto& aggregateRect = scored[aggregateTop].rect;
                const auto& replicaRect = scored[replicaTop].rect;
                const double aggregateRadius = 0.5 * std::sqrt(static_cast<double>(std::max(1, aggregateRect[2] * aggregateRect[3]))) * measuredHitProb.metadata.cellSize;
                const double replicaRadius = 0.5 * std::sqrt(static_cast<double>(std::max(1, replicaRect[2] * replicaRect[3]))) * measuredHitProb.metadata.cellSize;
                const double basinRadius = aggregateRadius + replicaRadius + measuredHitProb.metadata.cellSize;
                if (std::hypot(static_cast<double>(scored[replicaTop].point.x - scored[aggregateTop].point.x),
                               static_cast<double>(scored[replicaTop].point.y - scored[aggregateTop].point.y)) <= basinRadius)
                    ++agreeingReplicas;
            }
            sdReplicaTopAgreement = static_cast<double>(agreeingReplicas) / static_cast<double>(rc);
            sdStabilityGate = sdReplicaTopAgreement > 0.5;
            // The physical carrier has its own forecast--analysis increment
            // path.  Mark it explicitly so finalizeEvidence can use the
            // held-out replica agreement on the second consecutive window,
            // rather than silently falling back to the absolute-window basin
            // continuity heuristic.
            sdTemporalDifferenceActive = temporalPhysicalWindow;
            GSL_INFO("PFDI SD-TFEI physical-latent update {}: channels={}, replica_rank_cap={}, participation_ratio={:.3f}, leading_lambda={:.6f}, carriers={}, scoring_samples={}, top_agreement={:.3f}, factor_pure=true",
                     tadmSourceUpdateId, physicalChannelCount, physicalRankCap, physicalParticipation,
                     physicalSolver.eigenvalues()(q - 1), candidateCount, rc, sdReplicaTopAgreement);
            if (!tadmDirectory.empty())
            {
                const auto now = std::chrono::steady_clock::now();
                std::ofstream profile(tadmDirectory + "/pc_aci_runtime_profile.csv", std::ios::out | std::ios::app);
                if (profile.tellp() == 0)
                    profile << "run_uuid,source_update_id,sim_time,candidate_loop_wall_s,apply_total_wall_s,candidate_count,replica_count,physical_feature_count,temporal_window,marginal_loo_stable\n";
                profile << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17) << tadmSimTime << ','
                        << candidateLoopWallSeconds << ',' << std::chrono::duration<double>(now - start).count() << ','
                        << candidateCount << ',' << rc << ',' << physicalFeatureCount << ','
                        << (temporalPhysicalWindow ? 1 : 0) << ',' << (marginalLooStable ? 1 : 0) << '\n';
            }
            if (pfdiMode == "sd" || pfdiMode == "pc_aci")
            {
                sdPreviousObservedField.assign(measuredHitProb.data.size(), 0.0f);
                sdPreviousObserved.assign(measuredHitProb.data.size(), 0.0);
                sdPreviousSupportMask.assign(measuredHitProb.data.size(), 0);
                for (size_t cell = 0; cell < measuredHitProb.data.size(); ++cell)
                    sdPreviousObservedField[cell] = static_cast<float>(std::max(
                        static_cast<double>(measuredHitProb.data[cell].probability()), 0.0));
                for (size_t cell : support)
                {
                    sdPreviousObserved[cell] = std::sqrt(std::max(
                        static_cast<double>(measuredHitProb.data[cell].confidence), 0.0)) *
                        tadmLogit(static_cast<double>(measuredHitProb.data[cell].probability()));
                    sdPreviousSupportMask[cell] = 1;
                }
                sdPreviousPhysicalReplicaFeatures.clear();
                for (const auto& row : scored)
                {
                    std::vector<std::vector<double>> bank;
                    bank.reserve(row.physicalReplicaFeatures.size());
                    // Commit the absolute state, never the current
                    // forecast--analysis increment.  Otherwise the next
                    // update subtracts a previous increment rather than the
                    // previous physical realization.
                    for (const auto& feature : row.physicalAbsoluteReplicaFeatures)
                        bank.emplace_back(feature.begin(), feature.end());
                    sdPreviousPhysicalReplicaFeatures.emplace(row.id, std::move(bank));
                }
                sdPreviousInferenceUpdateId = tadmSourceUpdateId;
                sdTemporalHistoryValid = true;
            GSL_INFO("PFDI SD-TFEI physical history commit: candidates={}, representation=observed_field_plus_sliced_wasserstein_features",
                     sdPreviousPhysicalReplicaFeatures.size());
            }
            if (pfdiMode == "pc_aci")
            {
                if (!finalizePcAciSequential())
                    return false;
                return true;
            }
            return finalizeEvidence();
        }

        // For SD-TFEI, a first-difference window removes persistent
        // transport/model structure before the source-contrast operator is
        // formed.  This is only enabled when the immediately preceding
        // window contains the same stable candidate IDs; otherwise the first
        // window remains the absolute diagnostic defined by the frozen arm.
        bool sdUseTemporalDifference = false;
        Eigen::VectorXd sdObservedWeighted;
        Eigen::MatrixXd sdCandidateMeans = candidateMeans;
        Eigen::MatrixXd sdWithin = within;
        int sdTrainingCandidateCount = covarianceCandidateCount;
        if (pfdiMode == "sd" && !persistentCarrierMode && sdTemporalHistoryValid &&
            sdPreviousInferenceUpdateId + 1 == tadmSourceUpdateId &&
            sdPreviousObserved.size() == measuredHitProb.data.size() &&
            sdPreviousSupportMask.size() == measuredHitProb.data.size())
        {
            std::vector<int> overlap;
            overlap.reserve(scored.size());
            size_t nativeAnchorOverlap = 0;
            size_t commonSupportCount = 0;
            for (size_t cell = 0; cell < measuredHitProb.data.size(); ++cell)
                if (sdPreviousSupportMask[cell] && measuredHitProb.occupancy[cell] == Occupancy::Free)
                    ++commonSupportCount;
            for (int s = 0; s < candidateCount; ++s)
            {
                if (!sdComputeCandidate[static_cast<size_t>(s)])
                    continue;
                const auto* previous = previousReplicasFor(scored[static_cast<size_t>(s)]);
                if (previous != nullptr &&
                    (previous->size() == static_cast<size_t>(2 * replicaCount) || previous->size() == 1))
                {
                    overlap.push_back(s);
                    if (previous->size() == 1)
                        ++nativeAnchorOverlap;
                }
            }
            // Two channel covariance requires at least three candidate
            // trajectories for a meaningful source contrast.  If the bank
            // overlap is smaller, keep the absolute diagnostic rather than
            // inventing a temporal difference for new quadtree leaves.
            if (overlap.size() >= 3 && commonSupportCount >= 3)
            {
                sdUseTemporalDifference = true;
                sdTemporalDifferenceActive = true;
                sdTrainingCandidateCount = static_cast<int>(overlap.size());
                sdCandidateMeans.resize(sdTrainingCandidateCount, p);
                sdWithin.resize(sdTrainingCandidateCount * replicaCount, p);
                sdObservedWeighted.resize(p);
                for (int j = 0; j < p; ++j)
                {
                    const size_t cell = support[static_cast<size_t>(j)];
                    sdObservedWeighted(j) = sdPreviousSupportMask[cell]
                        ? std::sqrt(weights[static_cast<size_t>(j)]) * observed[static_cast<size_t>(j)] - sdPreviousObserved[cell]
                        : 0.0;
                }
                int temporalRow = 0;
                for (int row = 0; row < sdTrainingCandidateCount; ++row)
                {
                    const int s = overlap[static_cast<size_t>(row)];
                    const auto* previous = previousReplicasFor(scored[static_cast<size_t>(s)]);
                    if (previous == nullptr)
                    {
                        GSL_ERROR("SD-TFEI temporal registration lost candidate {}", scored[static_cast<size_t>(s)].id);
                        return false;
                    }
                    sdCandidateMeans.row(row).setZero();
                    for (int k = 0; k < replicaCount; ++k)
                        for (int j = 0; j < p; ++j)
                        {
                            const size_t cell = support[static_cast<size_t>(j)];
                            const double delta = sdPreviousSupportMask[cell]
                                ? scored[static_cast<size_t>(s)].weightedReplicaLogits[static_cast<size_t>(k)][static_cast<size_t>(j)] - previousReplicaAt(*previous, k)[cell]
                                : 0.0;
                            sdCandidateMeans(row, j) += delta / static_cast<double>(replicaCount);
                        }
                    for (int k = 0; k < replicaCount; ++k, ++temporalRow)
                        for (int j = 0; j < p; ++j)
                        {
                            const size_t cell = support[static_cast<size_t>(j)];
                            const double delta = sdPreviousSupportMask[cell]
                                ? scored[static_cast<size_t>(s)].weightedReplicaLogits[static_cast<size_t>(k)][static_cast<size_t>(j)] - previousReplicaAt(*previous, k)[cell]
                                : 0.0;
                            sdWithin(temporalRow, j) = delta - sdCandidateMeans(row, j);
                        }
                }
                GSL_INFO("PFDI SD-TFEI temporal-difference likelihood: overlap_candidates={}, native_anchor_overlap={}, common_support={}, current_update={}, previous_update={}, registration=physical_grid_with_replica_or_native_anchor",
                         sdTrainingCandidateCount, nativeAnchorOverlap, commonSupportCount, tadmSourceUpdateId, sdPreviousInferenceUpdateId);
            }
        }
        if (!sdUseTemporalDifference)
        {
            sdObservedWeighted.resize(p);
            for (int j = 0; j < p; ++j)
                sdObservedWeighted(j) = std::sqrt(weights[static_cast<size_t>(j)]) * observed[static_cast<size_t>(j)];
        }
        const int sdSampleCount = sdTrainingCandidateCount * replicaCount;
        if (sdUseTemporalDifference)
        {
            empirical = (sdWithin.transpose() * sdWithin) / static_cast<double>(std::max(sdSampleCount, 1));
            covarianceMean = empirical.trace() / static_cast<double>(p);
            covarianceSquareMean = empirical.squaredNorm() / static_cast<double>(p * p);
            shrinkNumerator = covarianceSquareMean + covarianceMean * covarianceMean;
            shrinkDenominator = (static_cast<double>(sdSampleCount) + 1.0) *
                (covarianceSquareMean - covarianceMean * covarianceMean / static_cast<double>(p));
            shrinkage = shrinkDenominator <= 1e-12 ? 1.0 : std::min(shrinkNumerator / shrinkDenominator, 1.0);
            covarianceFloor = std::max(covarianceMean * 1e-12, 1e-12);
            transportCovariance = (1.0 - shrinkage) * empirical;
            transportCovariance.diagonal().array() += shrinkage * covarianceMean + covarianceFloor;
        }
        Eigen::MatrixXd centeredSource = sdCandidateMeans.rowwise() - sdCandidateMeans.colwise().mean();
        Eigen::MatrixXd sourceCovariance = (centeredSource.transpose() * centeredSource) /
                                           static_cast<double>(std::max(sdTrainingCandidateCount, 1));
        sourceCovariance = 0.5 * (sourceCovariance + sourceCovariance.transpose());
        Eigen::GeneralizedSelfAdjointEigenSolver<Eigen::MatrixXd> sourceSolver(sourceCovariance, transportCovariance);
        if (sourceSolver.info() != Eigen::Success)
        {
            GSL_ERROR("SD-TFEI generalized eigenproblem failed");
            return false;
        }
        std::vector<int> eligibleChannelIndices;
        double eigenvalueSum = 0.0;
        double eigenvalueSquareSum = 0.0;
        for (int eigenIndex = p - 1; eigenIndex >= 0; --eigenIndex)
        {
            const double eigenvalue = sourceSolver.eigenvalues()(eigenIndex);
            if (std::isfinite(eigenvalue) && eigenvalue > 1.0)
            {
                eligibleChannelIndices.push_back(eigenIndex);
                eigenvalueSum += eigenvalue;
                eigenvalueSquareSum += eigenvalue * eigenvalue;
            }
        }
        if (eligibleChannelIndices.empty())
        {
            GSL_ERROR("SD-TFEI source-identifiability gate failed: no lambda > 1 channel");
            return false;
        }
        // The participation ratio is the effective rank of the source
        // contrast spectrum.  It retains the smallest leading subspace that
        // carries the observed source variance, instead of treating every
        // lambda>1 mode as equally reliable in a finite replica bank.
        const double participationRatio = eigenvalueSquareSum > 0.0
                                               ? (eigenvalueSum * eigenvalueSum) / eigenvalueSquareSum
                                               : 1.0;
        // A candidate-conditional covariance is estimated from the held-out
        // scoring bank.  With K replicas its centered sample covariance has
        // rank at most K-1; retaining more SD channels makes the Gaussian
        // likelihood numerically singular and creates artificial one-leaf
        // spikes even after a tiny diagonal ridge.  This is an identifiability
        // contract, not a House-specific performance knob.
        const int replicaRankCap = std::max(1, replicaCount - 1);
        const int channelUpperBound = std::min(
            static_cast<int>(eligibleChannelIndices.size()), replicaRankCap);
        const int effectiveChannelCount = std::clamp(
            static_cast<int>(std::ceil(participationRatio)), 1,
            channelUpperBound);
        std::vector<int> channelIndices(eligibleChannelIndices.begin(),
                                        eligibleChannelIndices.begin() + effectiveChannelCount);
        const int channelCount = static_cast<int>(channelIndices.size());
        Eigen::MatrixXd channels(p, channelCount);
        for (int c = 0; c < channelCount; ++c)
            channels.col(c) = sourceSolver.eigenvectors().col(channelIndices[static_cast<size_t>(c)]);

        if (pfdiMode == "sd")
        {
            // Pure SD-TFEI likelihood.  This branch must not import the TADM
            // discrepancy prior: SD is the temporal-stable source channel
            // ablation, while structural model mismatch belongs only to the
            // TADM and joint arms.  The previous trust-region candidate
            // accidentally used sigma_delta/Lambda_delta here, so the arm
            // labelled "sd" was not a factor-pure main-innovation test.
            const Eigen::VectorXd observedChannel = channels.transpose() * sdObservedWeighted;
            // The inference contract is candidate-conditional:
            //   Sigma_s = Cov(z | s),  z = V^T Y.
            // A single global V^T C_t V for every candidate is only a
            // population diagnostic; using it as the likelihood covariance
            // collapses source-dependent temporal uncertainty and can create
            // a spurious out-of-support SD basin.  Keep the global temporal
            // covariance only as a positive-definite ridge target.
            Eigen::MatrixXd globalChannelCovariance = channels.transpose() * transportCovariance * channels;
            globalChannelCovariance = 0.5 * (globalChannelCovariance + globalChannelCovariance.transpose());
            const double globalTrace = std::max(globalChannelCovariance.trace(), 1e-12);
            const double covarianceFloor = std::max(globalTrace * 1e-9, 1e-12);
            // The scoring bank contains only a few held-out replicas.  A
            // candidate-specific covariance from K samples is therefore a
            // noisy estimate whose log-determinant can dominate the Bayes
            // factor and reward an accidental low-variance candidate.  Use
            // the finite-sample covariance shrinkage implied by the ratio of
            // projected dimension to available centred degrees of freedom.
            // This is fixed by the replica contract (not tuned per House or
            // seed) and targets the population temporal covariance already
            // estimated from the disjoint calibration bank.
            const double covarianceShrinkage = std::clamp(
                static_cast<double>(channelCount) /
                    static_cast<double>(channelCount + std::max(1, replicaCount - 1)),
                0.0, 1.0);
            std::vector<Eigen::MatrixXd> candidateChannelInverse(static_cast<size_t>(candidateCount));
            std::vector<double> candidateChannelLogdet(static_cast<size_t>(candidateCount), 0.0);
            std::vector<char> sdCandidateHasHistory(static_cast<size_t>(candidateCount), 0);
            for (int s = 0; s < candidateCount; ++s)
            {
                if (!sdComputeCandidate[static_cast<size_t>(s)])
                {
                    candidateChannelInverse[static_cast<size_t>(s)] = Eigen::MatrixXd::Identity(channelCount, channelCount);
                    continue;
                }
                // Fit/score means are disjoint: use only the held-out scoring
                // bank for the predictive source mean.
                const std::vector<std::vector<double>>* previous = nullptr;
                if (sdUseTemporalDifference)
                {
                    previous = previousReplicasFor(scored[static_cast<size_t>(s)]);
                    if (previous != nullptr &&
                        (previous->size() == static_cast<size_t>(2 * replicaCount) || previous->size() == 1))
                    {
                        sdCandidateHasHistory[static_cast<size_t>(s)] = 1;
                    }
                    else
                        previous = nullptr;
                }
                if (sdUseTemporalDifference && previous == nullptr)
                {
                    scored[static_cast<size_t>(s)].logScore = -INFINITY;
                    candidateChannelInverse[static_cast<size_t>(s)] = Eigen::MatrixXd::Identity(channelCount, channelCount);
                    continue;
                }
                sdCandidateHasHistory[static_cast<size_t>(s)] = 1;
                Eigen::VectorXd scoringMean = Eigen::VectorXd::Zero(channelCount);
                std::vector<Eigen::VectorXd> projectedScoring;
                projectedScoring.reserve(static_cast<size_t>(replicaCount));
                for (int k = replicaCount; k < 2 * replicaCount; ++k)
                {
                    Eigen::VectorXd replicaWeighted(p);
                    for (int j = 0; j < p; ++j)
                    {
                        const size_t cell = support[static_cast<size_t>(j)];
                        replicaWeighted(j) = scored[static_cast<size_t>(s)].weightedReplicaLogits[static_cast<size_t>(k)][static_cast<size_t>(j)] -
                            (previous && sdPreviousSupportMask[cell] ? previousReplicaAt(*previous, k)[cell] : 0.0);
                    }
                    projectedScoring.push_back(channels.transpose() * replicaWeighted);
                    scoringMean += projectedScoring.back() / static_cast<double>(replicaCount);
                }
                Eigen::MatrixXd candidateCovariance = Eigen::MatrixXd::Zero(channelCount, channelCount);
                for (const Eigen::VectorXd& value : projectedScoring)
                {
                    const Eigen::VectorXd centered = value - scoringMean;
                    candidateCovariance.noalias() += centered * centered.transpose();
                }
                candidateCovariance /= static_cast<double>(std::max(1, replicaCount - 1));
                candidateCovariance = 0.5 * (candidateCovariance + candidateCovariance.transpose());
                candidateCovariance = (1.0 - covarianceShrinkage) * candidateCovariance +
                                      covarianceShrinkage * globalChannelCovariance;
                candidateCovariance = 0.5 * (candidateCovariance + candidateCovariance.transpose());
                candidateCovariance.diagonal().array() += covarianceFloor;
                Eigen::LDLT<Eigen::MatrixXd> candidateFactor(candidateCovariance);
                if (candidateFactor.info() != Eigen::Success || (candidateFactor.vectorD().array() <= 0.0).any())
                {
                    // A four-replica estimate can be rank-deficient.  Fall
                    // back to the population temporal covariance while
                    // preserving the candidate-specific estimate whenever it
                    // is positive definite; this is numerical regularization,
                    // not a performance parameter.
                    candidateCovariance = globalChannelCovariance;
                    candidateCovariance.diagonal().array() += covarianceFloor;
                    candidateFactor.compute(candidateCovariance);
                }
                if (candidateFactor.info() != Eigen::Success || (candidateFactor.vectorD().array() <= 0.0).any())
                {
                    GSL_ERROR("SD-TFEI candidate temporal-channel covariance factorization failed");
                    return false;
                }
                candidateChannelInverse[static_cast<size_t>(s)] = candidateFactor.solve(Eigen::MatrixXd::Identity(channelCount, channelCount));
                candidateChannelLogdet[static_cast<size_t>(s)] = candidateFactor.vectorD().array().log().sum();
                const Eigen::VectorXd residual = observedChannel - scoringMean;
                const Eigen::VectorXd solved = candidateChannelInverse[static_cast<size_t>(s)] * residual;
                const double quadratic = residual.dot(solved);
                scored[static_cast<size_t>(s)].logScore = -0.5 *
                    (quadratic + candidateChannelLogdet[static_cast<size_t>(s)] +
                     static_cast<double>(channelCount) * std::log(2.0 * std::acos(-1.0)));
            }
            // Convert Gaussian log densities to relative evidence.  Without
            // this log-mean-exp normalization, the large negative absolute
            // density would act as a candidate-independent penalty rather
            // than a Bayes factor when the trust-region power is applied.
            double sdMaxLogScore = -INFINITY;
            for (const auto& row : scored)
                if (std::isfinite(row.logScore))
                    sdMaxLogScore = std::max(sdMaxLogScore, row.logScore);
            if (std::isfinite(sdMaxLogScore))
            {
                double sdExpSum = 0.0;
                int sdFiniteCount = 0;
                for (const auto& row : scored)
                    if (std::isfinite(row.logScore))
                    {
                        sdExpSum += std::exp(row.logScore - sdMaxLogScore);
                        ++sdFiniteCount;
                    }
                if (sdFiniteCount > 0 && sdExpSum > 0.0 && std::isfinite(sdExpSum))
                {
                    const double sdLogMean = sdMaxLogScore + std::log(sdExpSum / static_cast<double>(sdFiniteCount));
                    for (auto& row : scored)
                        if (std::isfinite(row.logScore))
                            row.logScore -= sdLogMean;
                }
            }
            // The score above uses the independent scoring-bank mean.  Use
            // individual scoring realizations only for a truth-blind
            // reliability check, using the same candidate-conditional
            // temporal covariance as the predictive likelihood.
            const int scoringReplicaCount = replicaCount;
            if (scoringReplicaCount > 0)
            {
                size_t aggregateTop = 0;
                for (size_t s = 1; s < scored.size(); ++s)
                    if (scored[s].logScore > scored[aggregateTop].logScore)
                        aggregateTop = s;
                int agreeingReplicas = 0;
                for (int k = replicaCount; k < 2 * replicaCount; ++k)
                {
                    size_t replicaTop = 0;
                    double replicaBest = -INFINITY;
                    for (int s = 0; s < candidateCount; ++s)
                    {
                        if (!sdCandidateHasHistory[static_cast<size_t>(s)])
                            continue;
                        Eigen::VectorXd replicaVector(p);
                        for (int j = 0; j < p; ++j)
                            replicaVector(j) = scored[static_cast<size_t>(s)].weightedReplicaLogits[static_cast<size_t>(k)][static_cast<size_t>(j)];
                        if (sdUseTemporalDifference)
                        {
                            const auto* previous = previousReplicasFor(scored[static_cast<size_t>(s)]);
                            if (previous == nullptr ||
                                (previous->size() != static_cast<size_t>(2 * replicaCount) && previous->size() != 1))
                            {
                                GSL_ERROR("SD-TFEI scoring registration lost candidate {}", scored[static_cast<size_t>(s)].id);
                                return false;
                            }
                            for (int j = 0; j < p; ++j)
                            {
                                const size_t cell = support[static_cast<size_t>(j)];
                                if (sdPreviousSupportMask[cell])
                                    replicaVector(j) -= previousReplicaAt(*previous, k)[cell];
                                else
                                    replicaVector(j) = 0.0;
                            }
                        }
                        Eigen::VectorXd residual = channels.transpose() * (sdObservedWeighted - replicaVector);
                        const double replicaScore = -0.5 *
                            (residual.dot(candidateChannelInverse[static_cast<size_t>(s)] * residual) +
                             candidateChannelLogdet[static_cast<size_t>(s)] +
                             static_cast<double>(channelCount) * std::log(2.0 * std::acos(-1.0)));
                        scored[static_cast<size_t>(s)].replicaLogScores[static_cast<size_t>(k)] = replicaScore;
                        if (replicaScore > replicaBest)
                        {
                            replicaBest = replicaScore;
                            replicaTop = static_cast<size_t>(s);
                        }
                    }
                    const auto& aggregateRect = scored[aggregateTop].rect;
                    const auto& replicaRect = scored[replicaTop].rect;
                    const double aggregateRadius = 0.5 * std::sqrt(
                        static_cast<double>(std::max(1, aggregateRect[2] * aggregateRect[3]))) * measuredHitProb.metadata.cellSize;
                    const double replicaRadius = 0.5 * std::sqrt(
                        static_cast<double>(std::max(1, replicaRect[2] * replicaRect[3]))) * measuredHitProb.metadata.cellSize;
                    const double basinRadius = aggregateRadius + replicaRadius + measuredHitProb.metadata.cellSize;
                    const double dx = static_cast<double>(scored[replicaTop].point.x - scored[aggregateTop].point.x);
                    const double dy = static_cast<double>(scored[replicaTop].point.y - scored[aggregateTop].point.y);
                    if (std::hypot(dx, dy) <= basinRadius)
                        ++agreeingReplicas;
                }
                sdReplicaTopAgreement = static_cast<double>(agreeingReplicas) /
                                        static_cast<double>(scoringReplicaCount);
                sdStabilityGate = sdReplicaTopAgreement > 0.5;
            }
            GSL_INFO("PFDI SD-TFEI-only update {}: channels={}, replica_rank_cap={}, covariance_shrinkage={:.6f}, participation_ratio={:.3f}, leading_lambda={:.6f}, support={}, calibration_samples={}, scoring_samples={}, factor_pure=true",
                     tadmSourceUpdateId, channelCount, replicaRankCap, covarianceShrinkage, participationRatio, sourceSolver.eigenvalues()(channelIndices.front()), p, sampleCount, sampleCount);
            GSL_INFO("PFDI SD-TFEI scoring-replica top agreement update {}: {:.3f}, gate={}, temporal_confirmation={}, likelihood=gaussian_temporal_marginal",
                     tadmSourceUpdateId, sdReplicaTopAgreement, sdStabilityGate ? "accept" : "reject",
                     sdTemporalConfirmation ? "accept" : "pending");
            // Commit the current weighted observation and held-out replica
            // bank only after scoring.  The next consecutive window can then
            // form a first difference without mixing candidate IDs or using
            // the current window twice.  Store both exact IDs and physical
            // grid keys because adaptive leaves may be renamed/refined.
            sdPreviousObserved.assign(measuredHitProb.data.size(), 0.0);
            sdPreviousSupportMask.assign(measuredHitProb.data.size(), 0);
            for (int j = 0; j < p; ++j)
            {
                const size_t cell = support[static_cast<size_t>(j)];
                sdPreviousObserved[cell] = std::sqrt(weights[static_cast<size_t>(j)]) * observed[static_cast<size_t>(j)];
                sdPreviousSupportMask[cell] = 1;
            }
            sdPreviousCandidateReplicas.clear();
            sdPreviousCandidateReplicasByGrid.clear();
            size_t nativeAnchorCount = 0;
            for (const auto& row : scored)
            {
                std::vector<std::vector<double>> fullReplicas(
                    row.weightedReplicaLogits.size(),
                    std::vector<double>(measuredHitProb.data.size(), 0.0));
                for (size_t k = 0; k < row.weightedReplicaLogits.size(); ++k)
                    for (int j = 0; j < p; ++j)
                        fullReplicas[k][support[static_cast<size_t>(j)]] =
                            row.weightedReplicaLogits[k][static_cast<size_t>(j)];
                // Candidates outside the current 95% replica budget still
                // have one exact native forward realization.  Retain that
                // realization as a one-bank physical anchor for the next
                // temporal window.  It is not a scoring replica and is
                // never used to estimate the current covariance; the next
                // window treats it as a persistent-state mean, preventing
                // missing history from becoming an artificial -inf score.
                if (fullReplicas.empty() && row.nativeHitMap &&
                    row.nativeHitMap->size() == measuredHitProb.data.size())
                {
                    fullReplicas.assign(1, std::vector<double>(measuredHitProb.data.size(), 0.0));
                    for (int j = 0; j < p; ++j)
                    {
                        const size_t cell = support[static_cast<size_t>(j)];
                        fullReplicas[0][cell] = std::sqrt(weights[static_cast<size_t>(j)]) *
                            tadmLogit(static_cast<double>((*row.nativeHitMap)[cell]));
                    }
                    ++nativeAnchorCount;
                }
                sdPreviousCandidateReplicas.emplace(row.id, fullReplicas);
                // Prefer a full held-out replica bank over a one-bank native
                // anchor if two adaptive leaves share the same physical key.
                if (fullReplicas.size() == static_cast<size_t>(2 * tadmReplicas) ||
                    fullReplicas.size() == 1)
                {
                    const std::string key = temporalGridKey(row.point);
                    const auto gridIt = sdPreviousCandidateReplicasByGrid.find(key);
                    if (gridIt == sdPreviousCandidateReplicasByGrid.end() ||
                        (gridIt->second.size() != static_cast<size_t>(2 * tadmReplicas) &&
                         fullReplicas.size() == static_cast<size_t>(2 * tadmReplicas)))
                        sdPreviousCandidateReplicasByGrid[key] = std::move(fullReplicas);
                }
            }
            GSL_INFO("PFDI SD-TFEI temporal history commit: full_replica_banks={}, native_anchor_banks={}, total_candidates={}",
                     scored.size() - nativeAnchorCount, nativeAnchorCount, scored.size());
            sdPreviousInferenceUpdateId = tadmSourceUpdateId;
            sdTemporalHistoryValid = true;
            return finalizeEvidence();
        }

        // Keep the retained SD channels and test their overlap with the
        // shared-nuisance span.  The nuisance is integrated jointly with the
        // SD likelihood; it must not be projected away, otherwise TADM has
        // exactly zero contribution in the retained channel space.
        Eigen::HouseholderQR<Eigen::MatrixXd> sourceQR(channels);
        const Eigen::MatrixXd sourceQ = sourceQR.householderQ() * Eigen::MatrixXd::Identity(p, channelCount);
        Eigen::MatrixXd nuisanceStack(p, candidateCount * 3);
        for (int s = 0; s < candidateCount; ++s)
            for (int q = 0; q < 3; ++q)
                for (int j = 0; j < p; ++j)
                    nuisanceStack(j, 3 * s + q) = scored[static_cast<size_t>(s)].weightedBasis[static_cast<size_t>(j)][static_cast<size_t>(q)];
        Eigen::ColPivHouseholderQR<Eigen::MatrixXd> nuisanceQR(nuisanceStack);
        const int nuisanceRank = nuisanceQR.rank();
        if (nuisanceRank <= 0)
        {
            GSL_ERROR("TADM protected nuisance span is empty");
            return false;
        }
        const Eigen::MatrixXd nuisanceQ = nuisanceQR.householderQ() * Eigen::MatrixXd::Identity(p, nuisanceRank);
        const Eigen::VectorXd overlapSingular = (sourceQ.transpose() * nuisanceQ).jacobiSvd(Eigen::ComputeThinU | Eigen::ComputeThinV).singularValues();
        const double overlapRho = overlapSingular.size() > 0 ? overlapSingular(0) : 0.0;
        if (!(overlapRho < 0.95))
        {
            GSL_ERROR("SD-TFEI/TADM identifiability gate failed: overlap_rho={}", overlapRho);
            return false;
        }
        // Full-space reference covariance: independently estimated transport
        // covariance plus white model/sensor discrepancy.  TADM is added by a
        // rank-three Woodbury update after protecting its basis from the
        // source-identifiable SD span.
        const Eigen::MatrixXd sourceProjector = Eigen::MatrixXd::Identity(p, p) - sourceQ * sourceQ.transpose();
        const Eigen::MatrixXd fullBaseCovariance = transportCovariance +
                                                   tadmPrior.sigma2 * Eigen::MatrixXd::Identity(p, p);
        Eigen::LDLT<Eigen::MatrixXd> baseFactor(fullBaseCovariance);
        if (baseFactor.info() != Eigen::Success || (baseFactor.vectorD().array() <= 0.0).any())
        {
            GSL_ERROR("PFDI full covariance factorization failed");
            return false;
        }
        const double logdetBase = baseFactor.vectorD().array().log().sum();
        Eigen::Matrix3d lambda;
        Eigen::Vector3d discrepancyMean;
        for (int i = 0; i < 3; ++i)
        {
            discrepancyMean(i) = tadmPrior.mu[static_cast<size_t>(i)];
            for (int j = 0; j < 3; ++j)
                lambda(i, j) = tadmPrior.lambda[static_cast<size_t>(3 * i + j)];
        }
        Eigen::LDLT<Eigen::Matrix3d> lambdaFactor(lambda);
        if (lambdaFactor.info() != Eigen::Success || (lambdaFactor.vectorD().array() <= 0.0).any())
        {
            GSL_ERROR("PFDI TADM covariance factorization failed");
            return false;
        }
        const Eigen::Matrix3d lambdaInverse = lambdaFactor.solve(Eigen::Matrix3d::Identity());
        const double logdetLambda = lambdaFactor.vectorD().array().log().sum();
        Eigen::VectorXd observedWeighted(p);
        for (int j = 0; j < p; ++j)
            observedWeighted(j) = std::sqrt(weights[static_cast<size_t>(j)]) * observed[static_cast<size_t>(j)];
        for (int s = 0; s < candidateCount; ++s)
        {
            Eigen::MatrixXd weightedBasis(p, 3);
            Eigen::VectorXd scoringMean = Eigen::VectorXd::Zero(p);
            for (int j = 0; j < p; ++j)
                for (int q = 0; q < 3; ++q)
                    weightedBasis(j, q) = scored[static_cast<size_t>(s)].weightedBasis[static_cast<size_t>(j)][static_cast<size_t>(q)];
            for (int k = replicaCount; k < 2 * replicaCount; ++k)
                for (int j = 0; j < p; ++j)
                    scoringMean(j) += scored[static_cast<size_t>(s)].weightedReplicaLogits[static_cast<size_t>(k)][static_cast<size_t>(j)] /
                                      static_cast<double>(replicaCount);
            const Eigen::MatrixXd protectedBasis = sourceProjector * weightedBasis;
            const Eigen::MatrixXd baseInverseBasis = baseFactor.solve(protectedBasis);
            const Eigen::Matrix3d woodbury = lambdaInverse + protectedBasis.transpose() * baseInverseBasis;
            Eigen::LDLT<Eigen::Matrix3d> woodburyFactor(woodbury);
            if (woodburyFactor.info() != Eigen::Success || (woodburyFactor.vectorD().array() <= 0.0).any())
            {
                GSL_ERROR("PFDI full-covariance Woodbury factorization failed for candidate {}", scored[static_cast<size_t>(s)].id);
                return false;
            }
            const double sharedLogdet = logdetBase + logdetLambda + woodburyFactor.vectorD().array().log().sum();
            const Eigen::VectorXd residual = observedWeighted - scoringMean - protectedBasis * discrepancyMean;
            const Eigen::VectorXd baseInverseResidual = baseFactor.solve(residual);
            const Eigen::Vector3d q = protectedBasis.transpose() * baseInverseResidual;
            const double quadratic = residual.dot(baseInverseResidual) - q.dot(woodburyFactor.solve(q));
            scored[static_cast<size_t>(s)].logScore = -0.5 * (quadratic + sharedLogdet + static_cast<double>(p) * std::log(2.0 * std::acos(-1.0)));
        }
        GSL_INFO("PFDI protected SD-TFEI update {}: channels={}, participation_ratio={:.3f}, leading_lambda={:.6f}, overlap_rho={:.6f}, shrinkage={:.6f}, support={}, calibration_samples={}, scoring_samples={}",
                 tadmSourceUpdateId, channelCount, participationRatio, sourceSolver.eigenvalues()(channelIndices.front()), overlapRho,
                 shrinkage, p, sampleCount, sampleCount);

        if (!finalizeEvidence())
            return false;

        const auto end = std::chrono::steady_clock::now();
        const double elapsed = std::chrono::duration<double>(end - start).count();
        std::ofstream timing(tadmDirectory + "/tadm_update_timing.csv", std::ios::out | std::ios::app);
        if (timing.tellp() == 0)
            timing << "run_uuid,source_update_id,sim_time,candidate_count,calibration_replica_count,scoring_replica_count,support_count,elapsed_s,max_log_score\n";
        timing << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << std::setprecision(17) << tadmSimTime << ','
               << scored.size() << ',' << tadmReplicas << ',' << tadmReplicas << ',' << support.size() << ',' << elapsed << ',' << finalizedMaxLogScore << '\n';
        timing.flush();
        GSL_INFO("PFDI protected online update {}: {} candidates x {} calibration + {} scoring replicas, {:.3f}s", tadmSourceUpdateId,
                 scored.size(), tadmReplicas, tadmReplicas, elapsed);
        return true;
    }

    void Simulations::exportCandidateHitMap(const std::string& stableID, const Vector2& source, const std::vector<float>& hitMap)
    {
        if (!readOnlyForwardExportEnabled || readOnlyForwardExportDirectory.empty())
            return;

        std::lock_guard<std::mutex> guard(readOnlyForwardExportMutex);

        const std::string exportDirectory = readOnlyForwardExportCurrentDirectory.empty() ? readOnlyForwardExportDirectory : readOnlyForwardExportCurrentDirectory;
        std::filesystem::create_directories(exportDirectory + "/candidate_maps");
        const std::string prefix = fmt::format("{}/candidate_maps/snapshot_{:06}_{}", exportDirectory,
                                               readOnlyForwardExportSnapshot, stableID);
        std::ofstream binary(prefix + ".f32", std::ios::binary | std::ios::trunc);
        if (!binary.is_open())
            return;
        binary.write(reinterpret_cast<const char*>(hitMap.data()),
                     static_cast<std::streamsize>(hitMap.size() * sizeof(float)));

        std::ofstream manifest(exportDirectory + "/candidate_maps.csv", std::ios::out | std::ios::app);
        if (manifest.tellp() == 0)
            manifest << "run_uuid,snapshot,candidate_id,source_x,source_y,map_file,width,height,cell_size,origin_x,origin_y,pmfs_parameters_hash,map_hash,wind_hash,code_hash\n";
        manifest << readOnlyForwardExportRunUUID << ',' << readOnlyForwardExportSnapshot << ',' << stableID << ','
                 << source.x << ',' << source.y << ',' << prefix << ".f32," << measuredHitProb.metadata.dimensions.x << ','
                 << measuredHitProb.metadata.dimensions.y << ',' << measuredHitProb.metadata.cellSize << ','
                 << measuredHitProb.metadata.origin.x << ',' << measuredHitProb.metadata.origin.y << ','
                 << readOnlyForwardExportPMFSParametersHash << ',' << readOnlyForwardExportMapHash << ','
                 << readOnlyForwardExportWindHash << ',' << readOnlyForwardExportCodeHash << '\n';
    }

    void Simulations::exportCandidateExposureMap(const std::string& stableID, const Vector2& source, const std::vector<float>& exposureMap)
    {
        std::lock_guard<std::mutex> lock(readOnlyForwardExportMutex);
        const std::string exportDirectory = readOnlyForwardExportCurrentDirectory.empty() ? readOnlyForwardExportDirectory : readOnlyForwardExportCurrentDirectory;
        std::filesystem::create_directories(exportDirectory);
        const std::string prefix = fmt::format("{}/snapshot_{:06}_exposure_{}", exportDirectory, readOnlyForwardExportSnapshot, stableID);
        std::ofstream output(prefix + ".f32", std::ios::binary | std::ios::trunc);
        output.write(reinterpret_cast<const char*>(exposureMap.data()), static_cast<std::streamsize>(exposureMap.size() * sizeof(float)));
        std::ofstream manifest(exportDirectory + "/candidate_exposure_maps.csv", std::ios::app);
        if (manifest.tellp() == 0)
            manifest << "run_uuid,snapshot,candidate_id,source_x,source_y,map_file,width,height,cell_size,origin_x,origin_y,pmfs_parameters_hash,map_hash,wind_hash,code_hash\n";
        manifest << readOnlyForwardExportRunUUID << ',' << readOnlyForwardExportSnapshot << ',' << stableID << ',' << source.x << ',' << source.y << ',' << prefix << ".f32,"
                 << measuredHitProb.metadata.dimensions.x << ',' << measuredHitProb.metadata.dimensions.y << ',' << measuredHitProb.metadata.cellSize << ','
                 << measuredHitProb.metadata.origin.x << ',' << measuredHitProb.metadata.origin.y << ',' << readOnlyForwardExportPMFSParametersHash << ','
                 << readOnlyForwardExportMapHash << ',' << readOnlyForwardExportWindHash << ',' << readOnlyForwardExportCodeHash << '\n';
    }

    bool Simulations::exportCompletePointCandidateGrid(bool exportContinuousExposure)
    {
        if (!readOnlyForwardExportEnabled || readOnlyForwardExportDirectory.empty())
            return false;

        size_t exported = 0;
        for (int x = 0; x < measuredHitProb.metadata.dimensions.x; ++x)
        {
            for (int y = 0; y < measuredHitProb.metadata.dimensions.y; ++y)
            {
                if (!measuredHitProb.freeAt(x, y))
                    continue;
                const Vector2 point = measuredHitProb.metadata.indicesToCoordinates(x, y);
                std::vector<float> hitMap(measuredHitProb.data.size(), 0.0f);
                std::vector<float> exposureMap;
                simulateSourceInPosition(SimulationSource(point, measuredHitProb.metadata), hitMap, true,
                                         settings.iterationsToRecord, settings.deltaTime, settings.noiseSTDev,
                                         exportContinuousExposure ? &exposureMap : nullptr);
                if (exportContinuousExposure)
                    exportCandidateExposureMap(fmt::format("point_{}_{}", x, y), point, exposureMap);
                if (settings.blurSigmaX > 0 || settings.blurSigmaY > 0)
                {
                    cv::Mat asImage(hitMap);
                    asImage = asImage.reshape(1, measuredHitProb.metadata.dimensions.y);
                    blurHitMap(asImage);
                }
                exportCandidateHitMap(fmt::format("point_{}_{}", x, y), point, hitMap);
                ++exported;
            }
        }
        GSL_INFO("Read-only PMFS forward export snapshot {}: {} complete point candidates", readOnlyForwardExportSnapshot, exported);
        ++readOnlyForwardExportSnapshot;
        return exported > 0;
    }

    void Simulations::initializeContrastiveEventContext(const std::vector<SimulationResult>& results)
    {
        eventEvidenceContextProbability.assign(eventEvidence.size(), 0.0L);
        if (eventEvidence.empty())
            return;
        std::vector<const SimulationResult*> ordered;
        ordered.reserve(results.size());
        for (const SimulationResult& result : results)
            if (result.valid && result.leaf != nullptr)
                ordered.push_back(&result);
        std::sort(ordered.begin(), ordered.end(), [](const SimulationResult* left,
                                                     const SimulationResult* right)
        {
            const NQA::Node* a = left->leaf;
            const NQA::Node* b = right->leaf;
            return std::tie(a->origin.x, a->origin.y, a->size.x, a->size.y) <
                   std::tie(b->origin.x, b->origin.y, b->size.x, b->size.y);
        });
        size_t members = 0;
        for (const SimulationResult* result : ordered)
        {
            for (const auto& memberMap : result->transportMemberHitMaps)
            {
                if (memberMap.size() != measuredHitProb.data.size())
                    throw std::runtime_error("CER_RATIO_MEMBER_MAP_SIZE");
                for (size_t eventIndex = 0; eventIndex < eventEvidence.size(); ++eventIndex)
                    eventEvidenceContextProbability[eventIndex] += memberMap[eventEvidence[eventIndex].cell];
                ++members;
            }
        }
        if (members == 0)
            throw std::runtime_error("CER_RATIO_CONTEXT_EMPTY");
        for (long double& probability : eventEvidenceContextProbability)
            probability /= static_cast<long double>(members);
        GSL_INFO("CER contrastive context initialized: events={}, members={}, fixed_ratio_weight=1",
                 eventEvidence.size(), members);
    }

    long double Simulations::sourceProbFromContrastiveEvents(
        const std::vector<std::vector<float>>& transportMemberHitMaps) const
    {
        if (eventEvidence.empty())
            return 1.0L;
        if (eventEvidenceContextProbability.size() != eventEvidence.size() ||
            transportMemberHitMaps.empty())
            throw std::runtime_error("CER_RATIO_CONTEXT_NOT_READY");
        const auto clipped = [](long double probability)
        {
            return std::clamp(probability, 1.0e-4L, 1.0L - 1.0e-4L);
        };
        const auto logit = [&](long double probability)
        {
            const long double p = clipped(probability);
            return std::log(p) - std::log1p(-p);
        };
        const auto expit = [](long double value)
        {
            if (value >= 0.0L)
            {
                const long double z = std::exp(-value);
                return 1.0L / (1.0L + z);
            }
            const long double z = std::exp(value);
            return z / (1.0L + z);
        };

        long double mixtureLikelihood = 0.0L;
        for (const auto& memberMap : transportMemberHitMaps)
        {
            long double logLikelihood = 0.0L;
            double previousConcentration = 0.0;
            for (size_t eventIndex = 0; eventIndex < eventEvidence.size(); ++eventIndex)
            {
                const EventEvidence& event = eventEvidence[eventIndex];
                if (event.cell >= memberMap.size())
                    throw std::runtime_error("CER_RATIO_EVENT_CELL_RANGE");
                // Same fixed persistence law as the passed cross-House screen:
                // Normal(log1p(previous block concentration), unit scale).
                const long double thresholdLog = std::log1p(event.threshold);
                const long double previousLog = std::log1p(previousConcentration);
                const long double persistence = 0.5L * std::erfc(
                    (thresholdLog - previousLog) / std::sqrt(2.0L));
                const long double sourceProbability = clipped(memberMap[event.cell]);
                const long double contextProbability = clipped(eventEvidenceContextProbability[eventIndex]);
                // Fixed unit source/context odds ratio. Candidate-independent
                // persistence handles shared temporal dynamics; only the
                // source-specific forward contrast changes posterior odds.
                const long double corrected = clipped(expit(
                    logit(persistence) + logit(sourceProbability) - logit(contextProbability)));
                logLikelihood += std::log(event.hit ? corrected : 1.0L - corrected);
                previousConcentration = event.concentration;
            }
            mixtureLikelihood += std::exp(logLikelihood) /
                                 static_cast<long double>(transportMemberHitMaps.size());
        }
        if (!(std::isfinite(static_cast<double>(mixtureLikelihood)) && mixtureLikelihood > 0.0L))
            throw std::runtime_error("CER_RATIO_LIKELIHOOD_INVALID");
        return mixtureLikelihood;
    }

    void Simulations::applyContrastiveEventEvidence(std::vector<SimulationResult>& results,
                                                     std::vector<LeafScore>& scores)
    {
        std::unordered_map<NQA::Node*, long double> scoreByLeaf;
        for (SimulationResult& result : results)
        {
            if (!result.valid || result.leaf == nullptr)
                continue;
            result.sourceProb = sourceProbFromContrastiveEvents(result.transportMemberHitMaps);
            scoreByLeaf[result.leaf] = result.sourceProb;
            NQA::Node* node = result.leaf;
            for (int cellI = node->origin.x; cellI < node->origin.x + node->size.x; ++cellI)
                for (int cellJ = node->origin.y; cellJ < node->origin.y + node->size.y; ++cellJ)
                    sourceProbInternal[sourceProb.metadata.indexOf({cellI, cellJ})] = result.sourceProb;
        }
        for (LeafScore& score : scores)
        {
            const auto it = scoreByLeaf.find(score.leaf);
            if (it != scoreByLeaf.end())
                score.score = it->second;
        }
    }

    long double Simulations::sourceProbFromMaps(const Grid2D<HitProbability>& measuredHitProb, const std::vector<float>& hitMap) const
    {
        ZoneScoped;
        long double total = 1;
        for (int i = 0; i < measuredHitProb.data.size(); i++)
        {
            if (measuredHitProb.occupancy[i] != Occupancy::Free)
                continue;

            const double& simulated = hitMap[i];
            double sourceGivenThisCell = probabilityFromSingleCell(measuredHitProb.data[i], simulated);
            total *= sourceGivenThisCell;
            GSL_ASSERT(!std::isnan(total));
        }
        return total;
    }

    long double Simulations::sourceProbFromEvents(const std::vector<float>& hitMap) const
    {
        if (eventEvidence.empty())
            return 1.0L;
        long double logLikelihood = 0.0L;
        for (const auto& event : eventEvidence)
        {
            if (event.cell >= hitMap.size())
                throw std::runtime_error("CER_EVENT_CELL_RANGE");
            const long double probability = std::clamp(static_cast<long double>(hitMap[event.cell]),
                                                       1.0e-4L, 1.0L - 1.0e-4L);
            logLikelihood += std::log(event.hit ? probability : 1.0L - probability);
        }
        const long double result = std::exp(logLikelihood);
        if (!(std::isfinite(static_cast<double>(result)) && result > 0.0L))
            throw std::runtime_error("CER_EVENT_LIKELIHOOD_UNDERFLOW");
        return result;
    }

    double Simulations::probabilityFromSingleCell(HitProbability hitProb, double simulated) const
    {
#define FREQUENCY_DISTRIBUTION_METHOD 0
#if FREQUENCY_DISTRIBUTION_METHOD
        auto frequencyDistribution = hitProb.frequencyDistribution();
        double result = 0;
        for (int freqIndex = 0; freqIndex < frequencyDistribution.size(); freqIndex++)
        {
            float measured = HitProbability::frequencyOfBucket(freqIndex);
            result += frequencyDistribution[freqIndex] * probabilitySingleFrequency(measured, simulated);
            GSL_ASSERT(!std::isnan(result));
        }
        return result;
#else
        return Utils::lerp(1, probabilitySingleFrequency(hitProb.probability(), simulated), hitProb.confidence);
#endif
    }

    double Simulations::probabilitySingleFrequency(double measured, double simulated) const
    {
        return 1 - std::abs(measured - simulated) * settings.sourceDiscriminationPower;
    }

    void Simulations::moveFilament(Filament& filament, Vector2Int& indices, float deltaTime, float noiseSTDev,
                                   EventKeyedTransportRng* transportRng, uint64_t& drawIndex) const
    {
        const double noiseX = transportRng ? transportRng->normalAt(drawIndex++, 0.0, noiseSTDev) : gaussian.nextValue(0, noiseSTDev);
        const double noiseY = transportRng ? transportRng->normalAt(drawIndex++, 0.0, noiseSTDev) : gaussian.nextValue(0, noiseSTDev);
        Vector2 velocity = wind.dataAt(indices.x, indices.y) + Vector2(noiseX, noiseY);

        Vector2 newPos = filament.position + deltaTime * velocity;
        moveAlongPath(filament.position, newPos);
    }

    bool Simulations::filamentIsOutside(const Filament& filament) const
    {
        Vector2Int newIndices = measuredHitProb.metadata.coordinatesToIndices(filament.position.x, filament.position.y);
        return !measuredHitProb.metadata.indicesInBounds(newIndices);
    }

    void Simulations::simulateSourceInPosition(const SimulationSource& source, std::vector<float>& hitMap, bool warmup,
                                               int timesteps, float deltaTime, float noiseSTDev,
                                               std::vector<float>* exposureMapBeforeNormalization,
                                               EventKeyedTransportRng* transportRng) const
    {
        constexpr int numFilamentsIteration = 5;
        size_t max_filaments = settings.maxWarmupIterations * numFilamentsIteration + timesteps * numFilamentsIteration;

        // To avoid having to delete filaments from the middle of the vector, which is quite slow, we will ping-pong the active filaments between two vectors
        // at the start of any iteration, one vector (active) will contain all the released filaments and the other one will be empty
        // after each filament has been moved, if it is still active, it will be copied to the other vector
        // then, the active vector changes and the old one is cleared
        std::vector<Filament> filaments1;
        std::vector<Filament> filaments2;
        filaments1.reserve(max_filaments);
        filaments2.reserve(max_filaments);
        std::vector<Filament>* activeFilamentVec = &filaments1;
        std::vector<Filament>* otherFilamentVec = &filaments2;

        std::vector<uint16_t> updated(hitMap.size(), 0); // index of the last iteration in which this cell was updated, to avoid double-counting
        uint64_t drawIndex = 0;

        // warm-up: we don't want to start recording frequency of hits until the shape of the plume has stabilized. Wait until a filament exits the
        // environment through an outlet, or a maximum number of steps
        {
            ZoneScopedN("Warmup");

            bool stable = false;
            int iterationCount = 0;
            while (iterationCount < settings.minWarmupIterations || (!stable && iterationCount < settings.maxWarmupIterations))
            {
                for (size_t i = 0; i < numFilamentsIteration; i++)
                {
                    activeFilamentVec->emplace_back();
                    activeFilamentVec->back().position = source.getPoint();
                }

                for (Filament& filament : *activeFilamentVec)
                {
                    auto indices = measuredHitProb.metadata.coordinatesToIndices(filament.position.x, filament.position.y);

                    // move active filaments
                    moveFilament(filament, indices, deltaTime * 2, noiseSTDev, transportRng, drawIndex);

                    // remove filaments
                    if (filamentIsOutside(filament))
                        stable = true;
                    else
                        otherFilamentVec->push_back(filament);
                }
                iterationCount++;

                // "other" now contains the list of all the filaments that are still available, so swap the vectors and remove the old list
                activeFilamentVec->clear();
                std::swap(activeFilamentVec, otherFilamentVec);
            }
        }

        ZoneScopedN("Recording");
        // now, we do the thing
        for (int t = 1; t < timesteps + 1; t++)
        {
            for (int i = 0; i < numFilamentsIteration; i++)
            {
                activeFilamentVec->emplace_back();
                activeFilamentVec->back().position = source.getPoint();
            }

            for (Filament& filament : *activeFilamentVec)
            {
                // update map
                auto indices = measuredHitProb.metadata.coordinatesToIndices(filament.position.x, filament.position.y);
                size_t index = measuredHitProb.metadata.indexOf(indices);
                GSL_ASSERT(measuredHitProb.metadata.indicesInBounds(indices));
                // mark as updated so it doesn't count multiple filaments in the same timestep
                if (updated[index] < t)
                {
                    hitMap[index]++;
                    updated[index] = t;
                }

                // move active filaments
                moveFilament(filament, indices, deltaTime, noiseSTDev, transportRng, drawIndex);

                // remove filaments
                if (!filamentIsOutside(filament))
                    otherFilamentVec->push_back(filament);
            }
            activeFilamentVec->clear();
            std::swap(activeFilamentVec, otherFilamentVec);
        }

        if (exposureMapBeforeNormalization)
            *exposureMapBeforeNormalization = hitMap;
        // convert the total hit count into relative frequency
        for (int i = 0; i < measuredHitProb.data.size(); i++)
        {
            if (measuredHitProb.occupancy[i] == Occupancy::Free)
                hitMap[i] = hitMap[i] / timesteps;
        }
    }

    Vector2 SimulationSource::getPoint() const
    {
        if (mode == Mode::Point)
        {
            if (!firstSampledPointValid)
            {
                firstSampledPoint = point;
                firstSampledPointValid = true;
            }
            return point;
        }

        Vector2 start = metadata.indicesToCoordinates(nqaNode->origin.x, nqaNode->origin.y, false);
        Vector2 end = metadata.indicesToCoordinates(nqaNode->origin.x + nqaNode->size.x, nqaNode->origin.y + nqaNode->size.y, false);

        Vector2 randP;
        if (keyedRng)
        {
            const uint64_t draw = pointDrawIndex++;
            randP = Vector2(static_cast<float>(keyedRng->uniformAt(draw, 0, start.x, end.x)),
                            static_cast<float>(keyedRng->uniformAt(draw, 1, start.y, end.y)));
        }
        else
        {
            randP = Vector2(Utils::uniformRandomF(start.x, end.x), Utils::uniformRandomF(start.y, end.y));
        }
        GSL_ASSERT(randP.x >= start.x && randP.x < end.x && randP.y >= start.y && randP.y < end.y);
        if (!firstSampledPointValid)
        {
            firstSampledPoint = randP;
            firstSampledPointValid = true;
        }
        return randP;
    }

    bool Simulations::moveAlongPath(Vector2& currentPosition, const Vector2& end) const
    {
        Vector2Int indexEnd = measuredHitProb.metadata.coordinatesToIndices(end.x, end.y);
        Vector2Int indexOrigin = measuredHitProb.metadata.coordinatesToIndices(currentPosition.x, currentPosition.y);

        if (!measuredHitProb.freeAt(indexOrigin.x, indexOrigin.y))
        {
            return false;
        }

        // try to avoid doing the raycast by looking at the pre-computed visibilityMap
        if (indexOrigin == indexEnd || (measuredHitProb.metadata.indicesInBounds(indexEnd) && measuredHitProb.freeAt(indexEnd.x, indexEnd.y) &&
                                        visibilityMap->isVisible(indexOrigin, indexEnd) == Visibility::Visible))
        {
            currentPosition = end;
            return true;
        }

#define USE_DDA 0
#if USE_DDA
        Vector2 movement = end - currentPosition;
        DDA::_2D::RayCastInfo raycastInfo =
            DDA::_2D::castRay<GSL::Occupancy>(currentPosition, movement, vmath::length(movement),
                                              DDA::_2D::Map<GSL::Occupancy>(measuredHitProb.occupancy, measuredHitProb.metadata.origin,
                                                                            measuredHitProb.metadata.cellSize, measuredHitProb.metadata.dimensions),
                                              [](const GSL::Occupancy& occ)
                                              {
                                                  return occ == GSL::Occupancy::Free;
                                              });
        // This is a completely hacky arbitrary value to try and stop filaments from getting stuck right next to a wall
        // ideally, we should implement a "deflection" instead so they move along the wall a bit rather than stopping dead
        constexpr float wallStoppingProportion = 0.7;
        currentPosition += movement * raycastInfo.distance * wallStoppingProportion;

        return true;
#else
        const auto& metadata = measuredHitProb.metadata;
        bool pathIsFree = true;

        Vector2 vector = end - currentPosition;
        float travelDistance = vmath::length(vector);
        float stepSize = std::min(travelDistance, metadata.cellSize * 0.5f);
        Vector2 increment = vmath::normalized(vector) * stepSize;
        int steps = travelDistance / stepSize;

        int index = 0;
        while (index < steps && pathIsFree)
        {
            currentPosition += increment;
            index++;
            Vector2Int pair = metadata.coordinatesToIndices(currentPosition.x, currentPosition.y);
            pathIsFree = !metadata.indicesInBounds(pair) || measuredHitProb.freeAt(pair.x, pair.y);
            if (!pathIsFree)
                currentPosition -= increment;
        }
        return pathIsFree;
#endif
    }

    void Simulations::makeSimulationImage(const SimulationSource& source)
    {
        std::vector<float> hitMap(measuredHitProb.data.size(), 0.0);
        simulateSourceInPosition(source, hitMap, true, settings.iterationsToRecord, settings.deltaTime,
                                 settings.noiseSTDev);
        displayImage(hitMap);
    }

    void Simulations::runPointForwardReplay(const Vector2& point, std::vector<float>& hitMap,
                                            int timesteps, float deltaTime, float noiseSTDev,
                                            EventKeyedTransportRng* transportRng) const
    {
        simulateSourceInPosition(SimulationSource(point, measuredHitProb.metadata), hitMap, true,
                                 timesteps, deltaTime, noiseSTDev, nullptr, transportRng);
    }

    static void show(const cv::Mat& mat, std::string name)
    {
        cv::Mat resized;
        cv::resize(mat, resized, cv::Size(mat.size[1] * 10, mat.size[0] * 10), 0, 0, cv::INTER_NEAREST);
        cv::imshow(name, resized);
        cv::waitKey();
        cv::destroyAllWindows();
    }

    void Simulations::displayImage(const std::vector<float>& hitMap, const std::string& imageName) const
    {
        cv::Mat asImage(hitMap);
        asImage = asImage.reshape(1, measuredHitProb.metadata.dimensions.y);
        if (settings.blurSigmaX > 0 || settings.blurSigmaY > 0)
        {
            blurHitMap(asImage);
        }

        cv::Mat inColor;
        cv::cvtColor(asImage, inColor, cv::COLOR_GRAY2BGR);

        for (int j = 0; j < measuredHitProb.metadata.dimensions.y; j++)
        {
            for (int i = 0; i < measuredHitProb.metadata.dimensions.x; i++)
            {
                if (!measuredHitProb.freeAt(i, j))
                    inColor.at<cv::Vec3f>(j, i) = cv::Vec3f(0, 0, 1);
            }
        }

#if 0
        cv::flip(inColor, inColor, 0);
        inColor *= 255;
        cv::imwrite(fmt::format("{}.png", imageName), inColor);
        GSL_WARN("hitMap image saved");
#else
        cv::flip(inColor, inColor, 0);
        show(inColor, imageName);
#endif
    }

    void Simulations::blurHitMap(cv::Mat& asImage) const
    {
        cv::GaussianBlur(asImage, asImage, cv::Size(0, 0), settings.blurSigmaX, settings.blurSigmaY);
        // divide by the blurred mask to correct the edges always getting lower
        // TODO measure performance of doing this repeatedly. Is it worth it to pre-compute and only redo it if the blur sigma has changed?
        cv::Mat blurredMask;
        cv::GaussianBlur(freeSpaceMask, blurredMask, cv::Size(0, 0), settings.blurSigmaX, settings.blurSigmaY);

        for (int i = 0; i < measuredHitProb.metadata.dimensions.y; i++)
            for (int j = 0; j < measuredHitProb.metadata.dimensions.x; j++)
                if (blurredMask.at<float>(i, j) != 0)
                    asImage.at<float>(i, j) = Utils::clamp(asImage.at<float>(i, j) / blurredMask.at<float>(i, j), 0, 1);
    }

} // namespace GSL::PMFS_internal
