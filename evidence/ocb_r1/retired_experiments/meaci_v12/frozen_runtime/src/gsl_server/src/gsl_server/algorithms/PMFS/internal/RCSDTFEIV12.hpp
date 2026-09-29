#pragma once

#include <Eigen/Dense>
#include <Eigen/Eigenvalues>
#include <gsl_server/algorithms/PMFS/internal/EventKeyedRng.hpp>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <unordered_map>
#include <utility>
#include <vector>

namespace GSL::PMFS_internal::rc_sd_tfei_v12
{
    inline constexpr std::size_t kTransportMembers = 8;
    inline constexpr std::size_t kMainModelErrorMembers = 1;
    inline constexpr std::size_t kModelErrorMembers = 8;
    inline constexpr std::size_t kCrossedMembers =
        kTransportMembers * kModelErrorMembers;
    inline constexpr std::array<std::size_t, 4> kFoldACalibration{0, 2, 4, 6};
    inline constexpr std::array<std::size_t, 4> kFoldAScoring{1, 3, 5, 7};
    inline constexpr std::array<std::size_t, 4> kFoldBCalibration{1, 3, 5, 7};
    inline constexpr std::array<std::size_t, 4> kFoldBScoring{0, 2, 4, 6};

    static_assert(kTransportMembers == 8);
    static_assert(kMainModelErrorMembers == 1);
    static_assert(kModelErrorMembers == 8);
    static_assert(kCrossedMembers == 64);

    inline EventKey transportEventKey(std::uint64_t methodSeed,
                                      std::size_t transportMember,
                                      std::uint64_t transportSubstream)
    {
        if (transportMember >= kTransportMembers)
            throw std::out_of_range("V12 transport member index");
        // The legacy EventKey slot is deliberately pinned to zero. Candidate,
        // source-update, event and outcome identities cannot enter this root.
        return EventKey{methodSeed, 0ULL,
                        static_cast<std::uint64_t>(transportMember),
                        transportSubstream};
    }

    enum class DeploymentContract
    {
        MainV12M,
        FullV12F
    };

    inline constexpr std::size_t modelErrorMemberCount(DeploymentContract contract)
    {
        return contract == DeploymentContract::MainV12M
            ? kMainModelErrorMembers : kModelErrorMembers;
    }

    inline constexpr std::size_t crossedMemberCount(DeploymentContract contract)
    {
        return kTransportMembers * modelErrorMemberCount(contract);
    }

    inline void requireCalibrationForContract(DeploymentContract contract,
                                              bool calibrationPresent,
                                              bool calibrationHashMatches)
    {
        if (contract == DeploymentContract::FullV12F &&
            (!calibrationPresent || !calibrationHashMatches))
            throw std::runtime_error(
                "V12-F requires a present, hash-matched TADM calibration artifact");
    }

    struct CrossedLogitBank
    {
        std::size_t sourceCount = 0;
        std::size_t eventCount = 0;
        std::vector<double> values;

        CrossedLogitBank() = default;

        CrossedLogitBank(std::size_t sources, std::size_t events)
            : sourceCount(sources), eventCount(events),
              values(sources * kCrossedMembers * events, 0.0)
        {}

        double& at(std::size_t source, std::size_t transport,
                   std::size_t discrepancy, std::size_t event)
        {
            return values.at(index(source, transport, discrepancy, event));
        }

        double at(std::size_t source, std::size_t transport,
                  std::size_t discrepancy, std::size_t event) const
        {
            return values.at(index(source, transport, discrepancy, event));
        }

    private:
        std::size_t index(std::size_t source, std::size_t transport,
                          std::size_t discrepancy, std::size_t event) const
        {
            if (source >= sourceCount || transport >= kTransportMembers ||
                discrepancy >= kModelErrorMembers || event >= eventCount)
                throw std::out_of_range("RC-SD-TFEI crossed bank index");
            return (((source * kTransportMembers + transport) *
                     kModelErrorMembers + discrepancy) * eventCount + event);
        }
    };

    struct TransportLogitBank
    {
        std::size_t sourceCount = 0;
        std::size_t eventCount = 0;
        std::vector<double> values;

        TransportLogitBank() = default;

        TransportLogitBank(std::size_t sources, std::size_t events)
            : sourceCount(sources), eventCount(events),
              values(sources * kTransportMembers * events, 0.0)
        {}

        double& at(std::size_t source, std::size_t transport,
                   std::size_t discrepancy, std::size_t event)
        {
            return values.at(index(source, transport, discrepancy, event));
        }

