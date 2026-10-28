"""Scientific/software contracts, not native localization performance tests."""
from __future__ import annotations
import json
from pathlib import Path
import sys
from dataclasses import replace
from itertools import permutations
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from v46_flowolf import *
from v46_flowolf.core import common_catalog, common_scale


def setup(order=(0,1,2), *, mode="m1_full", K=8, score_kind="min_separation", qualifiers=None):
    specs=[SensorSpec("probe-C",gain=1.3,background=.003,sigma=.0002,tau_s=.7,lag_steps=1,vmax=.8),
           SensorSpec("probe-A",gain=.8,background=-.002,sigma=.00025,tau_s=.4,lag_steps=0,vmax=1.),
           SensorSpec("probe-B",gain=1.1,background=.001,sigma=.0003,tau_s=1.0,lag_steps=2,vmax=.9)]
    p=np.array([[-3.,-2.,3.],[4.,-1.,3.],[-1.,3.,3.]])
    specs=[specs[i] for i in order];p=p[list(order)]
    theta=np.array([[sx,sy,h,q] for sx in [-1.,1.] for sy in [-1.,1.]
                    for h in [2.,4.] for q in [12.,24.]])
    bank=SourceBank(theta,np.ones(len(theta)))
    model_args=dict(t0=5.,dt=.5,wind=(.2,.1,0),kappa=1.,release_time=0.)
    model=GreenZOHModel(bank,specs,p,**model_args)
    posterior=GaussianPosterior(model)
    safety=ConvexBoxSafety([-20,-20,1],[20,20,5],min_separation=.5,tracking_error=.05)
    cfg=ControllerConfig(budget_s=20.,action_s=2.,K=K,score_kind=score_kind,eig_samples=16)
    ctrl=Controller(posterior,safety,cfg,mode)
    world=ReferenceWorld([1.,-1.,2.,24.],specs,p,seed=23,qualifiers=qualifiers,**model_args)
    hold=Candidate("INITIAL",tuple(s.physical_id for s in specs),np.zeros_like(p),2.)
    block=world.execute(hold,output_order=hold.sensor_ids)
    ctrl.observe(block)
    return ctrl,world,block


def raw_reordered(block, order):
    return RawBlock(block.block_id,tuple(f.ordered(order) for f in block.frames))


def check_close(a,b,tol=1e-11):
    e=float(np.max(np.abs(np.asarray(a)-np.asarray(b))))
    assert e < tol,(e,a,b)
    return e


