"""Hash and losslessly package this completed audit; never remove originals."""
from pathlib import Path
import csv,hashlib,json,shutil,subprocess,sys,zipfile,datetime
R=Path(__file__).resolve().parents[1];D=Path(r'C:\Users\50176\Downloads')
QA=R.parent/'C4_CLOSE17_QA'
for name in ['REPLAY_PASS.json','REPLAY_EVENTS.csv']:
    shutil.copy2(QA/'portable_events'/name,R/'lineage'/('PORTABLE_'+name))
for x in ['C4_TIME_CONVERGENCE_20261017_FULL_VERIFIED.zip','C4_SOURCE_RESPONSE_ATTRIBUTION_20261017_VERIFIED.zip']:
    p=D/x
    if p.exists():
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        expected={'C4_TIME_CONVERGENCE_20261017_FULL_VERIFIED.zip':'b1dabe73190fa16494c7830609cd1acf3e1538073fa90208a617d23b9aa1c603','C4_SOURCE_RESPONSE_ATTRIBUTION_20261017_VERIFIED.zip':'518de2e838a014c35b7a8ea7320afffd10d39f3eb7455f4d040f04ec1addb834'}[x]
        assert h==expected
        (R/'lineage'/f'{x}.identity.json').write_text(json.dumps(dict(file=x,bytes=p.stat().st_size,sha256=h,read_only_identity_check=True),indent=2))
# Copy-only no new runs; publication receipts are external to immutable ZIP manifest.
def payload():return [p for p in R.rglob('*') if p.is_file() and not any(x in p.parts for x in ['__pycache__','.git']) and p.name not in ['MANIFEST_SHA256.json','PACKAGE_VERIFY.json','PUBLICATION.json','PUBLICATION_COMMANDS.json']]
manifest={p.relative_to(R).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(payload())}
(R/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
cmds=[]
for args in [['--verify-only'],['--analysis-out',str(QA/'analysis')]]:
    t=subprocess.run([sys.executable,str(R/'reproduce.py'),*args],capture_output=True,text=True)
    cmds.append(dict(command=[sys.executable,str(R/'reproduce.py'),*args],exit_code=t.returncode,stdout=t.stdout,stderr=t.stderr));assert t.returncode==0,t.stderr
package=D/'C4_FINAL_PHYSICAL_AUDIT_20261017_VERIFIED.zip';assert not package.exists()
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in [*manifest,'MANIFEST_SHA256.json']:z.write(R/name,'C4_FINAL_PHYSICAL_AUDIT_20261017/'+name)
with zipfile.ZipFile(package) as z:
    assert z.testzip() is None
    for name,item in manifest.items():
        b=z.read('C4_FINAL_PHYSICAL_AUDIT_20261017/'+name);assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],name
receipt=dict(status='PASS_FULL_ZIP_CRC_AND_EVERY_MEMBER_SHA256',archive=str(package),bytes=package.stat().st_size,sha256=hashlib.sha256(package.read_bytes()).hexdigest(),payload_files=len(manifest),zip_members=len(manifest)+1,commands=cmds,verification_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(R/'PACKAGE_VERIFY.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
package.with_suffix('.verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='commands'},indent=2))
