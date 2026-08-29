#pragma once
#include "gsl_server/algorithms/PMFS/internal/PFDEIModularRuntime.hpp"
#include <cstddef>
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
    };

    // A runtime provider must be trajectory-independent: it must answer a
    // candidate/member query at arbitrary causally visited poses/times.  A tensor
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
        virtual std::string provenanceHash() const = 0;
    };

    inline Tensor materializePrefix(const PredictiveProvider& provider,
                                    const std::vector<SampleContext>& contexts)
    {
        if (contexts.size() < 3) throw std::invalid_argument("PF-DEI prefix has <3 samples");
        const std::size_t S = provider.sourceCount(), M = provider.memberCount();
        if (S < 2 || M < 2) throw std::invalid_argument("PF-DEI provider has insufficient support");
        Tensor out(S, std::vector<std::vector<double>>(M, std::vector<double>(contexts.size(), 0.0)));
        for (std::size_t s = 0; s < S; ++s)
            for (std::size_t m = 0; m < M; ++m)
                for (std::size_t t = 0; t < contexts.size(); ++t)
                {
                    const double c = provider.physicalPpm(s, m, contexts[t]);
                    if (!(c >= 0.0) || !std::isfinite(c))
                        throw std::runtime_error("PF-DEI provider returned invalid physical ppm");
                    out[s][m][t] = c;
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
