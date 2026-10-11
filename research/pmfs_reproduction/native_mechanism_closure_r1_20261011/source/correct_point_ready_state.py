from common_n import *
import shutil,json,numpy as np,csv
D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011')
code='''from pathlib import Path
import os,json,subprocess,time
t=Path(REMOTE);d=Path(DATA);env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',LD_LIBRARY_PATH=json.loads((t/'ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH']);out=d/'point_corrected_results';out.mkdir()
rr=[]
for c in ['C7','K2','B000','B001','B002']:
 inp=d/'point_corrected_inputs/R0';start=time.time();p=subprocess.run(['/dev/shm/nmc_cold/native_cold_entry','point_forward',str(inp),str(inp/(c+'.csv')),str(out/(c+'_R0'))],env=env,capture_output=True,text=True,timeout=60);assert p.returncode==0,p.stderr;rr.append({'candidate':c,'wall_s':time.time()-start,'ready_index':19,'forward_calls':1})
print(json.dumps({'status':'PASS_CORRECTED_POINT_READY_STATE','records':rr,'new_forward_calls':5}))
'''.replace('REMOTE',repr(REMOTE)).replace('DATA',repr(DATA))
r=json.loads(run_remote(code,'corrected_point_first_ready_cache_state',120));dump(CORE/'POINT_READY_STATE_CORRECTION_EXECUTION.json',r)
for c in ['C7','K2','B000','B001','B002']:
 shutil.copytree(D/f'point_results/{c}_R1',D/f'point_corrected_results/{c}_R1')
src=(WORK/'analyze_point_diagnostic.py').read_text().replace("out=D/'point_scores'","out=D/'point_corrected_scores'").replace("point_results/{c}","point_corrected_results/{c}").replace("DATA+'/point_scores/","DATA+'/point_corrected_scores/").replace("'point_native_similarity_all_observations'","'point_corrected_similarity_all_observations'").replace("CORE/'N_POINT_", "CORE/'QUALIFIED_N_POINT_")
(WORK/'analyze_corrected_point.py').write_text(src,encoding='utf-8');p=subprocess.run([sys.executable,'-B','-X','utf8',str(WORK/'analyze_corrected_point.py')],capture_output=True,text=True);assert p.returncode==0,p.stderr;print(p.stdout)
