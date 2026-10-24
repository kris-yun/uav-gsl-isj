"""Final-snapshot diagnostics on all seven source-legal SCREEN12 runs, no forward calls."""
from pathlib import Path,PureWindowsPath
import bisect,csv,hashlib,io,json,zipfile,os,contextlib
import numpy as np
B=Path(__file__).resolve().parent
ARCHIVE=Path('C:/Users/50176/Downloads/O24_SCREEN12_COMBINED_FINAL_FULL_EVIDENCE_20261024.zip')
LOCAL_REFS=Path(os.environ['V11_NATIVE_REFERENCE_RUNS']) if 'V11_NATIVE_REFERENCE_RUNS' in os.environ else None
if LOCAL_REFS is None:assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()=='553ed6d0d3de761d2e2a13fff2b2fd1e205271bdce0e6bd75414fb1a24ac6ee3'
OUT=Path(os.environ.get('V11_CONTROL_OUTPUT',str(B/'correct_case_controls')));assert not OUT.exists();OUT.mkdir()
source=Path(os.environ.get('V11_EPISODE_RESULTS','D:/ZYC/A-gas/workspace/O24_PAPER_SCREEN12_20261024/EPISODE_RESULTS.csv'))
episodes=list(csv.DictReader(source.open(encoding='utf-8-sig',newline='')))
def csv_bytes(x):return list(csv.DictReader(io.StringIO(x.decode())))
summary=[]
class LocalReferences:
 def read(self,member):return (LOCAL_REFS/Path(member).name).read_bytes()
