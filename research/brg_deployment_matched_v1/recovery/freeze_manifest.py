"""Freeze metadata-only recovery list before regenerating any plume."""
from pathlib import Path
import csv,json,hashlib,collections
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=ROOT/'PROPOSED_RECOVERY_CANDIDATES_72.csv'
    rows=list(csv.DictReader(p.open(newline='',encoding='utf8')))
    audit=json.loads((ROOT.parent/'evidence/VERIFIED_ASSET_AUDIT.json').read_text())
    split=json.loads((ROOT/'PROPOSED_PRE_DATA_SPLIT_AND_COST.json').read_text())
    if len(rows)!=72 or not audit['all_recorded_hashes_match'] or split['72_run_units']!=72:raise RuntimeError('incomplete source audit')
    original={r['path']:r for r in audit['records']}
    splitmap={(r['house'],r['source_id']):r['split'] for r in split['source_splits']}
    winds={}
    for r in audit['records']:
        if r['metadata'].get('wind_path'):
            key=(r['house'],r['wind']);w=r['metadata']['wind_path']
            if key in winds and winds[key]!=w:raise RuntimeError('wind path drift')
            winds[key]=w
    proposed=[]
    for n,r in enumerate(rows):
        old=original[r['historical_cube_path']];meta=old['metadata'];key=(r['house'],r['wind'])
        if (old['sha256']!=r['historical_cube_sha256'] or old['metadata_sha256']!=r['historical_metadata_sha256'] or meta['requested_seed']!=int(r['historical_seed']) or old['raw_frame_count']!=0):raise RuntimeError('historical identity drift')
        if meta['source_id']!=r['source_id'] or any(abs(float(r[k])-float(v))>1e-6 for k,v in zip(('x_m','y_m','z_m'),meta['source_xyz'])):raise RuntimeError('source drift')
        if key not in winds:raise RuntimeError('missing wind path')
        proposed.append({'ordinal':n+1,'house':r['house'],'wind':r['wind'],'source_id':r['source_id'],'xyz':meta['source_xyz'],'historical_seed':meta['requested_seed'],'split':splitmap[(r['house'],r['source_id'])],'original_cube_path':r['historical_cube_path'],'original_cube_sha256':r['historical_cube_sha256'],'original_metadata_sha256':r['historical_metadata_sha256'],'binary_sha256':meta['binary_sha256'],'occupancy_sha256':meta['occupancy_sha256'],'wind_path':winds[key],'wind_iteration_hashes':meta['wind_iteration_hashes'],'run_id':f"{r['house']}_{r['wind']}_{r['source_id']}_seed{r['historical_seed']}"})
    if len({r['historical_seed'] for r in proposed})!=72 or len({r['run_id'] for r in proposed})!=72:raise RuntimeError('seed/run identity collision')
    if collections.Counter(r['split'] for r in proposed)!={'train':split['train_plume_units'],'dev':split['dev_plume_units'],'eval':72-split['train_plume_units']-split['dev_plume_units']}:raise RuntimeError('split budget drift')
    binary={r['binary_sha256'] for r in proposed};assert len(binary)==1
    config={'sim_time':'300.0','time_step':'0.1','num_filaments_sec':'7','variable_rate':'true','filament_stop_steps':'0','ppm_filament_center':'10.0','filament_initial_std':'10.0','filament_growth_gamma':'15.0','filament_noise_std':'0.01','gas_type':'10','temperature':'298.0','pressure':'1.0','concentration_unit_choice':'1','fixed_frame':'map','wind_time_step':'1.0','allow_looping':'true','loop_from_step':'1','loop_to_step':'10','save_results':'1','results_time_step':'0.5','results_min_time':'0.0','writeConcentrations':'false'}
    lock={'status':'SOURCE_AND_RESOURCE_FROZEN_BEFORE_NEW_SIMULATION','authorization_basis':'2026-09-28 direct request: if known backups absent, regenerate a small OPEN continuous dataset; bounded by package proposal to <=72 existing run units','house03_training_access':False,'old_v0_weight_initialization':False,'max_new_gaden_executions':72,'same_historical_seed_counts_as_new_independent_realization':False,'restored_records_offset_new_execution_count':True,'binary_sha256':next(iter(binary)),'source_zip_candidate_sha256':sha(p),'source_split_sha256':sha(ROOT/'PROPOSED_PRE_DATA_SPLIT_AND_COST.json'),'asset_audit_sha256':sha(ROOT.parent/'evidence/VERIFIED_ASSET_AUDIT.json'),'backup_index_sha256':sha(ROOT/'KNOWN_BACKUP_INDEX_AUDIT.json'),'simulation_parameters':config,'scratch_root':'/home/zyc/brg_v1_recovery_scratch_20260928','host_archive_root':'C:/Users/50176/Desktop/vm数据/BRG_V1_OPEN_CONTINUOUS_20260928','host_archive_free_bytes_at_audit':151719448576,'first_run_per_environment_resource_timebase_check':True,'planned_vgr_runs':split['base_vgr_runs_including_evaluation'],'formal_closed_loop_runs':32,'runs':proposed}
    target=ROOT/'FROZEN_RUN_MANIFEST.json'
    if target.exists():raise RuntimeError('refuse to overwrite run freeze')
    target.write_text(json.dumps(lock,indent=2)+'\n')
    print(json.dumps({'lock':str(target),'sha256':sha(target),'runs':len(proposed),'train':split['train_plume_units'],'dev':split['dev_plume_units'],'eval_source_cases':8,'planned_vgr_runs':split['base_vgr_runs_including_evaluation']},indent=2))
if __name__=='__main__':main()
