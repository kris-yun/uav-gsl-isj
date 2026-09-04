#include <gsl_server/algorithms/PMFS/PMFS.hpp>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <iomanip>
#include <limits>
#include <set>
#include <sstream>
#include <stdexcept>

namespace
{
    constexpr char kMagic[] = "PFV3STR1";
    constexpr double kDt = 0.2;
    constexpr double kTau = 1.2;
    constexpr double kThreshold = 0.1;
    constexpr int kStopSamples = 80;

    std::vector<std::string> splitCsv(const std::string& line)
    {
        std::vector<std::string> fields;
        std::stringstream stream(line);
        std::string item;
        while (std::getline(stream, item, ','))
            fields.push_back(item);
        return fields;
    }

    std::array<int, 4> carrierRect(const std::string& id)
    {
        std::array<int, 4> result{};
        if (std::sscanf(id.c_str(), "quadtree_%d_%d_%d_%d", &result[0], &result[1], &result[2], &result[3]) != 4)
            throw std::runtime_error("CPIR_CARRIER_ID_PARSE:" + id);
        return result;
    }

    std::string carrierIdForCell(const GSL::Grid2DMetadata& gridMetadata, size_t cell)
    {
        const GSL::Vector2Int ij = gridMetadata.indices2D(cell);
        const int oi = (ij.x / 2) * 2;
        const int oj = (ij.y / 2) * 2;
        const int sx = std::min(2, gridMetadata.dimensions.x - oi);
        const int sy = std::min(2, gridMetadata.dimensions.y - oj);
        return "quadtree_" + std::to_string(oi) + "_" + std::to_string(oj) +
               "_" + std::to_string(sx) + "_" + std::to_string(sy);
    }
}

