from pathlib import Path
import difflib,hashlib,json
R=Path(__file__).resolve().parent
rel=Path('src/gsl_server/algorithms/PMFS/PMFS_utils.cpp')
source=R/'source_runtime'/rel;before=source.read_text();old='for (int j = 0; j < gridMetadata.dimensions.x; j++)';new='for (int j = 0; j < gridMetadata.dimensions.y; j++)'
assert before.count(old)==2
after=before.replace(old,new)
(R/'patches/RECTANGULAR_READOUT_PMFS_utils.cpp.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='author_Sep18/'+rel.as_posix(),tofile='paper_all_free_cells/'+rel.as_posix())),encoding='utf-8')
source.write_text(after,encoding='utf-8',newline='\n')
def body(text,sig):
 i=text.index(sig);a=text.index('{',i);depth=0
 for j in range(a,len(text)):
  depth+=(text[j]=='{')-(text[j]=='}')
  if depth==0:return text[i:j+1]
 raise ValueError(sig)
functions=[body(before,'Vector2 PMFS::expectedValueSource('),body(before,'double PMFS::varianceSourcePosition(')]
prefix='''#include <algorithm>
#include <cmath>
#include <iostream>
#include <vector>
#include <iomanip>
struct Vector2 {float x=0,y=0;Vector2()=default;Vector2(double a,double b):x(a),y(b){}};
struct Vector2Int {int x=0,y=0;Vector2Int()=default;Vector2Int(int a,int b):x(a),y(b){}};
enum class Occupancy {Free};
struct Grid2DMetadata {Vector2Int dimensions{0,0};size_t indexOf(Vector2Int p)const{return p.x+p.y*dimensions.x;}Vector2 indexToCoordinates(int i,int j)const{return Vector2(i+.5,j+.5);}};
'''
def cls(namespace,fixed):
 code='\n'.join(functions)
 if fixed:code=code.replace(old,new)
 return 'namespace '+namespace+''' {
struct PMFS {Grid2DMetadata gridMetadata;std::vector<Occupancy>occupancy;std::vector<double>sourceProbability;
Vector2 expectedValueSource(double);double varianceSourcePosition();};
'''+code+'\n}\n'
main='''int main(){std::cout<<std::setprecision(17);fixed::PMFS b;native::PMFS a;
 a.gridMetadata.dimensions={3,5};a.occupancy.assign(15,Occupancy::Free);a.sourceProbability.assign(15,1./15);b.gridMetadata=a.gridMetadata;b.occupancy=a.occupancy;b.sourceProbability=a.sourceProbability;
 double nativeVariance=a.varianceSourcePosition(),fixedVariance=b.varianceSourcePosition();
 if(std::abs(nativeVariance-.8)>1e-12||std::abs(fixedVariance-8./3)>1e-12)return 1;
 for(Vector2Int d:{Vector2Int(5,3),Vector2Int(3,5),Vector2Int(4,4)}){fixed::PMFS p;p.gridMetadata.dimensions=d;p.occupancy.assign(d.x*d.y,Occupancy::Free);p.sourceProbability.assign(d.x*d.y,1./(d.x*d.y));auto m=p.expectedValueSource(1);double v=p.varianceSourcePosition();double target=(d.x*d.x+d.y*d.y-2)/12.;if(std::abs(m.x-d.x/2.)>1e-7||std::abs(m.y-d.y/2.)>1e-7||std::abs(v-target)>1e-12)return 2;}
 std::cout<<"{\\"status\\":\\"PASS\\",\\"native_3x5_variance\\":"<<nativeVariance<<",\\"correct_3x5_variance\\":"<<fixedVariance<<",\\"changed_loop_bounds\\":2}\\n";
}
'''
(R/'rectangular_probe.cpp').write_text(prefix+cls('native',False)+cls('fixed',True)+main,encoding='utf-8',newline='\n')
record=dict(status='RECTANGULAR_READOUT_FIX_PRECOMMITTED',author_before_sha256=hashlib.sha256(before.encode()).hexdigest(),runtime_after_sha256=hashlib.sha256(after.encode()).hexdigest(),changed_lines=2,affected_methods=['expectedValueSource','varianceSourcePosition'],reason='Native source has y-loop bounded by width. Paper full source-position probability moments require all legal cells. Fix domain iteration; no map cell/source/threshold changed.',new_ros_before_fix=0)
(R/'RECTANGULAR_FIX_PRECOMMIT.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
