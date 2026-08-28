#pragma once
#include "gaden/core/Logging.hpp"
#include "gaden/core/Vectors.hpp"
#include <cstdint>
#include <cstdlib>
#include <random>

namespace gaden
{
    constexpr float Deg2Rad = M_PI / 180.f;
    constexpr float Rad2Deg = 180.f / M_PI;

    inline size_t indexFrom3D(const Vector3i& index, const Vector3i& numCellsEnv)
    {
        return index.x + index.y * numCellsEnv.x + index.z * numCellsEnv.x * numCellsEnv.y;
    }

    inline Vector3i indicesFrom1D(size_t index, const Vector3i& numCellsEnv)
    {
        size_t z = index / (numCellsEnv.x * numCellsEnv.y);
        size_t remainder = index % (numCellsEnv.x * numCellsEnv.y);
        return Vector3i(remainder % numCellsEnv.x, remainder / numCellsEnv.x, z);
    }

    inline bool InRange(int val, int min, int max)
    {
        return val >= min && val < max;
    }

    // The default construction remains std::mt19937's fixed default seed, so
    // disabling the hook is source-compatible with the native implementation.
    // The explicit initializer is the only V3 change: it controls all random
    // engines used by the inline transport helpers without changing any draw,
    // distribution, or physical equation.
    namespace detail
    {
        inline thread_local bool seeded = false;
        inline thread_local bool env_checked = false;
        inline thread_local std::mt19937 seeded_gaussian_engine;
        inline thread_local std::mt19937 seeded_uniform_engine;
        inline thread_local std::normal_distribution<> seeded_gaussian_distribution{0, 1};
        inline thread_local std::uniform_real_distribution<float> seeded_uniform_distribution{0.0, 1.0};
    }

    inline void InitializeRandomEngines(std::uint64_t seed)
    {
        detail::seeded_gaussian_engine.seed(static_cast<std::uint32_t>(seed));
        detail::seeded_uniform_engine.seed(static_cast<std::uint32_t>(seed ^ 0x9e3779b97f4a7c15ULL));
        detail::seeded_gaussian_distribution.reset();
        detail::seeded_uniform_distribution.reset();
        detail::seeded = true;
        detail::env_checked = true;
    }

    inline void InitializeRandomEnginesFromEnvironment()
    {
        if (detail::env_checked) return;
        detail::env_checked = true;
        const char* text = std::getenv("GADEN_RNG_SEED");
        if (!text || !*text) return;
        char* end = nullptr;
        const auto value = std::strtoull(text, &end, 10);
        if (end && *end == '\0') InitializeRandomEngines(static_cast<std::uint64_t>(value));
    }

    // thread-safe
    inline float GaussianRandom(float mean, float stdDev)
    {
        InitializeRandomEnginesFromEnvironment();
        if (detail::seeded)
            return mean + detail::seeded_gaussian_distribution(detail::seeded_gaussian_engine) * stdDev;
        static thread_local std::mt19937 engine;
        static thread_local std::normal_distribution<> dist{0, 1};
        return mean + dist(engine) * stdDev;
    }

    inline float uniformRandom(float min, float max)
    {
        InitializeRandomEnginesFromEnvironment();
        if (detail::seeded)
            return min + detail::seeded_uniform_distribution(detail::seeded_uniform_engine) * (max - min);
        static thread_local std::mt19937 engine;
        static thread_local std::uniform_real_distribution<float> distribution{0.0, 1.0};
        return min + distribution(engine) * (max - min);
    }

    inline bool Approx(float x, float y, float epsilon = 1e-5)
    {
        return std::abs(x - y) < epsilon;
    }

    // holds a long list of N(0,1) values, and returns them one at a time, scaled as requested.
    // obviously not as good as generating them on the fly, but it's not like we are doing cryptography here
    template <int Size>
    class PrecalculatedGaussian
    {
    public:
        PrecalculatedGaussian()
        {
            m_index = uniformRandom(0, Size);
            for (size_t i = 0; i < Size; i++)
                m_precalculatedTable[i] = GaussianRandom(0, 1);
        }

        float nextValue(float mean, float stdev)
        {
            m_index = (m_index + 1) % Size;
            return mean + stdev * m_precalculatedTable[m_index];
        }

    private:
        uint16_t m_index;
        std::array<float, Size> m_precalculatedTable;
    };

} // namespace gaden
