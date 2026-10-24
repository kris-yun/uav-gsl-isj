"""Freeze existing O24 code/config/evidence. No compilation, ROS or new worlds."""
from pathlib import Path
import csv,hashlib,io,json,os,re,shutil,stat,subprocess,sys,tempfile,zipfile
from datetime import datetime,timezone

BASE=Path(__file__).resolve().parent
REPO=BASE.parent.parent
FREEZE=REPO/'workspace/FROZEN_O24_1M2_SCREEN12_20261024'
METHOD=REPO/'workspace/METHOD_COMPARISON_O24_1M2_20261024'
DOWNLOADS=Path('C:/Users/50176/Downloads')
ID='PMFS-O24-PORT-GMRF-PAPERSTOP1M2-SCREEN12-20261024'
ELF='e63fadfdb5b4b20ea6936f38c3a1d5edf0d1e9e236ed8d78a4846b009aefed78'
assert not FREEZE.exists() and not METHOD.exists(),'Refuse overwrite'
FREEZE.mkdir();METHOD.mkdir()
def sha(b):return hashlib.sha256(b).hexdigest()
def put(rel,value):
 p=FREEZE/rel;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def copy(src,rel):
 p=FREEZE/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
 assert sha(Path(src).read_bytes())==sha(p.read_bytes())

sources=[('PMFS_O24_SOURCE_LAUNCH_20261024.zip','9ecec278724279a304288fc0174f2c41ae7a9615eb22f5ef43a9c374e6555b19'),('O24_SCREEN12_COMBINED_FINAL_FULL_EVIDENCE_20261024.zip','553ed6d0d3de761d2e2a13fff2b2fd1e205271bdce0e6bd75414fb1a24ac6ee3')]
for name,digest in sources:
 p=DOWNLOADS/name;assert sha(p.read_bytes())==digest
 copy(p,'payload/'+name)

with zipfile.ZipFile(FREEZE/'payload'/sources[0][0]) as z:
 for n in z.namelist():
  target=None
  if n.startswith('frozen_o24/source_runtime/'):target='source_snapshot/'+n.removeprefix('frozen_o24/source_runtime/')
  elif n=='frozen_o24/binaries/gsl_actionserver_node':target='binaries/gsl_actionserver_node'
  elif n=='frozen_o24/provenance/FROZEN_SOURCE_IDENTITY_128.json':target='FROZEN_SOURCE_IDENTITY_128.json'
  elif n.startswith(('launch_cases/','environment_overlay/','active_protocol/')):target='actual_configuration/'+n
  elif n in ['CASE_LAUNCH_INDEX.json','PACKAGE_IDENTITY.json']:target='code_package_identity/'+n
  if target:
   p=FREEZE/target;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
 index=json.loads(z.read('CASE_LAUNCH_INDEX.json'))
 code_identity=json.loads(z.read('PACKAGE_IDENTITY.json'))
for n in ['EPISODE_RESULTS.csv','SCENARIO_SUMMARY.csv','中文筛查报告.md','PORTABLE_DELIVERY_QA.json','ACTUAL_SOURCE_LAUNCH_DELIVERY_RECEIPT.json','GITHUB_DELIVERY_RECEIPT.json']:
 copy(BASE/n,'evidence_index/'+n)
copy(__file__,'freeze_current_baseline.py')

remote='''import hashlib,json,os,time
from pathlib import Path
p=Path('/home/zyc/ros2_ws/pmfs_o24_port_gmrf_20261018/gsl_actionserver_node')
found=[]
for q in Path('/proc').iterdir():
 if not q.name.isdigit():continue
 try:
  args=(q/'cmdline').read_bytes().split(b'\\0')
  first=args[0].decode(errors='replace') if args else ''
  if Path(first).name in ['gsl_actionserver_node','public_clock_player']:
   env=(q/'environ').read_bytes().split(b'\\0')
   domain=next((x.decode() for x in env if x.startswith(b'ROS_DOMAIN_ID=')),None)
   found.append({'pid':int(q.name),'executable':first,'domain':domain})
 except (PermissionError,FileNotFoundError,ProcessLookupError):pass
print(json.dumps({'UTC_unix':time.time(),'ELF_path':str(p),'ELF_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'visible_matching_processes':found,'scope':'Current-user readable /proc; no processes stopped or started'}))
'''
remote_result=subprocess.run(['ssh','-i','C:/Users/50176/.ssh/id_ed25519_vm','-o','BatchMode=yes','-o','ConnectTimeout=8','zyc@192.168.111.128','python3','-'],input=remote,text=True,capture_output=True,check=True)
vm=json.loads(remote_result.stdout)
assert vm['ELF_sha256']==ELF and not vm['visible_matching_processes'],vm
put('LIVE_VM_SEAL_CHECK.json',vm)

