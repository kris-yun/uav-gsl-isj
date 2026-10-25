"""Causal tables from retained queries only. No extra model or world calls."""
from pathlib import Path
import csv,hashlib,json,math,os,struct,zlib
import numpy as np
from scipy.ndimage import label

B=Path('D:/ZYC/A-gas/workspace/METHOD_COMPARISON_O24_1M2_20261024/outputs')
O=Path(os.environ.get('E3_CAUSE_OUTPUT',str(B/'E3_TRANSPORT_CAUSE_20261025')))
P=Path(os.environ.get('E3_PAIR_OUTPUT',str(B/'E3_CAUSAL_PAIR_20261025')))

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n',encoding='utf8')
def table(p,data):
    with p.open('w',encoding='utf8',newline='') as f:w=csv.DictWriter(f,fieldnames=data[0]);w.writeheader();w.writerows(data)

def decode(p):
    raw=p.read_bytes();assert raw[:13]==b'GADEN_RESULT\0' and raw[13]==1;b=zlib.decompress(raw[22:]);n=struct.unpack_from('<Q',b,48)[0];off=56+n+28;length=struct.unpack_from('<Q',b,off)[0];off+=8+length;count=struct.unpack_from('<Q',b,off)[0];a=np.frombuffer(b,dtype='<f4',offset=off+8).reshape(-1,4);assert len(a)==count;return a

