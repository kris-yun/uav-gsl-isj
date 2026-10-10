from pathlib import Path
import sys,json,base64,subprocess,hashlib
root=Path(__file__).resolve().parents[2]
out=root/'outputs/PMFS_OFFICIAL_SCENARIO_STATIC_QUALIFICATION_20261009'
sys.path.insert(0,str(root/'work/pmfs_r2'))
from remote import run
q=run(r'''
from pathlib import Path
import json,os,hashlib,base64,shutil
roots=[Path('/home/zyc/ros2_ws/install/test_env/share/test_env/scenarios'),Path('/home/zyc/ros2_ws/install/pmfs_env/share/pmfs_env/scenarios')]
result={'configuration_roots':[],'small_yaml_files':{},'system':{}}
for base in roots:
    for scenario in sorted(base.iterdir()):
        if not scenario.is_dir():continue
        path=scenario/'environment_configurations/config1' if 'test_env' in str(base) else scenario
        item={'path':str(path),'scenario':scenario.name,'exists':path.exists(),'entries':[]}
        if path.exists():
            for d,dirs,files in os.walk(path):
                if len(Path(d).relative_to(path).parts)>=4:dirs[:]=[]
                frames=[n for n in files if n.startswith('iteration_') and n[10:].isdigit()]
                info={'path':d,'subdirs':dirs[:],'frame_count':len(frames),'files':[]}
                for n in files:
                    f=Path(d)/n
                    if n.endswith('.yaml'):
                        b=f.read_bytes();result['small_yaml_files'][str(f)]=base64.b64encode(b).decode()
                        info['files'].append({'name':n,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
                    elif n.endswith(('.csv','.pgm','.json')) and not ('wind_simulations' in d):
                        info['files'].append({'name':n,'bytes':f.stat().st_size})
                item['entries'].append(info)
        result['configuration_roots'].append(item)
disk=shutil.disk_usage('/home/zyc');result['system']['disk_free_bytes']=disk.free
result['system']['logical_cpus']=os.cpu_count()
mem={line.split(':')[0]:line.split(':')[1].strip() for line in Path('/proc/meminfo').read_text().splitlines()}
result['system']['MemTotal']=mem['MemTotal'];result['system']['MemAvailable']=mem['MemAvailable']
print(json.dumps(result))
''','OFFICIAL_SCENARIO_STATIC_CONFIG_DETAIL',60)
assert q.returncode==0,q.stderr.decode(errors='replace')
a=json.loads(q.stdout)
gaden=root/'work/pmfs_r5/GADEN';pmfsrepo='D:/ZYC/A-gas/_reference_native_pmfs_upstream_20260923'
checks=[]
for name,b64 in a.pop('small_yaml_files').items():
    b=base64.b64decode(b64)
    if '/test_env/scenarios/' in name:
        rel='test_env/scenarios/'+name.split('/test_env/scenarios/',1)[1]
        repo=str(gaden);pin='ccb02e959a45a188e4b6c78792e197633fc64f1c'
    else:
        rel='Environment_config/PMFS/scenarios/'+name.split('/pmfs_env/scenarios/',1)[1]
        repo=pmfsrepo;pin='4e141e162551e674f2f30ddb8859136c72139aac'
    expected=subprocess.run(['git','-C',repo,'show',pin+':'+rel],capture_output=True)
    equal=expected.returncode==0 and b.replace(b'\r\n',b'\n')==expected.stdout.replace(b'\r\n',b'\n')
    target=out/'evidence/installed_yaml'/(hashlib.sha256(name.encode()).hexdigest()[:12]+'_'+Path(name).name)
    checks.append(dict(path=name,git_path=rel,revision=pin,sha256=hashlib.sha256(b).hexdigest(),normalized_text_equals_fixed_git=equal,
        evidence_file=target.relative_to(out).as_posix()))
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
a['installed_yaml_version_checks']=checks
(out/'GUEST_CONFIGURATION_DETAIL.json').write_text(json.dumps(a,indent=2),encoding='utf-8')
print(json.dumps(dict(configuration_roots=len(a['configuration_roots']),existing_gas_frames=sum(e['frame_count'] for r in a['configuration_roots'] for e in r['entries']),
    installed_yaml_files=len(checks),normalized_equal=sum(r['normalized_text_equals_fixed_git'] for r in checks),system=a['system'])))
