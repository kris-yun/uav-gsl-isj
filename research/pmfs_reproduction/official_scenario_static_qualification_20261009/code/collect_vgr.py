from pathlib import Path
import json,os,struct,zlib,hashlib,shutil
import yaml,numpy as np
from audit_utils import source_support,occupancy3d,sha

root=Path(__file__).resolve().parents[2]
out=root/'outputs/PMFS_OFFICIAL_SCENARIO_STATIC_QUALIFICATION_20261009'
bank=Path('D:/ZYC/A-gas/workspace/GADEN_files/scenarios')
assets=[];houses=[];records=[];wind_cache={}
for house in sorted(bank.iterdir()):
    if not house.is_dir() or not house.name.startswith('House'):continue
    geometry={}
    for name in ['occupancy.pgm','occupancy.yaml','OccupancyGrid3D.csv']:
        f=house/name
        if f.exists():
            b=f.read_bytes();geometry[name]=dict(path=str(f),sha256=sha(b),bytes=len(b))
            assets.append(dict(provider='VGR_LOCAL_EXISTING',path=str(f),sha256=sha(b),bytes=len(b)))
            target=out/'evidence/vgr_geometry'/house.name/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
    gas=house/'gas_simulations';found=[]
    if gas.exists():
        for d,sub,files in os.walk(gas):
            if len(Path(d).relative_to(gas).parts)>=3:sub[:]=[]
            frames=sorted(int(n[10:]) for n in files if n.startswith('iteration_') and n[10:].isdigit())
            if not frames:continue
            p=Path(d);samples=[]
            for k in sorted(set([frames[0],frames[len(frames)//2],frames[-1]])):
                f=p/f'iteration_{k}';b=f.read_bytes()
                try:
                    raw=zlib.decompress(b)
                    assert struct.unpack_from('<i',raw)[0]==1
                    h=dict(index=k,format_version=1,dimensions=list(struct.unpack_from('<3i',raw,52)),
                        env_min=list(struct.unpack_from('<3d',raw,4)),env_max=list(struct.unpack_from('<3d',raw,28)),
                        cell_size=list(struct.unpack_from('<3d',raw,64)),source_xyz=list(struct.unpack_from('<3d',raw,88)),
                        gas_type=struct.unpack_from('<i',raw,112)[0],wind_index=struct.unpack_from('<i',raw,132)[0],header_hex=raw[:136].hex(),
                        bytes=len(b),sha256=sha(b),physical_timestamp_in_header=False)
                except (zlib.error,AssertionError,struct.error) as err:
                    h=dict(index=k,sha256=sha(b),bytes=len(b),error=type(err).__name__)
                samples.append(h)
                assets.append(dict(provider='VGR_EXISTING_GAS_SAMPLE',path=str(f),sha256=sha(b),bytes=len(b)))
                if k==frames[0] and len(b)<100_000:
                    target=out/'evidence/vgr_first_frames'/house.name/p.parent.name/p.name/f.name
                    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
            source=samples[0].get('source_xyz');support=None;three=None;winds=[]
            if source and 'occupancy.yaml' in geometry and 'occupancy.pgm' in geometry:
                support=source_support((house/'occupancy.pgm').read_bytes(),yaml.safe_load((house/'occupancy.yaml').read_text()),source)
            if source and 'OccupancyGrid3D.csv' in geometry:three=occupancy3d(house/'OccupancyGrid3D.csv',source)
            if source:
                for wi in sorted({h['wind_index'] for h in samples if 'wind_index' in h}):
                    f=p/'wind'/f'wind_iteration_{wi}'
                    key=str(f)
                    if key not in wind_cache and f.exists():
                        b=f.read_bytes();n=int(np.prod(samples[0]['dimensions']))
                        r=dict(path=key,wind_index=wi,bytes=len(b),sha256=sha(b),header_dimensions=samples[0]['dimensions'])
                        if len(b)==3*n*8:
                            values=np.frombuffer(b,dtype='<f8').reshape(3,n)
                            assert np.all(np.isfinite(values))
                            r.update(format='THREE_DENSE_COMPONENT_ARRAYS_F64_MATCHING_GRID_DIMENSIONS',numeric_sha256=sha(values.tobytes()),
                                component_min=values.min(axis=1).tolist(),component_max=values.max(axis=1).tolist(),
                                nonzero_cells=int(np.count_nonzero(np.any(values!=0,axis=0))),vertical_max_abs_m_s=float(np.max(np.abs(values[2]))))
                        else:r['format']='UNQUALIFIED_BINARY_LAYOUT'
                        wind_cache[key]=r
                        assets.append(dict(provider='VGR_EXISTING_WIND',path=key,sha256=sha(b),bytes=len(b)))
                    if key in wind_cache:winds.append(wind_cache[key])
            sidecars=[]
            for a in [p,p.parent,house/'launch']:
                if not a.exists():continue
                for f in a.iterdir():
                    if f.is_file() and f.suffix in ['.yaml','.yml','.json','.launch','.py','.xml','.txt']:
                        b=f.read_bytes();sidecars.append(dict(path=str(f),sha256=sha(b),bytes=len(b)))
                        assets.append(dict(provider='VGR_EXISTING_SIDECAR',path=str(f),sha256=sha(b),bytes=len(b)))
                        if len(b)<150_000:
                            target=out/'evidence/vgr_sidecars'/house.name/(p.parent.name if a!=house/'launch' else 'launch')/f.name
                            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
            r=dict(id='VGR_'+house.name+'_'+p.parent.name,house=house.name,path=str(p),frames=len(frames),first=frames[0],last=frames[-1],
                sampled_headers=samples,source_xyz=source,source_support=support,occupancy3d=three,wind_samples=winds,
                distinct_sampled_numeric_winds=len(set(x.get('numeric_sha256',x['sha256']) for x in winds)),sidecars=sidecars,
                resolved_generation_contract=False,actual_physical_time_trace=False,raw_ROS_events_attached=False,
                statement='Original binary headers and selected dense wind arrays audited; sampled wind changes are not a qualified continuous physical time sequence.')
            records.append(r);found.append(r['id'])
    houses.append(dict(house=house.name,path=str(house),geometry=geometry,gas_recordings=found))
    print(house.name,'records',len(found),flush=True)
(out/'VGR_LOCAL_STATIC_AUDIT.json').write_text(json.dumps(dict(houses=houses,recordings=records,wind_samples=list(wind_cache.values())),indent=2),encoding='utf-8')
(out/'VGR_ASSET_HASHES.json').write_text(json.dumps(assets,indent=2),encoding='utf-8')
print(json.dumps(dict(houses=len(houses),gas_recordings=len(records),wind_samples=len(wind_cache))))