        double at(std::size_t source, std::size_t transport,
                  std::size_t discrepancy, std::size_t event) const
        {
            return values.at(index(source, transport, discrepancy, event));
        }

    private:
        std::size_t index(std::size_t source, std::size_t transport,
                          std::size_t discrepancy, std::size_t event) const
        {
            if (source >= sourceCount || transport >= kTransportMembers ||
                discrepancy != 0 || event >= eventCount)
                throw std::out_of_range("V12-M transport bank index");
            return ((source * kTransportMembers + transport) * eventCount + event);
        }
    };

    struct StableOperator
    {
        Eigen::MatrixXd matrix;
        Eigen::MatrixXd patternProjector;
        Eigen::VectorXd eigenvalues;
        Eigen::VectorXd weights;
        double ridge = 0.0;
    };

    inline double sigmoid(double value)
    {
        if (value >= 0.0)
            return 1.0 / (1.0 + std::exp(-value));
        const double exponential = std::exp(value);
        return exponential / (1.0 + exponential);
    }

    inline double jeffreysHitProbability(double rawFrequency,
                                         std::size_t recordedTimesteps)
    {
        if (!std::isfinite(rawFrequency) || rawFrequency < 0.0 ||
            rawFrequency > 1.0 || recordedTimesteps == 0)
            throw std::invalid_argument("invalid simulated hit frequency");
        return (static_cast<double>(recordedTimesteps) * rawFrequency + 0.5) /
               (static_cast<double>(recordedTimesteps) + 1.0);
    }

    inline double logit(double probability)
    {
        if (!(probability > 0.0) || !(probability < 1.0))
            throw std::invalid_argument("logit probability must be in (0,1)");
        return std::log(probability) - std::log1p(-probability);
    }

    inline double simulatedFrequencyLogit(double rawFrequency,
                                          std::size_t recordedTimesteps)
    {
        return logit(jeffreysHitProbability(rawFrequency, recordedTimesteps));
    }

    inline double logAddExp(double left, double right)
    {
        if (!std::isfinite(left)) return right;
        if (!std::isfinite(right)) return left;
        const double maximum = std::max(left, right);
        return maximum + std::log(std::exp(left - maximum) +
                                  std::exp(right - maximum));
    }

    inline double logSumExp(const std::vector<double>& values)
    {
        if (values.empty())
            throw std::invalid_argument("logSumExp requires values");
        const double maximum = *std::max_element(values.begin(), values.end());
        double total = 0.0;
        for (double value : values)
            total += std::exp(value - maximum);
        return maximum + std::log(total);
    }

    inline double combineTrajectoryCrossFitEvidence(double cumulativeFoldA,
                                                     double cumulativeFoldB)
    {
        return logAddExp(cumulativeFoldA, cumulativeFoldB) - std::log(2.0);
    }

    inline double logBernoulli(unsigned char hit, double logit)
    {
        if (hit > 1)
            throw std::invalid_argument("hit must be zero or one");
        return hit != 0 ? -std::log1p(std::exp(-std::abs(logit))) +
                              std::min(logit, 0.0)
                        : -std::log1p(std::exp(-std::abs(logit))) -
                              std::max(logit, 0.0);
    }

    inline Eigen::MatrixXd rateGroupBasis(const std::vector<std::uint64_t>& rateGroupIds)
    {
        if (rateGroupIds.empty())
            throw std::invalid_argument("rate-group ids cannot be empty");
        std::vector<std::uint64_t> unique = rateGroupIds;
        std::sort(unique.begin(), unique.end());
        unique.erase(std::unique(unique.begin(), unique.end()), unique.end());
        Eigen::MatrixXd basis = Eigen::MatrixXd::Zero(
            static_cast<Eigen::Index>(rateGroupIds.size()),
            static_cast<Eigen::Index>(unique.size()));
        for (std::size_t column = 0; column < unique.size(); ++column)
        {
            std::size_t count = 0;
            for (std::uint64_t group : rateGroupIds)
                count += group == unique[column] ? 1U : 0U;
            const double scale = 1.0 / std::sqrt(static_cast<double>(count));
            for (std::size_t row = 0; row < rateGroupIds.size(); ++row)
                if (rateGroupIds[row] == unique[column])
                    basis(static_cast<Eigen::Index>(row),
                          static_cast<Eigen::Index>(column)) = scale;
        }
        return basis;
    }

