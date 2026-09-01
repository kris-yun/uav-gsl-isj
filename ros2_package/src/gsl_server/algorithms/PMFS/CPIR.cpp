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

    void PMFS::recordCPIRRawSample(float measuredPpm)
    {
        if (cpirCarrierCount == 0)
            return;
        const double elapsed = (node->now() - startTime).seconds();
        const int timeIndex = static_cast<int>(std::llround(elapsed / kDt)) - 1;
        if (timeIndex < 0)
            return;
        if (timeIndex <= cpirLastTimeIndex)
            throw std::runtime_error("CPIR_DUPLICATE_OR_REVERSED_RAW_SAMPLE");
        if (cpirLastTimeIndex >= 0 && timeIndex != cpirLastTimeIndex + 1)
            throw std::runtime_error("CPIR_RAW_SAMPLE_GAP");
        if (timeIndex >= static_cast<int>(cpirTimeCount))
            throw std::runtime_error("CPIR_TIME_OUT_OF_LOOKUP");
        cpirLastTimeIndex = timeIndex;
        const Vector2Int indices = gridMetadata.coordinatesToIndices(currentRobotPosition.x, currentRobotPosition.y);
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
        if (measuring && cpirStopActive && cpirCurrentStopSamples < kStopSamples)
        {
            sample.stopIndex = cpirCurrentStopIndex;
            sample.stopSampleIndex = cpirCurrentStopSamples++;
            cpirCurrentObservedHit = cpirCurrentObservedHit || measuredPpm > kThreshold;
        }
        cpirTrace.push_back(sample);
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
        std::set<size_t> neededCells;
        for (size_t index = cpirProcessedSamples; index < cpirTrace.size(); ++index)
            neededCells.insert(cpirTrace[index].nativeCellIndex);
        const size_t worlds = cpirWorldPaths.size();
        for (const size_t nativeCell : neededCells)
        {
            if (cpirCellCache.find(nativeCell) != cpirCellCache.end())
                continue;
            const size_t stream = cpirNativeCellToStream.at(nativeCell);
            std::vector<float> values(worlds * cpirTimeCount);
            for (size_t world = 0; world < worlds; ++world)
            {
                std::ifstream input(cpirWorldPaths[world], std::ios::binary);
                char magic[8]{};
                uint32_t count = 0;
                input.read(magic, 8);
                input.read(reinterpret_cast<char*>(&count), sizeof(count));
                if (!input || std::memcmp(magic, kMagic, 8) != 0 || count != cpirCellCount)
                    throw std::runtime_error("CPIR_WORLD_HEADER");
                const std::streamoff offset = static_cast<std::streamoff>(12 + 4 * cpirCellCount +
                    4 * cpirTimeCount * stream);
                input.seekg(offset);
                input.read(reinterpret_cast<char*>(values.data() + world * cpirTimeCount),
                           4 * cpirTimeCount);
                if (!input)
                    throw std::runtime_error("CPIR_WORLD_CELL_READ");
            }
            cpirCellCache.emplace(nativeCell, std::move(values));
        }

        const double alpha = std::exp(-kDt / kTau);
        // Frozen 2x2 factorial switches. cpir_m1_m3 is not a fourth module:
        // it combines the existing raw M1 event operator with the existing M3
        // stop-resolved score. No scientific constant or formula is changed.
        const bool rawEventMode = pfdiMode == "cpir_a1" || pfdiMode == "cpir_m1_m3";
        const bool stopResolvedMode = pfdiMode == "cpir_a3" || pfdiMode == "cpir_m1_m3";
        for (size_t index = cpirProcessedSamples; index < cpirTrace.size(); ++index)
        {
            const CPIRSample& sample = cpirTrace[index];
            const auto& values = cpirCellCache.at(sample.nativeCellIndex);
            for (size_t world = 0; world < worlds; ++world)
            {
                const float physical = values[world * cpirTimeCount + sample.timeIndex];
                if (!(std::isfinite(physical) && physical >= 0.0f))
                    throw std::runtime_error("CPIR_NONFINITE_OR_NEGATIVE_PPM");
                // M2 is a physical sensor state, not a stop-local feature.  It
                // must advance for every newly consumed native sample,
                // including motion samples between stops and samples crossing
                // a source-update boundary.  Only the event ledger below is
                // restricted to the first 80 samples of a completed stop.
                if (!rawEventMode)
                {
                    const double target = cpirDelayTwo[world];
                    cpirDelayTwo[world] = cpirDelayOne[world];
                    cpirDelayOne[world] = physical;
                    cpirSensorState[world] =
                        alpha * cpirSensorState[world] + (1.0 - alpha) * target;
                    if (!(std::isfinite(cpirSensorState[world]) && cpirSensorState[world] >= 0.0))
                        throw std::runtime_error("CPIR_SENSOR_STATE_INVALID");
                }
                if (sample.stopIndex >= 0 && sample.stopSampleIndex < kStopSamples &&
                    sample.stopIndex < static_cast<int>(cpirPredictedStopHit.size()))
                {
                    if (rawEventMode)
                    {
                        if (physical > kThreshold)
                            cpirPredictedStopHit[sample.stopIndex][world] = 1;
                    }
                    else
                    {
                        if (cpirSensorState[world] > kThreshold)
                            cpirPredictedStopHit[sample.stopIndex][world] = 1;
                    }
                }
            }
        }
        cpirProcessedSamples = cpirTrace.size();

        // The ledger is cumulative, but cell payloads are not scientific state:
        // once this batch has advanced the persistent sensor for all new raw
        // samples, previously loaded cell streams are never needed again.
        // Release them at each source update so a long trajectory cannot
        // materialize the entire 626-cell bank in VM RAM.
        cpirCellCache.clear();

        const size_t stops = cpirObservedStopHit.size();
        const size_t observedReached = std::count(cpirObservedStopHit.begin(), cpirObservedStopHit.end(), 1);
        std::vector<double> score(cpirCarrierCount, 0.0);
        for (size_t source = 0; source < cpirCarrierCount; ++source)
        {
            if (stopResolvedMode)
            {
                double logLikelihood = 0.0;
                for (size_t stop = 0; stop < stops; ++stop)
                {
                    int hits = 0;
                    for (size_t member = 0; member < cpirMemberCount; ++member)
                        hits += cpirPredictedStopHit[stop][source * cpirMemberCount + member];
                    const double qsb = (0.5 + hits) /
                                       (static_cast<double>(cpirMemberCount) + 1.0);
                    logLikelihood += cpirObservedStopHit[stop]
                        ? std::log(qsb)
                        : std::log1p(-qsb);
                }
                score[source] = logLikelihood;
            }
            else
            {
                double probabilityMean = 0.0;
                for (size_t stop = 0; stop < stops; ++stop)
                {
                    int hits = 0;
                    for (size_t member = 0; member < cpirMemberCount; ++member)
                        hits += cpirPredictedStopHit[stop][source * cpirMemberCount + member];
                    probabilityMean += (0.5 + hits) /
                                       (static_cast<double>(cpirMemberCount) + 1.0);
                }
                probabilityMean /= static_cast<double>(stops);
                score[source] = observedReached * std::log(probabilityMean) +
                                (stops - observedReached) * std::log1p(-probabilityMean);
            }
        }
        const double maxScore = *std::max_element(score.begin(), score.end());
        std::vector<double> carrierPosterior(cpirCarrierCount, 0.0);
        long double carrierMassSum = 0.0L;
        for (size_t source = 0; source < cpirCarrierCount; ++source)
        {
            // The pre-gas reference is uniform over native free cells, so its
            // carrier marginal is proportional to the number of free cells in
            // that carrier.  This factor is the frozen pi_0^C(s); omitting it
            // would silently replace the PMFS cell prior by a uniform-carrier
            // prior whenever carrier sizes differ.
            carrierPosterior[source] = cpirCarrierReferenceMass[source] *
                                       std::exp(score[source] - maxScore);
            carrierMassSum += carrierPosterior[source];
        }
        if (!(std::isfinite(static_cast<double>(carrierMassSum)) && carrierMassSum > 0.0L))
            throw std::runtime_error("CPIR_CARRIER_POSTERIOR_MASS_INVALID");
        for (double& value : carrierPosterior)
            value /= static_cast<double>(carrierMassSum);

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
            const std::string id = carrierIdForCell(gridMetadata, cell);
            const auto found = cpirCarrierToIndex.find(id);
            if (found == cpirCarrierToIndex.end())
                throw std::runtime_error("CPIR_FREE_CELL_WITHOUT_CARRIER:" + id);
            const size_t carrier = found->second;
            const double refMass = cpirReferenceCellMass[cell];
            const double carrierRefMass = cpirCarrierReferenceMass[carrier];
            if (!(refMass > 0.0) || !(carrierRefMass > 0.0))
                throw std::runtime_error("CPIR_REFERENCE_MASS_INVALID");
            const double value = carrierPosterior[carrier] * refMass / carrierRefMass;
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
