#pragma once
#include "gsl_server/algorithms/PMFS/internal/PFDEIModularRuntime.hpp"
#include <cstddef>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

namespace GSL::PMFS_internal::pfdei
{
    struct SampleContext
    {
        double timeS = 0.0;
        double x = 0.0;
        double y = 0.0;
        double z = 0.0;
        double windX = 0.0;
        double windY = 0.0;
        // Exact read-only GADEN playback state when available. Formal PF-SNRE
        // closed-loop uses this value and never infers field state from callback
        // wall time. -1 is permitted only for offline/unit-test providers.
        std::int64_t playbackIteration = -1;
    };

    // A runtime provider must be trajectory-independent: it must answer a
    // candidate/member query at arbitrary causally visited poses/times. A tensor
    // pre-sampled only on historical OFF trajectories is valid for offline audit
    // but does NOT satisfy this interface for adaptive closed-loop ON runs.
    class PredictiveProvider
    {
    public:
        virtual ~PredictiveProvider() = default;
        virtual std::size_t sourceCount() const = 0;
        virtual std::size_t memberCount() const = 0;
        virtual std::string sourceId(std::size_t source) const = 0;
        virtual std::string memberId(std::size_t member) const = 0;
        virtual long double geometryPriorMass(std::size_t source) const = 0;
        virtual double physicalPpm(std::size_t source, std::size_t member,
                                   const SampleContext& context) const = 0;

        // Providers backed by chronological field playback should override this
        // method so a complete source/member trajectory is streamed once rather
        // than repeatedly reopening the field. The default remains correct for
        // simple providers and unit tests.
        virtual std::vector<double> physicalSeries(std::size_t source, std::size_t member,
                                                   const std::vector<SampleContext>& contexts) const
        {
            std::vector<double> out;
            out.reserve(contexts.size());
            for (const auto& context : contexts)
                out.push_back(physicalPpm(source, member, context));
            return out;
        }

        virtual std::string provenanceHash() const = 0;
    };

    inline Tensor materializePrefix(const PredictiveProvider& provider,
                                    const std::vector<SampleContext>& contexts)
    {
        if (contexts.size() < 3) throw std::invalid_argument("PF-DEI prefix has <3 samples");
        const std::size_t S = provider.sourceCount(), M = provider.memberCount();
        if (S < 2 || M < 2) throw std::invalid_argument("PF-DEI provider has insufficient support");
        Tensor out(S, std::vector<std::vector<double>>(M));
        for (std::size_t s = 0; s < S; ++s)
            for (std::size_t m = 0; m < M; ++m)
            {
                out[s][m] = provider.physicalSeries(s, m, contexts);
                if (out[s][m].size() != contexts.size())
                    throw std::runtime_error("PF-DEI provider returned wrong series length");
                for (double c : out[s][m])
                    if (!(c >= 0.0) || !std::isfinite(c))
                        throw std::runtime_error("PF-DEI provider returned invalid physical ppm");
            }
        return out;
    }

    inline std::vector<long double> providerPrior(const PredictiveProvider& provider)
    {
        std::vector<long double> q(provider.sourceCount());
        for (std::size_t s = 0; s < q.size(); ++s) q[s] = provider.geometryPriorMass(s);
        return normalizeMass(std::move(q));
    }
}