    template <typename Bank, std::size_t FoldSize>
    StableOperator fitStableOperatorImpl(
        const Bank& bank,
        std::size_t discrepancyCount,
        const std::array<std::size_t, FoldSize>& calibrationTransport,
        const std::vector<std::uint64_t>& rateGroupIds)
    {
        if (bank.sourceCount < 2 || FoldSize < 2 || bank.eventCount == 0 ||
            discrepancyCount == 0)
            throw std::invalid_argument("insufficient RC-SD-TFEI bank");
        if (rateGroupIds.size() != bank.eventCount)
            throw std::invalid_argument("rate-group id dimension mismatch");
        const Eigen::Index dimension = static_cast<Eigen::Index>(bank.eventCount);
        for (std::size_t transport : calibrationTransport)
            if (transport >= kTransportMembers)
                throw std::invalid_argument("calibration transport out of range");

        const Eigen::MatrixXd q = rateGroupBasis(rateGroupIds);
        const Eigen::MatrixXd projector =
            Eigen::MatrixXd::Identity(dimension, dimension) - q * q.transpose();

        std::vector<Eigen::VectorXd> sourceMeans(bank.sourceCount,
                                                 Eigen::VectorXd::Zero(dimension));
        Eigen::MatrixXd temporalCovariance = Eigen::MatrixXd::Zero(dimension, dimension);
        std::size_t temporalTerms = 0;
        for (std::size_t source = 0; source < bank.sourceCount; ++source)
        {
            for (std::size_t discrepancy = 0;
                 discrepancy < discrepancyCount; ++discrepancy)
            {
                std::vector<Eigen::VectorXd> values;
                values.reserve(FoldSize);
                Eigen::VectorXd mean = Eigen::VectorXd::Zero(dimension);
                for (std::size_t transport : calibrationTransport)
                {
                    Eigen::VectorXd vector(dimension);
                    for (std::size_t event = 0; event < bank.eventCount; ++event)
                        vector(static_cast<Eigen::Index>(event)) =
                            bank.at(source, transport, discrepancy, event);
                    vector = projector * vector;
                    values.push_back(vector);
                    mean += vector / static_cast<double>(FoldSize);
                    sourceMeans[source] += vector /
                        static_cast<double>(FoldSize * discrepancyCount);
                }
                for (const Eigen::VectorXd& value : values)
                {
                    const Eigen::VectorXd residual = value - mean;
                    temporalCovariance.noalias() +=
                        residual * residual.transpose() /
                        static_cast<double>(FoldSize - 1);
                }
                ++temporalTerms;
            }
        }
        temporalCovariance /= static_cast<double>(temporalTerms);

        Eigen::VectorXd grandMean = Eigen::VectorXd::Zero(dimension);
        for (const Eigen::VectorXd& mean : sourceMeans)
            grandMean += mean / static_cast<double>(bank.sourceCount);
        Eigen::MatrixXd sourceCovariance = Eigen::MatrixXd::Zero(dimension, dimension);
        for (const Eigen::VectorXd& mean : sourceMeans)
        {
            const Eigen::VectorXd residual = mean - grandMean;
            sourceCovariance.noalias() += residual * residual.transpose() /
                static_cast<double>(bank.sourceCount - 1);
        }

        const Eigen::MatrixXd metric0 = temporalCovariance;
        const double ridge = std::sqrt(std::numeric_limits<double>::epsilon()) *
            std::max(metric0.trace() / static_cast<double>(dimension), 1.0);
        const Eigen::MatrixXd metric = 0.5 * (metric0 + metric0.transpose()) +
            ridge * Eigen::MatrixXd::Identity(dimension, dimension);
        Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> metricSolver(metric);
        if (metricSolver.info() != Eigen::Success)
            throw std::runtime_error("metric eigendecomposition failed");
        Eigen::VectorXd metricValues = metricSolver.eigenvalues();
        for (Eigen::Index i = 0; i < metricValues.size(); ++i)
            metricValues(i) = std::max(metricValues(i), ridge);
        const Eigen::MatrixXd metricVectors = metricSolver.eigenvectors();
        const Eigen::MatrixXd metricSqrt = metricVectors *
            metricValues.array().sqrt().matrix().asDiagonal() * metricVectors.transpose();
        const Eigen::MatrixXd metricInvSqrt = metricVectors *
            metricValues.array().rsqrt().matrix().asDiagonal() * metricVectors.transpose();

        const Eigen::MatrixXd whitened = metricInvSqrt *
            (0.5 * (sourceCovariance + sourceCovariance.transpose())) * metricInvSqrt;
        Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> sourceSolver(
            0.5 * (whitened + whitened.transpose()));
        if (sourceSolver.info() != Eigen::Success)
            throw std::runtime_error("source eigendecomposition failed");

        const Eigen::Index count = sourceSolver.eigenvalues().size();
        Eigen::VectorXd eigenvalues(count);
        Eigen::MatrixXd eigenvectors(dimension, count);
        for (Eigen::Index output = 0; output < count; ++output)
        {
            const Eigen::Index input = count - 1 - output;
            eigenvalues(output) = std::max(sourceSolver.eigenvalues()(input), 0.0);
            eigenvectors.col(output) = sourceSolver.eigenvectors().col(input);
        }
        const Eigen::VectorXd weights =
            eigenvalues.array() / (1.0 + eigenvalues.array());
        const Eigen::MatrixXd stable = metricSqrt * eigenvectors *
            weights.asDiagonal() * eigenvectors.transpose() * metricInvSqrt * projector;
        return StableOperator{stable, projector, eigenvalues, weights, ridge};
    }

