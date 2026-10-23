"""2D probability mass map. Never delete candidates after a challenge test."""
import numpy as np

def source_map(sources, probabilities):
    s=np.asarray(sources,float);p=np.asarray(probabilities,float)
    if s.ndim!=2 or s.shape[1]!=2 or p.shape!=(len(s),):raise ValueError('shape')
    if np.any(p<0) or not np.isfinite(p).all() or p.sum()<=0:raise ValueError('invalid probabilities')
    p=p/p.sum();xs=np.unique(s[:,0]);ys=np.unique(s[:,1]);grid=np.zeros((len(ys),len(xs)))
    support=np.zeros_like(grid,dtype=bool)
    for (x,y),v in zip(s,p):
        i=np.searchsorted(ys,y);j=np.searchsorted(xs,x);grid[i,j]+=v;support[i,j]=True
    return {'x':xs,'y':ys,'probability_mass':grid,'candidate_support':support,'sum':float(grid.sum()),'map_xy':s[np.argmax(p)],'posterior_mean_xy':p@s}

def posterior_metrics(sources,probabilities,truth,truth_index=None):
    """Evaluator-only. Top5 is highest ceil(0.05*N) cells' weighted centroid.

    Stable ties here; official C++ sorting/float behavior requires native endpoint.
    No minimum-distance-to-Top5 metric is substituted.
    """
    s=np.asarray(sources,float);p=np.asarray(probabilities,float);p=p/p.sum();truth=np.asarray(truth,float)
    if truth_index is None:truth_index=int(np.argmin(np.linalg.norm(s-truth,axis=1)))
    order=np.argsort(-p,kind='stable');n=max(1,int(np.ceil(.05*len(p))));best=order[:n]
    xy5=(p[best,None]*s[best]).sum(0)/p[best].sum()
    other=np.delete(p,truth_index);rank=1+int((p>p[truth_index]).sum())
    return {'true_top1':bool(np.argmax(p)==truth_index),'true_rank':rank,'map_error_m':float(np.linalg.norm(s[np.argmax(p)]-truth)),'top5_centroid_error_m':float(np.linalg.norm(xy5-truth)),'posterior_mean_error_m':float(np.linalg.norm(p@s-truth)),'true_log_margin':float(np.log(max(p[truth_index],1e-300))-np.log(max(other.max(),1e-300))),'true_probability':float(p[truth_index]),'brier':float(np.sum((p-np.eye(len(p))[truth_index])**2)),'source_support_distance_m':float(np.linalg.norm(s[truth_index]-truth)),'top5_scope':'point-panel stable tie reference; native C++ endpoint required for PMFS final acceptance'}
