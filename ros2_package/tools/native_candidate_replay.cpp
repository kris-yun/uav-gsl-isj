#include "gsl_server/algorithms/PMFS/PMFSLib.hpp"
#include "gsl_server/algorithms/PMFS/internal/EventKeyedRng.hpp"
#include "gsl_server/algorithms/PMFS/internal/HitProbability.hpp"
#include "gsl_server/algorithms/PMFS/internal/Simulations.hpp"
#include "gsl_server/algorithms/PMFS/internal/VisibilityMap.hpp"

#include <algorithm>
#include <bit>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <unordered_map>
#include <vector>

// Standalone process. No ROS node, source truth, live callback, or dynamic
// capture. This calls the compiled PMFS transport kernel through its existing
// protected entrypoint, using the same Quadtree-mode source sampling as Native.
namespace fs = std::filesystem;
using GSL::Grid2D;
using GSL::Grid2DMetadata;
using GSL::Occupancy;
using GSL::Vector2;
using GSL::Vector2Int;
using GSL::PMFS_internal::EventKey;
using GSL::PMFS_internal::EventKeyedTransportRng;
using GSL::PMFS_internal::Filament;
using GSL::PMFS_internal::HitProbability;
using GSL::PMFS_internal::SimulationSettings;
using GSL::PMFS_internal::SimulationSource;
using GSL::PMFS_internal::Simulations;

namespace
{
    struct TraceStep
    {
        int t = 0;
        size_t active = 0, hitCells = 0, positionOffset = 0, occupancyOffset = 0;
        double meanX = 0, meanY = 0, covXX = 0, covXY = 0, covYY = 0;
    };

    struct TraceResult
    {
        std::string candidateId;
        std::vector<TraceStep> steps;
        std::vector<float> positionsXY; // two float32 values per pre-move filament
        std::vector<int32_t> transitions; // from/to cell index, -1 on exit
        std::vector<int32_t> occupiedCells; // pair: timestep, cell index
    };

    struct Replay : Simulations
    {
        using Simulations::Simulations;
        void run(const SimulationSource& source, std::vector<float>& map, EventKeyedTransportRng& rng)
        {
            simulateSourceInPosition(source, map, true, 200, 0.2f, 0.5f, nullptr, &rng);
        }

