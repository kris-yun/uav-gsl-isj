from pathlib import Path
import csv,hashlib,json,re,struct
P=Path(__file__).resolve().parent;R=Path(json.loads((P/'PREPARED_LOCATION.json').read_text(encoding='utf-8'))['path']);AUD=Path(r'D:\ZYC\A-gas\workspace\PMFS_EARLY_DECLARATION_AUDIT_20261018');OFF=R/'upstream_readonly/gsl_server'
def read(p):return list(csv.DictReader(p.open(encoding='utf-8')))
def body(s,sig):
 a=s.index(sig);b=s.index('{',a);d=0
 for j in range(b,len(s)):
  d+=(s[j]=='{')-(s[j]=='}')
  if d==0:return s[a:j+1]
 raise ValueError(sig)
parts=[]
def extract(rel,sig):
 p=OFF/rel;t=body(p.read_text(encoding='utf-8'),sig);parts.append(dict(source=rel,signature=sig,body_sha256=hashlib.sha256(t.encode()).hexdigest()));return t
mathrel='src/gsl_server/algorithms/Common/Utils/Math.cpp';utils=extract(mathrel,'double lerp(')+'\n'+extract(mathrel,'double logOddsToProbability(')+'\n'+extract(mathrel,'void NormalizeDistribution(')
scorer=extract('src/gsl_server/algorithms/PMFS/internal/Simulations.cpp','double Simulations::sourceProbFromMaps(')
readoutrel='src/gsl_server/algorithms/PMFS/PMFS_utils.cpp';ef=extract(readoutrel,'Vector2 PMFS::expectedValueSource(');vf=extract(readoutrel,'double PMFS::varianceSourcePosition(')
metadata=(OFF/'src/gsl_server/algorithms/Common/Grid2D.hpp').read_text(encoding='utf-8');indices=body(metadata,'size_t indexOf(')+'\n'+body(metadata,'Vector2 indexToCoordinates(int i, int j,')
head='''#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>
#include <DDA/Vectors.h>
#define ZoneScoped
#define GSL_ASSERT(x) assert(x)
using Vector2=DDA::Vector2; using Vector2Int=DDA::Vector2Int;
enum class Occupancy {Obstacle=0,Free=1};
struct Grid2DMetadata {Vector2 origin;float cellSize;Vector2Int dimensions;
'''+indices+'''
};
template<class T> struct Grid2D { std::vector<T>&data;std::vector<Occupancy>&occupancy;Grid2DMetadata metadata; };
struct HitProbability {double logOdds=0,confidence=0,omega=0;};
namespace GSL::Utils {
'''+utils+'''
}
namespace Utils=GSL::Utils;
struct Simulations {struct Settings{double sourceDiscriminationPower=.2;}settings;
double sourceProbFromMaps(const Grid2D<HitProbability>&,const std::vector<float>&)const;};
'''+scorer+'\n'
cl='''struct PMFS {Grid2DMetadata gridMetadata;std::vector<Occupancy>occupancy;std::vector<double>sourceProbability;
Vector2 expectedValueSource(double);double varianceSourcePosition();};
'''
head+='namespace upstream {\n'+cl+ef+'\n'+vf+'\n}\n'
head+='namespace ported {\n'+cl+(ef+'\n'+vf).replace('j < gridMetadata.dimensions.x','j < gridMetadata.dimensions.y')+'\n}\n'
native_alpha='double exponent = -cell.omega / std::pow(settings.confidenceMeasurementWeight, 2);'
assert native_alpha in (OFF/'src/gsl_server/algorithms/PMFS/PMFSLib.cpp').read_text(encoding='utf-8')
head+='''double alpha_native(double omega) { struct {double omega;}cell{omega};struct {double confidenceMeasurementWeight=1.;}settings;
'''+native_alpha+'''
return 1-std::exp(exponent);}
double alpha_p24(double omega) {return 1-std::exp(-omega*omega);}
template<class T>T get(std::ifstream&f){T v{};f.read(reinterpret_cast<char*>(&v),sizeof(v));if(!f)throw std::runtime_error("Truncated input");return v;}
struct Call {int x,y,sx,sy;double saved;std::vector<float>hit;};
int main(int argc,char**argv){try{
 if(argc!=2)return 2;std::ifstream f(argv[1],std::ios::binary);if(get<uint32_t>(f)!=0x1234abcd)return 3;int groups=get<int32_t>(f);
 // Exact native readout on a rectangle demonstrates the audited domain repair.
 upstream::PMFS old;ported::PMFS fixed;old.gridMetadata={{0,0},1,{3,5}};old.occupancy.assign(15,Occupancy::Free);old.sourceProbability.assign(15,1./15);fixed.gridMetadata=old.gridMetadata;fixed.occupancy=old.occupancy;fixed.sourceProbability=old.sourceProbability;
 if(std::abs(old.varianceSourcePosition()-.8)>1e-12||std::abs(fixed.varianceSourcePosition()-8./3)>1e-12)return 4;
 if(alpha_native(0)!=0||std::abs(alpha_native(1)-(1-std::exp(-1.)))>1e-15)return 5;
 std::cout<<std::setprecision(17)<<"group,calls,max_saved_score_relative_error,official_normalized_mass,official_variance_m2,official_top5_error_m,official_mean_error_m,p24_variance_m2,p24_posterior_max_abs_error\\n";
 for(int g=0;g<groups;++g){
  int nx=get<int32_t>(f),ny=get<int32_t>(f),nf=get<int32_t>(f),nc=get<int32_t>(f);float ox=get<float>(f),oy=get<float>(f),cs=get<float>(f);double truthx=get<double>(f),truthy=get<double>(f);int n=nx*ny;
  ported::PMFS official,paper;official.gridMetadata={{ox,oy},cs,{nx,ny}};official.occupancy.assign(n,Occupancy::Obstacle);official.sourceProbability.assign(n,0);paper=official;
  std::vector<HitProbability>m(n);std::vector<double>reference(n);std::vector<int>legal;
  for(int i=0;i<nf;++i){int x=get<int32_t>(f),y=get<int32_t>(f),idx=x+nx*y;m[idx].logOdds=get<double>(f);m[idx].omega=get<double>(f);reference[idx]=get<double>(f);official.occupancy[idx]=paper.occupancy[idx]=Occupancy::Free;legal.push_back(idx);}
  std::vector<Call>calls;for(int i=0;i<nc;++i){Call c;c.x=get<int32_t>(f);c.y=get<int32_t>(f);c.sx=get<int32_t>(f);c.sy=get<int32_t>(f);c.saved=get<double>(f);if(get<int32_t>(f)!=n)return 6;c.hit.resize(n);f.read(reinterpret_cast<char*>(c.hit.data()),n*sizeof(float));if(!f)return 7;calls.push_back(c);}
  std::stable_sort(calls.begin(),calls.end(),[](const Call&a,const Call&b){return a.sx*a.sy>b.sx*b.sy;});Simulations calc;Grid2D<HitProbability>measured{m,official.occupancy,official.gridMetadata};double maxrel=0;
  for(auto&c:calls){for(auto&i:legal)m[i].confidence=alpha_p24(m[i].omega);calc.settings.sourceDiscriminationPower=1;double p=calc.sourceProbFromMaps(measured,c.hit);maxrel=std::max(maxrel,std::abs(p-c.saved)/std::max(std::abs(c.saved),1e-280));for(auto&i:legal)m[i].confidence=alpha_native(m[i].omega);calc.settings.sourceDiscriminationPower=.2;double q=calc.sourceProbFromMaps(measured,c.hit);
   for(int x=c.x;x<c.x+c.sx;++x)for(int y=c.y;y<c.y+c.sy;++y){official.sourceProbability[x+nx*y]=q;paper.sourceProbability[x+nx*y]=p;}}
  Utils::NormalizeDistribution(Grid2D<double>{official.sourceProbability,official.occupancy,official.gridMetadata});Utils::NormalizeDistribution(Grid2D<double>{paper.sourceProbability,paper.occupancy,paper.gridMetadata});double sum=0,maxdiff=0;for(int i:legal){sum+=official.sourceProbability[i];maxdiff=std::max(maxdiff,std::abs(paper.sourceProbability[i]-reference[i]));}if(std::abs(sum-1)>1e-12||maxrel>1e-10||maxdiff>1e-10)return 8;
  auto top=official.expectedValueSource(.05),mean=official.expectedValueSource(1);std::cout<<g<<','<<nc<<','<<maxrel<<','<<sum<<','<<official.varianceSourcePosition()<<','<<std::hypot(top.x-truthx,top.y-truthy)<<','<<std::hypot(mean.x-truthx,mean.y-truthy)<<','<<paper.varianceSourcePosition()<<','<<maxdiff<<'\\n';
 }
 return 0;
}catch(const std::exception&e){std::cerr<<e.what();return 9;}}
'''
(R/'host_cpp_core_check.cpp').write_text(head,encoding='utf-8',newline='\n')
(R/'CPP_EXTRACTION_PROVENANCE.json').write_text(json.dumps(dict(functions=parts,confidence_line=native_alpha,rectangular_only_replacement='j < gridMetadata.dimensions.x -> j < gridMetadata.dimensions.y',not_a_ROS_program=True),indent=2)+'\n',encoding='utf-8')
groups=[];index=[]
for role in ['EA18_A2_R01','EA18_A2_R02','EA18_B2_R01','EA18_B2_R02']:
 F=AUD/'cases'/role;rt=F/'runtime';rows=read(rt/'native_posterior_updates.csv');calls=read(rt/'native_candidate_maps.csv');blob=(rt/'native_candidate_maps.f32').read_bytes();meta=json.loads((F/'CASE_META.json').read_text(encoding='utf-8'));nav=json.loads((rt/'NAVIGATION_MAP_METADATA.json').read_text(encoding='utf-8'));nx=nav['width']//25;ny=nav['height']//25
 for u in sorted(set(int(x['update'])for x in rows)):
  rr=[x for x in rows if int(x['update'])==u];cc=[x for x in calls if int(x['update'])==u]
  data=struct.pack('<4i3f2d',nx,ny,len(rr),len(cc),nav['origin_x'],nav['origin_y'],nav['resolution']*25,*meta['source_xyz'][:2])
  for x in rr:data+=struct.pack('<2i3d',int(x['col']),int(x['row']),float(x['hit_log_odds']),float(x['hit_omega']),float(x['source_probability']))
  for c in cc:
   offset=int(c['offset_bytes']);n=int(c['count']);data+=struct.pack('<4idi',int(c['origin_x']),int(c['origin_y']),int(c['size_x']),int(c['size_y']),float(c['score']),n)+blob[offset:offset+4*n]
  index.append(dict(group=len(groups),role=role,case=meta['case'],update=u,candidate_calls=len(cc),source_history_identity='PMFS-P24-PAPER-FIRST_ONLY',score_identity='O24_FORMULAS_ON_FIXED_P24_HISTORY_NOT_O24_ROS_PERFORMANCE'));groups.append(data)
(R/'CPP_REPLAY_INPUT.bin').write_bytes(struct.pack('<Ii',0x1234abcd,len(groups))+b''.join(groups))
(R/'CPP_REPLAY_GROUPS.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(groups=len(groups),calls=sum(x['candidate_calls']for x in index),input_bytes=(R/'CPP_REPLAY_INPUT.bin').stat().st_size)))
