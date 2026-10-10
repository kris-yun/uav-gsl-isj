"""Read-only bundle verification. Requires NumPy, Pillow, PyYAML.
No VM, ROS, compilation, gas generation or algorithm update is started.
--recheck-local additionally hashes original local/Git sources when present.
"""
from pathlib import Path
import json,csv,hashlib,io,struct,sys,subprocess
import numpy as np
import yaml
from PIL import Image
sys.dont_write_bytecode=True
from audit_utils import source_support

p=Path(__file__).resolve().parent
def js(n):return json.loads((p/n).read_text(encoding='utf-8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def rows(n):
    with (p/n).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
decision=js('STATIC_QUALIFICATION_DECISION.json');inventory=rows('OFFICIAL_SCENARIO_INVENTORY.csv');matrix=rows('PHYSICAL_DATA_QUALIFICATION_MATRIX.csv')
assert len(inventory)==len(matrix)==decision['inventory_rows']==113
assert len({r['id'] for r in inventory})==len(inventory)
assert [r['id'] for r in inventory]==[r['id'] for r in matrix]
assert decision['new_native_tests']==decision['new_generations']==decision['new_seeds']==decision['new_CFD']==0
assert all(r['decision']=='HOLD' for r in inventory) and decision['ready_to_run_physically_qualified_cases']==0
assert sum(r['category']=='C' for r in inventory)==1 and sum(r['category']=='D' for r in inventory)==112
pmfs=js('OFFICIAL_PMFS_CONFIG_RAW.json');winds=js('WIND_NUMERICAL_AUDIT.json');wind_by={g['group']:g for g in winds}
assert len(pmfs['rows'])==20 and len({g['group'] for g in winds})==len(winds)
reconstructed=[]
for r in pmfs['rows']:
    base=p/'evidence/official_pmfs/scenarios'/r['scenario']
    meta=yaml.safe_load((base/'_occupancy.yaml').read_text())
    b=(base/'_occupancy.pgm').read_bytes();assert sha(b)==r['map_sha256']
    actual=source_support(b,meta,r['source_xyz'],25,r['basic']['robots'][0]['position'])
    for k in ['source_indices','source_coarse_free','source_supported','num_free_after_prune','num_free_before_prune']:
        assert actual[k]==r['source_support'][k],(r['id'],k)
    reconstructed.append(actual)
assert sum(r['source_supported'] for r in reconstructed)==10
selection=js('TWO_SCENARIO_SELECTION_LOCK.json')
assert selection['ids']==['PMFS_E3','PMFS_B4'] and selection['selection_before_new_outcomes']
assert selection['native_tests_executed']==selection['new_gas_generations']==selection['new_seeds']==selection['new_CFD']==0
for r in selection['selected_cases']:
    assert r['source_support']['source_supported'] and not r['simulation']['allow_looping']
assert selection['selected_cases'][1]['simulation']['sourceDiscriminationPower']==.4
assert selection['selected_cases'][1]['simulation']['filament_movement_stdev']==.2
assert selection['launch_default_bindings']['sourceDiscriminationPower']=='0.3'
assert all(r['simulation']['allow_looping'] and r['simulation']['loop_from_iteration']==100 and r['simulation']['loop_to_iteration']==200
    for r in pmfs['rows'] if r['scenario']=='A')
raw=js('SELECTED_RAW_ASSET_INDEX.json');full_winds={}
for asset in raw:
    b=(p/asset['evidence_file']).read_bytes();assert sha(b)==asset['sha256']
    if not asset['git_path'].endswith('.csv'):continue
    a=np.loadtxt(io.BytesIO(b),delimiter=',',skiprows=1)
    assert a.ndim==2 and a.shape[1]==6 and np.all(np.isfinite(a))
    g=next(g for g in winds if any(f['path']==asset['git_path'] for f in g['frames']))
    r=next(r for r in g['frames'] if r['path']==asset['git_path'])
    assert sha(a[:,:3].astype('<f8').tobytes())==r['velocity_numeric_sha256']
    assert len(a)==r['rows'] and abs(float(np.max(np.linalg.norm(a[:,:3],axis=1)))-r['max_speed_m_s'])<1e-12
    for probe in r['raw_numeric_probes']:
        assert a[probe['row'],:3].tolist()==probe['velocity'] and a[probe['row'],3:].tolist()==probe['xyz']
    full_winds[asset['git_path']]=a
key=next(r['wind_prefix'] for r in pmfs['rows'] if r['id']=='PMFS_B4')
a,b=[full_winds[key+'_'+str(i)+'.csv'] for i in [0,10]]
assert np.array_equal(a[:,3:],b[:,3:]) and not np.array_equal(a[:,:3],b[:,:3])
last=wind_by[key]['frames'][-1]
assert int(np.count_nonzero(np.any(b[:,:3]!=a[:,:3],axis=1)))==last['changed_velocity_rows']
assert float(np.max(np.abs(b[:,:3]-a[:,:3])))==last['max_velocity_difference_m_s']
vgr=js('VGR_LOCAL_STATIC_AUDIT.json')
assert len(vgr['houses'])==20 and len(vgr['recordings'])==77 and len(vgr['wind_samples'])==219
for r in vgr['recordings']:
    assert not r['resolved_generation_contract'] and not r['actual_physical_time_trace']
    for h in r['sampled_headers']:
        assert h['format_version']==1 and not h['physical_timestamp_in_header']
        raw_header=bytes.fromhex(h['header_hex'])
        assert list(struct.unpack_from('<3d',raw_header,88))==r['source_xyz']
        assert struct.unpack_from('<i',raw_header,132)[0]==h['wind_index']
tests=js('OFFICIAL_GADEN_CONFIG_RAW.json');assert len(tests)==7
line=next(r for r in tests if r['scenario']=='10x6_empty_room')
assert line['source_type']=='line' and line['source_line_end']==[1,.8,.7]
dynamic=next(g for g in winds if '10x6_empty_room' in g['group'])
assert len(dynamic['frames'])==dynamic['unique_velocity_numeric_fields']==25 and dynamic['observed_numerical_variation']
gitchecks=js('GADEN_FIXED_GIT_WIND_CHECK.json')
assert len(gitchecks)==45 and all(r['normalized_text_equals_official'] for r in gitchecks)
installed=js('GUEST_CONFIGURATION_DETAIL.json')
assert len(installed['installed_yaml_version_checks'])==76 and all(r['normalized_text_equals_fixed_git'] for r in installed['installed_yaml_version_checks'])
assert sum(e['frame_count'] for r in installed['configuration_roots'] for e in r['entries'])==0
for r in installed['installed_yaml_version_checks']:assert sha((p/r['evidence_file']).read_bytes())==r['sha256']
if (p/'SHA256_MANIFEST.json').exists():
    manifest=js('SHA256_MANIFEST.json')
    for n,h in manifest.items():assert sha((p/n).read_bytes())==h,n
else:manifest={}
local_checks=0
if '--recheck-local' in sys.argv:
    for r in js('SOURCE_ASSET_HASHES.json'):
        if r['provider'] in ['GSL_FIXED_GIT_OBJECT','GADEN_FIXED_GIT_OBJECT']:
            data=subprocess.check_output(['git','-C',r['repository'],'show',r['revision']+':'+r['path']])
            assert sha(data)==r['sha256'],r['path']
        else:
            f=Path(r['path']);assert f.is_file(),str(f)
            h=hashlib.sha256()
            with f.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
            assert h.hexdigest()==r['sha256'],str(f)
        local_checks+=1
print(json.dumps(dict(verdict='STATIC_AUDIT_VERIFICATION_PASS_EXECUTION_HOLD',inventory_rows=113,PMFS_maps_recomputed=20,
    PMFS_supported_sources=10,selected_pair=selection['ids'],selected_full_CFD_files_recomputed=len(full_winds),
    VGR_record_header_sets=77,installed_YAML_matches=76,manifest_files_verified=len(manifest),local_source_hash_checks=local_checks,
    native_tests=0,gas_generations=0,next_action='STOP_FOR_INDEPENDENT_REVIEW')))
