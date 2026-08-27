#pragma once

// Research-only, read-only tensor export helper for CG-PC-CTT V3.
//
// This header contains no PMFS scoring logic. It serializes an already-computed
// candidate x transport-member x observed-event probability tensor so the
// Python V3 implementation can be checked for runtime parity before any
// posterior injection is attempted.

#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <string>
#include <vector>

namespace GSL::PMFS_internal
{
    struct V3ShadowCandidateRecord
    {
        std::string id;
        double x = 0.0;
        double y = 0.0;
    };

    struct V3ShadowEventRecord
    {
        uint64_t blockId = 0;
        double simTime = 0.0;
        double x = 0.0;
        double y = 0.0;
        bool hit = false;
        double concentration = 0.0;
        double threshold = 0.0;
        double windSpeed = 0.0;
        double windDirection = 0.0;
    };

    inline bool writeV3ShadowExport(
        const std::string& rootDirectory,
        const std::string& runUUID,
        uint64_t sourceUpdateId,
        double updateSimTime,
        uint64_t globalSeed,
        uint64_t transportEpoch,
        uint64_t transportSubstream,
        const std::vector<V3ShadowCandidateRecord>& candidates,
        const std::vector<V3ShadowEventRecord>& events,
        const std::vector<std::vector<std::vector<double>>>& rawProbabilities)
    {
        namespace fs = std::filesystem;
        const size_t sourceCount = candidates.size();
        const size_t eventCount = events.size();
        if (sourceCount == 0 || eventCount == 0 || rawProbabilities.size() != sourceCount)
            return false;
        const size_t memberCount = rawProbabilities.front().size();
        if (memberCount == 0)
            return false;
        for (size_t s = 0; s < sourceCount; ++s)
        {
            if (rawProbabilities[s].size() != memberCount)
                return false;
            for (size_t m = 0; m < memberCount; ++m)
                if (rawProbabilities[s][m].size() != eventCount)
                    return false;
        }

        const fs::path root(rootDirectory);
        const fs::path exportRoot = root / "v3_shadow";
        const fs::path updateDir = exportRoot / ("update_" + std::to_string(sourceUpdateId));
        // Research parity artifacts are immutable. Refuse overwrite rather
        // than silently mixing two source updates with the same id.
        if (fs::exists(updateDir))
            return false;
        fs::create_directories(updateDir);

        const fs::path candidateTmp = updateDir / "candidates.csv.tmp";
        const fs::path candidateFinal = updateDir / "candidates.csv";
        {
            std::ofstream out(candidateTmp, std::ios::out | std::ios::trunc);
            if (!out.is_open()) return false;
            out << "candidate_index,candidate_id,source_x,source_y\n";
            out << std::setprecision(17);
            for (size_t s = 0; s < sourceCount; ++s)
                out << s << ',' << candidates[s].id << ',' << candidates[s].x << ',' << candidates[s].y << '\n';
            out.flush();
            if (!out.good()) return false;
        }
        fs::rename(candidateTmp, candidateFinal);

        const fs::path eventTmp = updateDir / "events.csv.tmp";
        const fs::path eventFinal = updateDir / "events.csv";
        {
            std::ofstream out(eventTmp, std::ios::out | std::ios::trunc);
            if (!out.is_open()) return false;
            out << "event_index,block_id,sim_time,x,y,hit,concentration,threshold,wind_speed,wind_direction\n";
            out << std::setprecision(17);
            for (size_t e = 0; e < eventCount; ++e)
                out << e << ',' << events[e].blockId << ',' << events[e].simTime << ','
                    << events[e].x << ',' << events[e].y << ',' << (events[e].hit ? 1 : 0) << ','
                    << events[e].concentration << ',' << events[e].threshold << ','
                    << events[e].windSpeed << ',' << events[e].windDirection << '\n';
            out.flush();
            if (!out.good()) return false;
        }
        fs::rename(eventTmp, eventFinal);

        // Row-major tensor order is [source][member][event]. Probabilities are
        // written as IEEE float32 because the underlying PMFS hit map is float.
        const fs::path tensorTmp = updateDir / "raw_probabilities_sme.f32.tmp";
        const fs::path tensorFinal = updateDir / "raw_probabilities_sme.f32";
        {
            std::ofstream out(tensorTmp, std::ios::binary | std::ios::trunc);
            if (!out.is_open()) return false;
            for (size_t s = 0; s < sourceCount; ++s)
                for (size_t m = 0; m < memberCount; ++m)
                    for (size_t e = 0; e < eventCount; ++e)
                    {
                        const double p = rawProbabilities[s][m][e];
                        if (!(p >= 0.0 && p <= 1.0))
                            return false;
                        const float pf = static_cast<float>(p);
                        out.write(reinterpret_cast<const char*>(&pf), sizeof(float));
                    }
            out.flush();
            if (!out.good()) return false;
        }
        fs::rename(tensorTmp, tensorFinal);

        const fs::path contractTmp = updateDir / "contract.json.tmp";
        const fs::path contractFinal = updateDir / "contract.json";
        {
            std::ofstream out(contractTmp, std::ios::out | std::ios::trunc);
            if (!out.is_open()) return false;
            out << std::setprecision(17)
                << "{\n"
                << "  \"contract\": \"CG_PC_CTT_V3_RUNTIME_SHADOW_RAW_SME_V1\",\n"
                << "  \"read_only_shadow\": true,\n"
                << "  \"posterior_injection\": false,\n"
                << "  \"source_truth_used\": false,\n"
                << "  \"run_uuid\": \"" << runUUID << "\",\n"
                << "  \"source_update_id\": " << sourceUpdateId << ",\n"
                << "  \"update_sim_time\": " << updateSimTime << ",\n"
                << "  \"shape_sme\": [" << sourceCount << ',' << memberCount << ',' << eventCount << "],\n"
                << "  \"dtype\": \"float32_little_endian_native\",\n"
                << "  \"tensor_order\": \"source_member_event\",\n"
                << "  \"value_semantics\": \"PMFS_hit_probability_at_actual_event_position_before_EC_ECDL_Hellinger_normalization\",\n"
                << "  \"global_seed\": " << globalSeed << ",\n"
                << "  \"transport_epoch\": " << transportEpoch << ",\n"
                << "  \"transport_substream\": " << transportSubstream << ",\n"
                << "  \"candidate_id_in_transport_key\": false,\n"
                << "  \"files\": {\n"
                << "    \"candidates\": \"candidates.csv\",\n"
                << "    \"events\": \"events.csv\",\n"
                << "    \"raw_probabilities\": \"raw_probabilities_sme.f32\"\n"
                << "  }\n"
                << "}\n";
            out.flush();
            if (!out.good()) return false;
        }
        fs::rename(contractTmp, contractFinal);
        return true;
    }
}
