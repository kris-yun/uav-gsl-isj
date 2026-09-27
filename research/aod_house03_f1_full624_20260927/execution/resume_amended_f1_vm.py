#!/usr/bin/env python3
"""Signed sampling amendment; metadata-first acquisition, no partial rankings."""
import argparse, csv, hashlib, json, os, shutil, subprocess, time
from pathlib import Path
import numpy as np

R=Path('/home/zyc/aod_house03_f1_full624_20260927')
A=R/'timebase_amendment'
O=R/'amended_execution'
NEW=Path('/mnt/hgfs/workspace/_staging/AOD_F1_AMENDED_TARGETS_20260927')
FIRST=Path('/home/zyc/ros2_ws/aod_house03_f1_full624_targets_20260927/source_0_replica_0')
EX=Path('/home/zyc/rmfe_filament_extractor_omp')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def read(p):return list(csv.DictReader(Path(p).open(),delimiter='\t'))
def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n');tmp.replace(p)
def runpath(row):
    if int(row['source_index'])==0 and int(row['realization_index'])==0:return FIRST
    return NEW/f"source_{row['source_index']}_replica_{row['realization_index']}"
def files(p):return {str(f.relative_to(p)):sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def schedule_check(run):
    times=read(run/'RESULT_TIME_MAP.tsv');base=read(FIRST/'RESULT_TIME_MAP.tsv')
    assert len(times)==len(base)==986
    fields=['save_record_id','physical_sim_time_s','wind_index','integration_step']
    assert [[r[k] for k in fields] for r in times]==[[r[k] for k in fields] for r in base]
    chosen=[]
    for s in read(A/'NATIVE_SNAPSHOT_SCHEDULE_SIGNED.tsv'):
        row=times[int(s['save_record_id'])]
        assert int(row['save_record_id'])==int(s['save_record_id'])
        assert float(row['physical_sim_time_s'])==float(s['clock_before_s'])
        assert int(row['wind_index'])==int(s['wind_before'])
        assert int(row['integration_step'])==int(s['integration_step'])
        assert s['state_stage']=='POST_MOVE_PRE_WIND_PRE_CLOCK'
        assert Path(row['output_path']).name==s['filename']
        assert (run/'realization'/s['filename']).is_file()
        chosen.append(s)
    release=read(run/'RELEASE_TIME_METADATA.tsv')
    assert release==read(FIRST/'RELEASE_TIME_METADATA.tsv')
    return chosen
def check_freeze():
    freeze=json.loads((A/'AMENDMENT_FREEZE.json').read_text())
    assert freeze['approved'] and freeze['concentration_values_read_at_signing'] is False
    for name,digest in freeze['file_sha256'].items():assert sha(R/name)==digest,name
    for name,digest in json.loads((R/'TEMPLATE_FREEZE.json').read_text())['arrays_sha256'].items():assert sha(R/'templates'/name)==digest,name
    return freeze
def preflight():
    check_freeze();O.mkdir(exist_ok=True)
    assert not (O/'target_data').exists(), 'Preflight must precede gas decoding'
    assert json.loads((R/'TIMEBASE_AUDIT.json').read_text())['concentration_values_read'] is False
    assert not (FIRST/'concentration.npy').exists()
    schedule_check(FIRST)
    provenance=json.loads((R/'timebase_logger/LOGGER_BUILD_PROVENANCE.json').read_text())
    assert sha(R/'timebase_logger/filament_simulator_timebase')==provenance['binary_sha256']
    assert sha(EX)=='206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91'
    audit=json.loads((R/'CANDIDATE_BANK_AUDIT.json').read_text())
    for i,rec in enumerate(audit['records']):
        pre=R/f"candidate_forward/source_{rec['source_index']}/state_{rec['wind_state']}_replica_{rec['transport_replica_index']}"
        for kind,digest in rec['hashes'].items():assert sha(str(pre)+f'.{kind}.f32')==digest
        if (i+1)%10000==0:print('BANK_BYTES_VERIFIED',i+1,flush=True)
    cfg=json.loads((FIRST/'RUN_CONFIGURATION.json').read_text())
    assert cfg['manifest_row']==read(R/'protocol/frozen/HOUSE03_FUTURE_GADEN_SEEDS_96.tsv')[0]
    shared=shutil.disk_usage(NEW.parent.parent).free
    firstbytes=sum(p.stat().st_size for p in FIRST.rglob('*') if p.is_file())
    assert shared>95*firstbytes*1.15+1024**3, (shared,firstbytes)
    inventory=files(FIRST)
    write(O/'PRE_READ_ASSET_AUDIT.json',dict(passed=True,old_hold_preserved=True,
        first_run_reused=True,first_run_sha256=inventory,first_raw_bytes=firstbytes,
        raw_candidate_files_rehashed=54912*4,template_hashes_unchanged=True,
        first_concentration_not_decoded=True,bank_forwards_regenerated=0,
        shared_free_bytes=shared,delete_policy='No deletion; retain all raw outputs'))
    print('AMENDED_PREFLIGHT_PASS_NO_GAS_DECODE',flush=True)
def acquire():
    check_freeze();assert json.loads((O/'PRE_READ_ASSET_AUDIT.json').read_text())['passed']
    rows=read(R/'protocol/frozen/HOUSE03_FUTURE_GADEN_SEEDS_96.tsv')
    first=json.loads((FIRST/'RUN_CONFIGURATION.json').read_text())
    new_records=[]
    NEW.mkdir(parents=True,exist_ok=True)
    for i,item in enumerate(rows):
        run=runpath(item);done=O/'metadata'/f"source_{item['source_index']}_replica_{item['realization_index']}.json"
        if done.exists():
            old=json.loads(done.read_text()); assert old['manifest_row']==item
            schedule_check(run)
            for n,h in old['files_sha256'].items():assert sha(run/n)==h
            new_records.append(old);continue
        t=time.monotonic()
        if i:
            assert not run.exists(),f'Preserve incomplete output for infrastructure review: {run}'
            assert run.resolve().is_relative_to(NEW.resolve())
            assert shutil.disk_usage(NEW).free>256*1024**2+1024**3,'Disk reserve stop'
            run.mkdir()
            options=dict(first['options'],results_location=str(run/'realization'),
                source_position_x=item['x_m'],source_position_y=item['y_m'],source_position_z=item['z_m'])
            binary=R/'timebase_logger/filament_simulator_timebase'
            env=dict(os.environ,GADEN_RNG_SEED=item['requested_seed'],AOD_TIME_AUDIT_DIR=str(run),
                     AOD_RUN_ID=f"House03_{item['source_id']}_replica_{item['realization_index']}",
                     ROS_DOMAIN_ID='229',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
            env['LD_LIBRARY_PATH']=first['runtime_ld_library_path']
            assert sha(binary)==first['binary_sha256']
            command=[str(binary),'--ros-args']+[v for k,x in options.items() for v in ('-p',f'{k}:={x}')]
            write(run/'RUN_CONFIGURATION.json',dict(manifest_row=item,options=options,command=command,
                 amended_sampling_freeze_sha256=sha(A/'AMENDMENT_FREEZE.json'),
                 binary_sha256=sha(binary),concentration_values_read=False))
            with (run/'generation.log').open('w') as log:subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            assert 'Filament simulator finished correctly!' in (run/'generation.log').read_text()
        selected=schedule_check(run)
        record=dict(manifest_row=item,run_directory=str(run),first_reused=(i==0),
            frozen_state_tuples=selected,files_sha256=files(run),wall_seconds=time.monotonic()-t,
            concentration_values_read=False)
        write(done,record);new_records.append(record)
        write(O/'ACQUISITION_PROGRESS.json',dict(completed=len(new_records),planned=96,
             additional_generated=len(new_records)-1,concentration_values_read=False))
        print('METADATA_VALID',len(new_records),item['source_id'],item['realization_index'],flush=True)
    assert len(new_records)==96
    write(O/'ALL96_METADATA_FREEZE.json',dict(passed=True,runs=new_records,
         reused_first=1,new_generated=95,same_full986_state_table=True,concentration_values_read=False))
def extract():
    check_freeze();complete=json.loads((O/'ALL96_METADATA_FREEZE.json').read_text());assert complete['passed']
    D=O/'target_data';D.mkdir(exist_ok=False)
    occ=Path(json.loads((FIRST/'RUN_CONFIGURATION.json').read_text())['options']['occupancy3D_data'])
    header=occ.read_text().splitlines()[:4];origin=[float(x) for x in header[0].split()[1:]]
    dims=[int(x) for x in header[2].split()[1:]];assert dims[:2]==[138,83]
    assert sha(EX)=='206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91'
    probes=read(R/'f0/HOUSE03_FROZEN_30_PROBES.tsv')
    pathranks={p:[int(x['probe_rank'])-1 for x in read(R/f'protocol/frozen/HOUSE03_PATH_{p}_10.tsv')] for p in ['A','B']}
    allpaths=np.empty((12,8,2,10),dtype=np.float64);allpooled=np.empty((12,8,10,30),dtype=np.float64)
    metadata=[]
    for rec in complete['runs']:
        row=rec['manifest_row'];run=Path(rec['run_directory']);schedule_check(run)
        for n,h in rec['files_sha256'].items():assert sha(run/n)==h
        real=run/'realization'
        # Required by historical extractor; numerical output files remain untouched.
        if not (real/'OccupancyGrid3D.csv').exists():os.symlink(occ,real/'OccupancyGrid3D.csv')
        out=D/f"source_{row['source_index']}_replica_{row['realization_index']}";out.mkdir()
        ids=[s['save_record_id'] for s in read(A/'NATIVE_SNAPSHOT_SCHEDULE_SIGNED.tsv')]
        cmd=[str(EX),str(real),str(real),str(out/'concentration.npy'),str(out/'spatial_metadata.json'),
             repr(origin[0]),repr(origin[1]),'0.1','1','0.20',str(dims[0]),str(dims[1]),*ids]
        with (out/'extraction.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
        cube=np.load(out/'concentration.npy',allow_pickle=False)
        assert cube.shape==(10,138,83) and np.isfinite(cube).all() and (cube>=0).all()
        pooled=np.stack([cube[:,int(p['native_x0']):int(p['native_x1_exclusive']),
                          int(p['native_y0']):int(p['native_y1_exclusive'])].mean(axis=(1,2),dtype=np.float64) for p in probes],axis=1)
        si,ri=int(row['source_index']),int(row['realization_index'])
        allpooled[si,ri]=pooled
        for pi,p in enumerate(['A','B']):allpaths[si,ri,pi]=pooled[np.arange(10),pathranks[p]]
        np.save(out/'pooled_10x30.npy',pooled,allow_pickle=False)
        metadata.append(dict(manifest_row=row,extraction_command=cmd,artifacts_sha256=files(out)))
        print('CUBE_EXTRACTED',len(metadata),flush=True)
    np.save(D/'TARGET_PATHS_12x8x2x10.npy',allpaths,allow_pickle=False)
    np.save(D/'TARGET_POOLED_12x8x10x30.npy',allpooled,allow_pickle=False)
    write(O/'TARGET_DATA_FREEZE.json',dict(passed=True,targets=96,full_cubes_preserved=True,
        extractor_sha256=sha(EX),runs=metadata,all_artifact_sha256=files(D),scientific_scores_computed=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['preflight','acquire','extract']);a=p.parse_args()
    {'preflight':preflight,'acquire':acquire,'extract':extract}[a.mode]()