episodes=list(csv.DictReader((FREEZE/'evidence_index/EPISODE_RESULTS.csv').open(encoding='utf-8-sig',newline='')))
assert len(episodes)==12
roles=[e['role'] for e in episodes]
legal=[e['role'] for e in episodes if e['source_domain']=='LEGAL']
diagnostic=[e['role'] for e in episodes if e['source_domain']!='LEGAL']
rows=[]
for row in index:
 role=row['role'];prefix='actual_configuration/launch_cases/'+role
 gate=json.loads((FREEZE/prefix/'runtime/BASELINE_PARAMETER_GATE.json').read_text(encoding='utf-8'))['checked']
 assert gate['convergence_thr']==1.0 and gate['sourceDiscriminationPower']==0.2 and gate['useWindGroundTruth'] is False
 rows.append({'role':role,'case':row['scenario_configuration'],'configuration_prefix':prefix,'source_domain':next(e['source_domain'] for e in episodes if e['role']==role),'GSL_parameters':gate,'navigation_map_sha256':sha((FREEZE/prefix/'runtime/navigation_map.s8').read_bytes()),'physical_time_csv_sha256':sha((FREEZE/prefix/'PHYSICAL_FRAME_TIME.csv').read_bytes()),'native_ELF_sha256':ELF,'full_original_archive':row['full_original_archive']})
put('FROZEN_CASES.json',rows)
lock={
 'freeze_identity':ID,'frozen_UTC':datetime.now(timezone.utc).isoformat(),
 'source_commit':'631145657461c41840f6844f118de57d1e747ea4','public_author_snapshot':'a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533','evidence_commit':'120bb2e833bfc6aa96a356101203570b476b6b9f','ELF_sha256':ELF,
 'source_file_count':128,'normal_stop':{'parameter':'convergence_thr','value':1.0,'unit':'m2','definition':'sum_s p(s)*((x_s-E[x])^2+(y_s-E[y])^2), covariance trace','comparison':'strictly less than','not_localization_error_threshold':True,'source_function':'PMFS_utils.cpp::varianceSourcePosition and checkSourceFound'},
 'baseline_core':{'sourceDiscriminationPower':0.2,'USE_GADEN':False,'useWindGroundTruth':False,'wind_information':'local measurements/GMRF only','noiseSTDev_by_case':{'A2':0.5,'B2':0.5,'C3':0.25,'D4':0.5,'E3':0.5}},
 'time_protocol':{'BasicSim_speed':1.0,'use_sim_time':True,'gas_world_looping':False,'maxSearchTime':1e9,'fixed_300_or_600_normal_stop':False,'data_exhaustion':'censored not native declaration','safety_caps':'preserve preregistered1100s pergoal and1250s perattempt separately from normal stop'},
 'RNG':'Original frozen RNG retained; actual states recorded; no prescribed-independent-seed or bitwise-replay claim',
 'roles':roles,'legal_source_roles':legal,'excluded_source_diagnostic_roles':diagnostic,
 'observed_outcome_classes':{'native_declarations':10,'recording_exhaustion_censor':1,'technical_isolation_abort':1},
 'paper_scope':'Paper 1m2 declaration threshold adopted with frozen O24 scoring. Not a claim that every parameter, author experiment commit, original clock, or30-repeat performance has been reproduced.',
 'source_config_archive_sha256':sources[0][1],'full_evidence_archive_sha256':sources[1][1],
 'historical_1p5_protocol':'Retained inside original code archive only; not active for this frozen comparison identity',
 'modification_policy':'Do not edit this freeze. New user methods and any future protocol changes require separate identities and output roots.',
 'new_builds':0,'new_ROS_runs':0,'new_worlds':0,
}
put('BASELINE_LOCK.json',lock)
put('AGENTS.md',f'''# Frozen baseline: {ID}\n\nThis directory is an archival reference. Never edit source, ELF, actual configuration, archived evidence, threshold, maps or historical outcomes in place. Do not launch into an old case output path. Verification is read-only; failure must reject use, not auto-repair. New methods belong in ../{METHOD.name}/. This task does not authorize new simulations or ROS runs.\n''')
put('.gitignore','payload/\nbinaries/\n__pycache__/\n')
put('00_冻结说明_zh.md',f'''# 当前正式对比基线已冻结\n\n唯一身份：`{ID}`。\n\n源码提交`{lock['source_commit']}`，实际ELF SHA256为`{ELF}`。本目录保留完整128文件冻结PMFS源码、实际ELF、12槽位实际配置与本轮完整证据原包。自定义依赖、编译记录和运行接线位于payload中的源码启动包。\n\n当前声明门是**后验二维位置总方差小于1 m²**（Var(x)+Var(y)），采用论文声明门。不是定位误差小于1米。O24评分仍为D=0.2，局地风/GMRF；C3噪声0.25、其余0.5。1倍物理时钟、已有气体数据不循环，数据耗尽和技术上限单列。本次不修改源码、不重编译、不新增运行。\n\n这叫“冻结O24＋论文1m²声明协议”。并未宣称作者全部实验条件或30次统计性能已复现。旧1.5m²配置只作为历史材料保留，不参与本身份的正式比较。\n\n12槽位为10次原生声明、1次数据耗尽、1次技术隔离中止。原生success表示声明收敛，不能等同正确定位。B2源被候选域排除，单列诊断；E3为合法源条件下的一次错误声明，不升级为多世界普遍失效。全部正反例、失败与RNG限制保留。\n\n## 隔离\n\n- `source_snapshot/`、`binaries/`、`actual_configuration/`和`payload/`是本次只读封存。\n- 新方法放在`../{METHOD.name}/`，代码和输出不得写回本目录或旧cases目录。\n- 基线原批次使用ROS_DOMAIN_ID=228；后续方法建议229，运行前重新检查占用且顺序运行，不以编号代替隔离验收。当前封存时原生PMFS和播放器均未运行。\n- 所有封存文件设置Windows只读属性并绑定SHA；属性不能阻止管理员写入，因此每次使用前必须运行核验器。\n\n## 核验\n\n`python verify_frozen_baseline.py`只读检查全部文件、源码Git blob、ELF、12份参数与候选地图绑定，不发ROS动作。可加`--live-elf <待运行ELF>`核对运行程序。`--method-manifest <新方法合同.json>`在方法未提交、输入协议不一致或身份错误时拒绝进入对比。\n\n气体世界与ROS系统安装仍为外部资产，完整路径、帧SHA和依赖版本在源码包及证据包中；本次不会再复制巨大世界。原历史目录、源码、运行配置、ELF和证据全部保留。\n''')

