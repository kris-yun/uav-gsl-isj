from pathlib import Path
import hashlib,json,shutil,subprocess,sys,zipfile
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def allowed(p):return p.is_file()and'official_repo'not in p.relative_to(R).parts and'__pycache__'not in p.parts and p.name!='MANIFEST_SHA256.json'
assert not (R/'MANIFEST_SHA256.json').exists(),'Do not overwrite a frozen release'
qa=R.parent/'PMFS_PAPER_FIRST_ROS_QA_20261017';assert not qa.exists()
q=subprocess.run([sys.executable,str(R/'portable_replay.py'),'--out',str(qa)],capture_output=True,text=True)
validation=R/'validation';validation.mkdir()
(validation/'replay.stdout').write_text(q.stdout,encoding='utf-8');(validation/'replay.stderr').write_text(q.stderr,encoding='utf-8')
assert q.returncode==0,q.stderr
shutil.copyfile(qa/'REPLAY.json',validation/'REPLAY.json')
files=[dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(R.rglob('*'))if allowed(p)]
(R/'MANIFEST_SHA256.json').write_text(json.dumps(dict(files=files),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
dest=Path('C:/Users/50176/Downloads/PMFS_完整ROS基线_A2B2实测与适配记录_20261017.zip');assert not dest.exists()
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for x in files:z.write(R/x['path'],'PMFS_PAPER_FIRST_ROS_QUAL_20261017/'+x['path'])
 z.write(R/'MANIFEST_SHA256.json','PMFS_PAPER_FIRST_ROS_QUAL_20261017/MANIFEST_SHA256.json')
with zipfile.ZipFile(dest)as z:
 assert z.testzip()is None
 for x in files:assert hashlib.sha256(z.read('PMFS_PAPER_FIRST_ROS_QUAL_20261017/'+x['path'])).hexdigest()==x['sha256']
receipt=dict(status='PASS_FRESH_PORTABLE_REPLAY_ZIP_CRC_EVERY_PAYLOAD_SHA256',archive=str(dest),bytes=dest.stat().st_size,sha256=sha(dest),files=len(files),manifest_sha256=sha(R/'MANIFEST_SHA256.json'),new_physical_worlds=0,AIMMD=0,completed_qualification_episodes=2,retained_technical_attempts=2)
dest.with_suffix('.verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