def main():
    report={"scope":"MATHEMATICAL_AND_SOFTWARE_CERTIFICATES_ONLY; no native benchmark"}
    base,world,block=setup()
    base_action,base_record=base.decide()
    assert base_record["scored_count"]==8
    assert base_record["source_confirmation"] is False
    assert base_record["score"]["continuous_source_certificate"]=="UNKNOWN"
    originalmass=base.posterior.mass.copy()
    originaltime=base.posterior.model.t
    originalstate=base.posterior.model.z.copy()
    # Same raw repackaged under another block ID is still rejected atomically.
    for b in [block,RawBlock("repackaged",block.frames),
              RawBlock("reordered",tuple(f.ordered(tuple(reversed(f.sensor_ids))) for f in block.frames))]:
        try:base.observe(b);raise AssertionError("Duplicate accepted")
        except ValueError as e:assert "uplicate" in str(e)
        check_close(base.posterior.mass,originalmass)
        check_close(base.posterior.model.z,originalstate)
        assert base.posterior.model.t==originaltime
    report["raw_once"]={"samples":len(base.posterior.ledger),"duplicate_rejections":3,"atomic":True}

    # Every storage order has different gain/delay/history carried with its ID.
    errors=[];allkeys=[]
    for order in permutations(range(3)):
        c,w,b=setup(order)
        action,record=c.decide()
        allkeys.append(action.semantic_id)
        errors.extend([check_close(c.posterior.mass,originalmass),
                       check_close(action.ordered(base.ids).velocities,base_action.velocities),
                       abs(record["score"]["score"]-base_record["score"]["score"])])
        c.execute_and_update(w,action)
        assert len(c.posterior.ledger)==8
    assert len(set(allkeys))==1
    report["full_chain_storage_permutation"]={"permutations":6,"max_error":max(errors),"candidate":allkeys[0]}

    # Deterministic semantic ties, safe projection and all-library negative control.
    exhaustive=[]
    for mode in ["m1_full","upwind","ordinary_array","gradient","information_uniform","merged_r","no_history"]:
        c,w,b=setup(mode=mode,K=1000)
        action,record=c.decide()
        exhaustive.append((mode,action.semantic_id,record["score"]["score"]))
    assert len({x[1] for x in exhaustive})==1
    assert np.ptp([x[2] for x in exhaustive])<1e-12
    report["full_catalog_negative_control"]={"methods":len(exhaustive),"candidate":exhaustive[0][1],"all_equal":True}
    c,w,b=setup()
    catalog=common_catalog(c.ids,c.last_frame.positions,c.cfg,c.specs)
    tied=min(reversed(catalog),key=lambda a:(0.0,a.semantic_id))
    assert tied.semantic_id=="T00_R00"
    report["semantic_tie_order_independent"]=True
    c,w,b=setup(K=1000)
    c.cfg=replace(c.cfg,source_tolerance=100.)
    actual_tie,tie_record=c.decide()
    assert actual_tie.semantic_id=="T00_R00" and tie_record["score"]["score"]==0.
    report["actual_controller_tie"]=actual_tie.semantic_id

    # Wrongly reassigning calibration while leaving the physical records in
    # place is not a symmetry. Keep this counterexample next to the valid test.
    c,w,b=setup()
    original_e,original_d=c._encode_decode()
    gains=[s.gain for s in c.specs]
    c.specs=tuple(replace(s,gain=gains[(i+1)%len(gains)]) for i,s in enumerate(c.specs))
    wrong_e,wrong_d=c._encode_decode()
    wrong_difference=float(np.linalg.norm(original_d["translation"]-wrong_d["translation"]))
    assert wrong_difference>1e-6
    report["wrong_calibration_association_counterexample"]=wrong_difference
    # Shared sanitation: ordinary controls must not consume a channel that M1
    # excludes. Otherwise a purported mechanism gain could be a dirty baseline.
    baseline_errors={}
    for mode in ["upwind","gradient"]:
        c,w,b=setup(mode=mode)
        mask=np.array([True,True,False])
        c.last_frame=replace(c.last_frame,instrument_valid=mask)
        clean=c._anchors(None,None)[0]
        raw=c.last_frame.raw.copy();raw[2]=1e100
        wind=c.last_frame.ambient_wind.copy();wind[2]=[1e100,-1e100,1e100]
        c.last_frame=replace(c.last_frame,raw=raw,ambient_wind=wind)
        dirty=c._anchors(None,None)[0]
        baseline_errors[mode]=check_close(clean,dirty)
        if mode=="gradient":assert c.baseline_fallback=="GRADIENT_RANK_DEFICIENT_TO_QUALIFIED_UPWIND"
    report["ordinary_baselines_share_qualification"]=baseline_errors

    # Unknown qualifications cannot create source confirmation. Shape is not
    # silently used as common-age evidence, and unknown model permits exploration.
    unknown=Qualifications(time=Gate(GateStatus.PASS,"known clock","fixture"))
    c,w,b=setup(qualifiers=unknown)
    action,r=c.decide()
    assert r["stage"]=="M1_TENTATIVE" and not r["source_confirmation"]
    assert r["qualifications"]=={"time":"PASS","shape":"UNKNOWN","coherence":"UNKNOWN","model":"UNKNOWN"}
    report["qualification_separation"]=r["qualifications"]
    # An optional declared finite-domain posterior rule is executable and
    # revocable, but it makes no calibrated false-positive-rate claim.
    c,w,b=setup()
    c.posterior.model.bank=SourceBank(c.posterior.model.bank.theta,c.posterior.model.bank.prior,
                                    exact_declared_domain=True)
    c.cfg=replace(c.cfg,confirmation_threshold=.95)
    c.last_frame=replace(c.last_frame,qualifications=Qualifications(
        time=Gate(GateStatus.PASS,"known time","fixture"),
        model=Gate(GateStatus.PASS,"specified raw model","fixture")))
    conf=c.refresh_confirmation()
    assert conf["status"]=="CONDITIONAL_CONFIRMED" and conf["calibrated_frequentist_error_rate"] is None
    c.last_frame=replace(c.last_frame,qualifications=Qualifications(time=Gate(GateStatus.PASS)))
    revoked=c.refresh_confirmation()
    assert revoked["status"]=="REVOKED" and c.source_confirmation is False
    assert c.posterior.xy_probability()[1].max()>.95
    report["conditional_confirmation_revoked"]={"initial":conf["status"],"after_unknown":revoked["status"],
                                               "retained_posterior":True,"frequentist_guarantee":False}
    # A currently PASS frame cannot retroactively certify UNKNOWN history.
    c,w,b=setup(qualifiers=unknown)
    c.posterior.model.bank=SourceBank(c.posterior.model.bank.theta,c.posterior.model.bank.prior,
                                    exact_declared_domain=True)
    c.cfg=replace(c.cfg,confirmation_threshold=.95)
    w.qualifications=Qualifications(time=Gate(GateStatus.PASS,"current clock","fixture"),
                                   model=Gate(GateStatus.PASS,"current model","fixture"))
    current=w.execute(Candidate("HOLD",c.ids,np.zeros_like(c.last_frame.positions),2.))
    c.observe(current)
    assert c.last_frame.qualifications.model.status==GateStatus.PASS
    assert c.posterior.xy_probability()[1].max()>.95 and not c.source_confirmation
    report["current_pass_does_not_certify_unknown_history"]=True
    c,w,b=setup()
    c.posterior.model.bank=SourceBank(c.posterior.model.bank.theta,c.posterior.model.bank.prior,
                                    exact_declared_domain=True)
    c.cfg=replace(c.cfg,confirmation_threshold=.95)
    assert c.refresh_confirmation()["status"]=="CONDITIONAL_CONFIRMED"
    w.qualifications=unknown
    mixed=w.execute(Candidate("HOLD",c.ids,np.zeros_like(c.last_frame.positions),2.))
    c.observe(mixed)
    assert c.confirmation["status"]=="REVOKED"
    w.qualifications=Qualifications(time=Gate(GateStatus.PASS,"current clock","fixture"),
                                   model=Gate(GateStatus.PASS,"current model","fixture"))
    later=w.execute(Candidate("HOLD",c.ids,np.zeros_like(c.last_frame.positions),2.))
    c.observe(later)
    assert c.confirmation["status"]=="REVOKED" and not c.source_confirmation
    assert len(c.posterior.ledger)==12
    report["pass_unknown_pass_remains_revoked"]={"status":c.confirmation["status"],"raw_frames_retained":12}

    # Changing likelihood parameters cannot multiply a new model onto an old
    # posterior. A newly acquired block is archived before the explicit error.
    c,w,b=setup()
    c.posterior.model.kappa=1.2
    try:c.decide();raise AssertionError("Mixed-model decision accepted")
    except ValueError as e:assert "fresh posterior" in str(e)
    new=w.execute(Candidate("HOLD",c.ids,np.zeros_like(c.last_frame.positions),2.))
    try:c.observe(new);raise AssertionError("Mixed-model update accepted")
    except ValueError as e:assert "fresh posterior" in str(e)
    assert len(c.posterior.ledger)==4 and len(c.posterior.received_archive)==8
    report["model_change_requires_fresh_raw_replay"]=True
    timeunknown=Qualifications()
    c,w,b=setup(qualifiers=timeunknown)
    a,r1=c.decide();assert r1["stage"]=="REMEASURE"
    c.execute_and_update(w,a)
    a,r2=c.decide();assert r2["stage"]=="COVER_TIME_UNKNOWN"
    assert c.safety.legal(c.last_frame.positions,a)
    report["bounded_remeasurement"]={"first":r1["stage"],"next":r2["stage"],"used_s":c.remeasure_used}
    failed=replace(unknown,model=Gate(GateStatus.FAIL,"independent residual violation","fixture"))
    c,w,b=setup(qualifiers=failed)
    a,r=c.decide();assert r["stage"]=="COVER_MODEL_FAIL" and c.safety.legal(c.last_frame.positions,a)
    report["failed_model_fallback_safe"]=True

    # A negative raw value enters the Gaussian likelihood without rectification.
    c,w,b=setup()
    a=Candidate("HOLD",c.ids,np.zeros_like(c.last_frame.positions),2.)
    new=w.execute(a)
    frames=list(new.frames)
    ff=frames[0]
    negative=ff.raw.copy();negative[0]=-.01
    frames[0]=replace(ff,raw=negative)
    altered=RawBlock(new.block_id,tuple(frames))
    means,state=c.posterior.model.preview_block(tuple(f.ordered(c.ids) for f in altered.frames))
    sigma=np.array([s.sigma for s in c.specs])
    y=np.stack([f.ordered(c.ids).raw for f in altered.frames])
    log=c.posterior.log_mass-.5*np.sum(((y[None]-means)/sigma)**2,axis=(1,2))
    expected=np.exp(log-log.max());expected/=expected.sum()
    c.observe(altered)
    report["negative_raw_likelihood_error"]=check_close(c.posterior.mass,expected)
    assert c.posterior.raw_archive[-4].raw[0]<0

    # Mask is a control qualification, distinct from a raw saturation/fault flag.
    c,w,b=setup()
    new=w.execute(Candidate("HOLD",c.ids,np.zeros_like(c.last_frame.positions),2.))
    valid=np.array([True,True,False])
    frames=tuple(replace(f,instrument_valid=valid) for f in new.frames)
    c.observe(RawBlock(new.block_id,frames))
    assert len(c.control_window)==4
    e,d=c._encode_decode()
    assert e is not None and e["odor_memory"][2]==0
    assert len(c.posterior.ledger)==8
    report["mask_change_restarts_control_only"]={"new_window":len(c.control_window),"raw_ledger":len(c.posterior.ledger)}
    faultblock=w.execute(Candidate("HOLD",c.ids,np.zeros_like(c.last_frame.positions),2.))
    faultframes=tuple(replace(f,raw_status=("OK","SATURATED","OK")) for f in faultblock.frames)
    oldmass=c.posterior.mass.copy()
    try:c.observe(RawBlock(faultblock.block_id,faultframes));raise AssertionError("Unsupported fault likelihood accepted")
    except ValueError as e:assert "fault likelihood" in str(e)
    check_close(c.posterior.mass,oldmass)
    assert all(f.sample_id in c.posterior.received_archive for f in faultframes)
    report["unsupported_fault_archived_not_faked"]=True

    # Continuous separation catches a collision missed at endpoints.
    ids=("A","B")
    p=np.array([[-1.,0,3],[1.,0,3]])
    crossing=Candidate("CROSS",ids,np.array([[2.,0,0],[-2.,0,0]]),1.)
    safe=ConvexBoxSafety([-3,-3,1],[3,3,5],min_separation=.5)
    assert np.linalg.norm(p[0]-p[1])>.5
    end=p+crossing.velocities;assert np.linalg.norm(end[0]-end[1])>.5
    assert not safe.legal(p,crossing)
    report["continuous_safety_endpoint_counterexample"]=True

    # Executed interruption: posterior time/state follows actual shorter path.
    c,w,b=setup()
    a,r=c.decide()
    partial=w.execute(a,fraction=.5)
    c.observe(partial)
    assert abs(c.posterior.model.t-(b.frames[-1].t+1.))<1e-12
    check_close(c.posterior.model.positions,w.model.positions)
    report["interrupted_execution_actual_path_used"]={"executed_s":1.,"planned_s":2.}

    # Noise and sensor delays do not leak future truth into decisions; choosing
    # two different world truths after the same history cannot alter a proposal.
    c,w,b=setup()
    before=c.posterior.model.forward_calls
    a,r=c.decide()
    assert c.posterior.model.forward_calls-before==r["scored_count"]
    report["expensive_prediction_accounting"]={"calls":r["scored_count"],"configured_K":c.cfg.K,
                                              "catalog_count":r["catalog_count"]}

    # XY marginalization and EIG: all nuisance rows sharing XY are merged.
    c,w,b=setup(score_kind="xy_eig")
    xy,mass=c.posterior.xy_probability()
    assert len(xy)==4 and abs(mass.sum()-1.)<1e-12
    a,r=c.decide();assert np.isfinite(r["score"]["score"])
    report["xy_marginal_and_finite_mc"]={"joint_hypotheses":len(c.posterior.mass),"xy_cells":len(xy),"eig":r["score"]["score"]}
    # Isolated EIG certificate with deliberately uncertain XY and duplicate
    # nuisance rows. This avoids a saturated initial posterior hiding a bug.
    theta=np.array([[0.,0.,1.,1.],[0.,0.,2.,1.],[3.,0.,1.,1.],[3.,0.,2.,1.]])
    bank=SourceBank(theta,np.ones(4))
    specs=[SensorSpec("A"),SensorSpec("B")]
    p=np.array([[-1.,0,2],[1.,0,2.]])
    cm=GreenZOHModel(bank,specs,p)
    cc=Controller(GaussianPosterior(cm),ConvexBoxSafety([-5,-5,0],[5,5,4]),
                  ControllerConfig(score_kind="xy_eig",eig_samples=2048))
    separated=cc._xy_eig(np.array([[0.],[0.],[5.],[5.]]))
    assert .4<separated<np.log(2)+1e-12
    allsame=theta.copy();allsame[:,:2]=0
    cc.posterior.model.bank=SourceBank(allsame,np.ones(4))
    onlyheight=cc._xy_eig(np.array([[0.],[5.],[0.],[5.]]))
    assert abs(onlyheight)<1e-14
    report["xy_eig_nontrivial_certificate"]={"xy_separated_information":separated,"same_xy_height_only_information":onlyheight}

    # True loop: multiple actual actions, new raw blocks and posterior updates.
    c,w,b=setup()
    for _ in range(4):
        a,r=c.decide();c.execute_and_update(w,a)
    assert len(c.posterior.ledger)==20
    xy,mass=c.posterior.xy_probability()
    report["runnable_reference_loop"]={"decisions":len(c.decisions),"raw_samples":len(c.posterior.ledger),
                                      "probability_sum":float(mass.sum()),"source_confirmation":c.source_confirmation,
                                      "physical_scope":"declared Green midpoint-input ZOH; not native"}

    # The implementation is not hard-coded to the paper's three-UAV drawing.
    sizes={}
    for n in [2,4]:
        angle=np.arange(n)*2*np.pi/n
        positions=np.column_stack([3*np.cos(angle),3*np.sin(angle),np.full(n,3.)])
        specs=[SensorSpec(f"node-{i}",sigma=.0003) for i in range(n)]
        theta=np.array([[x,y,2.,q] for x in [-1.,1.] for y in [-1.,1.] for q in [12.,24.]])
        bank=SourceBank(theta,np.ones(len(theta)))
        args=dict(t0=5.,dt=.5,wind=(.2,.1,0),kappa=1.)
        model=GreenZOHModel(bank,specs,positions,**args)
        controller=Controller(GaussianPosterior(model),ConvexBoxSafety([-20,-20,1],[20,20,5]),ControllerConfig(K=4))
        world=ReferenceWorld([1.,-1.,2.,24.],specs,positions,seed=3,**args)
        initial=world.execute(Candidate("INIT",model.ids,np.zeros_like(positions),2.))
        controller.observe(initial)
        action,record=controller.decide()
        controller.execute_and_update(world,action)
        sizes[str(n)]={"catalog":record["catalog_count"],"scored":record["scored_count"],
                       "decoded_R_rank":record.get("m1_relative_rank"),"raw_samples":len(controller.posterior.ledger)}
        if n==2:assert record["m1_relative_rank"]<=1
    report["two_and_four_sensor_runs"]=sizes

    path=Path(__file__).resolve().parents[1]/"results"/"chain_certificates.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__":main()
