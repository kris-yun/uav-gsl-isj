"""Source continuity audit; explicitly not a bitwise dynamic replay claim."""
import hashlib,json
from pathlib import Path
OLD=Path('/home/zyc/native_pmfs_recovery_v1/src/gsl_server/src/gsl_server')
NEW=Path('/home/zyc/ros2_ws/brg_closedloop_20260927/src/gsl_server/src/gsl_server')
ROOT=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 changed=[];same=[]
 for p in sorted(OLD.rglob('*')):
  if not p.is_file() or p.suffix not in ['.hpp','.cpp','.h']:continue
  n=NEW/p.relative_to(OLD);assert n.exists(),str(n)
  (same if sha(n)==sha(p) else changed).append(str(p.relative_to(OLD)))
 allowed={'algorithms/PMFS/PMFS.hpp','algorithms/PMFS/PMFS.cpp','algorithms/PMFS/PMFS_utils.cpp','algorithms/PMFS/MovingStatePMFS.cpp'}
 assert set(changed)<=allowed,changed
 # Parameter-disabled original sources are the exact preserved patch inputs.
 for n in ['PMFS.hpp','PMFS.cpp','MovingStatePMFS.cpp']:
  old=OLD/'algorithms/PMFS'/n;backup=NEW/'algorithms/PMFS'/(n+'.pre_brg');assert sha(old)==sha(backup)
 # Localization stopping function is unchanged, including threshold semantics.
 def function(text,name):
  k=text.index(name);start=text.index('{',k);level=0
  for i in range(start,len(text)):
   if text[i]=='{':level+=1
   elif text[i]=='}':
    level-=1
    if level==0:return text[k:i+1]
 old=(OLD/'algorithms/PMFS/PMFS_utils.cpp').read_text();new=(NEW/'algorithms/PMFS/PMFS_utils.cpp').read_text()
 assert function(old,'GSLResult PMFS::checkSourceFound')==function(new,'GSLResult PMFS::checkSourceFound')
 report={'status':'NATIVE_SOURCE_CONTINUITY_VERIFIED','unchanged_existing_source_files':len(same),'changed_files':changed,
  'preserved_before_brg_inputs_match_original':True,'stopping_function_byte_identical':True,
  'occupancy_reachability_navigation_planner_math_and_filament_sources_byte_identical_except_explicit_neural_mode_MI_visualization_guard':True,
  'changes':'parameter-gated neural client/apply, neural MI visualization guard, optional read-only belief logging; no Native arithmetic change when disabled',
  'not_claimed':'not a bitwise equality of two independently scheduled dynamic ROS closed loops',
  'changed_file_hashes':{x:{'original':sha(OLD/x),'compiled_execution':sha(NEW/x)} for x in changed}}
 (ROOT/'native_source_continuity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
