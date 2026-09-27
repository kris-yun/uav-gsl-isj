// Source-blind R1 diagnostic. Links the isolated official-PMFS library.
// Inputs are only observations, occupancy, candidate geometry and wind fields.
#include <gsl_server/algorithms/Common/Grid2D.hpp>
#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>
#include <gsl_server/algorithms/PMFS/internal/Simulations.hpp>
#ifdef R1_R2_REFERENCE_SOURCE
#include <gsl_server/algorithms/PMFS/internal/EventKeyedRng.hpp>
#endif
#include <opencv2/core.hpp>
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace GSL::PMFS_internal { void setMarkedMultiplicityCounter(std::vector<float>*); }
namespace fs = std::filesystem;
using namespace GSL;
using namespace GSL::PMFS_internal;

static std::vector<std::string> split(const std::string& line)
{
    std::vector<std::string> out;
    size_t begin = 0;
    while (true) {
        size_t end = line.find(',', begin);
        out.push_back(line.substr(begin, end == std::string::npos ? end : end - begin));
        if (end == std::string::npos) break;
        begin = end + 1;
    }
    return out;
}

using Row = std::map<std::string, std::string>;
static std::vector<Row> csv(const fs::path& path)
{
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open " + path.string());
    std::string line;
    if (!std::getline(in, line)) throw std::runtime_error("empty CSV " + path.string());
    if (!line.empty() && line.back() == '\r') line.pop_back();
    const auto header = split(line);
    std::vector<Row> result;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;
        auto values = split(line);
        if (values.size() != header.size()) throw std::runtime_error("CSV shape: " + path.string());
        Row row;
        for (size_t i = 0; i < header.size(); ++i) row.emplace(header[i], values[i]);
        result.push_back(std::move(row));
    }
    return result;
}

static double d(const Row& r, const char* key) { return std::stod(r.at(key)); }
static int integer(const Row& r, const char* key) { return std::stoi(r.at(key)); }

class Replay : public Simulations
{
public:
    using Simulations::Simulations;
    std::pair<long double, std::vector<float>> score(const Utils::NQA::Node& leaf)
    {
        std::vector<float> map(measuredHitProb.data.size(), 0.0f);
        std::vector<float> count(map.size(),0);
        setMarkedMultiplicityCounter(std::getenv("MARK_EXPORT_ON") ? &count : nullptr);
#ifdef R1_R2_REFERENCE_SOURCE
        // The frozen R2 PMFS::onGetMap calls configureNativeDeterminism with
        // algorithm seed 0 and this literal substream. Its runSimulation
        // constructs a fresh EventKeyedTransportRng per candidate at update 1.
        EventKeyedTransportRng rng(EventKey{0, 1, 0, 0x4E4154495645504DULL});
        SimulationSource source(&leaf, measuredHitProb.metadata, &rng);
        simulateSourceInPosition(source, map, true, settings.iterationsToRecord,
                                 settings.deltaTime, settings.noiseSTDev, nullptr, &rng);
#else
        SimulationSource source(&leaf, measuredHitProb.metadata);
        simulateSourceInPosition(source, map, true, settings.iterationsToRecord,
                                 settings.deltaTime, settings.noiseSTDev);
#endif
        if (settings.blurSigmaX > 0 || settings.blurSigmaY > 0) {
            cv::Mat image(map);
            image = image.reshape(1, measuredHitProb.metadata.dimensions.y);
            blurHitMap(image);
        }
        return {sourceProbFromMaps(measuredHitProb, map), std::move(map)};
    }
};

