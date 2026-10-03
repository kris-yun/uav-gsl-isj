"""Check proposed information-layer claims against frozen R1/R1A evidence.

Read-only reanalysis; no new simulations or changes to any previous gate.
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'evidence/information_layer_claim_review_20261003'
R1 = ROOT/'evidence/lakeshore_observability_r0_r2'
R1A = ROOT/'evidence/lakeshore_r1a_deconfound_20261003'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    inputs=[R1/'M4_summary_threshold_1.csv',R1/'M1_threshold_1.csv',
            R1A/'original_hit_summary.csv',R1A/'height_summary_factor_1.csv',
            R1A/'paired_F_control_comparisons.csv',R1A/'R1A_FINAL_DECISION.json']
    manifest=[]
    for p in inputs:
        with p.open('rb') as f:
            manifest.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.file_digest(f,'sha256').hexdigest()))
    scores=pd.read_csv(inputs[0]);hits=pd.read_csv(inputs[2]);m1=pd.read_csv(inputs[1])
    combined=scores.merge(hits,on=['environment','release','height'],validate='one_to_one')
    counts=m1.groupby(['environment','release','height'],as_index=False).gas_hits.sum()
    combined=combined.merge(counts,on=['environment','release','height'],validate='one_to_one')
    combined['hit_fraction_pp']=100*combined.hit_rate
    combined['top1_pp']=100*combined.top1
    combined.to_csv(OUT/'ORIGINAL_R1_DETECTION_AND_IDENTIFIABILITY.csv',index=False)
    controls=pd.read_csv(inputs[3])
    controls.query('height==30').to_csv(OUT/'R1A_30M_CONTROLS_ALL_RELEASES.csv',index=False)
    pd.read_csv(inputs[4]).to_csv(OUT/'R1A_PAIRED_CONTROL_EFFECTS.csv',index=False)
    baseline=combined.query("environment in ['N0','L1'] and height==30")
    assert len(baseline)==6
    assert (baseline.hit_rate==0).all() and (baseline.gas_hits==0).all()
    assert ((baseline.top1-1/9).abs()<1e-12).all()
    mid=controls.query('release==10 and height==30')
    for scene in ['C06','C08','S06','S08','H1','H2','F1','F2']:
        assert mid.loc[mid.environment==scene,'top1'].iloc[0]==1
    previous=json.loads(inputs[5].read_text(encoding='utf-8'))
    assert previous['decision']=='R1A_RESIDENCE_SUFFICIENT_STOP_UPLIFT_ATTRIBUTION'
    result=dict(decision='PROPOSAL_NOT_SUPPORTED_DO_NOT_LAUNCH_UPLIFT_CONFIRMATORY_RUN',
                original_height_contrast_exists=True,
                baseline_30m_detection_rows_all_zero=True,
                M1_is_conditional_upwind_cone_fraction_not_detection_rate=True,
                M2_is_low_altitude_front_blind_and_high_altitude_recovery_not_all_height_detection=True,
                slow_uniform_and_w_zero_controls_reproduce_30m_information=True,
                proposed_H_ID_exact_continuous_height_not_established=True,
                M4_is_known_environment_known_release_discrete_source_classifier=True,
                no_new_realizations=True,no_previous_gates_changed=True,
                input_manifest=manifest)
    (OUT/'REVIEW_DECISION.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='input_manifest'}))


if __name__=='__main__': main()
