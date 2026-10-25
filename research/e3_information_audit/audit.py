"""Read-only frozen O24 evidence audit. No propagation, fitting, or ROS.

Existing case outcomes are opened development evidence. Preregister only the
new bounded query design; never call retrospective analysis a blind test.
"""
from pathlib import Path
import argparse, bisect, csv, hashlib, io, json, math, os, shutil, time, zipfile
import numpy as np
from scipy.special import expit
from scipy.ndimage import distance_transform_edt

PROJECT=Path(os.environ.get('PMFS_PROJECT_ROOT','D:/ZYC/A-gas'))
COMPARE=PROJECT/'workspace/METHOD_COMPARISON_O24_1M2_20261024'
OUT=Path(os.environ.get('PMFS_AUDIT_OUTPUT',str(COMPARE/'outputs/E3_INFORMATION_SOURCE_20261025')))
BASELINE=PROJECT/'workspace/FROZEN_O24_1M2_SCREEN12_20261024'
REPLAY=Path(os.environ.get('PMFS_REPLAY_ROOT',str(COMPARE/'V12_REVIEW_20261024/pro_handoff/physical_replay_bundle')))
ROLES=['E3_R01','A2_R01_REFERENCE','A2_R02','A2_R03']

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def put(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n',encoding='utf8')
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def table(p,rr):
    if not rr: return
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    with Path(p).open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def params(r):
    d=load(r/'runtime/resolved_GSL_parameters.json')
    keys={1:'bool_value',2:'integer_value',3:'double_value',4:'string_value'}
    return {k:v[keys[v['type']]] for k,v in zip(d['names'],d['values']) if v['type'] in keys}

def prepare():
    OUT.mkdir(exist_ok=False)
    eps=rows(BASELINE/'evidence_index/EPISODE_RESULTS.csv')
    selected=[]
    for role in ROLES:
        e=next(e for e in eps if e['role']==role); p=Path(e['archive'])
        dest=OUT/'inputs'/role;dest.mkdir(parents=True)
        with zipfile.ZipFile(p) as z:
            names=[n for n in z.namelist() if n in ['CASE_META.json','PHYSICAL_FRAME_TIME.csv','POSTERIOR_UPDATE_METRICS.json','FINAL_RUN_QA.json'] or n.startswith('runtime/') and not '/ros_logs/' in n and not n.endswith('launch.log')]
            for n in names:
                target=dest/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))
        selected.append(dict(role=role,archive=str(p),sha256=sha(p),members=len(names),original_result=e))
    put(OUT/'INPUT_ARCHIVE_BINDINGS.json',selected)
    put(OUT/'PREREGISTERED_SCOPE.json',dict(
        identity='FROZEN_O24_E3_INFORMATION_SOURCE_AUDIT_20261025',
        created_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        status='RETROSPECTIVE_AUDIT_PLUS_FIXED_NEW_QUERIES_NOT_BLIND',
        cases=ROLES,B2='source-domain diagnostic only, no active comparison',
        truth_usage='evaluation and leaf binding only; never action selection',
        neural_training=0,new_worlds=0,forward_simulations=0,ROS_runs=0,
        native_replay='all saved updates and all saved candidate maps; score and normalized posterior parity required',
        replacements=['native_full_map','actual_cells_only','raw_window_compatibility','stop_frequency_compatibility'],
        replacement_scope='fixed native tree/table diagnostic; not a new PMFS execution or calibrated likelihood',
        action_anchors='E3 source updates 1,2,3 at consumed events20,35,50; no label-based anchor selection',
        actions=['hold','east_0p5','north_0p5','west_0p5','south_0p5','recorded_future_route'],
        motion=dict(max_speed_mps=.5,assumed_rest_acceleration_mps2=.5,body_radius_m=.2,motion_slot_s=2.,dwell_s=2.5,total_s=4.5),
        windows=dict(count=5,duration_s=.4,sample_dt_s=.1,window_start_relative_s=[2.,2.5,3.,3.5,4.]),
        eligibility='whole segment: frozen navigation clearance plus native3D free at sensor0.5m, no bypass/replacement on rejection',
        ordinary_EIG='single-station Bernoulli mutual information from full native source support and current cached hit frequencies; not asserted PID likelihood; no future gas queried for choice',
        physical_queries='existing E3 and eligible E4 companion archive only; all legal fixed actions share times; maximum720 gas point queries plus native historical regression290',
        E4_scope='different actual source coordinate/height; no substitution for locked wrong MAP world; no independent-realization claim',
        gates='no algorithm promotion or ROS from a model-only IG/observed one-world difference',
        code_sha256=sha(__file__)))
    print('PREPARED',len(selected),flush=True)

