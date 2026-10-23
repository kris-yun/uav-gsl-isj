"""Cross-module tests that guard scientific errors, not implementation copies."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import pytest
from gsl_discrimination.channel import FiniteChannel,JointPosterior
from gsl_discrimination.data import SynchronousBlock,DataQualification,QualificationError
from gsl_discrimination.ledger import RawObservationLedger
from gsl_discrimination.m1_opponent import SamplingContract
from gsl_discrimination.m1_opponent.raw_joint import calibrate_raw_joint,load_observation_model
from gsl_discrimination.evaluation.block_pipeline import calibrate_manifest,replay_manifest,load_manifest
from gsl_discrimination.evaluation.maps import export_source_map
from gsl_discrimination.navigation.bridge import JsonLineBackend
from gsl_discrimination.m2_boundary.calibration import fit_response_geometry


def test_joint_future_uses_one_nuisance_per_rollout():
    # Source is not needed to create this perfectly correlated nuisance law.
    p=np.zeros((2,2,2,2));p[:,:,0,0]=1;p[:,:,1,1]=1
    c=FiniteChannel(p,[1,1],[[0,0],[1,0]],['a','b'],['s0','s1'])
    draws,states=c.sample_joint([0,1],0,np.random.default_rng(1),1000)
    assert np.array_equal(draws[:,0],draws[:,1])
    assert np.array_equal(draws[:,0],states)


def test_posterior_shared_nuisance_not_resampled_each_block():
    p=np.array([[[[.9,.1],[.1,.9]],[[.5,.5],[.5,.5]]]])
    c=FiniteChannel(p,[1],[[0,0],[1,0]],['a'],['s0','s1'])
    post=JointPosterior(c)
    post.update(0,0,'one');post.update(0,0,'two')
    expected=.41/(.41+.25)
    assert np.isclose(post.source[0],expected)
    with pytest.raises(ValueError):post.update(0,0,'two')


def test_raw_joint_roundtrip(tmp_path):
    rng=np.random.default_rng(2);raw=rng.lognormal(size=(2,2,1,12,4,2))
    contract=SamplingContract(True,bandwidth_calibrated=True,maximum_step_s=.11)
    times=np.arange(4)*.1
    model=calibrate_raw_joint(raw,times,contract,[[0,0],[1,0]],['a','b'],['s0','s1'],[1,2],n_symbols=6)
    model.save(tmp_path);loaded=load_observation_model(tmp_path)
    assert model.encode(0,raw[0,0,0,0])==loaded.encode(0,raw[0,0,0,0])
    np.testing.assert_array_equal(model.channel.probabilities,loaded.channel.probabilities)


def _manifest(tmp_path):
    review={'status':'QUALIFIED_FOR_DECLARED_USES','scope':'CONSTRUCTED_UNIT_TEST_NOT_NATIVE_GADEN'}
    review_path=tmp_path/'review.json';review_path.write_text(json.dumps(review))
    d={'schema':'gsl-native-block-manifest-1','source_ids':['s0','s1'],'source_xy':[[0,0],[1,0]],
       'nuisance_ids':['r0'],'temporal':False,'sampling_contract':{'continuous':False,'provenance':'UNIT_TEST_ONLY'},
       'actions':[{'name':'pair0','cost_s':1,'positions_m':[[2,0,1],[3,0,1]]}],
       'capability_review':{'path':'review.json','sha256':hashlib.sha256(review_path.read_bytes()).hexdigest()},'records':[]}
    q=DataQualification(synchronous_spatial=True,physical_clock=True,source_occupancy_validated=True,
                        sensor_response_calibrated=True,scope='CONSTRUCTED_UNIT_TEST_ONLY')
    for source in range(2):
        for k in range(4):
            split='train' if k<3 else 'dev'
            b=SynchronousBlock([[1+source*8+k*.1,1+source+k*.2]],[10.],[[2,0,1],[3,0,1]],('left','right'),q,
                               f'{source}-{k}',f'world-{source}-{k}')
            target=tmp_path/f'b{source}-{k}.npz';b.save_npz(target)
            d['records'].append({'path':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                                'source_id':f's{source}','nuisance_id':'r0','action':0,'split':split})
    p=tmp_path/'manifest.json';p.write_text(json.dumps(d));return p,d


def test_qualified_manifest_to_calibration_and_fixed_replay(tmp_path):
    path,d=_manifest(tmp_path)
    fitted=calibrate_manifest(path,tmp_path/'model')
    assert fitted['training_blocks']==6
    result=replay_manifest(path,tmp_path/'model',tmp_path/'replay')
    assert result['n_episodes']==2 and not result['active_flight']
    assert len(list((tmp_path/'replay').glob('episodes/*/source_probability_map.npz')))==2


def test_source_geometry_mismatch_refused(tmp_path):
    path,d=_manifest(tmp_path);d['actions'][0]['positions_m'][0][0]=99;path.write_text(json.dumps(d))
    with pytest.raises(QualificationError,match='geometry'):load_manifest(path)


def test_false_native_qualification_refused(tmp_path):
    path,d=_manifest(tmp_path);p=tmp_path/'review.json';p.write_text(json.dumps({'status':'HOLD'}))
    d['capability_review']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();path.write_text(json.dumps(d))
    with pytest.raises(QualificationError,match='qualification'):load_manifest(path)


def test_training_never_opens_sealed_final_files(tmp_path):
    path,d=_manifest(tmp_path)
    d['records'].append({'split':'final','path':'SEALED_FILE_MUST_NOT_BE_READ.npz','sha256':'never-open'})
    path.write_text(json.dumps(d))
    fitted=calibrate_manifest(path,tmp_path/'model')
    assert fitted['training_blocks']==6
    with pytest.raises(QualificationError,match='sealed'):load_manifest(path,allowed_splits=('final',))


def test_replay_rejects_changed_action_cost_contract(tmp_path):
    path,d=_manifest(tmp_path);calibrate_manifest(path,tmp_path/'model')
    d['actions'][0]['cost_s']=2;path.write_text(json.dumps(d))
    with pytest.raises(QualificationError,match='contract differs'):replay_manifest(path,tmp_path/'model',tmp_path/'changed')


def test_geometry_fit_is_train_only_and_keeps_source_gradient_axes(tmp_path):
    path,d=_manifest(tmp_path)
    original=list(d['records']);d['records']=[];d['actions']=[]
    for action,center in enumerate(((2.5,0),(4.5,0),(2.5,2))):
        positions=[[center[0]-.5,center[1],1],[center[0]+.5,center[1],1]]
        d['actions'].append({'name':f'pair{action}','cost_s':1,'positions_m':positions})
        for r in original:
            b=SynchronousBlock.load_npz(tmp_path/r['path']);b.positions_m=np.array(positions)
            b.values=b.values+center[0]*2+center[1]
            b.block_id=f'{action}-'+b.block_id;b.realization_id=f'{action}-'+b.realization_id
            target=tmp_path/f'a{action}-{r["path"]}';b.save_npz(target)
            d['records'].append({**r,'path':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'action':action})
    d['records'].append({'split':'final','path':'SEALED_MUST_NOT_OPEN.npz','sha256':'unread'})
    path.write_text(json.dumps(d));calibrate_manifest(path,tmp_path/'model')
    receipt=fit_response_geometry(path,tmp_path/'model',bandwidth_m=10)
    assert receipt['training_blocks']==18 and receipt['sources']==2
    with np.load(tmp_path/'model'/'formation_predictions.npz') as f:
        assert f['gradients'].shape==(3,2,2)
        assert np.all(f['gradients'][:,:,0]>0) and np.all(f['gradients'][:,:,1]>0)
        assert np.all(np.linalg.eigvalsh(f['joint_covariance'])>0)
    with pytest.raises(ValueError,match='already frozen'):fit_response_geometry(path,tmp_path/'model')


def test_geometry_manifest_freeze_precedes_observation_reads(tmp_path,monkeypatch):
    path,d=_manifest(tmp_path);calibrate_manifest(path,tmp_path/'model')
    d['records'][0]['path']='RELABELED_SEALED_DATA.npz';path.write_text(json.dumps(d))
    def forbidden(*args,**kwargs):raise AssertionError('observation loader must not be called')
    monkeypatch.setattr('gsl_discrimination.evaluation.block_pipeline.load_manifest',forbidden)
    with pytest.raises(ValueError,match='exactly the frozen'):fit_response_geometry(path,tmp_path/'model')


def test_ppb_block_not_silently_used_as_ppm(tmp_path):
    path,d=_manifest(tmp_path);calibrate_manifest(path,tmp_path/'model')
    r=next(r for r in d['records'] if r['split']=='dev');p=tmp_path/r['path']
    b=SynchronousBlock.load_npz(p);b.units='ppb';b.save_npz(p)
    r['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();path.write_text(json.dumps(d))
    with pytest.raises(QualificationError,match='units'):replay_manifest(path,tmp_path/'model',tmp_path/'changed')


def test_fixed_episode_cannot_mix_realizations(tmp_path):
    path,d=_manifest(tmp_path);calibrate_manifest(path,tmp_path/'model')
    r=next(r for r in d['records'] if r['split']=='dev');p=tmp_path/r['path'];b=SynchronousBlock.load_npz(p)
    b.block_id+='new';b.realization_id+='different';b.times_s=np.array([11.]);new=tmp_path/'new.npz';b.save_npz(new)
    r['episode_id']='same_episode';d['records'].append({**r,'path':new.name,'sha256':hashlib.sha256(new.read_bytes()).hexdigest()})
    path.write_text(json.dumps(d))
    with pytest.raises(QualificationError,match='realization changed'):replay_manifest(path,tmp_path/'model',tmp_path/'changed')


def test_2d_map_sums_same_xy_and_preserves_illegal_cells(tmp_path):
    mass,mask=export_source_map([[0,0],[0,0],[1,1]],[.2,.3,.5],tmp_path/'map.npz')
    assert mass[0,0]==.5 and mass[1,1]==.5 and mass.sum()==1
    assert not mask[0,1]


def test_process_bridge_roundtrip_without_shell(tmp_path):
    server=tmp_path/'server.py'
    server.write_text('import sys,json\nfor l in sys.stdin:\n q=json.loads(l);print(json.dumps({"id":q["id"],"result":{"received":q["method"]}}),flush=True)\n')
    bridge=JsonLineBackend([sys.executable,str(server)],tmp_path/'stderr.log')
    try:assert bridge.call('describe')['received']=='describe'
    finally:bridge.close()


def test_process_bridge_partial_line_has_a_real_deadline(tmp_path):
    server=tmp_path/'partial.py'
    server.write_text('import sys,time\nsys.stdin.readline()\nsys.stdout.write("{\\\"id\\\":1")\nsys.stdout.flush()\ntime.sleep(10)\n')
    bridge=JsonLineBackend([sys.executable,str(server)],tmp_path/'stderr.log',timeout_s=.2)
    try:
        with pytest.raises(TimeoutError,match='complete'):bridge.call('describe')
    finally:bridge.close()
