"""Meaningful falsification tests of proposed mathematical statements."""
import json
from pathlib import Path
import numpy as np
from m1_decoders import odor_memory,encode,decode,decode_merged,phi_frozen,uniform_speed_scale,propose


def main():
    rng=np.random.default_rng(20261028)
    p=np.array([[-4.,-2.],[5.,-1.],[-1.,3.]])
    w=np.array([[1.3,.2],[.8,-.1],[1.1,.4]])
    yh=np.array([[.4,.2,.1],[.3,.2,.5],[.6,.4,.2]])
    chi=odor_memory(yh)
    e=encode(p,w,chi); a=decode(e)
    results={}
    results['centroid_zero_error']=float(np.linalg.norm(a['relative'].sum(axis=0)))
    assert results['centroid_zero_error']<1e-12
    x=e['x']; R=a['relative']
    ident=x.T@R/.5-a['support_matrix']
    results['rank_identity_error']=float(np.linalg.norm(ident))
    results['relative_rank']=int(np.linalg.matrix_rank(R))
    results['support_eigenvalues']=np.linalg.eigvalsh(a['support_matrix']).tolist()
    assert results['rank_identity_error']<1e-12 and results['relative_rank']==2
    results['relative_min_singular']=float(np.linalg.svd(R,compute_uv=False)[-1])
    results['relative_min_singular_lower_bound']=float(.5*results['support_eigenvalues'][0]/np.linalg.norm(x,2))
    assert results['relative_min_singular']+1e-12>=results['relative_min_singular_lower_bound']

    reverse=decode(encode(p,-w,chi))
    expected=-2*.8*a['first_polarity']/(.2+e['inward'].sum()+e['outward'].sum())
    results['wind_reverse_translation_identity_error']=float(np.linalg.norm(a['translation']-reverse['translation']-expected))
    results['wind_reverse_relative_difference']=float(np.linalg.norm(R-reverse['relative']))
    assert results['wind_reverse_translation_identity_error']<1e-12
    assert results['wind_reverse_relative_difference']<1e-12
    results['translation_wind_forward']=a['translation'].tolist()
    results['translation_wind_reversed']=reverse['translation'].tolist()

    scales=np.array([2.,.3,17.])[:,None]
    scaled=decode(encode(p,w,odor_memory(yh*scales)))
    results['framewise_common_scale_max_error']=float(max(np.max(np.abs(a[k]-scaled[k])) for k in ['translation','relative']))
    assert results['framewise_common_scale_max_error']<1e-12

    perm=np.array([2,0,1])
    re=decode(encode(p[perm],w[perm],odor_memory(yh[:,perm])))
    results['permutation_max_error']=float(max(np.max(np.abs(a['translation']-re['translation'])),np.max(np.abs(R[perm]-re['relative']))))
    assert results['permutation_max_error']<1e-12
    angle=.71; Q=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    ro=decode(encode(p@Q.T+[31.,-18.],w@Q.T,chi))
    results['rigid_transform_max_error']=float(max(np.max(np.abs(a['translation']@Q.T-ro['translation'])),np.max(np.abs(R@Q.T-ro['relative']))))
    assert results['rigid_transform_max_error']<1e-12

    eps=1e-6
    fp=phi_frozen(x+eps*R/5,e['inward'],e['outward'])
    fm=phi_frozen(x-eps*R/5,e['inward'],e['outward'])
    numerical=(fp-fm)/(2*eps)
    predicted=float(np.sum(R*R)/(.5*5))
    results['frozen_geometry_ascent_finite_difference']=numerical
    results['frozen_geometry_ascent_analytic']=predicted
    assert abs(numerical-predicted)<1e-8 and numerical>0

    collapsed=decode_merged(e)
    results['polarity_group_collapse_relative_difference']=float(np.linalg.norm(R-collapsed))
    assert results['polarity_group_collapse_relative_difference']>1e-3
    # Same current readings, positions and wind; only causal past differs.
    yh2=yh.copy();yh2[:-1]=yh2[:-1,::-1]
    history_alt=decode(encode(p,w,odor_memory(yh2)))
    results['same_snapshot_different_history_translation_difference']=float(np.linalg.norm(a['translation']-history_alt['translation']))
    results['same_snapshot_different_history_relative_difference']=float(np.linalg.norm(R-history_alt['relative']))
    assert results['same_snapshot_different_history_relative_difference']>1e-3
    assert results['same_snapshot_different_history_translation_difference']>1e-3
    # Same wind and mean odor, different body position/odor association.
    gas_alt=decode(encode(p,w,odor_memory(yh[:,::-1])))
    results['same_wind_reorganized_odor_translation_difference']=float(np.linalg.norm(a['translation']-gas_alt['translation']))
    results['same_wind_reorganized_odor_relative_difference']=float(np.linalg.norm(R-gas_alt['relative']))
    assert results['same_wind_reorganized_odor_relative_difference']>1e-3

    t2,r2,alpha=uniform_speed_scale(a['translation'],R,.1)
    results['uniform_scale']=alpha
    results['uniform_scale_max_speed']=float(np.linalg.norm(t2+r2,axis=1).max())
    assert results['uniform_scale_max_speed']<=.1+1e-12
    assert np.linalg.matrix_rank(r2)==2 and np.linalg.norm(r2.sum(axis=0))<1e-12

    # Geometry rank cannot be created in a perfectly collinear body.
    col=decode(encode(np.array([[-3.,0.],[0.,0.],[3.,0.]]),np.tile([1.,.4],(3,1)),np.ones(3)/3))
    results['collinear_rank']=int(np.linalg.matrix_rank(col['relative']))
    assert results['collinear_rank']==1
    # A receptor at the virtual center has zero radial polarity, no NaN.
    assert np.all(np.isfinite(col['relative']))
    # Identical two-channel moments imply identical operators, regardless of
    # information lost in the original higher-dimensional sensory tensor.
    mono=np.array([[1.,0.],[2.,0.]])
    de=encode(mono,np.tile([1.,0.],(2,1)),np.ones(2)/2)
    dr=decode(de)
    results['two_sensor_rank']=int(np.linalg.matrix_rank(dr['relative']))
    results['two_sensor_relative_norm']=float(np.linalg.norm(dr['relative']))
    assert results['two_sensor_rank']<=1
    assert results['two_sensor_relative_norm']>0
    partial=propose([[0.,0.,0.],[.4,0.,0.]],p,w,time_support_qualified=True)
    results['partial_contact_stage']=partial['stage']
    assert partial['stage']=='CONTACT_CANDIDATES'
    assert partial['raw_update_required']
    empty=propose([[0.,0.,0.]],p,w,time_support_qualified=True)
    results['all_zero_stage']=empty['stage']
    assert empty['stage']=='COVER_OR_SHORT_HOLD' and empty['raw_update_required']
    untimed=propose([[.2,0.,.1]],p,w,time_support_qualified=False)
    results['untimed_stage']=untimed['stage']
    assert untimed['stage']=='REMEASURE_THEN_POSE_COVER'
    rawnegative=np.array([[-.1,.4,-.2]])
    rawcopy=rawnegative.copy()
    negative=propose(rawnegative,p,w,time_support_qualified=True)
    results['legal_negative_sample_stage']=negative['stage']
    assert negative['stage']=='CONTACT_CANDIDATES'
    assert np.array_equal(rawnegative,rawcopy) and negative['raw_update_required']
    untimed_zero=propose([[0.,0.,0.]],p,w,time_support_qualified=False)
    results['untimed_zero_contact_stage']=untimed_zero['stage']
    assert untimed_zero['stage']=='COVER_OR_SHORT_HOLD'
    # A fixed qualified set controls both contact and memory normalization.
    # Arbitrarily large finite readings from a masked instrument must not
    # alter valid sensors' state or the proposed motion; raw remains intact.
    mask=np.array([1.,1.,0.])
    masked_base=yh.copy();masked_base[:,2]=0.
    masked_high=masked_base.copy();masked_high[:,2]=[1e6,1e60,1e300]
    masked_base_copy=masked_base.copy();masked_high_copy=masked_high.copy()
    mq=propose(masked_base,p,w,time_support_qualified=True,quality=mask)
    mh=propose(masked_high,p,w,time_support_qualified=True,quality=mask)
    assert mq['stage']==mh['stage']=='CONTACT_CANDIDATES'
    mask_errors=[np.max(np.abs(mq['encoded']['odor_memory']-mh['encoded']['odor_memory']))]
    mask_errors.extend(np.max(np.abs(mq['decoded'][key]-mh['decoded'][key]))
                       for key in ['translation','relative'])
    results['masked_high_readings_max_output_error']=float(max(mask_errors))
    assert results['masked_high_readings_max_output_error']==0.
    results['masked_probe_memory_and_activation_max']=float(max(
        abs(mh['encoded'][key][2]) for key in ['odor_memory','inward','outward']))
    assert results['masked_probe_memory_and_activation_max']==0.
    results['masked_inputs_raw_preserved']=bool(
        np.array_equal(masked_base,masked_base_copy)
        and np.array_equal(masked_high,masked_high_copy)
        and mq['raw_update_required'] and mh['raw_update_required'])
    assert results['masked_inputs_raw_preserved']
    only_masked=np.zeros_like(yh);only_masked[:,2]=[1e6,1e60,1e300]
    masked_no_contact=propose(only_masked,p,w,time_support_qualified=False,quality=mask)
    results['masked_only_signal_stage']=masked_no_contact['stage']
    assert masked_no_contact['stage']=='COVER_OR_SHORT_HOLD'
    assert masked_no_contact['raw_update_required']
    default_q=propose(yh,p,w,time_support_qualified=True)
    explicit_q=propose(yh,p,w,time_support_qualified=True,quality=np.ones(3))
    results['all_ones_mask_regression_max_error']=float(max(
        np.max(np.abs(default_q['encoded']['odor_memory']-chi)),
        *[np.max(np.abs(default_q['decoded'][key]-a[key])) for key in ['translation','relative']],
        *[np.max(np.abs(default_q['decoded'][key]-explicit_q['decoded'][key]))
          for key in ['translation','relative']]))
    assert results['all_ones_mask_regression_max_error']==0.
    all_invalid=propose(yh,p,w,time_support_qualified=True,quality=np.zeros(3))
    results['all_invalid_sensors_stage']=all_invalid['stage']
    assert all_invalid['stage']=='COVER_OR_SHORT_HOLD'
    try:
        propose(yh,p,w,time_support_qualified=True,quality=[1.,np.nan,0.])
        raise AssertionError('nonfinite quality mask was accepted')
    except ValueError:
        results['nonfinite_quality_mask_rejected']=True
    # Same mean and ordinary affine gradient but different receptor-polarity
    # association. A four-sensor checkerboard has zero first spatial moment.
    square=np.array([[-5.,-5.],[-5.,5.],[5.,-5.],[5.,5.]])
    sw=np.tile([1.,0.],(4,1))
    y1=np.ones(4);y2=np.array([1.4,.6,.6,1.4])
    design=np.column_stack([np.ones(4),square])
    fit1=np.linalg.lstsq(design,y1,rcond=None)[0]
    fit2=np.linalg.lstsq(design,y2,rcond=None)[0]
    aa=decode(encode(square,sw,odor_memory([y1])))
    bb=decode(encode(square,sw,odor_memory([y2])))
    results['same_affine_gradient_difference']=float(np.linalg.norm(fit1-fit2))
    results['same_affine_gradient_decoder_translation_difference']=float(np.linalg.norm(aa['translation']-bb['translation']))
    results['same_affine_gradient_decoder_relative_difference']=float(np.linalg.norm(aa['relative']-bb['relative']))
    assert results['same_affine_gradient_difference']<1e-12
    assert results['same_affine_gradient_decoder_relative_difference']>1e-3
    try:
        encode(p,w*np.nan,chi)
        raise AssertionError('nonfinite inputs were accepted')
    except ValueError:
        results['nan_input_rejected']=True
    try:
        odor_memory([])
        raise AssertionError('empty history was accepted')
    except ValueError:
        results['empty_history_rejected']=True
    # Random irregular 3-8 sensor stress: permutation, rotation, rank identity.
    max_rank_err=0.;trials=0
    for n in range(3,9):
      for j in range(50):
        pp=rng.normal(size=(n,2))*4
        ww=rng.normal(size=(n,2))
        cc=rng.dirichlet(np.ones(n))
        ee=encode(pp,ww,cc);dd=decode(ee)
        err=np.linalg.norm(ee['x'].T@dd['relative']/.5-dd['support_matrix'])
        max_rank_err=max(max_rank_err,float(err))
        assert np.linalg.matrix_rank(dd['relative'])==2
        assert err<1e-10
        trials+=1
    results['random_irregular_trials']=trials
    results['random_max_rank_identity_error']=max_rank_err
    results['claim']='MATHEMATICAL_CERTIFICATES_ONLY; native localization and superiority untested'
    path=Path(__file__).with_name('certificate_results.json')
    path.write_text(json.dumps(results,ensure_ascii=False,indent=2))
    print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
