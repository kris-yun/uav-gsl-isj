"""Freeze the authorized plan, cache hashes, implementation before fitting."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import ast,json,csv,hashlib,shutil,platform
BASE=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent
PARENT=BASE/'outputs/PMFS_RK0_PRO_REVIEW_BUNDLE_20261010_V2'
OUT=BASE/'outputs/PMFS_RK1_MATCHED_SUPPORT_CROSSFIT_20261010'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not OUT.exists(),'refuse overwrite/restart previous fit'
assert sha(PARENT/'SHA256SUMS.json')=='c808546bc326cd0e2a35ed28e212b4bb98922bae66b7ba1a8017f8982d501b0b'
pm=json.loads((PARENT/'SHA256SUMS.json').read_text(encoding='utf-8'))
for n,h in pm.items():assert sha(PARENT/n)==h,n
cache=PARENT/'RK0_NEW/reference_contribution_cache';idx=json.loads((cache/'CONTRIBUTION_CACHE_RESULT.json').read_text(encoding='utf-8'))
input_names=['RK0_NEW/reference_contribution_cache/'+e['cache_relative_path'] for e in idx['frames']]
input_names+=['RK0_NEW/reference_contribution_cache/'+n for n in ['CONTRIBUTION_CACHE_RESULT.json','FIRST_NATIVE_ANCHOR.json','CACHE_NATIVE_CPP_TOTAL_ANCHORS.csv','FIT_EXPOSURE_MULTIPLICITY.csv','RECEPTOR_ALIAS_51_TO_10.csv','RECEPTOR_POSES_STOP_ORDER.f32.npy']]
for b in idx['reference_ids']:
    input_names+=['PARENT_M2M3_FROZEN/M2_FROZEN/native_reference_evidence/realizations/'+b+'/'+n for n in ['QUERY_OUTPUT.csv','QUERY_PHYSICAL_LINEAGE.csv','QUERIES.csv']]
OUT.mkdir();(OUT/'source').mkdir()
sources={}
for n in ['run_rk1.py','supervise_rk1.py']:
    ast.parse((WORK/n).read_text(encoding='utf-8'));shutil.copyfile(WORK/n,OUT/'source'/n);sources[n]=sha(OUT/'source'/n)
shutil.copyfile(BASE/'outputs/PMFS_TARGETED_MECHANISM_PLAN_20261010.md',OUT/'AUTHORIZED_PLAN_zh.md')
pre=WORK/'SCIENCE_REVIEW_zh.md'
if pre.exists():shutil.copyfile(pre,OUT/'PRE_EXECUTION_SCIENTIFIC_REVIEW_zh.md')
mapping={'C7_0':'C7','C7_1':'C7','K2_0':'K2','K2_1':'K2'}
dump(OUT/'ANALYSIS_ONLY_GENERATOR_MAPPING_FROZEN.json',mapping)
contract=dict(stage='RK1_SHARED_SUPPORT_WHOLE_REALIZATION_CROSSFIT',user_authorization='Direct human 继续 after the explicit two-fold matched-support U/S/C plan; no new physics or future method batch authorized.',parent_commit='16d69ac263ec2f8a17fa0d4895b9e5fe9837f885',parent_frozen_root_manifest_SHA256=sha(PARENT/'SHA256SUMS.json'),authorized_plan_SHA256=sha(OUT/'AUTHORIZED_PLAN_zh.md'),executed_source_SHA256=sources,input_SHA256={n:sha(PARENT/n) for n in sorted(input_names)},analysis_mapping_file_SHA256=sha(OUT/'ANALYSIS_ONLY_GENERATOR_MAPPING_FROZEN.json'),folds=[dict(fold='T0_E1',train=['C7_0','K2_0'],test=['C7_1','K2_1']),dict(fold='T1_E0',train=['C7_1','K2_1'],test=['C7_0','K2_0'])],XY='float32 XY minus float32 origin(-7.55,-7.88), divide float32 .25 then mathematical floor',class_split='Train-only exposure-weighted global medians z and sigma_cm; >=cut high; class=2*height_bit+sigma_bit.',support='Q is intersection of fine XY/class keys appearing in both train banks. U,S,C_C7,C_K2 all fit and predict the exact same selected-Q particles. No heldout-driven support.',response='Existing cached native f32 per-particle phi; sum full/Q/tail in float64. No new phi/LOS/query executable.',kernels='U pooled XY, S pooled finekey, C_C7 and C_K2 separately conditioned XY; all zero contributions remain in denominators. Eight tables across two folds.',tail='Exact native sum over test particles outside Q added identically to every arm. Oracle intervention only; never deployable missing-kernel imputation.',prediction_freeze='Both C hypotheses saved for train/test/alternate membership before selecting generating-condition C_ORACLE in analysis. Bank names remain known metadata; no double-blind claim.',primary='Per whole-bank test MSE; only U→S and S→C_ORACLE. Four banks equal weight, all directions/反例 kept. MSE direction threshold max(1e-12,1e-10*scale) is numerical only, not statistical significance/effect-size.',secondary='Signed error, MAE, event errors with same tail/threshold, per-key source conditional difference reproduction and coverage; no source accuracy or posterior.',limits='Same inspected four banks/one geometry/static wind/one fixed route; correlated frames; C and S nonnested, C source-aware oracle/extra conditional capacity.',wall_limit_s=300,RSS_limit_bytes=512*1024**2,new_output_limit_bytes=200*1024**2,batch_entries=1,stop='Input or native anchor mismatch, nonfinite, runtime/resource limit. No additional source/statecap/seed/CFD/GADEN/ROS/VM/navigation/neural training.',numerical_tolerances=dict(relative=2e-12,absolute=3e-13,integer_counts='exact',native_F32_anchors='exact bit'),kernel_tables_fitted=8,new_phi_queries=0,new_GADEN=0,new_CFD=0,new_ROS=0,new_VM=0,new_network_training=0)
dump(OUT/'contract.json',contract)
(OUT/'PRE_RUN_CONTRACT_SHA256.txt').write_text(sha(OUT/'contract.json')+'  contract.json\n',encoding='utf-8')
dump(OUT/'ENVIRONMENT.json',dict(Python=sys.version,platform=platform.platform(),NumPy=__import__('numpy').__version__,bytecode_disabled=True))
dump(OUT/'PRE_EXECUTION_PARENT_PRESERVATION.json',dict(parent_manifest_SHA256=sha(PARENT/'SHA256SUMS.json'),parent_members_hashed=len(pm),all_hashes_match=True,new_kernel_fits_yet=0))
print(json.dumps(dict(status='FROZEN_BEFORE_FIT',out=str(OUT),contract_SHA256=sha(OUT/'contract.json'),inputs=len(contract['input_SHA256']),source_SHA256=sources),ensure_ascii=False,indent=2))
