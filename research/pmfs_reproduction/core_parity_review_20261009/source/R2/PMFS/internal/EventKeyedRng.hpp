#pragma once

#include <cstdint>
#include <cmath>

namespace GSL::PMFS_internal
{
    // The candidate id is deliberately absent from this key.  The same key
    // therefore defines the transport random stream for every candidate.
    struct EventKey
    {
        uint64_t globalSeed = 0;
        uint64_t sourceUpdateId = 0;
        uint64_t replicaId = 0;
        uint64_t transportSubstream = 0;
    };

    inline uint64_t splitmix64(uint64_t x)
    {
        x += 0x9e3779b97f4a7c15ULL;
        x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
        x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
        return x ^ (x >> 31);
    }

    inline uint64_t keyedBits(const EventKey& key, uint64_t drawIndex, uint64_t lane)
    {
        uint64_t state = splitmix64(key.globalSeed ^ 0x4b45595f53454544ULL);
        state = splitmix64(state ^ key.sourceUpdateId);
        state = splitmix64(state ^ key.replicaId);
        state = splitmix64(state ^ key.transportSubstream);
        state = splitmix64(state ^ drawIndex);
        return splitmix64(state ^ lane);
    }

    inline double keyedUnit(const EventKey& key, uint64_t drawIndex, uint64_t lane)
    {
        // 53 high bits give an exactly reproducible open interval (0, 1).
        constexpr double denominator = 9007199254740992.0; // 2^53
        const uint64_t bits = keyedBits(key, drawIndex, lane);
        return (static_cast<double>(bits >> 11) + 0.5) / denominator;
    }

    class EventKeyedTransportRng
    {
    public:
        explicit EventKeyedTransportRng(EventKey key) : key_(key) {}

        double normalAt(uint64_t drawIndex, double mean, double stdev) const
        {
            constexpr double twoPi = 6.283185307179586476925286766559;
            const double u1 = keyedUnit(key_, drawIndex, 0);
            const double u2 = keyedUnit(key_, drawIndex, 1);
            return mean + stdev * std::sqrt(-2.0 * std::log(u1)) * std::cos(twoPi * u2);
        }

        double unitAt(uint64_t drawIndex, uint64_t lane) const
        {
            return keyedUnit(key_, drawIndex, lane);
        }

        double uniformAt(uint64_t drawIndex, uint64_t lane, double minValue, double maxValue) const
        {
            return minValue + unitAt(drawIndex, lane) * (maxValue - minValue);
        }

        const EventKey& key() const { return key_; }

    private:
        EventKey key_;
    };
} // namespace GSL::PMFS_internal
