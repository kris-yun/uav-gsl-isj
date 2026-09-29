#include <gsl_server/algorithms/PMFS/internal/RCSDTFEIV12.hpp>
#include <gsl_server/algorithms/PMFS/internal/V12ResponseBank.hpp>

#include <Eigen/Dense>

#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <random>
#include <vector>

namespace v12 = GSL::PMFS_internal::rc_sd_tfei_v12;

namespace
{
    std::pair<v12::StableOperator, std::vector<std::uint64_t>> makeOperator();

    void requireClose(double left, double right, double tolerance,
                      const char* label)
    {
        if (std::abs(left - right) > tolerance)
            throw std::runtime_error(std::string(label) + " mismatch");
    }

    void testContractCounts()
    {
        static_assert(v12::kTransportMembers == 8);
        static_assert(v12::kMainModelErrorMembers == 1);
        static_assert(v12::kModelErrorMembers == 8);
        static_assert(v12::kCrossedMembers == 64);
        static_assert(v12::crossedMemberCount(
            v12::DeploymentContract::MainV12M) == 8);
        static_assert(v12::crossedMemberCount(
            v12::DeploymentContract::FullV12F) == 64);
        v12::requireCalibrationForContract(
            v12::DeploymentContract::MainV12M, false, false);
        bool rejected = false;
        try
        {
            v12::requireCalibrationForContract(
                v12::DeploymentContract::FullV12F, false, false);
        }
        catch (const std::runtime_error&)
        {
            rejected = true;
        }
        assert(rejected);
        v12::requireCalibrationForContract(
            v12::DeploymentContract::FullV12F, true, true);
        for (std::size_t left : v12::kFoldACalibration)
            for (std::size_t right : v12::kFoldAScoring)
                assert(left != right);
        for (std::size_t left : v12::kFoldBCalibration)
            for (std::size_t right : v12::kFoldBScoring)
                assert(left != right);
    }

    void testTransportRootInvariance()
    {
        const auto key = v12::transportEventKey(20260825, 3, 17);
        assert(key.globalSeed == 20260825);
        assert(key.sourceUpdateId == 0);
        assert(key.replicaId == 3);
        assert(key.transportSubstream == 17);
        GSL::PMFS_internal::EventKeyedTransportRng first(key);
        GSL::PMFS_internal::EventKeyedTransportRng repeated(
            v12::transportEventKey(20260825, 3, 17));
        for (std::uint64_t draw = 0; draw < 100; ++draw)
            requireClose(first.unitAt(draw, 0), repeated.unitAt(draw, 0),
                         0.0, "transport root repeatability");
    }

    void testOperatorAlgebra()
    {
        const auto [stable, blocks] = makeOperator();
        const Eigen::MatrixXd& projector = stable.patternProjector;
        assert((projector * projector - projector).cwiseAbs().maxCoeff() < 1e-12);
        const Eigen::MatrixXd basis = v12::rateGroupBasis(blocks);
        assert((basis.transpose() * projector).cwiseAbs().maxCoeff() < 1e-12);
        assert(stable.eigenvalues.allFinite());
        assert(stable.weights.allFinite());
        assert(stable.eigenvalues.minCoeff() >= 0.0);
        assert(stable.weights.minCoeff() >= 0.0);
        assert(stable.weights.maxCoeff() < 1.0);
        const Eigen::VectorXd expected = stable.eigenvalues.array() /
            (1.0 + stable.eigenvalues.array());
        assert((stable.weights - expected).cwiseAbs().maxCoeff() < 1e-14);
    }

    void testJeffreysCorrection()
    {
        constexpr std::size_t timesteps = 200;
        const double zero = v12::jeffreysHitProbability(0.0, timesteps);
        const double one = v12::jeffreysHitProbability(1.0, timesteps);
        assert(zero > 0.0 && one < 1.0);
        requireClose(zero + one, 1.0, 1e-15, "Jeffreys symmetry");
        requireClose(v12::simulatedFrequencyLogit(0.0, timesteps),
                    -v12::simulatedFrequencyLogit(1.0, timesteps),
                    1e-12, "Jeffreys logit symmetry");
        assert(std::abs(v12::jeffreysHitProbability(0.3, 2000) - 0.3) <
               std::abs(v12::jeffreysHitProbability(0.3, 20) - 0.3));
    }