namespace GSL
{
    void PMFS::initializeCPIR()
    {
        namespace fs = std::filesystem;
        if (cpirLookupRoot.empty() || cpirAuditDirectory.empty())
            throw std::runtime_error("CPIR_CONFIG_PATH_EMPTY");
        const fs::path root(cpirLookupRoot);
        if (!fs::is_regular_file(root / "bank_summary.json") || fs::exists(root / "IN_PROGRESS"))
            throw std::runtime_error("CPIR_LOOKUP_NOT_FROZEN");

        std::ifstream cells(root / "cell_manifest.csv");
        std::string line;
        if (!std::getline(cells, line) || line != "stream_ordinal,native_cell_index,x,y")
            throw std::runtime_error("CPIR_CELL_MANIFEST_HEADER");
        size_t expectedOrdinal = 0;
        while (std::getline(cells, line))
        {
            const auto fields = splitCsv(line);
            if (fields.size() != 4 || std::stoull(fields[0]) != expectedOrdinal)
                throw std::runtime_error("CPIR_CELL_MANIFEST_ROW");
            const size_t native = std::stoull(fields[1]);
            if (native >= occupancy.size() || occupancy[native] != Occupancy::Free)
                throw std::runtime_error("CPIR_CELL_MANIFEST_NOT_FREE");
            if (!cpirNativeCellToStream.emplace(native, expectedOrdinal).second)
                throw std::runtime_error("CPIR_CELL_MANIFEST_DUPLICATE");
            ++expectedOrdinal;
        }
        cpirCellCount = expectedOrdinal;
        if (cpirCellCount != gridMetadata.numFreeCells)
            throw std::runtime_error("CPIR_FREE_CELL_COUNT_MISMATCH");
        for (size_t cell = 0; cell < occupancy.size(); ++cell)
        {
            if (occupancy[cell] == Occupancy::Free &&
                cpirNativeCellToStream.find(cell) == cpirNativeCellToStream.end())
                throw std::runtime_error("CPIR_CELL_MANIFEST_MISSING_FREE_CELL");
        }

        const fs::path member0 = root / "worlds" / "member_00";
        for (const auto& item : fs::directory_iterator(member0))
            if (item.is_regular_file() && item.path().extension() == ".bin")
                cpirCarrierIds.push_back(item.path().stem().string());
        std::sort(cpirCarrierIds.begin(), cpirCarrierIds.end());
        cpirCarrierCount = cpirCarrierIds.size();
        if (cpirCarrierCount == 0)
            throw std::runtime_error("CPIR_CARRIER_SET_EMPTY");
        for (size_t source = 0; source < cpirCarrierCount; ++source)
        {
            if (!cpirCarrierToIndex.emplace(cpirCarrierIds[source], source).second)
                throw std::runtime_error("CPIR_CARRIER_DUPLICATE");
            for (size_t member = 0; member < cpirMemberCount; ++member)
            {
                const fs::path path = root / "worlds" / ("member_0" + std::to_string(member)) /
                                      (cpirCarrierIds[source] + ".bin");
                if (!fs::is_regular_file(path))
                    throw std::runtime_error("CPIR_WORLD_MISSING:" + path.string());
                const uintmax_t expected = 12 + 4 * cpirCellCount +
                                           4 * cpirCellCount * cpirTimeCount;
                if (fs::file_size(path) != expected)
                    throw std::runtime_error("CPIR_WORLD_SIZE:" + path.string());
                cpirWorldPaths.push_back(path);
            }
        }
        const size_t worlds = cpirCarrierCount * cpirMemberCount;
        cpirReferenceCellMass.assign(gridMetadata.dimensions.x * gridMetadata.dimensions.y, 0.0);
        const double uniformFreeMass = 1.0 / static_cast<double>(cpirCellCount);
        for (const auto& entry : cpirNativeCellToStream)
            cpirReferenceCellMass[entry.first] = uniformFreeMass;
        cpirCarrierReferenceMass.assign(cpirCarrierCount, 0.0);
        for (size_t cell = 0; cell < cpirReferenceCellMass.size(); ++cell)
        {
            if (occupancy[cell] != Occupancy::Free)
                continue;
            const std::string id = carrierIdForCell(gridMetadata, cell);
            const auto found = cpirCarrierToIndex.find(id);
            if (found == cpirCarrierToIndex.end())
                throw std::runtime_error("CPIR_FREE_CELL_WITHOUT_CARRIER:" + id);
            cpirCarrierReferenceMass[found->second] += cpirReferenceCellMass[cell];
        }
        for (size_t source = 0; source < cpirCarrierReferenceMass.size(); ++source)
        {
            if (!(cpirCarrierReferenceMass[source] > 0.0))
                throw std::runtime_error("CPIR_CARRIER_REFERENCE_MASS_ZERO");
        }
        cpirSensorState.assign(worlds, 0.0);
        cpirDelayOne.assign(worlds, 0.0f);
        cpirDelayTwo.assign(worlds, 0.0f);
        // G2-M1: load precomputed steady-state peak field (carrier × member × cell).
        {
            const fs::path peakPath = root / "g2m1_peak_field.bin";
            std::ifstream peakFile(peakPath, std::ios::binary);
            char peakMagic[8]{};
            uint32_t pc = 0, pcell = 0, pm = 0;
            peakFile.read(peakMagic, 8);
            peakFile.read(reinterpret_cast<char*>(&pc), sizeof(pc));
            peakFile.read(reinterpret_cast<char*>(&pcell), sizeof(pcell));
            peakFile.read(reinterpret_cast<char*>(&pm), sizeof(pm));
            if (!peakFile || std::memcmp(peakMagic, "G2M1PK01", 8) != 0 ||
                pc != cpirCarrierCount || pcell != cpirCellCount || pm != cpirMemberCount)
                throw std::runtime_error("CPIR_PEAK_FIELD_HEADER");
            cpirPeakField.resize(static_cast<size_t>(pc) * pm * pcell);
            peakFile.read(reinterpret_cast<char*>(cpirPeakField.data()),
                          static_cast<std::streamsize>(cpirPeakField.size() * sizeof(float)));
            if (!peakFile)
                throw std::runtime_error("CPIR_PEAK_FIELD_READ");
        }
        cpirObservedCellPeak.assign(occupancy.size(), 0.0f);
        cpirObservedCellVisited.assign(occupancy.size(), 0);

        fs::create_directories(cpirAuditDirectory);
        cpirUpdateAudit.open(fs::path(cpirAuditDirectory) / "cpir_update_audit.csv",
                             std::ios::out | std::ios::trunc);
        if (!cpirUpdateAudit)
            throw std::runtime_error("CPIR_AUDIT_OPEN");
        cpirUpdateAudit << "source_update_id,sim_time,raw_samples,processed_samples,completed_stops,"
                           "observed_reaches,carriers,members,posterior_sum,min_probability,max_probability,"
                           "duplicate_samples,provider_fallback,online_batch_max_abs\n";
        GSL_INFO("CPIR initialized: carriers={}, members={}, free_cells={}, time_count={}",
                 cpirCarrierCount, cpirMemberCount, cpirCellCount, cpirTimeCount);
    }

