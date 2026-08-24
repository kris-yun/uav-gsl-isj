#include "gsl_server/algorithms/PMFS/PMFSLib.hpp"
#include "gsl_server/algorithms/PMFS/internal/EventKeyedRng.hpp"
#include "gsl_server/algorithms/PMFS/internal/HitProbability.hpp"
#include "gsl_server/algorithms/PMFS/internal/Simulations.hpp"
#include "gsl_server/algorithms/PMFS/internal/Settings.hpp"
#include "gsl_server/algorithms/PMFS/internal/VisibilityMap.hpp"
#include "gsl_server/core/Vectors.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cerrno>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <mutex>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using GSL::Grid2D;
using GSL::Grid2DMetadata;
using GSL::Occupancy;
using GSL::Vector2;
using GSL::Vector2Int;
using GSL::PMFS_internal::EventKey;
using GSL::PMFS_internal::EventKeyedTransportRng;
using GSL::PMFS_internal::HitProbability;
using GSL::PMFS_internal::SimulationSettings;
using GSL::PMFS_internal::Simulations;
using GSL::VisibilityMap;

namespace
{
    struct Candidate
    {
        std::string id;
        double x = 0;
        double y = 0;
        double nativeScore = 0;
    };

    const Candidate& nearestCarrier(const std::vector<Candidate>& candidates, double truthX, double truthY)
    {
        return *std::min_element(candidates.begin(), candidates.end(), [=](const Candidate& a, const Candidate& b)
        {
            const double da = std::hypot(a.x - truthX, a.y - truthY);
            const double db = std::hypot(b.x - truthX, b.y - truthY);
            if (da != db)
                return da < db;
            return a.id < b.id;
        });
    }

    struct Timing
    {
        uint64_t update = 0;
        double simTime = 0;
        double robotX = 0;
        double robotY = 0;
        double robotZ = 0;
        int width = 0;
        int height = 0;
        double cellSize = 0;
        double originX = 0;
        double originY = 0;
    };

    struct CellRow
    {
        size_t index = 0;
        int i = 0;
        int j = 0;
        double logOdds = 0;
        double confidence = 0;
        double omega = 0;
        double distance = 0;
        double dirX = 0;
        double dirY = 0;
        Occupancy occupancy = Occupancy::Obstacle;
    };

    std::vector<std::string> split(const std::string& line)
    {
        std::vector<std::string> out;
        std::string field;
        std::stringstream ss(line);
        while (std::getline(ss, field, ','))
        {
            if (!field.empty() && field.back() == '\r')
                field.pop_back();
            out.push_back(field);
        }
        return out;
    }

    double asDouble(const std::string& s)
    {
        errno = 0;
        char* end = nullptr;
        const double value = std::strtod(s.c_str(), &end);
        if (end == s.c_str() || *end != '\0' || !std::isfinite(value))
            throw std::runtime_error(std::string("invalid numeric field[") + s + "]");
        // C0 contains a few finite subnormal legacy values.  strtod may set
        // ERANGE for those, but their finite value is still the contract data.
        return value;
    }

    std::string firstField(const std::string& line)
    {
        const size_t p = line.find(',');
        return p == std::string::npos ? line : line.substr(0, p);
    }

    Timing readTiming(const fs::path& timingPath, const std::string& runUUID, uint64_t update)
    {
        std::ifstream in(timingPath);
        if (!in)
            throw std::runtime_error("cannot open timing file: " + timingPath.string());
        std::string line;
        std::getline(in, line);
        while (std::getline(in, line))
        {
            const size_t uuidPos = line.find(runUUID);
            if (uuidPos == std::string::npos)
                continue;
            const size_t start = uuidPos + runUUID.size();
            if (start >= line.size() || line[start] != ',')
                continue;
            auto f = split(line.substr(start + 1));
            if (f.size() < 17 || static_cast<uint64_t>(std::stoull(f[0])) != update)
                continue;
            Timing t;
            t.update = update;
            t.simTime = asDouble(f[1]);
            t.robotX = asDouble(f[8]);
            t.robotY = asDouble(f[9]);
            t.robotZ = asDouble(f[10]);
            t.width = std::stoi(f[12]);
            t.height = std::stoi(f[13]);
            t.cellSize = asDouble(f[14]);
            t.originX = asDouble(f[15]);
            t.originY = asDouble(f[16]);
            return t;
        }
        throw std::runtime_error("missing timing row for " + runUUID + " update " + std::to_string(update));
    }

