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

    double binaryEntropy(double p)
    {
        if (!(std::isfinite(p) && p >= 0.0 && p <= 1.0))
            throw std::runtime_error("CTPI_M3_ENTROPY_INPUT");
        if (p == 0.0 || p == 1.0)
            return 0.0;
        return -(p * std::log(p) + (1.0 - p) * std::log1p(-p));
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
        if (cpirCarrierCount == 0 || cpirWorldPaths.size() != cpirCarrierCount * cpirMemberCount)
            throw std::runtime_error("CTPI_M3_BANK_NOT_READY");
        if (!(std::isfinite(ctpiDecisionSensorStatePpm) && ctpiDecisionSensorStatePpm >= 0.0))
            throw std::runtime_error("CTPI_M3_SENSOR_STATE_INVALID");

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

        const size_t actionCount = nativeCells.size();
        std::vector<size_t> stream(actionCount, 0);
        std::vector<int> start(actionCount, -1);
        std::vector<unsigned char> valid(actionCount, 1);
        for (size_t action = 0; action < actionCount; ++action)
        {
            const auto found = cpirNativeCellToStream.find(nativeCells[action]);
            if (found == cpirNativeCellToStream.end())
                throw std::runtime_error("CTPI_M3_ACTION_NOT_LOOKUP_CELL");
            if (!(std::isfinite(travelDistancesM[action]) && travelDistancesM[action] >= 0.0))
                throw std::runtime_error("CTPI_M3_TRAVEL_DISTANCE");
            stream[action] = found->second;
            const int travelSamples = static_cast<int>(std::ceil(
                travelDistancesM[action] / ctpiHorizontalSpeedMps / kDt));
            start[action] = cpirLastTimeIndex + 1 + travelSamples;
            if (start[action] < 0 || start[action] + static_cast<int>(kDwellSamples) > static_cast<int>(cpirTimeCount))
                valid[action] = 0;
        }

        std::vector<unsigned char> hits(actionCount * cpirCarrierCount * cpirMemberCount, 0);
        std::array<float, kDwellSamples> window{};
        for (size_t source = 0; source < cpirCarrierCount; ++source)
        {
            for (size_t member = 0; member < cpirMemberCount; ++member)
            {
                const size_t world = source * cpirMemberCount + member;
                std::ifstream input(cpirWorldPaths[world], std::ios::binary);
                char magic[8]{};
                uint32_t count = 0;
                input.read(magic, 8);
                input.read(reinterpret_cast<char*>(&count), sizeof(count));
                if (!input || std::memcmp(magic, kMagic, 8) != 0 || count != cpirCellCount)
                    throw std::runtime_error("CTPI_M3_WORLD_HEADER");
                for (size_t action = 0; action < actionCount; ++action)
                {
                    if (!valid[action])
                        continue;
                    const std::streamoff offset = static_cast<std::streamoff>(
                        12 + 4 * cpirCellCount +
                        4 * (cpirTimeCount * stream[action] + static_cast<size_t>(start[action])));
                    input.seekg(offset);
                    input.read(reinterpret_cast<char*>(window.data()),
                               static_cast<std::streamsize>(sizeof(float) * kDwellSamples));
                    if (!input)
                        throw std::runtime_error("CTPI_M3_WORLD_WINDOW_READ");
                    bool reached = false;
                    for (const float value : window)
                    {
                        if (!(std::isfinite(value) && value >= 0.0f))
                            throw std::runtime_error("CTPI_M3_WORLD_PPM");
                        reached = reached || value > kThreshold;
                    }
                    hits[(action * cpirCarrierCount + source) * cpirMemberCount + member] = reached ? 1 : 0;
                }
            }
        }

        std::vector<double> score(actionCount, -std::numeric_limits<double>::infinity());
        for (size_t action = 0; action < actionCount; ++action)
        {
            if (!valid[action])
                continue;
            double mixture = 0.0;
            double conditionalEntropy = 0.0;
            for (size_t source = 0; source < cpirCarrierCount; ++source)
            {
                int count = 0;
                for (size_t member = 0; member < cpirMemberCount; ++member)
                    count += hits[(action * cpirCarrierCount + source) * cpirMemberCount + member];
                const double probability = ctpiTSDCEnabled
                    ? tsdcProbability(count, ctpiDecisionSensorStatePpm)
                    : (static_cast<double>(count) + 0.5) / 9.0;
                mixture += carrierMass[source] * probability;
                conditionalEntropy += carrierMass[source] * binaryEntropy(probability);
            }
            const double information = binaryEntropy(mixture) - conditionalEntropy;
            if (!(std::isfinite(information) && information >= -1.0e-12))
                throw std::runtime_error("CTPI_M3_INFORMATION_INVALID");
            score[action] = std::max(0.0, information);
        }
        return score;
    }
}
