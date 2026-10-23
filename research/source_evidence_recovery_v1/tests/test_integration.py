import json
from pathlib import Path
import numpy as np
from gsl_recovery.pipeline import generate_controlled_dataset,train_from_manifest,run_closed_loop
from gsl_recovery.evaluation.native_pmfs import replay_native_b4

def test_train_and_committed_active_loop(tmp_path):
    generate_controlled_dataset(tmp_path/'data',seed=71,n_train=12,length=6)
    r=train_from_manifest(tmp_path/'data/manifest.json',tmp_path/'model','Bprime',seed=1,maxiter=80)
    assert r['final_objective']<r['initial_objective']
    s=run_closed_loop(tmp_path/'model/model.npz',tmp_path/'run',seed=72,rounds=1,draws=16,block_length=3)
    assert s['status']=='PASS_CONTROLLED_CLOSED_LOOP'
    assert s['observations']==3 and s['whole_blocks_committed']
    assert abs(s['posterior_mass']-1)<1e-12
    assert s['replay_max_error']<1e-8
    plan=json.loads((tmp_path/'run/round_000_plan.json').read_text())
    update=json.loads((tmp_path/'run/round_000_update.json').read_text())
    assert plan['history_ids']==[]
    assert [o['action'] for o in update['observations']]==plan['actions']

def test_actual_native_b4_fixture(tmp_path):
    root=Path(__file__).resolve().parents[1]/'examples/native_b4'
    receipt=replay_native_b4(root,tmp_path/'native')
    assert receipt['status']=='PASS'
    assert receipt['candidate_scores_replayed']==128
    assert receipt['measurement_blocks']==50
    assert receipt['max_posterior_abs_error']<1e-12
    assert abs(receipt['wrong_over_true_nearby_compatibility_score']-14874.598695195082)<1e-5

def test_persistent_native_adapter(tmp_path):
    from dataclasses import asdict
    from gsl_recovery.m1_generator import JointObservationGenerator
    from gsl_recovery.m1_teacher import ControlledPlumeBackend
    from gsl_recovery.pipeline import default_sources,default_mechanisms
    from gsl_recovery.navigation.session import ActiveSession
    from gsl_recovery.types import Action,observation_to_dict
    session=ActiveSession(JointObservationGenerator(),default_sources(),default_mechanisms(),draws=8)
    actions=[Action(1.,1.,time=float(i+1)) for i in range(3)]
    plan=session.request({'op':'plan','navigation_qualified':True,'action_blocks':[[asdict(a) for a in actions]]})
    obs=ControlledPlumeBackend().simulate_episode(default_sources()[0],actions,rng=np.random.default_rng(3))
    response=session.request({'op':'observe','observations':[observation_to_dict(o) for o in obs]})
    assert response['observations']==3 and abs(response['source_map']['sum']-1)<1e-12
    assert session.pending is None and session.round==1
