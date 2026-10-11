from common_n import *
code=r'''from pathlib import Path
import json
r=Path('/home/zyc/pmfs_native_capture_r4_20261009');ctx=json.loads((r/'BUILD_CONTEXT.json').read_text())
roots=[Path(x[2:]) for x in ctx['compileflags'] if x.startswith('-I')]
for root in roots:
 p=root/'gsl_server/algorithms/PMFS/internal/Simulations.hpp'
 if p.exists():
  s=p.read_text();i=s.find('struct SimulationSource');i=s.find('SimulationSource') if i<0 else i
  print(str(p));print(s[max(0,i-300):i+2200]);break
'''
print(run_remote(code,'native_point_source_header',45))