guard='''"""Read-only frozen baseline guard. Never builds, repairs or launches ROS."""
from pathlib import Path
import argparse,hashlib,json,re,sys
def check(root, live_elf=None, method_manifest=None):
 root=Path(root).resolve()
 manifest=json.loads((root/'FREEZE_MANIFEST_SHA256.json').read_text(encoding='utf-8'))
 declared={r['path'] for r in manifest['files']}
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='FREEZE_MANIFEST_SHA256.json' and '__pycache__' not in p.parts}
 assert declared==actual,{'missing':list(declared-actual),'unexpected':list(actual-declared)}
 for row in manifest['files']:
  p=(root/row['path']).resolve();assert p.is_relative_to(root)
  b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
 lock=json.loads((root/'BASELINE_LOCK.json').read_text(encoding='utf-8'))
 assert lock['normal_stop']['value']==1.0 and lock['normal_stop']['unit']=='m2'
 src=json.loads((root/'FROZEN_SOURCE_IDENTITY_128.json').read_text(encoding='utf-8'))['files']
 assert len(src)==128
 for f in src:
  b=(root/'source_snapshot'/f['path']).read_bytes()
  assert hashlib.sha256(b).hexdigest()==f['sha256']
  assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\\0'+b).hexdigest()==f['frozen_commit_blob']
 assert hashlib.sha256((root/'binaries/gsl_actionserver_node').read_bytes()).hexdigest()==lock['ELF_sha256']
 for c in json.loads((root/'FROZEN_CASES.json').read_text(encoding='utf-8')):
  p=json.loads((root/c['configuration_prefix']/'runtime/BASELINE_PARAMETER_GATE.json').read_text(encoding='utf-8'))['checked']
  assert p==c['GSL_parameters']
  assert p['convergence_thr']==1.0 and p['sourceDiscriminationPower']==0.2 and p['useWindGroundTruth'] is False
  assert p['noiseSTDev']==lock['baseline_core']['noiseSTDev_by_case'][c['case']]
 if live_elf:
  assert hashlib.sha256(Path(live_elf).read_bytes()).hexdigest()==lock['ELF_sha256'],'LIVE_ELF_MISMATCH'
 if method_manifest:
  m=json.loads(Path(method_manifest).read_text(encoding='utf-8'))
  assert m['baseline_freeze_identity']==lock['freeze_identity'],'BASELINE_IDENTITY_MISMATCH'
  assert m['baseline_lock_sha256']==hashlib.sha256((root/'BASELINE_LOCK.json').read_bytes()).hexdigest(),'BASELINE_LOCK_MISMATCH'
  assert m['status']=='PREREGISTERED_READY' and re.fullmatch('[0-9a-f]{64}',m.get('method_code_sha256','')),'METHOD_NOT_SUBMITTED_AND_FROZEN'
  assert m['shared_information_and_budget_contract_accepted'] is True,'SHARED_CONTRACT_NOT_ACCEPTED'
  assert m['normal_stop_variance_m2']==1.0,'STOP_PROTOCOL_MISMATCH'
 return {'status':'PASS_FROZEN_SOURCE_CONFIG_ELF_EVIDENCE','freeze_identity':lock['freeze_identity'],'files':len(declared),'source_files':128,'new_ROS':0}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(Path(__file__).resolve().parent));a.add_argument('--live-elf');a.add_argument('--method-manifest');args=a.parse_args()
 try:print(json.dumps(check(args.root,args.live_elf,args.method_manifest),ensure_ascii=False))
 except (AssertionError,KeyError,FileNotFoundError,ValueError) as e:print('REJECT_FROZEN_BASELINE_OR_COMPARISON: '+str(e),file=sys.stderr);sys.exit(2)
'''
put('verify_frozen_baseline.py',guard)
method_contract={'baseline_freeze_identity':ID,'baseline_lock_sha256':sha((FREEZE/'BASELINE_LOCK.json').read_bytes()),'baseline_path':str(FREEZE),'status':'AWAITING_USER_METHOD','method_code_sha256':None,'normal_stop_variance_m2':1.0,'shared_information_and_budget_contract_accepted':False,'shared_requirements':['Same existing world hashes and source/start conditions for each matched task','Same full legal source support, maps, sensors, local wind access, physical timeline and original observation rules; explicit method changes documented separately','No ground-truth source or future/full-field wind input to deployable inference or planning','Same declared motion, measurement and compute budget; all fitting and prescreening cost recorded','Closed loop vs fixed-history replay reported separately; method trajectories may differ in actual closed loop','No retuning against observed successes/failures; existing SCREEN12 already seen is development evidence, not unseen confirmation','B2 excluded-source diagnostics, technical abort and recording exhaustion kept separate','Original O24 RNG limits preserved; no prescribed-independent-seed or exact paired random-stream claim'],'method_specific_changes':[],'run_output_root':str(METHOD/'outputs'),'baseline_historical_domain':228,'future_method_suggested_domain':229,'run_sequentially':True,'check_domain_ownership_before_every_run':True,'new_ROS_authorized_by_this_freeze':False}
(METHOD/'METHOD_SUBMISSION_TEMPLATE.json').write_text(json.dumps(method_contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(METHOD/'README_新方法隔离入口.md').write_text('新方法待用户提供，尚未实现或运行。代码放method_source/、新结果放outputs/；不得修改冻结基线或覆盖旧case。先填写METHOD_SUBMISSION_TEMPLATE.json，冻结代码SHA和共同预算，再运行基线核验器的--method-manifest。现有SCREEN12为已见开发数据，不称新的盲测。\n',encoding='utf-8')
(METHOD/'method_source').mkdir();(METHOD/'outputs').mkdir()
put('FUTURE_COMPARISON_CONTRACT_TEMPLATE.json',method_contract)

files=[]
for p in sorted(FREEZE.rglob('*')):
 if p.is_file():b=p.read_bytes();files.append({'path':p.relative_to(FREEZE).as_posix(),'bytes':len(b),'sha256':sha(b)})
put('FREEZE_MANIFEST_SHA256.json',{'freeze_identity':ID,'scope':'All frozen files except this self-referential manifest; no method output in freeze','files':files})
verify=subprocess.run([sys.executable,str(FREEZE/'verify_frozen_baseline.py')],check=True,text=True,capture_output=True)

# Negative controls only touch our temporary metadata copies, never the freeze.
testdir=BASE/'freeze_negative_controls';testdir.mkdir()
bad=dict(method_contract);bad.update(status='PREREGISTERED_READY',method_code_sha256='1'*64,shared_information_and_budget_contract_accepted=True,normal_stop_variance_m2=1.5)
badpath=testdir/'WRONG_STOP_1P5.json';badpath.write_text(json.dumps(bad),encoding='utf-8')
neg=subprocess.run([sys.executable,str(FREEZE/'verify_frozen_baseline.py'),'--method-manifest',str(badpath)],text=True,capture_output=True)
assert neg.returncode==2 and 'STOP_PROTOCOL_MISMATCH' in neg.stderr
pending=subprocess.run([sys.executable,str(FREEZE/'verify_frozen_baseline.py'),'--method-manifest',str(METHOD/'METHOD_SUBMISSION_TEMPLATE.json')],text=True,capture_output=True)
assert pending.returncode==2 and 'METHOD_NOT_SUBMITTED_AND_FROZEN' in pending.stderr

# Independent Git index: do not check out, stage unrelated work, or modify the active index.
index_file=BASE/'freeze_git_index';assert not index_file.exists()
env=dict(os.environ,GIT_INDEX_FILE=str(index_file))
def git(*args,**kw):return subprocess.run(['git',*args],cwd=REPO,env=env,text=True,capture_output=True,check=True,**kw).stdout.strip()
parent='120bb2e833bfc6aa96a356101203570b476b6b9f'
git('read-tree',parent)
tracked=[str(p.relative_to(REPO)).replace('\\','/') for p in FREEZE.rglob('*') if p.is_file() and 'payload' not in p.relative_to(FREEZE).parts and 'binaries' not in p.relative_to(FREEZE).parts]
pathspec_file=BASE/'freeze_git_pathspec.nul'
pathspec_file.write_bytes(b'\0'.join(p.encode('utf-8') for p in tracked)+b'\0')
git('add','-f','--pathspec-from-file='+str(pathspec_file),'--pathspec-file-nul')
tree=git('write-tree')
commit=git('commit-tree',tree,'-p',parent,input='Freeze O24 actual source/config and SCREEN12 evidence under 1m2 declaration protocol\n')
branch='research/o24-1m2-frozen-20261024';tag='freeze/o24-1m2-screen12-20261024'
git('update-ref','refs/heads/'+branch,commit,'0'*40)
git('update-ref','refs/tags/'+tag,commit,'0'*40)
git_receipt={'status':'LOCAL_FREEZE_COMMIT_AND_TAG_NO_CHECKOUT','commit':commit,'branch':branch,'tag':tag,'parent_evidence_commit':parent,'active_worktree_and_index_unchanged':True,'payload_binary_archive_identity_recorded_not_git_uploaded':True}
(BASE/'FROZEN_1M2_GIT_RECEIPT.json').write_text(json.dumps(git_receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Set the self-created seal files read-only; hashes remain the actual integrity gate.
for p in FREEZE.rglob('*'):
 if p.is_file():os.chmod(p,stat.S_IREAD)
archive=DOWNLOADS/'O24_1M2_SCREEN12_FROZEN_BASELINE_20261024.zip';assert not archive.exists()
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(FREEZE.rglob('*')):
  if p.is_file():z.write(p,'baseline/'+p.relative_to(FREEZE).as_posix(),compress_type=zipfile.ZIP_STORED if p.suffix=='.zip' else zipfile.ZIP_DEFLATED)
 z.writestr('GIT_FREEZE_RECEIPT.json',json.dumps(git_receipt,ensure_ascii=False,indent=2))
 z.writestr('VERIFY_RECEIPT.txt',verify.stdout)
qa=BASE/'freeze_portable_qa';assert not qa.exists();qa.mkdir()
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None;z.extractall(qa)
fresh=subprocess.run([sys.executable,str(qa/'baseline/verify_frozen_baseline.py')],text=True,capture_output=True,check=True)
receipt={'status':'FROZEN_AND_ISOLATED_PASS','freeze_identity':ID,'canonical_baseline':str(FREEZE),'separate_method_workspace':str(METHOD),'archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive.read_bytes()),'manifest_files':len(files),'freeze_git':git_receipt,'verify_stdout':verify.stdout,'fresh_unzip_verify_stdout':fresh.stdout,'wrong_1p5_stop_rejected':True,'unsubmitted_method_rejected':True,'canonical_files_readonly':all(not (p.stat().st_mode & stat.S_IWRITE) for p in FREEZE.rglob('*') if p.is_file()),'new_builds':0,'new_ROS_runs':0,'new_worlds':0}
(BASE/'FROZEN_1M2_DELIVERY_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive.with_suffix('.zip.sha256').write_text(receipt['sha256']+'  '+archive.name+'\n',encoding='ascii')
archive.with_suffix('.receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
