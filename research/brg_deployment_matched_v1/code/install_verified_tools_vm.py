from pathlib import Path,PurePosixPath
import hashlib,json,os,subprocess,zipfile
archive=Path('/home/zyc/BRG_V1_INSTALL_ASSET_REVIEW_20260928.zip')
dest=Path('/home/zyc/brg_deployment_matched_v1_20260928')
expected='dd0a424edc46593b2c6fb43cebabba3eab491dec8960d2b362b8c89869d150f6'
if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:raise RuntimeError('install ZIP hash mismatch')
if dest.exists():raise RuntimeError('refuse to replace installed version')
with zipfile.ZipFile(archive) as z:
    if len(set(z.namelist()))!=len(z.namelist()):raise RuntimeError('duplicate members')
    manifest=json.loads(z.read('evidence/INSTALL_FILE_HASHES.json'))
    for name in z.namelist():
        p=PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts:raise RuntimeError('unsafe archive path')
        if name in manifest and hashlib.sha256(z.read(name)).hexdigest()!=manifest[name]:raise RuntimeError('payload hash mismatch')
    dest.mkdir();z.extractall(dest)
env=dict(os.environ);env.pop('PYTHONNOUSERSITE',None)
env['PYTHONPATH']='/home/zyc/.local/lib/python3.10/site-packages'
test=subprocess.run(['python3',str(dest/'tests/test_contract.py')],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(dest/'evidence/VM_CONTRACT_TEST.log').write_text(test.stdout)
result={'installed_directory':str(dest),'install_zip_sha256':expected,'file_hashes_verified':len(manifest),'test_exit_code':test.returncode,'tools_installed':True,'ros_runtime_changed':False,'training_executed':False,'closed_loop_executed':False,'status':json.loads((dest/'STATUS.json').read_text())['status']}
(dest/'evidence/VM_INSTALL_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));print(test.stdout)
if test.returncode:raise SystemExit(test.returncode)
