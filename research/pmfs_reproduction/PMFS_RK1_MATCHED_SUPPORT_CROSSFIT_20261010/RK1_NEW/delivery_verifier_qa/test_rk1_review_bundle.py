"""Software QA in a new work-only copy; never alters original scientific files."""
import sys
sys.dont_write_bytecode = True
import hashlib, importlib.util, json, shutil, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('rk1_master_qa', HERE/'verify_rk1_review_bundle.py')
v = importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
OLD = v.absolute_path(HERE.parent.parent/'outputs/PMFS_RK0_PRO_REVIEW_BUNDLE_20261010_V2', strict=True)
SANDBOX = v.absolute_path(HERE/('verifier_qa_fixture_'+time.strftime('%Y%m%d_%H%M%S')), strict=False)
assert not SANDBOX.exists()
shutil.copytree(OLD,SANDBOX)
(SANDBOX/'SHA256SUMS.json').rename(SANDBOX/v.RK0_MANIFEST)
(SANDBOX/'RK1_NEW').mkdir()
(SANDBOX/'RK1_NEW/verify_rk1.py').write_text('def verify(rk1,parent):\n    assert rk1.name == "RK1_NEW" and (parent/"RK0_NEW").is_dir()\n    return {"status":"PASS_SYNTHETIC_SOFTWARE_DISPATCH_ONLY"},{"dummy":[]}\n',encoding='utf-8')
(SANDBOX/'START_HERE_RK1_zh.md').write_text('Software QA fixture, not a science run.\n',encoding='utf-8')
long_member=SANDBOX/'RK1_NEW'/('long_component_'+('x'*95))/('second_component_'+('y'*95))/'long_path_evidence.txt'
long_member.parent.mkdir(parents=True)
long_member.write_text('long path check\n',encoding='utf-8')
checks=[]

def record(name, outcome, **details):
    checks.append(dict(check=name,outcome=outcome,**details))

def manifest():
    data={name:v.sha(p) for name,p in sorted(v.inventory(SANDBOX).items()) if name!='SHA256SUMS.json'}
    (SANDBOX/'SHA256SUMS.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return data

def expect_failure(name,call,needle=None):
    try:call()
    except Exception as e:
        if needle is not None:assert needle in str(e),(name,str(e))
        record(name,'PASS_EXPECTED_REJECTION',error_type=type(e).__name__,error=str(e))
        return
    raise AssertionError('QA should reject: '+name)

manifest()
baseline=v.verify_bundle(SANDBOX)
assert baseline['integrity']['frozen_RK0']['declared_members']==1848
assert len(str(long_member))>260
record('complete_new_manifest_frozen_1848_and_long_path','PASS',main_members=baseline['integrity']['main_members_checked'],long_path_characters=len(str(long_member)))
dispatch=v.verify_bundle(SANDBOX,deep=True)
assert dispatch['independent_RK1']['result']['status']=='PASS_SYNTHETIC_SOFTWARE_DISPATCH_ONLY'
record('new_deep_function_dispatch_and_post_hash','PASS_SYNTHETIC_SOFTWARE_ONLY')

extra=SANDBOX/'RK1_NEW/undeclared.txt';extra.write_text('unexpected\n',encoding='utf-8')
expect_failure('undeclared_file',lambda:v.verify_bundle(SANDBOX),'coverage mismatch')
extra.unlink()

original=SANDBOX/'FIRST_READ_FOR_PRO_zh.md';backup=original.read_bytes()
original.write_bytes(backup+b'\nTAMPER_QA\n');manifest()
expect_failure('legacy_tamper_even_if_new_manifest_rehashed',lambda:v.verify_bundle(SANDBOX),'RK0_ROOT_MANIFEST_FROZEN.json')
original.write_bytes(backup);manifest()

oldmanifest=SANDBOX/v.RK0_MANIFEST;backup=oldmanifest.read_bytes()
oldmanifest.write_bytes(backup+b'\n');manifest()
expect_failure('renamed_old_manifest_byte_change',lambda:v.verify_bundle(SANDBOX),'Frozen RK0 root manifest bytes changed')
oldmanifest.write_bytes(backup);manifest()

main=SANDBOX/'SHA256SUMS.json';backup=main.read_bytes()
data=json.loads(backup);data['../outside.txt']='0'*64
main.write_text(json.dumps(data),encoding='utf-8')
expect_failure('manifest_path_traversal',lambda:v.verify_bundle(SANDBOX),'traversing')
main.write_bytes(backup)

main.write_text('{"same":"'+('0'*64)+'","same":"'+('1'*64)+'"}',encoding='utf-8')
expect_failure('duplicate_JSON_manifest_keys',lambda:v.verify_bundle(SANDBOX),'Duplicate JSON key')
main.write_bytes(backup)

data=json.loads(backup);data['rk1_new/VERIFY_RK1.PY']=data['RK1_NEW/verify_rk1.py']
main.write_text(json.dumps(data),encoding='utf-8')
expect_failure('case_alias_manifest_paths',lambda:v.verify_bundle(SANDBOX),'Case-alias')
main.write_bytes(backup)

for label,p in [('normal',SANDBOX/'inside_result.json'),('dotdot',SANDBOX/'RK1_NEW/../inside_result.json'),('extended',Path(str(SANDBOX/'inside_extended.json')))]:
    expect_failure('output_inside_'+label,lambda p=p:v.output_destination(p,SANDBOX),'outside bundle')
outside=v.absolute_path(HERE/'already_existing_output_qa.json',strict=False)
outside.write_text('{}\n',encoding='utf-8')
expect_failure('existing_external_output_no_overwrite',lambda:v.output_destination(outside,SANDBOX),'new file')
expect_failure('PRO_scratch_inside',lambda:v.verify_bundle(SANDBOX,pro_scalar_scratch=SANDBOX/'scratch'),'outside bundle')
expect_failure('existing_PRO_scratch_no_overwrite',lambda:v.verify_bundle(SANDBOX,pro_scalar_scratch=outside),'new')

saved=v.deep_rk1
def tamper_after_integrity(root):
    (root/'START_HERE_RK1_zh.md').write_text('changed while deep checker ran',encoding='utf-8')
    return {'status':'SYNTHETIC_TEST'}
front=(SANDBOX/'START_HERE_RK1_zh.md').read_bytes()
v.deep_rk1=tamper_after_integrity
expect_failure('post_deep_package_modification',lambda:v.verify_bundle(SANDBOX,deep=True),'SHA256 mismatch')
v.deep_rk1=saved
(SANDBOX/'START_HERE_RK1_zh.md').write_bytes(front)
final=v.verify_bundle(SANDBOX)
assert final['integrity']==baseline['integrity']
assert v.sha(OLD/'SHA256SUMS.json')==v.RK0_MANIFEST_SHA256
assert not any(p.name=='__pycache__' for p in SANDBOX.rglob('*'))
record('original_manifest_preserved_and_copy_restored_no_bytecode','PASS')
result=dict(status='PASS_RK1_MASTER_VERIFIER_SOFTWARE_QA',check_count=len(checks),checks=checks,fixture=str(SANDBOX),fixture_science_not_executed=True,original_package_modified=False,new_physics=0)
out=HERE/'RK1_MASTER_VERIFIER_QA.json'
assert not out.exists()
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
