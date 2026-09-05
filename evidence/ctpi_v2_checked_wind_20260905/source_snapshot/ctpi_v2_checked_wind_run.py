"""Execute the two already-frozen spent-wind arms and preserve every exit."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    root=Path('/home/zyc/CTPI_ONLINE_CORE_V2_20260905')
    stage=root/'gmrf_checked_wind_v1'
    contract=stage/'CONTRACT.json'
    specification=json.loads(contract.read_text())
    executable=stage/'wind_replay'
    geometry=root/'gmrf_spent_wind_v2/NAVIGATION_MAP/navigation_slice.yaml'
    wind=root/'gmrf_spent_wind_v1/H01_wind_trace.csv'
    identity_paths=[contract,executable,geometry,geometry.with_suffix('.pgm'),wind,
        Path(__file__),root/'tools/ctpi_v2_gmrf_spent_wind.cpp',
        root/'ros2_package/src/gsl_server/algorithms/PMFS/CTPIGmrfCheckedWindV2.hpp',
        Path('/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib/libgmrf_wind_core.so'),
        Path('/home/zyc/ros2_ws/install/gmrf_wind_mapping/include/gmrf_wind_core/gmrf_map.h')]
    with (stage/'IDENTITY.json').open('x') as f:
        json.dump({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in identity_paths},f,indent=2)
    results=[]
    for arm in specification['arms']:
        name=arm['name']
        if name not in ('checked_cumulative','checked_latest_cell'):
            raise ValueError('unexpected arm')
        config=stage/(name+'.json')
        with config.open('x') as f:
            json.dump({'parameters':specification['parameters'],'latest_cell':arm['latest_cell']},f)
        output=stage/name
        command=[str(executable),str(geometry),str(wind),str(config),str(output)]
        started=time.monotonic()
        print('START '+name,flush=True)
        with (stage/(name+'.log')).open('x') as log:
            try:
                done=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=600)
                code=done.returncode
            except subprocess.TimeoutExpired:
                code='TIMEOUT_CHILD_TERMINATED'
        result={'arm':name,'returncode':code,'seconds':time.monotonic()-started,
                'completion_marker_present':(output/'COMPLETED.json').exists(),'command':command}
        results.append(result)
        with (stage/(name+'_RUN.json')).open('x') as f:
            json.dump(result,f,indent=2)
        print(json.dumps(result),flush=True)
    with (stage/'RUNS.json').open('x') as f:
        json.dump(results,f,indent=2)
    return int(any(r['returncode']!=0 for r in results))


if __name__=='__main__':
    sys.exit(main())
