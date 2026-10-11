"""Static RK2 preparation only: no fit, response query or model score."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,csv,shutil,os
import numpy as np
BASE=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
PARENT=BASE/'outputs/PMFS_RK1_PRO_REVIEW_BUNDLE_20261010'
OUT=BASE/'outputs/PMFS_RK2_FINITE_RESPONSE_PROTOTYPE_20261010'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not OUT.exists(),'Refuse overwrite a prior RK2'
OUT.mkdir();(OUT/'observable_inputs').mkdir();(OUT/'evaluation_only').mkdir();(OUT/'source').mkdir()
oldmanifest=PARENT/'SHA256SUMS.json'
assert sha(oldmanifest)=='b310b6c7d13112660ccd1bdd0cd4fbbb8f708ceb53e02bec4f03126d12575534'
old=json.loads(oldmanifest.read_text(encoding='utf-8'))
cache=PARENT/'RK0_NEW/reference_contribution_cache'
ci=json.loads((cache/'CONTRIBUTION_CACHE_RESULT.json').read_text(encoding='utf-8'))
m2=PARENT/'PARENT_M2M3_FROZEN/M2_FROZEN'
aliases={r['query_id']:r for r in rows(cache/'RECEPTOR_ALIAS_51_TO_10.csv')}
inputs={}
def bind(p):
    rel=p.relative_to(PARENT).as_posix();h=sha(p);assert old[rel]==h,rel;inputs[rel]=h
bind(oldmanifest) if False else None
for p in [cache/'CONTRIBUTION_CACHE_RESULT.json',cache/'RECEPTOR_ALIAS_51_TO_10.csv',cache/'RECEPTOR_POSES_STOP_ORDER.f32.npy',m2/'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv',PARENT/'RK0_NEW/source/verify_raw_receiver_queries.py',PARENT/'RK0_NEW/source/cache_native.py']:
    bind(p)
for e in ci['frames']:bind(cache/e['cache_relative_path'])
meta=[];plan=None;truth={};banks=['C7_0','C7_1','K2_0','K2_1','C7_2','C7_3','K2_2','K2_3']
for i,b in enumerate(banks):
    d=m2/'native_reference_evidence/realizations'/b
    for n in ['QUERY_OUTPUT.csv','QUERY_PHYSICAL_LINEAGE.csv','ALL_FRAME_SHA256_AND_TIME.csv','EXECUTION_INPUT.json','PARAMETERS.yaml','GENERATION_QUALIFICATION.json']:
        bind(d/n)
    lineage={int(r['block_id']):r for r in rows(d/'QUERY_PHYSICAL_LINEAGE.csv') if r['membership_branch']=='0'}
    qr=[r for r in rows(d/'QUERY_OUTPUT.csv') if r['query_id'] in aliases and aliases[r['query_id']]['membership_branch']=='0']
    qr.sort(key=lambda r:int(aliases[r['query_id']]['block_id']))
    assert len(qr)==50 and {int(aliases[r['query_id']]['block_id']) for r in qr}==set(range(50))
    rec=[]
    for r in qr:
        a=aliases[r['query_id']];block=int(a['block_id']);frame=int(r['frame'])
        assert frame==int(lineage[block]['selected_frame'])
        bind(d/'bank'/('iteration_'+str(frame)))
        rec.append(dict(block_id=block,frame=frame,pose_id=int(a['pose_index']),receiver_xyz=[float(r[k]) for k in ['x','y','z']],
            target_physical_s=float(lineage[block]['target_physical_s']),native_ppm=float(np.float32(float(r['ppm_float32'])))))
    receiverplan=[{k:r[k] for k in ['block_id','frame','pose_id','receiver_xyz','target_physical_s']} for r in rec]
    if plan is None:plan=receiverplan
    else:assert plan==receiverplan,'candidate time/receiver plan mismatch'
    if i<4:
        opaque='REF_'+str(i).zfill(2);candidate='candidate_000' if i<2 else 'candidate_001';role='reference'
    else:
        opaque='O'+str(i-4).zfill(2);candidate=None;role='compression_evaluation_only'
        truth[opaque]='candidate_000' if i<6 else 'candidate_001'
        dump(OUT/'observable_inputs'/(opaque+'.json'),dict(observation_id=opaque,observed_ppm=[r['native_ppm'] for r in rec],receiver_plan_id='B4_FROZEN_50_V0'))
    meta.append(dict(opaque_id=opaque,parent_bank=b,role=role,candidate_hypothesis_id=candidate,queries=rec))
dump(OUT/'receiver_plan.json',dict(receiver_plan_id='B4_FROZEN_50_V0',correlated_blocks=50,physical_stops=10,queries=plan))
dump(OUT/'evaluation_only/truth_mapping_AFTER_prediction_freeze.json',truth)
dump(OUT/'INPUT_LAYOUT.json',dict(reference_banks=meta[:4],compression_evaluation=meta[4:],
    infer_input_directories=['candidate_forecasts','observable_inputs'],infer_forbidden_directories=['evaluation_only'],
    original_parent_names_are_lineage_only=True,independent_new_realizations=0))
dump(OUT/'PARENT_INPUT_SHA256.json',inputs)
for s in ['verify_raw_receiver_queries.py','cache_native.py']:shutil.copyfile(PARENT/'RK0_NEW/source'/s,OUT/'source'/s)
handoff=WORK/'pro_handoff'
shutil.copyfile(handoff/'RK2_有限原型与单任务否证_待执行.md',OUT/'AUTHORIZED_RK2_TASK_zh.md')
shutil.copyfile(Path('D:/ZYC/UAV/.codex/attachments/f650220e-3ec5-4e6a-a1a5-9d2d95729951/已粘贴的文本.txt'),OUT/'USER_PRO_REQUEST_zh.txt')
dump(OUT/'STATIC_INPUT_PREPARATION.json',dict(status='PASS_STATIC_SEPARATED_INTERFACE_INPUTS_NO_FIT',
    parent_manifest_SHA256=sha(oldmanifest),bound_inputs=len(inputs),reference_banks=4,evaluation_banks=4,
    reference_cached_unique_frames=196,all_raw_selected_snapshots=392,main_blocks_per_bank=50,new_phi_calls=0,new_method_fits=0,
    observations_have_no_truth_source_or_particle_fields=True))
print(json.dumps(dict(status='PREPARED_NO_METHOD_FIT',bound_inputs=len(inputs),out=str(OUT)),ensure_ascii=False))
