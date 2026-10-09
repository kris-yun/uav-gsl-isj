"""Read-only, standard-library verification of the saved R3 ROS evidence.

Usage: python verify_r3.py [package_directory]
No ROS process, simulator, network request, or source update is started.
"""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def wrap(x):
    return math.atan2(math.sin(x), math.cos(x))


def rows(p):
    with p.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def verify(root):
    real = root / 'evidence/real_ros'
    raw = real / 'results/stamp'
    manifest = json.loads((real / 'REMOTE_FILE_HASHES.json').read_text())
    for name, expected in manifest.items():
        assert sha(real / name) == expected['sha256'], name
    original = (real / 'code/Algorithm_original.cpp').read_bytes()
    stamped = (real / 'code/Algorithm_stamped.cpp').read_bytes()
    needle = b'anemometer_downWind_pose.header.frame_id = msg->header.frame_id;'
    assert original.count(needle) == 1
    assert original.replace(needle, b'anemometer_downWind_pose.header = msg->header;') == stamped
    assert hashlib.sha256(original).hexdigest() == 'c22d05a445b60dc39e7da98b4b86b9186e898c3644b86638d0b6f2977d9cc2d7'
    contract = json.loads((raw / 'PRE_RUN_CONTRACT.json').read_text())
    cases = json.loads((raw / 'CASES.json').read_text())
    assert [c['id'] for c in cases] == contract['cases']
    assert json.loads((raw / 'COMPLETE.json').read_text()) == {'cases': 5, 'complete': True}
    traces = {k: list(csv.reader((raw / n).open(newline=''))) for k, n in [('N0','N0_original.csv'),('N1','N1_stamped.csv'),('GMRF','GMRF.csv')]}
    results = []
    for c in cases:
        expected = math.atan2(c['v'], c['u'])
        sample = c['TF_at_sample']
        assert sample['stamp_ns'] == c['stamp_ns']
        assert math.hypot(sample['x']-c['x'],sample['y']-c['y']) < 1e-8
        assert abs(wrap(sample['yaw']-c['yaw'])) < 1e-8
        assert c['publisher_use_sim_time'] is False
        gm = c['GMRF']
        assert gm in traces['GMRF']
        assert int(gm[0])*10**9+int(gm[1]) == c['stamp_ns']
        assert gm[2] == c['frame'] and int(gm[11]) == 0
        gm_error = abs(wrap(float(gm[5])-expected))
        stored_pos_error = math.hypot(float(gm[14])-c['x'],float(gm[15])-c['y'])
        gm_age = (int(gm[10])-c['stamp_ns'])/1e9
        assert int(gm[8]) == 1 and int(gm[9]) == 1 and int(gm[12]) == 1
        assert gm_error < contract['angle_tolerance_rad']
        assert stored_pos_error < contract['position_tolerance_m']
        assert 0 <= gm_age < contract['age_limit_s']
        local_to = float(c['N0'][4]); local_from = float(gm[4])
        assert abs(wrap(local_to+c['yaw']-expected)) < 1e-6
        assert abs(wrap(local_from+c['yaw']+math.pi-expected)) < 1e-6
        if c['id'] != 'delayed_rotate90':
            assert c['N0'][8:13] == c['N1'][8:13], 'fixed-pose readings changed'
        for variant in ['N0','N1']:
            p = c[variant]
            assert p in traces[variant]
            assert int(p[0])*10**9+int(p[1]) == c['stamp_ns']
            assert p[2] == c['frame'] and p[5] == 'map' and int(p[14]) == 0
            transform_ns = int(p[6])*10**9+int(p[7])
            age = (int(p[13])-c['stamp_ns'])/1e9
            assert 0 <= age < contract['age_limit_s']
            consume = c['TF_at_'+variant+'_consume']
            drift_xy = math.hypot(consume['x']-sample['x'],consume['y']-sample['y'])
            drift_yaw = abs(wrap(consume['yaw']-sample['yaw']))
            assert abs(drift_xy-c[variant+'_pose_drift_xy_m']) < 1e-10
            assert abs(drift_yaw-c[variant+'_pose_drift_yaw_rad']) < 1e-10
            direction_error = abs(wrap(float(p[10])-expected))
            stop_error = abs(wrap(float(p[12])-expected))
            pose_error = math.hypot(float(p[8])-sample['x'],float(p[9])-sample['y'])
            scoped_input = drift_xy < contract['fixed_pose_drift_xy_limit'] and drift_yaw < contract['fixed_pose_drift_yaw_limit']
            passed = max(direction_error,stop_error) < contract['angle_tolerance_rad'] and pose_error < contract['position_tolerance_m']
            if variant == 'N1':
                assert transform_ns == c['stamp_ns']
                assert passed, (c['id'],variant)
            elif scoped_input:
                assert passed, (c['id'],variant)
            else:
                assert c['id'] == 'delayed_rotate90' and not passed
                assert abs(direction_error-math.pi/2) < 1e-4
            results.append(dict(case=c['id'],variant=variant,expected_map_TO_rad=expected,actual_map_TO_rad=float(p[10]),angle_error_rad=direction_error,stop_average_error_rad=stop_error,pmfs_xy_error_m=pose_error,gmrf_angle_error_rad=gm_error,gmrf_stored_xy_error_m=stored_pos_error,msg_stamp_ns=c['stamp_ns'],returned_transform_stamp_ns=transform_ns,transform_stamp_offset_s=(transform_ns-c['stamp_ns'])/1e9,receipt_age_s=age,gmrf_receipt_age_s=gm_age,pose_drift_xy_m=drift_xy,pose_drift_yaw_rad=drift_yaw,stationary_scope_input=scoped_input,physical_reading_pass=passed))
    cleanup = json.loads((real/'PROCESS_CLEANUP.json').read_text())
    assert cleanup['test_processes_remaining'] == []
    frozen = root/'evidence/frozen_R1'
    fm = json.loads((frozen/'r1_scores_frozen_manifest.json').read_text())
    for n in ['measurement_events.csv','measured_map_at_update.csv','frozen_candidate_geometry.csv','wind_source_update.csv']:
        assert sha(frozen/n) == fm['source_blind_inputs'][n], n
    events = rows(frozen/'measurement_events.csv')
    grid = rows(frozen/'measured_map_at_update.csv')
    wind = rows(frozen/'wind_source_update.csv')
    leaves = rows(frozen/'frozen_candidate_geometry.csv')
    assert len(events)==20 and len(grid)==1102 and len(wind)==626 and len(leaves)==87
    free = {int(r['cell_index']) for r in grid if r['occupancy']=='Free'}
    assert {int(r['cell_index']) for r in wind} == free
    assert len(free)==626
    maps = fm['arms']['C']['candidate_map_sha256']
    for candidate_id,expected in maps.items():
        p=frozen/'R1_arm_C/maps'/f'{candidate_id}.f32'
        assert sha(p)==expected and p.stat().st_size==len(grid)*4
    assert len(maps)==87
    availability=json.loads((real/'FROZEN_INPUT_AVAILABILITY.json').read_text())
    assert availability['results_members']==[]
    assert not {'stamp','stamp_ns','frame_id','t_sim_s','iteration','raw_message_ids','TF_at_sample','TF_at_consume'} & set(events[0])
    assert not {'t_sim_s','iteration','stamp_ns','frame_id'} & set(wind[0])
    old=json.loads((root/'evidence/previous/CORE_PARITY_RESULTS.json').read_text())
    assert old['score_only_current_recomputation']['online_native_full_candidate_maps_available'] is False
    assert old['score_only_current_recomputation']['online_native_final_posterior_available'] is False
    source_manifest=root/'SOURCE_MANIFEST.json'
    if source_manifest.exists():
        for name, expected in json.loads(source_manifest.read_text()).items():
            assert sha(root/name)==expected,name
    package_hash_count=0
    checksum=root/'SHA256SUMS.txt'
    if checksum.exists():
        for line in checksum.read_text().splitlines():
            expected,name=line.split('  ',1)
            assert sha(root/name)==expected,name
            package_hash_count+=1
    return dict(STAMP_PATCH='PASS',STATIONARY_INTERFACE='PASS',original_stationary_cases_pass=sum(r['variant']=='N0' and r['stationary_scope_input'] and r['physical_reading_pass'] for r in results),patched_cases_pass=sum(r['variant']=='N1' and r['physical_reading_pass'] for r in results),R3B='SCOPED_P1b_HOLD',R3B_execution='NOT_RUN_INPUT_QUALIFICATION_HOLD',native_source_updates_this_round=0,physical_mechanism='NOT_YET_QUALIFIED',frozen_C_maps_hashes_pass=87,frozen_delivered_events=20,known_native_results_directory_empty=True,package_hashes_pass=package_hash_count,rows=results)


if __name__=='__main__':
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
    print(json.dumps(verify(root),ensure_ascii=False,indent=2))
