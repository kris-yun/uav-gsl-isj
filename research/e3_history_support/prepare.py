"""Preregister one bounded continuation before looking at intervention outputs."""
from pathlib import Path
import csv, datetime, hashlib, json, math, shutil, sys
import numpy as np

ROOT = Path('D:/ZYC/A-gas/workspace/METHOD_COMPARISON_O24_1M2_20261024')
OLD = ROOT / 'outputs/E3_CAUSAL_PAIR_20261025'
PARENT = ROOT / 'outputs/E3_INFORMATION_SOURCE_20261025'
OUT = ROOT / 'outputs/E3_HISTORY_SUPPORT_20261025'

def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def put(path, value): path.parent.mkdir(exist_ok=True, parents=True); path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
def rows(path): return list(csv.DictReader(path.open(encoding='utf-8-sig')))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert not OUT.exists(), 'Never overwrite a first experiment'
    OUT.mkdir()
    sig=[np.float32(10.)]
    for _ in range(10002):
        s=sig[-1]; sig.append(np.float32(s+np.float32(np.float32(np.float32(15.)/np.float32(np.float32(2.)*s))*np.float32(.1))))
    sig=np.array(sig)
    query_ids={r['query_id'] for r in rows(OLD/'schedule/QUERIES.csv') if r['group']=='historical' and int(r['stop'])>=8}
    age=[]; weight=[]
    for r in rows(OLD/'original_E3_decomposition/FILAMENT_CONTRIBUTIONS.csv'):
        if r['query_id'] in query_ids and float(r['contribution_ppm'])>0:
            idx=int(np.searchsorted(sig,np.float32(r['sigma_cm']))); assert sig[idx]==np.float32(r['sigma_cm'])
            age.append(idx*.1);weight.append(float(r['contribution_ppm']))
    order=np.argsort(age);a=np.array(age)[order];w=np.array(weight)[order];cdf=np.cumsum(w)/sum(w)
    q99=float(a[np.searchsorted(cdf,.99)]); seconds=math.ceil(q99/20)*20
    assert seconds==220, seconds
    plan=read(OLD/'PREREGISTERED_CAUSAL_CONTRACT.json')
    contract=dict(identity='E3_HISTORY_SUPPORT_INTERVENTION_20261025',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        parent_commit='58d8610f95a501d2347844740d9b495ba193b099',
        objective='One native warmup termination intervention, with local GMRF and2D transport fixed',
        development_only=True, new_physical_worlds=0,new_ROS=0,neural_training=0,
        history_rule='ceil(concentration-weighted99percentile original critical gas age/20s)*20s, fixed before outputs',
        q99_age_s=q99, fixed_history_s=seconds,
        native_reference='first exiting filament or max500warmup iterations, record200steps, dt0.1s; warmup dt0.2s',
        intervention='continue warmup to exactly1100steps; exiting particles removed, all remaining particles updated; same movement/noise/mask and200recordsteps',
        same_RNG_scope='same cached Gaussian tables and uniform initial state, exact shared prefix until native exit; after unequal consumption trajectories are not bitwise paired',
        prediction_streams=plan['prediction_streams'],
        E3_sources=dict(true=[-4.,-1.9],rival=[-2.375,-4.875]),
        A2_scope='normal-case source-pair guard only; does not establish full1195cell posterior or closed-loop nondegradation',
        max_point_forwards=16,technical_native_leaf_replays=4,
        limits=dict(total_execution_wall_s=900,child_CPU_s=120,new_output_bytes=134217728,sequential=True),
        preregistered_endpoints=['critical8to13 true-source center andPID response','source-pair signed compatibility on four retained actual worlds','age support and active-particle residence','A2 normal pair native full-map score difference','all positive/negative contrasts andcost'],
        interpretation='A rescue establishes conditional intervention effect, not unique physical cause; a failure rules out sufficiency of this fixed warmup extension only. No adaptive longer duration, true-wind substitution or3D upgrade.')
    put(OUT/'PREREGISTERED_HISTORY_CONTRACT.json',contract)
    inp=OUT/'inputs';inp.mkdir()
    for name in ['scene.json','CONSTANTS.json']:
        shutil.copy2(OLD/'event_control'/name,inp/('E3_'+name))
    shutil.copy2(OLD/'schedule/UNIQUE_POINTS.csv',inp/'E3_UNIQUE_POINTS.csv')
    for p in plan['prediction_streams']:
        shutil.copy2(OLD/'event_control'/(p['id']+'.cache.f32'),inp/(p['id']+'.cache.f32'))
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'e3_information_audit'))
    import audit
    d=audit.case_data('A2_R01_REFERENCE');u=max(int(r['update']) for r in d['allpost']);s=audit.snapshot(d,u)
    n=d['nx']*d['ny'];occupancy=np.ones(n,int);wind=np.zeros((n,2));lo=np.zeros(n);conf=np.zeros(n)
    post=[r for r in d['allpost'] if int(r['update'])==u]
    for r in post:
        i=int(r['col'])+d['nx']*int(r['row']);occupancy[i]=0
        wind[i]=[float(r['estimated_wind_u']),float(r['estimated_wind_v'])];lo[i]=float(r['hit_log_odds']);conf[i]=float(r['hit_confidence'])
    stops=[]
    for start in range(0,len(d['windows']),5):
        group=d['windows'][start:start+5];cell=group[0]['flat'];stops.append(dict(stop=start//5+1,cell=[cell%d['nx'],cell//d['nx']],hits=sum(r['hit'] for r in group),n=len(group)))
    scene=dict(nx=d['nx'],ny=d['ny'],origin=[d['nav']['origin_x'],d['nav']['origin_y']],cell_size=d['cs'],occupancy=occupancy.tolist(),wind_xy=wind.tolist(),logodds=lo.tolist(),confidence=conf.tolist(),params=d['par'],stops=stops,input_scope='A2 final saved local GMRF, offline retrospective normal pair guard')
    put(inp/'A2_scene.json',scene)
    true_owner=int(s['owner'][d['tf']]);mapflat=int(s['idx'][np.argmax(s['p'])]);rival_owner=int(s['owner'][mapflat]);spec=[]
    for label,owner in [('true',true_owner),('rival',rival_owner)]:
        candidate=s['candidates'][owner];call=int(candidate['call']);rng=next(r for r in [json.loads(line) for line in (d['root']/'runtime/native_rng_states.jsonl').read_text().splitlines()] if r['call']==call)
        put(inp/f'A2_replay_{label}.json',dict(candidate=candidate,rng=rng))
        (inp/f'A2_expected_{label}.f32').write_bytes(s['maps'][owner].astype('<f4').tobytes())
        shutil.copy2(d['root']/'runtime'/f'native_rng_states.jsonl.cache.thread{rng["before"]["tid"]}.f32',inp/f'A2_replay_{label}.cache.f32')
        c=np.where(s['idx']==(d['tf'] if label=='true' else mapflat))[0][0];spec.append(dict(label=label,point=s['xy'][c].tolist(),call=call))
    put(inp/'A2_PAIR.json',dict(points=spec,original_full_domain_metrics=audit.metrics(s['p'],s,d),point_scope='covering-cell centers, not moved physical truth'))
    prior=ROOT/'V11_REVIEW_20261024/function_trial'
    for call in [589,660]:
        p=read(prior/f'replay_call_{call}.json');put(inp/f'E3_replay_{call}.json',p)
        shutil.copy2(prior/f'expected_call_{call}.f32',inp/f'E3_expected_{call}.f32')
        shutil.copy2(prior/f'native_rng_states.jsonl.cache.thread{p["rng"]["before"]["tid"]}.f32',inp/f'E3_replay_{call}.cache.f32')
    for p in inp.iterdir():
        assert p.is_file()
    put(OUT/'INPUT_SHA256.json',[dict(path=p.relative_to(OUT).as_posix(),sha256=sha(p)) for p in sorted(inp.iterdir())])
    print('PREREGISTERED_HISTORY220',len(stops),len(s['idx']),flush=True)

if __name__=='__main__':main()
