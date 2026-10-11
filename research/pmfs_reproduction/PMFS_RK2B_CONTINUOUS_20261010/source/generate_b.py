"""VM worker: one frozen campaign, serial generation and native query, bounded."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,csv,bisect,hashlib,os,subprocess,signal,time,shutil,zlib,struct
import numpy as np,yaml
ROOT=Path(__file__).resolve().parent;REG=json.loads((ROOT/'experiment_registry.json').read_text());PREF=json.loads((ROOT/'PREFLIGHT.json').read_text())
DATA=Path(REG['remote_data_path']);LIMIT=REG['hard_limits'];OLD=Path('/home/zyc/pmfs_m2_process_observation_20261010')
WS=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws');ENVROOT=Path('/home/zyc/pmfs_b4_native_validation_20261009/derived_B4')
assert not (DATA/'CAMPAIGN_STARTED.json').exists()
(DATA/'CAMPAIGN_STARTED.json').write_text(json.dumps(dict(wall_time=time.time(),registry_SHA256=hashlib.sha256((ROOT/'experiment_registry.json').read_bytes()).hexdigest())))
LED=dict(status='RUNNING',records=[],generation_wall_s=0.,response_wall_s=0.,mode=PREF['chosen_mode'],technical_retries=[],scientific_result_used_for_control=False)
last_beat=0.;last_size_check=0.;disk=0;begun=time.monotonic()
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save():(DATA/'GENERATION_LEDGER.json').write_text(json.dumps(LED,indent=2))
def heartbeat(phase,job=None,process=None,force=False):
    global last_beat,last_size_check,disk
    now=time.monotonic()
    if now-last_size_check>60 or force:
        disk=sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file());last_size_check=now
        assert disk<=REG['new_disk_cap_bytes'],'NEW_DISK_CEILING'
        assert shutil.disk_usage(DATA).free>=4294967296,'DATA_DISK_SAFETY_MARGIN'
        assert shutil.disk_usage(ROOT).free>=4294967296,'CODE_ROOT_SAFETY_MARGIN'
    if now-last_beat>=30 or force:
        value=dict(phase=phase,job_id=job,time=time.time(),campaign_wall_s=now-begun,disk_bytes=disk,generation_wall_s=LED['generation_wall_s'],response_wall_s=LED['response_wall_s'],process_pid=process)
        (DATA/'progress.json').write_text(json.dumps(value));
        with (DATA/'progress.jsonl').open('a') as f:f.write(json.dumps(value)+'\n')
        last_beat=now
def bounded(cmd,env,log,stage,job):
    start=time.monotonic();peak=0;reason=None;last_growth=start;previous=-1
    with log.open('w') as f:
        p=subprocess.Popen(cmd,env=env,stdout=f,stderr=f,start_new_session=True)
        try:
            while p.poll() is None:
                rss=0
                for e in Path('/proc').iterdir():
                    if not e.name.isdigit():continue
                    try:
                        if os.getpgid(int(e.name))!=p.pid:continue
                        for line in (e/'status').read_text().splitlines():
                            if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
                    except (OSError,ProcessLookupError):pass
                peak=max(peak,rss);elapsed=time.monotonic()-start
                if rss>1073741824:raise RuntimeError('RSS_1GIB')
                cap=LIMIT['generation_s'] if stage=='generation' else LIMIT['response_s']
                if LED[stage+'_wall_s']+elapsed>cap:raise RuntimeError(stage+'_WALL_CAP')
                if time.monotonic()-begun>LIMIT['total_scientific_s']:raise RuntimeError('TOTAL_CAP')
                size=log.stat().st_size
                if stage=='generation':
                    trace=log.parent/'PHYSICAL_FRAME_TIME.csv'
                    if trace.exists():size+=trace.stat().st_size
                if size!=previous:previous=size;last_growth=time.monotonic()
                if time.monotonic()-last_growth>120:raise RuntimeError('NO_EXPECTED_OUTPUT_GROWTH_120S')
                heartbeat(stage,job,p.pid);time.sleep(.1)
        except Exception as error:
            reason=repr(error)
            for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGKILL):
                try:os.killpg(p.pid,sig);p.wait(timeout=3);break
                except subprocess.TimeoutExpired:continue
                except ProcessLookupError:break
        code=p.wait()
    cost=dict(stage=stage,wall_s=time.monotonic()-start,sampled_process_group_peak_RSS_bytes=peak,exitcode=code,resource_stop=reason,command=cmd)
    LED[stage+'_wall_s']+=cost['wall_s'];save()
    assert code==0 and reason is None,(cost,log.read_text()[-2500:])
    return cost
def validate_generation(root,job):
    tt=list(csv.DictReader((root/'PHYSICAL_FRAME_TIME.csv').open()));frames=sorted((root/'bank').glob('iteration_*'),key=lambda p:int(p.name.split('_')[1]))
    assert len(tt)==len(frames)==1803
    rr=[]
    for file,row in zip(frames,tt):
        b=file.read_bytes();assert b[:13]==b'GADEN_RESULT\0' and b[13]==1
        a=zlib.decompress(b[22:]);assert len(a)==struct.unpack_from('<Q',b,14)[0]
        off=56+struct.unpack_from('<Q',a,48)[0];s=struct.unpack_from('<3f',a,off)
        assert np.allclose(s,job['source_xyz'],rtol=0,atol=1e-6)
        assert struct.unpack_from('<i',a,off+12)[0]==13
        moles,all_gas=struct.unpack_from('<2f',a,off+16)
        assert np.isfinite([moles,all_gas]).all() and moles>0 and all_gas>0
        wi=struct.unpack_from('<i',a,off+24)[0];assert wi==int(row['wind_index_at_save'])
        nstr=struct.unpack_from('<Q',a,off+28)[0];ptr=off+36+nstr;num=struct.unpack_from('<Q',a,ptr)[0];ptr+=8
        vals=np.frombuffer(a,dtype='<f4',offset=ptr).reshape(num,4);assert np.isfinite(vals).all() and (vals[:,3]>0).all()
        assert num==int(row['filaments_after_step'])
        rr.append(dict(frame=int(file.name.split('_')[1]),physical_snapshot_time_s=float(row['physical_snapshot_time_s']),wind_index=wi,filaments=num,bytes=len(b),SHA256=hashlib.sha256(b).hexdigest()))
    times=[r['physical_snapshot_time_s'] for r in rr];assert times[0]==0 and times[-1]>999 and np.all(np.diff(times)>0)
    assert {r['wind_index'] for r in rr if r['physical_snapshot_time_s']>=320}=={10}
    for name,h in PREF['RNG_initial_and_cache_SHA256'][job['job_id']].items():assert sh(root/name)==h,(job['job_id'],name,'RNG_PRECOMMIT_MISMATCH')
    for p in (root/'bank/wind').glob('wind_iteration_*'):assert sh(p)==sh(ENVROOT/'wind'/p.name)
    with (root/'ALL_FRAME_SHA256_AND_TIME.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
    return rr
base=yaml.safe_load(Path('/home/zyc/pmfs_b4_native_validation_20261009/B4_generation_RESOLVED.yaml').read_text())['/**']['ros__parameters']
try:
    for job in REG['jobs']:
        root=DATA/'realizations'/job['job_id'];assert not root.exists();root.mkdir(parents=True)
        pars=base.copy();pars.update(source_position_x=job['source_xyz'][0],source_position_y=job['source_xyz'][1],source_position_z=job['source_xyz'][2],results_location=str(root/'bank'),r6_time_trace_path=str(root/'PHYSICAL_FRAME_TIME.csv'))
        (root/'PARAMETERS.yaml').write_text(yaml.safe_dump({'/**':{'ros__parameters':pars}},sort_keys=False))
        env=os.environ.copy();env.update(M2_GAUSSIAN_SEED=str(job['gaussian_seed']),M2_UNIFORM_SEED=str(job['uniform_seed']),M2_RNG_TRACE=str(root/'RNG'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',ROS_DOMAIN_ID='228')
        env.pop('GADEN_RNG_SEED',None);env['LD_LIBRARY_PATH']=str(OLD)+':'+str(WS/'install/gaden_common/lib')+':'+str(WS/'build/gaden_common/third_party/gaden_core/third_party/libbsc')+':/opt/ros/humble/lib'
        cmd=['bash','-c','source /opt/ros/humble/setup.bash; exec "$@"','bash',str(WS/'install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator'),'--ros-args','--params-file',str(root/'PARAMETERS.yaml')]
        heartbeat('generation_start',job['job_id'],force=True)
        gc=bounded(cmd,env,root/'generation.log','generation',job['job_id']);frames=validate_generation(root,job)
        times=[r['physical_snapshot_time_s'] for r in frames];query=[];lineage=[]
        for b in REG['receiver_plan']:
            fi=bisect.bisect_right(times,b['physical_s'])-1;assert fi>=0 and times[fi]<=b['physical_s']<times[fi+1]
            actual=frames[fi]['frame']
            lineage.append(dict(block_id=b['block_id'],target_s=b['physical_s'],frame=actual,actual_s=times[fi],next_s=times[fi+1],wind_index=frames[fi]['wind_index']))
            for pi,xyz in enumerate(REG['all_receiver_xyz']):query.append(dict(query_id=f"b{b['block_id']}_p{pi}",frame=actual,x=xyz[0],y=xyz[1],z=xyz[2]))
        query.append(dict(query_id='source_support_anchor',frame=lineage[0]['frame'],x=job['source_xyz'][0],y=job['source_xyz'][1],z=job['source_xyz'][2]))
        query.sort(key=lambda q:q['frame'])
        for name,rr in [('QUERIES.csv',query),('QUERY_PHYSICAL_LINEAGE.csv',lineage)]:
            with (root/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
        env['LD_LIBRARY_PATH']=str(WS/'install/gaden_common/lib')+':'+str(WS/'build/gaden_common/third_party/gaden_core/third_party/libbsc')+':/opt/ros/humble/lib'
        qc=bounded([str(OLD/'query_native'),str(ENVROOT),str(root/'bank'),str(root/'QUERIES.csv'),str(root/'QUERY_OUTPUT.csv')],env,root/'query.log','response',job['job_id'])
        out=list(csv.DictReader((root/'QUERY_OUTPUT.csv').open()));assert len(out)==50*len(REG['all_receiver_xyz'])+1
        assert all(r['physical_free']=='1' and np.isfinite(float(r['ppm_float32'])) and float(r['ppm_float32'])>=0 for r in out)
        if not LED['records']:
            import verify_raw_receiver_queries as raw
            from cache_native import cutoff_and_contributions
            ast=time.monotonic();occ=raw.occupancy(ENVROOT/'OccupancyGrid3D.csv')
            desc=raw.snapshot(root/'bank'/f"iteration_{lineage[0]['frame']}")
            assert np.array_equal(desc['minimum'],occ['minimum']) and np.array_equal(desc['dimensions'],occ['dimensions'])
            _,total,*_=cutoff_and_contributions(desc['filaments'],np.array(REG['all_receiver_xyz'][:10],dtype=np.float32),desc,occ,raw)
            target=np.array([float(next(r['ppm_float32'] for r in out if r['query_id']==f'b0_p{k}')) for k in range(10)],dtype=np.float32)
            assert np.all(np.abs(total.astype(float)-target.astype(float))<=3e-7+5e-6*np.abs(target))
            anchor=dict(job_id=job['job_id'],frame=lineage[0]['frame'],native_CPP_ppm=target.tolist(),independent_raw_ppm=total.tolist(),maximum_abs_difference=float(np.max(np.abs(total-target))),wall_s=time.monotonic()-ast,first_realization_before_any_other_generation=True)
            (root/'FIRST_REALIZATION_NATIVE_ANCHOR.json').write_text(json.dumps(anchor,indent=2));LED['response_wall_s']+=anchor['wall_s']
        rec=dict(job_id=job['job_id'],role=job['role'],candidate_id=job['candidate_id'],physical_qualification='PASS',generation=gc,native_response=qc,frames=len(frames),selected_frames=len(set(l['frame'] for l in lineage)),all_native_queries=len(out),query_SHA256=sh(root/'QUERY_OUTPUT.csv'),wind_during_task=[10],no_stable_cross_frame_particle_ID=True)
        (root/'QUALIFICATION.json').write_text(json.dumps(rec,indent=2));LED['records'].append(rec);save();heartbeat('REALIZATION_QUALIFIED',job['job_id'],force=True)
        # First entry is engineering qualification only, counted in24. No method score has been run.
    LED['status']='PASS_ALL_PRECOMMITTED_REALIZATIONS_NATIVE_QUERY'
except Exception as error:
    LED['status']='INTEGRITY_STOP_DEPENDENCIES_BLOCKED';LED['error']=repr(error)
finally:save();heartbeat(LED['status'],force=True)
print(json.dumps(LED,indent=2))
raise SystemExit(0 if LED['status'].startswith('PASS') else 1)
