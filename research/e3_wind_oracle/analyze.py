"""Single-factor wind diagnostic tables. No additional propagation."""
from pathlib import Path
import csv,json,math,os,struct
import numpy as np

B=Path('D:/ZYC/A-gas/workspace/METHOD_COMPARISON_O24_1M2_20261024/outputs')
O=Path(os.environ.get('E3_ORACLE_OUTPUT',str(B/'E3_HORIZONTAL_WIND_ORACLE_20261025')))
H=Path(os.environ.get('E3_HISTORY_OUTPUT',str(B/'E3_HISTORY_SUPPORT_20261025')))
P=Path(os.environ.get('E3_PAIR_OUTPUT',str(B/'E3_CAUSAL_PAIR_20261025')))

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n',encoding='utf8')
def table(p,data):
    with p.open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=data[0]);w.writeheader();w.writerows(data)

def main():
    plan=load(O/'PREREGISTERED_WIND_CONTRACT.json');assert load(O/'EXECUTION_RECEIPT.json')['status'].startswith('PASS_')
    physical=[r for r in rows(P/'PHYSICAL_WINDOWS.csv') if r['group']=='historical'];points=rows(O/'inputs/E3_UNIQUE_POINTS.csv');scene=load(O/'inputs/E3_scene.json');models={};response=[];reach=[];native=[];domain=[];predictions=plan['prediction_streams']
    for source in ['true','rival']:
        for pred in predictions:
            for wind in ['GMRF','horizontal_oracle']:
                prefix=O/'runs'/f'{"control" if wind=="GMRF" else "oracle"}_{source}_{pred["id"]}'
                series=H/'runs'/f'E3_{source}_{pred["id"]}_long220.timeseries.csv' if wind=='GMRF' else Path(str(prefix)+'.timeseries.csv')
                rawseries=rows(series);values=np.array([float(r['ppm']) for r in rawseries]).reshape(200,len(points));freq=np.fromfile(prefix.with_suffix('.f32'),dtype='<f4');one_per_step=rawseries[::len(points)];active=sum(int(r['active_filaments']) for r in one_per_step);invalid=sum(int(r['physical3D_rejected_centers']) for r in one_per_step)
                domain.append(dict(source=source,prediction=pred['id'],wind=wind,mean_active_centers=active/200,mean_centers_nonfree_in_native3D=invalid/200,particle_time_fraction_nonfree_3D=invalid/active,used_for_filtering_or_rescue=False,geometry_mask_unchanged=True))
                for pid,p in enumerate(points):
                    ij=((np.array([float(p['x']),float(p['y'])],np.float32)-np.array(scene['origin'],np.float32))/np.float32(scene['cell_size'])).astype(int);q=float(freq[ij[0]+scene['nx']*ij[1]])
                    for count in [3,4,5]:
                        v=values[:200//count*count,pid].reshape(-1,count).mean(1)
                        for arm,predicted in [('native_center',q),('PID_window',float((v>.1).mean()))]:models[source,pred['id'],wind,pid,count,arm]=predicted
                for stop in range(1,14):
                    obs=next(r for r in physical if int(r['stop'])==stop);pid=int(obs['point_id']);count=int(obs['samples'])
                    response.append(dict(source=source,prediction=pred['id'],wind=wind,stop=stop,point_id=pid,center_frequency=models[source,pred['id'],wind,pid,count,'native_center'],PID_window_frequency=models[source,pred['id'],wind,pid,count,'PID_window'],mean_predicted_ppm=float(values[:,pid].mean()),max_predicted_ppm=float(values[:,pid].max())))
                oldest=10.;oldcount=0;total=0;nearest={s:1e30 for s in range(8,14)}
                with Path(str(prefix)+'.particles.bin').open('rb') as stream:
                    while raw:=stream.read(8):
                        step,n=struct.unpack('<2I',raw);a=np.frombuffer(stream.read(n*16),dtype='<f4').reshape(n,4).astype(float);oldest=max(oldest,float(a[:,2].max()));oldcount+=int(((a[:,2]**2-100)/15>100).sum());total+=n
                        for stop in nearest:
                            p=points[int(next(r for r in physical if int(r['stop'])==stop)['point_id'])];d2=(a[:,0]-float(p['x']))**2+(a[:,1]-float(p['y']))**2+(.7-float(p['z']))**2;nearest[stop]=min(nearest[stop],float(np.sqrt(d2.min())))
                for stop in nearest:reach.append(dict(source=source,prediction=pred['id'],wind=wind,stop=stop,max_spread_equivalent_age_s=(oldest*oldest-100)/15,old100s_particle_time_fraction=oldcount/total,min_center_to_sensor_m=nearest[stop]))
    pairs=[]
    for world in ['true_r0','true_r1','rival_r0','rival_r1']:
        obs=[r for r in physical if r['world']==world]
        for pred in predictions:
            for wind in ['GMRF','horizontal_oracle']:
                for scope,valid in [('whole13',set(range(1,14))),('critical8to13',set(range(8,14)))]:
                    use=[r for r in obs if int(r['stop']) in valid]
                    for arm in ['native_center','PID_window']:
                        score={s:0. for s in ['true','rival']};brier=dict(score)
                        for r in use:
                            for s in score:
                                q=models[s,pred['id'],wind,int(r['point_id']),int(r['samples']),arm];y=int(r['hit']);score[s]+=math.log(1-.2*abs(y-q))/5;brier[s]+=(y-q)**2/len(use)
                        gap=score['true']-score['rival'];choose='true' if gap>1e-12 else 'rival' if gap< -1e-12 else 'tie';actual=world.split('_')[0];pairs.append(dict(world=world,actual_source=actual,prediction=pred['id'],wind=wind,scope=scope,arm=arm,true_minus_rival_log_compatibility=gap,true_over_rival_compatibility_ratio=math.exp(gap),pair_MAP=choose,actual_source_pair_rank=1 if choose==actual else 2,actual_source_Brier=brier[actual],calibrated_likelihood=False,full_domain_posterior=False))
    for pred in predictions:
        for wind in ['GMRF','horizontal_oracle']:
            r={s:load((O/'runs'/f'{"control" if wind=="GMRF" else "oracle"}_{s}_{pred["id"]}').with_suffix('.json')) for s in ['true','rival']};gap=math.log(r['true']['score'])-math.log(r['rival']['score']);native.append(dict(prediction=pred['id'],wind=wind,true_minus_rival_native_log_score=gap,wrong_over_true_native_full_observation_map_score=math.exp(-gap),pair_preference='true' if gap>0 else 'rival',full1132_source_posterior=False))
    table(O/'STATION_RESPONSE_COMPARISON.csv',response);table(O/'AGE_AND_REACH.csv',reach);table(O/'PHYSICAL_WORLD_PAIR_RANKING.csv',pairs);table(O/'NATIVE_OBSERVATION_MAP_PAIR_SCORES.csv',native);table(O/'PHYSICAL_DOMAIN_DIAGNOSTIC.csv',domain)
    summary=[]
    for scope in ['whole13','critical8to13']:
        for arm in ['native_center','PID_window']:
            for wind in ['GMRF','horizontal_oracle']:
                r=[r for r in pairs if r['scope']==scope and r['arm']==arm and r['wind']==wind];t=[r for r in r if r['actual_source']=='true'];summary.append(dict(scope=scope,arm=arm,wind=wind,correct_true_world_by_prediction=sum(q['actual_source_pair_rank']==1 for q in t),true_world_by_prediction_count=len(t),correct_all_world_by_prediction=sum(q['actual_source_pair_rank']==1 for q in r),all_world_by_prediction_count=len(r),actual_independent_worlds=4))
    table(O/'SOURCE_PAIR_SUMMARY.csv',summary)
    put(O/'RESULT_SUMMARY.json',dict(source_pair=summary,native_score=native,qualification=load(O/'WIND_INPUT_QUALIFICATION.json'),full_source_new_localization_claim=False,new_ROS=False))
    print(json.dumps(dict(summary=summary,native=native,critical_true=[r for r in response if r['source']=='true' and r['stop']>=8]),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
