#include <gsl_server/algorithms/PMFS/PMFS.hpp>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <fstream>
#include <limits>
#include <stdexcept>

namespace
{
    constexpr char kMagic[] = "PFV3STR1";
    constexpr double kDt = 0.2;
    constexpr double kThreshold = 0.1;
    constexpr size_t kDwellSamples = 80;
    constexpr double kBeta0 = -1.1915279295661385;
    constexpr double kBetaK = 1.0423583775118566;
    constexpr double kBetaM = 2.9896670550884170;

    std::string carrierIdForCellCTPI(const GSL::Grid2DMetadata& gridMetadata, size_t cell)
    {
        const GSL::Vector2Int ij = gridMetadata.indices2D(cell);
        const int oi = (ij.x / 2) * 2;
        const int oj = (ij.y / 2) * 2;
        const int sx = std::min(2, gridMetadata.dimensions.x - oi);
        const int sy = std::min(2, gridMetadata.dimensions.y - oj);
        return "quadtree_" + std::to_string(oi) + "_" + std::to_string(oj) +
               "_" + std::to_string(sx) + "_" + std::to_string(sy);
    }

    constexpr double kPlumeHitRef = 0.3;

    double binaryEntropy(double p)
    {
        if (!(std::isfinite(p) && p >= 0.0 && p <= 1.0))
            throw std::runtime_error("CTPI_M3_ENTROPY_INPUT");
        if (p == 0.0 || p == 1.0)
            return 0.0;
        return -(p * std::log(p) + (1.0 - p) * std::log1p(-p));
    }

    std::array<int, 4> carrierRect(const std::string& id)
    {
        std::array<int, 4> result{};
        if (std::sscanf(id.c_str(), "quadtree_%d_%d_%d_%d",
                        &result[0], &result[1], &result[2], &result[3]) != 4)
            throw std::runtime_error("CTPI_M3_CARRIER_ID_PARSE:" + id);
        return result;
    }

    double logistic(double x)
    {
        if (x >= 0.0)
        {
            const double z = std::exp(-x);
            return 1.0 / (1.0 + z);
        }
        const double z = std::exp(x);
        return z / (1.0 + z);
    }

    double tsdcProbability(int hits, double sensorState)
    {
        if (hits < 0 || hits > 8 || !(std::isfinite(sensorState) && sensorState >= 0.0))
            throw std::runtime_error("CTPI_M2_TSDC_INPUT");
        const double p = (static_cast<double>(hits) + 0.5) / 9.0;
        const double rK = std::log(p / (1.0 - p));
        const double rM = std::log1p(sensorState / kThreshold);
        const double q = logistic(kBeta0 + kBetaK * rK + kBetaM * rM);
        if (!(std::isfinite(q) && q > 0.0 && q < 1.0))
            throw std::runtime_error("CTPI_M2_TSDC_RANGE");
        return q;
    }
}

