"""Read-only verification of original runtime; copy only into new study output."""
import hashlib,json,pathlib,shutil,subprocess,sys
r=pathlib.Path(sys.argv[1]);out=r/'provenance';out.mkdir(exist_ok=False)
old=pathlib.Path('/home/zyc/ros2_ws/tnqc_r2_six_offline_20260921_authoritative')
frozen=json.loads((old/'freeze/runtime_sha256.json').read_text())
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
checks={p:pathlib.Path(p).is_file() and sha(p)==h for p,h in frozen.items()}
(out/'FROZEN_RUNTIME_POST_AUDIT.json').write_text(json.dumps({'all_unchanged':all(checks.values()),'checks':checks},indent=2)+'\n')
assert all(checks.values())
build=pathlib.Path('/home/zyc/ros2_ws/tnqc_h01_pipeline_20260921/verified_native_v2/build')
files=[build/'libPMFS.a',build/'libGSL_common.a',build/'CMakeFiles/meaci_replay_true.dir/flags.make',build/'CMakeFiles/meaci_replay_true.dir/link.txt',r/'build/native_bank',r/'build/build_provenance.json',r.parent/'active_deconfounding_native_20260921.log',r.parent/'active_deconfounding_native_20260921_retry.log']
for p in files:shutil.copy2(p,out/p.name)
env={'compiler':subprocess.check_output(['c++','--version'],text=True),'platform':subprocess.check_output(['uname','-a'],text=True)}
(out/'toolchain.json').write_text(json.dumps(env,indent=2)+'\n')
bank_provenance=[]
for p in sorted((r/'run').glob('House??_seed?')):
    bank_provenance.append({'case':p.name,'response_sha256':sha(p/'responses.f32'),
        'wrapper_source_commit':'c6f2d95' if p.name=='House01_seed0' else 'f6241ac',
        'wrapper_executable_sha256':None if p.name=='House01_seed0' else sha(r/'build/native_bank'),
        'limitation':'first wrapper executable hash not retained before obstacle-only validation correction' if p.name=='House01_seed0' else None})
(out/'bank_provenance.json').write_text(json.dumps(bank_provenance,indent=2)+'\n')
for p in (r/'run').glob('*_incomplete_*'):
    shutil.copy2(p/'timing.csv',out/(p.name+'_timing.csv'))
    (out/(p.name+'.json')).write_text(json.dumps({'path':str(p),'response_bytes':(p/'responses.f32').stat().st_size,'response_sha256':sha(p/'responses.f32'),'retained_on_VM':True},indent=2)+'\n')
(out/'SHA256SUMS.json').write_text(json.dumps({p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()},indent=2)+'\n')
print(json.dumps({'runtime_files':len(checks),'all_unchanged':True,'banks':len(bank_provenance)}))
