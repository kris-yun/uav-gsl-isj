from common_n import *
import csv,io,numpy as np,importlib.util
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,rs):
 with Path(p).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011');r=rows(D/'readout/PUBLIC_B_C7_0/QUERY_OUTPUT.csv');first=[a for a in r if a['query_id'].startswith('g0_')];illegal=[int(a['query_id'].split('_')[1]) for a in first if a['physical_free']!='1'];assert len(first)==447
plan=load(CORE/'FACTORIAL_CONTRACT.json');sources={j['candidate']:j['source_xyz'] for j in plan['jobs']};field=[];qs=[]
for c,xyz in sources.items():
 for name,z in [('source_height',-.5),('sensor_height',-.2)]:qs.append(dict(query_id=c+'_'+name,frame=int(first[0]['frame']),x=xyz[0],y=xyz[1],z=z))
out=D/'geometry_height_audit';out.mkdir(exist_ok=False);wc(out/'QUERIES.csv',qs)
code='''from pathlib import Path
import subprocess,os,json
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',LD_LIBRARY_PATH='/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/gaden_common/lib:/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/build/gaden_common/third_party/gaden_core/third_party/libbsc:/opt/ros/humble/lib')
p=subprocess.run(['/home/zyc/pmfs_m2_process_observation_20261010/query_native','/home/zyc/pmfs_b4_native_validation_20261009/derived_B4','/home/zyc/pmfs_m2_process_observation_20261010/realizations/C7_0/bank',DATA+'/geometry_height_audit/QUERIES.csv',DATA+'/geometry_height_audit/QUERY_OUTPUT.csv'],env=env,capture_output=True,text=True,timeout=30);assert p.returncode==0,p.stderr
print(json.dumps({'status':'PASS_READONLY_WIND_HEIGHT_QUERY','physical_generations':0,'native_candidate_forwards':0}))
'''.replace('DATA',repr(DATA))
receipt=json.loads(run_remote(code,'source_wind_height_readonly_diagnostic',45));wc(CORE/'SOURCE_WIND_HEIGHT_DIAGNOSTIC.csv',rows(out/'QUERY_OUTPUT.csv'))
rr=rows(out/'QUERY_OUTPUT.csv');assert all(r['physical_free']=='1' for r in rr if r['query_id'].endswith('source_height'))
indices=[int((np.float32(xyz[0])-np.float32(-7.55))/.25)+34*int((np.float32(xyz[1])-np.float32(-7.88))/.25) for xyz in sources.values()]
nativepoints=[]
for c in sources:
 q0=np.fromfile(D/f'point_scores/{c}_R01.f32',dtype='<f4');nativepoints.append((c,q0))
m=rows(D/'readout_scores/input_B4/input.csv');pr=np.array([1-1/(1+np.exp(float(r['logOdds']))) for r in m]);cf=np.array([float(r['confidence']) for r in m]);q={c:a for c,a in nativepoints};factor=np.log(1-.4*abs(pr-q['C7'])*cf)-np.log(1-.4*abs(pr-q['K2'])*cf)
dump(CORE/'GEOMETRY_SUPPORT_INTERSECTION.json',dict(native_scoring_free_cells=447,physically_free_at_sensor_height=447-len(illegal),nonfree_grid_indices=illegal,all_five_actual_sources_free_at_release_height=True,source_nav_indexes=dict(zip(sources,indices)),
 exact_point_B4_true_minus_K2_contribution_from_nonphysical_receptor_grid=float(factor[illegal].sum()),maximum_possible_single_cell_log_ratio=float(np.log(1/.6)),
 map_cells_are_inferred_not_actual_sensor_events=True,source_vs_receptor_supports_distinguished=True,original_support_not_changed=True,
 height_wind_scope='Read-only diagnostic of same CFD10 at-.5 and-.2; no alternate wind input forwarded to native model; not an intervention or new physical realization'))
print(json.dumps({'nonphysical_native_receptor_cells':illegal,'source_indexes':dict(zip(sources,indices)),'no_scoring_support_change':True}))
