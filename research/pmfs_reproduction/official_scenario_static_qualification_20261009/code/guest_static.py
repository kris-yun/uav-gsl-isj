from pathlib import Path
import json,sys
root=Path(__file__).resolve().parents[2]
out=root/'outputs/PMFS_OFFICIAL_SCENARIO_STATIC_QUALIFICATION_20261009'
sys.path.insert(0,str(root/'work/pmfs_r2'))
from remote import run
code=r'''
from pathlib import Path
import os,json,hashlib
roots=[
'/home/zyc/ros2_ws/install/pmfs_env/share/pmfs_env/scenarios',
'/home/zyc/ros2_ws/install/test_env/share/test_env/scenarios',
'/home/zyc/native_pmfs_recovery_v1/src/gsl_server/Environment_config/PMFS/scenarios',
'/home/zyc/pmfs_official_alignment_r5_20261009/ws/src/pmfs_env/scenarios',
'/home/zyc/pmfs_clean_c1_preparation_r6_20261009',
'/home/zyc/hcmc_v1_independent_data_20260922']
result={'read_only_static_audit':True,'ROS_nodes_started':0,'gas_generations':0,'roots':[]}
for name in roots:
    p=Path(name);r={'path':name,'exists':p.exists(),'entries':[]}
    if p.exists():
        for directory,dirs,files in os.walk(p):
            depth=len(Path(directory).relative_to(p).parts)
            if depth>=4:dirs[:]=[]
            if 'gas_simulations' in directory or 'realization' in directory or 'FilamentSimulation' in directory:
                frames=[n for n in files if n.startswith('iteration_') and n[10:].isdigit()]
                if frames:
                    indices=sorted(int(n[10:]) for n in frames)
                    r['entries'].append(dict(path=directory,frame_count=len(frames),first=indices[0],last=indices[-1],other_files=[n for n in files if n not in frames][:15]))
                    continue
            chosen=[n for n in files if n.endswith(('.yaml','.gproj','.json','.csv','.pgm'))]
            r['entries'].append(dict(path=directory,subdirs=dirs[:],files=[dict(name=n,bytes=(Path(directory)/n).stat().st_size) for n in chosen][:50]))
    result['roots'].append(r)
print(json.dumps(result))
'''
q=run(code,'OFFICIAL_SCENARIO_STATIC_GUEST_INVENTORY',60)
if q.returncode:
    (out/'GUEST_ACCESS_ERROR.txt').write_text(q.stderr.decode(errors='replace'),encoding='utf-8')
    raise SystemExit(q.returncode)
a=json.loads(q.stdout)
(out/'GUEST_STATIC_INVENTORY.json').write_text(json.dumps(a,indent=2),encoding='utf-8')
print(json.dumps([dict(path=r['path'],exists=r['exists'],entries=len(r['entries']),gas_recordings=sum('frame_count' in x for x in r['entries'])) for r in a['roots']]))
