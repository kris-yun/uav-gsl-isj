import numpy as np
import pytest
from gsl_recovery.types import Action,Mechanism,Observation
from gsl_recovery.navigation import RectWorld,action_blocks,route_cost
from gsl_recovery.posterior import source_map,posterior_metrics
from gsl_recovery.data.qualification import qualify_episode,check_split_disjointness,audit_manifest
from gsl_recovery.pipeline import inference_version,default_sources,default_mechanisms,generate_controlled_dataset
from gsl_recovery.m1_generator import JointObservationGenerator
from gsl_recovery.evaluation.native_pmfs import compatibility_scores

def test_navigation_blocks_and_obstacles():
    world=RectWorld(obstacles=((-.3,.3,-.3,.3),))
    assert not world.legal_segment((-2.,0.),(2.,0.))
    assert world.legal_segment((-2.,1.),(2.,1.))
    blocks=action_blocks((-1.,1.),0.,world,length=3)
    assert blocks and all(np.all(np.diff([0]+[a.time for a in b])>0) for b in blocks)
    assert all(route_cost(b,(-1.,1.))>0 for b in blocks)

def test_probability_map_and_top5_definition():
    sources=np.column_stack((np.arange(20),np.zeros(20)));p=np.arange(1.,21.)
    grid=source_map(sources,p)
    assert abs(grid['sum']-1)<1e-12
    # 5% of 20 is one cell: weighted Top5 centroid equals MAP, not min-distance over arbitrary support.
    metrics=posterior_metrics(sources,p,[0,0])
    assert metrics['top5_centroid_error_m']==19
    assert metrics['map_error_m']==19

def test_freeze_and_split_leak(tmp_path):
    generate_controlled_dataset(tmp_path,seed=13,n_train=3,length=2)
    assert audit_manifest(tmp_path/'manifest.json',True)['status']=='PASS'
    from gsl_recovery.io import read_json,write_json
    path=tmp_path/'train/episode_0000.json';r=read_json(path)
    r['observations'][1]['uid']=r['observations'][0]['uid']
    assert 'duplicate_observation_id' in qualify_episode(r,True)['errors']
    write_json(path,r)
    assert audit_manifest(tmp_path/'manifest.json',True)['status']=='FAIL'
    m={'scene':'X','source_group':'s','wind_group':'w','realization_id':'r','split':'train'}
    assert check_split_disjointness([{'metadata':m},{'metadata':{**m,'split':'frozen_test'}}])['status']=='FAIL'

def test_model_version_includes_mechanism_and_support():
    model=JointObservationGenerator();sources=default_sources();m=default_mechanisms()
    v=inference_version(model,m,sources)
    assert inference_version(model,m+[Mechanism('detection_loss',0,None,.2)],sources)!=v
    assert inference_version(model,m,sources+1)!=v

def test_source_mechanism_cross_product(tmp_path):
    from gsl_recovery.io import read_json
    generate_controlled_dataset(tmp_path,seed=3,n_train=9,length=2)
    pairs=[]
    for p in (tmp_path/'train').glob('*.json'):
        r=read_json(p);pairs.append((tuple(r['source']),r['mechanism']['kind'],r['mechanism']['magnitude']))
    assert len(set(pairs))==9
    from gsl_recovery.m1_teacher import ControlledPlumeBackend,make_training_episodes
    eps=make_training_episodes(ControlledPlumeBackend(),default_sources()[:3],[Action(0.,0.,time=1.)],n_episodes=9,mechanisms=default_mechanisms())
    assert len({(tuple(e['source']),e['mechanism'].kind,e['mechanism'].magnitude) for e in eps})==9

def test_native_score_uses_cells_once_not_old_posterior():
    p=np.array([.8,.3]);c=np.array([.9,.7]);h=np.array([[.4,.5],[.8,.3]])
    scores=compatibility_scores(p,c,h,[True,True])
    assert np.isclose(scores[0],(1-.9*.4*.4)*(1-.7*.4*.2))
    assert scores[1]==1
