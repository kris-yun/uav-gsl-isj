from pathlib import Path
import csv,datetime,difflib,hashlib,json,shutil,statistics,zipfile
R=Path(__file__).resolve().parent;OLD=R.parent/'PMFS_O24_ROS_QUAL_20261018';D=Path(r'C:\Users\50176\Downloads')
W=Path(r'D:\ZYC\UAV\.codex\worktrees\pmfs-paper-eq6-20261017\A-gas');T=W/'research/pmfs_o24_a2_recovery_20261018'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def read(p):return list(csv.DictReader(p.open(encoding='utf-8')))
def write(p,rr):
 with p.open('w',newline='',encoding='utf-8')as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
assert load(R/'FINAL_RECOVERY_GATE.json')['status']=='PASS_AUTHORIZED_SINGLE_A2_ISOLATION_RECOVERY_SOURCE_AND_PARAMETERS_UNCHANGED'
assert not T.exists();T.mkdir(parents=True)
initial=R/'EXECUTION_ADAPTER_DIFFS.json';shutil.copyfile(initial,R/'EXECUTION_ADAPTER_DIFFS_INITIAL_DOMAIN228.json');diffs=[]
for name in ['N1_launch.py','runtime_driver.py','RUN_SHELL.sh','CASE_META.json','AUTHOR_WALL_FILE_CADENCE.csv']:
 old=OLD/'cases/O24G_A2_R02'/name;new=R/'cases/O24G_A2_ISO_R03'/name;a=old.read_text(encoding='utf-8');b=new.read_text(encoding='utf-8')
 diffs.append(dict(file=name,old_sha256=sha(old),new_sha256=sha(new),diff=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='old/'+name,tofile='actual_recovery/'+name))))
 if name=='N1_launch.py':assert a.replace('PMFS_O24_ROS_QUAL_20261018','PMFS_O24_A2_RECOVERY_20261018').replace('O24G_A2_R02','O24G_A2_ISO_R03')==b
assert load(OLD/'cases/O24G_A2_R02/CASE_META.json')['expected_parameters']==load(R/'cases/O24G_A2_ISO_R03/CASE_META.json')['expected_parameters']
initial.write_text(json.dumps(diffs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
E=R/'combined';E.mkdir(exist_ok=True);rr=read(OLD/'analysis/O24_EPISODES.csv')+read(R/'analysis/O24_EPISODES.csv')
for x in rr:
 x['selected_for_four_episode_summary']=x['role']!='O24G_A2_R02'
 x['isolation_evidence']='HOLD_HISTORICAL_DOMAIN_COLLISION'if x['role']=='O24G_A2_R02'else 'PASS_ALL_ENV_AND_GRAPH_PRE_POST_OWNER_MONITOR'if x['role']=='O24G_A2_ISO_R03'else 'NO_CONFIRMED_COLLISION_ORIGINAL_PRECHECK_INCOMPLETE'
write(E/'ALL_FIVE_EPISODES.csv',rr);selected=[x for x in rr if x['selected_for_four_episode_summary']];write(E/'SELECTED_FOUR_EPISODES.csv',selected)
stats=[]
for case in ['A2','B2']:
 s=[x for x in selected if x['case']==case];stats.append(dict(case=case,n=len(s),mean_Top5_error_m=statistics.mean(float(x['native_Top5_error_m'])for x in s),mean_search_wall_s=statistics.mean(float(x['native_search_wall_s'])for x in s),scope='Descriptive same-world repeats; original3 have weaker historical domain precheck. Not paper30-run performance replication.'))
write(E/'DESCRIPTIVE_SUMMARY.csv',stats)
for p in R.rglob('*'):
 if not p.is_file()or any(x in ['__pycache__','offline_qa']for x in p.relative_to(R).parts):continue
 q=T/p.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
oldreceipt=load(D/'PMFS_O24_四回合_交付回执_20261018.json');oldzip=Path(oldreceipt['archive']);assert sha(oldzip)=='e41712cbb4d19e336a4a725a64ad217deaca749cfc90956d48f377e99bf371fd'
Z=D/'PMFS_O24_最终冻结_A2隔离补跑与五回合完整证据_V2_20261018.zip';assert not Z.exists()
files=[dict(path=p.relative_to(T).as_posix(),sha256=sha(p),bytes=p.stat().st_size)for p in sorted(T.rglob('*'))if p.is_file()]
(T/'MANIFEST_SHA256.json').write_text(json.dumps(dict(files=files,excludes=['MANIFEST_SHA256.json itself','new offline QA outputs']),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
top=[dict(path='recovery/'+x['path'],sha256=x['sha256'],bytes=x['bytes'])for x in files]
top.append(dict(path='recovery/MANIFEST_SHA256.json',sha256=sha(T/'MANIFEST_SHA256.json'),bytes=(T/'MANIFEST_SHA256.json').stat().st_size))
top.append(dict(path='history/previous_four_episode_HOLD_evidence.zip',sha256=sha(oldzip),bytes=oldzip.stat().st_size))
for name in ['最终冻结与补跑验收_zh.md','给Pro_冻结代码与改进边界_zh.md']:top.append(dict(path=name,sha256=sha(T/name),bytes=(T/name).stat().st_size))
manifest=json.dumps(dict(files=top,scope='All5 raw episodes: old4 preserved byte-exact inside history ZIP and new1 in recovery. No original gas frames or full ROS installation included.'),ensure_ascii=False,indent=2)+'\n'
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted(T.rglob('*')):
  if p.is_file():z.write(p,'recovery/'+p.relative_to(T).as_posix())
 z.write(oldzip,'history/previous_four_episode_HOLD_evidence.zip')
 for name in ['最终冻结与补跑验收_zh.md','给Pro_冻结代码与改进边界_zh.md']:z.write(T/name,name)
 z.writestr('MANIFEST_SHA256.json',manifest)
with zipfile.ZipFile(Z)as z:
 assert z.testzip()is None
 for x in top:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
receipt=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),archive=str(Z),archive_bytes=Z.stat().st_size,archive_sha256=sha(Z),verified_payload_entries=len(top),previous_archive_sha256=sha(oldzip),research_root=str(T),branch='codex/pmfs-o24-ros-qualification-20261018',scientific_source_commit='a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533',runtime_recovery='PASS',paper_performance='HOLD',new_ROS_goals=1,total_ROS_goals_preserved=5,new_worlds=0,AIMMD=0)
(D/'PMFS_O24_V2_最终交付回执_20261018.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=True))