    std::pair<v12::StableOperator, std::vector<std::uint64_t>> makeOperator()
    {
        constexpr std::size_t sources = 12;
        constexpr std::size_t events = 16;
        v12::TransportLogitBank bank(sources, events);
        std::mt19937_64 generator(20260825);
        std::normal_distribution<double> normal(0.0, 1.0);
        for (std::size_t source = 0; source < sources; ++source)
            for (std::size_t transport = 0; transport < v12::kTransportMembers; ++transport)
                for (std::size_t event = 0; event < events; ++event)
                    bank.at(source, transport, 0, event) =
                        0.7 * normal(generator) +
                        0.08 * static_cast<double>(source) *
                            std::sin(0.4 * static_cast<double>(event + 1));
        std::vector<std::uint64_t> blocks(events, 0);
        return {v12::fitStableOperatorMain(bank, v12::kFoldACalibration,
                                           blocks), blocks};
    }

    void testRatePreservation()
    {
        const auto [stable, blocks] = makeOperator();
        Eigen::VectorXd raw(static_cast<Eigen::Index>(blocks.size()));
        for (Eigen::Index i = 0; i < raw.size(); ++i)
            raw(i) = -3.0 + 6.0 * static_cast<double>(i) /
                static_cast<double>(raw.size() - 1) + 0.4 * std::sin(static_cast<double>(i));
        const Eigen::VectorXd filtered = v12::filterAndMatchRates(raw, stable, blocks);
        for (std::uint64_t group = 0; group < 1; ++group)
        {
            double rawMean = 0.0;
            double filteredMean = 0.0;
            std::size_t count = 0;
            for (std::size_t event = 0; event < blocks.size(); ++event)
                if (blocks[event] == group)
                {
                    rawMean += v12::sigmoid(raw(static_cast<Eigen::Index>(event)));
                    filteredMean += v12::sigmoid(filtered(static_cast<Eigen::Index>(event)));
                    ++count;
                }
            requireClose(rawMean / count, filteredMean / count, 1e-12,
                         "block rate");
        }
    }

    void testBlockConstantContrastSurvives()
    {
        constexpr Eigen::Index events = 16;
        Eigen::VectorXd candidate(events);
        const std::array<double, 4> blockValues{-2.0, -0.5, 0.8, 2.0};
        for (Eigen::Index event = 0; event < events; ++event)
            candidate(event) = blockValues[static_cast<std::size_t>(event / 4)];
        const std::vector<std::uint64_t> incrementGroups(
            static_cast<std::size_t>(events), 0);
        std::vector<std::uint64_t> forbiddenPerBlock(
            static_cast<std::size_t>(events));
        for (std::size_t event = 0; event < forbiddenPerBlock.size(); ++event)
            forbiddenPerBlock[event] = event / 4;
        const Eigen::MatrixXd correctQ = v12::rateGroupBasis(incrementGroups);
        const Eigen::MatrixXd wrongQ = v12::rateGroupBasis(forbiddenPerBlock);
        const Eigen::VectorXd correctPattern =
            (Eigen::MatrixXd::Identity(events, events) - correctQ * correctQ.transpose()) * candidate;
        const Eigen::VectorXd wrongPattern =
            (Eigen::MatrixXd::Identity(events, events) - wrongQ * wrongQ.transpose()) * candidate;
        assert(correctPattern.norm() > 1.0);
        assert(wrongPattern.norm() < 1e-12);
    }

    void testExtremeRateBracket()
    {
        const double rawProbability = 0.1;
        const double rawLogit = std::log(rawProbability / (1.0 - rawProbability));
        Eigen::VectorXd raw = Eigen::VectorXd::Constant(4, rawLogit);
        v12::StableOperator stable;
        stable.matrix = Eigen::MatrixXd::Zero(4, 4);
        stable.matrix(0, 0) = 1000.0;
        stable.matrix(1, 1) = 250.0;
        stable.matrix(2, 2) = -300.0;
        stable.matrix(3, 3) = -1200.0;
        const std::vector<std::uint64_t> blocks(4, 0);
        const Eigen::VectorXd filtered = v12::filterAndMatchRates(raw, stable, blocks);
        double mean = 0.0;
        for (Eigen::Index index = 0; index < filtered.size(); ++index)
            mean += v12::sigmoid(filtered(index)) / 4.0;
        requireClose(mean, rawProbability, 1e-12, "extreme rate bracket");
    }

    void testSaturatedRate()
    {
        const double low = std::log(0.2 / 0.8);
        const double high = std::log(0.9 / 0.1);
        double lowScore = 0.0;
        double highScore = 0.0;
        for (int i = 0; i < 128; ++i)
        {
            const unsigned char hit = i < 119 ? 1 : 0;
            lowScore += v12::logBernoulli(hit, low);
            highScore += v12::logBernoulli(hit, high);
        }
        assert(highScore > lowScore);
    }