        TraceResult runTraced(const SimulationSource& source, std::vector<float>& hitMap,
                              EventKeyedTransportRng& rng)
        {
            // Offline-only mirror of Simulations::simulateSourceInPosition.
            // Movement, collision/visibility and RNG are the compiled PMFS
            // protected methods. Full-map bitwise parity with run() is
            // required before any TraceResult is written to disk.
            constexpr int releasePerStep = 5;
            const size_t reserve = static_cast<size_t>(settings.maxWarmupIterations + 200) * releasePerStep;
            std::vector<Filament> a, b;
            a.reserve(reserve); b.reserve(reserve);
            auto* active = &a;
            auto* other = &b;
            std::vector<uint16_t> updated(hitMap.size(), 0);
            uint64_t drawIndex = 0;
            bool stable = false;
            int warmupCount = 0;
            while (warmupCount < settings.minWarmupIterations ||
                   (!stable && warmupCount < settings.maxWarmupIterations))
            {
                for (int i = 0; i < releasePerStep; ++i)
                {
                    active->emplace_back();
                    active->back().position = source.getPoint();
                }
                for (Filament& filament : *active)
                {
                    auto index = measuredHitProb.metadata.coordinatesToIndices(filament.position);
                    moveFilament(filament, index, 0.2f * 2, 0.5f, &rng, drawIndex);
                    if (filamentIsOutside(filament)) stable = true;
                    else other->push_back(filament);
                }
                ++warmupCount;
                active->clear();
                std::swap(active, other);
            }

            TraceResult result;
            result.steps.reserve(200);
            for (int t = 1; t <= 200; ++t)
            {
                for (int i = 0; i < releasePerStep; ++i)
                {
                    active->emplace_back();
                    active->back().position = source.getPoint();
                }
                TraceStep step;
                step.t = t;
                step.active = active->size();
                step.positionOffset = result.positionsXY.size() / 2;
                step.occupancyOffset = result.occupiedCells.size() / 2;
                double sx = 0, sy = 0, sxx = 0, sxy = 0, syy = 0;
                for (Filament& filament : *active)
                {
                    const double x = filament.position.x, y = filament.position.y;
                    result.positionsXY.push_back(filament.position.x);
                    result.positionsXY.push_back(filament.position.y);
                    sx += x; sy += y; sxx += x * x; sxy += x * y; syy += y * y;
                    auto index = measuredHitProb.metadata.coordinatesToIndices(filament.position);
                    const size_t cell = measuredHitProb.metadata.indexOf(index);
                    if (updated[cell] < t)
                    {
                        hitMap[cell]++;
                        updated[cell] = t;
                        ++step.hitCells;
                        result.occupiedCells.push_back(t);
                        result.occupiedCells.push_back(static_cast<int32_t>(cell));
                    }
                    moveFilament(filament, index, 0.2f, 0.5f, &rng, drawIndex);
                    const bool outside = filamentIsOutside(filament);
                    const auto moved = measuredHitProb.metadata.coordinatesToIndices(filament.position);
                    result.transitions.push_back(static_cast<int32_t>(cell));
                    result.transitions.push_back(outside ? -1 : static_cast<int32_t>(measuredHitProb.metadata.indexOf(moved)));
                    if (!outside) other->push_back(filament);
                }
                if (step.active)
                {
                    const double inv = 1.0 / static_cast<double>(step.active);
                    step.meanX = sx * inv; step.meanY = sy * inv;
                    step.covXX = sxx * inv - step.meanX * step.meanX;
                    step.covXY = sxy * inv - step.meanX * step.meanY;
                    step.covYY = syy * inv - step.meanY * step.meanY;
                }
                result.steps.push_back(step);
                active->clear();
                std::swap(active, other);
            }
            for (size_t i = 0; i < hitMap.size(); ++i)
                if (measuredHitProb.occupancy[i] == Occupancy::Free)
                    hitMap[i] = hitMap[i] / 200;
            return result;
        }
    };

    struct Candidate
    {
        std::string id;
        int x = 0, y = 0, w = 0, h = 0;
        float sampledX = 0, sampledY = 0;
        double score = 0;
    };

    struct Timing
    {
        int width = 0, height = 0;
        float cellSize = 0, originX = 0, originY = 0;
        float robotX = 0, robotY = 0;
        uint64_t update = 0;
        size_t candidateCount = 0;
        std::string uuid;
    };

    std::vector<std::string> split(const std::string& line)
    {
        std::vector<std::string> out;
        std::stringstream stream(line);
        std::string field;
        while (std::getline(stream, field, ','))
        {
            if (!field.empty() && field.back() == '\r') field.pop_back();
            out.push_back(field);
        }
        return out;
    }

    std::ifstream openCsv(const fs::path& path, const std::string& expectedHeader)
    {
        std::ifstream in(path);
        if (!in) throw std::runtime_error("missing artifact: " + path.string());
        std::string header;
        std::getline(in, header);
        if (!header.empty() && header.back() == '\r') header.pop_back();
        if (header != expectedHeader) throw std::runtime_error("unexpected CSV schema: " + path.string());
        return in;
    }

    template <typename T> T number(const std::string& text)
    {
        try
        {
            if constexpr (std::is_same_v<T, int>) return std::stoi(text);
            else if constexpr (std::is_same_v<T, float> || std::is_same_v<T, double>)
            {
                char* end = nullptr;
                const double value = std::strtod(text.c_str(), &end);
                if (end == text.c_str() || *end != '\0' || !std::isfinite(value))
                    throw std::runtime_error("invalid floating field");
                return static_cast<T>(value);
            }
            else return static_cast<T>(std::stoull(text));
        }
        catch (const std::exception&)
        {
            throw std::runtime_error("invalid numeric field [" + text + "]");
        }
    }

