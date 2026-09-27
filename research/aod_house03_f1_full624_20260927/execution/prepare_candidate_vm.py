#!/usr/bin/env python3
"""Geometry/wind-only full-support adapter. Never opens House03 gas results."""
import csv, hashlib, json, shlex, shutil, subprocess
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

R=Path('/home/zyc/aod_house03_f1_full624_20260927')
P=R/'protocol'; I=R/'inputs'; B=R/'build'
D0=Path('/home/zyc/marked_encounter_pmfs_d0_20260927')
N=Path('/home/zyc/native_pmfs_recovery_v1')
GEOM=Path('/tmp/aod_h03_f0_assets_20260927_v4/geometry')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def rows(p):
    return list(csv.DictReader(Path(p).open(), delimiter='\t'))

def dump(p, data):
    p.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')

def main():
    for line in (P/'SHA256SUMS.txt').read_text().splitlines():
        h,name=line.split(None,1);name=name.lstrip('* ')
        assert sha(P/name)==h,name
    assert sha(P/'frozen/HOUSE03_FUTURE_PMFS_SEEDS_FULL624_54912.tsv')=='00bf64ab0d1ce55fda58303b11208019473313b97c4de11f7a2305d16143327d'
    pf=rows(P/'frozen/HOUSE03_FUTURE_PMFS_SEEDS_FULL624_54912.tsv')
    gd=rows(P/'frozen/HOUSE03_FUTURE_GADEN_SEEDS_96.tsv')
    bank={r['source_id']:r for r in rows(P/'frozen/HOUSE03_CANONICAL_SOURCE_GEOMETRY_BANK_624.tsv')}
    assert len(pf)==54912 and len(bank)==624
    assert len({int(r['requested_seed']) for r in pf})==54912
    assert not {r['requested_seed'] for r in pf}&{r['requested_seed'] for r in gd}
    indexed={}
    keys=set()
    for r in pf:
        ix=int(r['source_index']);indexed.setdefault(ix, r)
        assert indexed[ix]['source_id']==r['source_id']
        assert r['seed_sha256']==hashlib.sha256(r['seed_key'].encode()).hexdigest()
        assert int(r['requested_seed'])==1+int(r['seed_sha256'][:16],16)%(2**31-2)
        key=(ix,int(r['wind_state']),int(r['transport_replica_index']))
        assert key not in keys;keys.add(key)
        for coord in ['x_m','y_m','z_m']:
            assert abs(float(r[coord])-float(bank[r['source_id']][coord]))<1e-12
    assert set(indexed)==set(range(624))
    assert keys=={(s,k,r) for s in range(624) for k in range(11) for r in range(8)}
    I.mkdir(exist_ok=False);B.mkdir(exist_ok=False)
    expected={'pruned_meta.json':'cdda9e893a35fb2ee3e094a5d66b23acb1503afc61210f2a038a1117b607c3e5',
              'pruned_seed0.bin':'32d362e73211532547d76f699e957ca3c0f3f6f2b3f6cc4f4fa862cf4f4943d7'}
    for name,h in expected.items(): assert sha(GEOM/name)==h,name
    shutil.copyfile(GEOM/'pruned_meta.json',I/'meta.json')
    shutil.copyfile(GEOM/'pruned_seed0.bin',I/'occupancy.u8')
    meta=json.loads((I/'meta.json').read_text())
    occ=np.fromfile(I/'occupancy.u8',np.uint8)
    assert occ.size==meta['width']*meta['height'] and set(occ)<={0,1}
    with (I/'meta.csv').open('w',newline='') as f:
        w=csv.writer(f);cols=['width','height','resolution','origin_x','origin_y'];w.writerow(cols);w.writerow([meta[c] for c in cols])
    with (I/'sources.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['source_index','source_id','x','y','z','pair_id'])
        for ix in range(624):
            r=indexed[ix];x,y,z=[float(r[c]) for c in ['x_m','y_m','z_m']]
            i=int(np.floor((x-meta['origin_x'])/meta['resolution']))
            j=int(np.floor((y-meta['origin_y'])/meta['resolution']))
            assert occ[i+j*meta['width']]==1 and z==.2
            w.writerow([ix,r['source_id'],r['x_m'],r['y_m'],r['z_m'],r['pair_id']])
    free=np.flatnonzero(occ==1);ij=np.c_[free%meta['width'],free//meta['width']]
    q=np.array([meta['origin_x'],meta['origin_y']])+(ij+.5)*meta['resolution']
    q=np.c_[q,np.full(len(q),.2)];wind_audit=[]
    for r in rows(P/'frozen/HOUSE03_WIND_HASHES_11.tsv'):
        path=Path(r['csv_path']);binary=Path(r['preprocessed_path']);state=int(r['state'])
        assert sha(path)==r['csv_sha256'] and sha(binary)==r['preprocessed_sha256']
        data=np.loadtxt(path,delimiter=',',skiprows=1)
        assert data.shape[1]==6 and np.isfinite(data).all()
        pos=data[:,3:6];dist,two=cKDTree(pos).query(q,k=2);near=two[:,0].copy()
        for n in np.flatnonzero(np.abs(dist[:,1]-dist[:,0])<=1e-12):
            near[n]=int(np.argmin(np.sum((pos-q[n])**2,axis=1)))
        uv=data[near,:2].astype(np.float32)
        dest=I/f'wind_{state}.csv'
        with dest.open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['cell_index','u','v'])
            w.writerows((int(idx),repr(float(u)),repr(float(v))) for idx,(u,v) in zip(free,uv))
        wind_audit.append(dict(state=state,csv_path=str(path),csv_sha256=sha(path),
            binary_path=str(binary),binary_sha256=sha(binary),export_sha256=sha(dest),nearest_rows=near.tolist(),
            query_z_m=.2,semantics='map Cartesian downwind; same historical nearest-row tie rule'))
    provenance=json.loads((D0/'build_provenance.json').read_text())
    assert json.loads((D0/'NATIVE_PARITY.json').read_text())['pass']
    for path,h in provenance['historical_library_sha256'].items(): assert sha(path)==h,path
    # The numerical kernel, occurrence blur and RNG implementation are reused
    # exactly. Only wrapper input ranges expand to 624 candidates and manifest seeds.
    cpp=(D0/'execution/marked_forward.cpp').read_text()
    old='if(source<0||source>=6||state<0||state>=11||seed<1||seed>8)'
    assert cpp.count(old)==1
    cpp=cpp.replace(old,'if(source<0||source>=624||state<0||state>=11||seed<1)')
    wrapper=R/'execution/marked_forward_full624.cpp';wrapper.write_text(cpp)
    flags=[]
    for line in (N/'build/gsl_server/CMakeFiles/native_pmfs_r1_forward_replay.dir/flags.make').read_text().splitlines():
        if line.startswith(('CXX_DEFINES =','CXX_INCLUDES =','CXX_FLAGS =')):
            flags+=shlex.split(line.split('=',1)[1])
    args=shlex.split((N/'build/gsl_server/CMakeFiles/native_pmfs_r1_forward_replay.dir/link.txt').read_text())
    for n,v in enumerate(args):
        if v.endswith('.cpp.o'): args[n]=str(wrapper)
        if n>0 and args[n-1]=='-o': args[n]=str(B/'marked_forward_full624')
    objects=[D0/'build/Simulations_marked.o',D0/'build/Math_seeded.o']
    # Verify these exact observer/RNG sources against the completed D0 provenance.
    for name in ['Simulations_marked.cpp','Math_seeded.cpp']:
        assert sha(D0/'execution'/name)==provenance['patched_source_sha256'][name]
    command=args[:1]+flags+[str(p) for p in objects]+args[1:]
    with (R/'build.log').open('w') as f:
        f.write(shlex.join(command)+'\n');f.flush()
        subprocess.run(command,cwd=N/'build/gsl_server',stdout=f,stderr=subprocess.STDOUT,check=True)
    dump(R/'BUILD_AND_ASSET_AUDIT.json',dict(passed=True,source_support=624,manifest_count=54912,
        geometry_hashes=expected,wind=wind_audit,source_csv_sha256=sha(I/'sources.csv'),
        occurrence_kernel_reused_unchanged=True,native_parity_archived=json.loads((D0/'NATIVE_PARITY.json').read_text()),
        object_hashes={str(p):sha(p) for p in objects},command=command,
        old_wrapper_sha256=sha(D0/'execution/marked_forward.cpp'),wrapper_sha256=sha(wrapper),
        binary_sha256=sha(B/'marked_forward_full624'),fresh_target_generated=False,fresh_target_values_read=False))
    print('FULL624_BUILD_ASSETS_READY',flush=True)

if __name__=='__main__':main()