    void PMFS::recordCPIRRawSample(float measuredPpm, double simTime)
    {
        if (cpirCarrierCount == 0)
            return;
        const int timeIndex = static_cast<int>(std::llround(simTime / kDt)) - 1;
        if (timeIndex < 0)
            return;
        if (timeIndex <= cpirLastTimeIndex)
            throw std::runtime_error("CPIR_DUPLICATE_OR_REVERSED_RAW_SAMPLE");
        if (cpirLastTimeIndex >= 0 && timeIndex != cpirLastTimeIndex + 1)
            throw std::runtime_error("CPIR_RAW_SAMPLE_GAP");
        if (timeIndex >= static_cast<int>(cpirTimeCount))
            throw std::runtime_error("CPIR_TIME_OUT_OF_LOOKUP");
        cpirLastTimeIndex = timeIndex;
        // Causal observation timestamp-pose association: bind this gas sample
        // (header.stamp = simTime) to the latest pose whose timestamp is
        // <= simTime. Never use callback-time currentRobotPosition (backlog
        // would mis-bind) and never use a future pose.
        const auto& poseHistory = resultLogging.robotPosesVector;
        if (poseHistory.empty())
            throw std::runtime_error("CPIR_NO_CAUSAL_POSE");
        size_t lo = 0, hi = poseHistory.size();
        while (lo < hi)
        {
            const size_t mid = lo + (hi - lo) / 2;
            const double t = static_cast<double>(poseHistory[mid].header.stamp.sec)
                           + static_cast<double>(poseHistory[mid].header.stamp.nanosec) * 1e-9;
            if (t <= simTime)
                lo = mid + 1;
            else
                hi = mid;
        }
        if (lo == 0)
            throw std::runtime_error("CPIR_NO_CAUSAL_POSE");
        const auto& poseMsg = poseHistory[lo - 1];
        const double poseStampUsed = static_cast<double>(poseMsg.header.stamp.sec)
                                   + static_cast<double>(poseMsg.header.stamp.nanosec) * 1e-9;
        const double poseX = static_cast<double>(poseMsg.pose.pose.position.x);
        const double poseY = static_cast<double>(poseMsg.pose.pose.position.y);
        if (poseStampUsed > simTime)
            throw std::runtime_error("CPIR_CAUSALITY_VIOLATION");
        const Vector2Int indices = gridMetadata.coordinatesToIndices(
            static_cast<float>(poseX), static_cast<float>(poseY));
        if (!gridMetadata.indicesInBounds(indices))
            throw std::runtime_error("CPIR_POSE_OUT_OF_GRID");
        const size_t nativeCell = gridMetadata.indexOf(indices);
        if (cpirNativeCellToStream.find(nativeCell) == cpirNativeCellToStream.end())
            throw std::runtime_error("CPIR_POSE_NOT_FREE_LOOKUP_CELL");

        const bool measuring = stateMachine.getCurrentState() == stopAndMeasureState.get();
        if (measuring && !cpirStopActive)
        {
            cpirStopActive = true;
            cpirCurrentStopIndex = static_cast<int>(cpirObservedStopHit.size());
            cpirCurrentStopSamples = 0;
            cpirCurrentObservedHit = false;
        }
        CPIRSample sample;
        sample.timeIndex = timeIndex;
        sample.nativeCellIndex = nativeCell;
        sample.gasStamp = simTime;
        sample.poseStampUsed = poseStampUsed;
        sample.poseAgeSec = simTime - poseStampUsed;
        sample.poseX = poseX;
        sample.poseY = poseY;
        if (measuring && cpirStopActive && cpirCurrentStopSamples < kStopSamples)
        {
            sample.stopIndex = cpirCurrentStopIndex;
            sample.stopSampleIndex = cpirCurrentStopSamples++;
            cpirCurrentObservedHit = cpirCurrentObservedHit || measuredPpm > kThreshold;
        }
        cpirTrace.push_back(sample);
        // G2-M1: accumulate per-cell observed peak for shape likelihood.
        if (measuredPpm > cpirObservedCellPeak[nativeCell])
            cpirObservedCellPeak[nativeCell] = measuredPpm;
        cpirObservedCellVisited[nativeCell] = 1;
    }

