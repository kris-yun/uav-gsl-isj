"""One real event stream, upstream zero-shot weights, no training or target selection."""
import ast,csv,hashlib,json,math,os,sys,time
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'comparison_work/vgr_adapter'))
from official_three_channel import channels,location
from wind_parity import device_clockwise_degree
sys.path.insert(0,str(ROOT.parent/'comparison_work/official_reproduction'))
from run_official_smoke import UP,sha,code,definition_nodes
OUT=Path('C:/GADEN_OCB_R2_ARCHIVE/d0_lite_20260930')
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
def tsv(path,rows):
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
def main():
    freeze=json.loads((ROOT/'freeze/D0_LITE_PRE_TARGET_FREEZE.json').read_text());case=freeze['case'];run=OUT/case['run_id']/'on'
    dest=OUT/'results';dest.mkdir(exist_ok=False)
    execution=json.loads((run/'execution_status.json').read_text());assert execution['status']=='NATIVE_REPLAY_RETURNED',execution
    status=json.loads((run/'run_status.json').read_text())
    receipt=json.loads((run/'map_receipt.json').read_text());h,w=receipt['height'],receipt['width'];res=receipt['resolution']
    origin={k:receipt['origin'][k] for k in ['x','y']};occupancy=np.array(receipt['data'],np.float32).reshape(h,w)
    assert np.array_equal(receipt['origin_quaternion'],[0,0,0,1]),'rotated map not supported by official adapter'
    beliefs=[json.loads(s) for s in (run/'beliefs.jsonl').read_text().splitlines() if s.strip()]
    beliefs=[b for b in beliefs if 0<=b['time_s']<=300 and 0<=b['search_time_s']<=300]
    assert beliefs and np.isfinite(beliefs[-1]['estimate_xy']).all()
    trace=[]
    for idx,b in enumerate(beliefs):
        full=np.asarray(b['source_map'],dtype='<f8');assert np.isfinite(full).all();nx,ny=b['width'],b['height']
        free=np.asarray(b['free_cells'],int);assert free.ndim==1
        cells=np.column_stack([free%nx,free//nx])
        # Native source_map storage is x + y*width; use only free_cells for diagnostics.
        probs=full[free];assert (probs>=0).all() and probs.sum()>0
        coords=np.array([b['origin_x'],b['origin_y']])+b['resolution']*(cells+.5)
        normalized=probs/probs.sum();mean=(normalized[:,None]*coords).sum(axis=0);peak=coords[int(probs.argmax())]
        entropy=-float(np.sum(normalized[normalized>0]*np.log(normalized[normalized>0])))
        trace.append(dict(update_id=idx,stage=b['stage'],physical_time_s=b['time_s'],search_time_s=b['search_time_s'],
            native_expected_x=b['estimate_xy'][0],native_expected_y=b['estimate_xy'][1],MAP_x=float(peak[0]),MAP_y=float(peak[1]),
            full_mean_x=float(mean[0]),full_mean_y=float(mean[1]),entropy=entropy,candidate_count=len(cells),
            source_probability_sha256=hashlib.sha256(full.tobytes()).hexdigest(),scientific_random_stream_digest=b.get('scientific_random_stream_digest','NOT_AVAILABLE')))
    tsv(dest/'source_estimate_trace.tsv',trace);last=beliefs[-1];native=np.asarray(last['estimate_xy'],float)
    np.save(dest/'native_source_posterior_300s.npy',np.asarray(last['source_map'],dtype='<f8'),allow_pickle=False)
    dump(dest/'native_posterior_metadata.json',{k:last[k] for k in ['width','height','resolution','origin_x','origin_y','free_cells','stage','time_s','search_time_s']})
    raw=[json.loads(s) for s in (run/'events_raw.jsonl').read_text().splitlines() if s.strip()]
    raw=[e for e in raw if 0<=e['physical_time_s']<=300]
    events=[];table=[]
    for idx,e in enumerate(raw):
        assert e['run_id']==case['run_id'] and 0<=e['window_start_s']<=e['window_end_s']<=300
        assert len(e['gas_samples_ppm'])==10 and np.isfinite(e['gas_samples_ppm']).all()
        assert np.isfinite(e['xyz']+e['quaternion_xyzw']).all()
        speed=e['local_wind_speed_used_m_s'];direction=e['map_downwind_direction_used_rad']
        angle=device_clockwise_degree([speed*math.cos(direction),speed*math.sin(direction)],e['quaternion_xyzw'])
        if angle is not None and abs(angle-round(angle))<1e-10:angle=float(round(angle))
        events.append(dict(timestamp_s=e['physical_time_s'],x=e['xyz'][0],y=e['xyz'][1],encounter=e['hit'],
            event_id=str(idx),quaternion_xyzw=e['quaternion_xyzw'],official_wind_clockwise_deg=angle))
        table.append(dict(run_id=case['run_id'],event_id=idx,measurement_cycle_id=e['measurement_cycle_id'],
            physical_time_s=e['physical_time_s'],window_start_s=e['window_start_s'],window_end_s=e['window_end_s'],
            x=e['xyz'][0],y=e['xyz'][1],z=e['xyz'][2],quaternion_xyzw=json.dumps(e['quaternion_xyzw']),
            gas_units='ppm',gas_used_ppm=e['gas_value_used_ppm'],threshold_ppm=e['gas_threshold_ppm'],hit=int(e['hit']),
            raw_gas_samples_ppm=json.dumps(e['gas_samples_ppm']),local_wind_speed_m_s=speed,map_downwind_direction_rad=direction,
            official_clockwise_deg=angle,validity='finite completed block',dropout='callback acceptance only; publication drops not measurable'))
    assert table,'no completed Native events'
    tsv(dest/'events.tsv',table);dump(dest/'adapter_events_source_blind.json',events)
    x,meta=channels(occupancy,res,origin,events);np.save(dest/'unet_three_channel_input.npy',x,allow_pickle=False)
    meta.update(map_receipt_sha256=sha(run/'map_receipt.json'),event_log_sha256=sha(run/'events_raw.jsonl'),
        resolution=res,origin=origin,width=w,height=h,source_truth_in_input=False,unvisited_concentration_queries=0)
    dump(dest/'adapter_input_audit.json',meta)
    # Load EXACT upstream definitions, not a replacement network.
    nodes=definition_nodes(code('GSLInference.ipynb',2),ast.ClassDef)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<official-unet-definitions>','exec'),globals())
    os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8';torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    assert torch.cuda.is_available();device=torch.device('cuda')
    weights=[];outputs=[]
    for item in freeze['weights']:
        path=UP/'model'/item['file'];assert sha(path)==item['sha256']
        ts=time.perf_counter();state=torch.load(path,map_location='cpu',weights_only=True)
        nchan=int(state['inc.double_conv.0.weight'].shape[1]);assert nchan==item['input_channels']
        model=UNet(nchan,1);model.load_state_dict(state,strict=True);model.to(device).eval();load_s=time.perf_counter()-ts
        if nchan==3:inp=x
        else:
            marked_map=x[0].copy();marked_map[x[2]>0]=233
            inp=np.stack([marked_map,x[1]])
        tx=torch.from_numpy(inp).unsqueeze(0).to(device);torch.cuda.synchronize();ts=time.perf_counter()
        with torch.inference_mode():prediction=model(tx)
        torch.cuda.synchronize();latency=time.perf_counter()-ts
        with torch.inference_mode():repeat=model(tx)
        assert torch.equal(prediction,repeat),'inference byte repeat'
        out=prediction[0,0].cpu().numpy();loc=location(out,res,origin,h,w)
        name=item['file'].replace('.pth','');np.save(dest/(name+'_likelihood.npy'),out,allow_pickle=False)
        np.save(dest/(name+'_input.npy'),inp,allow_pickle=False)
        peak_i=int(round((loc['peak_xy'][1]-origin['y'])/res));peak_j=int(round((loc['peak_xy'][0]-origin['x'])/res))
        peak_blocked=bool(occupancy[peak_i,peak_j]>0)
        weights.append(dict(weight=item['file'],weight_sha256=item['sha256'],input_channels=nchan,estimate=loc,
            inference_runtime_s=latency,weight_load_and_GPU_transfer_s=load_s,repeat_byte_equal=True,peak_in_obstacle=peak_blocked,
            output_sum=float(out[:h,:w].sum()),mass_in_obstacles_fraction=float(out[:h,:w][occupancy>0].sum()/out[:h,:w].sum()),
            input_semantics='audited three channels' if nchan==3 else 'upstream commented two-channel marked-map+wind; checkpoint provenance ambiguous'))
        outputs.append(out[:h,:w]);del model,state,tx,prediction,repeat;torch.cuda.empty_cache()
    # Truth is first used HERE, after every frozen checkpoint prediction has been saved.
    truth=np.array([float(case['source_x']),float(case['source_y'])]);native_error=float(np.linalg.norm(native-truth))
    for r in weights:
        error=float(np.linalg.norm(np.asarray(r['estimate']['centroid_xy'])-truth));r['XY_error_m']=error
        r['peak_error_m']=float(np.linalg.norm(np.asarray(r['estimate']['peak_xy'])-truth))
        r['engineering_label']=('D0_LITE_ZERO_SHOT_TRANSFER_POOR' if r['peak_in_obstacle'] or error>native_error+.5 else
            'D0_LITE_DL_PROMISING' if error<native_error-.5 else 'D0_LITE_DL_PLAUSIBLE')
    compatible=[r for r in weights if r['input_channels']==3];labels=[r['engineering_label'] for r in compatible]
    decision=('D0_LITE_DL_PROMISING' if all(v=='D0_LITE_DL_PROMISING' for v in labels) else
        'D0_LITE_ZERO_SHOT_TRANSFER_POOR' if all(v=='D0_LITE_ZERO_SHOT_TRANSFER_POOR' for v in labels) else 'D0_LITE_DL_PLAUSIBLE')
    def summary(rs):
        vals=[r['XY_error_m'] for r in rs];return dict(mean=float(np.mean(vals)),range=[min(vals),max(vals)])
    result=dict(decision=decision,scope='single-case engineering transfer screen; no performance generalization',case=case,
        truth_xy=truth.tolist(),PMFS_estimate_xy=native.tolist(),PMFS_error_m=native_error,PMFS_MAP_xy=[trace[-1]['MAP_x'],trace[-1]['MAP_y']],
        native_stop_reason=status['status'],native_last_available_belief_s=last['time_s'],budget_s=300,event_count=len(events),
        hit_events=sum(e['encounter'] for e in events),unique_encounter_pixels=meta['visited_positive_pixels'],weights=weights,
        primary_weight=None,three_channel_error_summary=summary(compatible),all_four_error_summary=summary(weights),
        deterministic_inference_repeat=True,GPU=torch.cuda.get_device_name(0),torch=torch.__version__,
        new_plumes=0,native_target_replays=1,formal_OFF_ON_parity='NOT_EXECUTED; D1A PAUSED',training_steps=0,
        confirmation_read=False,house03_read=False,no_second_case=True,
        caveats=['all-four weight semantics not uniquely documented','Native uses full field state0 forward wind; network only encounter-local wind',
                 'single case cannot decide overall deep-learning or PMFS performance'])
    dump(dest/'D0_LITE_RESULT.json',result)
    extent=[origin['x'],origin['x']+w*res,origin['y'],origin['y']+h*res]
    with (run/'sim_pose_trace.csv').open() as f:poses=[r for r in csv.DictReader(f) if float(r['t_sim_s'])<=300]
    xy=np.array([[float(r['x']),float(r['y'])] for r in poses]);hits=np.array([[e['x'],e['y']] for e in events if e['encounter']])
    nx,ny=last['width'],last['height'];posterior=np.zeros((ny,nx));full=np.array(last['source_map'])
    for index in last['free_cells']:posterior[index//nx,index%nx]=full[index]
    pextent=[last['origin_x'],last['origin_x']+nx*last['resolution'],last['origin_y'],last['origin_y']+ny*last['resolution']]
    panels=[(occupancy,extent,'Occupancy / actual trajectory'),(posterior,pextent,f'Native belief: {native_error:.3f} m'),
        (x[1,:h,:w],extent,'Encounter-local wind channel'),(x[2,:h,:w],extent,'Encounter channel')]
    panels +=[(o,extent,f"{r['weight']}\ncentroid error {r['XY_error_m']:.3f} m") for o,r in zip(outputs,weights)]
    fig,axs=plt.subplots(2,4,figsize=(19,11),constrained_layout=True)
    for idx,(ax,(image,ex,title)) in enumerate(zip(axs.ravel(),panels)):
        im=ax.imshow(image,origin='lower',extent=ex,aspect='equal',interpolation='nearest');ax.set_title(title)
        ax.scatter(*truth,marker='*',s=120,color='red',label='Truth (evaluation only)');ax.plot(xy[:,0],xy[:,1],color='cyan',lw=.7)
        if len(hits):ax.scatter(hits[:,0],hits[:,1],s=12,color='lime')
        if idx==1:ax.scatter(*native,marker='x',color='orange',s=80)
        elif idx>=4:ax.scatter(*weights[idx-4]['estimate']['centroid_xy'],marker='x',color='orange',s=80)
        ax.set_xlabel('map x (m)');ax.set_ylabel('map y (m)');fig.colorbar(im,ax=ax,shrink=.7)
    fig.savefig(dest/'D0_LITE_MAPS_AND_TRAJECTORY.png',dpi=150);plt.close(fig)
    lines=['# D0-Lite single-case zero-shot replay',f"Decision: `{decision}`",'',f"Run: `{case['run_id']}`; {case['house']} / {case['wind_id']}; immutable GADEN seed {case['master_seed']}.",
        f"Truth XY {truth.tolist()}; Native top5% XY {native.tolist()}; error {native_error:.6f} m.",
        f"Native termination {status['status']}; final available belief at {last['time_s']:.6f} s, maximum budget300s.",
        f"{len(events)} completed events; {result['hit_events']} hits; {result['unique_encounter_pixels']} unique encounter pixels.",'',
        '| checkpoint | channels | centroid XY | XY error m | peak error m | inference s |','|---|---:|---|---:|---:|---:|']
    for r in weights:lines.append(f"| {r['weight']} | {r['input_channels']} | {r['estimate']['centroid_xy']} | {r['XY_error_m']:.6f} | {r['peak_error_m']:.6f} | {r['inference_runtime_s']:.6f} |")
    lines +=['','No primary/best checkpoint selected. Four checkpoint outputs are retained; two-channel semantic ambiguity remains explicit.',
        'No training, no new GADEN, no second case, no confirmation/H03. Formal logger OFF/ON parity was waived for this engineering pilot; D1A remains paused.',
        'This single-case screen does not establish U-Net superiority or deep-learning failure. Native consumes full-field state0 forward wind; U-Net receives encounter-local measured wind only.',
        'STOP after packaging.']
    (dest/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
