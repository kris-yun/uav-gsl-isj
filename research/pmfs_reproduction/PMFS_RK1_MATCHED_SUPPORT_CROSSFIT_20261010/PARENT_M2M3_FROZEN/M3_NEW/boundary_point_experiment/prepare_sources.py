import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,csv,io
W=Path(__file__).resolve().parent;ROOT=W.parents[2]
old=ROOT/'work/pmfs_b4_m1'
source=(old/'Simulations_native_with_state_access.cpp').read_text(encoding='utf-8')
source=source.replace('#include "Audit.hpp"','#include "Audit.hpp"\n#include "M3Audit.hpp"',1)
source=source.replace('        Vector2 newPos = filament.position + deltaTime * velocity;\n        moveAlongPath(filament.position, newPos);', '''        Vector2 newPos = filament.position + deltaTime * velocity;
        const Vector2 before = filament.position;
        const uint64_t blockedBefore = M3Audit::blocked;
        moveAlongPath(filament.position, newPos);
        const auto afterIndices=measuredHitProb.metadata.coordinatesToIndices(filament.position.x,filament.position.y);
        M3Audit::movement(before,filament.position,indices,afterIndices,blockedBefore);''')
source=source.replace('            bool stable = false;','            M3Audit::phase=0;\n            bool stable = false;',1)
source=source.replace('        for (int t = 1; t < timesteps + 1; t++)','        M3Audit::phase=1;\n        for (int t = 1; t < timesteps + 1; t++)',1)
source=source.replace('        if (mode == Mode::Point)\n            return point;','        if (mode == Mode::Point) {R4Audit::point(point);return point;}',1)
source=source.replace('            return false;\n        }\n\n        // try to avoid', '            M3Audit::originBlocked++;\n            return false;\n        }\n\n        // try to avoid',1)
source=source.replace('            currentPosition = end;\n            return true;', '            M3Audit::visibilityFast++;\n            currentPosition = end;\n            return true;',1)
original='''            if (!pathIsFree)
                currentPosition -= increment;'''
replacement='''            if (!pathIsFree) {
                const Vector2Int blockedCell=pair;
                currentPosition -= increment;
                M3Audit::blocked++;
                if(M3Audit::wallSlide) {
                    const auto previousCell=metadata.coordinatesToIndices(currentPosition.x,currentPosition.y);
                    Vector2 normal(float(previousCell.x-blockedCell.x),float(previousCell.y-blockedCell.y));
                    const float denominator=normal.x*normal.x+normal.y*normal.y;
                    if(denominator>0) {
                        Vector2 remaining=end-currentPosition;
                        const float projection=(remaining.x*normal.x+remaining.y*normal.y)/denominator;
                        Vector2 rejected=remaining-normal*projection;
                        M3Audit::slideAttempts++;
                        if(rejected.x!=0||rejected.y!=0) {
                            M3Audit::slideNonzero++;
                            if(M3Audit::depth>=32){M3Audit::guardHits++;return false;}
                            M3Audit::depth++;
                            bool result=moveAlongPath(currentPosition,currentPosition+rejected);
                            M3Audit::depth--;
                            return result;
                        }
                    }
                }
            }'''
assert original in source;source=source.replace(original,replacement,1)
(W/'Simulations_boundary_diagnostic.cpp').write_text(source,encoding='utf-8',newline='\n')
entry=(old/'m1_candidate_forward.cpp').read_text(encoding='utf-8')
entry=entry.replace('#include "Fixture.hpp"','#include "Fixture.hpp"\n#include "M3Audit.hpp"',1)
entry=entry.replace('long double one(const Utils::NQA::Node& node, const fs::path& output)', 'long double one(const Utils::NQA::Node& node, const fs::path& output,bool pointMode,Vector2 exactPoint)')
entry=entry.replace('        SimulationSource source(&node,measuredHitProb.metadata);','        SimulationSource source=pointMode?SimulationSource(exactPoint,measuredHitProb.metadata):SimulationSource(&node,measuredHitProb.metadata);',1)
entry=entry.replace('        return score;\n    }','        M3Audit::finish(output);\n        return score;\n    }',1)
entry=entry.replace('    const long double score=simulation.one(node,output);','''    const bool pointMode=job.at("source_form")=="point";
    if(!(pointMode||job.at("source_form")=="uniform"))throw std::runtime_error("source form");
    M3Audit::wallSlide=job.at("boundary")=="slide";
    if(!(M3Audit::wallSlide||job.at("boundary")=="native"))throw std::runtime_error("boundary form");
    Vector2 exactPoint(float(checkedDouble(job,"point_x")),float(checkedDouble(job,"point_y")));
    if(pointMode && !measured[0].probability()){} // no state mutation
    const long double score=simulation.one(node,output,pointMode,exactPoint);''')