    void PMFS::finalizeCPIRPhysicalStop()
    {
        if (!cpirStopActive)
            throw std::runtime_error("CPIR_FINALIZE_WITHOUT_ACTIVE_STOP");
        if (cpirCurrentStopSamples < kStopSamples)
            throw std::runtime_error("CPIR_INCOMPLETE_PHYSICAL_STOP");
        if (cpirCurrentStopIndex != static_cast<int>(cpirObservedStopHit.size()))
            throw std::runtime_error("CPIR_STOP_LEDGER_INDEX");
        cpirObservedStopHit.push_back(cpirCurrentObservedHit ? 1 : 0);
        if (ctpiPlannerEnabled)
        {
            if (!(std::isfinite(ctpiLatestMeasuredPpm) && ctpiLatestMeasuredPpm >= 0.0))
                throw std::runtime_error("CTPI_M2_DECISION_SENSOR_STATE_INVALID");
            ctpiDecisionSensorStatePpm = ctpiLatestMeasuredPpm;
        }
        cpirPredictedStopHit.emplace_back(cpirCarrierCount * cpirMemberCount, 0);
        cpirStopActive = false;
        cpirCurrentStopIndex = -1;
        cpirCurrentStopSamples = 0;
        cpirCurrentObservedHit = false;
    }

