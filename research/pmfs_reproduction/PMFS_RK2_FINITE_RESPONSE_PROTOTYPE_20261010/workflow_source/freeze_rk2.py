"""Freeze A rules and source before any new method score is observed."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,shutil,platform
BASE=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent
OUT=BASE/'outputs/PMFS_RK2_FINITE_RESPONSE_PROTOTYPE_20261010'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):
    assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (OUT/'contract.json').exists()
for n in ['rk2_models.py','rk2_infer.py','test_rk2_infer.py','run_rk2.py','supervise_rk2.py']:
    compile((WORK/n).read_text(encoding='utf-8'),str(WORK/n),'exec')
    shutil.copyfile(WORK/n,OUT/'source'/n)
for n in ['CONTRACT_REVIEW_zh.md','PRE_EXECUTION_CODE_REVIEW_zh.md','INPUT_INTERFACE_AUDIT_zh.md','INPUT_INTERFACE_PATHS.json','PRO_ADDENDUM_INDEPENDENT_REVIEW_zh.md','PRO_ADDENDUM_INDEPENDENT_REVIEW.json','INFER_SOFTWARE_QA.json']:
    shutil.copyfile(WORK/n,OUT/n)
source={p.name:sha(p) for p in sorted((OUT/'source').iterdir())}
prepared={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and 'source' not in p.relative_to(OUT).parts}
contract=dict(stage='RK2_A_SINGLE_FINITE_RESPONSE_PROTOTYPE',parent_commit='210b94e5de0ab7e906136fd0765c3639f10103b2',
    parent_root_manifest_SHA256='b310b6c7d13112660ccd1bdd0cd4fbbb8f708ceb53e02bec4f03126d12575534',
    PRO_ZIP_SHA256='212ed6dd59c5f5e9f8e8e098f0e877dd8ff863ef359b8e01b91da2862332568f',
    user_authorization='Human submitted PRO request explicitly directing one old-material RK2-A finite method comparison; future B is design only.',
    source_SHA256=source,prepared_input_SHA256=prepared,
    training='C7_0/1 K2_0/1 only; 4 full realizations; stationary h at ten locked receiver poses',
    compression_evaluation='C7_2/3 K2_2/3, old inspected development holdouts, explicit simulator-state interface only',
    infer='two candidate hypotheses each with 2 reference forecasts; observed scalar gas from old 2/3 tasks; no test states, phi, Q, tail, labels',
    ridge_lambda=.01,solver_maxiter=600,solver_gtol=1e-8,solver_ftol=1e-12,KKT_relative_tolerance=1e-6,
    loss='Per-pose 20 query mean squared native-F32 total-response error plus lambda*(RMS-scaled coefficient - common particle-mean prior)^2',
    prior_weighting='Each complete training realization has total particle-exposure weight1; all zero contributions retained. Query loss equal whole-realization/time weight.',
    feature_ids=['float32 XY cell subposition_x','float32 XY cell subposition_y','z metres','sigma centimetres'],
    L='One globally shared axis-aligned tree, maximum4 leaves3nodes; same ordinary nonnegative decoder; no learned transition or sourceID router',
    split_quantiles=[.25,.5,.75],split_loss_tolerance=1e-10,max_partition_proposals=72,
    split_tie_rule='ascending training MSE then leafID then featureID then numeric cut; empty-child/capacity exclusions before fitting',
    S='Fixed training-weighted median z x sigma four-class router, same query fit/prior/fallback as U and L',
    capacity='L active state count and canonical bytes and actual minimal Python owning-array runtime bytes no greater than S; routing charged; runtime NPZ bytes checked too',
    fallback='Missing (XY,class) only: local complete native PID/LOS on that input/candidate own particles, no observer hidden tail; no zero-fill',
    event_threshold='np.float32(response)>np.float32(.1), per reference first then M=2 Jeffreys(alpha=.5,beta=.5)',
    inference_score='50 block mean marginal Bernoulli log score; temperature1 softmax same for all methods; composite probability not calibrated joint posterior',
    task_score_tolerance=1e-10,Top1_ties='not uniquely localized: error1 and tie count reported',
    A_gate='equal-bank sourceNLL L strictly below both U_query/S_query beyond1e-10; Top1 errors no higher than either; storage within S and measured local Python reference readout no slower than F',
    A_gate_is_development_only=True,B_suggested_10percent_and_point2nat_are_not_A_requirements=True,
    physical_reader_cost='F actual local native-math recomputation from own raw snapshots with phi/LOS counts; not cachedsum timing and not unmeasured ROS/C++ speed',
    wall_limit_s=600,RSS_limit_bytes=1024**3,output_limit_bytes=1024**3,threads=1,
    new_physics_GADEN_CFD_ROS_VM_navigation_network_training=False,new_L_versions=1,automatic_scientific_retry=False,
    future_B='geometry design and12-realization resource proposal only; requires separate approval before any generation')
dump(OUT/'contract.json',contract)
(OUT/'PRE_RUN_CONTRACT_SHA256.txt').write_text(sha(OUT/'contract.json')+'  contract.json\n',encoding='utf-8')
dump(OUT/'ENVIRONMENT.json',dict(Python=sys.version,platform=platform.platform(),source_entry_count=0,CPU_threads_frozen=1))
dump(OUT/'PRE_EXECUTION_PATCHES_AND_QA.json',dict(metadata_field_fixed='filament_records',candidate_groups='metadata IDs, equal group XYZ',empty_train_children_excluded=True,Top1_tie_is_error=True,
    model_software_QA_cases=5,model_software_QA_latest_source_SHA256=source['rk2_models.py'],infer_software_QA_cases=10,
    source_still_not_executed_on_scientific_data=True))
print(json.dumps(dict(status='RULES_SOURCE_AND_INPUTS_FROZEN_BEFORE_METHOD_EXECUTION',contract_SHA256=sha(OUT/'contract.json'),source_files=len(source),input_files=len(prepared)),ensure_ascii=False))
