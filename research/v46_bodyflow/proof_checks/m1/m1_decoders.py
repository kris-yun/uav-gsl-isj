"""V45A proposed source-independent dual sensory/motor decoder.

Mathematical certificate implementation, not a native gas transport experiment.
The two objectives are engineering constructions inspired by joint body-position
and polarity organization, not equations claimed to be implemented by fish.
"""
from __future__ import annotations
import numpy as np


def odor_memory(gas_excess_history, beta=0.65):
    """Normalize each qualified nonnegative frame, then causal memory.

    Input frames must already have a fixed, qualified sensor set and aligned
    timestamps; unqualified sensor columns must be zero. This is a control
    feature, not reconstructed concentration.
    The finite-window weights sum to one; no future frames are accessed.
    """
    y = np.asarray(gas_excess_history, dtype=float)
    if (y.ndim != 2 or y.shape[0] == 0 or y.shape[1] < 2
            or np.any(y < 0) or not np.all(np.isfinite(y))):
        raise ValueError("Need finite nonnegative frames with at least two sensors")
    if not np.isfinite(beta) or not 0 <= beta < 1:
        raise ValueError("beta must be in [0,1)")
    totals=y.sum(axis=1,keepdims=True)
    if np.any(totals <= 0) or not np.all(np.isfinite(totals)):
        raise ValueError("Zero-total frames require COVER/HOLD; retain raw samples")
    shape = y / totals
    w = beta ** np.arange(len(y)-1, -1, -1, dtype=float)
    w /= w.sum()
    return w @ shape


def encode(positions, relative_wind, odor_shape_memory, quality=None,
           scale_m=5., flow_floor=0.1):
    p = np.asarray(positions, float)
    w = np.asarray(relative_wind, float)
    chi = np.asarray(odor_shape_memory, float)
    if p.ndim != 2 or p.shape != w.shape or p.shape[1]!=2 or chi.shape != (len(p),):
        raise ValueError("shape mismatch")
    if (len(p) < 2 or not np.isfinite(scale_m) or scale_m <= 0
            or not np.isfinite(flow_floor) or flow_floor <= 0):
        raise ValueError("invalid geometry/regularization")
    q = np.ones(len(p)) if quality is None else np.asarray(quality,float)
    if q.shape!=(len(p),) or not all(np.all(np.isfinite(t)) for t in [p,w,chi,q]):
        raise ValueError("nonfinite input or quality shape mismatch")
    if np.any(chi < 0) or np.any((q != 0) & (q != 1)):
        raise ValueError("nonnegative activation and preregistered binary quality mask required")
    delta = p-p.mean(axis=0)
    radius = np.linalg.norm(delta,axis=1)
    normals = np.divide(delta,radius[:,None],out=np.zeros_like(delta),
                        where=radius[:,None]>1e-12)
    d = np.einsum('ij,ij->i',w,normals)
    wt = q*chi
    denominator = flow_floor + np.dot(wt,np.abs(d))
    inward = wt*np.maximum(-d,0)/denominator
    outward = wt*np.maximum(d,0)/denominator
    return {'x':delta/scale_m,'inward':inward,'outward':outward,
            'radial_flow':d,'scale_m':float(scale_m),
            'positions':p.copy(),'delta':delta.copy(),
            'relative_wind':w.copy(),'odor_memory':chi.copy(),
            'quality':q.copy()}


def decode(encoded, speed_contact=0.35, speed_flow=0.8, damping_t=0.2,
           speed_reconfigure=0.5, ridge_r=0.15):
    x=encoded['x']; am=encoded['inward']; ap=encoded['outward']
    pars=[speed_contact,speed_flow,damping_t,speed_reconfigure,ridge_r]
    if (not np.all(np.isfinite(pars)) or damping_t <= 0 or ridge_r <= 0
            or min(speed_contact,speed_flow,speed_reconfigure)<0):
        raise ValueError("positive regularization required")
    total=am+ap
    m=total@x
    d=(ap-am)@x
    v_t=(speed_contact*m-speed_flow*d)/(damping_t+total.sum())
    cm=x.T@(am[:,None]*x)
    cp=x.T@(ap[:,None]*x)
    eye=np.eye(x.shape[1])
    im=np.linalg.inv(ridge_r*eye+cm)
    ip=np.linalg.inv(ridge_r*eye+cp)
    g=am[:,None]*(x@im.T)+ap[:,None]*(x@ip.T)
    v_r=speed_reconfigure*(g-g.mean(axis=0))
    return {'translation':v_t,'relative':v_r,'gradient':g,
            'first_contact':m,'first_polarity':d,
            'cov_in':cm,'cov_out':cp,
            'support_matrix':cm@im+cp@ip}