    void PMFS::applyCPIRPosterior(uint64_t sourceUpdateId, double simTime)
    {
        if (cpirObservedStopHit.empty())
            throw std::runtime_error("CPIR_NO_COMPLETED_STOP");
        cpirProcessedSamples = cpirTrace.size();

        const size_t stops = cpirObservedStopHit.size();
        const size_t observedReached = std::count(cpirObservedStopHit.begin(), cpirObservedStopHit.end(), 1);
        // G2-M1 归一化形状似然（替代二值命中核）。位置 θ 用归一化形状，
        // 强度 q 用绝对幅值分离；8 member 平均峰值吸收 transport 不确定性。
        std::vector<size_t> visitedCells;
        std::vector<float> obsPeak;
        for (size_t cell = 0; cell < occupancy.size(); ++cell)
        {
            if (occupancy[cell] == Occupancy::Free && cpirObservedCellVisited[cell])
            {
                visitedCells.push_back(cell);
                obsPeak.push_back(cpirObservedCellPeak[cell]);
            }
        }
        const size_t N = visitedCells.size();
        if (N < 2)
            throw std::runtime_error("CPIR_INSUFFICIENT_OBSERVATION");
        const float obsMax = *std::max_element(obsPeak.begin(), obsPeak.end());
        if (!(std::isfinite(obsMax) && obsMax > 0.0f))
            throw std::runtime_error("CPIR_OBSERVATION_ZERO");
        for (float& v : obsPeak)
            v /= obsMax;
        // bank-free Gaussian plume likelihood (cell level, time-varying wind).
        // Take the max plume over the observed per-stop downwind directions so
        // opposite swings don't cancel into a meaningless mean direction.
        const size_t nWind = cpirWindHistoryU.size();
        // M2 (F11) transport prediction is realtime: use only the most recent
        // wind. F00/F10 keep the conservative max over the wind history.
        const size_t wBegin = (ctpiTSDCEnabled && nWind > 0) ? (nWind - 1) : 0;
        std::vector<double> visitedX(N), visitedY(N);
        for (size_t i = 0; i < N; ++i)
        {
            const Vector2 p = gridMetadata.indexToCoordinates(visitedCells[i]);
            visitedX[i] = static_cast<double>(p.x);
            visitedY[i] = static_cast<double>(p.y);
        }
        std::vector<double> cellScore(occupancy.size(), -std::numeric_limits<double>::infinity());
        std::vector<double> predTmp(N);
        for (size_t cell = 0; cell < occupancy.size(); ++cell)
        {
            if (occupancy[cell] != Occupancy::Free)
                continue;
            const Vector2 src = gridMetadata.indexToCoordinates(cell);
            const double sx = static_cast<double>(src.x);
            const double sy = static_cast<double>(src.y);
            double predMax = 0.0;
            for (size_t i = 0; i < N; ++i)
            {
                double pred = 0.0;
                for (size_t w = wBegin; w < nWind; ++w)
                {
                    const double wu = cpirWindHistoryU[w];
                    const double wv = cpirWindHistoryV[w];
                    const double ws = std::hypot(wu, wv);
                    const double cd = ws > 1e-6 ? wu / ws : 1.0;
                    const double sd = ws > 1e-6 ? wv / ws : 0.0;
                    const double dx = (visitedX[i] - sx) * cd + (visitedY[i] - sy) * sd;
                    const double dy = -(visitedX[i] - sx) * sd + (visitedY[i] - sy) * cd;
                    if (dx > 0.15)
                    {
                        const double sigma = 0.5 * dx + 0.3;
                        const double p = (1.0 / sigma) * std::exp(-dy * dy / (2.0 * sigma * sigma)) / dx;
                        pred = std::max(pred, p);
                    }
                }
                predTmp[i] = pred;
                predMax = std::max(predMax, pred);
            }
            if (!(predMax > 0.0))
                continue;
            double sse = 0.0;
            for (size_t i = 0; i < N; ++i)
            {
                const double d = static_cast<double>(obsPeak[i]) - predTmp[i] / predMax;
                sse += d * d;
            }
            cellScore[cell] = -100.0 * sse / static_cast<double>(N);
        }
        const double maxScore = *std::max_element(cellScore.begin(), cellScore.end());
        if (!std::isfinite(maxScore))
            throw std::runtime_error("CPIR_ALL_CARRIERS_ZERO");
        long double mass = 0.0L;
        double minimum = std::numeric_limits<double>::infinity();
        double maximum = 0.0;
        for (size_t cell = 0; cell < sourceProbability.size(); ++cell)
        {
            if (occupancy[cell] != Occupancy::Free)
            {
                sourceProbability[cell] = 0.0;
                continue;
            }
            const double value = std::exp(cellScore[cell] - maxScore);
            sourceProbability[cell] = value;
            mass += value;
        }
        if (!(std::isfinite(static_cast<double>(mass)) && mass > 0.0L))
            throw std::runtime_error("CPIR_POSTERIOR_MASS_INVALID");
        long double normalizedSum = 0.0L;
        for (size_t cell = 0; cell < sourceProbability.size(); ++cell)
        {
            if (occupancy[cell] != Occupancy::Free)
                continue;
            sourceProbability[cell] /= static_cast<double>(mass);
            minimum = std::min(minimum, sourceProbability[cell]);
            maximum = std::max(maximum, sourceProbability[cell]);
            normalizedSum += sourceProbability[cell];
        }
        const double residual = std::abs(static_cast<double>(normalizedSum) - 1.0);
        if (residual > 1e-12)
            throw std::runtime_error("CPIR_POSTERIOR_NORMALIZATION");
        cpirUpdateAudit << sourceUpdateId << ',' << std::setprecision(17) << simTime << ','
                        << cpirTrace.size() << ',' << cpirProcessedSamples << ',' << stops << ','
                        << observedReached << ',' << cpirCarrierCount << ',' << cpirMemberCount << ','
                        << static_cast<double>(normalizedSum) << ',' << minimum << ',' << maximum
                        << ",0,0," << residual << '\n';
        cpirUpdateAudit.flush();
        GSL_INFO("CPIR {} posterior update {}: stops={}, reaches={}, samples={}, carriers={}",
                 pfdiMode, sourceUpdateId, stops, observedReached, cpirProcessedSamples,
                 cpirCarrierCount);
    }
}