    std::string readRunUUID(const fs::path& manifestPath)
    {
        std::ifstream in(manifestPath);
        if (!in)
            throw std::runtime_error("cannot open candidate manifest: " + manifestPath.string());
        std::string line;
        std::getline(in, line);
        if (!std::getline(in, line))
            throw std::runtime_error("empty candidate manifest: " + manifestPath.string());
        return firstField(line);
    }

    std::vector<Candidate> readCandidates(const fs::path& manifestPath)
    {
        std::ifstream in(manifestPath);
        if (!in)
            throw std::runtime_error("cannot open candidate manifest: " + manifestPath.string());
        std::string line;
        std::getline(in, line);
        std::vector<Candidate> result;
        while (std::getline(in, line))
        {
            if (line.empty())
                continue;
            auto f = split(line);
            if (f.size() < 12)
                continue;
            Candidate c;
            c.id = f[2];
            c.x = asDouble(f[7]);
            c.y = asDouble(f[8]);
            c.nativeScore = asDouble(f[11]);
            result.push_back(c);
        }
        if (result.empty())
            throw std::runtime_error("no candidates in " + manifestPath.string());
        return result;
    }

    std::vector<CellRow> readMeasured(const fs::path& path)
    {
        std::ifstream in(path);
        if (!in)
            throw std::runtime_error("cannot open measured map: " + path.string());
        std::string line;
        std::getline(in, line);
        std::vector<CellRow> rows;
        while (std::getline(in, line))
        {
            if (line.empty())
                continue;
            auto f = split(line);
            if (f.size() < 13)
                continue;
            CellRow r;
            r.index = static_cast<size_t>(std::stoull(f[0]));
            r.i = std::stoi(f[1]);
            r.j = std::stoi(f[2]);
            r.occupancy = f[5] == "Free" ? Occupancy::Free : Occupancy::Obstacle;
            r.logOdds = asDouble(f[7]);
            r.confidence = asDouble(f[8]);
            r.omega = asDouble(f[9]);
            r.distance = asDouble(f[10]);
            r.dirX = asDouble(f[11]);
            r.dirY = asDouble(f[12]);
            rows.push_back(r);
        }
        if (rows.empty())
            throw std::runtime_error("no measured cells in " + path.string());
        return rows;
    }

    void readWind(const fs::path& path, std::vector<Vector2>& wind)
    {
        std::ifstream in(path);
        if (!in)
            throw std::runtime_error("cannot open wind map: " + path.string());
        std::string line;
        std::getline(in, line);
        while (std::getline(in, line))
        {
            if (line.empty())
                continue;
            auto f = split(line);
            if (f.size() < 5)
                continue;
            const size_t index = static_cast<size_t>(std::stoull(f[0]));
            if (index >= wind.size())
                throw std::runtime_error("wind index out of range");
            wind[index] = Vector2(asDouble(f[3]), asDouble(f[4]));
        }
    }

    double probabilityFromLogOdds(double logOdds)
    {
        if (logOdds >= 0)
        {
            const double e = std::exp(-logOdds);
            return 1.0 / (1.0 + e);
        }
        const double e = std::exp(logOdds);
        return e / (1.0 + e);
    }