    uint64_t readEffectiveNativeSeed(const fs::path& path)
    {
        std::ifstream in(path);
        if (!in) throw std::runtime_error("missing runtime manifest");
        const std::string text((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
        std::smatch match;
        if (!std::regex_search(text, match, std::regex("\\\"seed\\\"\\s*:\\s*([0-9]+)")))
            throw std::runtime_error("runtime seed absent");
        if (!std::regex_search(text, std::regex("\\\"arm\\\"\\s*:\\s*\\\"off\\\"")) ||
            !std::regex_search(text, std::regex("\\\"pfdi_mode\\\"\\s*:\\s*\\\"off\\\"")) ||
            !std::regex_search(text, std::regex("\\\"tnqc_mode\\\"\\s*:\\s*\\\"off\\\"")))
            throw std::runtime_error("run is not the frozen Native OFF arm");
        const uint64_t navigationSeed = number<uint64_t>(match[1].str());
        if (navigationSeed != 2)
            throw std::runtime_error("this frozen replay is bound to H01_R2026092201 navigation seed 2");
        // Frozen launch SHA 0cd1... passes 'random_seed' to the algorithm,
        // while Algorithm/PMFS reads 'seed'. The effective Native transport
        // seed is therefore its declared default zero, independently of the
        // navigation seed stored in runtime_manifest.json.
        if (text.find("0cd1ae4ad852bf548fd1ebc131e7f46f0d6d20603a2e4e71ae37c6831e40f2c9") == std::string::npos)
            throw std::runtime_error("unrecognized frozen launch hash; effective Native seed not established");
        return 0;
    }

    Timing readTiming(const fs::path& path)
    {
        auto in = openCsv(path, "run_uuid,source_update_id,sim_time,time_since_previous_update,wall_start_epoch,wall_end_epoch,native_candidate_count,native_forward_simulation_count,native_update_wall_s,robot_x,robot_y,robot_z,robot_yaw,grid_width,grid_height,cell_size,origin_x,origin_y");
        std::string line;
        if (!std::getline(in, line)) throw std::runtime_error("empty timing file");
        auto f = split(line);
        if (f.size() != 18) throw std::runtime_error("bad timing row");
        Timing t;
        t.uuid = f[0]; t.update = number<uint64_t>(f[1]);
        t.candidateCount = number<size_t>(f[6]);
        if (t.candidateCount != number<size_t>(f[7])) throw std::runtime_error("candidate/forward count disagreement");
        t.robotX = number<float>(f[9]); t.robotY = number<float>(f[10]);
        t.width = number<int>(f[13]); t.height = number<int>(f[14]);
        t.cellSize = number<float>(f[15]);
        t.originX = number<float>(f[16]); t.originY = number<float>(f[17]);
        if (std::getline(in, line)) throw std::runtime_error("expected exactly one source update");
        if (t.update != 1 || t.width <= 0 || t.height <= 0 || t.cellSize <= 0)
            throw std::runtime_error("unsupported source update or grid");
        return t;
    }

    std::vector<Candidate> readCandidates(const fs::path& path, const Timing& t)
    {
        auto in = openCsv(path, "run_uuid,source_update_id,candidate_id,origin_i,origin_j,size_i,size_j,center_x,center_y,native_source_x,native_source_y,native_score,hit_map_file");
        std::vector<Candidate> candidates;
        std::set<std::string> ids;
        std::string line;
        while (std::getline(in, line))
        {
            auto f = split(line);
            if (f.size() != 13 || f[0] != t.uuid || number<uint64_t>(f[1]) != t.update)
                throw std::runtime_error("bad candidate row or identity");
            Candidate c;
            c.id = f[2]; c.x = number<int>(f[3]); c.y = number<int>(f[4]);
            c.w = number<int>(f[5]); c.h = number<int>(f[6]);
            c.sampledX = number<float>(f[9]); c.sampledY = number<float>(f[10]);
            c.score = number<double>(f[11]);
            const std::string id = "quadtree_" + std::to_string(c.x) + "_" + std::to_string(c.y) + "_" + std::to_string(c.w) + "_" + std::to_string(c.h);
            if (c.id != id || !ids.insert(c.id).second || c.x < 0 || c.y < 0 || c.w <= 0 || c.h <= 0 ||
                c.x + c.w > t.width || c.y + c.h > t.height)
                throw std::runtime_error("invalid candidate leaf geometry/ID: " + c.id);
            candidates.push_back(c);
        }
        if (candidates.size() != t.candidateCount) throw std::runtime_error("candidate count differs from timing");
        // Deterministic source-blind prefix: a multi-cell leaf first tests
        // repeated source sampling; all remaining candidates use ID order.
        std::sort(candidates.begin(), candidates.end(), [](const Candidate& a, const Candidate& b) {
            const bool ma = a.w * a.h > 1, mb = b.w * b.h > 1;
            return ma != mb ? ma > mb : a.id < b.id;
        });
        return candidates;
    }

    using Support = std::unordered_map<size_t, float>;
    std::unordered_map<std::string, Support> readAlignment(const fs::path& path)
    {
        auto in = openCsv(path, "candidate_id,cell_index,grid_i,grid_j,x,y,measured_probability,measured_confidence,simulated_hit_probability,absolute_residual");
        std::unordered_map<std::string, Support> byCandidate;
        std::string line;
        while (std::getline(in, line))
        {
            auto f = split(line);
            if (f.size() != 10) throw std::runtime_error("bad alignment row");
            auto& support = byCandidate[f[0]];
            if (!support.emplace(number<size_t>(f[1]), number<float>(f[8])).second)
                throw std::runtime_error("duplicate support row");
        }
        return byCandidate;
    }

    std::set<std::string> validateFinalLeaves(const std::vector<Candidate>& candidates,
                                              const std::vector<Occupancy>& occupancy,
                                              const Grid2DMetadata& metadata)
    {
        std::set<std::string> terminal;
        std::vector<unsigned> coverage(occupancy.size(), 0);
        for (const Candidate& c : candidates)
        {
            bool hasEvaluatedChild = false;
            for (const Candidate& other : candidates)
            {
                if (other.id == c.id) continue;
                if (other.x >= c.x && other.y >= c.y && other.x + other.w <= c.x + c.w &&
                    other.y + other.h <= c.y + c.h && other.w * other.h < c.w * c.h)
                {
                    hasEvaluatedChild = true;
                    break;
                }
            }
            if (hasEvaluatedChild) continue;
            terminal.insert(c.id);
            for (int x = c.x; x < c.x + c.w; ++x)
                for (int y = c.y; y < c.y + c.h; ++y)
                    ++coverage[metadata.indexOf(x, y)];
        }
        for (size_t i = 0; i < occupancy.size(); ++i)
            if (coverage[i] != (occupancy[i] == Occupancy::Free ? 1u : 0u))
                throw std::runtime_error("terminal candidate leaves do not exactly partition free grid");
        return terminal;
    }

    template <typename T> bool bitsEqual(T a, T b)
    {
        if constexpr (sizeof(T) == 4)
            return std::bit_cast<uint32_t>(a) == std::bit_cast<uint32_t>(b);
        else
            return std::bit_cast<uint64_t>(a) == std::bit_cast<uint64_t>(b);
    }
}

int main(int argc, char** argv)
{
    if (argc != 4 && argc != 5)
    {
        std::cerr << "usage: native_candidate_replay <accepted_run_dir> <output_csv> <limit:1|10|all> [trace_dir]\n";
        return 2;
    }
    try
    {
        const fs::path runDir = fs::absolute(argv[1]);
        const fs::path outPath = fs::absolute(argv[2]);
        const bool traceRequested = argc == 5;
        const fs::path traceDir = traceRequested ? fs::absolute(argv[4]) : fs::path();
        if (traceRequested && fs::exists(traceDir))
            throw std::runtime_error("trace output directory already exists");
        const uint64_t seed = readEffectiveNativeSeed(runDir / "runtime_manifest.json");
        const fs::path bank = runDir / "context_bank";
        const Timing timing = readTiming(bank / "source_update_timing.csv");
        const fs::path update = bank / "source_update_0001";
        auto candidates = readCandidates(update / "candidate_manifest.csv", timing);
        const auto alignment = readAlignment(update / "candidate_support_alignment.csv");
        if (alignment.size() != candidates.size()) throw std::runtime_error("alignment candidate set mismatch");
        size_t limit = candidates.size();
        if (std::string(argv[3]) != "all") limit = number<size_t>(argv[3]);
        if (limit != 1 && limit != 10 && limit != candidates.size()) throw std::runtime_error("limit must be 1, 10 or all");
        if (limit > candidates.size()) throw std::runtime_error("limit exceeds candidate count");

        Grid2DMetadata metadata;
        metadata.dimensions = {timing.width, timing.height};
        metadata.cellSize = timing.cellSize;
        metadata.origin = {timing.originX, timing.originY};
        metadata.scale = 3;
        metadata.numFreeCells = 0;
        const size_t n = static_cast<size_t>(timing.width) * timing.height;
        std::vector<HitProbability> measured(n);
        std::vector<Occupancy> occupancy(n, Occupancy::Obstacle);
        std::vector<Vector2> wind(n, Vector2(0, 0));
        std::vector<bool> seen(n, false), windSeen(n, false);
        {
            auto in = openCsv(update / "measured_hit_probability.csv", "cell_index,grid_i,grid_j,x,y,occupancy,probability,logOdds,confidence,omega,distanceFromRobot,originalPropagationDirection_x,originalPropagationDirection_y");
            std::string line;
            while (std::getline(in, line))
            {
                auto f = split(line);
                if (f.size() != 13) throw std::runtime_error("bad measured row");
                const size_t i = number<size_t>(f[0]);
                if (i >= n || seen[i] || i != static_cast<size_t>(number<int>(f[1]) + number<int>(f[2]) * timing.width))
                    throw std::runtime_error("invalid measured cell index");
                seen[i] = true;
                occupancy[i] = f[5] == "Free" ? Occupancy::Free : Occupancy::Obstacle;
                measured[i].logOdds = number<double>(f[7]);
                measured[i].confidence = number<double>(f[8]);
                measured[i].omega = number<double>(f[9]);
                measured[i].distanceFromRobot = number<double>(f[10]);
                measured[i].originalPropagationDirection = Vector2(number<float>(f[11]), number<float>(f[12]));
            }
            if (std::count(seen.begin(), seen.end(), true) != static_cast<long>(n))
                throw std::runtime_error("measured grid is incomplete");
        }
        {
            auto in = openCsv(update / "estimated_wind.csv", "cell_index,x,y,wind_x,wind_y");
            std::string line;
            while (std::getline(in, line))
            {
                auto f = split(line);
                if (f.size() != 5) throw std::runtime_error("bad estimated wind row");
                const size_t i = number<size_t>(f[0]);
                if (i >= n || windSeen[i] || occupancy[i] != Occupancy::Free)
                    throw std::runtime_error("invalid estimated wind cell");
                windSeen[i] = true;
                wind[i] = Vector2(number<float>(f[3]), number<float>(f[4]));
            }
            for (size_t i = 0; i < n; ++i)
                if ((occupancy[i] == Occupancy::Free) != windSeen[i])
                    throw std::runtime_error("incomplete free-cell wind grid");
        }
        const auto originalOccupancy = occupancy;
        std::vector<double> posterior(n, 0.0);
        Grid2D<HitProbability> measuredGrid(measured, occupancy, metadata);
        Grid2D<double> sourceGrid(posterior, occupancy, metadata);
        SimulationSettings settings;
        settings.maxRegionSize = 5;
        settings.sourceDiscriminationPower = 1.0;
        settings.refineFraction = 0.25;
        settings.minWarmupIterations = 1;
        settings.maxWarmupIterations = 3;
        settings.iterationsToRecord = 200;
        settings.deltaTime = 0.2;
        settings.noiseSTDev = 0.5;
        settings.blurSigmaX = 0;
        settings.blurSigmaY = 0;
        Replay replay(measuredGrid, sourceGrid, Grid2D<Vector2>(wind, occupancy, metadata), settings);
        GSL::VisibilityMap visibility(static_cast<size_t>(timing.width), static_cast<size_t>(timing.height), 5);
        GSL::PMFSLib::InitializeMap(measuredGrid, replay, visibility, Vector2(timing.robotX, timing.robotY));
        if (occupancy != originalOccupancy) throw std::runtime_error("offline InitializeMap changed frozen occupancy");
        const auto terminalLeaves = validateFinalLeaves(candidates, occupancy, metadata);

        std::ofstream out(outPath, std::ios::trunc);
        if (!out) throw std::runtime_error("cannot write parity CSV");
        out << "candidate_id,terminal_leaf,source_point_exact,support_exact,native_score_exact,support_count,max_abs_support_diff,expected_score,replayed_score,expected_source_x,expected_source_y,replayed_source_x,replayed_source_y\n";
        out << std::setprecision(17);
        size_t passed = 0;
        std::vector<TraceResult> traces;
        if (traceRequested) traces.reserve(limit);
        for (size_t ci = 0; ci < limit; ++ci)
        {
            const Candidate& c = candidates[ci];
            auto expected = alignment.find(c.id);
            if (expected == alignment.end()) throw std::runtime_error("missing alignment for " + c.id);
            for (int i = c.x; i < c.x + c.w; ++i)
                for (int j = c.y; j < c.y + c.h; ++j)
                    if (occupancy[metadata.indexOf(i, j)] != Occupancy::Free)
                        throw std::runtime_error("candidate leaf includes nonfree cell: " + c.id);
            GSL::Utils::NQA::Node node(nullptr, Vector2Int(c.x, c.y), Vector2Int(c.w, c.h), replay.quadtree->map);
            EventKeyedTransportRng rng(EventKey{seed, timing.update, 0, 0x4E4154495645504DULL});
            SimulationSource source(&node, metadata, &rng);
            std::vector<float> map(n, 0.0f);
            replay.run(source, map, rng);
            const Vector2 sampled = source.firstSampledSourcePoint();
            const bool pointExact = bitsEqual(sampled.x, c.sampledX) && bitsEqual(sampled.y, c.sampledY);
            size_t supported = 0;
            bool supportExact = true;
            double maxDiff = 0.0;
            for (size_t i = 0; i < n; ++i)
            {
                if (occupancy[i] != Occupancy::Free || measured[i].confidence <= 0) continue;
                ++supported;
                auto it = expected->second.find(i);
                if (it == expected->second.end()) throw std::runtime_error("missing observed support cell");
                supportExact &= bitsEqual(map[i], it->second);
                maxDiff = std::max(maxDiff, std::abs(static_cast<double>(map[i]) - it->second));
            }
            if (supported != expected->second.size()) throw std::runtime_error("alignment has extra support rows");
            const double score = static_cast<double>(replay.sourceProbFromMaps(measuredGrid, map));
            const bool scoreExact = bitsEqual(score, c.score);
            out << c.id << ',' << terminalLeaves.contains(c.id) << ',' << pointExact << ',' << supportExact << ',' << scoreExact << ',' << supported << ','
                << maxDiff << ',' << c.score << ',' << score << ',' << c.sampledX << ',' << c.sampledY << ','
                << sampled.x << ',' << sampled.y << '\n';
            if (!pointExact || !supportExact || !scoreExact)
            {
                out.flush();
                std::cerr << "REPLAY_PARITY_FAIL candidate=" << c.id << " point=" << pointExact
                          << " support=" << supportExact << " score=" << scoreExact << " max_diff=" << maxDiff << '\n';
                return 1;
            }
            if (traceRequested)
            {
                EventKeyedTransportRng traceRng(EventKey{seed, timing.update, 0, 0x4E4154495645504DULL});
                SimulationSource traceSource(&node, metadata, &traceRng);
                std::vector<float> traceMap(n, 0.0f);
                TraceResult trace = replay.runTraced(traceSource, traceMap, traceRng);
                bool fullMapExact = true;
                for (size_t i = 0; i < n; ++i)
                    fullMapExact &= bitsEqual(traceMap[i], map[i]);
                const Vector2 tracePoint = traceSource.firstSampledSourcePoint();
                if (!fullMapExact || !bitsEqual(tracePoint.x, sampled.x) ||
                    !bitsEqual(tracePoint.y, sampled.y) || trace.steps.size() != 200)
                {
                    out.flush();
                    std::cerr << "TRACE_KERNEL_PARITY_FAIL candidate=" << c.id
                              << " full_map=" << fullMapExact << '\n';
                    return 1;
                }
                trace.candidateId = c.id;
                traces.push_back(std::move(trace));
            }
            ++passed;
        }
        if (traceRequested)
        {
            fs::create_directories(traceDir);
            std::ofstream summary(traceDir / "step_summary.csv");
            std::ofstream sparse(traceDir / "occupied_cells.csv");
            if (!summary || !sparse) throw std::runtime_error("cannot create trace summary files");
            summary << "candidate_id,source_update_id,internal_timestep,t_internal_s,active_filament_count,hit_cell_count,centroid_x,centroid_y,cov_xx,cov_xy,cov_yy,position_offset_pairs,position_count,occupancy_offset_pairs\n";
            sparse << "candidate_id,source_update_id,internal_timestep,cell_index\n";
            summary << std::setprecision(17);
            for (const TraceResult& trace : traces)
            {
                std::ofstream positions(traceDir / (trace.candidateId + "_positions_xy.f32"), std::ios::binary);
                std::ofstream transitions(traceDir / (trace.candidateId + "_transitions.i32"), std::ios::binary);
                if (!positions || !transitions) throw std::runtime_error("cannot create candidate binary traces");
                positions.write(reinterpret_cast<const char*>(trace.positionsXY.data()),
                                static_cast<std::streamsize>(trace.positionsXY.size() * sizeof(float)));
                transitions.write(reinterpret_cast<const char*>(trace.transitions.data()),
                                  static_cast<std::streamsize>(trace.transitions.size() * sizeof(int32_t)));
                if (!positions || !transitions) throw std::runtime_error("candidate binary trace write failed");
                for (const TraceStep& step : trace.steps)
                    summary << trace.candidateId << ',' << timing.update << ',' << step.t << ','
                            << step.t * 0.2 << ',' << step.active << ',' << step.hitCells << ','
                            << step.meanX << ',' << step.meanY << ',' << step.covXX << ','
                            << step.covXY << ',' << step.covYY << ',' << step.positionOffset << ','
                            << step.active << ',' << step.occupancyOffset << '\n';
                for (size_t i = 0; i < trace.occupiedCells.size(); i += 2)
                    sparse << trace.candidateId << ',' << timing.update << ','
                           << trace.occupiedCells[i] << ',' << trace.occupiedCells[i + 1] << '\n';
            }
            if (!summary || !sparse) throw std::runtime_error("trace summary write failed");
            std::ofstream contract(traceDir / "trace_contract.txt");
            contract << "STANDALONE_NATIVE_CANDIDATE_TRACE_V1\n"
                     << "source_update_id=1\n"
                     << "effective_native_seed=0\n"
                     << "internal_steps=200\n"
                     << "delta_time_s=0.2\n"
                     << "positions=pre_move_after_injection_xy_float32_pairs_per_candidate\n"
                     << "transitions=from_to_cell_index_int32_pairs_aligned_to_positions_minus_one_on_exit\n"
                     << "source_truth=false\nfuture_gas=false\nfuture_wind=false\nfuture_pose=false\n";
        }
        std::cout << "REPLAY_PARITY_PASS checked=" << passed << " bank_candidates=" << candidates.size()
                  << " seed=" << seed << " source_update=" << timing.update
                  << " final_leaves=" << terminalLeaves.size()
                  << " trace=" << (traceRequested ? "YES_FULL_MAP_VERIFIED" : "NO") << '\n';
        return 0;
    }
    catch (const std::exception& e)
    {
        std::cerr << "REPLAY_INPUT_OR_RUNTIME_FAIL " << e.what() << '\n';
        return 1;
    }
}