    void testFlatEvidence()
    {
        const std::vector<unsigned char> hits{1, 0, 1, 1, 0, 0};
        double score = 0.0;
        for (unsigned char hit : hits)
            score += v12::logBernoulli(hit, 0.0);
        for (int candidate = 0; candidate < 5; ++candidate)
            requireClose(std::exp(score) / (5.0 * std::exp(score)), 0.2,
                         1e-14, "flat evidence");
    }

    void testLateReversal()
    {
        const std::vector<unsigned char> hits{1, 1, 0, 0, 0, 0, 0, 0, 0, 0};
        const double candidate0 = std::log(0.85 / 0.15);
        const double candidate1 = std::log(0.35 / 0.65);
        double prefix0 = 0.0;
        double prefix1 = 0.0;
        double full0 = 0.0;
        double full1 = 0.0;
        for (std::size_t event = 0; event < hits.size(); ++event)
        {
            full0 += v12::logBernoulli(hits[event], candidate0);
            full1 += v12::logBernoulli(hits[event], candidate1);
            if (event < 2)
            {
                prefix0 = full0;
                prefix1 = full1;
            }
        }
        assert(prefix0 > prefix1);
        assert(full1 > full0);
    }

    void testTrajectoryLevelCrossFitMixture()
    {
        // The fold identity is selected once for the whole trajectory.
        // Product-of-per-update mixtures would silently create four paths
        // after two updates instead of the declared two-model mixture.
        const double a1 = std::log(0.8);
        const double a2 = std::log(0.7);
        const double b1 = std::log(0.3);
        const double b2 = std::log(0.4);
        const double correct = v12::combineTrajectoryCrossFitEvidence(
            a1 + a2, b1 + b2);
        const double expected = std::log(0.5 * 0.8 * 0.7 +
                                         0.5 * 0.3 * 0.4);
        requireClose(correct, expected, 1e-14,
                     "trajectory cross-fit mixture");
        const double forbiddenPerUpdate =
            v12::combineTrajectoryCrossFitEvidence(a1, b1) +
            v12::combineTrajectoryCrossFitEvidence(a2, b2);
        assert(std::abs(correct - forbiddenPerUpdate) > 1e-3);
    }

    void testResponseBankRoundTripAndMismatch()
    {
        v12::ResponseBankMetadata metadata;
        metadata.dimensionsX = 3;
        metadata.dimensionsY = 2;
        metadata.cellCount = 6;
        metadata.carrierCount = 2;
        metadata.transportMembers = v12::kTransportMembers;
        metadata.recordedTimesteps = 200;
        metadata.methodSeed = 20260825;
        metadata.transportSubstream = 17;
        metadata.cellSize = 0.1;
        metadata.originX = -1.0;
        metadata.originY = 2.0;
        metadata.deltaTime = 0.1;
        metadata.noiseStandardDeviation = 0.05;
        metadata.blurSigmaX = 1.0;
        metadata.blurSigmaY = 1.5;
        metadata.occupancy = {0, 1, 0, 0, 1, 0};
        metadata.carrierIds = {"c0", "c1"};
        metadata.carrierX = {0.0, 1.0};
        metadata.carrierY = {0.5, 1.5};
        metadata.carrierFreeCells = {3, 2};
        std::vector<std::vector<float>> maps(
            static_cast<std::size_t>(metadata.carrierCount * metadata.transportMembers),
            std::vector<float>(static_cast<std::size_t>(metadata.cellCount)));
        for (std::size_t map = 0; map < maps.size(); ++map)
            for (std::size_t cell = 0; cell < maps[map].size(); ++cell)
                maps[map][cell] = static_cast<float>(0.01 * map + 0.001 * cell);
        const auto nonce = std::chrono::high_resolution_clock::now()
            .time_since_epoch().count();
        const std::filesystem::path path = std::filesystem::temp_directory_path() /
            ("v12_response_bank_contract_" + std::to_string(nonce) + ".bin");
        v12::writeResponseBankAtomic(path, metadata, maps);
        const auto loaded = v12::readResponseBankValidated(path, metadata);
        assert(loaded == maps);
        v12::ResponseBankMetadata mismatched = metadata;
        ++mismatched.methodSeed;
        bool rejected = false;
        try
        {
            (void)v12::readResponseBankValidated(path, mismatched);
        }
        catch (const std::runtime_error&)
        {
            rejected = true;
        }
        assert(rejected);
        assert(std::filesystem::remove(path));
    }