    std::array<double, 8> summary(const std::vector<HitProbability>& measured,
                                  const std::vector<Occupancy>& occupancy,
                                  const std::vector<float>* simulated)
    {
        std::vector<double> values;
        values.reserve(measured.size());
        for (size_t i = 0; i < measured.size(); ++i)
            if (occupancy[i] == Occupancy::Free && measured[i].confidence > 0)
                values.push_back(simulated ? static_cast<double>((*simulated)[i]) : probabilityFromLogOdds(measured[i].logOdds));
        if (values.empty())
            throw std::runtime_error("empty scoring support");
        std::sort(values.begin(), values.end());
        std::array<double, 8> r{};
        r[0] = std::accumulate(values.begin(), values.end(), 0.0) / values.size();
        double sq = 0;
        for (double v : values)
            sq += (v - r[0]) * (v - r[0]);
        r[1] = std::sqrt(sq / values.size());
        r[2] = values.back();
        const auto quantile = [&values](double q)
        {
            const double p = q * static_cast<double>(values.size() - 1);
            const size_t lo = static_cast<size_t>(p);
            const size_t hi = std::min(lo + 1, values.size() - 1);
            return values[lo] + (p - lo) * (values[hi] - values[lo]);
        };
        r[3] = quantile(.50);
        r[4] = quantile(.75);
        r[5] = quantile(.90);
        r[6] = quantile(.95);
        r[7] = static_cast<double>(std::count_if(values.begin(), values.end(), [](double v) { return v > 0; })) / values.size();
        return r;
    }

    void writeSummary(std::ostream& out, const std::array<double, 8>& s)
    {
        for (double v : s)
            out << ',' << std::setprecision(17) << v;
    }
}

