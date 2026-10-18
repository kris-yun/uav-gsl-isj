#include <gsl_server/algorithms/Common/Utils/Math.hpp>
#include <xxHash/xxhash32.h>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <sstream>
#include <random>
#include <vector>
#include <chrono>
namespace mirror {namespace Utils=mirror;static thread_local std::minstd_rand0 RNGengine;static uint32_t capturedSeed;
double uniformRandom(double min, double max)
    {
#if 1
        // xxHash-based RNG. I don't really know much about it, but it goes vroom vroom
        const uint32_t seed = capturedSeed;
        static thread_local uint32_t state = 0xFFFF;
        state = XXHash32::hash(&state, sizeof(state), seed);

        constexpr double reciprocalMax = 1 / (double)std::numeric_limits<uint32_t>::max();
        double rndVal01 = state * reciprocalMax;
        return min + rndVal01 * (max - min);
#else
        static thread_local std::uniform_real_distribution<double> distribution {0.0, 0.999};
        return min + distribution(RNGengine) * (max - min);
#endif
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

        return mean + dist(RNGengine);
    }
template<int Size>
class PrecalculatedGaussian
    {
    public:
        PrecalculatedGaussian()
        {
            m_index = uniformRandom(0, Size);
            for (size_t i = 0; i < Size; i++)
                m_precalculatedTable[i] = Utils::randomFromGaussian(0, 1);
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
}
template<class T>bool bits(T a,T b){return std::memcmp(&a,&b,sizeof(T))==0;}
uint64_t step(uint64_t h,uint64_t v){return(h^v)*1099511628211ULL;}
int main(int argc,char**argv){using namespace GSL::Utils;if(argc!=2)return 2;std::string prefix=argv[1];
 // Production seed remains native. Only the independent author-code mirror
 // receives the already observed actual seed; production is never reseeded.
 for(int i=0;i<500;++i){double a=uniformRandom(-2.,3.);auto s=O24Capture();if(i==0)mirror::capturedSeed=s.seed;double b=mirror::uniformRandom(-2.,3.);if(!bits(a,b))return 3;}
 for(int i=0;i<100;++i){double sd=(i%2)?.3:.8,mean=(i%3)-1;double a=randomFromGaussian(mean,sd),b=mirror::randomFromGaussian(mean,sd);if(!bits(a,b))return 4;}
 PrecalculatedGaussian<2500> actual;mirror::PrecalculatedGaussian<2500> native;
 for(int i=0;i<5000;++i){float a=actual.nextValue(float(i%3),.5f),b=native.nextValue(float(i%3),.5f);if(!bits(a,b))return 5;}
 if(!bits(randomFromGaussian(0,1),mirror::randomFromGaussian(0,1)))return 12;
 O24WriteCache(prefix);auto before=O24Capture();std::ifstream f(prefix+".thread"+std::to_string(before.tid)+".f32",std::ios::binary);std::vector<float>table(before.size);f.read(reinterpret_cast<char*>(table.data()),before.size*sizeof(float));if(!f)return 6;
 std::minstd_rand0 engine;std::normal_distribution<>dist;std::istringstream es(before.engine),ds(before.distribution);es>>engine;ds>>dist;if(!es||!ds)return 7;
 uint32_t state=before.state;int index=before.index;uint64_t uc=before.uc,uh=before.uh,gc=before.gc,gh=before.gh,nc=before.nc,nh=before.nh;
 for(int i=0;i<1000;++i){
  double a=uniformRandom(-1.,2.);state=XXHash32::hash(&state,sizeof(state),before.seed);double b=-1.+(state*(1./double(UINT32_MAX)))*3.;if(!bits(a,b))return 8;++uc;uh=step(uh,state);
  float x=actual.nextValue(0,.5f);index=(index+1)%before.size;float y=.5f*table[index];if(!bits(x,y))return 9;uint32_t q;std::memcpy(&q,&table[index],4);++gc;gh=step(gh,q);
  double n=randomFromGaussian(0,1),m=dist(engine);if(!bits(n,m))return 10;uint64_t z;std::memcpy(&z,&m,8);++nc;nh=step(nh,z);
 }
 auto after=O24Capture();std::ostringstream ee,dd;ee<<engine;dd<<std::setprecision(17)<<dist;
 if(uc!=after.uc||uh!=after.uh||gc!=after.gc||gh!=after.gh||nc!=after.nc||nh!=after.nh||state!=after.state||index!=after.index||ee.str()!=after.engine||dd.str()!=after.distribution)return 11;
 std::cout<<"{\"status\":\"PASS_PRODUCTION_RNG_VS_AUTHOR_MIRROR_AND_CAPTURE_REPLAY\",\"uniform_mirror_draws\":500,\"normal_mirror_draws\":100,\"cached_mirror_draws\":5000,\"replayed_interleaved_steps\":1000,\"actual_native_seed\":"<<after.seed<<",\"before\":"<<before.json()<<",\"after\":"<<after.json()<<"}\n";
}
