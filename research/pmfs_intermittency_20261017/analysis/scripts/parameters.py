from pathlib import Path
import yaml,re,json
def read_parameters(root):
 p=yaml.safe_load((root/'runtime/resolved_GSL_parameters.yaml').read_text())
 if p:return next(iter(p.values()))['ros__parameters'],'CAPTURED_RUNTIME_DUMP'
 # Preserve failed dump, and use literal launch values rather than fit outcomes.
 text=(root/'N1_launch.py').read_text();keys=['kernelSigma','kernelStretchConstant','hitPriorProbability','confidenceSigmaSpatial','confidenceMeasurementWeight']
 out={}
 for k in keys:
  m=re.search(r'"'+k+r'"\s*:\s*([\d.]+)',text);assert m,(root,k);out[k]=float(m[1])
 for k in ['th_gas_present','sourceDiscriminationPower']:
  m=re.search(r'name="'+k+r'",\s*value="([\d.]+)"',text);assert m,(root,k);out[k]=float(m[1])
 out['localEstimationWindowSize']=2 # Official PMFSLib.cpp GetHitProbabilitySettings, explicit getParam default.
 return out,'LAUNCH_LITERAL_AND_OFFICIAL_DEFAULT_FALLBACK_RUNTIME_DUMP_FAILED_REQUIRES_NUMERIC_PARITY'