def case_data(role):
    r=OUT/'inputs'/role;p=params(r);nav=load(r/'runtime/NAVIGATION_MAP_METADATA.json')
    allpost=rows(r/'runtime/native_posterior_updates.csv');cm=rows(r/'runtime/native_candidate_maps.csv')
    binary=(r/'runtime/native_candidate_maps.f32').read_bytes();path=np.array(load(r/'runtime/robot_path.json'))
    win=[x for x in rows(r/'runtime/native_window_consumption.csv') if x['status']=='CONSUMED']
    nx=nav['width']//p['scale'];ny=nav['height']//p['scale'];cs=float(allpost[0]['cell_size_m'])
    meta=load(r/'CASE_META.json');truth=np.array(meta['source_xyz'][:2]);tc=np.floor((truth-[nav['origin_x'],nav['origin_y']])/cs).astype(int);tf=int(tc[0]+nx*tc[1])
    wp=[]
    for w in win:
        t=int(w['node_clock_ns'])*1e-9;pi=max(0,np.searchsorted(path[:,0],t,side='right')-1)
        xy=path[pi,1:3];c=np.floor((xy-[nav['origin_x'],nav['origin_y']])/cs).astype(int)
        wp.append(dict(**w,ros_s=t,x=float(xy[0]),y=float(xy[1]),pose_age_s=t-path[pi,0],flat=int(c[0]+nx*c[1]),hit=float(w['concentration_mean_ppm'])>p['th_gas_present']))
    return dict(root=r,par=p,nav=nav,nx=nx,ny=ny,cs=cs,meta=meta,truth=truth,tf=tf,allpost=allpost,cm=cm,binary=binary,path=path,windows=wp)

def snapshot(d,u):
    post=[x for x in d['allpost'] if int(x['update'])==u]
    idx=np.array([int(x['col'])+d['nx']*int(x['row']) for x in post]);xy=np.array([[float(x['x_m']),float(x['y_m'])] for x in post]);saved=np.array([float(x['source_probability']) for x in post])
    hit=expit([float(x['hit_log_odds']) for x in post]);alpha=np.array([float(x['hit_confidence']) for x in post]);D=d['par']['sourceDiscriminationPower']
    cc=sorted([x for x in d['cm'] if int(x['update'])==u],key=lambda x:(-int(x['size_x'])*int(x['size_y']),int(x['call'])))
    maps=[];owner=np.full(d['nx']*d['ny'],-1,int);grid=np.zeros(len(owner));errors=[]
    for j,c in enumerate(cc):
        f=np.frombuffer(d['binary'],dtype='<f4',count=int(c['count']),offset=int(c['offset_bytes'])).astype(float)
        score=np.prod(1-D*abs(hit-f[idx])*alpha);errors.append(abs(score-float(c['score']))/max(abs(float(c['score'])),1e-280))
        x,y,sx,sy=[int(c[k]) for k in ['origin_x','origin_y','size_x','size_y']]
        owner.reshape(d['ny'],d['nx'])[y:y+sy,x:x+sx]=j;grid.reshape(d['ny'],d['nx'])[y:y+sy,x:x+sx]=score;maps.append(f)
    assert np.all(owner[idx]>=0)
    p=grid[idx]/grid[idx].sum();err=float(np.max(abs(p-saved)))
    assert max(errors)<1e-10 and err<1e-10,(u,max(errors),err)
    return dict(update=u,idx=idx,xy=xy,p=p,hit=hit,alpha=alpha,candidates=cc,maps=np.array(maps),owner=owner,grid=grid,max_score_relative_error=max(errors),max_posterior_absolute_error=err)

