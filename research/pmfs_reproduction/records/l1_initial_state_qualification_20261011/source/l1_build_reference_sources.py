"""Make an isolated, auditable RNG/wind-provider variant of the pinned kernel."""
from pathlib import Path
import re,json,hashlib,difflib
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'outputs/PMFS_L1_INITIAL_STATE_QUALIFICATION_20261011'
SHARE=Path('D:/ZYC/A-gas/workspace/PMFS_L1_INITIAL_STATE_QUALIFICATION_20261011')

RNG_HEADER=r'''#pragma once
#include <cstdint>
#include <random>
#include <array>
#include <sstream>
#include <iomanip>
#include <stdexcept>
class L1InstanceGaussian {
 std::mt19937 engine;std::array<float,1000> table;size_t index=0;
 public:
 explicit L1InstanceGaussian(uint32_t seed):engine(seed){std::uniform_real_distribution<float> u(0,1000);index=size_t(u(engine));std::normal_distribution<double> n(0,1);for(auto&v:table)v=float(n(engine));}
 float nextValue(float mean,float sd){index=(index+1)%1000;return mean+sd*table[index];}
 std::string state()const{std::ostringstream s;s<<engine<<" "<<index<<" ";s<<std::setprecision(9);for(auto v:table)s<<v<<" ";return s.str();}
 void restore(const std::string&x){std::istringstream s(x);s>>engine>>index;for(auto&v:table)s>>v;if(!s||index>=1000)throw std::runtime_error("RNG_STATE_BAD");}
};
'''