    void testHMMProjectivity()
    {
        constexpr std::size_t states = 4;
        constexpr std::size_t events = 20;
        std::mt19937_64 generator(17);
        std::normal_distribution<double> normal(0.0, 1.0);
        Eigen::MatrixXd logits(states, events);
        std::vector<unsigned char> hits(events);
        std::vector<std::uint64_t> blocks(events);
        for (std::size_t event = 0; event < events; ++event)
        {
            hits[event] = static_cast<unsigned char>(generator() % 2);
            blocks[event] = event / 5;
            for (std::size_t state = 0; state < states; ++state)
                logits(static_cast<Eigen::Index>(state),
                       static_cast<Eigen::Index>(event)) = normal(generator);
        }
        const v12::HmmResult batch = v12::hmmLogEvidence(hits, logits, blocks);
        const std::size_t split = 7;
        const std::vector<unsigned char> firstHits(hits.begin(), hits.begin() + split);
        const std::vector<unsigned char> secondHits(hits.begin() + split, hits.end());
        const std::vector<std::uint64_t> firstBlocks(blocks.begin(), blocks.begin() + split);
        const std::vector<std::uint64_t> secondBlocks(blocks.begin() + split, blocks.end());
        const v12::HmmResult first = v12::hmmLogEvidence(
            firstHits, logits.leftCols(static_cast<Eigen::Index>(split)), firstBlocks);
        const v12::HmmResult second = v12::hmmLogEvidence(
            secondHits, logits.rightCols(static_cast<Eigen::Index>(events - split)),
            secondBlocks, &first.normalizedLogState, &first.lastBlockId);
        requireClose(batch.logEvidence, first.logEvidence + second.logEvidence,
                     1e-12, "HMM evidence");
        if ((batch.normalizedLogState - second.normalizedLogState).cwiseAbs().maxCoeff() > 1e-12)
            throw std::runtime_error("HMM state mismatch");
        assert(batch.hasLastBlock && second.hasLastBlock);
        assert(batch.lastBlockId == second.lastBlockId);

        const Eigen::MatrixXd within = v12::transitionMatrix(true, states);
        const Eigen::MatrixXd between = v12::transitionMatrix(false, states);
        assert((within - Eigen::MatrixXd::Identity(states, states)).cwiseAbs().maxCoeff() < 1e-15);
        assert((between - Eigen::MatrixXd::Constant(states, states, 1.0 / states)).cwiseAbs().maxCoeff() < 1e-15);
    }

    void testTadmMarginalization()
    {
        const std::vector<unsigned char> hits{1, 0, 1, 0};
        const std::vector<std::uint64_t> blocks{0, 0, 1, 1};
        std::array<Eigen::MatrixXd, v12::kModelErrorMembers> logits;
        std::array<double, v12::kModelErrorMembers> weights;
        std::vector<double> components;
        for (std::size_t discrepancy = 0;
             discrepancy < v12::kModelErrorMembers; ++discrepancy)
        {
            logits[discrepancy] = Eigen::MatrixXd::Constant(
                4, static_cast<Eigen::Index>(hits.size()),
                -1.0 + 2.0 * static_cast<double>(discrepancy) / 7.0);
            weights[discrepancy] = 1.0 / 8.0;
            components.push_back(v12::hmmLogEvidence(
                hits, logits[discrepancy], blocks).logEvidence);
        }
        const double score = v12::tadmLogEvidence(hits, logits, blocks, weights);
        const double expected = v12::logSumExp(components) - std::log(8.0);
        requireClose(score, expected, 1e-12, "TADM marginalization");
    }
}

int main()
{
    const std::array<std::pair<const char*, void(*)()>, 14> tests{{
        {"contract_counts", testContractCounts},
        {"transport_root_invariance", testTransportRootInvariance},
        {"jeffreys_correction", testJeffreysCorrection},
        {"operator_algebra", testOperatorAlgebra},
        {"rate_preservation", testRatePreservation},
        {"block_constant_contrast_survives", testBlockConstantContrastSurvives},
        {"extreme_rate_bracket", testExtremeRateBracket},
        {"saturated_rate", testSaturatedRate},
        {"flat_evidence", testFlatEvidence},
        {"late_reversal", testLateReversal},
        {"trajectory_level_crossfit_mixture", testTrajectoryLevelCrossFitMixture},
        {"response_bank_roundtrip_and_mismatch", testResponseBankRoundTripAndMismatch},
        {"hmm_projectivity", testHMMProjectivity},
        {"tadm_marginalization", testTadmMarginalization}
    }};
    for (const auto& [name, function] : tests)
    {
        function();
        std::cout << "PASS " << name << '\n';
    }
    std::cout << "PASS_COUNT=" << tests.size() << '\n';
    return 0;
}
