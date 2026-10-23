"""Verify already-open OCB-R2 discovery exports; no propagation or new scoring."""
from pathlib import Path
import base64, csv, hashlib, json
import numpy as np

ROOT = Path(__file__).resolve().parent
M = ROOT / 'metadata'
R = ROOT / 'raw'
def readj(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p): return list(csv.DictReader(Path(p).read_text(encoding='utf-8-sig').splitlines(),delimiter='\t'))
def sha(b): return hashlib.sha256(b).hexdigest()
receipts = readj(ROOT/'REMOTE_FETCH_RECEIPTS.json')
by_file = {Path(x['local_path']).name:x for x in receipts}
expected = {x['run_id']:x for x in readj(M/'AOD_R2_F0_TARGET_EXTRACTION.json')['runs']}
freeze = readj(ROOT/'RETRIEVAL_FREEZE.json')
selected = freeze['run_ids']
extension = ROOT/'RETRIEVAL_EXTENSION.json'
if extension.exists(): selected += readj(extension)['run_ids']
for path in sorted(R.glob('*.base64')):
    binary = base64.b64decode(path.read_bytes())
    dest = path.with_suffix('')
    ref = by_file[dest.name]
    gitsha = hashlib.sha1(b'blob '+str(len(binary)).encode()+b'\0'+binary).hexdigest()
    assert gitsha == ref['git_blob_sha'], dest
    if dest.exists(): assert dest.read_bytes()==binary
    else: dest.write_bytes(binary)
times = rows(M/'AOD_R2_F0_TIME_MAPPING.tsv')
probes = sorted((x for x in rows(M/'E1_HOUSE_PROBE_CONTRACTS.tsv') if x['house']=='House01'),key=lambda x:int(x['probe_rank']))
meta = readj(M/'ocb_r2_cfg00_r01.meta.json')
for p in probes:
    # Averages of native grid cell centres, confirmed by original probe contract.
    x = meta['min_x'] + .05*(int(p['native_x0'])+int(p['native_x1_exclusive']))
    y = meta['min_y'] + .05*(int(p['native_y0'])+int(p['native_y1_exclusive']))
    assert abs(x-float(p['center_x_m']))<1e-12
    assert abs(y-float(p['center_y_m']))<1e-12
out=[]
for name in selected:
    cpath=R/(name+'.cube.npy'); ppath=R/(name+'.pooled.npy')
    cube=np.load(cpath,allow_pickle=False); pooled=np.load(ppath,allow_pickle=False)
    assert cube.shape==(10,87,114) and pooled.shape==(10,30)
    assert np.isfinite(cube).all() and (cube>=0).all()
    assert np.isfinite(pooled).all() and (pooled>=0).all()
    assert sha(cpath.read_bytes())==expected[name]['cube_sha256']
    assert sha(ppath.read_bytes())==expected[name]['pooled_sha256']
    recreated=np.stack([cube[:,int(p['native_x0']):int(p['native_x1_exclusive']),int(p['native_y0']):int(p['native_y1_exclusive'])].mean(axis=(1,2),dtype=np.float64) for p in probes],axis=1)
    assert np.array_equal(recreated,pooled), name
    mapping=sorted([x for x in times if x['run_id']==name],key=lambda x:int(x['slot']))
    assert [int(x['record_index']) for x in mapping]==meta['iters']
    manifest=readj(M/(name+'.RUN_MANIFEST.json'))
    assert manifest['phase'] in {'S2_H12_DISCOVERY','S2X_MATCHED_SOURCE_DISCOVERY'}
    out.append(dict(run_id=name,master_seed=manifest['master_seed'],source_id=manifest['source_id'],source_xyz=[float(manifest['simulation_parameters']['source_position_'+a])for a in 'xyz'],source_label_role='offline discovery provenance only',cube_shape=list(cube.shape),cube_dtype=str(cube.dtype),cube_sha256=sha(cpath.read_bytes()),pooled_shape=list(pooled.shape),pooled_dtype=str(pooled.dtype),pooled_sha256=sha(ppath.read_bytes()),pooling_bit_exact=True,actual_time_s=[float(x['actual_time_s'])for x in mapping],wind_index=[int(x['wind_index'])for x in mapping],occupancy_sha256=manifest['asset_checks']['occupancy_sha256'],wind_bundle_sha256=manifest['asset_checks']['wind_bundle_sha256'],timeline_sha256=manifest['qualification_standard']['timeline_sha256'],generator_binary_sha256=manifest['generator_binary_sha256']))
assert len({x['master_seed']for x in out})==len(out)
assert len({x['source_id']for x in out})==2
for k in ['occupancy_sha256','wind_bundle_sha256','timeline_sha256','generator_binary_sha256']:
    assert len({x[k]for x in out})==1,k
assert len({tuple(x['actual_time_s'])for x in out})==1
receipt=dict(status='PASS_EXISTING_DISCOVERY_NUMERICAL_BYTES_AND_SYNC',new_gaden_worlds=0,new_propagation_steps=0,confirmation_H03_opened=False,selected_context='X00',runs=out,sync_spatial_points=True,physical_clock_bound=True,continuous_window_available=False,minimum_snapshot_gap_s=min(np.diff(out[0]['actual_time_s'])),maximum_snapshot_gap_s=max(np.diff(out[0]['actual_time_s'])),local_wind_vectors_available=False,wind_index_and_bundle_hash_available=True,native_active_closed_loop_available=False,gas_unit='native extracted molar ppm; no real sensor response lag',grid=dict(axis_order=['time','x','y'],x_m='-7.55 + 0.1*(ix+0.5)',y_m='-7.88 + 0.1*(iy+0.5)',z_m=.2,coordinate_note='cell-centre formula checked against source-blind 2x2 probe centres; extractor source verification recorded separately'),split_requirement='split whole independent plume realization within source; never split 10 correlated snapshots as independent worlds',scope='already-open discovery, retrospective 2D slice of native 3D GADEN; not full 3D state or final confirmation')
(ROOT/'RETRIEVAL_VERIFICATION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items()if k!='runs'},indent=2))
print('verified_run_count',len(out),'raw_bytes',sum((R/(x['run_id']+'.'+t+'.npy')).stat().st_size for x in out for t in ['cube','pooled']))
