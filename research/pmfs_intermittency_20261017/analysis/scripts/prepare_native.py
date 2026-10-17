from pathlib import Path
import re,shutil,json,hashlib
R=Path(__file__).resolve().parents[1];W=R.parent
S=W/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA/native_pmfs/official_upstream/gsl_server/src/gsl_server'
O=R/'cpp';O.mkdir(exist_ok=True)
def extract(text,start):
 i=text.index(start);b=text.index('{',i);n=1;j=b+1
 while n:
  n+=(text[j]=='{')-(text[j]=='}');j+=1
 return text[i:j]
original=(S/'algorithms/PMFS/PMFSLib.cpp').read_text()
functions=[extract(original,'    '+ret+' PMFSLib::'+name) for ret,name in [('void','EstimateHitProbabilities'),('double','PropagateProbabilities'),('double','applyFalloffLogOdds')]]
mathtext=(S/'algorithms/Common/Utils/Math.cpp').read_text()
mathf=[extract(mathtext,'    double '+n+'(') for n in ['lerp','clamp','evaluate1DGaussian','evaluate2DGaussian']]
mathf += [extract(mathtext,'    Vector2 ExpectedValue('),extract(mathtext,'    double Variance(')]
(O/'native_functions.cpp').write_text('#include "native_support.hpp"\nnamespace GSL {\n'+'\n'.join(functions)+'\n}\nnamespace GSL::Utils {\n'+'\n'.join(mathf)+'\n}\n')
v=(S/'algorithms/PMFS/internal/VisibilityMap.hpp').read_text();v='\n'.join(a for a in v.splitlines() if not a.startswith('#include'))
(O/'visibility.hpp').write_text(v)
dda=Path('/home/zyc/ros2_ws/src/GSL/gsl_server/third_party/DDA/include')
if (O/'dda/DDA/Vectors.h').exists():pass # Prefer bundled frozen headers, including on the original VM.
elif dda.exists():shutil.copytree(dda,O/'dda',dirs_exist_ok=True)
else:raise FileNotFoundError('Bundled frozen DDA headers missing; no internet fallback.')
rows=[]
for name,f in zip(['EstimateHitProbabilities','PropagateProbabilities','applyFalloffLogOdds'],functions):
 rows.append({'function':name,'official_body_sha256':hashlib.sha256(f.encode()).hexdigest(),'exact_verbatim_extraction':True})
(R/'results/NATIVE_FUNCTION_EXTRACTION.json').write_text(json.dumps(rows,indent=2))
print('Copied exact 2026 functions and locally preserved DDA headers; full-history parity still required.')
