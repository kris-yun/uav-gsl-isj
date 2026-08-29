#pragma once

#include "gsl_server/algorithms/PMFS/internal/PFDEIPredictiveProvider.hpp"
#include <gaden/EnvironmentConfiguration.hpp>
#include <gaden/PlaybackSimulation.hpp>
#include <gaden/core/Vectors.hpp>
#include <gaden/datatypes/LoopConfig.hpp>

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <limits>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace GSL::PMFS_internal::pfdei
{
    // Text manifest deliberately avoids a JSON dependency in the ROS runtime.
    // Format (tab-separated, paths must not contain tabs):
    // PFSNRE_PLAYBACK_V1
    // CONFIG <dir>
    // ITERATION_DT_S <seconds>
    // TIME_ORIGIN_S <seconds>
    // START_ITERATION <integer>
    // PROVENANCE <64-char-sha256>
    // SOURCE <s> <id> <prior> <cx> <cy> <width> <height> <free_count>
    // CELL   <s> <x> <y>
    // FIELD  <s> <m> <member_id> <results_dir>
    //
    // No source truth, localization result, ON/OFF result or performance field
    // is permitted in this file.
    class GadenPlaybackPredictiveProvider final : public PredictiveProvider
    {
    public:
        struct SourceGeometry
        {
            std::string id;
            long double prior = 0.0L;
            double cx = 0.0;
            double cy = 0.0;
            double width = 0.0;
            double height = 0.0;
            std::size_t freeCount = 0;
            std::vector<std::pair<double, double>> freeCells;
        };

        explicit GadenPlaybackPredictiveProvider(const std::filesystem::path& manifestPath)
            : manifestPath_(std::filesystem::absolute(manifestPath))
        {
            parseManifest();
            validateManifest();
            config_ = gaden::EnvironmentConfiguration::ReadDirectory(configDirectory_);
            if (!config_)
                throw std::runtime_error("PF-SNRE GADEN environment configuration load failed: " + configDirectory_.string());
        }

        std::size_t sourceCount() const override { return sources_.size(); }
        std::size_t memberCount() const override { return memberIds_.size(); }
        std::string sourceId(std::size_t source) const override { return sources_.at(source).id; }
        std::string memberId(std::size_t member) const override { return memberIds_.at(member); }
        long double geometryPriorMass(std::size_t source) const override { return sources_.at(source).prior; }
        std::string provenanceHash() const override { return provenance_; }
        const SourceGeometry& sourceGeometry(std::size_t source) const { return sources_.at(source); }
        const std::filesystem::path& manifestPath() const { return manifestPath_; }
        double iterationDtS() const { return iterationDtS_; }
        double timeOriginS() const { return timeOriginS_; }
        std::size_t startIteration() const { return startIteration_; }

        double physicalPpm(std::size_t source, std::size_t member,
                           const SampleContext& context) const override
        {
            const auto series = physicalSeries(source, member, std::vector<SampleContext>{context});
            return series.front();
        }

        std::vector<double> physicalSeries(std::size_t source, std::size_t member,
                                           const std::vector<SampleContext>& contexts) const override
        {
            if (source >= sourceCount() || member >= memberCount())
                throw std::out_of_range("PF-SNRE source/member index out of range");
            if (contexts.empty()) return {};

            std::vector<std::size_t> iterations;
            iterations.reserve(contexts.size());
            std::size_t previous = 0;
            bool first = true;
            for (const auto& context : contexts)
            {
                if (!std::isfinite(context.timeS) || !std::isfinite(context.x) ||
                    !std::isfinite(context.y) || !std::isfinite(context.z))
                    throw std::runtime_error("PF-SNRE nonfinite query context");
                const std::size_t iteration = iterationForTime(context.timeS);
                if (!first && iteration < previous)
                    throw std::runtime_error("PF-SNRE playback query must be chronological");
                previous = iteration;
                first = false;
                iterations.push_back(iteration);
            }

            const auto& field = fieldDirectories_.at(source).at(member);
            const auto firstIteration = iterations.front();
            requireIterationFile(field, firstIteration);
            gaden::PlaybackSimulation::Parameters params;
            params.startIteration = firstIteration;
            params.resultsDirectory = field;
            gaden::LoopConfig loop;
            loop.loop = false;
            gaden::PlaybackSimulation playback(params, config_, loop);

            std::vector<double> result;
            result.reserve(contexts.size());
            std::size_t loaded = std::numeric_limits<std::size_t>::max();
            for (std::size_t i = 0; i < contexts.size(); ++i)
            {
                const std::size_t wanted = iterations[i];
                if (loaded == std::numeric_limits<std::size_t>::max())
                {
                    requireIterationFile(field, wanted);
                    playback.AdvanceTimestep();
                    loaded = wanted;
                }
                while (loaded < wanted)
                {
                    requireIterationFile(field, loaded + 1);
                    playback.AdvanceTimestep();
                    ++loaded;
                }
                const auto& c = contexts[i];
                const float ppm = playback.SampleConcentration(
                    gaden::Vector3(static_cast<float>(c.x), static_cast<float>(c.y), static_cast<float>(c.z)));
                if (!(ppm >= 0.0f) || !std::isfinite(ppm))
                    throw std::runtime_error("PF-SNRE GADEN playback returned invalid concentration");
                result.push_back(static_cast<double>(ppm));
            }
            return result;
        }

        // Cheap asset gate. This validates the complete source/member support and
        // boundary iterations without reading every payload byte. The formal
        // preflight additionally executes spot playback and a full-prefix timing benchmark.
        void validateFieldBoundaries(std::size_t minIteration, std::size_t maxIteration) const
        {
            if (maxIteration < minIteration) throw std::invalid_argument("invalid iteration boundary");
            for (std::size_t s = 0; s < sourceCount(); ++s)
                for (std::size_t m = 0; m < memberCount(); ++m)
                {
                    requireIterationFile(fieldDirectories_[s][m], minIteration);
                    requireIterationFile(fieldDirectories_[s][m], maxIteration);
                }
        }

    private:
        std::filesystem::path manifestPath_;
        std::filesystem::path configDirectory_;
        double iterationDtS_ = 0.0;
        double timeOriginS_ = 0.0;
        std::size_t startIteration_ = 0;
        std::string provenance_;
        std::vector<SourceGeometry> sources_;
        std::vector<std::string> memberIds_;
        std::vector<std::vector<std::filesystem::path>> fieldDirectories_;
        mutable std::shared_ptr<gaden::EnvironmentConfiguration> config_;

        static std::vector<std::string> splitTabs(const std::string& line)
        {
            std::vector<std::string> out;
            std::size_t start = 0;
            while (true)
            {
                const auto pos = line.find('\t', start);
                out.emplace_back(line.substr(start, pos == std::string::npos ? pos : pos - start));
                if (pos == std::string::npos) break;
                start = pos + 1;
            }
            return out;
        }

        static bool sha256Hex(const std::string& value)
        {
            return value.size() == 64 && std::all_of(value.begin(), value.end(), [](unsigned char c)
            {
                return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
            });
        }

        std::filesystem::path resolvePath(const std::string& value) const
        {
            std::filesystem::path p(value);
            if (p.is_relative()) p = manifestPath_.parent_path() / p;
            return std::filesystem::weakly_canonical(p);
        }

        void parseManifest()
        {
            std::ifstream in(manifestPath_);
            if (!in) throw std::runtime_error("PF-SNRE playback manifest open failed: " + manifestPath_.string());
            std::string line;
            if (!std::getline(in, line) || line != "PFSNRE_PLAYBACK_V1")
                throw std::runtime_error("PF-SNRE playback manifest magic/version mismatch");

            struct PendingField { std::size_t s; std::size_t m; std::string member; std::filesystem::path dir; };
            std::vector<PendingField> pending;
            while (std::getline(in, line))
            {
                if (line.empty() || line[0] == '#') continue;
                const auto f = splitTabs(line);
                if (f.empty()) continue;
                if (f[0] == "CONFIG" && f.size() == 2) configDirectory_ = resolvePath(f[1]);
                else if (f[0] == "ITERATION_DT_S" && f.size() == 2) iterationDtS_ = std::stod(f[1]);
                else if (f[0] == "TIME_ORIGIN_S" && f.size() == 2) timeOriginS_ = std::stod(f[1]);
                else if (f[0] == "START_ITERATION" && f.size() == 2) startIteration_ = static_cast<std::size_t>(std::stoull(f[1]));
                else if (f[0] == "PROVENANCE" && f.size() == 2) provenance_ = f[1];
                else if (f[0] == "SOURCE" && f.size() == 9)
                {
                    const auto s = static_cast<std::size_t>(std::stoull(f[1]));
                    if (s != sources_.size()) throw std::runtime_error("PF-SNRE SOURCE indices must be contiguous from zero");
                    SourceGeometry g;
                    g.id = f[2]; g.prior = std::stold(f[3]); g.cx = std::stod(f[4]); g.cy = std::stod(f[5]);
                    g.width = std::stod(f[6]); g.height = std::stod(f[7]); g.freeCount = static_cast<std::size_t>(std::stoull(f[8]));
                    sources_.push_back(std::move(g));
                }
                else if (f[0] == "CELL" && f.size() == 4)
                {
                    const auto s = static_cast<std::size_t>(std::stoull(f[1]));
                    if (s >= sources_.size()) throw std::runtime_error("PF-SNRE CELL references undeclared source");
                    sources_[s].freeCells.emplace_back(std::stod(f[2]), std::stod(f[3]));
                }
                else if (f[0] == "FIELD" && f.size() == 5)
                    pending.push_back({static_cast<std::size_t>(std::stoull(f[1])), static_cast<std::size_t>(std::stoull(f[2])), f[3], resolvePath(f[4])});
                else
                    throw std::runtime_error("PF-SNRE unknown/malformed manifest record: " + line);
            }

            std::size_t maxMember = 0;
            for (const auto& p : pending) maxMember = std::max(maxMember, p.m);
            memberIds_.assign(pending.empty() ? 0 : maxMember + 1, std::string());
            fieldDirectories_.assign(sources_.size(), std::vector<std::filesystem::path>(memberIds_.size()));
            for (const auto& p : pending)
            {
                if (p.s >= sources_.size() || p.m >= memberIds_.size()) throw std::runtime_error("PF-SNRE FIELD index invalid");
                if (!memberIds_[p.m].empty() && memberIds_[p.m] != p.member) throw std::runtime_error("PF-SNRE member identity drift");
                if (!fieldDirectories_[p.s][p.m].empty()) throw std::runtime_error("PF-SNRE duplicate source/member FIELD");
                memberIds_[p.m] = p.member;
                fieldDirectories_[p.s][p.m] = p.dir;
            }
        }

        void validateManifest()
        {
            const std::string lower = manifestPath_.filename().string();
            (void)lower;
            if (configDirectory_.empty() || !std::filesystem::is_directory(configDirectory_))
                throw std::runtime_error("PF-SNRE CONFIG directory missing");
            if (!(iterationDtS_ > 0.0) || !std::isfinite(iterationDtS_) || !std::isfinite(timeOriginS_))
                throw std::runtime_error("PF-SNRE invalid iteration/time contract");
            if (!sha256Hex(provenance_)) throw std::runtime_error("PF-SNRE provenance must be lowercase SHA-256");
            if (sources_.size() < 2) throw std::runtime_error("PF-SNRE requires >=2 sources");
            if (memberIds_.size() != 8) throw std::runtime_error("PF-SNRE V2 runtime requires exactly 8 predictive members");
            long double priorSum = 0.0L;
            for (std::size_t s = 0; s < sources_.size(); ++s)
            {
                const auto& g = sources_[s];
                if (g.id.empty() || !(g.prior > 0.0L) || !std::isfinite(static_cast<double>(g.prior)) ||
                    !std::isfinite(g.cx) || !std::isfinite(g.cy) || !(g.width > 0.0) || !(g.height > 0.0) ||
                    g.freeCount == 0 || g.freeCells.size() != g.freeCount)
                    throw std::runtime_error("PF-SNRE invalid SOURCE/CELL geometry support");
                priorSum += g.prior;
                for (std::size_t m = 0; m < memberIds_.size(); ++m)
                {
                    if (memberIds_[m].empty() || fieldDirectories_[s][m].empty() || !std::filesystem::is_directory(fieldDirectories_[s][m]))
                        throw std::runtime_error("PF-SNRE incomplete source/member field support");
                }
            }
            if (std::abs(static_cast<double>(priorSum - 1.0L)) > 1e-9)
                throw std::runtime_error("PF-SNRE geometry prior is not normalized");
        }

        std::size_t iterationForTime(double timeS) const
        {
            const double q = (timeS - timeOriginS_) / iterationDtS_;
            const double rounded = std::round(q);
            if (q < -1e-9 || std::abs(q - rounded) > 1e-6)
                throw std::runtime_error("PF-SNRE sample time is not aligned to frozen GADEN iteration cadence");
            return startIteration_ + static_cast<std::size_t>(std::llround(rounded));
        }

        static void requireIterationFile(const std::filesystem::path& field, std::size_t iteration)
        {
            const auto path = field / ("iteration_" + std::to_string(iteration));
            if (!std::filesystem::is_regular_file(path))
                throw std::runtime_error("PF-SNRE missing GADEN playback iteration: " + path.string());
        }
    };
}
