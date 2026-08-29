#pragma once
#include "gsl_server/algorithms/PMFS/internal/PFDEIPredictiveProvider.hpp"
#include <cmath>
#include <stdexcept>
#include <vector>

namespace GSL::PMFS_internal::pfdei
{
    struct RawSample
    {
        double measuredPpm = 0.0;
        SampleContext context;
    };

    // Forward form of the same frozen deterministic sensor used by M1.
    // Input is physical C[0:T).  The returned sequence is M[delay:delay+T),
    // i.e. the measured-domain samples causally aligned with those T physical
    // inputs after the fixed sensor delay.  Zero pre-history is the benchmark
    // launch contract and matches the archived traces (first delay samples 0).
    inline std::vector<double> forwardSensorAligned(
        const std::vector<double>& physical,
        const SensorInverseConfig& cfg = {})
    {
        if (!(cfg.dt > 0.0 && cfg.tau > 0.0) || cfg.delaySamples < 1)
            throw std::invalid_argument("invalid sensor forward configuration");
        if (physical.empty())
            throw std::invalid_argument("empty physical sensor input");
        for (double v : physical)
            if (!(v >= 0.0) || !std::isfinite(v))
                throw std::invalid_argument("physical ppm must be finite nonnegative");

        const double alpha = std::exp(-cfg.dt / cfg.tau);
        const std::size_t delay = static_cast<std::size_t>(cfg.delaySamples);
        std::vector<double> measured(physical.size() + delay, 0.0);
        for (std::size_t k = 1; k < measured.size(); ++k)
        {
            const double input = k >= delay ? physical[k - delay] : 0.0;
            measured[k] = alpha * measured[k - 1] + (1.0 - alpha) * input;
        }
        return std::vector<double>(measured.begin() + static_cast<std::ptrdiff_t>(delay), measured.end());
    }

    inline Tensor forwardSensorAligned(const Tensor& physical, const SensorInverseConfig& cfg = {})
    {
        Tensor measured = physical;
        for (auto& source : measured)
            for (auto& member : source)
                member = forwardSensorAligned(member, cfg);
        return measured;
    }

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

            // M1 ablation must be a same-domain comparison.  The earlier draft
            // compared measured M directly with physical C predictions, which is
            // not a valid one-module removal.  Instead, keep the observation in
            // measured space and forward-filter every candidate physical member
            // through the same frozen source-independent sensor T.
            if (mode == Mode::AblateSensor)
            {
                const std::size_t delay = static_cast<std::size_t>(sensorConfig.delaySamples);
                if (sensorConfig.delaySamples < 1 || measured.size() <= delay + 2)
                {
                    invalid.reason = "INSUFFICIENT_ALIGNED_PREFIX";
                    return invalid;
                }
                const std::size_t physicalCount = measured.size() - delay;
                std::vector<SampleContext> physicalContexts;
                physicalContexts.reserve(physicalCount);
                for (std::size_t i = 0; i < physicalCount; ++i)
                    physicalContexts.push_back(history[i].context);

                const Tensor predictedPhysical = materializePrefix(provider, physicalContexts);
                const Tensor predictedMeasured = forwardSensorAligned(predictedPhysical, sensorConfig);
                std::vector<double> observedMeasured(
                    measured.begin() + static_cast<std::ptrdiff_t>(delay), measured.end());
                return compute(observedMeasured, predictedMeasured,
                               providerPrior(provider), referencePpm, mode);
            }

            std::vector<double> observed = deconvolveMeasuredPpm(measured, sensorConfig);
            if (observed.size() < 3)
            {
                invalid.reason = "INSUFFICIENT_ALIGNED_PREFIX";
                return invalid;
            }

            std::vector<SampleContext> contexts;
            contexts.reserve(observed.size());
            // Exact inverse returns C[0 : N-delay). Align candidate physics
            // to those causal physical times/poses; do not shift to future poses.
            for (std::size_t i = 0; i < observed.size(); ++i)
                contexts.push_back(history[i].context);

            const Tensor predicted = materializePrefix(provider, contexts);
            return compute(observed, predicted, providerPrior(provider), referencePpm, mode);
        }

    private:
        SensorInverseConfig sensorConfig;
        std::vector<RawSample> history;
    };
}
