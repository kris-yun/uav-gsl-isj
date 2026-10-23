"""Explain the frozen pair's apparent gain without changing its results."""
import json
import numpy as np
from protocol import *
from analysis import load,classify,cross
from analyze_train import make_features,score

def main():
 s=json.loads((OUT/'SELECTION_FREEZE.json').read_text())['selected'];rows=[]
 v,t,r=load('train');idx=np.array(s['window_indices']);pair=np.array([[s['probe_L']-1,s['probe_R']-1]])
 # Single-side decimated feature is literally the nonzero component of the
 # already-frozen equal-budget pair. This is an algebraic attribution, not
 # a new pair, head, parameter search or additional DEV observation.
 f=make_features(v[:,:,idx],t[idx],pair,True)['pair_means_equal_scalar_budget']
 assert np.max(abs(f[...,1]))==0
 dp,dm=cross(f,False);sp,sm=cross(f[...,:1],False);assert np.array_equal(dp,sp)
 train_correct=int(np.sum(sp[:,0]==np.repeat(np.arange(3),2)))
 v,t,r=load('dev');pair=np.array([[r['probe_ranks'].index(s['probe_L']),r['probe_ranks'].index(s['probe_R'])]])
 with np.load(OUT/'FROZEN_ORDINARY_MODELS.npz') as q:
  for known,prefix in ((True,'known'),(False,'unknown_gain')):
   feats=make_features(v,t,pair,known);mu=q[prefix+'__pair_means_equal_scalar_budget']
   # Full sequence at every second native record for the unknown-gain arm.
   if not known:mu=q[prefix+'__pair_ordered_equal_scalar_budget']
   name='pair_means_equal_scalar_budget' if known else 'pair_ordered_equal_scalar_budget'
   for source in range(3):
    for rep in range(2):
     y=feats[name][source,rep,0]
     if known:single=y[:1];single_mu=mu[:,:1]
     else:single=y.reshape(-1,2)[:,0];single_mu=mu.reshape(3,-1,2)[:,:,0]
     d=np.array([score(y,m,not known) for m in mu]);sd=np.array([score(single,m,not known) for m in single_mu])
     assert int(classify(d))==int(classify(sd))
     rows.append({'scope':prefix,'world':r['worlds'][2*source+rep]['run_id'],'pair_prediction':int(classify(d)),
      'same_sample_single_prediction':int(classify(sd)),'strict_correct':int(classify(d))==source})
 write('ZERO_RIGHT_AND_SAMPLING_ATTRIBUTION.json',{'status':'EXACT_NO_NEW_SPATIAL_INFORMATION_IN_FROZEN_PAIR',
 'TRAIN_equal_budget_pair_correct':train_correct,'TRAIN_same_decimated_single_correct':train_correct,
 'TRAIN_full_sample_single_correct':s['global_single']['strict_correct'],
 'explanation':'right response is zero in all six TRAIN and six DEV windows; apparent TRAIN 6-versus-5 comes from time quadrature/subsampling of the left channel, not information from the second point',
 'mirror_equation_when_right_zero':'h_k=max(<log(1+L), w-kappa*w_delay>,0); mirror branch is nonpositive. The static gradient equals common intensity.',
 'all_DEV_equal_budget_predictions_match_same_sample_single':True,'checks':rows,
 'post_primary_attribution_only':True,'original_primary_results_not_overwritten':True,
 'not_a_proof_mirror_is_useless_at_other_nonzero_receivers':True})
 print('EXACT_ZERO_RIGHT_ATTRIBUTION_PASS',train_correct,'same-sampled single and pair identical')
if __name__=='__main__':main()
