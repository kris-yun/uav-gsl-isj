"""Full 3-D Green-kernel algebra certificate; no native performance claim."""
from pathlib import Path
import json
import numpy as np
from m1_decoders import encode, decode


def main():
    delta1=np.array([[-4.,-2.],[5.,-1.],[-1.,3.]])
    wind=np.array([[1.3,.2],[.8,-.1],[1.1,.4]])
    R=decode(encode(delta1,wind,[.4,.35,.25]))['relative']
    kappa=.8; a1=100.; a2=102.; T_R=1.5; alpha=1.
    Q1=np.eye(2)/(2*kappa*a1); Q2=np.eye(2)/(2*kappa*a2)
    delta2=delta1+T_R*alpha*R
    D=delta2-delta1
    p1=np.column_stack([delta1+[40.,20.],np.full(3,5.)])
    p2=np.column_stack([delta2+[42.,19.],np.full(3,7.)])
    U=np.array([.7,.2,.1]); s=np.array([2.,-3.]); q=150.
    fixed_log_gain=np.log([1.1,.8,1.2]); H=np.eye(3)-np.ones((3,3))/3

    def corrected_log(p,age,Q,source_height):
        # The source height is used only by the forward generator. The known
        # horizontal correction does not use height, source xy, q, or gains.
        source3=np.r_[s,source_height]
        r3=p-U*age
        log_y=(np.log(q)-1.5*np.log(4*np.pi*kappa*age)
               -np.sum((r3-source3)**2,axis=1)/(4*kappa*age)
               +fixed_log_gain)
        horizontal_correction=.5*np.sum(r3[:,:2]*(r3[:,:2]@Q),axis=1)
        return log_y+horizontal_correction

    def contrast(height):
        return H@(corrected_log(p2,a2,Q2,height)-corrected_log(p1,a1,Q1,height))

    E=delta2@Q2-delta1@Q1
    z=contrast(11.)  # Fixed but unknown source height; no height correction.
    identity_error=float(np.linalg.norm(z-E@s))
    decomposition_error=float(np.linalg.norm(E-(D@Q2+delta1@(Q2-Q1))))
    main_sigma=float(np.linalg.svd(D@Q2,compute_uv=False)[-1])
    drift_norm=float(np.linalg.norm(delta1@(Q2-Q1),2))
    lower=main_sigma-drift_norm
    actual_sigma=float(np.linalg.svd(E,compute_uv=False)[-1])
    height_error=float(max(np.linalg.norm(contrast(h)-z) for h in [-5.,27.]))
    wrong_E=(a2-a1)*alpha*R@Q2+delta1@(Q2-Q1)
    wrong_time_error=float(np.linalg.norm(z-wrong_E@s))
    assert identity_error<1e-12 and decomposition_error<1e-14
    assert lower>0 and actual_sigma>=lower-1e-14 and np.linalg.matrix_rank(E)==2
    assert height_error<1e-12 and 0<T_R<a2-a1 and wrong_time_error>1e-5
    report={
        'scope':'FULL_3D_GREEN_ALGEBRA_ONLY; no native localization or superiority claim',
        'kernel_dimension':3,'log_normalizer_exponent':-1.5,
        'altitudes_by_epoch':[5.,7.],'same_height_within_each_epoch':True,
        'source_height_fixed_unknown_to_contrast':11.,
        'gains_fixed_across_epochs':[1.1,.8,1.2],
        'ages_s':[a1,a2],'movement_duration_T_R_s':T_R,
        'waiting_duration_s':a2-a1-T_R,'actual_D_equals_T_R_alpha_R':True,
        'corrected_log_identity_error':identity_error,
        'E_decomposition_error':decomposition_error,
        'sigma_min_DQ2':main_sigma,'age_drift_spectral_norm':drift_norm,
        'weyl_lower_bound':lower,'actual_min_singular_E':actual_sigma,
        'E_rank':int(np.linalg.matrix_rank(E)),
        'unknown_fixed_height_invariance_error':height_error,
        'incorrect_age_interval_as_motion_duration_error':wrong_time_error,
        'E':E.tolist(),'z':z.tolist()}
    Path(__file__).with_name('green_3d_certificate_results.json').write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
