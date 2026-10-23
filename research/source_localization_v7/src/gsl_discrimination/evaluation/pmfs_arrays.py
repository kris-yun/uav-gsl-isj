"""Replay extracted PMFS maps with the pinned compatibility operator.

Input maps must come from the official run/exporter. This executable port
does not reproduce navigation, forward propagation or ROS callback timing.
"""
from pathlib import Path
import json
import numpy as np
from ..baselines import pmfs_map_compatibility,pmfs_variance_interest
from .maps import export_source_map
from .metrics import source_metrics


def replay_pmfs_maps(path,output,difference_factor=1.,truth=None):
    with np.load(path,allow_pickle=False) as z:
        measured=z['measured_hit'];confidence=z['confidence'];predicted=z['predicted_hit'];xy=z['source_xy']
        mask=z['free_mask'] if 'free_mask' in z else None
    if measured.ndim!=2 or predicted.ndim!=3 or confidence.shape!=measured.shape or predicted.shape[0]!=len(measured):
        raise ValueError('need measured_hit[T,C], confidence[T,C], predicted_hit[T,S,C]')
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    if (out/'PMFS_OPERATOR_REPLAY.json').exists():raise ValueError('receipt exists')
    rows=[]
    for index,(m,c,h) in enumerate(zip(measured,confidence,predicted)):
        probability,logscore=pmfs_map_compatibility(m,c,h,difference_factor,mask)
        interest=pmfs_variance_interest(h,probability,c)
        row={'frame_index':index,'source_probability':probability.tolist(),'compatibility_log_score':logscore.tolist(),
             'variance_interest':interest.tolist(),'physical_likelihood_ratio_claim':False}
        if truth is not None:row.update(source_metrics(probability,truth,xy))
        rows.append(row)
    export_source_map(xy,probability,out/'source_probability_map.npz')
    result={'status':'PMFS_OPERATOR_REPLAY_ONLY','official_pin':'4e141e162551e674f2f30ddb8859136c72139aac',
            'full_native_pmfs_ros':False,'previous_posterior_multiplied':False,'rows':rows}
    (out/'PMFS_OPERATOR_REPLAY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    return result
