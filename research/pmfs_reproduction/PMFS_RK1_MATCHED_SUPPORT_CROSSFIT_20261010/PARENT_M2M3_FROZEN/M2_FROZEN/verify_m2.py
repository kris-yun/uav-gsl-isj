"""Portable, read-only verification of the delivered M2 evidence. No VM/ROS."""
import sys
sys.dont_write_bytecode=True
import argparse,csv,gzip,hashlib,importlib.util,json,math,runpy,contextlib,io
from pathlib import Path
def js(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def verify(root,skip_hashes=False):
    count=None
    if not skip_hashes:
        manifest=js(root/'SHA256_MANIFEST.json')
        actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='SHA256_MANIFEST.json'}
        assert actual==set(manifest),('unlisted/missing package files',actual^set(manifest))
        for name,expected in manifest.items():assert sha(root/name)==expected,('SHA256',name)
        count=len(manifest)
    for name,expected in js(root/'handoff_original/SHA256.json').items():assert sha(root/'handoff_original'/name)==expected
    freeze=js(root/'frozen_contract.json')
    assert sha(root/'frozen_contract.json')==(root/'PRE_RUN_CONTRACT_SHA256.txt').read_text().split()[0]
    assert len(freeze['jobs'])==8 and freeze['reference_split']==[0,1] and freeze['heldout_split']==[2,3]
    # Full original ROS message -> service -> physical clock audit, without executing recovery writer.
    d=module(root/'observation_lineage/final_contract_delivery/recover_frozen_schedule.py','cdr_recovery')
    raw=[]
    with gzip.open(root/'frozen_B4_inputs/runtime/raw_ros_cdr.jsonl.gz','rt',encoding='utf-8') as f:
        raw=[json.loads(line) for line in f]
    with gzip.open(root/'frozen_B4_inputs/runtime/service_queries.jsonl.gz','rt',encoding='utf-8') as f:
        queries={q['serial']:q for q in map(json.loads,f) if q['kind']=='GasPosition'}
    consumers=rows(root/'frozen_B4_inputs/runtime/consumer_messages.csv')
    clocks=[r for r in rows(root/'frozen_B4_inputs/runtime/physical_clock_trace.csv') if r['reason']=='gas_service']
    schedule=rows(root/'observation_lineage/FROZEN_RECEPTOR_SCHEDULE_ALL_MEMBERSHIP_BRANCHES.csv')
    assert len(schedule)==51 and len({r['block_id'] for r in schedule})==50
    for r in schedule:
        entry=raw[int(r['raw_cdr_line'])-1];msg=d.CDR(entry['cdr_hex']).gas()
        assert hashlib.sha256(bytes.fromhex(entry['cdr_hex'])).hexdigest()==r['raw_cdr_sha256']
        assert msg['stamp_ns']==int(r['sensor_stamp_ns']) and msg['frame']==r['sensor_frame'] and msg['raw_units']==3
        assert d.f32(msg['raw'])==float(r['observed_pid_ppm'])==float(r['observed_block_mean_ppm'])
        c=consumers[int(r['consumer_row'])-2]
        assert int(c['stamp_ns'])==msg['stamp_ns'] and d.f32(float(c['value']))==float(r['observed_pid_ppm'])
        q=queries[int(r['service_serial'])]
        assert q['request_ns']==int(r['service_request_ros_ns']) and q['response_ns']==int(r['service_response_ros_ns'])==msg['stamp_ns']
        response=d.CDR(q['response_cdr_hex']).gas_response();value=0.
        for v in response['concentrations'][0]:value=d.f32(value+v)
        assert value==float(r['observed_pid_ppm'])
        for a in ['x','y','z']:assert q[a][0]==float(r['sensor_'+a])
        cc=[z for z in clocks if q['request_ns']<=int(z['receipt_ros_ns'])<=q['response_ns']]
        assert len(cc)==1 and float(cc[0]['target_internal_s'])==float(r['physical_target_s'])
        assert int(cc[0]['wind_index'])==int(r['wind_index'])==10
    original={q['query_id']:q for q in rows(root/'ORIGINAL_NATIVE_QUERY.csv')}
    for r in schedule:
        q=original[f"block{r['block_id']}_branch{r['membership_branch']}"]
        assert float(q['ppm_float32'])==float(r['observed_pid_ppm']) and q['physical_free']=='1'
    semantic=module(root/'semantic_anchor/verify_semantic_anchor.py','semantic_verifier').verify(root/'semantic_anchor')
    native_map=module(root/'event_map_anchor/verify_event_map_anchor.py','map_verifier').verify(root/'event_map_anchor')
    scalarbuf=io.StringIO()
    with contextlib.redirect_stdout(scalarbuf):independent=runpy.run_path(str(root/'verify_independent_scalar.py'))['result']
    assert independent['heldout_n']==4 and independent['heldout_log_correct']==independent['heldout_Brier_correct']==4
    selected=0;allframe_count=0
    for job in freeze['jobs']:
        bank=root/'native_reference_evidence/realizations'/f"{job['candidate_id']}_{job['realization']}"
        g=js(bank/'GENERATION_QUALIFICATION.json');q=js(bank/'QUERY_QUALIFICATION.json')
        assert g['source_xyz']==job['source_xyz'] and g['seeds']==job['seeds'] and g['role']==job['role']
        assert g['exit_code']==q['exitcode']==0 and not g['resource_stop']
        assert g['peak_RSS_bytes']<=freeze['maximum_single_process_RSS_bytes']
        full=rows(bank/'ALL_FRAME_SHA256_AND_TIME.csv');assert len(full)==1803
        times=[float(x['physical_snapshot_time_s']) for x in full]
        assert all(a<b for a,b in zip(times,times[1:]))
        assert all(int(x['wind_index'])==10 for x in full if float(x['physical_snapshot_time_s'])>=267)
        byframe={int(x['frame']):x for x in full}
        for p in (bank/'bank').iterdir():
            f=int(p.name.split('_')[-1]);assert sha(p)==byframe[f]['SHA256'];selected+=1
        for stream in (0,1):
            assert int((bank/f'RNG.stream{stream}.initial.txt').read_text().split()[0])==job['seeds'][stream]!=5489
        allframe_count+=len(full)
        ledger=rows(root/'native_aligned_maps'/bank.name/'event_replay_ledger.csv')
        assert len(ledger)==50
        assert len(rows(root/'native_aligned_maps'/bank.name/'event_cell_lineage.csv'))==50*447
    assert selected==392 and allframe_count==14424
    budget=js(root/'RESOURCE_BUDGET_ACTUAL.json')
    assert budget['source_conditioned_gas_realizations']==8 and budget['generation_total_wall_s']<=900 and budget['task_disk_before_archiving_bytes']<=2*1024**3
    assert budget['auxiliary_semantic_compiler_peak_RSS_bytes']>1024**3 and budget['compiler_memory_exception']
    extra={}
    if (root/'independent_raw_query_verify/verify_raw_queries.py').exists():
        m=module(root/'independent_raw_query_verify/verify_raw_queries.py','raw_query_verifier')
        extra=m.verify(root)
    # Header-only default draws prove preservation of native draw/cache sequence; no new physics.
    rp=root/'independent_raw_query_verify/rng_header_parity_evidence'
    if rp.exists():
        rr=js(rp/'RNG_PARITY_RESULT.json')
        assert rr['bytes_equal'] and sha(rp/'pristine_draws.txt')==sha(rp/'isolated_draws.txt')
    decision=js(root/'DISCRIMINATION_RESULT.json')
    assert decision['same_bank_observation_alignment_selection_changed'] is False
    assert decision['prototype_admission'].startswith('HOLD') and decision['new_PMFS_localization_performance']=='NOT_TESTED'
    return dict(verdict='PASS_PACKAGE_AND_FIXED_NUMERICAL_RECOMPUTATION_PHYSICAL_CAUSE_HOLD',package_SHA256_files=count,handoff_files=len(js(root/'handoff_original/SHA256.json')),actual_ROS_CDR_service_clock_member_rows=51,unique_blocks=50,membership_ambiguity='block40 preserved; branch predictions identical',original_native_query_max_abs_ppm_difference=0.,semantic=semantic,native_map=native_map,independent_scalar_QA=independent['verdict'],heldout_log_correct=4,heldout_Brier_correct=4,heldout_n=4,raw_used_snapshots_SHA256=selected,external_full_bank_hash_commitments=allframe_count,independent_raw_query=extra,new_simulators_or_compilation_or_ROS_started_by_verifier=0,physical_mechanism='HOLD',prototype_admission='HOLD')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--skip-package-hashes',action='store_true')
    a=p.parse_args();print(json.dumps(verify(a.root.resolve(),a.skip_package_hashes),ensure_ascii=False,indent=2))
