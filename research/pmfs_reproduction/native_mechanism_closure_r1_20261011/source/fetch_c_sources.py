from common_n import *
code=r'''from pathlib import Path
import json,base64
m=Path('/home/zyc/pmfs_m2_process_observation_20261010')
paths=list(m.glob('**/RunningSimulation.cpp'))
paths += [m/'include/gaden/internal/MathUtils.hpp',Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/build/gaden_common/third_party/gaden_core/CMakeFiles/gaden.dir/flags.make'),m/'RNG_LIBRARY_LINK_COMMAND.json']
print(json.dumps({str(p):base64.b64encode(p.read_bytes()).decode() for p in paths}))
'''
r=json.loads(run_remote(code,'fetch_C_source_bytes',45))
for path,b in r.items():
 out=WORK/'C_original'/Path(path).name;out.parent.mkdir(exist_ok=True);out.write_bytes(base64.b64decode(b))
 print(path)
dump(CORE/'C_ORIGINAL_SOURCE_HASHES.json',{p:hashlib.sha256(base64.b64decode(b)).hexdigest() for p,b in r.items()})
print((WORK/'C_original/flags.make').read_text())
