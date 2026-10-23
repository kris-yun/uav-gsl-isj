from __future__ import annotations
import numpy as np


def source_metrics(probability,truth,source_xy):
    p=np.asarray(probability,dtype=float); xy=np.asarray(source_xy,dtype=float)
    if p.ndim!=1 or xy.shape!=(len(p),2) or not np.isclose(p.sum(),1) or np.any(p<0):
        raise ValueError("normalized source probabilities and source coordinates required")
    order=np.argsort(-p,kind='stable'); best=int(order[0]); k=max(1,int(np.ceil(.05*len(p))))
    alternatives=np.delete(p,int(truth)); strongest=float(np.max(alternatives))
    return {"true_source":int(truth),"top1":int(best==truth),
            "map_error_m":float(np.linalg.norm(xy[best]-xy[truth])),
            "top5pct_error_m":float(np.min(np.linalg.norm(xy[order[:k]]-xy[truth],axis=1))),
            "true_rank":int(np.where(order==truth)[0][0]+1),
            "log_margin":float(np.log(max(p[truth],1e-300))-np.log(max(strongest,1e-300))),
            "brier":float(np.sum((p-np.eye(len(p))[truth])**2)),
            "true_probability":float(p[truth]),"max_probability":float(np.max(p)),
            "wrong_high_confidence":bool(best!=truth and p[best]>.9),
            "top1_tie":bool(np.sum(np.isclose(p,p[best],atol=1e-12,rtol=0))>1)}