    template <std::size_t FoldSize>
    StableOperator fitStableOperatorMain(
        const TransportLogitBank& bank,
        const std::array<std::size_t, FoldSize>& calibrationTransport,
        const std::vector<std::uint64_t>& rateGroupIds)
    {
        return fitStableOperatorImpl(bank, kMainModelErrorMembers,
                                     calibrationTransport, rateGroupIds);
    }

    template <std::size_t FoldSize>
    StableOperator fitStableOperator(
        const CrossedLogitBank& bank,
        const std::array<std::size_t, FoldSize>& calibrationTransport,
        const std::vector<std::uint64_t>& rateGroupIds)
    {
        return fitStableOperatorImpl(bank, kModelErrorMembers,
                                     calibrationTransport, rateGroupIds);
    }

    inline Eigen::VectorXd filterAndMatchRates(
        const Eigen::VectorXd& rawLogits,
        const StableOperator& stableOperator,
        const std::vector<std::uint64_t>& rateGroupIds)
    {
        if (rawLogits.size() != static_cast<Eigen::Index>(rateGroupIds.size()) ||
            stableOperator.matrix.rows() != rawLogits.size() ||
            stableOperator.matrix.cols() != rawLogits.size())
            throw std::invalid_argument("filter dimension mismatch");
        const Eigen::VectorXd pattern = stableOperator.matrix * rawLogits;
        Eigen::VectorXd output(rawLogits.size());
        std::vector<std::uint64_t> unique = rateGroupIds;
        std::sort(unique.begin(), unique.end());
        unique.erase(std::unique(unique.begin(), unique.end()), unique.end());
        for (std::uint64_t group : unique)
        {
            double target = 0.0;
            std::size_t count = 0;
            for (std::size_t event = 0; event < rateGroupIds.size(); ++event)
                if (rateGroupIds[event] == group)
                {
                    target += sigmoid(rawLogits(static_cast<Eigen::Index>(event)));
                    ++count;
                }
            target /= static_cast<double>(count);
            double minimumPattern = std::numeric_limits<double>::infinity();
            double maximumPattern = -std::numeric_limits<double>::infinity();
            for (std::size_t event = 0; event < rateGroupIds.size(); ++event)
                if (rateGroupIds[event] == group)
                {
                    const double value = pattern(static_cast<Eigen::Index>(event));
                    minimumPattern = std::min(minimumPattern, value);
                    maximumPattern = std::max(maximumPattern, value);
                }
            const double targetLogit = logit(target);
            // Every probability at low is <= target and every probability at
            // high is >= target, so this is a proof-carrying bracket rather
            // than a magic numeric range.
            double low = targetLogit - maximumPattern;
            double high = targetLogit - minimumPattern;
            for (int iteration = 0; iteration < 100; ++iteration)
            {
                const double middle = 0.5 * (low + high);
                double mean = 0.0;
                for (std::size_t event = 0; event < rateGroupIds.size(); ++event)
                    if (rateGroupIds[event] == group)
                        mean += sigmoid(middle + pattern(static_cast<Eigen::Index>(event)));
                mean /= static_cast<double>(count);
                if (mean < target) low = middle;
                else high = middle;
            }
            const double intercept = 0.5 * (low + high);
            for (std::size_t event = 0; event < rateGroupIds.size(); ++event)
                if (rateGroupIds[event] == group)
                    output(static_cast<Eigen::Index>(event)) =
                        intercept + pattern(static_cast<Eigen::Index>(event));
        }
        return output;
    }