WORKER=r'''#include "gaden/L1RunningSimulation.hpp"
#include "gaden/datatypes/GasTypes.hpp"
#include <fstream>
#include <iostream>
#include <iomanip>
#include <chrono>
#include <cmath>
#include <memory>
#include <sys/resource.h>
#include <unistd.h>
#include <numeric>
#include <algorithm>
using namespace gaden;
template<class T>std::vector<T> readbin(const std::string& p,size_t count){std::vector<T>a(count);std::ifstream f(p,std::ios::binary);f.read(reinterpret_cast<char*>(a.data()),a.size()*sizeof(T));if(!f||size_t(f.gcount())!=a.size()*sizeof(T))throw std::runtime_error("INPUT_BINARY_LENGTH_"+p);return a;}
struct WindAssets{int modes,nfree;std::vector<int32_t> node;std::vector<float> faces;std::vector<double>times,coeff[2];};
class WindReference final: public L1RunningSimulation{
 std::shared_ptr<const WindAssets>w;int ref;std::array<double,24>c;
 public: WindReference(Parameters p,std::shared_ptr<EnvironmentConfiguration> e,std::shared_ptr<const WindAssets>assets,int r):L1RunningSimulation(p,e),w(assets),ref(r){}
 void Prepare(){double t=GetCurrentTime();size_t i=std::upper_bound(w->times.begin(),w->times.end(),t)-w->times.begin();if(i==0)i=1;if(i>=w->times.size())i=w->times.size()-1;double a=(t-w->times[i-1])/(w->times[i]-w->times[i-1]);for(int m=0;m<24;++m)c[m]=(1-a)*w->coeff[ref][(i-1)*24+m]+a*w->coeff[ref][i*24+m];}
 Vector3 SampleWindAtPosition(const Vector3&p)const override{
  auto ijk=config->environment.coordsToIndices(p);if(!config->environment.IsInBounds(ijk))throw std::runtime_error("WIND_QUERY_OOB");size_t cell=config->environment.indexFrom3D(ijk);int n=w->node[cell];if(n<0)throw std::runtime_error("WIND_QUERY_NONFREE");auto o=config->environment.coordsOfCellOrigin(ijk);float h=config->environment.description.cellSize;double f[3]={(p.x-o.x)/h,(p.y-o.y)/h,(p.z-o.z)/h};double v[3]={0,0,0};for(int d=0;d<3;++d){double q=std::clamp(f[d],0.,1.);for(int m=0;m<24;++m){size_t k=(size_t(m)*w->nfree+n)*6+2*d;v[d]+=c[m]*((1-q)*w->faces[k]+q*w->faces[k+1]);}}return Vector3(v[0],v[1],v[2]);
 }
};
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("ONE_SHARED_ROOT_REQUIRED");std::string root=argv[1];
 rlimit mem{1024ULL*1024*1024,1024ULL*1024*1024};if(setrlimit(RLIMIT_AS,&mem))throw std::runtime_error("RLIMIT_AS_FAILED");
 L1InstanceGaussian ra(123),rb(456);auto before=ra.state();std::array<float,128>draws;for(auto&x:draws)x=ra.nextValue(0,1);ra.restore(before);for(auto x:draws)if(x!=ra.nextValue(0,1))throw std::runtime_error("RNG_ROUNDTRIP_FAIL");if(ra.state()==rb.state())throw std::runtime_error("RNG_REFERENCE_COLLISION");
 std::ofstream rng(root+"/L1_RNG_UNIT_PASS.txt");rng<<"128draws exactstate roundtrip; independentseeds differ; no physics rerun\n";rng.close();
 std::ifstream f(root+"/runtime_settings.txt");int nx,ny,nz,N,M,NT;double target,dt,rate,ppm,sigma,gamma,noise,temp,pressure;int gas;
 f>>nx>>ny>>nz>>N>>M>>NT>>target>>dt>>rate>>ppm>>sigma>>gamma>>noise>>temp>>pressure>>gas;if(!f||M!=24)throw std::runtime_error("SETTINGS_BAD");
 auto env=std::make_shared<EnvironmentConfiguration>();if(env->environment.ReadFromFile(root+"/OccupancyGrid3D.csv")!=ReadResult::OK)throw std::runtime_error("GEOMETRY_READ_FAIL");
 if(env->environment.numCells()!=size_t(nx)*ny*nz)throw std::runtime_error("GEOMETRY_SIZE_FAIL");
 // EnvironmentConfiguration::ReadDirectory is deliberately not called: it loads CFD.
 auto w=std::make_shared<WindAssets>();w->modes=M;w->nfree=N;w->node=readbin<int32_t>(root+"/free_node_index.i32",size_t(nx)*ny*nz);w->faces=readbin<float>(root+"/flow_faces.f32",size_t(M)*N*6);w->times=readbin<double>(root+"/wind_times.f64",NT);for(int r=0;r<2;++r)w->coeff[r]=readbin<double>(root+"/wind_coeff_ref"+std::to_string(r)+".f64",size_t(NT)*M);
 std::ifstream pfile(root+"/pilots.txt");std::ofstream summary(root+"/L1_SIX_FORWARD_RESULTS.csv");summary<<"ordinal,native_id,ref,seed,x,y,z,steps,final_physical_s,born,survivors,outlet_removed,min_sigma_cm,max_sigma_cm,ppm_query,forward_wall_s,moles_remaining,moles_released\n";summary<<std::setprecision(12);
 auto batchStart=std::chrono::steady_clock::now();int calls=0;
 for(int k=0;k<6;++k){int id,ref;uint32_t seed;double x,y,z;pfile>>id>>ref>>seed>>x>>y>>z;if(!pfile)throw std::runtime_error("PILOT_INPUT_SHORT");
  L1RunningSimulation::Parameters p;p.referenceSeed=seed;p.deltaTime=dt;p.numFilaments_sec=rate;p.filamentPPMcenter_initial=ppm;p.filamentInitialSigma=sigma;p.filamentGrowthGamma=gamma;p.filamentNoise_std=noise;p.temperature=temp;p.pressure=pressure;p.expectedNumIterations=size_t(std::ceil(target/dt))+2;p.saveResults=false;p.preCalculateConcentrations=false;p.windLoop=std::nullopt;p.source=std::make_shared<PointSource>();p.source->sourcePosition=Vector3(x,y,z);p.source->gasType=GasType(gas);
  if(env->environment.at(p.source->sourcePosition)!=Environment::CellState::Free)throw std::runtime_error("SOURCE_NOT_FREE_STOP");
  WindReference sim(p,env,w,ref);auto begin=std::chrono::steady_clock::now();calls++;std::ofstream marker(root+"/L1_PROFILE_PROGRESS.txt");marker<<calls<<" physicalforwards started; max6\n";marker.close();
  size_t steps=0;while(sim.GetCurrentTime()<target){double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-batchStart).count();if(elapsed>=300)throw std::runtime_error("TOTAL_SIX_FORWARD_300S_STOP");sim.Prepare();sim.AdvanceTimestep();steps++;}
  double mins=1e9,maxs=0;for(const auto&fil:sim.GetFilaments()){if(!std::isfinite(fil.sigma)||fil.sigma<=0||env->environment.at(fil.position)!=Environment::CellState::Free)throw std::runtime_error("FINAL_FILAMENT_STATE_FAIL");mins=std::min(mins,double(fil.sigma));maxs=std::max(maxs,double(fil.sigma));}
  double c=sim.SampleConcentration(Vector3(-.9,.15,-.2));if(!std::isfinite(c)||c<0)throw std::runtime_error("PPM_READOUT_FAIL");size_t born=sim.BirthCount(),surv=sim.GetFilaments().size();if(surv>born)throw std::runtime_error("MASS_BOOKKEEPING_FAIL");
  double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();double mole=sim.simulationMetadata.constants.totalMolesInFilament;
  summary<<k<<","<<id<<","<<ref<<","<<seed<<","<<x<<","<<y<<","<<z<<","<<steps<<","<<sim.GetCurrentTime()<<","<<born<<","<<surv<<","<<(born-surv)<<","<<mins<<","<<maxs<<","<<c<<","<<sec<<","<<(surv*mole)<<","<<(born*mole)<<"\n";summary.flush();
  std::ofstream ck(root+"/reference_"+std::to_string(k)+"_own_state.bin",std::ios::binary);auto&v=sim.GetFilaments();ck.write(reinterpret_cast<const char*>(v.data()),v.size()*sizeof(Filament));ck.close();std::ofstream rs(root+"/reference_"+std::to_string(k)+"_rng_state.txt");rs<<sim.RNGState();rs.close();
  std::cout<<"FORWARD "<<k<<" wall="<<sec<<" steps="<<steps<<" t="<<sim.GetCurrentTime()<<" survive="<<surv<<" ppm="<<c<<std::endl;
 }
 double total=std::chrono::duration<double>(std::chrono::steady_clock::now()-batchStart).count();rusage u;getrusage(RUSAGE_SELF,&u);std::ofstream receipt(root+"/L1_PROFILE_CPP_RECEIPT.txt");receipt<<std::setprecision(12)<<"completed "<<calls<<"\nbatch_wall_s "<<total<<"\nmaxRSS_KiB "<<u.ru_maxrss<<"\nFilament_size_bytes "<<sizeof(Filament)<<"\nphysics_replays 0\n";
 return 0;
 }catch(const std::exception&e){std::cerr<<"L1_FAIL_CLOSED "<<e.what()<<std::endl;return 2;}}
'''