def decode_merged(encoded, speed_reconfigure=.5,ridge_r=.15):
    """Pure branch-collapse ablation: same raw states, geometric domain, budget."""
    x=encoded['x']; a=encoded['inward']+encoded['outward']
    c=x.T@(a[:,None]*x)
    inv=np.linalg.inv(ridge_r*np.eye(x.shape[1])+c)
    g=a[:,None]*(x@inv.T)
    return speed_reconfigure*(g-g.mean(axis=0))


def phi_frozen(x, am, ap, ridge_r=.15):
    """Fixed sensory weights/scale during a local movement proposal."""
    eye=np.eye(x.shape[1]); value=0.
    for a in [am,ap]:
        c=x.T@(a[:,None]*x)+ridge_r*eye
        sign,logdet=np.linalg.slogdet(c)
        if sign<=0: raise ValueError("lost positive definiteness")
        value+=.5*logdet
    return value


def uniform_speed_scale(translation, relative, vmax):
    """Common scale preserves the translation/relative decomposition."""
    v=np.asarray(relative)+np.asarray(translation)
    if not np.isfinite(vmax) or vmax<=0 or not np.all(np.isfinite(v)):
        raise ValueError("finite positive speed cap and finite velocities required")
    alpha=min(1.,float(vmax)/max(1e-15,float(np.linalg.norm(v,axis=1).max())))
    return alpha*np.asarray(translation),alpha*np.asarray(relative),alpha


def propose(raw_excess_history, positions, relative_wind,
            *, time_support_qualified, model_gate_known=False,
            total_contact_threshold=0., beta=.65, quality=None,
            remeasure_budget_s=2.):
    """Minimal explicit stage routing, with no posterior mutation.

    The external application supplies time qualification and a native physical
    coverage/safety controller. This function never certifies source evidence,
    sensor timing, or executable flight. Returned raw_update_required records
    that invalid/no-contact morphology must NOT delete acquired raw data.
    quality is one fixed mask certified for every supplied history frame. The
    caller must restart the window when that set changes; current validity
    cannot retrospectively qualify earlier samples.
    """
    if (not np.isfinite(total_contact_threshold) or total_contact_threshold<0
            or not np.isfinite(remeasure_budget_s) or remeasure_budget_s<=0):
        raise ValueError("nonnegative finite threshold required")
    raw=np.asarray(raw_excess_history,float)
    base={'raw_update_required':True,'physical_execution_certified':False,
          'source_evidence_certified':False}
    if raw.ndim!=2 or raw.shape[0]==0 or raw.shape[1]<2:
        return {**base,'stage':'INVALID_INPUT','reason':'empty or malformed history'}
    if not np.all(np.isfinite(raw)):
        return {**base,'stage':'INVALID_INPUT','reason':'nonfinite instrument sample'}
    mask=np.ones(raw.shape[1]) if quality is None else np.asarray(quality,float)
    if (mask.shape!=(raw.shape[1],) or not np.all(np.isfinite(mask))
            or np.any((mask!=0)&(mask!=1))):
        raise ValueError("fixed preregistered binary quality mask required")
    # Legal negative background-subtracted readings are retained unchanged for
    # inference. Rectification is a separate, lossy CONTROL feature only.
    # Mask before contact/normalization: invalid instrument readings must not
    # change valid sensors' memory or turn a no-contact state into contact.
    y=np.where(mask[None,:]>0,np.maximum(raw,0.),0.)
    # Restart after the latest unqualified/zero-total frame. A partial-contact
    # frame with one nonzero sensor is accepted; no all-sensors-positive gate.
    totals=y.sum(axis=1)
    if totals[-1]<=total_contact_threshold:
        return {**base,'stage':'COVER_OR_SHORT_HOLD','reason':'current zero/weak total'}
    if not time_support_qualified:
        return {**base,'stage':'REMEASURE_THEN_POSE_COVER',
                'remeasure_budget_s':float(remeasure_budget_s),
                'reason':'bounded remeasurement; then independently qualified pose coverage'}
    bad=np.flatnonzero(totals<=total_contact_threshold)
    start=int(bad[-1]+1) if len(bad) else 0
    chi=odor_memory(y[start:],beta=beta)
    encoded=encode(positions,relative_wind,chi,quality=mask)
    if float(encoded['inward'].sum()+encoded['outward'].sum())<=0:
        return {**base,'stage':'GEOMETRY_PROBE','reason':'zero radial activation'}
    decoded=decode(encoded)
    singular=np.linalg.svd(decoded['relative'],compute_uv=False)
    return {**base,'stage':'CONTACT_CANDIDATES','encoded':encoded,
            'decoded':decoded,'relative_singular_values':singular,
            'model_gate_known':bool(model_gate_known),
            'reason':'candidate only; external M2/M3 and physical checks required'}