def metrics(p,s,d):
    ti=int(np.where(s['idx']==d['tf'])[0][0]);a=p[ti];n=len(p)
    greater=int(np.sum(p>a*(1+1e-12)));tied=int(np.sum(np.isclose(p,a,rtol=1e-12,atol=0)));order=np.argsort(-p,kind='stable');mp=int(order[0])
    k=max(1,int(n*.05));cut=p[order[k-1]];strict=p>cut*(1+1e-12);boundary=np.isclose(p,cut,atol=0,rtol=1e-12);remaining=k-int(strict.sum())
    # Conservative source-cell membership when top5 boundary is tied.
    guaranteed=bool(p[ti]>cut*(1+1e-12) or boundary.sum()<=remaining and boundary[ti])
    hp=order[:np.searchsorted(np.cumsum(p[order]),.9)+1]
    top=order[:k];center=np.average(s['xy'][top],axis=0,weights=p[top]);mu=p@s['xy']
    return dict(rank_best=greater+1,rank_worst=greater+tied,true_probability=float(a),MAP_x=float(s['xy'][mp,0]),MAP_y=float(s['xy'][mp,1]),MAP_error_m=float(np.linalg.norm(s['xy'][mp]-d['truth'])),Top5_stable_sort_error_m=float(np.linalg.norm(center-d['truth'])),Top5_true_guaranteed=guaranteed,Top5_true_possible=bool(p[ti]>=cut*(1-1e-12)),HPD90_true=bool(ti in hp),variance_m2=float(p@np.sum((s['xy']-mu)**2,axis=1)))