with (contextlib.nullcontext(LocalReferences()) if LOCAL_REFS is not None else zipfile.ZipFile(ARCHIVE)) as outer:
 for ep in episodes:
  if ep['source_domain']!='LEGAL':continue
  role=ep['role'];member='full_runs/'+PureWindowsPath(ep['archive']).name
  payload=outer.read(member)
  with zipfile.ZipFile(io.BytesIO(payload)) as z:
   meta=json.loads(z.read('CASE_META.json'));nav=json.loads(z.read('runtime/NAVIGATION_MAP_METADATA.json'))
   raw=json.loads(z.read('runtime/resolved_GSL_parameters.json'));par={k:v[{1:'bool_value',2:'integer_value',3:'double_value',4:'string_value'}[v['type']]] for k,v in zip(raw['names'],raw['values'])}
   allpost=csv_bytes(z.read('runtime/native_posterior_updates.csv'));update=max(int(x['update']) for x in allpost);post=[x for x in allpost if int(x['update'])==update]
   nx=nav['width']//par['scale'];ny=nav['height']//par['scale'];cs=float(post[0]['cell_size_m'])
   idx=np.array([int(x['col'])+nx*int(x['row']) for x in post]);pidx={x:i for i,x in enumerate(idx)}
   truth=meta['source_xyz'][:2];tf=int((truth[0]-nav['origin_x'])/cs)+nx*int((truth[1]-nav['origin_y'])/cs);assert tf in pidx
   saved=np.array([float(x['source_probability']) for x in post]);mp=int(idx[np.argmax(saved)])
   m=1-1/(1+np.exp([float(x['hit_log_odds']) for x in post]));alpha=np.array([float(x['hit_confidence']) for x in post]);D=par['sourceDiscriminationPower']
   candidates=[x for x in csv_bytes(z.read('runtime/native_candidate_maps.csv')) if int(x['update'])==update];candidates.sort(key=lambda x:(-int(x['size_x'])*int(x['size_y']),int(x['call'])))
   data=z.read('runtime/native_candidate_maps.f32');owner=np.full(nx*ny,-1);unnorm=np.zeros(nx*ny);fm=[];score_errors=[]
   for j,c in enumerate(candidates):
    a=np.frombuffer(data,dtype='<f4',count=int(c['count']),offset=int(c['offset_bytes'])).astype(float);fm.append(a)
    score=np.prod(1+((1-D*np.abs(m-a[idx]))-1)*alpha);score_errors.append(abs(score-float(c['score']))/max(abs(float(c['score'])),1e-280))
    x,y,sx,sy=(int(c[k]) for k in ['origin_x','origin_y','size_x','size_y']);owner.reshape(ny,nx)[y:y+sy,x:x+sx]=j;unnorm.reshape(ny,nx)[y:y+sy,x:x+sx]=score
   p=unnorm[idx]/unnorm[idx].sum();posterr=float(np.max(abs(p-saved)));assert max(score_errors)<1e-10 and posterr<1e-10,role
   ti,mi=int(owner[tf]),int(owner[mp]);ft,fw=fm[ti],fm[mi]
   path=json.loads(z.read('runtime/robot_path.json'));times=[r[0] for r in path]
   windows=[x for x in csv_bytes(z.read('runtime/native_window_consumption.csv')) if x['status']=='CONSUMED'];observed=[];cell_indices=[]
   for w in windows:
    pose=path[max(0,bisect.bisect_right(times,int(w['node_clock_ns'])*1e-9)-1)];col=int((pose[1]-nav['origin_x'])/cs);row=int((pose[2]-nav['origin_y'])/cs);k=col+nx*row
    cell_indices.append(k);observed.append({'event':w['event'],'cell_col':col,'cell_row':row,'concentration_mean_ppm':float(w['concentration_mean_ppm']),'actual_hit':float(w['concentration_mean_ppm'])>par['th_gas_present'],'true_region_frequency':ft[k],'map_region_frequency':fw[k]})
   obs=np.array([x['actual_hit'] for x in observed]);freq=np.array([x['true_region_frequency'] for x in observed]);wf=np.array([x['map_region_frequency'] for x in observed]);actual=np.isin(idx,cell_indices)
   delta=np.log(1-D*np.abs(m-fw[idx])*alpha)-np.log(1-D*np.abs(m-ft[idx])*alpha)
   record={'role':role,'case':ep['case'],'scope':'Saved final source table against historical windows; not time-matched PID likelihood.','official_success':ep['official_success'],'stop_reason':ep['stop_reason'],'source_domain':ep['source_domain'],'Top5_error_m':float(ep['Top5_error_m']),'true_rank_native':int(ep['true_rank']),'true_responsible_call':int(candidates[ti]['call']),'true_region_size':[int(candidates[ti]['size_x']),int(candidates[ti]['size_y'])],'positive_windows':int(obs.sum()),'total_windows':len(windows),'positive_windows_true_region_zero':int(np.sum(obs&(freq==0))),'positive_windows_true_region_zero_MAP_nonzero':int(np.sum(obs&(freq==0)&(wf>0))),'native_MAP_over_true_score_ratio':float(unnorm[mp]/unnorm[tf]),'score_replay_max_relative_error':max(score_errors),'posterior_replay_max_abs_error':posterr,'visited_cells_loggap':float(delta[actual].sum()),'unvisited_cells_loggap':float(delta[~actual].sum()),'correctness_label':'source-legal diagnostic; native declaration is not positional success'}
   summary.append(record)
   run=OUT/role;run.mkdir();(run/'SUMMARY.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
   with (run/'WINDOW_RESPONSE_COMPARISON.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=observed[0]);w.writeheader();w.writerows(observed)
   (run/'NATIVE_RESPONSE_TABLE_BINDING.json').write_text(json.dumps({'archive_member':member,'archive_sha256':hashlib.sha256(payload).hexdigest(),'native_update':update,'input_hashes':{n:hashlib.sha256(z.read(n)).hexdigest() for n in ['runtime/native_candidate_maps.csv','runtime/native_candidate_maps.f32','runtime/native_posterior_updates.csv','runtime/native_window_consumption.csv']}},indent=2)+'\n',encoding='utf-8')
(OUT/'ALL_SOURCE_LEGAL_CONTROL_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (OUT/'ALL_SOURCE_LEGAL_CONTROL_SUMMARY.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=summary[0]);w.writeheader();w.writerows(summary)
for r in summary:print(json.dumps({k:r[k] for k in ['role','true_region_size','positive_windows','positive_windows_true_region_zero','native_MAP_over_true_score_ratio','Top5_error_m']},ensure_ascii=False))
