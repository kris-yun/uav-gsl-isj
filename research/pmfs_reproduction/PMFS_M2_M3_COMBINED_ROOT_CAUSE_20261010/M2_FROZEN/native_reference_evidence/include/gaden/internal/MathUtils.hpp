#pragma once
#include "gaden/core/Logging.hpp"
#include "gaden/core/Vectors.hpp"
#include <random>
#include <fstream>
#include <cstdlib>
#include <iomanip>

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


    // M2 isolated initialization and audit only: native distributions and calls retained.
    struct M2RandomStream {
        std::mt19937 engine;
        std::normal_distribution<> normal{0,1};
        std::uniform_real_distribution<float> uniform{0.f,1.f};
        uint64_t draws=0;
        int stream;
        M2RandomStream(int s):stream(s) {
            const char* value=std::getenv(s==0?"M2_GAUSSIAN_SEED":"M2_UNIFORM_SEED");
            if(value)engine.seed(static_cast<uint32_t>(std::stoull(value)));
            if(const char* root=std::getenv("M2_RNG_TRACE")) {
                std::ofstream f(std::string(root)+".stream"+std::to_string(s)+".initial.txt");
                f<<engine<<"\nnormal="<<normal<<"\nuniform="<<uniform<<"\ndraws="<<draws<<"\n";
            }
        }
        ~M2RandomStream() {
            if(const char* root=std::getenv("M2_RNG_TRACE")) {
                std::ofstream f(std::string(root)+".stream"+std::to_string(stream)+".final.txt");
                f<<engine<<"\nnormal="<<normal<<"\nuniform="<<uniform<<"\ndraws="<<draws<<"\n";
            }
        }
    };
    inline M2RandomStream& M2Stream(int s) {
        if(s==0){static thread_local M2RandomStream x(0);return x;}
        static thread_local M2RandomStream x(1);return x;
    }

    // thread-safe
    inline float GaussianRandom(float mean, float stdDev)
    {
        auto& random=M2Stream(0);random.draws++;
        return mean + random.normal(random.engine) * stdDev;
    }

    inline float uniformRandom(float min, float max)
    {
        auto& random=M2Stream(1);random.draws++;
        return min + random.uniform(random.engine) * (max - min);
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
            if(const char* root=std::getenv("M2_RNG_TRACE")) {
                std::ofstream f(std::string(root)+".cache"+std::to_string(Size)+".f32",std::ios::binary);
                f.write(reinterpret_cast<const char*>(m_precalculatedTable.data()),sizeof(float)*Size);
                std::ofstream index(std::string(root)+".cache"+std::to_string(Size)+".index.txt");index<<m_index;
            }
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