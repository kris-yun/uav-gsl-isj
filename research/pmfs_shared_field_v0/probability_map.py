"""Export the frozen learned decision map; never multiplies probe posteriors."""
import json
from pathlib import Path
import numpy as np

def source_probability_map(evidence_dir,fold,protocol,two_ppm,model='SHARED_FIELD'):
    e=Path(evidence_dir)
    models=json.loads((e/'FOLD_MODELS.json').read_text())
    if not 0<=fold<4 or not 0<=protocol<60:raise ValueError('invalid frozen fold/protocol')
    values=np.asarray(two_ppm,dtype=float)
    if values.shape!=(2,) or not np.isfinite(values).all() or (values<0).any():raise ValueError('two finite nonnegative ppm values required')
    abc=models[fold]['alphabet'];B=abc['bins']
    bins=np.where(values==0,0,1+np.searchsorted(abc['positive_thresholds'],values,side='left')) if B>1 else np.zeros(2,dtype=int)
    symbol=int(bins[0]*B+bins[1])
    with np.load(e/'PROBABILITY_MAP_TABLES.npz') as tables:prob=tables[f'fold_{fold}_{model}'][:,protocol,symbol].copy()
    return prob  # Same ordered168 candidate support; decision distribution, not guaranteed calibrated truth posterior.
