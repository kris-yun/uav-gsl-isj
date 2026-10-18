from pathlib import Path
import ast,csv,datetime,difflib,hashlib,json,math,re,shutil,subprocess
R=Path(__file__).resolve().parent
OLD=R.parent/'PMFS_PAPER_FIRST_ROS_QUAL_20261017'
S='/mnt/hgfs/workspace/'+R.name
V='/home/zyc/ros2_ws/pmfs_early_declaration_20261018'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (R/'PRECOMMIT.json').exists()
source=R/'source_runtime';shutil.copytree(OLD/'source_runtime',source)
rel=Path('src/gsl_server/algorithms/PMFS/internal/Simulations.cpp')
p=source/rel;before=p.read_text();text=before
text=text.replace('#include <fstream>','#include <fstream>\n#include <atomic>\n#include <chrono>')
needle='    namespace NQA = Utils::NQA;';assert text.count(needle)==1
text=text.replace(needle,needle+'\n    static std::atomic<size_t> auditUpdate{0};')
needle='        Utils::Time::Stopwatch stopwatch;';assert text.count(needle)==1
text=text.replace(needle,needle+'\n        ++auditUpdate; // Passive identity for each source update; never used by the algorithm.')
needle='        result.sourceProb = sourceProbFromMaps(measuredHitProb, result.hitMap);';assert text.count(needle)==1
text=text.replace(needle,needle+'''
        // Capture the exact maps already computed by the native forward model.
        // No random draws, parameters, source choices, or score values change.
        if (const char* base = std::getenv("NATIVE_PMFS_CANDIDATE_AUDIT")) {
            #pragma omp critical(native_passive_candidate_audit)
            {
                static std::ofstream maps(std::string(base)+".f32",std::ios::binary);
                static std::ofstream rows(std::string(base)+".csv");
                static size_t call=0;
                if(call==0) rows<<"update,call,origin_x,origin_y,size_x,size_y,score,offset_bytes,count\\n";
                const auto offset=maps.tellp();
                maps.write(reinterpret_cast<const char*>(result.hitMap.data()),result.hitMap.size()*sizeof(float));
                rows<<std::setprecision(17)<<auditUpdate.load()<<","<<++call<<","<<node->origin.x<<","<<node->origin.y<<","<<node->size.x<<","<<node->size.y<<","<<result.sourceProb<<","<<offset<<","<<result.hitMap.size()<<"\\n";
                maps.flush();rows.flush();
            }
        }
''')
p.write_text(text,encoding='utf-8',newline='\n')
(R/'PASSIVE_CANDIDATE_CAPTURE.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),text.splitlines(True),fromfile='qualified_20261017/'+rel.as_posix(),tofile='passive_audit_20261018/'+rel.as_posix())),encoding='utf-8')
oldBuild=json.loads((OLD/'BUILD_RESULT.json').read_text())
roles=[]
for case,template in [('A2','PF24_A2_T02'),('B2','PF24_B2_Q01')]:
 for repeat in [1,2]:
  rid=f'EA18_{case}_R{repeat:02d}';domain=219+len(roles)
  dst=R/'cases'/rid;dst.mkdir(parents=True)
  old=OLD/'cases'/template
  oldT='/home/zyc/ros2_ws/pmfs_paper_first_qual_20261017/cases/'+template
  oldRuntime='/mnt/hgfs/workspace/'+OLD.name+'/cases/'+template+'/runtime'
  T=V+'/cases/'+rid;runtime=S+'/cases/'+rid+'/runtime'
  meta=json.loads((old/'CASE_META.json').read_text());meta['ROS_DOMAIN_ID']=domain
  meta['audit_setting']['id']=rid;meta['expected_parameters_unchanged_from_previous']=True
  meta['frozen_repeat']=repeat
  meta['player']['r7_frame_time_csv']=T+'/AUTHOR_WALL_FILE_CADENCE.csv';meta['player']['r7_clock_trace_path']=runtime+'/physical_clock_trace.csv'
  meta['source_support_policy']='Pinned official map and all-pixels-free rule unchanged; B2 excluded source explicitly retained, not repaired by opening map or moving truth.'
  meta['actual_binary_sha256']='TO_BE_BOUND_AFTER_BUILD_BEFORE_RUN'
  put(dst/'CASE_META.json',meta)
  for name in ['N1_launch.py','runtime_driver.py','RUN_SHELL.sh','AUTHOR_WALL_FILE_CADENCE.csv']:
   t=(old/name).read_text().replace(oldT,T).replace(oldRuntime,runtime).replace(template,rid)
   t=t.replace(oldBuild['binary'],V+'/gsl_actionserver_node')
   previousDomain=227 if case=='A2'else 228
   t=t.replace('ROS_DOMAIN_ID='+str(previousDomain),'ROS_DOMAIN_ID='+str(domain)).replace("ROS_DOMAIN_ID='"+str(previousDomain)+"'","ROS_DOMAIN_ID='"+str(domain)+"'").replace('ROS_DOMAIN_ID='+str(previousDomain),'ROS_DOMAIN_ID='+str(domain))
   if name=='runtime_driver.py':
    needle="os.environ['NATIVE_PMFS_POSTERIOR_TRACE']=str(R/'native_posterior_updates.csv')";assert needle in t
    t=t.replace(needle,needle+"\nos.environ['NATIVE_PMFS_CANDIDATE_AUDIT']=str(R/'native_candidate_maps')")
   (dst/name).write_text(t,encoding='utf-8',newline='\n')
   if name.endswith('.py'):ast.parse(t)
  roles.append(dict(id=rid,case=case,repeat=repeat,domain=domain,guest_path=T,runtime_shared=runtime))
# Frozen before outcomes: not a search over clocks, thresholds, seeds, source locations, or scoring parameters.
plan=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Audit premature variance declarations and two bounded repeats per A2/B2',roles=roles,primary_goals=4,technical_retry_cap=2,total_goal_cap=6,max_goal_wall_s=420,total_batch_wall_s=2100,native_wall_cutoff_s=300,guest_free_floor_bytes=5*2**30,host_free_floor_bytes=2*2**30,new_worlds=0,AIMMD=0,parameters=json.loads((OLD/'RUN_PRECOMMIT.json').read_text())['parameters'],clock='Retain official launch mixed wall/5x clock; report wall, robot-clock and gas-file age separately',source_support='Do not open B2 source cell or move the source. Official configuration compatibility is tested separately from distance error.',offline_controls=['same sampled candidate maps: paper-square alpha / code-linear alpha crossed with paper D=1 / official D=0.2','fixed actual native refinement tree: offline controls are not new complete counterfactual closed loops'],stop='No retries for scientific bad error, early declaration or native nondeclaration; preserve all such outcomes',source_input_manifest=[dict(path=p.relative_to(source).as_posix(),sha256=sha(p))for p in sorted(source.rglob('*'))if p.is_file()])
put(R/'PRECOMMIT.json',plan)
print(json.dumps(dict(status='FROZEN',roles=roles,source_files=len(plan['source_input_manifest']))))
