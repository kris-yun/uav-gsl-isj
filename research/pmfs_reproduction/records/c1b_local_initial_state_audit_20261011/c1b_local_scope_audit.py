"""Read-only C1B clock/input audit. No plume, field, truth or prediction reads."""
from pathlib import Path
import csv, gzip, hashlib, json, re, time
from datetime import datetime, timezone
import yaml

BASE = Path(__file__).resolve().parents[1]
OLD = BASE / 'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010'
OUT = BASE / 'outputs/PMFS_C1B_LOCAL_INITIAL_STATE_AUDIT_20261011'
SHARE = Path('D:/ZYC/A-gas/workspace/PMFS_C1B_LOCAL_INITIAL_STATE_AUDIT_20261011')

def dump(name, obj):
    (OUT/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf8')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    started = time.monotonic()
    OUT.mkdir(exist_ok=True); SHARE.mkdir(exist_ok=True)
    status = json.loads((OLD/'run/RUNTIME_STATUS.json').read_text())
    # Receipt of the completion log is only an upper bound, not startTime.
    cutoff = int(status['goal_invocation_ROS_ns'])
    observed_init = int(status['native_initialization_observed_ROS_ns'])
    allowed = {
        'run/RUNTIME_STATUS.json': 'selected clock fields only; no outcome/truth',
        'run/PHYSICAL_FRAME_TIME.csv': 'frame and physical time only; no filament state',
        'runtime/physical_clock_trace.csv': 'clock binding and frame timestamps only',
        'runtime/raw_ros_cdr.jsonl.gz': 'topic/receipt metadata; decode only wind, clock, permitted TF prefix',
        'runtime/consumer_messages.csv': 'wind metadata counts only; no gas values',
        'source/gsl/Common/Algorithm.cpp': 'Initialize timing source, no parameter truth values',
        'runtime_driver.py': 'capture/timing code only',
        'runtime/launch.log': 'literal INITIALIZATON COMPLETED logger timestamp only',
        'run/B4_generation_RESOLVED.yaml': 'explicit public parameter allowlist only',
        'runtime/resolved_player_parameters.yaml': 'explicit clock/playback allowlist only',
        'runtime/preflight_PioneerP3DX_Anemometer_parameters.yaml': 'instrument metadata',
        'runtime/preflight_PioneerP3DX_PID_parameters.yaml': 'instrument metadata',
    }
    registry = {n: {'sha256': sha(OLD/n), 'projection': role} for n,role in allowed.items()}
    registry['contract'] = {'path': 'outputs/PMFS_R3_R5_CONTINUOUS_20261011/authorization/CODEX_R3_R5_CONTINUOUS_RESEARCH_CONTRACT_zh.md', 'sha256': sha(BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011/authorization/CODEX_R3_R5_CONTINUOUS_RESEARCH_CONTRACT_zh.md')}
    freeze = {'UTC': datetime.now(timezone.utc).isoformat(), 'cutoff_receipt_ROS_ns': cutoff,
        'cutoff_basis': 'goal invocation BEFORE native initialization; conservative prefix, no future decoding',
        'allowed_source_files': registry,
        'denied': ['actual test plume/filaments/concentration fields', 'actual source coordinates/labels', 'all full CFD fields and /wind_value service answers', 'future wind/gas payloads', 'candidate/posterior/result values'],
        'historical_auditor_exposure': 'B4 was already inspected by supervisor. No independent-confirmation claim; inference input projection below excludes labels.',
        'physics_calls': 0, 'goals': 0, 'is_new_scientific_prior_registered': False}
    dump('C1B_INPUT_SCOPE_FREEZE.json', freeze)
    table = []
    with (OLD/'run/PHYSICAL_FRAME_TIME.csv').open(newline='', encoding='utf8') as f:
        for r in csv.DictReader(f):
            table.append({k:r[k] for k in ['frame','physical_snapshot_time_s','post_step_time_s','wind_index_at_save']})
    times = {int(r['frame']):float(r['physical_snapshot_time_s']) for r in table}
    with (OUT/'C1B_FRAME_TIME_METADATA_ONLY.csv').open('w', newline='', encoding='utf8') as f:
        w=csv.DictWriter(f, fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    with (OLD/'runtime/physical_clock_trace.csv').open(newline='', encoding='utf8') as f:
        clocks=list(csv.DictReader(f))
    # Later clock queries are not required for initialization and are excluded.
    prefix_clocks=[r for r in clocks if int(r['receipt_ros_ns'])<=cutoff]
    anchors=sorted(set(int(r['anchor_ros_ns']) for r in prefix_clocks))
    assert len(anchors)==1
    anchor=anchors[0]; frame0=times[500]
    expected=lambda ns: frame0+(ns-anchor)/1e9
    residuals=[abs(float(r['target_internal_s'])-expected(int(r['receipt_ros_ns']))) for r in prefix_clocks]
    with (OUT/'C1B_ALLOWED_CLOCK_PREFIX.csv').open('w', newline='', encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(prefix_clocks[0]));w.writeheader();w.writerows(prefix_clocks)
    public_keys={'time_step','num_filaments_sec','variable_rate','filament_growth_gamma','filament_noise_std','gas_type','temperature','pressure','fixed_frame','results_time_step','results_min_time','save_results','wind_time_step','allow_looping','initial_iteration','player_freq','use_sim_time','frequency','noise_std','sensor_model','use_PID_correction_factors'}
    public={}
    for n in [n for n in allowed if n.endswith('.yaml')]:
        obj=yaml.safe_load((OLD/n).read_text())
        def walk(x,path=''):
            if isinstance(x,dict):
                for k,v in x.items():
                    if isinstance(v,dict):walk(v,path+'/'+str(k))
                    elif k in public_keys:public[n+path+'/'+k]=v
        walk(obj)
    topic_stats={}; kept={}; early=0; out_path=SHARE/'allowed_prefix_transport.jsonl.gz'
    allowed_topics={'/tf','/tf_static','/clock','/PioneerP3DX/Anemometer/WindSensor_reading','/b4/wind_to'}
    with gzip.open(OLD/'runtime/raw_ros_cdr.jsonl.gz','rt',encoding='utf8') as f, gzip.open(out_path,'wt',encoding='utf8') as dest:
        for line in f:
            # Decoder never receives gas, maps, query responses or later payloads.
            o=json.loads(line);topic=o['topic'];receipt=int(o['receipt_ns'])
            st=topic_stats.setdefault(topic,{'count':0,'first_receipt_ns':receipt,'last_receipt_ns':receipt,'prefix_count':0})
            st['count']+=1;st['last_receipt_ns']=receipt
            if receipt<=cutoff:st['prefix_count']+=1
            if topic not in allowed_topics or receipt>cutoff:continue
            dest.write(json.dumps({k:o[k] for k in ['topic','receipt_ns','cdr_hex']})+'\n')
            kept[topic]=kept.get(topic,0)+1
            if 'WindSensor' in topic and receipt<anchor:early+=1
    # Only consumer timestamps are counted; gas values are not used.
    with (OLD/'runtime/consumer_messages.csv').open(newline='',encoding='utf8') as f:
        wind_meta=[{k:r[k] for k in ['receipt_ns','stamp_ns','frame']} for r in csv.DictReader(f) if r['kind']=='wind']
    init_logs=[]
    for line in (OLD/'runtime/launch.log').read_text(errors='replace').splitlines():
        if 'INITIALIZATON COMPLETED' in line:
            match=re.search(r'\[INFO\] \[([0-9.]+)\]',re.sub(r'\x1b\[[0-9;]*m','',line))
            if match:init_logs.append({'logger_timestamp':match.group(1),'clock_domain':'logger epoch; not node ROS startTime'})
    # launch.log is projected by a fixed literal marker only. No contents copied.
    registry['runtime/launch.log']={'sha256':sha(OLD/'runtime/launch.log'),'projection':'literal INITIALIZATON COMPLETED logger timestamp only'}
    data={
        'release_origin_physical_s':0.0, 'release_origin_evidence':'RunningSimulation starts currentTime=0 and frame0 metadata is t=0; no actual plume read',
        'frame500_physical_s':frame0,'ROS_player_anchor_ns':anchor,
        'physical_time_binding':'t_phys=267.307098389+(t_ROS-11.095207360) for this archived epoch at/after anchor',
        'binding_max_prefix_residual_s':max(residuals,default=None),
        'goal_invocation_ROS_ns':cutoff,'goal_invocation_physical_s':expected(cutoff),
        'native_init_observed_ROS_ns_upper_bound':observed_init,
        'native_init_observed_physical_s_upper_bound':expected(observed_init),
        'native_exact_startTime':'NOT_SEPARATELY_RECORDED; observed marker is delayed, logger timestamp is another clock domain',
        'native_init_lower_bound_ROS_ns':cutoff,'init_logger_markers':init_logs,
        'prefix_clock_rows':len(prefix_clocks),'topics_metadata':topic_stats,'kept_prefix_counts':kept,
        'wind_messages_before_player_anchor':early,'before_anchor_rule':'unbound to this playback physical epoch; do not extrapolate backward',
        'PMFS_first_wind_consumer_metadata':wind_meta[0],
        'native_wind_consumed_before_conservative_cutoff':sum(int(x['receipt_ns'])<=cutoff for x in wind_meta),
        'full_release_to_start_local_history':'ABSENT_IN_THIS_CAPTURE; causal observations after playback cannot identify unobserved past wind',
        'public_instrument_and_release_metadata':public,
        'filtered_transport_sha256':sha(out_path),'filtered_transport_bytes':out_path.stat().st_size,
        'filtered_transport_caveat':'intermediate audit-only transport; TF frames must be filtered and decoded before publishing consumer inputs',
        'actual_initial_concentration_state_loaded':False,'actual_source_label_loaded_as_input':False,'full_CFD_loaded':False,
        'input_sha256':registry,
    }
    dump('C1B_ALLOWED_HISTORY_AND_CLOCK.json',data)
    dump('C1B_READONLY_AUDIT_RECEIPT.json',{'UTC':datetime.now(timezone.utc).isoformat(),'active_wall_s':time.monotonic()-started,'new_physics_calls':0,'goals':0,'decoded_future_payloads':0,'gas_values_used':0,'clock_preinspection_fault':'exploratory list/dict inspection raised AttributeError; no physics/result changed; corrected in scoped script'})
    print(json.dumps({k:data[k] for k in ['frame500_physical_s','ROS_player_anchor_ns','goal_invocation_physical_s','native_init_observed_physical_s_upper_bound','prefix_clock_rows','kept_prefix_counts','native_wind_consumed_before_conservative_cutoff']}))

if __name__=='__main__':main()
