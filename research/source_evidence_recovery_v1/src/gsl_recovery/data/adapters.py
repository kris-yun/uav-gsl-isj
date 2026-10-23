"""Explicit readout/coordinate adapters; no hidden rescaling or truth-selected route."""
from pathlib import Path
import csv, numpy as np
from ..types import Action,Observation,observation_to_dict
from ..io import read_json,write_json,sha256
from .qualification import qualify_episode

def csv_to_episode(csv_path,metadata_path,candidates_path,out_path,threshold):
    meta=read_json(metadata_path); cand=np.asarray(read_json(candidates_path),float)
    required={'time','x','y','z','gas','wind_x','wind_y'}
    obs=[]
    with open(csv_path,newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not required.issubset(reader.fieldnames or []): raise ValueError('CSV columns required: '+','.join(sorted(required)))
        for i,row in enumerate(reader):
            obs.append(Observation(row.get('uid') or f'csv-{i}',Action(float(row['x']),float(row['y']),float(row['z']),float(row['time']),float(row.get('dwell') or 1)),(float(row['wind_x']),float(row['wind_y'])),float(float(row['gas'])>=threshold)))
    meta.update(readout='binary_hit',threshold=float(threshold),input_sha256=sha256(csv_path))
    r={'schema_version':1,'metadata':meta,'candidates':cand.tolist(),'observations':[observation_to_dict(o) for o in obs]}
    receipt=qualify_episode(r);write_json(out_path,r);return receipt

def inspect_legacy_packet(root,out_dir):
    """Read existing packet, verify provenance; export one unlabelled replay only.

    No truth-owner or evaluation_only file is opened; never returns training data.
    Threshold must be supplied by user manifest for scientific use. For connection
    check gas>0 is explicitly named `positive_readout_connection_only`.
    """
    root=Path(root);out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    scope='UNSEEN_SOURCE';base=root/'inputs'/scope
    paths=[base/'DEV_OBS.npz',base/'GEOMETRY_MOBILE_ONLY.npz',base/'PREDICTIONS.npz']
    if not all(p.is_file() for p in paths):raise FileNotFoundError('legacy packet lacks raw observations/geometry/predictions')
    with np.load(paths[0],allow_pickle=False) as a: gas=a['gas'].copy();wind=a['wind'].copy()
    with np.load(paths[1],allow_pickle=False) as a: xyz=a['xyz'].copy();clock=a['clock'].copy()
    if gas.ndim!=2 or wind.shape!=gas.shape+(3,) or xyz.shape!=(gas.shape[1],3) or clock.shape!=(gas.shape[1],):raise ValueError('legacy shape inconsistency')
    if not all(np.isfinite(a).all() for a in [gas,wind,xyz,clock]) or not np.all(np.diff(clock)>0):raise ValueError('legacy numeric/time failure')
    with np.load(paths[2],allow_pickle=False) as a:
        logs=a['new_observation_log_density'].copy();posterior=a['posterior'].copy();methods=a['methods'].copy()
    if not np.isfinite(logs).all() or not np.isfinite(posterior).all():raise ValueError('nonfinite legacy scores')
    # Historical normalized conditional density replay, no new model training.
    from scipy.special import softmax
    reconstructed=softmax(np.cumsum(logs,axis=2),axis=-1)
    mismatch=float(np.max(np.abs(reconstructed-posterior)))
    obs=[Observation(f'legacy-{i}',Action(*map(float,xyz[i]),float(clock[i]),2.),tuple(map(float,wind[0,i,:2])),float(gas[0,i]>0)) for i in range(len(clock))]
    # No candidate coordinates are invented. Export raw observations separate from candidate-dependent inference.
    write_json(out/'legacy_history.json',{'metadata':{'scope':'legacy_evaluation_interface_only','readout':'positive_readout_connection_only','threshold':0.,'trained':False,'house_qualification':False},'observations':[observation_to_dict(o) for o in obs]})
    receipt={'status':'PASS_INPUT_AND_LEGACY_DENSITY_REPLAY','scientific_performance_status':'NOT_EVALUATED','house_runtime':'BLOCKED_NOT_PRESENT','training_eligible':False,'truth_owner_opened':False,'future_response_library_used':False,'raw_episodes':len(gas),'observations_per_episode':gas.shape[1],'finite_values':True,'monotone_time':True,'legacy_methods':methods.tolist(),'posterior_reconstruction_max_abs':mismatch,'posterior_reconstruction_pass':mismatch<1e-8,'assets':[{'path':str(p),'sha256':sha256(p)} for p in paths],'limitations':['Legacy source-panel data, not a new House benchmark','Threshold >0 is only adapter connectivity, not frozen physical sensor calibration','No teacher training from DEV/CAL/evaluation-only'],'history_path':str(out/'legacy_history.json')}
    write_json(out/'qualification_receipt.json',receipt);return receipt
