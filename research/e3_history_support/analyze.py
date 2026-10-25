"""Analyze the preregistered warmup intervention without further forward calls."""
from pathlib import Path
import csv,hashlib,json,math,os,struct
import numpy as np

B=Path('D:/ZYC/A-gas/workspace/METHOD_COMPARISON_O24_1M2_20261024')
O=Path(os.environ.get('E3_HISTORY_OUTPUT',str(B/'outputs/E3_HISTORY_SUPPORT_20261025')))
OLD=Path(os.environ.get('E3_PAIR_OUTPUT',str(B/'outputs/E3_CAUSAL_PAIR_20261025')))

def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n',encoding='utf8')
def table(p,data):
    with p.open('w',encoding='utf8',newline='') as f:w=csv.DictWriter(f,fieldnames=data[0]);w.writeheader();w.writerows(data)

def main():
    assert load(O/'EXECUTION_RECEIPT.json')['status'].startswith('PASS_')
    plan=load(O/'PREREGISTERED_HISTORY_CONTRACT.json');stages=[];native=[];rates=[];pair=[];particles=[]
    points=rows(O/'inputs/E3_UNIQUE_POINTS.csv');physical=[r for r in rows(OLD/'PHYSICAL_WINDOWS.csv') if r['group']=='historical']
    models={};npoints=len(points)
    for case in ['E3','A2']:
        for source in ['true','rival']:
            for pred in plan['prediction_streams']:
                for history in ['native','long220']:
                    prefix=O/'runs'/f'{case}_{source}_{pred["id"]}_{history}';record=load(prefix.with_suffix('.json'));h=record['history'];stages.append(dict(case=case,source=source,prediction=pred['id'],history=history,actual_warmup_s=h['actual_warmup_s'],first_exit_step=h['first_exit_step'],max_sigma_at_record_start_cm=h['max_sigma_cm_at_record_start'],native_full_map_score=record['score'],filament_moves=record['filament_moves']))
                    if case!='E3':continue
                    series=OLD/'event_control'/f'{source}_{pred["id"]}.timeseries.csv' if history=='native' else Path(str(prefix)+'.timeseries.csv')
                    data=rows(series);values=np.array([float(r['ppm']) for r in data]).reshape(200,npoints);freq=np.fromfile(prefix.with_suffix('.f32'),dtype='<f4');scene=load(O/'inputs/E3_scene.json')
                    for pid,point in enumerate(points):
                        x,y=float(point['x']),float(point['y']);ij=((np.array([x,y],np.float32)-np.array(scene['origin'],np.float32))/np.float32(scene['cell_size'])).astype(int);q=float(freq[ij[0]+scene['nx']*ij[1]])
                        for count in [3,4,5]:
                            v=values[:200//count*count,pid].reshape(-1,count).mean(1)
                            for arm,p in [('native_center',q),('PID_window',float((v>.1).mean()))]:
                                models[source,pred['id'],history,pid,count,arm]=p
                                rates.append(dict(source=source,prediction=pred['id'],history=history,point_id=pid,samples_per_window=count,arm=arm,predicted_hit=p,mean_ppm=float(values[:,pid].mean()),max_ppm=float(values[:,pid].max())))
                    trace=OLD/'event_control'/f'{source}_{pred["id"]}.particles.bin' if history=='native' else Path(str(prefix)+'.particles.bin')
                    oldest=10.;nearest={stop:1e30 for stop in range(8,14)};nearest_old=dict(nearest);num_old=0;num_total=0
                    target={stop:next(r for r in physical if int(r['stop'])==stop) for stop in range(8,14)}
                    with trace.open('rb') as stream:
                        while raw:=stream.read(8):
                            step,n=struct.unpack('<2I',raw);a=np.frombuffer(stream.read(n*16),dtype='<f4').reshape(n,4).astype(float);assert len(a)==n
                            oldest=max(oldest,float(a[:,2].max()));is_old=(a[:,2]**2-100)/15>100;num_old+=int(is_old.sum());num_total+=n
                            for stop in nearest:
                                pt=points[int(target[stop]['point_id'])];ds=np.sqrt((a[:,0]-float(pt['x']))**2+(a[:,1]-float(pt['y']))**2+(.7-float(pt['z']))**2)
                                nearest[stop]=min(nearest[stop],float(ds.min()))
                                if is_old.any():nearest_old[stop]=min(nearest_old[stop],float(ds[is_old].min()))
                    for stop in nearest:
                        r=target[stop];pid=int(r['point_id']);particles.append(dict(source=source,prediction=pred['id'],history=history,stop=stop,max_spread_equivalent_age_s=(oldest*oldest-100)/15,min_center_to_sensor_m=nearest[stop],min_old100s_center_to_sensor_m=nearest_old[stop] if nearest_old[stop]<1e29 else None,old100s_particle_time_fraction=num_old/num_total,center_hit=models[source,pred['id'],history,pid,int(r['samples']),'native_center'],PID_window_hit=models[source,pred['id'],history,pid,int(r['samples']),'PID_window']))
    for case in ['E3','A2']:
        for pred in plan['prediction_streams']:
            for history in ['native','long220']:
                rec={h:load((O/'runs'/f'{case}_{h}_{pred["id"]}_{history}').with_suffix('.json')) for h in ['true','rival']}
                delta=math.log(rec['true']['score'])-math.log(rec['rival']['score']);native.append(dict(case=case,prediction=pred['id'],history=history,true_minus_rival_log_native_full_map_score=delta,true_over_rival_native_full_map_score=math.exp(delta),pair_preference='true' if delta>0 else 'rival',full_domain_new_posterior=False))
    for world in ['true_r0','true_r1','rival_r0','rival_r1']:
        obs=[r for r in physical if r['world']==world];actual=world.split('_')[0]
        for pred in plan['prediction_streams']:
            for history in ['native','long220']:
                for scope,valid in [('whole13',set(range(1,14))),('critical8to13',set(range(8,14)))]:
                    selected=[r for r in obs if int(r['stop']) in valid]
                    for arm in ['native_center','PID_window']:
                        scores={s:0. for s in ['true','rival']};brier=dict(scores)
                        for r in selected:
                            for source in scores:
                                q=models[source,pred['id'],history,int(r['point_id']),int(r['samples']),arm];y=int(r['hit']);scores[source]+=math.log(1-.2*abs(y-q))/5;brier[source]+=(y-q)**2/len(selected)
                        delta=scores['true']-scores['rival'];chosen='true' if delta>1e-12 else 'rival' if delta< -1e-12 else 'tie'
                        pair.append(dict(world=world,actual_source=actual,prediction=pred['id'],history=history,scope=scope,arm=arm,true_minus_rival_log_compatibility=delta,true_over_rival_compatibility_ratio=math.exp(delta),pair_MAP=chosen,actual_source_pair_rank=1 if chosen==actual else 2,actual_source_proxy_Brier=brier[actual],full_domain_localization=False,calibrated_likelihood=False))
    table(O/'WARMUP_STAGE_AND_COST.csv',stages);table(O/'E3_PREDICTED_EVENT_RATES.csv',rates);table(O/'NATIVE_FULL_MAP_PAIR_SCORES.csv',native);table(O/'ACTUAL_WORLD_PAIR_RANKING.csv',pair);table(O/'AGE_AND_SPATIAL_REACH.csv',particles)
    recovery=[]
    for pred in plan['prediction_streams']:
        for history in ['native','long220']:
            for arm in ['native_center','PID_window']:
                q=[r for r in particles if r['source']=='true' and r['prediction']==pred['id'] and r['history']==history]
                recovery.append(dict(prediction=pred['id'],history=history,arm=arm,stations_with_nonzero_prediction=sum(r['center_hit' if arm=='native_center' else 'PID_window_hit']>0 for r in q),stations_with_nonzero_prediction_9to13=sum(r['center_hit' if arm=='native_center' else 'PID_window_hit']>0 for r in q if r['stop']>=9),max_age_equivalent_s=q[0]['max_spread_equivalent_age_s']))
    summary=[]
    for scope in ['whole13','critical8to13']:
        for arm in ['native_center','PID_window']:
            for history in ['native','long220']:
                q=[r for r in pair if r['scope']==scope and r['arm']==arm and r['history']==history];t=[r for r in q if r['actual_source']=='true'];summary.append(dict(scope=scope,arm=arm,history=history,world_by_prediction_evaluations=len(q),true_world_evaluations=len(t),true_world_correct=sum(r['actual_source_pair_rank']==1 for r in t),all_correct=sum(r['actual_source_pair_rank']==1 for r in q),independent_worlds=4))
    table(O/'RESPONSE_RECOVERY_SUMMARY.csv',recovery);table(O/'SOURCE_PAIR_SUMMARY.csv',summary)
    put(O/'RESULT_SUMMARY.json',dict(recovery=recovery,source_pair=summary,native_map_pairs=native,A2_scope='local pair guard only, no full-domain or ROS nondegradation proof',unique_wind_vs_dimension_cause_established=False))
    print(json.dumps(dict(recovery=recovery,source_pair=summary,native_pairs=native),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
