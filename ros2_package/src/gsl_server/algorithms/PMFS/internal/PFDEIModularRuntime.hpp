#pragma once

// PF-DEI modular runtime core.
// Header-only, ROS-independent, truth-independent.  The adapter must supply:
//   observed measured ppm prefix;
//   candidate physical concentration prefixes [source][member][time];
//   geometry-only prior mass;
//   the fixed physical gas threshold used as log-level reference.
//
// The core intentionally separates modules so closed-loop ablations can disable
// one mechanism without changing the others.

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace GSL::PMFS_internal::pfdei
{
    enum class Mode
    {
        Full,
        Shadow,
        AblateSensor,
        AblateTemporal,
        AblateCoherence,
        AblateNuisance
    };

    inline Mode parseMode(const std::string& value)
    {
        if (value == "pfdei_full") return Mode::Full;
        if (value == "pfdei_shadow") return Mode::Shadow;
        if (value == "pfdei_ablate_sensor") return Mode::AblateSensor;
        if (value == "pfdei_ablate_temporal") return Mode::AblateTemporal;
        if (value == "pfdei_ablate_coherence") return Mode::AblateCoherence;
        if (value == "pfdei_ablate_nuisance") return Mode::AblateNuisance;
        throw std::invalid_argument("unknown PF-DEI modular mode");
    }

    struct SensorInverseConfig
    {
        double dt = 0.2;
        double tau = 1.2;
        int delaySamples = 2;
        double serializationBoundPpm = 1e-10;
    };

    struct Result
    {
        bool valid = false;
        std::string reason;
        std::vector<double> scores;
        std::vector<double> zEvidence;
        std::vector<long double> candidateMass;
        int selectedSource = -1;
    };

    inline std::vector<double> deconvolveMeasuredPpm(
        const std::vector<double>& measured,
        const SensorInverseConfig& cfg = {})
    {
        if (!(cfg.dt > 0.0 && cfg.tau > 0.0) || cfg.delaySamples < 0 ||
            !(cfg.serializationBoundPpm >= 0.0))
            throw std::invalid_argument("invalid sensor inverse configuration");
        if (measured.size() < 2)
            throw std::invalid_argument("measured prefix too short");
        for (double v : measured)
            if (!(std::isfinite(v) && v >= -cfg.serializationBoundPpm))
                throw std::invalid_argument("invalid measured ppm");

        const double alpha = std::exp(-cfg.dt / cfg.tau);
        std::vector<double> raw;
        raw.reserve(measured.size() - 1);
        for (std::size_t k = 1; k < measured.size(); ++k)
        {
            double c = (measured[k] - alpha * measured[k - 1]) / (1.0 - alpha);
            if (c < -cfg.serializationBoundPpm)
                throw std::runtime_error("sensor inverse produced materially negative concentration");
            raw.push_back(std::max(c, 0.0));
        }
        const std::size_t skip = cfg.delaySamples > 0 ? static_cast<std::size_t>(cfg.delaySamples - 1) : 0U;
        if (raw.size() <= skip)
            throw std::invalid_argument("prefix too short after delay alignment");
        return std::vector<double>(raw.begin() + static_cast<std::ptrdiff_t>(skip), raw.end());
    }

    inline std::vector<long double> normalizeMass(std::vector<long double> q)
    {
        long double total = 0.0L;
        for (long double v : q)
        {
            if (!(v >= 0.0L) || !std::isfinite(static_cast<double>(v)))
                throw std::invalid_argument("invalid prior mass");
            total += v;
        }
        if (!(total > 0.0L)) throw std::invalid_argument("zero prior mass");
        for (auto& v : q) v /= total;
        return q;
    }

    inline std::vector<double> pathVector(const std::vector<double>& x, double referencePpm, bool temporal)
    {
        if (!(referencePpm > 0.0) || !std::isfinite(referencePpm) || x.size() < 2)
            throw std::invalid_argument("invalid path/reference");
        std::vector<double> level(x.size());
        for (std::size_t i = 0; i < x.size(); ++i)
        {
            if (!(x[i] >= 0.0) || !std::isfinite(x[i]))
                throw std::invalid_argument("path ppm must be finite nonnegative");
            level[i] = std::log1p(x[i] / referencePpm);
        }
        if (!temporal) return level;
        std::vector<double> out;
        out.reserve(level.size() + level.size() - 1);
        const double sl = std::sqrt(static_cast<double>(level.size()));
        const double sd = std::sqrt(static_cast<double>(level.size() - 1));
        for (double v : level) out.push_back(v / sl);
        for (std::size_t i = 1; i < level.size(); ++i)
            out.push_back((level[i] - level[i - 1]) / sd);
        return out;
    }

    inline double euclidean(const std::vector<double>& a, const std::vector<double>& b)
    {
        if (a.size() != b.size() || a.empty()) throw std::invalid_argument("vector shape mismatch");
        long double sum = 0.0L;
        for (std::size_t i = 0; i < a.size(); ++i)
        {
            const long double d = static_cast<long double>(a[i]) - static_cast<long double>(b[i]);
            sum += d * d;
        }
        return std::sqrt(static_cast<double>(sum));
    }

    inline double pathDistance(const std::vector<double>& a, const std::vector<double>& b,
                               double referencePpm, bool temporal)
    {
        return euclidean(pathVector(a, referencePpm, temporal), pathVector(b, referencePpm, temporal));
    }

    using Tensor = std::vector<std::vector<std::vector<double>>>; // [S][M][T]

    inline void validateTensor(const std::vector<double>& observed, const Tensor& predicted)
    {
        if (observed.size() < 3 || predicted.size() < 2 || predicted[0].size() < 2)
            throw std::invalid_argument("PF-DEI requires T>=3,S>=2,M>=2");
        const std::size_t M = predicted[0].size();
        for (double v : observed)
            if (!(v >= 0.0) || !std::isfinite(v)) throw std::invalid_argument("invalid observation");
        for (const auto& source : predicted)
        {
            if (source.size() != M) throw std::invalid_argument("member count drift");
            for (const auto& member : source)
            {
                if (member.size() != observed.size()) throw std::invalid_argument("time support mismatch");
                for (double v : member)
                    if (!(v >= 0.0) || !std::isfinite(v)) throw std::invalid_argument("invalid prediction");
            }
        }
    }

    inline Tensor coherenceScramble(const Tensor& input)
    {
        if (input.empty() || input[0].empty() || input[0][0].empty())
            throw std::invalid_argument("empty tensor");
        Tensor out = input;
        const std::size_t S = input.size(), M = input[0].size(), T = input[0][0].size();
        for (std::size_t s = 0; s < S; ++s)
            for (std::size_t m = 0; m < M; ++m)
                for (std::size_t t = 0; t < T; ++t)
                    out[s][m][t] = input[s][(m + t) % M][t];
        return out;
    }

    inline std::vector<double> energyScores(const std::vector<double>& observed, const Tensor& predicted,
                                            double referencePpm, bool temporal)
    {
        validateTensor(observed, predicted);
        const std::size_t S = predicted.size(), M = predicted[0].size();
        std::vector<double> out(S, 0.0);
        for (std::size_t s = 0; s < S; ++s)
        {
            long double first = 0.0L, second = 0.0L;
            for (std::size_t m = 0; m < M; ++m)
                first += pathDistance(observed, predicted[s][m], referencePpm, temporal);
            first /= static_cast<long double>(M);
            for (std::size_t m = 0; m < M; ++m)
                for (std::size_t n = 0; n < M; ++n)
                    second += pathDistance(predicted[s][m], predicted[s][n], referencePpm, temporal);
            second /= static_cast<long double>(2 * M * M);
            out[s] = static_cast<double>(first - second);
        }
        return out;
    }

    inline std::vector<double> meanFieldScores(const std::vector<double>& observed, const Tensor& predicted,
                                               double referencePpm, bool temporal)
    {
        validateTensor(observed, predicted);
        const std::size_t S = predicted.size(), M = predicted[0].size(), T = observed.size();
        std::vector<double> out(S, 0.0);
        for (std::size_t s = 0; s < S; ++s)
        {
            std::vector<double> mean(T, 0.0);
            for (std::size_t m = 0; m < M; ++m)
                for (std::size_t t = 0; t < T; ++t)
                    mean[t] += predicted[s][m][t] / static_cast<double>(M);
            out[s] = pathDistance(observed, mean, referencePpm, temporal);
        }
        return out;
    }

    inline double normalQuantile(double probability)
    {
        const double p=std::clamp(probability,1e-12,1.0-1e-12);
        constexpr double a1=-3.969683028665376e+01,a2=2.209460984245205e+02,a3=-2.759285104469687e+02;
        constexpr double a4=1.383577518672690e+02,a5=-3.066479806614716e+01,a6=2.506628277459239e+00;
        constexpr double b1=-5.447609879822406e+01,b2=1.615858368580409e+02,b3=-1.556989798598866e+02;
        constexpr double b4=6.680131188771972e+01,b5=-1.328068155288572e+01;
        constexpr double c1=-7.784894002430293e-03,c2=-3.223964580411365e-01,c3=-2.400758277161838e+00;
        constexpr double c4=-2.549732539343734e+00,c5=4.374664141464968e+00,c6=2.938163982698783e+00;
        constexpr double d1=7.784695709041462e-03,d2=3.224671290700398e-01,d3=2.445134137142996e+00,d4=3.754408661907416e+00;
        constexpr double low=0.02425, high=1.0-low;
        if(p<low){const double q=std::sqrt(-2.0*std::log(p));return (((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6)/((((d1*q+d2)*q+d3)*q+d4)*q+1.0);}
        if(p>high){const double q=std::sqrt(-2.0*std::log(1.0-p));return -(((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6)/((((d1*q+d2)*q+d3)*q+d4)*q+1.0);}
        const double q=p-0.5,r=q*q;return (((((a1*r+a2)*r+a3)*r+a4)*r+a5)*r+a6)*q/(((((b1*r+b2)*r+b3)*r+b4)*r+b5)*r+1.0);
    }

    inline std::vector<double> normalMidrankEvidenceLowerIsBetter(const std::vector<double>& values)
    {
        const std::size_t n = values.size();
        if (n < 2) throw std::invalid_argument("need >=2 scores");
        for (double v : values) if (!std::isfinite(v)) throw std::invalid_argument("nonfinite score");
        std::vector<std::size_t> order(n); std::iota(order.begin(), order.end(), 0);
        std::stable_sort(order.begin(), order.end(), [&](std::size_t a, std::size_t b){return values[a] < values[b];});
        std::vector<double> rank(n, 0.0), z(n, 0.0);
        std::size_t begin = 0;
        while (begin < n)
        {
            std::size_t end = begin + 1;
            const double tol = 1e-12 * (1.0 + std::abs(values[order[begin]]));
            while (end < n && std::abs(values[order[end]] - values[order[begin]]) <= tol) ++end;
            const double mid = 0.5 * (static_cast<double>(begin + 1) + static_cast<double>(end));
            for (std::size_t k = begin; k < end; ++k) rank[order[k]] = mid;
            begin = end;
        }
        for (std::size_t i = 0; i < n; ++i)
        {
            const double p = 1.0 - (rank[i] - 0.5) / static_cast<double>(n);
            z[i] = normalQuantile(p);
        }
        return z;
    }

    inline std::vector<long double> reversiblePosterior(std::vector<long double> prior,
                                                         const std::vector<double>& z)
    {
        prior = normalizeMass(std::move(prior));
        if (prior.size() != z.size()) throw std::invalid_argument("posterior shape mismatch");
        std::vector<long double> logq(prior.size());
        long double maximum = -std::numeric_limits<long double>::infinity();
        const long double tiny = std::numeric_limits<long double>::min();
        for (std::size_t i = 0; i < prior.size(); ++i)
        {
            logq[i] = std::log(std::max(prior[i], tiny)) + static_cast<long double>(z[i]);
            maximum = std::max(maximum, logq[i]);
        }
        long double total = 0.0L;
        for (auto& v : logq) { v = std::exp(v - maximum); total += v; }
        for (auto& v : logq) v /= total;
        return logq;
    }

    inline Result compute(const std::vector<double>& observedPhysicalPpm,
                          const Tensor& predictedPhysicalPpm,
                          std::vector<long double> geometryPrior,
                          double referencePpm,
                          Mode mode)
    {
        Result out;
        try
        {
            Tensor p = predictedPhysicalPpm;
            if (mode == Mode::AblateCoherence) p = coherenceScramble(p);
            const bool temporal = mode != Mode::AblateTemporal;
            out.scores = (mode == Mode::AblateNuisance)
                       ? meanFieldScores(observedPhysicalPpm, p, referencePpm, temporal)
                       : energyScores(observedPhysicalPpm, p, referencePpm, temporal);
            out.zEvidence = normalMidrankEvidenceLowerIsBetter(out.scores);
            out.candidateMass = reversiblePosterior(std::move(geometryPrior), out.zEvidence);
            out.selectedSource = static_cast<int>(std::distance(
                out.candidateMass.begin(), std::max_element(out.candidateMass.begin(), out.candidateMass.end())));
            out.valid = true;
            out.reason = "OK";
        }
        catch (const std::exception& e)
        {
            out.valid = false;
            out.reason = e.what();
        }
        return out;
    }
}
