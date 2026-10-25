"""Independent artifact checks; no new physical or algorithm runs."""
import argparse,hashlib,json,csv,zipfile,io
from pathlib import Path
import numpy as np
from audit import OUT,ROLES,rows,load,sha,put

def main():
    manifests=load(OUT/'INPUT_ARCHIVE_BINDINGS.json');members=0
    for archive in manifests:
        original=Path(archive['archive'])
        if not original.exists():continue
        assert sha(original)==archive['sha256']
        with zipfile.ZipFile(original) as z:
            for p in (OUT/'inputs'/archive['role']).rglob('*'):
                if p.is_file():assert p.read_bytes()==z.read(p.relative_to(OUT/'inputs'/archive['role']).as_posix());members+=1
    ur=rows(OUT/'UPDATE_TRAJECTORIES.csv');assert len(ur)==36
    assert max(float(r['score_replay_relative_error']) for r in ur)<1e-10
    assert max(float(r['posterior_replay_absolute_error']) for r in ur)<1e-10
    for r in ur:
        assert abs(np.log(float(r['wrong_to_true_score_ratio']))-float(r['visited_loggap'])-float(r['unvisited_loggap']))<1e-10
    # Audit EIG selection without true source coordinates or observed future gas.
    designs=load(OUT/'FROZEN_QUERY_DESIGNS.json');selected=load(OUT/'ORDINARY_EIG_SELECTED_BEFORE_READOUT.json')
    for r in selected:
        choices=[d for d in designs if d['update']==r['update'] and d['legal'] and d['action']!='recorded_future_route']
        assert max(choices,key=lambda d:d['model_single_station_IG_nats'])['action']==r['selection']
    ns=rows(OUT/'ALL_NATIVE_QUERY_READOUTS.csv');assert len(ns)==640
    assert {int(r['kernel_mode']) for r in ns}=={1}
    expected={r['query_id']:r for r in rows(OUT/'FIXED_QUERY_SCHEDULE.csv')}
    for case in ['E3','E4']:
        rr=[r for r in ns if r['case']==case];assert len(rr)==len(expected)==320
        for r in rr:
            q=expected[r['query_id']];assert r['x']==q['x'] and r['y']==q['y']
            assert 0<=float(r['staleness_s'])<=.61
    for r in load(OUT/'QUERIED_FRAME_IDENTITIES.json'):
        assert sha(OUT/r['packaged_path'])==r['sha256']
    before=load(OUT/'NATIVE_READOUT_RECEIPT.json');assert before['historical_regression_max_abs_error_ppm']==0
    assert before['new_gas_worlds']==before['ROS_runs']==before['physical_propagation_calls']==0
    # Every raw world/phase is retained; no rank-based source or action deletion.
    assert len(designs)==18 and sum(d['legal'] for d in designs)==16
    assert len(rows(OUT/'ACTION_WINDOW_SUMMARY.csv'))==32
    assert len(rows(OUT/'ACTUAL_E3_E4_OBSERVABILITY_DIAGNOSTIC.csv'))==16
    put(OUT/'INDEPENDENT_QA.json',dict(status='PASS_ARTIFACT_AND_ARITHMETIC_CHECKS_NOT_SCIENTIFIC_PROMOTION',archive_members_exact=members,source_updates=36,actual_consumed_windows=560,new_point_queries=640,queried_case_frames=101,source_label_free_action_selection=True,future_route_not_a_deployable_choice=True,raw_response_zero_regression=True,all_source_domains_preserved=True,main_localization_gain_claim=False,new_ROS=0,new_worlds=0))
    print('PASS_INDEPENDENT_QA',members,flush=True)
if __name__=='__main__':main()
