#!/usr/bin/env python3
"""Independent checks of new M1 kernels and cross-window nuisance reasoning."""
from pathlib import Path
import sys,json,numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'m1'))
from m1_decoders import encode,decode,odor_memory,decode_merged

def info(Js,Jeta,sigma=1.):
    Js=np.atleast_2d(Js)/sigma;Jeta=np.atleast_2d(Jeta)/sigma
    return Js.T@(np.eye(len(Js))-Jeta@np.linalg.pinv(Jeta))@Js

def main():
    # P0 history repair: preserve one shared q across windows before projection.
    a=float(info([[1]],[[1]])[0,0]);b=float(info([[1]],[[-1]])[0,0])
    joint=float(info([[1],[1]],[[1],[-1]])[0,0]);assert a==b==0 and abs(joint-2)<1e-12
    # V43 degenerate case becomes a real source-free relative movement.
    p=np.array([[-5.,0],[5.,0]])
    e=encode(p,np.tile([1.,0],(2,1)),[.5,.5]);d=decode(e)
    assert np.linalg.norm(d['relative'])>0 and np.allclose(d['relative'].sum(0),0)
    # Extremely flat but non-collinear arrays illustrate exact rank vs margin.
    narrow=np.array([[-5.,0],[0,1e-5],[5.,0]])
    en=encode(narrow,np.tile([1.,.4],(3,1)),np.ones(3)/3);dn=decode(en)
    eigen=np.linalg.eigvalsh(dn['support_matrix'])
    assert eigen[-1]>1e-2 and eigen[0]<1e-9
    # Three-dimensional rank does not imply horizontal rank.
    pv=np.array([[-4.,0,-2.],[5.,0,-1.],[-1.,0,3.]])
    rank3=int(np.linalg.matrix_rank(pv));rankxy=int(np.linalg.matrix_rank(pv[:,:2]))
    assert rank3==2 and rankxy==1
    try:encode(pv,np.tile([1.,0,.3],(3,1)),np.ones(3)/3)
    except ValueError:reject_3d=True
    else:reject_3d=False
    assert reject_3d
    # Full recorded tensor -> downstream frozen moments is not injective:
    # identify the engineering sufficiency being claimed, not universal lossless control.
    report={'scope':'R2 independent mathematical and implementation checks; no plume performance.',
        'shared_q_information':{'separate':a+b,'joint':joint},
        'symmetric_pair_new_M1':{'translation':d['translation'].tolist(),'relative':d['relative'].tolist(),
                                'relative_norm':float(np.linalg.norm(d['relative']))},
        'nearly_collinear_support_eigenvalues':eigen.tolist(),
        'vertical_array':{'rank_3d':rank3,'horizontal_rank':rankxy,'new_kernel_correctly_rejects_3D_input':reject_3d},
        'requires_claim_boundary':['frozen-weight ascent is not closed-loop Lyapunov or source information',
            'rank must be combined with numerical sensitivity margin','qualification and safe execution are separate from the kernel',
            'horizontal and 3D ranks must be distinguished']}
    (HERE/'independent_m1_review_results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