def analyze():
    reports=[];updates=[];winrows=[];stops=[];replacement=[];contributions=[]
    for role in ROLES:
        d=case_data(role);last=max(int(x['update']) for x in d['allpost']);final=snapshot(d,last);wf=int(final['idx'][np.argmax(final['p'])])
        for u in range(1,last+1):
            s=snapshot(d,u);prefix=d['windows'][:(1+u*d['par']['stepsSourceUpdate'])*d['par']['maxUpdatesPerStop']]
            assert len(prefix)==(1+u*3)*5
            vis=np.isin(s['idx'],[w['flat'] for w in prefix]);ti=int(s['owner'][d['tf']]);mi=int(s['owner'][wf]);ft=s['maps'][ti];fm=s['maps'][mi];D=d['par']['sourceDiscriminationPower']
            delta=np.log1p(-D*abs(s['hit']-fm[s['idx']])*s['alpha'])-np.log1p(-D*abs(s['hit']-ft[s['idx']])*s['alpha'])
            row=dict(role=role,update=u,windows_consumed=len(prefix),positive_windows=sum(w['hit'] for w in prefix),positive_true_zero=sum(w['hit'] and ft[w['flat']]==0 for w in prefix),positive_true_zero_wrong_nonzero=sum(w['hit'] and ft[w['flat']]==0 and fm[w['flat']]>0 for w in prefix),true_call=int(s['candidates'][ti]['call']),wrong_fixed_call=int(s['candidates'][mi]['call']),true_leaf=json.dumps({k:int(s['candidates'][ti][k]) for k in ['origin_x','origin_y','size_x','size_y']}),wrong_to_true_score_ratio=float(s['grid'][wf]/s['grid'][d['tf']]),visited_loggap=float(delta[vis].sum()),unvisited_loggap=float(delta[~vis].sum()),score_replay_relative_error=s['max_score_relative_error'],posterior_replay_absolute_error=s['max_posterior_absolute_error'],**metrics(s['p'],s,d))
            updates.append(row)
            if u!=last: continue
            grid_modes={x:np.zeros(d['nx']*d['ny']) for x in ['actual_cells_only','raw_window_compatibility','stop_frequency_compatibility']}
            wi=np.array([w['flat'] for w in prefix]);observed=np.array([w['hit'] for w in prefix],float)
            for j,c in enumerate(s['candidates']):
                f=s['maps'][j];vals=1-D*abs(s['hit']-f[s['idx']])*s['alpha'];ss={
                    'actual_cells_only':float(np.prod(vals[vis])),
                    'raw_window_compatibility':float(np.prod(1-D*abs(observed-f[wi]))),
                    'stop_frequency_compatibility':float(np.prod([1-D*abs(observed[a:a+5].mean()-f[wi[a]]) for a in range(0,len(wi),5)]))}
                x,y,sx,sy=[int(c[k]) for k in ['origin_x','origin_y','size_x','size_y']]
                for mode,v in ss.items():grid_modes[mode].reshape(d['ny'],d['nx'])[y:y+sy,x:x+sx]=v
            for mode,g in grid_modes.items():
                p=g[s['idx']]/g[s['idx']].sum();replacement.append(dict(role=role,mode=mode,wrong_to_true_score_ratio=float(g[wf]/g[d['tf']]),**metrics(p,s,d)))
            for w in prefix:
                k=w['flat'];ipos=np.where(s['idx']==k)[0];ip=int(ipos[0]) if len(ipos) else None
                winrows.append(dict(role=role,diagnostic_response_update=last,scope='final snapshot against historical reading; not contemporaneous predictive calibration',event=int(w['event']),stop=(int(w['event'])-1)//5+1,ros_s=w['ros_s'],pose_age_s=w['pose_age_s'],x=w['x'],y=w['y'],cell_col=k%d['nx'],cell_row=k//d['nx'],measurement_cell_in_saved_source_support=ip is not None,concentration_ppm=float(w['concentration_mean_ppm']),actual_hit=int(w['hit']),gas_count=int(w['gas_count']),local_wind_speed=float(w['wind_speed_mean']),local_wind_angle=float(w['wind_direction_mean']),true_native_center_hit_frequency=float(ft[k]),wrong_native_center_hit_frequency=float(fm[k]),native_contact_probability=float(s['hit'][ip]) if ip is not None else None,confidence=float(s['alpha'][ip]) if ip is not None else None))
            for a in range(0,len(prefix),5):
                ww=prefix[a:a+5];k=ww[0]['flat'];assert len(set(w['flat'] for w in ww))==1
                pp=np.array([float(w['concentration_mean_ppm']) for w in ww]);stops.append(dict(role=role,stop=a//5+1,x=ww[0]['x'],y=ww[0]['y'],first_ros_s=ww[0]['ros_s'],last_ros_s=ww[-1]['ros_s'],mean_ppm=float(pp.mean()),min_ppm=float(pp.min()),max_ppm=float(pp.max()),hits=sum(w['hit'] for w in ww),windows=5,true_native_frequency=float(ft[k]),wrong_native_frequency=float(fm[k])))
            for i,k in enumerate(s['idx']):
                contributions.append(dict(role=role,flat=int(k),x=float(s['xy'][i,0]),y=float(s['xy'][i,1]),directly_sampled=int(vis[i]),contact_probability=float(s['hit'][i]),confidence=float(s['alpha'][i]),true_frequency=float(ft[k]),wrong_frequency=float(fm[k]),wrong_minus_true_log_compatibility=float(delta[i])))
            pos=[float(w['concentration_mean_ppm']) for w in prefix if w['hit']]
            reports.append(dict(**row,world_identity=d['meta'].get('world_identity','NOT_IN_LEGACY_CASE_META_SEE_ARCHIVE_BINDING'),native_ELF=d['meta'].get('actual_binary_sha256',load(d['root']/'runtime/NATIVE_EXECUTABLE_IDENTITY.json')),positive_ppm_min=min(pos),positive_ppm_max=max(pos),unique_sampled_cells=len(set(wi)),true_xyz=d['meta']['source_xyz'],wrong_fixed_xy=final['xy'][np.argmax(final['p'])].tolist(),all_zero_conflict_not_sufficient_failure='A2 normal controls included',compression_conclusion='binary branch demonstrably discards amplitude; source usefulness cannot be determined from one actual source archive'))
    for name,rr in [('UPDATE_TRAJECTORIES.csv',updates),('WINDOW_RESPONSE_COMPARISON.csv',winrows),('STOP_RESPONSE_COMPARISON.csv',stops),('FIXED_TABLE_ORDINARY_CONTROLS.csv',replacement),('SPATIAL_LOG_SUPPORT_CONTRIBUTIONS.csv',contributions)]: table(OUT/name,rr)
    put(OUT/'CASE_AUDIT.json',reports)
    if (BASELINE/'evidence_index/EPISODE_RESULTS.csv').exists():table(OUT/'B2_DOMAIN_DIAGNOSTIC_ONLY.csv',[r for r in rows(BASELINE/'evidence_index/EPISODE_RESULTS.csv') if r['case']=='B2'])
    print('AUDITED',len(updates),'source updates and',len(winrows),'windows')

def entropy(q):
    q=np.asarray(q);mask=(q>0)&(q<1);out=np.zeros_like(q);out[mask]=-q[mask]*np.log(q[mask])-(1-q[mask])*np.log1p(-q[mask]);return out

def plan_queries():
    assert not (OUT/'FROZEN_QUERY_DESIGNS.json').exists()
    d=case_data('E3_R01');nav=d['nav'];r=d['root'];fine=np.fromfile(r/'runtime/navigation_map.s8',dtype=np.int8).reshape(nav['height'],nav['width'])==0
    clearance=distance_transform_edt(fine)*nav['resolution'];origin=np.array([nav['origin_x'],nav['origin_y']])
    lines=(REPLAY/'actual_runtime/OccupancyGrid3D.csv').read_text().splitlines();gorigin=np.array(list(map(float,lines[0].split()[1:])));dims=np.array(list(map(int,lines[2].split()[1:])));res=float(lines[3].split()[1]);layers=[];rr=[]
    for line in lines[4:]:
        if line.strip()==';':
            if rr: layers.append(rr);rr=[]
        elif line.strip():rr.append(list(map(int,line.split())))
    if rr:layers.append(rr)
    vox=np.asarray(layers,np.int8);assert vox.shape==tuple(dims[[2,0,1]])
    def check(point):
        ij=np.floor((point-origin)/nav['resolution']).astype(int)
        if np.any(ij<0) or ij[0]>=nav['width'] or ij[1]>=nav['height']:return 'outside_navigation_map'
        if clearance[ij[1],ij[0]]<.2:return 'disc_clearance_less_than_0p2m'
        xyz=np.r_[point,.5];ijk=np.floor((xyz-gorigin)/res).astype(int)
        if np.any(ijk<0) or np.any(ijk>=dims) or vox[ijk[2],ijk[0],ijk[1]]!=0:return 'sensor_not_native3D_free'
        return None
    trace=rows(r/'runtime/physical_clock_trace.csv');anchor_ros=int(trace[0]['anchor_ros_ns'])*1e-9
    physical_offset=float(trace[0]['target_internal_s'])-int(trace[0]['receipt_ros_ns'])*1e-9
    designs=[];queryrows=[];summary=[]
    for u in [1,2,3]:
        s=snapshot(d,u);w=d['windows'][(1+u*3)*5-1];t=w['ros_s'];center=np.array([w['x'],w['y']]);ti=int(s['owner'][d['tf']]);mp=int(s['idx'][np.argmax(s['p'])]);mi=int(s['owner'][mp])
        probs=s['maps'][s['owner'][s['idx']]]
        for action,offset in [('hold',[0,0]),('east_0p5',[.5,0]),('north_0p5',[0,.5]),('west_0p5',[-.5,0]),('south_0p5',[0,-.5]),('recorded_future_route',None)]:
            if offset is not None:
                goal=center+offset;path=center[None,:]+np.linspace(0,1,101)[:,None]*np.array(offset);endpoint=goal;dist=float(np.linalg.norm(offset));min_time=0 if not dist else 2*math.sqrt(dist/.5) if dist<.5 else dist/.5+1.
            else:
                ii=(d['path'][:,0]>=t)&(d['path'][:,0]<=t+4.5);path=np.vstack([center,d['path'][ii,1:3]]);endpoint=path[-1];dist=float(np.linalg.norm(np.diff(path,axis=0),axis=1).sum());min_time=None
                dense=[]
                for a,b in zip(path[:-1],path[1:]):dense.extend(a+np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(b-a)/.005))))[:,None]*(b-a))
                path=np.array(dense)
            rejected=next((err for p in path if (err:=check(p)) is not None),None)
            if min_time is not None and min_time>2+1e-9:rejected=rejected or 'rest_to_rest_motion_exceeds2s'
            if dist>2.25+1e-9:rejected=rejected or 'translation_exceeds_common_speed_time_cap'
            col,row=np.floor((endpoint-origin)/d['cs']).astype(int);flat=int(col+d['nx']*row)
            if flat not in s['idx']:rejected=rejected or 'endpoint_not_native_response_support'
            if rejected is None:
                q=probs[:,flat];ig=float(entropy(np.array([s['p']@q]))[0]-s['p']@entropy(q))
            else:ig=None
            design=dict(update=u,action=action,start_ros_s=t,start_physical_s=t+physical_offset,start_xy=center.tolist(),endpoint_xy=endpoint.tolist(),path_length_m=dist,total_s=4.5,speed_cap_mps=.5,assumed_acceleration_mps2=.5,minimum_rest_motion_s=min_time,legal=rejected is None,rejection=rejected,model_single_station_IG_nats=ig,planner_truth_access=False,planner_future_measurement_access=False,planner_uses_current_full_source_domain=len(s['idx']),physical_offset_s=physical_offset,model_scope='puff-center frequency treated as Bernoulli proxy; not a calibrated PID event model',true_region_model_frequency=float(s['maps'][ti,flat]) if 0<=flat<d['nx']*d['ny'] else None,current_MAP_region_frequency=float(s['maps'][mi,flat]) if 0<=flat<d['nx']*d['ny'] else None)
            designs.append(design)
            if rejected:continue
            for window in range(5):
                for tick in range(4):
                    ros=t+2+.5*window+.1*tick
                    if offset is None:
                        pi=np.searchsorted(d['path'][:,0],ros,side='right')-1;pos=d['path'][pi,1:3]
                    else:pos=endpoint
                    queryrows.append(dict(query_id=f'u{u}_{action}_w{window}_t{tick}',update=u,action=action,window=window,tick=tick,ros_s=ros,physical_s=ros+physical_offset,x=float(pos[0]),y=float(pos[1]),z=.5))
        eligible=[v for v in designs if v['update']==u and v['legal'] and v['action']!='recorded_future_route']
        best=max(eligible,key=lambda v:v['model_single_station_IG_nats']) if eligible else None
        summary.append(dict(update=u,selection=best['action'] if best else None,reason='ordinary full-support IG from past cached responses; source-blind, frozen before physical queries'))
    put(OUT/'FROZEN_QUERY_DESIGNS.json',designs);put(OUT/'ORDINARY_EIG_SELECTED_BEFORE_READOUT.json',summary);table(OUT/'FIXED_QUERY_SCHEDULE.csv',queryrows)
    # Qualify actual other-source archives without conflating models and worlds.
    inventories=[];qroot=PROJECT/'workspace/O24_MULTIWORLD_BASELINE_20261024/G0_AE';base=load(qroot/'E3/WORLD_QUALIFICATION.json')
    for case in ['E1','E2','E3','E4']:
        z=load(qroot/case/'WORLD_QUALIFICATION.json');same_map=z['grid_sha256']==base['grid_sha256'];same_wind=[w['sha256'] for w in z['wind']]==[w['sha256'] for w in base['wind']]
        inventories.append(dict(case=case,source_xyz=z['source_xyz_nominal'],geometry_sha256=z['grid_sha256'],wind_sha256=[v['sha256'] for v in z['wind']],same_geometry=same_map,same_wind=same_wind,source_2D_legal=z['geometry_class']=='G1_3D_AND_2D_LEGAL',gas_type=z['first_frame']['gas_type'],moles_per_filament=z['first_frame']['moles_per_filament'],source_height_matches_E3=abs(z['source_xyz_nominal'][2]-.7)<1e-6,exact_locked_wrong_source=False,independent_randomness=z['independent_random_realization_verified'],qualified_strict_locked_pair=False,companion_scope='E4 only: descriptive different3Dsource world under same geometry/wind/nominal release; no fixedheight or lockedwrongsource inference' if case=='E4' else 'inventory only'))
    put(OUT/'OTHER_SOURCE_WORLD_INVENTORY.json',inventories)
    print(json.dumps(dict(designs=len(designs),legal=sum(v['legal'] for v in designs),query_positions_per_world=len(queryrows),selections=summary),indent=2))

