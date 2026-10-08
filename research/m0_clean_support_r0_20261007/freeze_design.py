"""Freeze/verify a static design folder and produce a portable ZIP, no simulation.

Default freeze is one-shot. --verify is read-only. Artifacts live outside the
frozen folder. Ignore only Python bytecode (not scientific content).
"""
from pathlib import Path
import argparse,csv,datetime,hashlib,io,json,zipfile

ROOT=Path(__file__).resolve().parent
DELIVERY=Path('D:/ZYC/A-gas/_deliveries/M0_CLEAN_SUPPORT_DESIGN_R0_20261007')
FREEZE=ROOT/'M0_R0_FREEZE.json';MANIFEST=ROOT/'M0_R0_FILES_SHA256.csv'
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def sha(p):return sha_bytes(Path(p).read_bytes())
def content_files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p not in [FREEZE,MANIFEST])
def verify():
    frozen=json.loads(FREEZE.read_text(encoding='utf-8'))
    assert sha(MANIFEST)==frozen['manifest_sha256']
    with MANIFEST.open(encoding='utf-8',newline='') as f:records=list(csv.DictReader(f))
    actual={p.relative_to(ROOT).as_posix() for p in content_files()}
    assert actual=={r['path'] for r in records},'Unexpected/missing frozen files'
    for r in records:
        p=ROOT/r['path'];assert p.stat().st_size==int(r['bytes']) and sha(p)==r['sha256'],r['path']
    assert frozen['execution_authorized'] is False and frozen['actual_GADEN_runs']==0
    return records,frozen

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    if args.verify:
        rec,frozen=verify();print(json.dumps({'freeze_hash_verification':'PASS','files':len(rec),'status':frozen['status'],'execution_authorized':False},indent=2));raise SystemExit(0)
    if FREEZE.exists() or MANIFEST.exists():raise RuntimeError('Already frozen; use --verify. Never overwrite.')
    check=json.loads((ROOT/'M0_STATIC_DESIGN_VERIFICATION.json').read_text(encoding='utf-8'))
    assert check['status']=='STATIC_DESIGN_CHECKS_PASS' and all(check['checks'].values()) and check['GADEN_runs']==0
    rec=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in content_files()]
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=['path','bytes','sha256'],lineterminator='\n');writer.writeheader();writer.writerows(rec);MANIFEST.write_bytes(stream.getvalue().encode('utf-8'))
    frozen={'status':'M0_R0_DESIGN_FROZEN','design_revision':'M0_R0_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'parent_handoff_head':'4e7e1ce16f7c6db3c68214c984337375c8d09e26','branch':'codex/m0-clean-support-design-20261007','actual_GADEN_runs':0,'actual_OpenFOAM_runs':0,'actual_PMFS_runs':0,'preview_scientific_runs':40,'execution_authorized':False,'scientific_verdict':'NOT_TESTED','manifest_sha256':sha(MANIFEST),'static_verification_sha256':sha(ROOT/'M0_STATIC_DESIGN_VERIFICATION.json'),'historical_W0C_verdict':'W0C_STAGE0_NO_CLEAN_BASE_HOLD','file_count':len(rec),'after_freeze':'Stop; review first. No simulation is authorized by design completion.'}
    FREEZE.write_bytes((json.dumps(frozen,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
    verify();DELIVERY.mkdir(parents=True,exist_ok=True);archive=DELIVERY/'M0_CLEAN_SUPPORT_DESIGN_R0_FROZEN_20261007.zip'
    if archive.exists():raise RuntimeError('Existing archive must not be overwritten.')
    members=[ROOT/r['path'] for r in rec]+[MANIFEST,FREEZE]
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(members):z.write(p,arcname=ROOT.name+'/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist())=={ROOT.name+'/'+p.relative_to(ROOT).as_posix() for p in members}
        for p in members:assert sha_bytes(z.read(ROOT.name+'/'+p.relative_to(ROOT).as_posix()))==sha(p)
    result={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive),'CRC_and_member_hashes':'PASS','member_count':len(members),'status':'M0_R0_DESIGN_FROZEN','actual_GADEN_runs':0,'execution_authorized':False}
    (DELIVERY/'PACKAGE_VERIFICATION.json').write_bytes((json.dumps(result,indent=2)+'\n').encode('utf-8'))
    (DELIVERY/(archive.name+'.sha256')).write_bytes((result['sha256']+'  '+archive.name+'\n').encode('ascii'))
    print(json.dumps(result,indent=2))
