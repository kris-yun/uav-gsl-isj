#pragma once
#include "gsl_server/algorithms/PMFS/internal/PFDEIPredictiveProvider.hpp"
#include <stdexcept>
#include <vector>

namespace GSL::PMFS_internal::pfdei
{
    struct RawSample
    {
        double measuredPpm = 0.0;
        SampleContext context;
    };

    class Engine
    {
    public:
        explicit Engine(SensorInverseConfig sensor = {}) : sensorConfig(sensor) {}

        void clear() { history.clear(); }

        void append(const RawSample& sample)
        {
            if (!(sample.measuredPpm >= 0.0) || !std::isfinite(sample.measuredPpm))
                throw std::invalid_argument("PF-DEI measured ppm must be finite nonnegative");
            if (!history.empty() && !(sample.context.timeS > history.back().context.timeS))
                throw std::invalid_argument("PF-DEI sample time must increase strictly");
            history.push_back(sample);
        }

        std::size_t sampleCount() const { return history.size(); }

        Result infer(const PredictiveProvider& provider, double referencePpm, Mode mode) const
        {
            Result invalid;
            if (history.size() < 4)
            {
                invalid.reason = "INSUFFICIENT_PREFIX";
                return invalid;
            }

            std::vector<double> measured;
            measured.reserve(history.size());
            for (const auto& s : history) measured.push_back(s.measuredPpm);

            std::vector<double> observed;
            std::vector<SampleContext> contexts;
            if (mode == Mode::AblateSensor)
            {
                observed = measured;
                contexts.reserve(history.size());
                for (const auto& s : history) contexts.push_back(s.context);
            }
            else
            {
                observed = deconvolveMeasuredPpm(measured, sensorConfig);
                contexts.reserve(observed.size());
                // Exact inverse returns C[0 : N-delay). Align candidate physics
                // to those causal physical times/poses; do not shift to future poses.
                for (std::size_t i = 0; i < observed.size(); ++i)
                    contexts.push_back(history[i].context);
            }

            if (observed.size() < 3)
            {
                invalid.reason = "INSUFFICIENT_ALIGNED_PREFIX";
                return invalid;
            }
            const Tensor predicted = materializePrefix(provider, contexts);
            return compute(observed, predicted, providerPrior(provider), referencePpm, mode);
        }

    private:
        SensorInverseConfig sensorConfig;
        std::vector<RawSample> history;
    };
}
