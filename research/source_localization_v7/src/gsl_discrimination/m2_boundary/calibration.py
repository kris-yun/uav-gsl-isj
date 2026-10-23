"""Ordinary TRAIN-only RBF response fit for M2's required geometry input.

This is structural adaptation A', not an innovation claim. Measured paired
common mode approximates the response at the center only where the spatial
linearization check is valid. The caller still needs independent validation.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from ..m1_opponent.operator import time_weights


def fit_response_geometry(manifest_path,model_directory,bandwidth_m=None,ridge=1e-3):
    from ..evaluation.block_pipeline import load_manifest
    from ..m1_opponent.raw_joint import load_observation_model
    model=load_observation_model(model_directory);out=Path(model_directory)
    # Freeze guard precedes opening any observation block. Relabelled DEV/final
    # records must not become readable merely because a caller says TRAIN.
    if hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest()!=model.channel.metadata.get('calibration_manifest_sha256'):
        raise ValueError('geometry fit must use exactly the frozen M1 training manifest')
    d,records=load_manifest(manifest_path,allowed_splits=('train',))
    frozen=model.channel.metadata.get('native_manifest_contract')
    if frozen!={k:d[k] for k in ('source_ids','source_xy','nuisance_ids','actions','temporal','sampling_contract')}:
        raise ValueError('geometry fit must use the M1 calibration contract')
    if (out/'formation_predictions.npz').exists():raise ValueError('geometry already frozen')
    points=np.asarray([x['positions_m'] for x in d['actions']],dtype=float)
    if points.shape!=(len(d['actions']),2,3):raise ValueError('current geometry fitter requires stationary paired actions')
    if not np.allclose(points[...,2],points[0,0,2],rtol=0,atol=1e-8):
        raise ValueError('all paired sensing endpoints must share one qualified altitude; source height is separate')
    centers=[];center_index=[]
    for p in points:
        q=p[:,:2].mean(0)
        matches=[i for i,c in enumerate(centers) if np.allclose(c,q,rtol=0,atol=1e-8)]
        if not matches:centers.append(q);matches=[len(centers)-1]
        center_index.append(matches[0])
    q=np.asarray(centers);n=len(q);s=len(d['source_ids'])
    if n<3 or np.linalg.matrix_rank(q-q.mean(0))<2:
        raise ValueError('two-dimensional response gradient fit requires non-collinear training centers')
    distances=np.linalg.norm(q[:,None]-q[None,:],axis=-1)
    bandwidth=float(np.median(distances[distances>0])) if bandwidth_m is None else float(bandwidth_m)
    if not np.isfinite([bandwidth,ridge]).all() or bandwidth<=0 or ridge<=0:
        raise ValueError('positive finite RBF bandwidth and ridge required')
    samples=[[[] for _ in range(s)] for _ in range(n)]
    for record,block in records:
        channel_average=time_weights(block.times_s)@block.values
        eo=np.array([channel_average.mean(),(channel_average[0]-channel_average[1])/2])
        samples[center_index[int(record['action'])]][d['source_ids'].index(record['source_id'])].append(eo)
    mean=np.empty((n,s));covariance=np.empty((n,s,2,2))
    for i in range(n):
        for j in range(s):
            x=np.asarray(samples[i][j])
            if len(x)<3:raise ValueError('three training blocks per source/center required for covariance')
            mean[i,j]=x[:,0].mean();c=np.cov(x,rowvar=False)
            covariance[i,j]=c+np.eye(2)*max(float(np.trace(c))*1e-6,1e-12)
    kernel=np.exp(-distances**2/(2*bandwidth**2));beta=np.linalg.solve(kernel+ridge*np.eye(n),mean)
    fitted=kernel@beta
    gradient=np.einsum('ij,ijs,jk->iks',kernel,(q[None,:,:]-q[:,None,:])/bandwidth**2,beta)
    # Gradient axes [center,source,xy]. This operation does not use dev/final.
    np.savez_compressed(out/'formation_predictions.npz',centers=q,means=fitted,gradients=gradient,
                        joint_covariance=covariance,action_to_center=np.array(center_index))
    receipt={'status':'TRAIN_GEOMETRY_FIT_NOT_PHYSICAL_CERTIFICATION','source':'native reviewed paired training blocks',
      'bandwidth_m':bandwidth,'ridge':ridge,'centers':n,'sources':s,'training_blocks':len(records),
      'sensing_z_m':float(points[0,0,2]),
      'manifest_sha256':hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest(),
      'readout':'raw finite-window common/odd concentration, trapezoid time average',
      'constraints':['validate paired-common-mode approximation and gradient on independent calibration worlds',
                     'covariance pools declared action geometry and nuisance; it is a proposal metric, never a likelihood',
                     'requires Cartesian center/separation/orientation catalogue for current bridge']}
    (out/'GEOMETRY_CALIBRATION_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    return receipt
