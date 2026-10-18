from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;F=Path(r'D:\ZYC\UAV\.codex\worktrees\pmfs-paper-eq6-20261017\A-gas\research\pmfs_o24_baseline_freeze_20261018')
def body(s,sig):
 a=s.index(sig);b=s.index('{',a);d=0
 for j in range(b,len(s)):
  d+=(s[j]=='{')-(s[j]=='}')
  if d==0:return s[a:j+1]
 raise ValueError(sig)
orig=(F/'upstream_readonly/gsl_server/src/gsl_server/algorithms/Common/Utils/Math.cpp').read_text(encoding='utf-8');hdr=(F/'upstream_readonly/gsl_server/src/gsl_server/algorithms/Common/Utils/Math.hpp').read_text(encoding='utf-8')
uniform=body(orig,'double uniformRandom(');line='static thread_local uint32_t seed = std::chrono::high_resolution_clock::now().time_since_epoch().count();';assert line in uniform;uniform=uniform.replace(line,'const uint32_t seed = capturedSeed;')
normal=body(orig,'double randomFromGaussian(')
template=body(hdr,'class PrecalculatedGaussian')+';';template='template<int Size>\n'+template
text='''#include <gsl_server/algorithms/Common/Utils/Math.hpp>
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
'''+uniform+'\n'+normal+'\n'+template+'''
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
 std::cout<<"{\\\"status\\\":\\\"PASS_PRODUCTION_RNG_VS_AUTHOR_MIRROR_AND_CAPTURE_REPLAY\\\",\\\"uniform_mirror_draws\\\":500,\\\"normal_mirror_draws\\\":100,\\\"cached_mirror_draws\\\":5000,\\\"replayed_interleaved_steps\\\":1000,\\\"actual_native_seed\\\":"<<after.seed<<",\\\"before\\\":"<<before.json()<<",\\\"after\\\":"<<after.json()<<"}\\n";
}
'''
(R/'rng_recording_check.cpp').write_text(text,encoding='utf-8',newline='\n')
(R/'RNG_CHECK_PROVENANCE.json').write_text(json.dumps(dict(author_functions_sha256={k:hashlib.sha256(body(orig,k).encode()).hexdigest()for k in ['double uniformRandom(','double randomFromGaussian(']},qualification_only_mirror_seed='Actual seed observed from production, never forced in the production implementation',production_seed_initialization_unchanged=line in (R/'source_runtime/src/gsl_server/algorithms/Common/Utils/Math.cpp').read_text(encoding='utf-8')),indent=2)+'\n',encoding='utf-8')
print('RNG recording qualification source prepared')
