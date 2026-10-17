from pathlib import Path
import argparse,hashlib,json,zipfile
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('mode',choices=['manifest','zip']);a=p.parse_args()
Z=Path(r'C:\Users\50176\Downloads\C4_TIME_CONVERGENCE_20261017_FULL_VERIFIED.zip')
excluded={'MANIFEST_SHA256.json','PACKAGE_VERIFY.json','PUBLICATION.json','PUBLICATION_COMMANDS.json'}
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
if a.mode=='manifest':
    paths=sorted(p for p in R.rglob('*') if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts and '.publish' not in p.parts)
    manifest={p.relative_to(R).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in paths}
    (R/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('MANIFEST_CREATED',len(manifest),sum(v['bytes'] for v in manifest.values()))
else:
    assert not Z.exists(),'Refuse to replace an existing delivery'
    manifest=json.loads((R/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for name,v in manifest.items():
            assert sha(R/name)==v['sha256'],name
            z.write(R/name,name)
        z.write(R/'MANIFEST_SHA256.json','MANIFEST_SHA256.json')
    with zipfile.ZipFile(Z) as z:
        assert set(z.namelist())==set(manifest)|{'MANIFEST_SHA256.json'}
        for name,v in manifest.items():
            data=z.read(name);assert len(data)==v['bytes'] and hashlib.sha256(data).hexdigest()==v['sha256'],name
        assert z.read('MANIFEST_SHA256.json')==(R/'MANIFEST_SHA256.json').read_bytes()
    result=dict(status='PASS_ALL_ARCHIVE_MEMBERS_CRC_AND_SHA256',archive=str(Z),bytes=Z.stat().st_size,sha256=sha(Z),manifest_files=len(manifest),members=len(manifest)+1)
    (R/'PACKAGE_VERIFY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    Z.with_suffix('.zip.sha256').write_text(result['sha256']+'  '+Z.name+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