entry=entry.replace('    if(pointMode && !measured[0].probability()){} // no state mutation\n','')
entry=entry.replace('        <<",\\\"release_points\\\":"<<R4Audit::point_count', '        <<",\\\"source_form\\\":\\\""<<job.at("source_form")<<"\\\",\\\"boundary\\\":\\\""<<job.at("boundary")<<"\\\",\\\"exact_point\\\":["<<exactPoint.x<<","<<exactPoint.y<<"]"\n        <<",\\\"release_points\\\":"<<R4Audit::point_count')
(W/'candidate_forward.cpp').write_text(entry,encoding='utf-8',newline='\n')
jobs=[]
for bundle,rng,phase in [('T','1122849406',5),('W','53064653',2425)]:
 for candidate,ij,p in [('C7',(17,18),(-3.2,-3.3)),('K2',(23,37),(-1.675,1.495))]:
  for form,boundary in [('point','native'),('uniform','slide'),('point','slide')]:
   jobs.append(dict(job=f'{bundle}_{candidate}_{form}_{boundary}',bundle=bundle,candidate=candidate,origin_i=ij[0],origin_j=ij[1],size_i=1,size_j=1,rng_before=rng,gaussian_index_before=phase,source_form=form,boundary=boundary,point_x=p[0],point_y=p[1],is_anchor=False))
anchors=[]
for bundle,candidate,ij,rng,phase,expected in [('T','C7',(17,18),'1122849406',5,'T_true_fine'),('W','K2',(23,37),'53064653',2425,'anchor_W_fine')]:
 anchors.append(dict(job=f'anchor_{bundle}_{candidate}',bundle=bundle,candidate=candidate,origin_i=ij[0],origin_j=ij[1],size_i=1,size_j=1,rng_before=rng,gaussian_index_before=phase,source_form='uniform',boundary='native',point_x=0,point_y=0,is_anchor=True,expected_M1_job=expected))
jobdir=W/'jobs';jobdir.mkdir(exist_ok=True)
for job in anchors+jobs:
 fields=[x for x in job if x not in ('is_anchor','expected_M1_job')];s=io.StringIO();w=csv.DictWriter(s,fields,lineterminator='\n');w.writeheader();w.writerow({k:job[k] for k in fields});(jobdir/(job['job']+'.csv')).write_text(s.getvalue(),encoding='utf-8')
contract=dict(scope='POSTHOC_FIXED_TWO_CANDIDATE_2x2_DIAGNOSTIC_NOT_LOCALIZATION_PERFORMANCE',new_science_forward_calls=12,parity_anchor_calls=2,total_forward_cap=14,jobs=anchors+jobs,reused_native_uniform=[dict(bundle=b,candidate=c,job=j) for b,c,j in [('T','C7','T_true_fine'),('T','K2','T_wrong_fine'),('W','C7','W_true_fine'),('W','K2','anchor_W_fine')]],forward_wall_cap_s=120,forward_RSS_cap_bytes=536870912,build_wall_cap_s=180,build_RSS_cap_bytes=1610612736,disk_cap_bytes=200000000,single_thread=True,parameters_unchanged=True,old_inputs_unchanged=True,point_source_is_oracle=True,slide='GADEN-inspired 2D tangent projection only after native obstacle rollback; original floor traversal, fastpath and out-of-domain deletion retained; guard depth32 must remain zero',no_new_ros_gaden_cfd_navigation=True,source_sha256={name:hashlib.sha256((W/name).read_bytes()).hexdigest() for name in ['candidate_forward.cpp','Simulations_boundary_diagnostic.cpp','M3Audit.hpp']})
(W/'PREPARED_CONTRACT.json').write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8')
print(json.dumps(contract,indent=2))
