"""Standalone audited child; only whitelisted scalar files can be opened."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util,json,numpy as np
root=Path(__file__).resolve().parent;config=json.loads((root/'config.json').read_text());opens=[];denied=[]
allowed={root/'forecast.npz',root/'observation.npz',root/'kernel.py'}
libraries=[Path(sys.prefix).resolve(),Path(sys.base_prefix).resolve()]
def hook(event,args):
    if event!='open' or not isinstance(args[0],(str,bytes)):return
    p=Path(args[0]).resolve();mode=args[1] or ''
    if p in allowed or any(p.is_relative_to(d) for d in libraries):opens.append(str(p));return
    denied.append(str(p));raise PermissionError('INFER_READ_NOT_WHITELISTED')
sys.addaudithook(hook)
s=importlib.util.spec_from_file_location('frozen_scalar_kernel',root/'kernel.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with np.load(root/'forecast.npz',allow_pickle=False) as z:
    assert set(z.files)=={'predicted_ppm','candidate_ids'};x=z['predicted_ppm'];ids=z['candidate_ids'].tolist()
with np.load(root/'observation.npz',allow_pickle=False) as z:
    assert set(z.files)=={'observed_ppm'};y=z['observed_ppm']
res=m.infer(x,y,config['head'],config['scale']);checks=False
try:Path(config['forbidden_path']).read_bytes()
except PermissionError:checks=True
assert checks
out={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in res.items()}
print(json.dumps(dict(result=out,candidate_ids=ids,denied_illegal_read=checks,opened_paths=opens,denied_paths=denied)))
