from pathlib import Path
import os,json,hashlib,collections,csv,re,numpy as np,shutil
home=Path('/home/zyc')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
roots=[home/'E2_CROSS_ENVIRONMENT_168_RUNS_20260925/OPEN_DISCOVERY',home/'JTD_E1_FRESH_TARGETS_20260925',home/'JTD_E2_K12_180_RUNS_20260925']
records=[]
for root in roots:
    for p in sorted(root.rglob('concentration.npy')):
        if 'House03' in str(p):raise RuntimeError('unexpected sealed path')
        meta_path=p.parent/'run_metadata.json';meta=json.loads(meta_path.read_text())
        a=np.load(p,mmap_mode='r',allow_pickle=False);actual=sha(p)
        expected=meta.get('cube_sha256') or meta.get('concentration_sha256')
        raw_paths=[p.parent/'realization',p.parent/'raw',p.parent/'results']
        raw_count=sum(sum(bool(re.fullmatch(r'iteration_\d+',c.name)) for c in q.iterdir()) for q in raw_paths if q.is_dir())
        records.append({'path':str(p),'root':str(root),'shape':list(a.shape),'sha256':actual,'historical_manifest_sha256':expected,'hash_match':actual==expected if expected else None,'metadata_sha256':sha(meta_path),'source_id':meta.get('source_id'),'source_xyz':meta.get('source_xyz'),'house':meta.get('house'),'wind':meta.get('wind'),'raw_frame_count':raw_count,'metadata':meta})
raw=json.loads((home/'brg_v1_raw_frames_inventory_20260928.json').read_text())
real_dirs=[r for r in raw['raw_directories'] if r['frames']>=300 and not any(x in r['path'].lower() for x in ('h03','house03'))]
c0=[]
for p in sorted((home/'c0_5_real_gaden_bank_20260923').glob('S*/manifest.tsv')):
    kv=dict(line.split('\t',1) for line in p.read_text().splitlines() if '\t' in line)
    frames=sorted(int(q.name.split('_')[1]) for q in (p.parent/'realization').glob('iteration_*') if re.fullmatch(r'iteration_\d+',q.name))
    c0.append({'manifest_path':str(p),'manifest_sha256':sha(p),'manifest':kv,'frame_count':len(frames),'first_frame':min(frames),'last_frame':max(frames),'contiguous_ids':frames==list(range(min(frames),max(frames)+1))})
code=[]
for root in (home/'jtd_e2_repo_20260925/research',home/'e2_repo_20260925/research'):
    for p in root.rglob('*.py'):
        if any(x in p.name for x in ('e2','e1')):
            lines=p.read_text(errors='replace').splitlines()
            hits=[{'line':i,'text':l} for i,l in enumerate(lines,1) if ('rmtree(' in l or 'extract_times' in l or 'TIMES =' in l)]
            if hits:code.append({'path':str(p),'sha256':sha(p),'snippets':hits})
counts=collections.Counter(r['root'] for r in records)
out={'roots':{str(r):{'exists':r.exists(),'cubes':counts[str(r)]} for r in roots},'records':records,'all_recorded_hashes_match':all(r['hash_match'] is True for r in records),'raw_directories_elsewhere':real_dirs,'c0_manifest_inventory':c0,'generator_source_audit':code,'disk':{p:dict(zip(('total','used','free'),shutil.disk_usage(p))) for p in ('/','/mnt/hgfs/workspace','/dev/shm')},'concentration_values_inspected':False,'concentration_bytes_hashed_only':True,'house03_training_reads':0}
dest=home/'brg_v1_verified_asset_audit_20260928.json';dest.write_text(json.dumps(out,indent=2))
print(json.dumps({'path':str(dest),'root_counts':dict(counts),'total':len(records),'hash_matches':collections.Counter(str(r['hash_match']) for r in records),'shapes':collections.Counter(str(r['shape']) for r in records),'raw_frames_in_288':sum(r['raw_frame_count'] for r in records),'c0_runs':len(c0),'c0_source_groups':sorted(set(c['manifest']['source_xyz_m'] for c in c0)),'disk':out['disk']},indent=2))