int main(int argc, char** argv)
{
    try {
        if (argc != 4) throw std::runtime_error("usage: native_pmfs_r1_forward_replay SNAPSHOT_DIR ARM OUTPUT_DIR");
        fs::path run(argv[1]), out(argv[3]);
        const std::string arm(argv[2]);
        if (arm != "A" && arm != "B" && arm != "C") throw std::runtime_error("arm must be A/B/C");
        if (fs::exists(out)) throw std::runtime_error("output exists; refusing overwrite");
        const auto snapshot = csv(run / "measured_map_at_update.csv");
        const auto candidates = csv(run / "frozen_candidate_geometry.csv");
        const auto events = csv(run / "measurement_events.csv");
        const auto windRows = csv(run / (arm == "A" ? "gmrf_wind_at_update.csv" : "wind_source_update.csv"));
        if (snapshot.empty() || candidates.empty() || events.empty() || windRows.empty())
            throw std::runtime_error("incomplete source-blind snapshot");
        if (integer(snapshot[0], "source_update_id") != 1) throw std::runtime_error("not first update");
        Grid2DMetadata meta;
        meta.dimensions = Vector2Int(integer(snapshot[0], "grid_width"), integer(snapshot[0], "grid_height"));
        meta.cellSize = static_cast<float>(d(snapshot[0], "cell_size"));
        meta.origin = Vector2(static_cast<float>(d(snapshot[0], "origin_x")),
                              static_cast<float>(d(snapshot[0], "origin_y")));
        meta.scale = 3;
        const size_t n = static_cast<size_t>(meta.dimensions.x) * meta.dimensions.y;
        if (snapshot.size() != n) throw std::runtime_error("snapshot cell count mismatch");
        std::vector<Occupancy> occupancy(n);
        std::vector<HitProbability> native(n), measured(n);
        meta.numFreeCells = 0;
        for (size_t i = 0; i < n; ++i) {
            const auto& row = snapshot[i];
            if (integer(row, "cell_index") != static_cast<int>(i) ||
                integer(row, "grid_i") != static_cast<int>(i % meta.dimensions.x) ||
                integer(row, "grid_j") != static_cast<int>(i / meta.dimensions.x))
                throw std::runtime_error("snapshot index order mismatch");
            occupancy[i] = row.at("occupancy") == "Free" ? Occupancy::Free : Occupancy::Obstacle;
            if (occupancy[i] == Occupancy::Free) ++meta.numFreeCells;
            native[i].logOdds = d(row, "log_odds");
            native[i].confidence = d(row, "confidence");
            native[i].omega = d(row, "omega");
            native[i].distanceFromRobot = d(row, "distance_from_robot");
            native[i].originalPropagationDirection = Vector2(
                static_cast<float>(d(row, "propagation_x")),
                static_cast<float>(d(row, "propagation_y")));
        }
        const long long updateStamp = std::stoll(windRows[0].at(
            arm == "A" ? "snapshot_steady_ns" : "steady_ns"));
        HitProbabilitySettings hit;
        hit.localEstimationWindowSize = 2;
        hit.maxUpdatesPerStop = arm == "C" ? 5 : 8;
        hit.prior = arm == "C" ? 0.3 : 0.1;
        hit.kernelSigma = arm == "C" ? 1.5 : 0.5;
        hit.kernelStretchConstant = 1.5;
        hit.confidenceMeasurementWeight = arm == "C" ? 1.0 : 0.5;
        hit.confidenceSigmaSpatial = arm == "C" ? 1.0 : 0.5;
        for (auto& hp : measured) { hp.auxWeight = -1; hp.setProbability(hit.prior); }
        Grid2D<HitProbability> hitGrid(measured, occupancy, meta);
        VisibilityMap visibility(meta.dimensions.x, meta.dimensions.y, 5);
        for (int x = 0; x < meta.dimensions.x; ++x) {
            for (int y = 0; y < meta.dimensions.y; ++y) {
                const Vector2Int ij(x, y);
                if (!hitGrid.freeAt(x, y)) { visibility.emplace(ij, {}); continue; }
                std::vector<Vector2Int> visible;
                for (int row = std::max(0, y - 5); row <= std::min(meta.dimensions.y - 1, y + 5); ++row)
                    for (int col = std::max(0, x - 5); col <= std::min(meta.dimensions.x - 1, x + 5); ++col) {
                        Vector2Int cell(col, row);
                        if (cell == ij || GridUtils::PathFree(meta, occupancy,
                            meta.indicesToCoordinates(ij), meta.indicesToCoordinates(cell))) visible.push_back(cell);
                    }
                visibility.emplace(ij, visible);
            }
        }
        int eventCount = 0;
        for (const auto& event : events) {
            if (std::stoll(event.at("steady_ns")) > updateStamp) continue;
            const auto cell = Vector2Int(integer(event, "robot_i"), integer(event, "robot_j"));
            if (!meta.indicesInBounds(cell) || !hitGrid.freeAt(cell)) throw std::runtime_error("event outside free grid");
            PMFSLib::EstimateHitProbabilities(hitGrid, visibility, hit,
                integer(event, "hit") != 0, d(event, "wind_direction"),
                d(event, "wind_speed"), cell);
            ++eventCount;
        }
        if (eventCount == 0) throw std::runtime_error("no events before snapshot");
        double maxLogOdds = 0, maxConfidence = 0;
        for (size_t i = 0; i < n; ++i) if (occupancy[i] == Occupancy::Free) {
            maxLogOdds = std::max(maxLogOdds, std::abs(measured[i].logOdds - native[i].logOdds));
            maxConfidence = std::max(maxConfidence, std::abs(measured[i].confidence - native[i].confidence));
        }
        if (arm == "C" && (maxLogOdds > 1e-6 || maxConfidence > 1e-6))
            throw std::runtime_error("C hit-map replay differs from live Native snapshot");
        if (windRows.size() != meta.numFreeCells) throw std::runtime_error("wind free-cell count mismatch");
        std::vector<Vector2> wind(n, Vector2(0, 0));
        std::vector<bool> windSeen(n, false);
        double windMin = INFINITY, windMax = 0;
        std::vector<double> windMagnitudes;
        for (const auto& row : windRows) {
            if (integer(row, "source_update_id") != 1) throw std::runtime_error("mixed source updates");
            int index = integer(row, "cell_index");
            if (index < 0 || static_cast<size_t>(index) >= n || windSeen[index] || occupancy[index] != Occupancy::Free)
                throw std::runtime_error("invalid wind index");
            windSeen[index] = true;
            const float u = static_cast<float>(d(row, arm == "A" ? "gmrf_u" : "internal_u"));
            const float v = static_cast<float>(d(row, arm == "A" ? "gmrf_v" : "internal_v"));
            wind[index] = Vector2(u, v);
            double magnitude = std::hypot(u, v);
            windMin = std::min(windMin, magnitude);
            windMax = std::max(windMax, magnitude);
            windMagnitudes.push_back(magnitude);
        }
        for (size_t i = 0; i < n; ++i)
            if ((occupancy[i] == Occupancy::Free) != windSeen[i]) throw std::runtime_error("incomplete wind grid");
        std::sort(windMagnitudes.begin(), windMagnitudes.end());
        SimulationSettings settings;
        settings.useWindGroundTruth = arm != "A";
        settings.maxRegionSize = 5;
        settings.sourceDiscriminationPower = arm == "C" ? 0.3 : 1.0;
        settings.refineFraction = arm == "C" ? 0.1 : 0.25;
        settings.minWarmupIterations = arm == "C" ? 200 : 1;
        settings.maxWarmupIterations = arm == "C" ? 500 : 3;
        settings.iterationsToRecord = 200;
        settings.deltaTime = arm == "C" ? 0.1 : 0.2;
        settings.noiseSTDev = 0.5;
        settings.blurSigmaX = arm == "C" ? 1.5 : 0;
        settings.blurSigmaY = arm == "C" ? 1.5 : 0;
        std::vector<double> posterior(n, 1.0 / meta.numFreeCells);
        Replay replay(Grid2D<HitProbability>(measured, occupancy, meta),
                      Grid2D<double>(posterior, occupancy, meta),
                      Grid2D<Vector2>(wind, occupancy, meta), settings);
        std::vector<std::vector<uint8_t>> occupancyMap(meta.dimensions.x,
            std::vector<uint8_t>(meta.dimensions.y, 0));
        for (int x = 0; x < meta.dimensions.x; ++x)
            for (int y = 0; y < meta.dimensions.y; ++y)
                occupancyMap[x][y] = hitGrid.freeAt(x, y) ? 1 : 0;
        replay.initializeMap(occupancyMap);
        replay.visibilityMap = &visibility;
        // Use the exported Native geometry literally for all three arms.
        std::vector<Utils::NQA::Node> frozenLeaves;
        frozenLeaves.reserve(candidates.size());
        for (const auto& row : candidates) {
            Vector2Int origin(integer(row, "origin_i"), integer(row, "origin_j"));
            Vector2Int size(integer(row, "size_i"), integer(row, "size_j"));
            const std::string expectedId = "quadtree_" + std::to_string(origin.x) + "_" +
                std::to_string(origin.y) + "_" + std::to_string(size.x) + "_" + std::to_string(size.y);
            if (row.at("candidate_id") != expectedId || size.x <= 0 || size.y <= 0)
                throw std::runtime_error("bad frozen candidate ID or dimensions");
            for (int x = origin.x; x < origin.x + size.x; ++x)
                for (int y = origin.y; y < origin.y + size.y; ++y)
                    if (!meta.indicesInBounds(Vector2Int(x, y)) || !hitGrid.freeAt(x, y))
                        throw std::runtime_error("frozen candidate includes obstacle or out-of-bounds cell");
            frozenLeaves.emplace_back(nullptr, origin, size, occupancyMap);
        }
        fs::create_directories(out / "maps");
        std::ofstream scores(out / "candidate_scores.csv");
        scores << "arm,candidate_id,origin_i,origin_j,size_i,size_j,center_x,center_y,source_score,map_file\n";
        scores << std::setprecision(21);
        for (size_t i = 0; i < candidates.size(); ++i) {
            const auto& row = candidates[i];
            auto [score, map] = replay.score(frozenLeaves[i]);
            if (!(score > 0) || !std::isfinite(score)) throw std::runtime_error("invalid candidate score");
            fs::path mapFile = fs::path("maps") / (row.at("candidate_id") + ".f32");
            std::ofstream binary(out / mapFile, std::ios::binary);
            binary.write(reinterpret_cast<const char*>(map.data()), map.size() * sizeof(float));
            if (!binary) throw std::runtime_error("failed to write candidate map");
            scores << arm << ',' << row.at("candidate_id") << ','
                   << row.at("origin_i") << ',' << row.at("origin_j") << ','
                   << row.at("size_i") << ',' << row.at("size_j") << ','
                   << row.at("center_x") << ',' << row.at("center_y") << ','
                   << score << ',' << mapFile.generic_string() << '\n';
        }
        std::ofstream audit(out / "source_blind_replay_audit.txt");
        audit << std::setprecision(17)
              << "arm=" << arm << "\nsource_truth_read=false\nobservation_events=" << eventCount
              << "\ncandidates=" << candidates.size()
              << "\nmax_live_C_log_odds_diff=" << maxLogOdds
              << "\nmax_live_C_confidence_diff=" << maxConfidence
              << "\nwind_min=" << windMin
              << "\nwind_median=" << windMagnitudes[windMagnitudes.size() / 2]
              << "\nwind_max=" << windMax << "\n";
        std::cout << "R1_SOURCE_BLIND_ARM_COMPLETE arm=" << arm << " candidates=" << candidates.size()
                  << " events=" << eventCount << " max_C_log_odds_diff=" << maxLogOdds << '\n';
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "R1_REPLAY_FAILED: " << e.what() << '\n';
        return 1;
    }
}
