"""Restore occupancy and construct observed-only prefixes; no target inference."""
import ast,csv,hashlib,json,math,re,sys
from pathlib import Path
import numpy as np
from audit_open49 import ROOT,OUT,CACHE,load,dump,sha,rows
METHOD=Path(r'D:\ZYC\Topography-aware-Gas-Source')
sys.path.insert(0,str(METHOD/'comparison_work/vgr_adapter'))
sys.path.insert(0,str(METHOD/'d1a_common_replay'))
from official_three_channel import channels,official_functions
from wind_parity import device_clockwise_degree

def main():
    audit=load(OUT/'OPEN49_RAW_AUDIT.json');report=[];prefixes=[];maps={};f=official_functions()
    # Reconstruct the exact binary altitude slice used by VGR, verified against its archived log hash.
    for house in ['House01','House02']:
        p=CACHE/'map_inputs'/f'{house}_OccupancyGrid3D.csv';meta={};vals=[]
        for line in p.read_text(encoding='utf-8').splitlines():
            if line.startswith('#'):meta[line.split()[0]]=line.split()[1:]
            elif line.strip() and line.strip()!=';':vals.extend(int(v) for v in line.split())
        dims=list(map(int,meta['#num_cells']));origin3=list(map(float,meta['#env_min(m)']));res=float(meta['#cell_size(m)'][0])
        zidx=int((.2-origin3[2])/res);a=(np.array(vals).reshape(dims[2],dims[0],dims[1])[zidx]!=0).T.astype(np.float32)*100
        maps[house]=(a,float(np.float32(res)),{'x':origin3[0],'y':origin3[1]},sha(p),zidx)
        np.save(CACHE/f'{house}_occupancy.npy',a,allow_pickle=False)
    for t in audit['trajectories']:
        leaf=Path(t['raw_cache']);log=(leaf/'launch.log').read_text(encoding='utf-8',errors='replace');bind=load(leaf/'runtime_binding.json');final=load(leaf/'case_result.json')
        a,res,origin,digest,zidx=maps[t['house']];h,w=a.shape
        occmatch=f'input_sha256={digest}' in log and f'slice z_idx={zidx} (z=0.2m)' in log
        intersection=re.search(r'Sensor-safe occupancy intersection: (\d+)x(\d+) min=\[([^]]+)\]',log)
        cropmatch=intersection is not None and [int(intersection[1]),int(intersection[2])]==[w,h] and np.allclose([float(v) for v in intersection[3].split(',')],[origin['x'],origin['y']],atol=1e-10)
        events=rows((leaf/'measurement_events.csv').read_bytes());blocks=rows((leaf/'measurement_blocks.csv').read_bytes());pose=rows((leaf/'sim_pose_trace.csv').read_bytes());times=np.array([float(p['t_sim_s']) for p in pose]);observed=[];maxpose=0.;maxdt=0.;hitn=0;errors=[]
        for ev,block in zip(events,blocks):
            ts=float(block['sim_time_end']);ix=int(np.searchsorted(times,ts+1e-6,side='right'))-1
            if ix<0:errors.append('no causal actual pose');continue
            p=pose[ix];dist=math.hypot(float(p['x'])-float(ev['robot_x']),float(p['y'])-float(ev['robot_y']));maxpose=max(maxpose,dist);maxdt=max(maxdt,ts-times[ix])
            if dist>1e-3:errors.append('event and causal pose differ');continue
            yaw=float(p['yaw']);quat=[0.,0.,math.sin(yaw/2),math.cos(yaw/2)];speed=float(ev['wind_speed']);ang=float(ev['wind_direction']);flow=[speed*math.cos(ang),speed*math.sin(ang)]
            deg=device_clockwise_degree(flow,quat)
            if deg is not None and abs(deg-round(deg))<1e-10:deg=float(round(deg))
            event=dict(timestamp_s=ts,x=float(ev['robot_x']),y=float(ev['robot_y']),encounter=bool(int(ev['hit'])),event_id=ev['event_id'],quaternion_xyzw=quat,official_wind_clockwise_deg=deg)
            observed.append(event)
        positive=[e for e in observed if e['encounter']];leafout=CACHE/'prepared'/t['case_id'];leafout.mkdir(parents=True,exist_ok=True)
        if occmatch and cropmatch and not errors and maxdt<=.200001:
            mapch=np.pad(a,((0,279-h),(0,279-w)),constant_values=-1)
            windch=np.zeros((279,279));hitmask=np.zeros((279,279))
            # N is the actual encounter-event prefix count, not a new independent realization.
            for hitn,event in enumerate(positive,1):
                ix,iy=f['convert_coordinates'](event['x'],event['y'],res,origin)
                assert 0<=ix<w and 0<=iy<h
                hitmask[iy,ix]=1
                if event['official_wind_clockwise_deg'] is not None:
                    radians=f['sensor_direction_in_world'](*event['quaternion_xyzw'],-np.radians(int(event['official_wind_clockwise_deg'])))
                    raster=np.zeros((279,279));raster[iy,ix]=1
                    windch+=f['mark_wind_direction'](raster,radians)
                x=np.stack([mapch,windch,hitmask]).astype(np.float32)
                yy,xx=np.indices(a.shape);gx,gy=final['truth_xy'];d=3*math.exp(-.3*(hitn-1))+1
                distance=np.hypot(origin['x']+res*xx-gx,origin['y']+res*yy-gy)
                label=np.where(distance>d,0,((d-distance)/d)*(100-a)/100)
                # Official label writer uses %.2f. Preserve that quantization, not np.round.
                label=np.array([[float(f'{v:.2f}') for v in row] for row in label],np.float32)
                label=np.pad(label,((0,279-h),(0,279-w)))
                dest=leafout/f'prefix_{hitn:03d}.npz';np.savez_compressed(dest,x=x,label=label)
                split='validation' if t['historical_split']=='dev' else 'train'
                prefixes.append(dict(case_id=t['case_id'],physical_seed=t['physical_seed'],house=t['house'],source_id=t['source_id'],wind=t['wind'],prefix_encounters=hitn,measurement_event_id=event['event_id'],timestamp_s=event['timestamp_s'],split=split,path=str(dest),sha256=sha(dest)))
        r=dict(case_id=t['case_id'],house=t['house'],source_id=t['source_id'],wind=t['wind'],physical_seed=t['physical_seed'],
            occupancy_sha256=digest,map_dimensions=[h,w],resolution=res,origin=origin,occupancy_logged_hash_match=occmatch,logged_crop_match=cropmatch,
            max_pose_difference_m=maxpose,max_causal_pose_age_s=maxdt,causal_pose_error_count=len(errors),positive_prefixes=len(positive),
            no_encounter_trajectory=len(positive)==0,split='validation' if t['historical_split']=='dev' else 'train',truth_xy=final['truth_xy'],
            raw_event_sha256=sha(leaf/'measurement_events.csv'),raw_block_sha256=sha(leaf/'measurement_blocks.csv'),raw_pose_sha256=sha(leaf/'sim_pose_trace.csv'),
            runtime_sha256=sha(leaf/'runtime_binding.json'),launch_sha256=sha(leaf/'launch.log'),ready=t['ready'] and occmatch and cropmatch and not errors and maxdt<=.200001)
        dump(leafout/'OBSERVED_EVENTS.json',observed);report.append(r)
    ready=all(r['ready'] for r in report) and any(p['split']=='train' for p in prefixes) and any(p['split']=='validation' for p in prefixes)
    result=dict(decision='OPEN49_TRAINABLE' if ready else 'OPEN49_NOT_TRAINABLE',physical_trajectories=49,by_house=audit['by_house'],
        positive_prefixes=len(prefixes),rotations_per_prefix=4,augmented_samples=4*len(prefixes),
        zero_encounter_trajectories=sum(r['no_encounter_trajectory'] for r in report),zero_encounter_handling='invent no positive prefix; retained in inventory, no official encounter-index label',
        grouped_split='Preserve historical train/dev source grouping; extra historical OPEN H02 source joins training. All prefixes and rotations from a physical plume stay together.',
        train_prefixes=sum(p['split']=='train' for p in prefixes),validation_prefixes=sum(p['split']=='validation' for p in prefixes),
        current_target_excluded=True,confirmation_read=False,house03_read=False,new_simulation=0,
        map_semantics='Exact binary VGR altitude slice z=.2; occupancy SHA and no-crop dimensions independently checked in every archived launch log. Current target z=.3 remains a documented domain difference.',
        label_semantics='Exact upstream triangular radial label, N actual completed positive measurement events, literal %.2f quantization, occupancy masking; padding=0.',
        train_padding=-1,inference_padding=0,trajectories=report)
    dump(OUT/'OPEN49_TRAINABILITY.json',result);dump(OUT/'PREFIX_MANIFEST.json',prefixes)
    print({k:v for k,v in result.items() if k!='trajectories'})
    for r in report:
        if not r['ready']:print('NOT_READY',r['case_id'],r)
if __name__=='__main__':main()
