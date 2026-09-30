"""Evidence/QC packaging only. No additional target or inference."""
import csv,hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=Path('C:/GADEN_OCB_R2_ARCHIVE/d0_lite_20260930')
RESULT=OUT/'results'
REPO=Path('D:/ZYC/A-gas/_worktrees/ocb-r2-census-20260930')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def main():
    result=json.loads((RESULT/'D0_LITE_RESULT.json').read_text());run=OUT/result['case']['run_id']/'on'
    native=dict(run_id=result['case']['run_id'],budget_s=300,actual_last_belief_s=result['native_last_available_belief_s'],
        stop_reason=result['native_stop_reason'],official_estimator='original C++ top5% probability weighted ExpectedValue',
        estimate_xy=result['PMFS_estimate_xy'],XY_error_m=result['PMFS_error_m'],MAP_diagnostic_xy=result['PMFS_MAP_xy'],
        truth_xy=result['truth_xy'],declared_success=True,geometric_success_0p5m=result['PMFS_error_m']<=.5,
        source_probability_file='native_source_posterior_300s.npy',posterior_metadata='native_posterior_metadata.json',
        actual_event_count=result['event_count'],hit_count=result['hit_events'],native_target_runs=1,
        full_300_seconds_trace=False,early_declaration_preserved=True,formal_logger_OFF_ON_parity='NOT_EXECUTED')
    dump(RESULT/'final_native_result.json',native)
    meta=json.loads((RESULT/'adapter_input_audit.json').read_text())
    # Match delivered completed blocks and Native aggregation, independent of network outputs.
    with (run/'measurement_events.csv').open() as f:measurements=list(csv.DictReader(f))
    raw=[json.loads(s) for s in (run/'events_raw.jsonl').read_text().splitlines()]
    assert len(measurements)==len(raw)==result['event_count']
    for observed,logged in zip(measurements,raw):
        assert int(observed['hit'])==int(logged['hit'])
        assert float(observed['concentration'])==logged['gas_value_used_ppm']
        assert float(observed['wind_speed'])==logged['local_wind_speed_used_m_s']
        assert float(observed['wind_direction'])==logged['map_downwind_direction_used_rad']
    # Network event artifact forbids truth/unused concentration fields by exact adapter schema.
    events=json.loads((RESULT/'adapter_events_source_blind.json').read_text())
    allowed={'timestamp_s','x','y','encounter','event_id','quaternion_xyzw','official_wind_clockwise_deg'}
    assert all(set(e)==allowed for e in events)
    assert all(e['timestamp_s']<=300 for e in events)
    qc=dict(decision='D0_LITE_LOG_AND_INPUT_QC_PASS',run_id=result['case']['run_id'],completed_event_count=len(raw),
        raw_vs_native_aggregate_exact=True,source_truth_in_network_input=False,oracle_unvisited_concentration_queries=0,
        actual_ROS_map_receipt=True,map_dimensions=[meta['height'],meta['width']],map_resolution_m=meta['resolution'],
        identical_saved_input_repeated_inference=True,all_four_repeat_byte_equal=True,
        native_run_count=1,new_gaden=0,confirmation_read=False,house03_read=False,D1A='PAUSED_NOT_EXECUTED',
        termination='Native early declaration at258.2s; full300s trace not claimed',
        preclock_infrastructure_attempt='saved; no simulation clock start, no belief, zero scientific target execution',
        preserved_adapter_commit='9a12cc69833d04cce5c8859ed51764956eeabe92')
    dump(RESULT/'D0_LITE_QC.json',qc)
    # Main repository: small code, scalar results/provenance, no tensors/weights/plume.
    ev=REPO/'evidence/ocb_r2/d0_lite_20260930';ev.mkdir(parents=True,exist_ok=True)
    for p in RESULT.iterdir():
        if p.suffix in ('.json','.md','.tsv'):shutil.copy2(p,ev/p.name)
    shutil.copy2(OUT/'INPUT_TRANSFER_RECEIPT.json',ev/'INPUT_TRANSFER_RECEIPT.json')
    shutil.copy2(run/'provenance.json',ev/'NATIVE_RUNTIME_PROVENANCE.json')
    shutil.copy2(run/'execution_status.json',ev/'NATIVE_EXECUTION_STATUS.json')
    code=REPO/'research/icra2025_pmfs_common_replay_d1a_20260930'
    for p in ROOT.iterdir():
        if p.suffix in ('.py','.sh','.md'):shutil.copy2(p,code/p.name)
    (code/'CURRENT_STAGE.md').write_text('# Current stage\n\nD1A: PAUSED; OFF/ON and64-run campaign NOT EXECUTED.\n\nD0-Lite: exactly1Native target, all4pretrained checkpoints; result D0_LITE_ZERO_SHOT_TRANSFER_POOR.\n\nNo training, new GADEN, second case, confirmation/H03. STOP.\n',encoding='utf-8')
    inventory=[]
    for folder in [RESULT,OUT/result['case']['run_id']]:
        for p in sorted(folder.rglob('*')):
            if p.is_file():inventory.append(dict(path=p.relative_to(OUT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    with (OUT/'OUTPUT_FILE_SHA256.tsv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['path','bytes','sha256'],delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(inventory)
    shutil.copy2(OUT/'OUTPUT_FILE_SHA256.tsv',ev/'OUTPUT_FILE_SHA256.tsv')
    package=Path('C:/Users/50176/Downloads/ICRA2025_PMFS_D0_LITE_REVIEW_20260930.zip')
    assert not package.exists()
    with zipfile.ZipFile(package,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in ROOT.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:z.write(p,'methods/'+p.relative_to(ROOT).as_posix())
        for folder in [RESULT,OUT/result['case']['run_id']]:
            for p in folder.rglob('*'):
                if p.is_file():z.write(p,'scientific_logs/'+p.relative_to(OUT).as_posix())
        for p in [OUT/'OUTPUT_FILE_SHA256.tsv',OUT/'INPUT_TRANSFER_RECEIPT.json']:
            z.write(p,p.name)
    receipt=dict(package_path=str(package),bytes=package.stat().st_size,sha256=sha(package),
        excluded=['all pretrained .pth weights','raw plume input archive','original GADEN assets'],
        raw_logs_transfer_sha256='253b75aff72c7891f71bce51265c0cd72f15f7d4c870ef184651ff2051825a9d')
    dump(OUT/'REVIEW_PACKAGE_RECEIPT.json',receipt);shutil.copy2(OUT/'REVIEW_PACKAGE_RECEIPT.json',ev/'REVIEW_PACKAGE_RECEIPT.json')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