def analyze_queries():
    designs=load(OUT/'FROZEN_QUERY_DESIGNS.json');selection={r['update']:r['selection'] for r in load(OUT/'ORDINARY_EIG_SELECTED_BEFORE_READOUT.json')}
    joined=[];station=[];pair=[]
    for case in ['E3','E4']:
        folder=OUT/'native_query'/case;bindings=rows(folder/'QUERY_BINDING.csv');data=rows(folder/'QUERY_OUTPUT.csv');assert len(bindings)==len(data)==320
        for a,b in zip(bindings,data):
            assert a['query_id']==b['query_id'] and a['frame']==b['frame']
            assert abs(float(a['x'])-float(b['x']))<1e-10 and abs(float(a['y'])-float(b['y']))<1e-10
            joined.append(dict(**a,concentration_ppm=float(b['raw_gas_ppm']),hit=int(float(b['raw_gas_ppm'])>.1),kernel_mode=int(b['mode'])))
        for design in designs:
            if not design['legal']:continue
            rr=[x for x in joined if x['case']==case and int(x['update'])==design['update'] and x['action']==design['action']]
            assert len(rr)==20
            pp=np.array([r['concentration_ppm'] for r in rr]).reshape(5,4);means=pp.mean(axis=1);hits=means>.1
            pred=design['true_region_model_frequency'];wrong=design['current_MAP_region_frequency']
            station.append(dict(case=case,update=design['update'],action=design['action'],selected_before_readout=design['action']==selection[design['update']],physical_source_role='frozen E3 true world' if case=='E3' else 'E4 different actual3Dsource; not lockedwrongworld',height_m=.7 if case=='E3' else 1.,five_window_mean_ppm=float(means.mean()),minimum_window_mean_ppm=float(means.min()),maximum_window_mean_ppm=float(means.max()),positive_windows=int(hits.sum()),windows=5,requested_ticks=20,unique_physical_frames=len(set(r['frame'] for r in rr)),model_single_station_IG_nats=design['model_single_station_IG_nats'],E3_true_leaf_prediction=pred,E3_current_MAP_leaf_prediction=wrong,E3_true_proxy_Brier=float(np.mean((hits-pred)**2)) if case=='E3' else None,E3_current_MAP_proxy_Brier=float(np.mean((hits-wrong)**2)) if case=='E3' else None,motion_distance_m=design['path_length_m'],time_budget_s=4.5,window_hit_pattern=''.join(map(str,hits.astype(int)))))
    for design in designs:
        if not design['legal']:continue
        seq=[]
        for c in ['E3','E4']:
            rr=[x for x in joined if x['case']==c and int(x['update'])==design['update'] and x['action']==design['action']];seq.append(np.array([r['concentration_ppm'] for r in rr]))
        a,b=seq;ma=a.reshape(5,4).mean(1);mb=b.reshape(5,4).mean(1);dot=float(a@b);den=float(np.linalg.norm(a)*np.linalg.norm(b));gain=float(max(0,a@b/max(b@b,1e-30)))
        pair.append(dict(update=design['update'],action=design['action'],EIG_selected=design['action']==selection[design['update']],different_sampled_hit_windows=int(np.sum((ma>.1)!=(mb>.1))),different_raw_samples=int(np.sum(a!=b)),raw_RMSE_ppm=float(np.sqrt(np.mean((a-b)**2))),cosine_similarity=float(dot/den) if den>0 else None,nonnegative_amplitude_fit_residual_RMSE=float(np.sqrt(np.mean((a-gain*b)**2))),five_window_pattern_E3=''.join(map(str,(ma>.1).astype(int))),five_window_pattern_E4=''.join(map(str,(mb>.1).astype(int))),scope='one archived world per source; source height differs0.3m; not unseen-source localization nor independent-replicate evidence'))
    table(OUT/'ALL_NATIVE_QUERY_READOUTS.csv',joined);table(OUT/'ACTION_WINDOW_SUMMARY.csv',station);table(OUT/'ACTUAL_E3_E4_OBSERVABILITY_DIAGNOSTIC.csv',pair)
    # Direct-vs-masked conflict separates a coarse-domain artifact from prediction mismatch.
    rr=rows(OUT/'WINDOW_RESPONSE_COMPARISON.csv');quality=[]
    for role in ROLES:
        ww=[r for r in rr if r['role']==role];supported=[r for r in ww if r['measurement_cell_in_saved_source_support']=='True']
        quality.append(dict(role=role,windows=len(ww),measurement_cells_outside_native_coarse_support=sum(r['measurement_cell_in_saved_source_support']=='False' for r in ww),positive_true_zero_all=sum(r['actual_hit']=='1' and float(r['true_native_center_hit_frequency'])==0 for r in ww),positive_true_zero_supported_cells_only=sum(r['actual_hit']=='1' and float(r['true_native_center_hit_frequency'])==0 for r in supported),max_pose_time_join_age_s=max(float(r['pose_age_s']) for r in ww)))
    put(OUT/'MEASUREMENT_SUPPORT_QUALIFIER.json',quality)
    # Check whether the locked rival is even a possible physical source at E3 height.
    lines=(REPLAY/'actual_runtime/OccupancyGrid3D.csv').read_text().splitlines();origin=np.array(list(map(float,lines[0].split()[1:])));res=float(lines[3].split()[1]);layers=[];rr=[]
    for line in lines[4:]:
        if line.strip()==';':
            if rr:layers.append(rr);rr=[]
        elif line.strip():rr.append(list(map(int,line.split())))
    if rr:layers.append(rr)
    vox=np.array(layers);rival=np.array([-2.375,-4.875,.7]);i=((rival.astype(np.float32)-origin.astype(np.float32))/np.float32(res)).astype(int)
    put(OUT/'LOCKED_RIVAL_PHYSICAL_SOURCE_CHECK.json',dict(point_xyz=rival.tolist(),native_voxel_index=i.tolist(),native_cell_state=int(vox[i[2],i[0],i[1]]),source_free=bool(vox[i[2],i[0],i[1]]==0),scope='diagnostic source query only; no source moved, no world generated'))
    print(json.dumps(dict(E3_selected=[r for r in station if r['case']=='E3' and r['selected_before_readout']],support_checks=quality),indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('stage',choices=['prepare','analyze','plan_queries','analyze_queries']);opt=a.parse_args();globals()[opt.stage]()
