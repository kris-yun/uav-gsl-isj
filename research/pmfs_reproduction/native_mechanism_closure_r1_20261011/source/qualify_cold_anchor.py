from common_n import *
import csv,numpy as np
D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011')
code='''from pathlib import Path
import subprocess,os,json
t=Path(REMOTE);d=Path(DATA);env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',LD_LIBRARY_PATH=json.loads((t/'ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH'])
p=subprocess.run(['/dev/shm/nmc_cold/native_cold_entry','anchor_forward',str(d/'cold_inputs/B4_FIRST'),str(d/'cold_inputs/B4_FIRST/anchor_job.csv'),str(d/'cold_FIRST_OFF')],env=env,capture_output=True,text=True,timeout=60);assert p.returncode==0,p.stderr
print(json.dumps({'status':'EXECUTED_NATIVE_COLD_FIRST_CANDIDATE','new_forward_calls':1}))
'''.replace('REMOTE',repr(REMOTE)).replace('DATA',repr(DATA))
r=json.loads(run_remote(code,'native_cold_first_OFF_qualification',90))
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
old=BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010/runtime/updates/update_0';a=rows(old/'candidates.csv')[0];folder=D/'cold_FIRST_OFF/forward';b=rows(folder/'candidates.csv')[0]
proof=dict(new_forward_calls=1,map_difference=float(np.max(np.abs(np.fromfile(old/a['map_file'],dtype='<f4')-np.fromfile(folder/b['map_file'],dtype='<f4')))),
 point_difference=float(np.max(np.abs(np.fromfile(old/a['points_file'],dtype='<f4')-np.fromfile(folder/b['points_file'],dtype='<f4')))),cache_equal=sha(old/'gaussian_cache.f32')==sha(folder/'gaussian_cache.f32'),gaussian_initial_equal=(old/'gaussian_initial.csv').read_bytes()==(folder/'gaussian_initial.csv').read_bytes(),
 captured_fields_equal={k:a[k]==b[k] for k in ['rng_before','rng_after','gaussian_ready_before','gaussian_index_before','gaussian_index_after','point_count','score','logscore']})
proof['status']='PASS_TRUE_COLD_FIRST_NATIVE_ANCHOR' if proof['map_difference']==0 and proof['point_difference']==0 and proof['cache_equal'] and proof['gaussian_initial_equal'] and all(proof['captured_fields_equal'].values()) else 'FAIL_COLD_RESTORE'
dump(CORE/'COLD_FIRST_ANCHOR.json',proof);print(json.dumps(proof));assert proof['status'].startswith('PASS')
