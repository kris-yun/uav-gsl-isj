"""One explicitly labelled post-hoc exact-coordinate oracle, as permitted by the user contract."""
from pathlib import Path
import json,shutil,subprocess,os,time,resource,csv,hashlib,sys
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA';plan=json.loads((R/'FROZEN_PLAN.json').read_text())
def prepare_oracle():
    assert (R/'results/CONTRASTS_COMPLETE.json').exists();assert not (R/'POSTHOC_ORACLE_PLAN.json').exists()
    oracle=dict(scope='Post-hoc attribution only; exact true xy permitted explicitly in the user C4 contract. No oracle posterior, task gain or deployed method claim.',
                sources=[dict(case=x['case'],epoch=x['epoch'],xy=x['truth'][:2]) for x in plan['cases']],
                states=plan['prediction_rng_states'],maximum_oracle_calls=9,additional_parity_calls=293,
                settings='The same captured per-case settings and native Point source mode; all physical kernels unchanged.',
                stopping='Exactly these coordinates and states once; no finer search, seed choice, noise fit or further source changes.')
    (R/'POSTHOC_ORACLE_PLAN.json').write_text(json.dumps(oracle,indent=2))
    O=R/'oracle_code';shutil.copytree(R/'code',O)
    p=O/'support.hpp';s=p.read_text();needle=' Vector2 getPoint()const;';assert s.count(needle)==1
    s=s.replace(needle,' SimulationSource(const Vector2&p,const Grid2DMetadata&m):mode(Point),nqaNode(nullptr),point(p),metadata(m){}\n'+needle);p.write_text(s)
    p=O/'native_forward.cpp';s=p.read_text();needle='    Vector2 SimulationSource::getPoint() const\n    {';assert s.count(needle)==1
    s=s.replace('++diag::releases; return diag::source_point(randP);','return diag::source_point(randP);').replace(needle,needle+' ++diag::releases;');p.write_text(s)
    p=O/'forward.cpp';s=p.read_text();s=s.replace('if(argc!=7)','if(argc!=7 && argc!=9)')
    needle=' if(mode=="parity"){jobs=candidates;}';assert needle in s
    s=s.replace(needle,' if(mode=="point"){if(argc!=9)throw std::runtime_error("Point mode needs exact xy");auto ij=m.coordinatesToIndices(std::stof(argv[7]),std::stof(argv[8]));GSL_ASSERT(m.indicesInBounds(ij)&&occ[m.indexOf(ij)]==Occupancy::Free);Row r{{"candidate_id","oracle_true"},{"parent_id","oracle_true"},{"origin_i",std::to_string(ij.x)},{"origin_j",std::to_string(ij.y)},{"size_i","1"},{"size_j","1"}};jobs.push_back(r);}\n else '+needle.lstrip())
    needle='SimulationSource source(&node,m);';assert s.count(needle)==1
    s=s.replace(needle,'SimulationSource source=mode=="point"?SimulationSource(Vector2(std::stof(argv[7]),std::stof(argv[8])),m):SimulationSource(&node,m);');p.write_text(s)
    (R/'lineage/ORACLE_BUILD_INPUT_SHA256.json').write_text(json.dumps({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in O.rglob('*') if p.is_file()},indent=2))

if '--resume' not in sys.argv:prepare_oracle()
else:assert (R/'POSTHOC_ORACLE_PLAN.json').exists()
O=R/'oracle_code'
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1');ledger=json.loads((R/'ORACLE_EXECUTION.json').read_text()) if '--resume' in sys.argv else []
def run(cmd,tag):
 if (R/f'logs/{tag}.stdout').exists():tag+='_compile_retry1'
 start=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
 with (R/f'logs/{tag}.stdout').open('w') as out,(R/f'logs/{tag}.stderr').open('w') as err:q=subprocess.run(cmd,env=env,stdout=out,stderr=err,timeout=120)
 after=resource.getrusage(resource.RUSAGE_CHILDREN);ledger.append(dict(command=cmd,exit_code=q.returncode,wall_s=time.monotonic()-start,cpu_user_s=after.ru_utime-before.ru_utime,cpu_system_s=after.ru_stime-before.ru_stime));(R/'ORACLE_EXECUTION.json').write_text(json.dumps(ledger,indent=2));print(tag,q.returncode,flush=True);assert q.returncode==0
build=Path('/tmp/c4a17_oracle_build');run(['cmake','-S',str(O),'-B',str(build)],'oracle_configure');run(['cmake','--build',str(build),'-j2'],'oracle_build')
parity=[];responses=[];costs=[]
for item in plan['cases']:
 case,ep=item['case'],item['epoch'];key=f'{case}_update_{ep}';native=P/f'cases/{case}/native_execution/runtime/updates/update_{ep}';dest=R/'results/oracle_parity'/key
 run([str(build/'forward'),'parity',str(R/'inputs'/key),str(native),str(dest),'0',key],'oracle_parity_'+key)
 for p in (dest/'maps').iterdir():assert p.read_bytes()==(native/'maps'/p.name).read_bytes(),p.name
 parity.append(dict(case=case,epoch=ep,maps_byte_identical=len(list((dest/'maps').iterdir()))))
 ev=np.loadtxt(R/f'inputs/{case}_measurement_events.csv',delimiter=',',ndmin=2);ev=ev[ev[:,0]<=item['metadata']['stamp_ns']];m=item['metadata']
 for seed in plan['prediction_rng_states']:
  dest=R/'results/oracle'/f'{key}_{seed}';xy=item['truth'][:2]
  run([str(build/'forward'),'point',str(R/'inputs'/key),str(native),str(dest),str(seed),key,*map(str,xy)],f'oracle_{key}_{seed}')
  score=list(csv.DictReader((dest/'scores.csv').open()))[0];costs.append(dict(case=case,epoch=ep,prediction_state=seed,**score))
  raw=np.fromfile(dest/'maps/oracle_true_unblurred.f32','<f4');blur=np.fromfile(dest/'maps/oracle_true.f32','<f4')
  for stop in np.unique(ev[:,6]).astype(int):
   a=ev[ev[:,6]==stop];x,y=a[-1,4:6];i=int((np.float32(x)-np.float32(m['origin_x']))/np.float32(m['cell_size']));j=int((np.float32(y)-np.float32(m['origin_y']))/np.float32(m['cell_size']));k=i+j*m['width']
   responses.append(dict(case=case,epoch=ep,prediction_state=seed,stop=int(stop),true_source_exact_x=xy[0],true_source_exact_y=xy[1],consumed_hit_fraction=float(np.mean(a[:,1]>.1)),oracle_raw_frequency=float(raw[k]),oracle_blurred_frequency=float(blur[k]),oracle_logscore=float(score['logscore']),interpretation='POSTHOC_ORACLE_ONLY_NOT_AN_ALGORITHM_OR_CLOSED_LOOP_GAIN'))
for name,data in [('ORACLE_EXACT_POINT_RESPONSES.csv',responses),('ORACLE_COSTS.csv',costs)]:
 with (R/'results'/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
(R/'results/ORACLE_PARITY_PASS.json').write_text(json.dumps(parity,indent=2));print('PASS exact-coordinate oracle; no posterior or task benefit claim',flush=True)
