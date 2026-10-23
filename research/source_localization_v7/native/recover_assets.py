"""R0/R1: only the eight explicitly open worlds; no propagation or sealed data."""
from pathlib import Path
import csv, hashlib, json, os, subprocess, sys, time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/native_20261023'
PROTO = ROOT / 'native/NATIVE_RUN_PROTOCOL_20261023.json'
OCC = Path('D:/ZYC/A-gas/workspace/GADEN_files/scenarios/House01/OccupancyGrid3D.csv')
WIND = OCC.parent / 'wind_simulations/1,3-2,4_fast'
EXPECTED_OCC = '846003ffbbc8e99aa322cf189356399412763710e937bb5e5316186afccf17cb'

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1<<20), b''): h.update(b)
    return h.hexdigest()

def write(name, value):
    p=OUT/name; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def run_path(run):
    if run not in json.loads(PROTO.read_text())['authorized_runs']:
        raise PermissionError('run not in exact open allowlist')
    base='s2x_matched_source' if '_s2x_' in run else 's2_discovery'
    return Path('C:/GADEN_OCB_R2_ARCHIVE')/base/run

def occupancy():
    assert sha(OCC)==EXPECTED_OCC
    lines=OCC.read_text().splitlines()
    dims=np.array(list(map(int,lines[2].split()[1:])))
    origin=np.array(list(map(float,lines[0].split()[1:])),dtype=np.float32)
    cell=np.float32(lines[3].split()[1])
    rows=[[int(v) for v in x.split()] for x in lines[4:] if x!=';']
    a=np.array(rows,dtype=np.uint8).reshape(dims[2],dims[0],dims[1])
    return dims,origin,cell,a

def geometry_receipt(points):
    dims,origin,cell,a=occupancy(); records=[]
    for p in points:
        p=np.asarray(p,dtype=np.float32)
        index=np.floor((p-origin)/cell).astype(int)
        inside=bool(np.all(index>=0) and np.all(index<dims))
        value=int(a[index[2],index[0],index[1]]) if inside else 3
        records.append({'point_m':p.astype(float).tolist(),'index_xyz':index.tolist(),
                        'native_cell':value,'legal_free':inside and value==0})
    return records

