#!/usr/bin/env python3
"""Bind existing OPEN AOD plumes and exact writer times; no new gas simulation."""
import csv, hashlib, json
from pathlib import Path

ROOT=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
AOD=Path('/home/zyc/aod_house03_f1_full624_20260927')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    with Path(p).open() as f:return list(csv.DictReader(f,delimiter='\t'))
def main():
    out=ROOT/'campaign_contract';out.mkdir(exist_ok=False)
    manifest=AOD/'protocol/frozen/HOUSE03_FUTURE_GADEN_SEEDS_96.tsv'
    panel=AOD/'protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv'
    cases=[]
    for index,row in enumerate(rows(manifest)):
        s=int(row['source_index']);r=int(row['realization_index']);label=f'source_{s}_replica_{r}'
        if (s,r)==(0,0):
            realization=Path('/home/zyc/ros2_ws/aod_house03_f1_full624_targets_20260927')/label/'realization'
            meta=AOD/'review_metadata'/label
        else:
            meta=Path('/mnt/hgfs/workspace/_staging/AOD_F1_AMENDED_TARGETS_20260927')/label
            realization=meta/'realization'
        time_map=meta/'RESULT_TIME_MAP.tsv';configuration=meta/'RUN_CONFIGURATION.json'
        assert realization.is_dir() and time_map.is_file() and configuration.is_file(),label
        times=rows(time_map)
        assert float(times[0]['physical_sim_time_s'])==0 and float(times[-1]['physical_sim_time_s'])>=300,label
        config=json.loads(configuration.read_text())
        assert config['manifest_row']['requested_seed']==row['requested_seed'],label
        assert float(config['options']['source_position_z'])==.2
        for t in times:
            assert (realization/('iteration_'+t['save_record_id'])).is_file(),(label,t)
        case={'case_id':label,'source_index':s,'realization_index':r,'source_id':row['source_id'],
            'plume_id':row['seed_key'],'requested_seed':int(row['requested_seed']),
            'initial_pose_id':'H03_FIXED_2_0_0_0_Z_0_2','observation_contract_id':'ACTUAL_WRITER_TIME_CAUSAL_HOLD_300S_V1',
            'candidate_support_id':'AOD_FULL624_MODEL_ONLY','truth_xy':[float(row['x_m']),float(row['y_m'])],
            'scenario_root':'/mnt/hgfs/workspace/GADEN_files/scenarios/House03','wind':row['wind'],
            'realization':str(realization),'time_map':str(time_map),'time_map_sha256':sha(time_map),
            'run_configuration_sha256':sha(configuration),'arm_rotation_offset':index%4}
        path=out/(label+'.json');path.write_text(json.dumps(case,indent=2,sort_keys=True)+'\n');cases.append(case)
    assert len(cases)==96 and len({c['requested_seed'] for c in cases})==96
    freeze={'campaign_status':'OPEN_DEVELOPMENT_NOT_FRESH_CONFIRMATION','new_plumes':0,'source_count':12,
        'realizations_per_source':8,'cases':96,'arms':['native_pmfs','candidate_gru','brg','brg_ungated'],
        'runs':384,'budget_s':300,'seed':0,'realtime_factor':1.,'convergence_threshold':.5,
        'primary':'last finite valid source estimate at <=300 s; Euclidean error <=0.5m, timeout separately',
        'estimate':'same Native top5-percent probability weighted source estimate for all arms',
        'measurement_blocks_per_stop':5,'measurement_samples_per_block':10,'sim_dt_s':.2,
        'initial_pose_xy':[2.,0.],'sensor_z':.2,'source_panel_sha256':sha(panel),'seed_manifest_sha256':sha(manifest),
        'case_sha256':{p.name:sha(p) for p in sorted(out.glob('source_*.json'))},
        'case_order':'source_index ascending, replica ascending; four arm order rotated by case_index mod4',
        'deployment_failures':'service/TCP/navigation failure or no finite valid estimate -> geometric failure'}
    (out/'CAMPAIGN_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n')
    print(json.dumps(freeze,indent=2))
if __name__=='__main__':main()
