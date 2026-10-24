from pathlib import Path,PureWindowsPath
import csv,hashlib,io,json,os,shutil,subprocess,sys,zipfile
B=Path(__file__).resolve().parent
REPO=Path('D:/ZYC/A-gas');F=REPO/'workspace/FROZEN_O24_1M2_SCREEN12_20261024'
ROOT=REPO/'_deliverables/V11_NATIVE_FUNCTION_EVIDENCE_20261024';assert not ROOT.exists();ROOT.mkdir()
def sha(x):return hashlib.sha256(x).hexdigest()
def cp(src,rel):
 p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
def text(rel,s):p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def jwrite(rel,x):text(rel,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
cp(B/'REPORT_FOR_PRO_zh.md','00_给Pro先读_实测裁决.md');cp(B/'PRO_NEXT_TASK_zh.md','01_直接发给Pro的推进任务.md')
for name in ['prepare_function_trial.py','run_function_trial_guest.py','audit_correct_case_controls.py','analyze_function_trial.py','package_for_pro.py','FUNCTION_TRIAL_SUMMARY.json','FUNCTION_TRIAL_EACH_STOP.csv','JOINT_SOURCE_EVENT_ENUMERATION.json']:
 cp(B/name,name)
for sub in ['function_trial','correct_case_controls']:
 shutil.copytree(B/sub,ROOT/sub)
shutil.copytree(F/'source_snapshot',ROOT/'native_source')
cp(F/'FROZEN_SOURCE_IDENTITY_128.json','NATIVE_SOURCE_IDENTITY_128.json');cp(F/'BASELINE_LOCK.json','FROZEN_BASELINE_LOCK_REFERENCE.json')
cp(REPO/'workspace/O24_PAPER_SCREEN12_20261024/EPISODE_RESULTS.csv','EPISODE_RESULTS.csv')
original=Path('C:/Users/50176/Downloads/PMFS_V11_research_package.zip');assert sha(original.read_bytes())=='ad6f8106898a272209a8ba155319abc156082905cbd449af7fcb6718138b7bf1'
cp(original,'original_inputs/PMFS_V11_research_package.zip')
for n in ['audit_e3_native_kernel.py.stdout.txt','audit_e3_native_kernel.py.stderr.txt','diagnose_e3_source_support.py.stdout.txt','diagnose_e3_source_support.py.stderr.txt']:
 cp(B/n,'v11_reproduction/'+n)
for n in ['E3_fixed_table_source_diagnostic.json','E3_fixed_table_candidate_scores.csv','E3_native_kernel_local_audit.json']:
 cp(B/'independent_reproduction/research_v11/evidence'/n,'v11_reproduction/'+n)

parent=Path('C:/Users/50176/Downloads/O24_SCREEN12_COMBINED_FINAL_FULL_EVIDENCE_20261024.zip');assert sha(parent.read_bytes())=='553ed6d0d3de761d2e2a13fff2b2fd1e205271bdce0e6bd75414fb1a24ac6ee3'
episodes=list(csv.DictReader((ROOT/'EPISODE_RESULTS.csv').open(encoding='utf-8-sig',newline='')));refs=[]
with zipfile.ZipFile(parent) as z:
 for ep in episodes:
  if ep['source_domain']!='LEGAL':continue
  filename=PureWindowsPath(ep['archive']).name;data=z.read('full_runs/'+filename);p=ROOT/'reference_runs'/filename;p.parent.mkdir(exist_ok=True);p.write_bytes(data)
  with zipfile.ZipFile(io.BytesIO(data)) as zz:assert zz.testzip() is None
  refs.append({'role':ep['role'],'path':p.relative_to(ROOT).as_posix(),'sha256':sha(data),'source_domain':'LEGAL','scope':'Original native ROS evidence, not a new run or independent gas-world claim'})
jwrite('REFERENCE_RUNS_IDENTITY.json',refs)
assert len(refs)==7
result=subprocess.run([sys.executable,str(F/'verify_frozen_baseline.py')],text=True,capture_output=True,check=True)
text('BASELINE_POST_RESEARCH_QA.txt',result.stdout)

text('function_trial/CMakeLists.txt','''cmake_minimum_required(VERSION 3.16)
project(v11_native_function_diagnostic LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
add_executable(native_function_runner native_function_runner.cpp ../native_source/src/gsl_server/algorithms/Common/Utils/NQAQuadtree.cpp)
target_include_directories(native_function_runner PRIVATE compatibility_headers ../native_source/src ../native_source/third_party/DDA/include ../native_source/third_party/xxHash/include)
target_compile_options(native_function_runner PRIVATE -O3 -DNDEBUG -include bits/stdc++.h)
# Ubuntu22.04 g++11; nlohmann-json and fmt headers required, no ROS runtime.
''')
text('verify_package.py','''from pathlib import Path
import hashlib,json,sys,zipfile,numpy as np
R=Path(__file__).resolve().parent
manifest=json.loads((R/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
for q in manifest['files']:
 p=(R/q['path']).resolve();assert p.is_relative_to(R)
 b=p.read_bytes();assert len(b)==q['bytes'] and hashlib.sha256(b).hexdigest()==q['sha256'],q['path']
src=json.loads((R/'NATIVE_SOURCE_IDENTITY_128.json').read_text())['files'];assert len(src)==128
for q in src:
 b=(R/'native_source'/q['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==q['sha256'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\\0'+b).hexdigest()==q['frozen_commit_blob']
for call in [589,660]:
 r=R/'function_trial';assert (r/f'expected_call_{call}.f32').read_bytes()==(r/f'results/replay_{call}.f32').read_bytes()
 q=json.loads((r/f'replay_call_{call}.json').read_text());o=json.loads((r/f'results/replay_{call}.json').read_text());assert abs(o['score']/float(q['candidate']['score'])-1)<1e-12
 for k in ['seed','state','uc','uh','gc','gh','index']:assert o['after'][k]==q['rng']['after'][k]
summary=json.loads((R/'FUNCTION_TRIAL_SUMMARY.json').read_text());assert summary['C_vs_D']['C_wins']==0
for arm in 'ABC':
 for rep in range(4):
  q=json.loads((R/f'function_trial/results/{arm}_{rep}.json').read_text());assert all(s['prediction']==0 for s in q['stops'][8:])
for ref in json.loads((R/'REFERENCE_RUNS_IDENTITY.json').read_text()):
 with zipfile.ZipFile(R/ref['path']) as z:assert z.testzip() is None
print(json.dumps({'status':'PASS_ALL_HASHES_FROZEN128_2_EXACT_REPLAYS_16_ARMS_7_REFERENCE_RUNS','files':len(manifest['files']),'new_ROS':0}))
''')
text('reproduce_saved_results.py','''"""Recompute saved diagnostics only; no compile, training, propagation, ROS or network."""
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile
R=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(R/'verify_package.py')],check=True)
with tempfile.TemporaryDirectory(prefix='v11_saved_replay_') as tmp:
 t=Path(tmp);shutil.copyfile(R/'analyze_function_trial.py',t/'analyze_function_trial.py');(t/'function_trial').mkdir();shutil.copyfile(R/'function_trial/scene.json',t/'function_trial/scene.json');shutil.copytree(R/'function_trial/results',t/'function_trial/results')
 subprocess.run([sys.executable,str(t/'analyze_function_trial.py')],check=True)
 new=json.loads((t/'FUNCTION_TRIAL_SUMMARY.json').read_text());old=json.loads((R/'FUNCTION_TRIAL_SUMMARY.json').read_text());assert new['C_vs_D']==old['C_vs_D']
 env=dict(os.environ,V11_NATIVE_REFERENCE_RUNS=str(R/'reference_runs'),V11_EPISODE_RESULTS=str(R/'EPISODE_RESULTS.csv'),V11_CONTROL_OUTPUT=str(t/'control_replay'))
 subprocess.run([sys.executable,str(R/'audit_correct_case_controls.py')],check=True,env=env)
 a=json.loads((t/'control_replay/ALL_SOURCE_LEGAL_CONTROL_SUMMARY.json').read_text());b=json.loads((R/'correct_case_controls/ALL_SOURCE_LEGAL_CONTROL_SUMMARY.json').read_text());assert len(a)==len(b)==7
 for x,y in zip(a,b):
  for k in ['role','positive_windows','positive_windows_true_region_zero','true_region_size']:assert x[k]==y[k]
  assert abs(x['native_MAP_over_true_score_ratio']/y['native_MAP_over_true_score_ratio']-1)<1e-10
print('PASS_SAVED_16_ARM_AND_SEVEN_NATIVE_CONTROL_RECOMPUTATION_NO_NEW_FORWARD')
''')
text('02_复算与边界说明.md','''# 复算入口

先读00裁决及01给Pro的任务。本包是V11的新原生函数证据增量，不是新算法成功包。

```text
python verify_package.py
python reproduce_saved_results.py
```

只需Python3和NumPy。默认只核验并复算保存的16次响应、2条原生重放及7条源域合法控制，不重新传播、不发ROS动作，不覆盖原结果。

`reference_runs/`中是7条原有原生ROS运行完整证据；B2域外诊断及技术中止分类仍在EPISODE_RESULTS.csv，未冒充合格推断失败。原始40项V11资料保留在original_inputs原ZIP。

`function_trial/`含预注册、16组响应、原生调用589/660保存的输入/输出、RNG状态和缓存、C++源码、编译成本及Linux x86-64独立诊断程序。输运/评分函数从冻结源码逐函数提取，RNG恢复适配及必要声明有明确身份；它不是O24闭环二进制。native_source/为128个冻结源码文件，均有Gitblob核对。

Linux可自行复编诊断器（Ubuntu22.04，g++11，nlohmann-json和fmt头文件）：

```text
cmake -S function_trial -B /tmp/v11_diagnostic_build -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/v11_diagnostic_build -j1
```

根目录prepare_function_trial.py和run_function_trial_guest.py保留本机实际准备/执行路径，用于来源审计，不应不改输出目录就重复执行。复用函数时每次必须新建输出目录、锁定随机初态和预算；不按成绩修改预注册。精确真源输入属于诊断Oracle，不能进入在线推断或选点。

16次结果不等于16个物理世界；未估计独立重复置信区间。未新增完整后验、MAP、Top-5%成绩或新ROS闭环。D/C数值是兼容评分比，不能写成经校准的Bayes因子。本轮没有定位增益。
''')
jwrite('DELTA_IDENTITY.json',{'identity':ROOT.name,'baseline_freeze_commit':'a339136931c4f285697c6e2c7804869646971ed3','original_V11_sha256':sha(original.read_bytes()),'new_mechanism_function_calls':16,'exact_original_replay_calls':2,'old_native_ROS_reference_runs':7,'new_ROS_calls':0,'new_GADEN_worlds':0,'training':0,'limits':'All current examples already seen/development. No qualified main innovation or new localization improvement claimed.','source_URLs_verified':['https://proceedings.mlr.press/v267/yang25af.html','https://arxiv.org/html/2502.11909v2','https://arxiv.org/html/2304.08879v3']})
files=[]
for p in sorted(ROOT.rglob('*')):
 if p.is_file():b=p.read_bytes();files.append({'path':p.relative_to(ROOT).as_posix(),'bytes':len(b),'sha256':sha(b)})
jwrite('MANIFEST_SHA256.json',{'identity':ROOT.name,'files':files})
check=subprocess.run([sys.executable,str(ROOT/'reproduce_saved_results.py')],check=True,text=True,capture_output=True)
(B/'DELTA_REPRODUCTION_QA.log').write_text(check.stdout,encoding='utf-8')
archive=Path('C:/Users/50176/Downloads/PMFS_V11_NATIVE_FUNCTION_EVIDENCE_20261024.zip');assert not archive.exists()
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(ROOT.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(ROOT).as_posix(),compress_type=zipfile.ZIP_STORED if p.suffix=='.zip' else zipfile.ZIP_DEFLATED)
qa=Path('C:/Users/50176/Downloads/_V11_NATIVE_FRESH_QA_20261024');assert not qa.exists();qa.mkdir()
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;z.extractall(qa)
fresh=subprocess.run([sys.executable,str(qa/'reproduce_saved_results.py')],check=True,text=True,capture_output=True)
receipt={'status':'PASS_FRESH_UNZIP_HASH_AND_SCIENTIFIC_RECOMPUTATION','archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive.read_bytes()),'files':len(files)+1,'new_function_calls':16,'exact_native_replays':2,'old_source_legal_runs':7,'new_ROS':0,'new_worlds':0,'main_innovation_status':'NOT_ESTABLISHED','fresh_QA_stdout':fresh.stdout}
(B/'DELTA_DELIVERY_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');archive.with_suffix('.zip.sha256').write_text(receipt['sha256']+'  '+archive.name+'\n',encoding='ascii')
print(json.dumps({k:v for k,v in receipt.items() if k!='fresh_QA_stdout'},ensure_ascii=False,indent=2))