def main():
    assert load(O/'UV_EXTENSION_RECEIPT.json')['status'].startswith('PASS_');plan=load(O/'PREREGISTERED_CAUSAL_CONTRACT.json');schedule=rows(O/'inputs/QUERIES.csv');groups={}
    for r in schedule:
        if r['group']=='historical':groups.setdefault((int(r['stop']),int(r['window'])),[]).append(r['query_id'])
    actual_windows=rows(O/'inputs/TARGET_PHYSICAL_WINDOWS.csv');target={w:np.array([float(next(r['mean_ppm'] for r in actual_windows if r['world']==w and r['group']=='historical' and int(r['window'])==e)) for s,e in sorted(groups)]) for w in ['true_r0','true_r1','rival_r0','rival_r1']}
    # Exact native contribution accounting of the untouched old E3, including
    # a state-level outside-center exclusion. This is not regenerated truth.
    original={r['query_id']:float(r['native_ppm']) for r in rows(P/'original_E3_decomposition/DECOMPOSED_QUERIES.csv')};bad=dict.fromkeys(original,0.);weighted={s:dict(total=0.,z=0.,below05=0.,outside=0.) for s in range(1,14)};stop_by_q={r['query_id']:int(r['stop']) for r in schedule if r['group']=='historical'}
    for r in rows(P/'original_E3_decomposition/FILAMENT_CONTRIBUTIONS.csv'):
        v=float(r['contribution_ppm']);z=float(r['center_z']);s=stop_by_q[r['query_id']]
        if z<0:bad[r['query_id']]+=v
        a=weighted[s];a['total']+=v;a['z']+=v*z;a['below05']+=v*(z<.5);a['outside']+=v*(z<0)
    original_means=np.array([np.mean([original[q] for q in groups[k]]) for k in sorted(groups)]);filtered_means=np.array([np.mean([original[q]-bad[q] for q in groups[k]]) for k in sorted(groups)]);target['original_E3']=original_means;target['original_E3_state_censored']=filtered_means
    observation=[]
    for s,a in weighted.items():
        idx=[i for i,k in enumerate(sorted(groups)) if k[0]==s];observation.append(dict(stop=s,concentration_weighted_center_z_m=a['z']/a['total'] if a['total'] else None,concentration_fraction_from_z_below0p5=a['below05']/a['total'] if a['total'] else None,fraction_from_outside_z_negative=a['outside']/a['total'] if a['total'] else None,original_positive_windows=int(sum(original_means[idx]>.1)),positive_windows_after_readonly_invalid_center_exclusion=int(sum(filtered_means[idx]>.1)),censor_is_not_full_physical_correction=True))
    table(O/'ORIGINAL_E3_HEIGHT_AND_BOUNDARY_AUDIT.csv',observation)
    archived=[]
    for world in ['true_r0','true_r1','rival_r0','rival_r1']:
        count=0;outside=0;minz=1e30;last_count=0;last_outside=0
        frames=sorted((P/'worlds'/world/'saved_world').glob('iteration_*'),key=lambda p:int(p.name.split('_')[-1]))
        for path in frames:
            a=decode(path);bad=np.any((a[:,:3]<[-5.5,-6.,0.])|(a[:,:3]>=[5.5,6.,3.]),axis=1);count+=len(a);outside+=int(bad.sum());minz=min(minz,float(a[:,2].min()));last_count=len(a);last_outside=int(bad.sum())
        archived.append(dict(world=world,saved_frames=len(frames),min_center_z_m=minz,outside_centers_across_selected_frames=outside,centers_across_selected_frames=count,last_frame_centers=last_count,last_frame_outside_centers=last_outside,scope='nonuniform saved snapshots, not an unbiased residence-time estimate',original_archive_not_changed=True))
    table(O/'ORIGINAL_TARGET_WORLD_BOUNDARY_AUDIT.csv',archived)
    arms=['original_bounds_full3d','strict_bounds_full3d','strict_bounds_plane','strict_bounds_no_vertical_wind','strict_bounds_no_buoyancy','strict_bounds_fixed_uv'];models={};window=[];station=[];identity=[];anchors=[]
    for arm in arms:
        for source in ['true','rival']:
            for pred in plan['prediction_streams']:
                d=O/'runs'/f'{arm}_{source}_{pred["id"]}';a={r['query_id']:float(r['raw_gas_ppm']) for r in rows(d/'RESPONSES.csv')};v=np.array([np.mean([a[q] for q in groups[k]]) for k in sorted(groups)]);models[arm,source,pred['id']]=v;result=load(d/'RESULT.json');identity.append(dict(arm=arm,source=source,prediction=pred['id'],outside_particle_time_samples=result['outside_particle_time_samples'],total_particle_time_samples=result['all_particle_time_samples'],min_z=result['min_z'],max_z=result['max_z'],effective_noise=result['noise_effective'],recorded_queries=result['queries'],steps=result['steps']))
                for i,(stop,event) in enumerate(sorted(groups)):window.append(dict(arm=arm,source=source,prediction=pred['id'],stop=stop,window=event,mean_ppm=float(v[i]),hit=int(v[i]>.1)))
                for stop in range(1,14):
                    ix=[i for i,k in enumerate(sorted(groups)) if k[0]==stop];station.append(dict(arm=arm,source=source,prediction=pred['id'],stop=stop,mean_ppm=float(v[ix].mean()),positive_windows=int(sum(v[ix]>.1)),total_windows=len(ix)))
                    fil=decode(d/'anchors'/f'stop_{stop}');anchors.append(dict(arm=arm,source=source,prediction=pred['id'],stop=stop,filaments=len(fil),center_z_mean=float(fil[:,2].mean()),center_z_q10=float(np.quantile(fil[:,2],.1)),center_z_q90=float(np.quantile(fil[:,2],.9)),physical_outside_centers=int(np.any((fil[:,:3]<[-5.5,-6.,0.])|(fil[:,:3]>=[5.5,6.,3.]),axis=1).sum())))
    table(O/'PREDICTION_WINDOW_RESPONSES.csv',window);table(O/'STATION_RECOVERY.csv',station);table(O/'MODEL_STATE_BOUNDS.csv',identity);table(O/'ANCHOR_HEIGHTS.csv',anchors)
    pairs=[]
    for arm in arms:
        for pred in plan['prediction_streams']:
            for case,y in target.items():
                source='true' if case.startswith('true') or case.startswith('original') else 'rival'
                for scope,idx in [('whole13',np.arange(65)),('critical8to13',np.arange(35,65)),('late10to13',np.arange(45,65))]:
                    yy=y[idx]
                    for method in ['continuous_MSE','unknown_nonnegative_amplitude_MSE','binary_Brier']:
                        loss={};gains={}
                        for h in ['true','rival']:
                            x=models[arm,h,pred['id']][idx];gain=max(0,float(x@yy)/max(float(x@x),1e-30)) if method=='unknown_nonnegative_amplitude_MSE' else 1.;gains[h]=gain
                            loss[h]=float(np.mean(((yy>.1).astype(float)-(x>.1).astype(float))**2)) if method=='binary_Brier' else float(np.mean((yy-gain*x)**2))
                        delta=loss['rival']-loss['true'];tol=1e-12*max(1,loss['true'],loss['rival']);chosen='true' if delta>tol else 'rival' if delta< -tol else 'tie';correct=.5 if chosen=='tie' else int(chosen==source);pairs.append(dict(arm=arm,prediction=pred['id'],case=case,actual_source=source,scope=scope,method=method,true_hypothesis_loss=loss['true'],rival_hypothesis_loss=loss['rival'],source_pair_choice=chosen,tie_aware_correct=correct,true_gain=gains['true'],rival_gain=gains['rival'],source_pair_only=True,calibrated_posterior=False,new_full_domain_localization=False))
    table(O/'SOURCE_PAIR_RESULTS.csv',pairs)
    summary=[]
    for arm in arms:
        for scope in ['whole13','critical8to13','late10to13']:
            for method in ['continuous_MSE','unknown_nonnegative_amplitude_MSE','binary_Brier']:
                r=[r for r in pairs if r['arm']==arm and r['scope']==scope and r['method']==method and not r['case'].startswith('original')];summary.append(dict(arm=arm,scope=scope,method=method,correct_tie_aware_of8=sum(q['tie_aware_correct'] for q in r),true_source_cases_correct_of4=sum(q['tie_aware_correct'] for q in r if q['actual_source']=='true'),actual_target_worlds=4,prediction_streams=2,independent_evaluations_not8=True))
    table(O/'SOURCE_PAIR_SUMMARY.csv',summary)
    # Topological path existence is distinct from directed dynamic transport.
    text=(O/'inputs/OccupancyGrid3D.csv').read_text().splitlines();grid=np.array([int(v) for line in text[4:] if line!=';' for v in line.split()],np.uint8).reshape(30,110,120).transpose(0,2,1);topology=[]
    for z in [.2,.5,.7,1.]:
        k=int(np.float32(z)/np.float32(.1));components,n=label(grid[k]==0);start=((np.array([-4.,-1.9])-[-5.5,-6.])/.1).astype(int);s=int(components[start[1],start[0]])
        for stop in range(1,14):
            q=next(r for r in schedule if r['group']=='historical' and int(r['stop'])==stop);i=((np.array([float(q['x']),float(q['y'])])-[-5.5,-6.])/.1).astype(int);topology.append(dict(height_m=z,stop=stop,source_free_component=s,query_free_component=int(components[i[1],i[0]]),same_free_component=bool(s!=0 and components[i[1],i[0]]==s),scope='axis-adjacent geometric path existence, not advective reachability'))
    table(O/'FINE_SLICE_TOPOLOGY_NEGATIVE_CONTROL.csv',topology)
    put(O/'ANALYSIS_SUMMARY.json',dict(source_pair_summary=summary,critical_recovery=[r for r in station if r['source']=='true' and r['stop']>=8],old_height_audit=[r for r in observation if r['stop']>=8],all_fine_slices_connected=all(r['same_free_component'] for r in topology),all_strict_candidate_states_inbounds=all(r['outside_particle_time_samples']==0 for r in identity if r['arm']!='original_bounds_full3d'),new_ROS=0,original_worlds_overwritten=False))
    print(json.dumps(dict(whole13=[r for r in summary if r['scope']=='whole13'],late_true=[r for r in station if r['source']=='true' and r['stop']>=10]),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
