from pathlib import Path
import os,json,hashlib,zipfile,subprocess,sys,datetime
R=Path(__file__).resolve().parent;QA=R.parent/'AIMMD_PATH_NECESSITY_PILOT_20261017_QA'
excluded={'MANIFEST_SHA256.json','PACKAGE_VERIFY.json','PUBLICATION.json','PUBLICATION_COMMANDS.json'}
files=[p for p in R.rglob('*') if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts]
size=sum(p.stat().st_size for p in files);assert size<256*1024**2
manifest={p.relative_to(R).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)}
(R/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
commands=[]
for args in [['--verify-only'],['--analysis-out',str(QA/'analysis')]]:
    t=subprocess.run([sys.executable,str(R/'reproduce.py'),*args],capture_output=True,text=True)
    commands.append(dict(command=[sys.executable,str(R/'reproduce.py'),*args],exit_code=t.returncode,stdout=t.stdout,stderr=t.stderr));assert t.returncode==0,t.stderr
out=Path(r'C:\Users\50176\Downloads\AIMMD_关键路径必要性实测_完整证据_20261017.zip');assert not out.exists()
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for n in [*manifest,'MANIFEST_SHA256.json']:z.write(R/n,'AIMMD_PATH_NECESSITY_PILOT_20261017/'+n)
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    for n,v in manifest.items():
        b=z.read('AIMMD_PATH_NECESSITY_PILOT_20261017/'+n);assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'],n
receipt=dict(status='PASS_MANIFEST_FRESH_ANALYSIS_ZIP_CRC_AND_EVERY_MEMBER_SHA256',archive=str(out),bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),payload_bytes=size,payload_files=len(manifest),zip_members=len(manifest)+1,commands=commands,verification_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(R/'PACKAGE_VERIFY.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');out.with_suffix('.verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='commands'},ensure_ascii=False,indent=2))
