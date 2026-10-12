"""Independent input gate, never an initialization or physical prediction."""
from pathlib import Path
import csv,json,math,hashlib,time

def validate(rows,cutoff):
    accepted=[]
    for r in rows:
        receipt=int(r['receipt_ns']);stamp=int(r['stamp_ns'])
        if stamp>receipt or receipt>cutoff:raise ValueError('FUTURE_OR_UNRECEIVED_INPUT')
        if r['frame']!='PioneerP3DX_anemometer_frame':raise ValueError('UNREGISTERED_FRAME')
        speed=float(r['speed_m_s'])
        if not math.isfinite(speed) or speed<0:raise ValueError('INVALID_SPEED')
        if r['physical_epoch_bound']!='True':continue
        if r['TF_at_initialization_cutoff']!='PASS_PAST_STAMP':continue
        t=float(r['physical_stamp_s']);phi=float(r['cutoff_TO_rad_map'])
        if not math.isfinite(t+phi):raise ValueError('NONFINITE_CLOCK_OR_DIRECTION')
        accepted.append((t,receipt,stamp))
    return accepted

def initial_state_gate(prior_registered,full_release_history):
    if not full_release_history and not prior_registered:
        raise ValueError('UNOBSERVED_HISTORY_REQUIRES_REGISTERED_MARGINAL_MODEL')
    return 'INPUT_CONTRACT_ONLY_NOT_PHYSICAL_PASS'

def main():
    started=time.monotonic()
    root=Path(__file__).resolve().parents[1]
    out=root/'outputs/PMFS_C1B_LOCAL_INITIAL_STATE_AUDIT_20261011'
    scope=json.loads((out/'C1B_INPUT_SCOPE_FREEZE.json').read_text())
    meta=json.loads((out/'C1B_ALLOWED_HISTORY_AND_CLOCK.json').read_text())
    cutoff=scope['cutoff_receipt_ROS_ns']
    with (out/'C1B_PAST_LOCAL_WIND.csv').open(newline='',encoding='utf8') as f:rows=list(csv.DictReader(f))
    q=validate(rows,cutoff);assert len(q)==184
    expected0=267.307098389
    assert abs(meta['frame500_physical_s']-expected0)<1e-9
    assert abs(meta['goal_invocation_physical_s']-(expected0+(cutoff-meta['ROS_player_anchor_ns'])/1e9))<1e-9
    assert min(x[0] for x in q)>267
    hashes={}
    for n,v in meta['input_sha256'].items():
        if n=='contract':p=root/v['path']
        else:p=root/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010'/n
        h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==v['sha256'];hashes[n]=h
    tests=[]
    cases=[('future_receipt',{'receipt_ns':str(cutoff+1)}),('future_stamp',{'stamp_ns':str(cutoff+10**9)}),('unknown_frame',{'frame':'source_label_frame'}),('negative_speed',{'speed_m_s':'-1'}),('NaN_speed',{'speed_m_s':'nan'})]
    for name,patch in cases:
        altered=[dict(rows[-1],**patch)]
        try:validate(altered,cutoff)
        except ValueError as e:tests.append({'name':name,'rejected':True,'reason':str(e)})
        else:raise AssertionError(name)
    for name,prior,history in [('zero_plume_at_search_is_not_evidence',False,False),('unregistered_retrospective_prior',False,False)]:
        try:initial_state_gate(prior,history)
        except ValueError as e:tests.append({'name':name,'rejected':True,'reason':str(e)})
        else:raise AssertionError(name)
    result={'qualification':'PASS_CAUSAL_INPUT_PROJECTION_ONLY','input_SHA_count':len(hashes),'accepted_wind_rows':len(q),'physical_first_s':min(x[0] for x in q),'physical_last_s':max(x[0] for x in q),'release_to_search_history_complete':False,'initial_state_qualification':'REQUIRES_NEW_3D_MARGINAL_MODEL_CONTRACT','fail_closed_tests':tests,'fresh_physical_calls':0,'goals':0,'active_wall_s':time.monotonic()-started}
    (out/'C1B_INDEPENDENT_INPUT_GATE.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result))

if __name__=='__main__':main()