def main():
    started=time.time(); OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'INPUT_FREEZE.json').exists(): raise RuntimeError('freeze already exists')
    protocol=json.loads(PROTO.read_text())
    write('INPUT_FREEZE.json',{'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
          'protocol_sha256':sha(PROTO),'protocol':protocol,
          'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          'upstream_source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'src').rglob('*.py'))},
          'first_failures_retained':['WSL Ubuntu-22.04 startup: ERROR_FILE_NOT_FOUND for its pre-existing ext4.vhdx; no data/distro modification',
          'Initial format probe tried legacy zlib; failed header check; actual frame has GADEN_RESULT modern header and mode=ZLIB; diagnostic only, no science scoring']})
    records=[]; all_ok=True; timelines=[]
    for run in protocol['authorized_runs']:
        p=run_path(run); manifest=json.loads((p/'RUN_MANIFEST.json').read_text())
        assert manifest['run_id']==run and manifest['house']=='House01'
        assert manifest['asset_checks']['occupancy_sha256']==EXPECTED_OCC
        with (p/'OUTPUT_SHA256SUMS.tsv').open(newline='') as f: expected=list(csv.DictReader(f,delimiter='\t'))
        rows=[]
        for r in expected:
            f=p/r['name']; ok=f.exists() and f.stat().st_size==int(r['size_bytes']) and sha(f)==r['sha256']
            rows.append({'name':r['name'],'size_bytes':int(r['size_bytes']),'sha256':r['sha256'],'match':ok})
        with (p/'RECORD_TIMELINE.tsv').open(newline='') as f: timeline=list(csv.DictReader(f,delimiter='\t'))
        t=np.array([float(r['internal_simulation_time_s']) for r in timeline])
        idx=np.flatnonzero((t>=50)&(t<=70))
        assert len(idx)>=3 and np.all(np.diff(t)>0)
        assert sha(p/'RECORD_TIMELINE.tsv')==manifest['qualification_standard']['timeline_sha256']
        timelines.append(sha(p/'RECORD_TIMELINE.tsv'))
        wm=[{'path':str(f),'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted((p/'wind').glob('wind_iteration_*'))]
        data={'run_id':run,'root':str(p),'manifest_sha256':sha(p/'RUN_MANIFEST.json'),
              'source_xyz':[float(manifest['simulation_parameters']['source_position_'+v]) for v in 'xyz'],
              'master_seed':manifest['master_seed'],'timeline_sha256':sha(p/'RECORD_TIMELINE.tsv'),
              'frame_count':len(t),'first_time_s':float(t[0]),'last_time_s':float(t[-1]),
              'window_indices':[int(timeline[i]['record_index']) for i in idx],
              'window_times_s':t[idx].tolist(),'window_max_step_s':float(np.diff(t[idx]).max()),
              'files':rows,'wind':wm,'all_frames_match':all(x['match'] for x in rows)}
        write('assets/'+run+'.json',data);records.append({k:v for k,v in data.items() if k not in ('files','wind')})
        all_ok &= data['all_frames_match']
        print('VERIFIED',run,len(rows),len(idx),flush=True)
    assert all_ok and len(set(timelines))==1
    sources=geometry_receipt(protocol['source_xyz_m'])
    with (ROOT/'evidence/discovery/ocb_r2/metadata/E1_HOUSE_PROBE_CONTRACTS.tsv').open(newline='') as f:
        probes=[r for r in csv.DictReader(f,delimiter='\t') if r['house']=='House01']
    pair=[probes[k-1] for k in protocol['pair_original_probe_ranks']]
    pts=[]
    for p in pair:
        for ix in range(int(p['native_x0']),int(p['native_x1_exclusive'])):
            for iy in range(int(p['native_y0']),int(p['native_y1_exclusive'])):
                # Original extractor uses float32 arithmetic for cell centres.
                ox=np.float32(-7.55);oy=np.float32(-7.88);c=np.float32(.1)
                pts.append([float(ox+(np.float32(ix)+np.float32(.5))*c),float(oy+(np.float32(iy)+np.float32(.5))*c),.2])
    receivers=geometry_receipt(pts)
    write('GEOMETRY_QUALIFICATION.json',{'occupancy_path':str(OCC),'occupancy_sha256':sha(OCC),
          'sources':sources,'receivers':receivers,'all_legal':all(r['legal_free'] for r in sources+receivers),
          'negative_z_alone_not_invalid':True,'source_birth_neighborhood':'requires point-source implementation and actual frame audit; not inferred from centre only',
          'readout':'two fixed spatial pools, not a flown UAV trajectory'})
    # Restore only the exact 16 allowed reference arrays, using pinned Git blobs.
    manifest=json.loads((ROOT/'src/gsl_discrimination/data/ocb_x00_manifest.json').read_text())
    cache=ROOT/'local_assets/ocb_x00/raw';cache.mkdir(parents=True,exist_ok=True)
    restores=[]
    for w in manifest['worlds']:
        assert w['run_id'] in protocol['authorized_runs']
        for kind in ('cube','pooled'):
            spec=w['files'][kind];name=spec['filename'];dst=cache/name
            blob=subprocess.check_output(['git','show',manifest['commit']+':'+spec['remote_path']],cwd=ROOT)
            assert len(blob)==spec['size_bytes'] and hashlib.sha256(blob).hexdigest()==spec['sha256']
            assert hashlib.sha1(('blob '+str(len(blob))+'\0').encode()+blob).hexdigest()==spec['git_blob_sha']
            dst.write_bytes(blob);restores.append({'name':name,'bytes':len(blob),'sha256':sha(dst)})
    write('REFERENCE_RESTORATION.json',{'files':restores,'from_pinned_git':manifest['commit'],
          'sealed_content_read':False,'raw_reference_arrays_excluded_from_final_zip':True})
    write('R0_INPUT_RESULT.json',{'status':'RAW_FILES_HASH_AND_POINT_GEOMETRY_VERIFIED',
          'world_count':len(records),'frame_count':sum(r['frame_count'] for r in records),
          'all_frames_match':all_ok,'sources_and_pools_legal':all(r['legal_free'] for r in sources+receivers),
          'worlds':records,'duration_s':time.time()-started,'new_propagation_steps':0})

if __name__=='__main__': main()
