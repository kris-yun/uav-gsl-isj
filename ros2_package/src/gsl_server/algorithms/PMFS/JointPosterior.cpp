#include <gsl_server/algorithms/PMFS/PMFS.hpp>
#include <gsl_server/algorithms/PMFS/internal/JointPosteriorContract.hpp>
#include <chrono>
#include <thread>
#include <iomanip>

namespace GSL
{
    void PMFS::requestJointPosterior(uint64_t update)
    {
        if (jointLatestStampNs == 0)
            throw std::runtime_error("JOINT_NO_STAMPED_GAS");
        jointRequestedStampNs = jointLatestStampNs;
        const std::filesystem::path root(jointSourceExchangeDir);
        const auto target = root / ("request_" + std::to_string(update) + ".txt");
        if (std::filesystem::exists(target))
            throw std::runtime_error("JOINT_STALE_REQUEST_DIRECTORY");
        auto temporary = target;
        temporary += ".tmp";
        std::ofstream output(temporary);
        output << std::setprecision(17) << "CSTAR_JOINT_V1 " << jointRunId << ' ' << update << ' '
               << jointRequestedStampNs << ' ' << gridMetadata.dimensions.x << ' ' << gridMetadata.dimensions.y << ' '
               << gridMetadata.cellSize << ' ' << gridMetadata.origin.x << ' ' << gridMetadata.origin.y << '\n';
        for (const auto cell : occupancy)
            output << (cell == Occupancy::Free ? 1 : 0) << '\n';
        output.close();
        if (!output) throw std::runtime_error("JOINT_REQUEST_WRITE");
        std::filesystem::rename(temporary, target);
    }

    void PMFS::applyJointPosterior(uint64_t update)
    {
        const auto path = std::filesystem::path(jointSourceExchangeDir) / ("posterior_" + std::to_string(update) + ".txt");
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(30);
        while (!std::filesystem::exists(path))
        {
            if (std::chrono::steady_clock::now() >= deadline)
                throw std::runtime_error("JOINT_POSTERIOR_DEADLINE_NO_NATIVE_FALLBACK");
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
        PMFS_internal::JointGridContract contract{jointRunId, update, jointRequestedStampNs,
            static_cast<size_t>(gridMetadata.dimensions.x), static_cast<size_t>(gridMetadata.dimensions.y),
            gridMetadata.cellSize, gridMetadata.origin.x, gridMetadata.origin.y, {}};
        for (const auto cell : occupancy)
            contract.free.push_back(cell == Occupancy::Free ? 1 : 0);
        std::ifstream input(path);
        auto posterior = PMFS_internal::readJointPosterior(input, contract);
        sourceProbability.swap(posterior);
        std::ofstream audit(std::filesystem::path(jointSourceExchangeDir) / "consumption.csv", std::ios::app);
        audit << update << ',' << jointRequestedStampNs << ',' << sourceProbability.size() << '\n';
        audit.close();
        if (!audit) throw std::runtime_error("JOINT_CONSUMPTION_AUDIT_WRITE");
        GSL_INFO("JOINT_POSTERIOR_CONSUMED update={} stamp_ns={}", update, jointRequestedStampNs);
    }
}
