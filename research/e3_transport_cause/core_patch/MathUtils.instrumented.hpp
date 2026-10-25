#pragma once
#include "gaden/core/Logging.hpp"
#include "gaden/core/Vectors.hpp"
#include <random>
#include <fstream>
#include <sstream>
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


    struct E3Stream {
        std::mt19937 engine;
        std::normal_distribution<> normal{0,1};
        std::uniform_real_distribution<float> uniform{0.f,1.f};
        uint64_t draws=0;std::string name;
        E3Stream(std::string n):name(n){
            const char* v=std::getenv(("E3_"+name+"_WORDS").c_str());
            if(v){std::stringstream s(v);std::string w;std::vector<uint32_t>a;while(std::getline(s,w,','))a.push_back(std::stoul(w));std::seed_seq seed(a.begin(),a.end());engine.seed(seed);}
            log("initial");
        }
        void log(const std::string&phase){if(const char*p=std::getenv("E3_RNG_TRACE")){std::ofstream f(std::string(p)+"."+name+"."+phase+".txt");f<<std::setprecision(17)<<engine<<"\nnormal="<<normal<<"\nuniform="<<uniform<<"\ndraws="<<draws<<'\n';}}
        ~E3Stream(){log("final");}
    };
    inline E3Stream& e3Gaussian(){static thread_local E3Stream s("GAUSSIAN");return s;}
    inline E3Stream& e3Uniform(){static thread_local E3Stream s("UNIFORM");return s;}
    inline float GaussianRandom(float mean,float stdDev){auto&s=e3Gaussian();s.draws++;return mean+s.normal(s.engine)*stdDev;}
    inline float uniformRandom(float min,float max){auto&s=e3Uniform();s.draws++;return min+s.uniform(s.engine)*(max-min);}
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
            if(const char*p=std::getenv("E3_RNG_TRACE")){std::ofstream f(std::string(p)+".cache.f32",std::ios::binary);f.write((char*)m_precalculatedTable.data(),Size*sizeof(float));std::ofstream i(std::string(p)+".cache.initial.txt");i<<"index="<<m_index<<" size="<<Size<<"\n";}
        }

        ~PrecalculatedGaussian(){if(const char*p=std::getenv("E3_RNG_TRACE")){std::ofstream f(std::string(p)+".cache.final.txt");f<<"index="<<m_index<<" calls="<<e3Calls<<"\n";}}

        float nextValue(float mean, float stdev)
        {
            m_index = (m_index + 1) % Size; ++e3Calls;
            return mean + stdev * m_precalculatedTable[m_index];
        }

    private:
        uint64_t e3Calls=0;
        uint16_t m_index;
        std::array<float, Size> m_precalculatedTable;
    };

} // namespace gaden