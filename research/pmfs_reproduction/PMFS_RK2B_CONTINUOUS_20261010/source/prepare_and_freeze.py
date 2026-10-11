"""Last prephysical freeze: source/configuration, existing assets and software tests."""
from common_b import *
import difflib,shutil

reg=load(WORK/'registry_preflight.json');pf=load(CORE/'PREFLIGHT.json')
assert pf['chosen_mode']==24 and pf['new_physical_outputs']==0
reg.update(mode=24,jobs=pf['jobs'],remote_data_path=DATA,host_data_path='D:/ZYC/A-gas/workspace/PMFS_RK2B_DATA_20261010',new_disk_cap_bytes=6*1024**3,prephysical_freeze_time_ns=time.time_ns(),parent_A_manifest_SHA256='de2b538a6c43d807f7fabb3d8b493a573fb14629be1761f5f359a9f898a5a8a0')
assert Path(reg['host_data_path']).is_dir() and not any(Path(reg['host_data_path']).iterdir())
reg['receiver_plan_id']=hashlib.sha256(json.dumps(reg['receiver_plan'],sort_keys=True).encode()).hexdigest()
dump(CORE/'experiment_registry.json',reg)
(CORE/'source').mkdir(exist_ok=False)
for p in WORK.glob('*.py'):
    compile(p.read_text(encoding='utf-8'),str(p),'exec');shutil.copyfile(p,CORE/'source'/p.name)
shutil.copyfile(WORK/'rng_probe.cpp',CORE/'source/rng_probe.cpp')
sourcehashes={p.name:sha(p) for p in (CORE/'source').iterdir()}
dump(CORE/'PREPHYSICAL_SOURCE_SHA256.json',sourcehashes)
(CORE/'authorization').mkdir()
for n in ['machine_contract.json','NEW_SEED_PROPOSAL.json','02_Codex_一次授权连续执行总任务书_zh.md','00_直接发给Codex.txt']:
    p=WORK/'pro_handoff'/n
    if not p.exists():p=Path('C:/Users/50176/Downloads')/n
    if p.exists():shutil.copyfile(p,CORE/'authorization'/n)
dump(CORE/'PARENT_EVIDENCE_REFERENCES.json',dict(A_commit=reg['parent_commit'],A_manifest=reg['parent_A_manifest_SHA256'],A_ZIP_SHA256='aacc34567871da11e6d67451272e1f119801946c8337e7ead376a36086e9e214',RK1_manifest='b310b6c7d13112660ccd1bdd0cd4fbbb8f708ceb53e02bec4f03126d12575534',PRO_ZIP_SHA256='7aedf06c37ab19f582c0d6db325367421aa515281942785a591281dade06d7d9',large_parent_copied=False))
(CORE/'technical_repairs').mkdir()
first=WORK/'preflight_b.FIRST_FAILED.py';now=WORK/'preflight_b.py'
shutil.copyfile(first,CORE/'technical_repairs/preflight_first_failed.py')
(CORE/'technical_repairs/PREPHYSICAL_SEED_ENDIAN_ASSERTION.diff').write_text(''.join(difflib.unified_diff(first.read_text().splitlines(True),now.read_text().splitlines(True),fromfile='failed assertion',tofile='correct original LE / new BE validation')),encoding='utf-8')
dump(CORE/'technical_repairs/LEDGER.json',dict(repairs=[dict(kind='prephysical assertion',count=1,physical_attempts_before_repair=0,original_numeric_seeds_changed=False,reason='Original B SHA seed convention little-endian, new PRO seeds big-endian; validation repaired, values retained.')]))
subprocess.run([sys.executable,'-B',str(WORK/'test_and_audit_b.py'),'software'],check=True)
files={'experiment_registry.json':(CORE/'experiment_registry.json').read_bytes(),'PREFLIGHT.json':(CORE/'PREFLIGHT.json').read_bytes()}
for n in ['generate_b.py','verify_raw_receiver_queries.py','cache_native.py']:files[n]=(WORK/n).read_bytes()
tail="""
import hashlib,shutil,time,subprocess
data=Path(REGDATA)
assert not any(data.iterdir())
pref=json.loads((t/'PREFLIGHT.json').read_text())
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in pref['runtime_assets_SHA256'].items())
assert shutil.disk_usage(data).free>=10737418240
assert shutil.disk_usage(t).free>=4294967296+16777216
Path(data/'PREPHYSICAL_SOURCE_SHA256.json').write_text(SOURCEHASH)
print(json.dumps({'status':'PASS_FINAL_PREFLIGHT_SOURCE_FREEZE','physical_outputs':0,'free_data_bytes':shutil.disk_usage(data).free,'code_files':[p.name for p in t.glob('*') if p.is_file()]}))
""".replace('REGDATA',repr(DATA)).replace('SOURCEHASH',repr(json.dumps(sourcehashes,indent=2)))
print(upload(files,tail,'FINAL_PREPHYSICAL_FREEZE',60))
# Copy only existing occupancy and small RNG probe audit; do not run the generator.
scp=['scp','-i','C:/Users/50176/.ssh/id_ed25519_vm','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes']
p=subprocess.run(scp+['zyc@192.168.111.128:/home/zyc/pmfs_b4_native_validation_20261009/derived_B4/OccupancyGrid3D.csv',str(RAW/'OccupancyGrid3D.csv')],capture_output=True);assert p.returncode==0,p.stderr
assert sha(RAW/'OccupancyGrid3D.csv')=='00914f3d7114d45d764ff24be9e832da70d6e2e69528918f2c3c1143fea40295'
dump(CORE/'PREPHYSICAL_FREEZE_COMPLETE.json',dict(time_ns=time.time_ns(),registry_SHA256=sha(CORE/'experiment_registry.json'),source_SHA256=sha(CORE/'PREPHYSICAL_SOURCE_SHA256.json'),physical_outputs=0,mode=24,all_evaluation_code_present_before_first_generation=True))
print('PREPHYSICAL_FREEZE_COMPLETE')
