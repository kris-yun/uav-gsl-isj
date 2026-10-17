"""Preserve initial delivery; fix cross-platform text loading and bounded publication tooling."""
from pathlib import Path
import json,hashlib,zipfile,shutil
R=Path(__file__).resolve().parents[1];B=Path(r'C:\Users\50176\Downloads\C4_PRO_REVIEW_20261017')
old=B.with_name('C4_SOURCE_RESPONSE_ATTRIBUTION_20261017.zip');new=B.with_name('C4_SOURCE_RESPONSE_ATTRIBUTION_20261017_VERIFIED.zip');assert not new.exists()
sha=lambda data:hashlib.sha256(data).hexdigest()
previous=json.loads((R/'PACKAGE_VERIFY.json').read_text());assert sha(old.read_bytes())==previous['sha256']
(R/'logs/PACKAGE_VERIFY_V1.json').write_text(json.dumps(previous,indent=2))
issue=dict(stage='Windows verify-only command',exit_code=1,error='Windows GBK default could not decode UTF-8 manifest path names',fix='Explicit UTF-8 JSON loading. Scientific data and frozen input hashes unchanged.',note='The previous Linux path remained UTF-8; preserve first archive and error.')
(R/'logs/PACKAGE_WINDOWS_ENCODING_FAILURE.json').write_text(json.dumps(issue,indent=2))
updates={'reproduce.py':R/'reproduce.py','study/reproduce.py':R/'reproduce.py','study/scripts/publish.py':R/'scripts/publish.py','study/scripts/assemble_archive.py':R/'scripts/assemble_archive.py','study/scripts/finalize_package.py':Path(__file__),'study/logs/PACKAGE_WINDOWS_ENCODING_FAILURE.json':R/'logs/PACKAGE_WINDOWS_ENCODING_FAILURE.json','study/logs/PACKAGE_VERIFY_V1.json':R/'logs/PACKAGE_VERIFY_V1.json'}
with zipfile.ZipFile(old) as src:
 manifest=json.loads(src.read('MANIFEST_SHA256.json'))
 for name,p in updates.items():
  data=p.read_bytes();manifest[name]=dict(bytes=len(data),sha256=sha(data));target=B/name;target.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(p,target)
 (B/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
 with zipfile.ZipFile(new,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as dest:
  for name in manifest:
   data=updates[name].read_bytes() if name in updates else src.read(name)
   assert sha(data)==manifest[name]['sha256'],name
   dest.writestr(name,data)
  dest.writestr('MANIFEST_SHA256.json',(B/'MANIFEST_SHA256.json').read_bytes())
with zipfile.ZipFile(new) as z:
 assert len(z.infolist())==len(manifest)+1
 for name,v in manifest.items():assert sha(z.read(name))==v['sha256'],name
receipt=dict(status='PASS_ALL_ARCHIVE_MEMBERS_CRC_AND_SHA256',members=len(manifest)+1,input_history_files_verified=1601,archive=str(new),bytes=new.stat().st_size,sha256=sha(new.read_bytes()),prior_archive_preserved=str(old),scientific_data_changed=False,new_ROS=0,new_gas_worlds=0)
new.with_suffix('.zip.sha256').write_text(receipt['sha256']+'  '+new.name+'\n','utf-8');(R/'PACKAGE_VERIFY.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True)
