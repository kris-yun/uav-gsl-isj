#pragma once
#include <cmath>
#include <cstdint>
#include <istream>
#include <stdexcept>
#include <string>
#include <vector>

namespace GSL::PMFS_internal
{
    // Transport-only contract. No inference, source truth, or controller tuning.
    struct JointGridContract
    {
        std::string run;
        uint64_t update, stamp;
        size_t width, height;
        double resolution, ox, oy;
        std::vector<uint8_t> free;
    };

    inline std::vector<double> readJointPosterior(std::istream& input, const JointGridContract& expected)
    {
        std::string magic, run;
        uint64_t update = 0, stamp = 0;
        size_t width = 0, height = 0;
        double resolution = 0, ox = 0, oy = 0;
        if (!(input >> magic >> run >> update >> stamp >> width >> height >> resolution >> ox >> oy) ||
            magic != "CSTAR_JOINT_V1" || run != expected.run || update != expected.update || stamp != expected.stamp ||
            width != expected.width || height != expected.height ||
            !std::isfinite(resolution) || !std::isfinite(ox) || !std::isfinite(oy) ||
            std::abs(resolution - expected.resolution) > 1e-12 ||
            std::abs(ox - expected.ox) > 1e-12 || std::abs(oy - expected.oy) > 1e-12)
            throw std::runtime_error("JOINT_POSTERIOR_IDENTITY_OR_GEOMETRY");
        if (width == 0 || height == 0 || expected.free.size() / width != height ||
            expected.free.size() % width != 0)
            throw std::runtime_error("JOINT_POSTERIOR_GRID_SIZE");
        std::vector<double> posterior(expected.free.size());
        long double mass = 0;
        for (size_t i = 0; i < posterior.size(); ++i)
        {
            int free = -1;
            double p = 0;
            if (!(input >> free >> p) || free != expected.free[i] || !std::isfinite(p) || p < 0 ||
                (free == 0 && p != 0))
                throw std::runtime_error("JOINT_POSTERIOR_SUPPORT_OR_VALUE");
            posterior[i] = p;
            mass += p;
        }
        std::string extra;
        if (input >> extra || std::abs(mass - 1.0L) > 1e-10L)
            throw std::runtime_error("JOINT_POSTERIOR_TRAILING_OR_MASS");
        return posterior; // caller swaps only after the whole message validates
    }
}
