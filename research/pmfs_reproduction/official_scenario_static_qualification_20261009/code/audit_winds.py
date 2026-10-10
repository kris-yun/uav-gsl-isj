from pathlib import Path
import json,subprocess,hashlib,io,csv
import numpy as np

root=Path(__file__).resolve().parents[2]
out=root/'outputs/PMFS_OFFICIAL_SCENARIO_STATIC_QUALIFICATION_20261009'
repo='D:/ZYC/A-gas/_reference_native_pmfs_upstream_20260923'
pin='4e141e162551e674f2f30ddb8859136c72139aac'
data=json.loads((out/'OFFICIAL_PMFS_CONFIG_RAW.json').read_text())
assets=json.loads((out/'RAW_ASSET_HASHES.json').read_text())
groups=json.loads((out/'WIND_NUMERICAL_AUDIT.json').read_text()) if (out/'WIND_NUMERICAL_AUDIT.json').exists() else []
groups=[g for g in groups if not (g['group'].endswith('Exp_C\\wind_simulations') and len(g['frames'])>1)]
def analyze_group(key,frames,get_bytes,metadata):
    frames=sorted(frames,key=lambda n:int(Path(n).stem.split('_')[-1]))
    results=[];reference=None;coords=None
    for n in frames:
        b=get_bytes(n)
        if 'outdoors' in n:
            a=np.loadtxt(io.BytesIO(b),delimiter=',')
            assert a.ndim==2 and a.shape[1]==3 and np.all(np.isfinite(a))
            return dict(group=key,source=metadata,frames=[dict(path=n,frame_index=0,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),
                format='UNIFORM_VECTOR_ROWS_NOT_SPATIAL_CFD_FRAME',numeric_rows=a.tolist())],
                unique_velocity_numeric_fields=None,observed_numerical_variation=None,
                physical_time_contract='Vector rows differ numerically inside one file; loader row/time meaning is unqualified here. Do not claim a qualified time-varying spatial field.')
        header=next(csv.reader(io.StringIO(b.decode().splitlines()[0])))
        a=np.loadtxt(io.BytesIO(b),delimiter=',',skiprows=1)
        assert a.ndim==2 and a.shape[1]>=6 and np.all(np.isfinite(a)),n
        normalized=[x.strip('" ').lower().replace('u [m/s]','u') for x in header]
        if all('u:'+str(k) in normalized for k in range(3)):
            ui=[normalized.index('u:'+str(k)) for k in range(3)]
            xi=[normalized.index('points:'+str(k)) for k in range(3)]
        else:raise ValueError((n,header))
        velocity=a[:,ui].copy();xyz=a[:,xi].copy()
        if reference is None:reference=velocity;coords=xyz
        assert xyz.shape==coords.shape,n
        same_coords=np.array_equal(xyz,coords)
        difference=velocity-reference if same_coords else None
        speed=np.linalg.norm(velocity,axis=1)
        fields=dict(path=n,frame_index=int(Path(n).stem.split('_')[-1]),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),
            rows=len(a),velocity_numeric_sha256=hashlib.sha256(velocity.astype('<f8').tobytes()).hexdigest(),
            coordinates_equal_reference=same_coords,velocity_equal_reference=bool(np.array_equal(velocity,reference)) if same_coords else None,
            changed_velocity_rows=int(np.count_nonzero(np.any(difference!=0,axis=1))) if same_coords else None,
            max_velocity_difference_m_s=float(np.max(np.abs(difference))) if same_coords else None,
            mean_velocity_xyz=velocity.mean(axis=0).tolist(),max_speed_m_s=float(speed.max()),
            median_speed_m_s=float(np.median(speed)),vertical_velocity_max_abs_m_s=float(np.max(np.abs(velocity[:,2]))))
        inds=np.unique(np.concatenate([np.linspace(0,len(a)-1,12,dtype=int),[int(np.argmax(speed))],
            [int(np.argmax(np.linalg.norm(difference,axis=1)))] if same_coords else []]))
        fields['raw_numeric_probes']=[dict(row=int(i),xyz=xyz[i].tolist(),velocity=velocity[i].tolist()) for i in inds]
        results.append(fields)
        print(key,fields['frame_index'],fields['changed_velocity_rows'],flush=True)
    return dict(group=key,source=metadata,frames=results,unique_velocity_numeric_fields=len(set(r['velocity_numeric_sha256'] for r in results)),
        observed_numerical_variation=any(r['velocity_equal_reference'] is False for r in results),
        physical_time_contract='Must use configured wind interval plus generated gas/header timing; raw CSV index is not an observation timestamp')

for key,frames in data['wind_groups'].items():
    if any(g['group']==key for g in groups):continue
    def read(n):
        b=subprocess.check_output(['git','-C',repo,'show',pin+':'+n])
        assets.append(dict(provider='GSL_FIXED_GIT_OBJECT',repository=repo,revision=pin,path=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
        return b
    groups.append(analyze_group(key,frames,read,dict(repository=repo,revision=pin,wind_interval_s=1)))
    (out/'WIND_NUMERICAL_AUDIT.json').write_text(json.dumps(groups,indent=2),encoding='utf-8')
    (out/'RAW_ASSET_HASHES.json').write_text(json.dumps(assets,indent=2),encoding='utf-8')
gaden=root/'work/pmfs_r5/GADEN'
testgroups={}
for f in (gaden/'test_env/scenarios').rglob('*.csv'):
    if 'wind_simulations' in f.parts:
        key=str(f.parent/f.stem.rsplit('_',1)[0]) if 'Exp_C' in f.parts else str(f.parent)
        testgroups.setdefault(key,[]).append(str(f))
for key,frames in testgroups.items():
    if any(g['group']==key for g in groups):continue
    def read(n):
        b=Path(n).read_bytes()
        assets.append(dict(provider='LOCAL_PINNED_GADEN_COPY',revision='ccb02e959a45a188e4b6c78792e197633fc64f1c',path=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
        return b
    groups.append(analyze_group(key,frames,read,dict(repository=str(gaden),revision='ccb02e959a45a188e4b6c78792e197633fc64f1c',wind_interval_s=1)))
    (out/'WIND_NUMERICAL_AUDIT.json').write_text(json.dumps(groups,indent=2),encoding='utf-8')
    (out/'RAW_ASSET_HASHES.json').write_text(json.dumps(assets,indent=2),encoding='utf-8')
(out/'WIND_NUMERICAL_AUDIT.json').write_text(json.dumps(groups,indent=2),encoding='utf-8')
(out/'RAW_ASSET_HASHES.json').write_text(json.dumps(assets,indent=2),encoding='utf-8')
print(json.dumps([dict(group=g['group'],frames=len(g['frames']),unique_numeric=g['unique_velocity_numeric_fields'],varies=g['observed_numerical_variation']) for g in groups]))
