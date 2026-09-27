"""Only the signed 4-case pilot; no automatic 96-case campaign."""
import concurrent.futures,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
ARMS=['native_pmfs','candidate_gru','brg','brg_ungated']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    contract=ROOT/'pilot_contract_resolved';binding=json.loads((contract/'PILOT_PRETRAIN_BINDING.json').read_text())
    assert binding['P1_STOP_NO_AUTOMATIC_FULL_CAMPAIGN'] and binding['P1_cumulative_runs']==16
    weights=json.loads((ROOT/'CHECKPOINT_FREEZE.json').read_text())
    for v,h in weights['weights_sha256'].items():assert sha(ROOT/f'trained_full/{v}/best.pt')==h
    out=Path('/mnt/hgfs/workspace/_staging/BRG_NATIVE615_PILOT_P1_20260927');out.mkdir(exist_ok=False)
    sources=[ROOT/'tools/bind_native_case_vm.py',ROOT/'tools/run_bound_case_vm.sh',ROOT/'integration/brg_existing_native.launch.py']
    for package in ['pmfs_brg','../vgr_execution_v2/vgr_bridge']:
        folder=(ROOT/package).resolve()
        if folder.is_dir():sources+=list(folder.glob('*.py'))
    binary=Path('/home/zyc/ros2_ws/brg_closedloop_20260927/install/gsl_server/lib/gsl_server/gsl_actionserver_node')
    freeze={'binding_sha256':sha(contract/'PILOT_PRETRAIN_BINDING.json'),'checkpoint_freeze_sha256':sha(ROOT/'CHECKPOINT_FREEZE.json'),
        'weights':weights['weights_sha256'],'code':{str(p):sha(p) for p in sources},'native_binary_sha256':sha(binary),
        'cases':binding['P1_cumulative_cases'],'arms':ARMS,'budget_s':300,'radius_m':.5,'stage1_stop':True,'maximum_parallel_arms':4,
        'no_target_conditioned_selection':True,'only_existing_OPEN_House03_gas':True}
    (out/'PRE_PILOT_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n');print('PRE_PILOT_FROZEN',sha(out/'PRE_PILOT_FREEZE.json'),flush=True)
    records=[]
    for ci,case_id in enumerate(binding['P1_cumulative_cases']):
        stage='P0' if ci==0 else 'P1';case=contract/(case_id+'.json')
        assert sha(case)==binding['case_sha256'][case.name]
        def run(ai):
            arm=ARMS[ai];dest=out/(case_id+'__'+arm+'.json');log=out/(case_id+'__'+arm+'_adapter.log')
            cmd=['bash',str(ROOT/'tools/run_bound_case_vm.sh'),'--arm',arm,'--case-file',str(case),'--budget-s','300','--output',str(dest),'--domain',str(224+ai)]
            with log.open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=2400)
            if p.returncode or not dest.exists():raise RuntimeError('adapter infrastructure stop: '+case_id+'/'+arm)
            row=json.loads(dest.read_text());assert row['case_id']==case_id and row['arm']==arm and not row['software_smoke'];return row
        print(stage,'RUNNING',case_id,flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,range(4)))
        records+=rows
        (out/'all_results.jsonl').write_text(''.join(json.dumps(row,sort_keys=True)+'\n' for row in records))
        print(stage,'COMPLETE',json.dumps([{k:r.get(k) for k in ['arm','status','failure_reason','geometric_success','final_source_error_m','measurement_count','hit_count','path_length_m']} for r in rows]),flush=True)
        if ci==0:
            # Pure execution faults block the remaining cases; poor geometry is not a fault.
            faults=[r for r in rows if r['status'] in ['infrastructure_error','service_error','algorithm_error']]
            if faults:
                (out/'P0_INFRASTRUCTURE_STOP.json').write_text(json.dumps(faults,indent=2)+'\n');raise RuntimeError('P0 execution fault; preserve raw artifacts and repair before remaining cases')
    assert len(records)==16
    p=subprocess.run(['python3',str(ROOT/'tools/evaluate_closed_loop.py'),'--jsonl',str(out/'all_results.jsonl'),'--arms']+ARMS+['--radius-m','.5','--out',str(out/'P1_RESULT.json')],capture_output=True,text=True,check=True)
    (out/'evaluation.log').write_text(p.stdout+p.stderr)
    result=json.loads((out/'P1_RESULT.json').read_text());result.update(stage='P1_COMPLETE_STOP',scored_runs=16,cases=4,new_plumes=0,full96_campaign_started=False,
        pilot_not_scientific_pass=True,raw_output_directory=str(out),support_count=615,
        per_run=records,descriptive_strata={a:{s:{'cases':sum(r['arm']==a and r['reporting_stratum']==s for r in records),'successes':sum(r['geometric_success'] for r in records if r['arm']==a and r['reporting_stratum']==s)} for s in ['in_support','support_misspecification']} for a in ARMS})
    (out/'P1_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('P1_COMPLETE_STOP',json.dumps(result['comparison']),flush=True)
if __name__=='__main__':main()
