"""Software safety QA only; does not execute physical or RK0 experiments."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,importlib.util,json,shutil,subprocess
W=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('qa_review_verifier',W/'verify_review_bundle.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
Q=W/'verify_review_bundle_qa_v2';assert not Q.exists();Q.mkdir()
def hash_bytes(b):return hashlib.sha256(b).hexdigest()
def write_json(p,data):p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def make(name):
 root=Q/name;root.mkdir()
 for directory in v.REQUIRED_DIRECTORIES:(root/directory).mkdir()
 (root/'PARENT_M2M3_FROZEN/M2_FROZEN').mkdir();(root/'PARENT_M2M3_FROZEN/M2_FROZEN/data.txt').write_text('unchanged raw fixture\n',encoding='utf-8')
 (root/'PRO_REVIEW/readme.txt').write_text('fixture only\n',encoding='utf-8')
 (root/'RK0_NEW/verify_rk0_independent.py').write_text("def verify(root,m2):\n print('independent fixture call only')\n return {'status':'PASS_FIXTURE','new_experiments':0},{'fixture_table':[{'one':1}]}\n",encoding='utf-8')
 write_json(root/'PRO_REVIEW/PRO_REVIEW_SHA256SUMS.json',{'readme.txt':v.sha(root/'PRO_REVIEW/readme.txt')})
 shutil.copy2(W/'verify_review_bundle.py',root/'verify_review_bundle.py')
 (root/'PRO_REVIEW/handoff/new_diagnostics').mkdir(parents=True)
 for n in ('SAME_BANK_SAME_SCORER_MARGINS.csv','READOUT_MASK_DENOMINATOR_FACTORIAL.csv'):(root/'PRO_REVIEW/handoff/new_diagnostics'/n).write_text('a,b\n1,2\n',encoding='utf-8')
 (root/'PRO_REVIEW/independent_scalar_readout_check.py').write_text("def run(parent,out):\n from pathlib import Path\n assert (out.parent/'handoff/new_diagnostics/SAME_BANK_SAME_SCORER_MARGINS.csv').is_file()\n out.mkdir(parents=True,exist_ok=False)\n (out/'only_arithmetic.json').write_text('{\"status\":\"PASS_FIXTURE\"}')\n return {'status':'PASS_FIXTURE','physics':0}\n",encoding='utf-8')
 refresh(root);return root
def refresh(root):write_json(root/'SHA256SUMS.json',{p.relative_to(root).as_posix():v.sha(p) for p in sorted(root.rglob('*')) if p.is_file() and p!=root/'SHA256SUMS.json'})
tests=[]
root=make('valid_bundle');r=v.verify_bundle(root);assert r['status']=='PASS_SELF_CONTAINED_REVIEW_BUNDLE';tests.append('valid main coverage and nested digest PASS')
r=v.verify_bundle(root,True);assert r['integrity_after_deep'].startswith('PASS') and r['independent_RK0']['table_row_counts']=={'fixture_table':1};assert not list(root.rglob('__pycache__'));tests.append('deep only independent function, stdout captured, no bytecode, unchanged package PASS')
scratch=Q/'new_external_pro_scratch';r=v.verify_bundle(root,True,scratch);assert r['independent_PRO_scalar']['result']['status']=='PASS_FIXTURE' and (scratch/'independent_recompute/only_arithmetic.json').exists() and not list(root.rglob('__pycache__'));tests.append('deep PRO arithmetic outside scratch, canonical CSV copy, package unchanged PASS')
def reject(label,action):
 try:action()
 except (ValueError,AssertionError,FileNotFoundError,FileExistsError):tests.append(label+' rejected PASS')
 else:raise AssertionError('expected rejection: '+label)
reject('inside-bundle PRO scratch',lambda:v.deep_pro_scalar(root,root/'bad_scratch'))
reject('existing PRO scratch',lambda:v.deep_pro_scalar(root,scratch))
reject('inside-bundle output',lambda:v.output_destination(root/'result.json',root))
outside=Q/'new_external_result.json';p=subprocess.run([sys.executable,'-B',str(W/'verify_review_bundle.py'),'--package',str(root),'--out',str(outside)],capture_output=True,text=True);assert p.returncode==0 and json.loads(p.stdout)['status']=='PASS_SELF_CONTAINED_REVIEW_BUNDLE' and outside.exists();tests.append('CLI exit0 JSON and explicit external output PASS')
reject('overwrite existing external output',lambda:v.output_destination(outside,root))
for label,name in [('parent traversal','../outside.txt'),('Windows drive','C:/outside.txt'),('UNC','\\\\host\\share\\outside.txt'),('dot segment','PRO_REVIEW/./readme.txt'),('trailing dot','PRO_REVIEW/readme.txt.')]:reject(label,lambda name=name:v.normalized_relative(name))
bad=make('extra_file');(bad/'unexpected.txt').write_text('extra');reject('undeclared actual member',lambda:v.verify_bundle(bad))
bad=make('nested_bad');write_json(bad/'PRO_REVIEW/PRO_REVIEW_SHA256SUMS.json',{'readme.txt':'0'*64});refresh(bad);reject('stale nested manifest even when main matches',lambda:v.verify_bundle(bad))
bad=make('duplicate_normalized');data=json.loads((bad/'SHA256SUMS.json').read_text());data['PRO_REVIEW\\readme.txt']=data['PRO_REVIEW/readme.txt'];write_json(bad/'SHA256SUMS.json',data);reject('duplicate slash normalized path',lambda:v.verify_bundle(bad))
bad=make('missing_hash_member');data=json.loads((bad/'SHA256SUMS.json').read_text());del data['verify_review_bundle.py'];write_json(bad/'SHA256SUMS.json',data);reject('main verifier excluded incorrectly',lambda:v.verify_bundle(bad))
bad=make('duplicate_json_key');(bad/'SHA256SUMS.json').write_text('{"PRO_REVIEW/readme.txt":"'+'0'*64+'","PRO_REVIEW/readme.txt":"'+'0'*64+'"}');reject('duplicate JSON key',lambda:v.verify_bundle(bad))
bad=make('self_manifest');data=json.loads((bad/'SHA256SUMS.json').read_text());data['SHA256SUMS.json']='0'*64;write_json(bad/'SHA256SUMS.json',data);reject('main manifest self inclusion',lambda:v.verify_bundle(bad))
result=dict(status='PASS_REVIEW_BUNDLE_VERIFIER_SOFTWARE_QA',test_count=len(tests),tests=tests,physics_calls=0,cache_producer_calls=0,actual_RK0_deep_audit_executed=False,deep_QA_uses_explicit_small_fixture_only=True,source_SHA256=v.sha(W/'verify_review_bundle.py'))
write_json(W/'REVIEW_BUNDLE_VERIFIER_QA_V2.json',result);print(json.dumps(result,indent=2))
