#include <gsl_server/algorithms/Common/Utils/Math.hpp>
#include <xxHash/xxhash32.h>
#include <random>
#include <chrono>
#include <atomic>
#include <cstring>
#include <sstream>
#include <fstream>
#include <iomanip>
#include <stdexcept>

namespace GSL::Utils
{
    static thread_local std::minstd_rand0 RNGengine;

    namespace { struct O24AuditState {O24Snapshot snap;uint32_t *seed=nullptr,*state=nullptr;uint16_t *index=nullptr;const float*table=nullptr;std::normal_distribution<>*dist=nullptr;bool written=false;};
    static thread_local O24AuditState oa;static std::atomic<uint64_t> oat{0};
    uint64_t hstep(uint64_t h,uint64_t x){return (h^x)*1099511628211ULL;}}
    void O24NoteUniform(uint32_t*seed,uint32_t*state){oa.seed=seed;oa.state=state;++oa.snap.uc;oa.snap.uh=hstep(oa.snap.uh,*state);}
    void O24NoteNormal(void*distribution,double value){oa.dist=static_cast<std::normal_distribution<>*>(distribution);uint64_t b;std::memcpy(&b,&value,8);++oa.snap.nc;oa.snap.nh=hstep(oa.snap.nh,b);}
    void O24NoteCache(uint16_t*index,const float*table,int size){oa.index=index;oa.table=table;oa.snap.size=size;oa.snap.initial=*index;}
    void O24NoteCacheNext(float value){uint32_t b;std::memcpy(&b,&value,4);++oa.snap.gc;oa.snap.gh=hstep(oa.snap.gh,b);}
    O24Snapshot O24Capture(){if(!oa.snap.tid)oa.snap.tid=++oat;auto s=oa.snap;s.ui=oa.seed!=nullptr;if(s.ui){s.seed=*oa.seed;s.state=*oa.state;}s.ci=oa.index!=nullptr;if(s.ci)s.index=*oa.index;std::ostringstream e;e<<RNGengine;s.engine=e.str();if(oa.dist){std::ostringstream d;d<<std::setprecision(17)<<*oa.dist;s.distribution=d.str();}return s;}
    void O24WriteCache(const std::string&prefix){if(oa.table&&!oa.written){std::ofstream f(prefix+".thread"+std::to_string(oa.snap.tid)+".f32",std::ios::binary);if(!f)throw std::runtime_error("Cannot write RNG cache");f.write(reinterpret_cast<const char*>(oa.table),oa.snap.size*sizeof(float));if(!f)throw std::runtime_error("RNG cache write failed");oa.written=true;}}
    std::string O24Snapshot::json()const{std::ostringstream s;s<<"{\"ui\":"<<int(ui)<<",\"seed\":"<<seed<<",\"state\":"<<state<<",\"uc\":"<<uc<<",\"uh\":"<<uh<<",\"gc\":"<<gc<<",\"gh\":"<<gh<<",\"nc\":"<<nc<<",\"nh\":"<<nh<<",\"tid\":"<<tid<<",\"ci\":"<<int(ci)<<",\"size\":"<<size<<",\"index\":"<<index<<",\"initial\":"<<initial<<",\"engine\":\""<<engine<<"\",\"distribution\":\""<<distribution<<"\"}";return s.str();}


    double lerp(double start, double end, double proportion)
    {
        if (proportion < 0 || std::isnan(proportion))
            return start;

        return start + (end - start) * std::min(1.0, proportion);
    }

    double clamp(double val, double min, double max)
    {
        return std::max(min, std::min(val, max));
    }

    double remapRange(double value, double low1, double high1, double low2, double high2)
    {
        return low2 + (value - low1) * (high2 - low2) / (high1 - low1);
    }

    double evaluate1DGaussian(double distance, double sigma)
    {
        return exp(-0.5 * (std::pow(distance, 2) / std::pow(sigma, 2))) / (sigma * std::sqrt(2 * M_PI));
    }

    double evaluate2DGaussian(const Vector2& sampleOffset, const Vector2& sigma, float distributionRotation)
    {
        // we rotate the vector instead of the gaussian because keeping the distribution axis-aligned removes several terms from the PDF equation
        Vector2 v = vmath::rotate(sampleOffset, distributionRotation);

        return std::exp(-0.5 * (std::pow(v.x / sigma.x, 2) + std::pow(v.y / sigma.y, 2))) / (2 * M_PI * sigma.x * sigma.y);
    }

    double logOddsToProbability(double lo)
    {
        return 1.0 - 1.0 / (1 + std::exp(lo));
    }

    double randomFromGaussian(double mean, double stdev)
    {
        static thread_local std::normal_distribution<> dist{0, stdev};
        static thread_local double previousStdev = stdev;

        if (stdev != previousStdev)
        {
            dist = std::normal_distribution<> {0, stdev};
            previousStdev = stdev;
        }

        const double nativeValue = mean + dist(RNGengine);
        O24NoteNormal(&dist,nativeValue);
        return nativeValue;
    }

    double uniformRandom(double min, double max)
    {
#if 1
        // xxHash-based RNG. I don't really know much about it, but it goes vroom vroom
        static thread_local uint32_t seed = std::chrono::high_resolution_clock::now().time_since_epoch().count();
        static thread_local uint32_t state = 0xFFFF;
        state = XXHash32::hash(&state, sizeof(state), seed);
        O24NoteUniform(&seed,&state);

        constexpr double reciprocalMax = 1 / (double)std::numeric_limits<uint32_t>::max();
        double rndVal01 = state * reciprocalMax;
        return min + rndVal01 * (max - min);
#else
        static thread_local std::uniform_real_distribution<double> distribution {0.0, 0.999};
        return min + distribution(RNGengine) * (max - min);
#endif
    }

    double KLD(std::vector<std::vector<double>>& a, std::vector<std::vector<double>>& b)
    {
        double total = 0;
        for (int r = 0; r < a.size(); r++)
        {
            for (int c = 0; c < a[0].size(); c++)
            {
                double aux = a[r][c] * std::log(a[r][c] / b[r][c]) + (1 - a[r][c]) * std::log((1 - a[r][c]) / (1 - b[r][c]));
                total += std::isnan(aux) ? 0 : aux;
            }
        }
        return total;
    }

    void NormalizeDistribution(Grid2D<double> variable)
    {
        // we account for the possibility of having positive and negative values by offsetting everything by the value of the minimum (capped at 0)
        // so, [-1, -0.5, 1, 2] would become [0, 0.5, 2, 3] before the normalization happens
        double total = 0;
        int count = 0;
        for (int i = 0; i < variable.data.size(); i++)
        {
            if (variable.occupancy[i] == Occupancy::Free)
            {
                total += variable.data[i];
                count++;
            }
        }

        #pragma omp parallel for
        for (int i = 0; i < variable.data.size(); i++)
        {
            if (variable.occupancy[i] == Occupancy::Free)
            {
                variable.data[i] = variable.data[i] / total;
            }
        }
    }

    float EquallyDistributed01F()
    {
        constexpr float phi = 1.61803398875;
        static float current = 0;
        current += phi;
        return fmod(current, 1);
    }
} // namespace GSL::Utils