    inline Eigen::MatrixXd transitionMatrix(bool sameStopAndMeasureBlock,
                                             std::size_t stateCount)
    {
        if (stateCount == 0)
            throw std::invalid_argument("transport state count cannot be zero");
        if (sameStopAndMeasureBlock)
            return Eigen::MatrixXd::Identity(
                static_cast<Eigen::Index>(stateCount),
                static_cast<Eigen::Index>(stateCount));
        return Eigen::MatrixXd::Constant(
            static_cast<Eigen::Index>(stateCount),
            static_cast<Eigen::Index>(stateCount),
            1.0 / static_cast<double>(stateCount));
    }

    struct HmmResult
    {
        double logEvidence = 0.0;
        Eigen::VectorXd normalizedLogState;
        std::uint64_t lastBlockId = 0;
        bool hasLastBlock = false;
    };

    inline HmmResult hmmLogEvidence(
        const std::vector<unsigned char>& hits,
        const Eigen::MatrixXd& logitsByState,
        const std::vector<std::uint64_t>& blockIds,
        const Eigen::VectorXd* initialLogState = nullptr,
        const std::uint64_t* previousBlockId = nullptr)
    {
        const std::size_t eventCount = hits.size();
        const std::size_t stateCount = static_cast<std::size_t>(logitsByState.rows());
        if (blockIds.size() != eventCount ||
            logitsByState.cols() != static_cast<Eigen::Index>(eventCount) ||
            stateCount == 0)
            throw std::invalid_argument("HMM dimension mismatch");
        Eigen::VectorXd logState(static_cast<Eigen::Index>(stateCount));
        if (initialLogState != nullptr)
        {
            if (initialLogState->size() != logState.size())
                throw std::invalid_argument("initial state dimension mismatch");
            logState = *initialLogState;
        }
        else
            logState.setConstant(-std::log(static_cast<double>(stateCount)));

        double accumulated = 0.0;
        for (std::size_t event = 0; event < eventCount; ++event)
        {
            const bool sameBlock = event > 0
                ? blockIds[event] == blockIds[event - 1]
                : previousBlockId != nullptr && blockIds[event] == *previousBlockId;
            Eigen::VectorXd predicted(static_cast<Eigen::Index>(stateCount));
            if (sameBlock)
                predicted = logState;
            else
                predicted.setConstant(-std::log(static_cast<double>(stateCount)));
            /* The general transition sum reduces exactly to the two branches
               above: identity within a block and a uniform row-stochastic
               reset between blocks. */
            if (!predicted.allFinite())
            {
                throw std::runtime_error("non-finite transport prediction");
            }
            for (std::size_t state = 0; state < stateCount; ++state)
                predicted(static_cast<Eigen::Index>(state)) +=
                    logBernoulli(hits[event], logitsByState(
                        static_cast<Eigen::Index>(state),
                        static_cast<Eigen::Index>(event)));
            std::vector<double> values(static_cast<std::size_t>(predicted.size()));
            for (Eigen::Index i = 0; i < predicted.size(); ++i)
                values[static_cast<std::size_t>(i)] = predicted(i);
            const double normalizer = logSumExp(values);
            logState = predicted.array() - normalizer;
            accumulated += normalizer;
        }
        return HmmResult{accumulated, logState,
                         eventCount > 0 ? blockIds.back() : 0,
                         eventCount > 0};
    }

    inline double tadmLogEvidence(
        const std::vector<unsigned char>& hits,
        const std::array<Eigen::MatrixXd, kModelErrorMembers>& logitsByDiscrepancy,
        const std::vector<std::uint64_t>& blockIds,
        const std::array<double, kModelErrorMembers>& discrepancyWeights)
    {
        double weightTotal = std::accumulate(discrepancyWeights.begin(),
                                             discrepancyWeights.end(), 0.0);
        if (!(weightTotal > 0.0))
            throw std::invalid_argument("invalid discrepancy weights");
        std::vector<double> components;
        components.reserve(kModelErrorMembers);
        for (std::size_t discrepancy = 0;
             discrepancy < kModelErrorMembers; ++discrepancy)
        {
            if (!(discrepancyWeights[discrepancy] > 0.0))
                throw std::invalid_argument("discrepancy weights must be positive");
            components.push_back(
                std::log(discrepancyWeights[discrepancy] / weightTotal) +
                hmmLogEvidence(hits, logitsByDiscrepancy[discrepancy],
                               blockIds).logEvidence);
        }
        return logSumExp(components);
    }
}
