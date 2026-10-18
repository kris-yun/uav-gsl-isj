#!/usr/bin/env python3
"""B0 algebra-only precheck: do NOT call this a neural operator or localization gain."""
import json
import numpy as np


def rank_one_approximations(K:np.ndarray)->dict[str,np.ndarray]:
    K=np.asarray(K,dtype=float)
    u,s,vt=np.linalg.svd(K,full_matrices=False)
    raw=s[0]*np.outer(u[:,0],vt[0])
    center=K.mean(axis=1,keepdims=True)
    uc,sc,vc=np.linalg.svd(K-center,full_matrices=False)
    centered=center + sc[0]*np.outer(uc[:,0],vc[0])
    return {'raw_POD_rank1':raw,'centered_POD_rank1':centered}


def pilot_report()->dict:
    K=np.array([[100.,100.],[2.,0.]]) # columns: unit-release source response
    approximations=rank_one_approximations(K)
    true_diff=np.linalg.norm(K[:,0]-K[:,1]); energy=np.linalg.norm(K,'fro')**2
    d={}
    for name,A in approximations.items():
        d[name]={
          'Frobenius_energy_retained_fraction':float(1-np.linalg.norm(K-A,'fro')**2/energy),
          'contrast_retained_fraction':float(np.linalg.norm(A[:,0]-A[:,1])/true_diff),
          'contrast_vector_error':float(np.linalg.norm((A[:,0]-A[:,1])-(K[:,0]-K[:,1]))/true_diff),
        }
    return {'status':'TOY_ONLY_NO_B_SUCCESS','matrix_K':K.tolist(),
      'source_pair_true_response_distance':true_diff,'ordinary_comparators':d,
      'key_finding':'Ordinary centered rank-1 POD retains the entire source contrast on this two-source toy; uncentered SVD alone is a weak strawman.',
      'NEMO_trained':False,'new_physical_forward_calls':0,'gas_localization_gain':'NOT_ESTABLISHED'}

if __name__=='__main__':
    print(json.dumps(pilot_report(),indent=2,ensure_ascii=False))