namespace GSL
{
    std::vector<double> PMFS::evaluateCTPIActionInformation(
        const std::vector<size_t>& nativeCells,
        const std::vector<double>& travelDistancesM)
    {
        if (!ctpiPlannerEnabled || !cpirEnabled)
            throw std::runtime_error("CTPI_M3_NOT_ENABLED");
        if (nativeCells.empty() || nativeCells.size() != travelDistancesM.size())
            throw std::runtime_error("CTPI_M3_ACTION_INPUT");
        if (!(std::isfinite(ctpiDecisionSensorStatePpm) && ctpiDecisionSensorStatePpm >= 0.0))
            throw std::runtime_error("CTPI_M3_SENSOR_STATE_INVALID");

        // carrier marginal of the cell-level M1 posterior
        std::vector<double> carrierMass(cpirCarrierCount, 0.0);
        for (size_t cell = 0; cell < sourceProbability.size(); ++cell)
        {
            if (occupancy[cell] != Occupancy::Free)
                continue;
            const auto found = cpirCarrierToIndex.find(carrierIdForCellCTPI(gridMetadata, cell));
            if (found == cpirCarrierToIndex.end())
                throw std::runtime_error("CTPI_M3_CELL_WITHOUT_CARRIER");
            const double p = sourceProbability[cell];
            if (!(std::isfinite(p) && p >= 0.0))
                throw std::runtime_error("CTPI_M3_POSTERIOR_INVALID");
            carrierMass[found->second] += p;
        }
        long double posteriorSum = 0.0L;
        for (const double p : carrierMass)
            posteriorSum += p;
        if (!(std::isfinite(static_cast<double>(posteriorSum)) && posteriorSum > 0.0L))
            throw std::runtime_error("CTPI_M3_POSTERIOR_MASS");
        for (double& p : carrierMass)
            p /= static_cast<double>(posteriorSum);

        // carrier source positions (center of the 2x2 quadtree block)
        std::vector<double> carrierCx(cpirCarrierCount), carrierCy(cpirCarrierCount);
        for (size_t source = 0; source < cpirCarrierCount; ++source)
        {
            const std::array<int, 4> r = carrierRect(cpirCarrierIds[source]);
            carrierCx[source] = static_cast<double>(gridMetadata.origin.x) +
                (static_cast<double>(r[0]) + static_cast<double>(r[2]) * 0.5 + 0.5) *
                    static_cast<double>(gridMetadata.cellSize);
            carrierCy[source] = static_cast<double>(gridMetadata.origin.y) +
                (static_cast<double>(r[1]) + static_cast<double>(r[3]) * 0.5 + 0.5) *
                    static_cast<double>(gridMetadata.cellSize);
        }

        // bank-free Gaussian plume EIG: posterior-weighted concentration
        // variance across source hypotheses at each candidate action.
        const size_t nWind = cpirWindHistoryU.size();
        // M2 (F11) realtime transport: most-recent wind only.
        const size_t wBegin = (ctpiTSDCEnabled && nWind > 0) ? (nWind - 1) : 0;
        const size_t actionCount = nativeCells.size();
        std::vector<double> score(actionCount, -std::numeric_limits<double>::infinity());
        for (size_t action = 0; action < actionCount; ++action)
        {
            const Vector2 ap = gridMetadata.indexToCoordinates(nativeCells[action]);
            const double ax = static_cast<double>(ap.x);
            const double ay = static_cast<double>(ap.y);
            double mixture = 0.0;
            double conditionalEntropy = 0.0;
            for (size_t source = 0; source < cpirCarrierCount; ++source)
            {
                double best = 0.0;
                for (size_t w = wBegin; w < nWind; ++w)
                {
                    const double wu = cpirWindHistoryU[w];
                    const double wv = cpirWindHistoryV[w];
                    const double ws = std::hypot(wu, wv);
                    const double cd = ws > 1e-6 ? wu / ws : 1.0;
                    const double sd = ws > 1e-6 ? wv / ws : 0.0;
                    const double dx = (ax - carrierCx[source]) * cd + (ay - carrierCy[source]) * sd;
                    const double dy = -(ax - carrierCx[source]) * sd + (ay - carrierCy[source]) * cd;
                    if (dx > 0.15)
                    {
                        const double sigma = 0.5 * dx + 0.3;
                        const double v = (1.0 / sigma) * std::exp(-dy * dy / (2.0 * sigma * sigma)) / dx;
                        best = std::max(best, v);
                    }
                }
                // soft hit probability for source `source` at action `a`
                const double pHit = best / (best + kPlumeHitRef);
                mixture += carrierMass[source] * pHit;
                conditionalEntropy += carrierMass[source] * binaryEntropy(pHit);
            }
            const double information = binaryEntropy(mixture) - conditionalEntropy;
            if (!(std::isfinite(information) && information >= -1.0e-12))
                throw std::runtime_error("CTPI_M3_INFORMATION_INVALID");
            // M3 v3: blend explore (mutual information) with exploit
            // (posterior mass at the action cell), so EID prefers informative
            // locations near the current source belief.
            const double posteriorMass = sourceProbability[nativeCells[action]];
            score[action] = std::max(0.0, information) * (1.0 + 20.0 * posteriorMass);
        }
        return score;
    }
}