def main():
    original_h=(SHARE/'RunningSimulation.original.hpp').read_text();original_c=(SHARE/'RunningSimulation.original.cpp').read_text()
    header=original_h.replace('RunningSimulation','L1RunningSimulation')
    header=header.replace('#pragma once','#pragma once\n#include "L1Rng.hpp"')
    header=header.replace('struct Parameters\n        {','struct Parameters\n        {\n            uint32_t referenceSeed = 0;')
    header=header.replace('Vector3 SampleWind(const Vector3i& indices) const override;', 'Vector3 SampleWind(const Vector3i& indices) const override;\n        virtual Vector3 SampleWindAtPosition(const Vector3& p) const { return SampleWind(config->environment.coordsToIndices(p)); }\n        size_t BirthCount()const{return birthCount;}\n        std::string RNGState()const{return gaussian.state();}')
    header=header.replace('Parameters parameters;','Parameters parameters;\n        L1InstanceGaussian gaussian;\n        size_t birthCount = 0;')
    cpp=original_c.replace('RunningSimulation','L1RunningSimulation')
    cpp=re.sub(r'    static thread_local PrecalculatedGaussian<1000> gaussian;[^\n]*\n','',cpp)
    cpp=cpp.replace(': parameters(params), Simulation(envConfig)',': parameters(params), gaussian(params.referenceSeed), Simulation(envConfig)')
    cpp=cpp.replace('params.expectedNumIterations * params.numFilaments_sec / params.deltaTime','size_t(std::ceil(params.expectedNumIterations * params.numFilaments_sec * params.deltaTime))+1')
    cpp=cpp.replace('rawBuffer.resize(serialization::defaultBufferSize);\n        compressedBuffer.resize(serialization::defaultBufferSize);','if (parameters.saveResults) { rawBuffer.resize(serialization::defaultBufferSize); compressedBuffer.resize(serialization::defaultBufferSize); }')
    cpp=cpp.replace('activeFilaments->emplace_back(position, parameters.filamentInitialSigma);','activeFilaments->emplace_back(position, parameters.filamentInitialSigma);\n            birthCount++;')
    cpp=cpp.replace('Vector3 windVec = SampleWind(cellIdx);','Vector3 windVec = SampleWindAtPosition(filament.position);')
    (SHARE/'gaden').mkdir(exist_ok=True)
    for p,text in [(SHARE/'gaden/L1RunningSimulation.hpp',header),(SHARE/'gaden/L1Rng.hpp',RNG_HEADER),(SHARE/'L1RunningSimulation.cpp',cpp),(SHARE/'l1_reference_worker.cpp',WORKER)]:p.write_text(text,encoding='utf8',newline='\n')
    (OUT/'L1_KERNEL_PATCH.diff').write_text(''.join(difflib.unified_diff(original_c.splitlines(True),cpp.splitlines(True),fromfile='pinned/RunningSimulation.cpp',tofile='isolated/L1RunningSimulation.cpp')),encoding='utf8')
    manifest={str(p.relative_to(SHARE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SHARE/'gaden/L1RunningSimulation.hpp',SHARE/'gaden/L1Rng.hpp',SHARE/'L1RunningSimulation.cpp',SHARE/'l1_reference_worker.cpp']}
    (OUT/'L1_ISOLATED_SOURCE_SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'isolated_files':4,'original_sources_modified':False,'physics_calls':0,'changes':'namespace rename, instance RNG, position-awarewindcallback, lazy unusedbuffers/reserveunits, birthcounter'}))

if __name__=='__main__':main()