int main(int argc, char** argv)
{
    if (argc != 5)
    {
        std::cerr << "usage: meaci_replay_true <context_bank_dir> <output_dir> <truth_x> <truth_y>\n";
        return 2;
    }
    try
    {
        const fs::path runDir = fs::absolute(argv[1]);
        const fs::path outDir = fs::absolute(argv[2]);
        const double truthX = asDouble(argv[3]);
        const double truthY = asDouble(argv[4]);
        fs::create_directories(outDir / "maps");
        const fs::path timingPath = runDir / "source_update_timing.csv";
        const fs::path firstManifest = runDir / "source_update_0001/candidate_manifest.csv";
        const std::string runUUID = readRunUUID(firstManifest);

        constexpr uint64_t globalSeed = 20260824ULL;
        constexpr uint64_t transportSubstream = 5570802872545061271ULL;
        constexpr int replicas = 8;
        std::ofstream contract(outDir / "meaci_replay_contract.json");
        contract << "{\n"
                 << "  \"contract\": \"MEACI_TRUE_CARRIER_EVENT_KEYED_R8\",\n"
                 << "  \"key\": [\"global_seed\",\"source_update_id\",\"replica_id\",\"transport_substream\"],\n"
                 << "  \"candidate_id_in_transport_key\": false,\n"
                 << "  \"fixed_trajectory_source\": \"historical_context_bank\",\n"
                 << "  \"truth_use\": \"development_nearest_carrier_selection_only\",\n"
                 << "  \"truth_x\": " << truthX << ",\n"
                 << "  \"truth_y\": " << truthY << ",\n"
                 << "  \"global_seed\": " << globalSeed << ",\n"
                 << "  \"replicas\": " << replicas << ",\n"
                 << "  \"replica_ids\": [0,1,2,3,4,5,6,7],\n"
                 << "  \"transport_substream\": " << transportSubstream << ",\n"
                 << "  \"iterationsToRecord\": 200,\n"
                 << "  \"deltaTime\": 0.2,\n"
                 << "  \"noiseSTDev\": 0.5,\n"
                 << "  \"summary\": [\"mean\",\"std_population\",\"max\",\"q50\",\"q75\",\"q90\",\"q95\",\"fraction_gt_zero\"]\n"
                 << "}\n";

        std::ofstream obs(outDir / "meaci_observation_map_summary.csv");
        obs << "run_uuid,source_update_id,sim_time,support_count,obs_mean,obs_std,obs_max,obs_q50,obs_q75,obs_q90,obs_q95,obs_fraction_gt_zero\n";
        std::ofstream candidatesOut(outDir / "meaci_true_carrier.csv");
        candidatesOut << "run_uuid,source_update_id,sim_time,candidate_id,source_x,source_y,native_score,candidate_replica_count\n";
        std::ofstream replicasOut(outDir / "meaci_replicas.csv");
        replicasOut << "run_uuid,source_update_id,sim_time,candidate_id,source_x,source_y,replica_id,global_seed,transport_substream,wall_ms,summary_mean,summary_std,summary_max,summary_q50,summary_q75,summary_q90,summary_q95,summary_fraction_gt_zero,c0p_score\n";
        std::ofstream manifestOut(outDir / "meaci_maps.csv");
        manifestOut << "run_uuid,source_update_id,sim_time,candidate_id,source_x,source_y,replica_id,map_file,cell_count,width,height,cell_size,origin_x,origin_y\n";
        std::ofstream timingOut(outDir / "source_update_timing_used.csv");
        timingOut << "run_uuid,source_update_id,sim_time,robot_x,robot_y,robot_z,width,height,cell_size,origin_x,origin_y,candidate_count\n";

        for (uint64_t update = 1; update <= 64; ++update)
        {
            const fs::path updateDir = runDir / (std::string("source_update_") + [&]() { std::ostringstream s; s << std::setw(4) << std::setfill('0') << update; return s.str(); }());
            const fs::path measuredPath = updateDir / "measured_hit_probability.csv";
            if (!fs::exists(measuredPath))
            {
                if (update == 1)
                    throw std::runtime_error("no source updates in " + runDir.string());
                break;
            }
            const Timing timing = readTiming(timingPath, runUUID, update);
            const auto cells = readMeasured(measuredPath);
            const auto candidates = readCandidates(updateDir / "candidate_manifest.csv");

            Grid2DMetadata metadata;
            metadata.dimensions = {timing.width, timing.height};
            metadata.cellSize = static_cast<float>(timing.cellSize);
            metadata.origin = {static_cast<float>(timing.originX), static_cast<float>(timing.originY)};
            metadata.scale = 1;
            metadata.numFreeCells = 0;
            const size_t n = static_cast<size_t>(timing.width * timing.height);
            std::vector<HitProbability> measured(n);
            std::vector<Occupancy> occupancy(n, Occupancy::Obstacle);
            std::vector<Vector2> wind(n, Vector2(0, 0));
            for (const auto& c : cells)
            {
                if (c.index >= n)
                    throw std::runtime_error("measured index out of range");
                measured[c.index].logOdds = c.logOdds;
                measured[c.index].confidence = c.confidence;
                measured[c.index].omega = c.omega;
                measured[c.index].distanceFromRobot = c.distance;
                measured[c.index].originalPropagationDirection = Vector2(c.dirX, c.dirY);
                occupancy[c.index] = c.occupancy;
            }
            readWind(updateDir / "estimated_wind.csv", wind);
            std::vector<double> sourceProbData(n, 0.0);
            Grid2D<HitProbability> measuredGrid(measured, occupancy, metadata);
            Grid2D<double> sourceGrid(sourceProbData, occupancy, metadata);

            SimulationSettings settings;
            settings.maxRegionSize = 5;
            settings.stepsBetweenSourceUpdates = 10;
            settings.sourceDiscriminationPower = 1.0;
            settings.refineFraction = 0.25;
            settings.maxWarmupIterations = 3;
            settings.minWarmupIterations = 1;
            settings.iterationsToRecord = 200;
            settings.deltaTime = 0.2;
            settings.noiseSTDev = 0.5;
            settings.blurSigmaX = 0;
            settings.blurSigmaY = 0;

            Simulations simulations(measuredGrid, sourceGrid, Grid2D<Vector2>(wind, occupancy, metadata), settings);
            VisibilityMap visibility(static_cast<size_t>(metadata.dimensions.x), static_cast<size_t>(metadata.dimensions.y), 5);
            GSL::PMFSLib::InitializeMap(measuredGrid, simulations, visibility, Vector2(timing.robotX, timing.robotY));

            const auto observed = summary(measured, occupancy, nullptr);
            const size_t support = static_cast<size_t>(std::count_if(measured.begin(), measured.end(), [&occupancy, &measured](const HitProbability& h)
            {
                const size_t i = static_cast<size_t>(&h - measured.data());
                return occupancy[i] == Occupancy::Free && h.confidence > 0;
            }));
            obs << runUUID << ',' << update << ',' << std::setprecision(17) << timing.simTime << ',' << support;
            writeSummary(obs, observed);
            obs << '\n';
            timingOut << runUUID << ',' << update << ',' << std::setprecision(17) << timing.simTime << ','
                      << timing.robotX << ',' << timing.robotY << ',' << timing.robotZ << ',' << timing.width << ',' << timing.height << ','
                      << timing.cellSize << ',' << timing.originX << ',' << timing.originY << ',' << candidates.size() << '\n';
            const Candidate& selected = nearestCarrier(candidates, truthX, truthY);
            candidatesOut << runUUID << ',' << update << ',' << std::setprecision(17) << timing.simTime << ',' << selected.id << ','
                          << selected.x << ',' << selected.y << ',' << selected.nativeScore << ',' << replicas << '\n';
            obs.flush();
            candidatesOut.flush();
            timingOut.flush();

            const long long taskCount = replicas;
#pragma omp parallel for schedule(dynamic)
            for (long long task = 0; task < taskCount; ++task)
            {
                const int replica = static_cast<int>(task);
                const Candidate& c = selected;
                EventKey key{globalSeed, update, static_cast<uint64_t>(replica), transportSubstream};
                EventKeyedTransportRng rng(key);
                std::vector<float> hitMap(n, 0.0f);
                const auto start = std::chrono::steady_clock::now();
                simulations.runPointForwardReplay(Vector2(c.x, c.y), hitMap, 200, 0.2f, 0.5f, &rng);
                const auto end = std::chrono::steady_clock::now();
                const double wallMs = std::chrono::duration<double, std::milli>(end - start).count();
                const auto s = summary(measured, occupancy, &hitMap);
                const long double c0p = simulations.sourceProbFromMaps(measuredGrid, hitMap);
                const std::string fileName = "update_" + [&]() { std::ostringstream s; s << std::setw(6) << std::setfill('0') << update; return s.str(); }() + "_" + c.id + "_replica_" + [&]() { std::ostringstream s; s << std::setw(2) << std::setfill('0') << replica; return s.str(); }() + ".f32";
                const fs::path mapPath = outDir / "maps" / fileName;
                std::ofstream mapFile(mapPath, std::ios::binary | std::ios::trunc);
                mapFile.write(reinterpret_cast<const char*>(hitMap.data()), static_cast<std::streamsize>(hitMap.size() * sizeof(float)));
                mapFile.close();

                std::ostringstream rep;
                rep << runUUID << ',' << update << ',' << std::setprecision(17) << timing.simTime << ',' << c.id << ',' << c.x << ',' << c.y << ','
                    << replica << ',' << globalSeed << ',' << transportSubstream << ',' << wallMs;
                writeSummary(rep, s);
                rep << ',' << static_cast<double>(c0p) << '\n';
                std::ostringstream man;
                man << runUUID << ',' << update << ',' << std::setprecision(17) << timing.simTime << ',' << c.id << ',' << c.x << ',' << c.y << ','
                    << replica << ',' << fs::absolute(mapPath).string() << ',' << n << ',' << metadata.dimensions.x << ',' << metadata.dimensions.y << ','
                    << metadata.cellSize << ',' << metadata.origin.x << ',' << metadata.origin.y << '\n';
#pragma omp critical(segi_replay_output)
                {
                    replicasOut << rep.str();
                    manifestOut << man.str();
                }
            }
            replicasOut.flush();
            manifestOut.flush();
            std::cout << "MEACI_REPLAY_UPDATE " << update << " carrier=" << selected.id << " maps=" << taskCount << std::endl;
        }
        std::cout << "MEACI_TRUE_CARRIER_REPLAY=PASS run_uuid=" << runUUID << std::endl;
        return 0;
    }
    catch (const std::exception& e)
    {
        std::cerr << "SEGI_FIXED_TRAJECTORY_REPLAY=FAIL " << e.what() << std::endl;
        return 1;
    }
}
