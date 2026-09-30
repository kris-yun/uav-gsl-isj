"""Read-only Phase 0 inventory of exactly the historical OPEN49 cohort."""
import csv, hashlib, io, json, subprocess, tarfile
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'evidence/icra2025_vgr_d0b'
CACHE = Path(r'C:\GADEN_OCB_R2_ARCHIVE\d0b_supervised_20260930')
ZSTD = r'D:\Anaconda\Library\bin\zstd.exe'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x): Path(p).write_text(json.dumps(x,indent=2,sort_keys=True,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def rows(b): return list(csv.DictReader(io.StringIO(b.decode('utf-8'))))
def archive_raw(p):
    proc=subprocess.Popen([ZSTD,'-dc',str(p)],stdout=subprocess.PIPE)
    raw={}; wanted={'measurement_events.csv','measurement_blocks.csv','sim_pose_trace.csv','runtime_binding.json','launch.log','beliefs.jsonl','measured_map_at_update.csv'}
    result=None
    with tarfile.open(fileobj=proc.stdout,mode='r|') as t:
        for m in t:
            if not m.isfile(): continue
            name=Path(m.name).name
            if name in wanted and '_raw/' in m.name and '/results/' not in m.name:
                raw[name]=t.extractfile(m).read()
            if '/' not in m.name and m.name.endswith('.json') and not m.name.endswith('_episode.json'):
                result=json.loads(t.extractfile(m).read())
    proc.stdout.read();proc.stdout.close();assert proc.wait()==0
    return raw,result

def main():
    OUT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True)
    frozen=ROOT/'evidence/ds_pmfs_identity_d1/ASSET_FREEZE.json'
    routes=ROOT/'evidence/aec_d0/ROUTE_POSITIONS_ONLY.json'
    ids={r['case_id'] for r in load(routes)}
    eps=[e for e in load(frozen)['episodes'] if e['case_id'] in ids]
    assert len(eps)==len(ids)==49
    results=[]
    for e in eps:
        case=e['case_id']; missing=[];checks={}
        if 'archive' in e:
            p=Path(e['archive']);checks['archive_hash']=p.is_file() and sha(p)==e['archive_sha256']
            raw,final=archive_raw(p) if checks['archive_hash'] else ({},None)
            digest=e['archive_sha256']
        else:
            p=Path(e['raw_dir']);raw={n:q.read_bytes() for n in ['measurement_events.csv','measurement_blocks.csv','sim_pose_trace.csv','runtime_binding.json','launch.log','beliefs.jsonl','measured_map_at_update.csv'] if (q:=p/n).is_file()}
            checks['raw_hashes']=all((p/n).is_file() and sha(p/n)==h for n,h in e['raw_files_sha256'].items())
            final=load(e['episode_metadata']);digest=e['episode_metadata_sha256']
        events=rows(raw['measurement_events.csv']) if 'measurement_events.csv' in raw else []
        blocks=rows(raw['measurement_blocks.csv']) if 'measurement_blocks.csv' in raw else []
        pose=rows(raw['sim_pose_trace.csv']) if 'sim_pose_trace.csv' in raw else []
        checks.update(house_open=e['house'] in ('House01','House02'), current_target_excluded='2026900001' not in case and 'ocb_r2' not in case,
            events_exist=bool(events), completed_times=len(events)==len(blocks)>0, actual_pose_yaw=bool(pose) and all(k in pose[0] for k in ('t_sim_s','x','y','yaw')),
            measured_wind=bool(events) and all(k in events[0] for k in ('wind_speed','wind_direction','robot_x','robot_y','hit','concentration')),
            source_truth=final is not None and len(final.get('truth_xy',[]))==2,
            runtime_map_provenance='runtime_binding.json' in raw and 'launch.log' in raw and 'measured_map_at_update.csv' in raw)
        if checks['completed_times']:
            checks['event_block_pose_match']=all(abs(float(a['robot_x'])-float(b['pose_x']))<1e-4 and abs(float(a['robot_y'])-float(b['pose_y']))<1e-4 and int(a['event_id'])==int(b['measurement_cycle_id']) for a,b in zip(events,blocks))
            checks['time_monotone']=all(float(a['sim_time_end'])<=float(b['sim_time_end']) for a,b in zip(blocks,blocks[1:]))
        leaf=CACHE/'raw_audit'/case;leaf.mkdir(parents=True,exist_ok=True)
        for n,b in raw.items(): (leaf/n).write_bytes(b)
        if final is not None:dump(leaf/'case_result.json',final)
        results.append(dict(case_id=case,house=e['house'],wind=e['wind'],source_id=e['source_id'],historical_split=e['split'],physical_seed=int(case.split('_seed')[-1]),
            input_path=str(p),input_sha256=digest,events=len(events),hits=sum(int(x['hit']) for x in events),raw_cache=str(leaf),checks=checks,ready=all(checks.values())))
    # Map reconstruction and causal pose checks are independently required before TRAINABLE.
    report=dict(stage='PHASE0_RAW_FIELD_AUDIT',decision='PENDING_MAP_AND_POSE_SEMANTICS',exact_historical_cohort=49,
        freeze_sha256=sha(frozen),routes_sha256=sha(routes),raw_fields_pass=sum(r['ready'] for r in results),
        by_house=dict(Counter(r['house'] for r in results)),by_source=dict(Counter(r['house']+'/'+r['source_id'] for r in results)),
        new_simulations=0,confirmation_opened=False,house03_opened=False,trajectories=results)
    dump(OUT/'OPEN49_RAW_AUDIT.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='trajectories'},indent=2))
    for r in results:
        if not r['ready']:print('INCOMPLETE',r['case_id'],[k for k,v in r['checks'].items() if not v])
if __name__=='__main__':main()
