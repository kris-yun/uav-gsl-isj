#!/usr/bin/env python3
"""Run the actual suite and preserve an auditable receipt even on failure."""
import argparse,hashlib,importlib.metadata,json,os,platform,subprocess,sys,time
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--out',default='results/test_receipt');a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
start=time.time();command=[sys.executable,'-m','pytest','-q','--junitxml='+str((out/'junit.xml').resolve())]
env=os.environ.copy();env['PYTHONPATH']=str(root/'src')+os.pathsep+env.get('PYTHONPATH','')
with (out/'pytest.log').open('w') as log:
    result=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
hashes={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest()
        for pattern in ('src/**/*.py','tests/*.py') for f in sorted(root.glob(pattern))}
receipt={'command':command,'cwd':str(root),'exit_code':result.returncode,'duration_s':time.time()-start,
         'python':sys.version,'platform':platform.platform(),
         'versions':{n:importlib.metadata.version(n) for n in ('numpy','scipy','PyYAML','pytest')},
         'source_sha256':hashes,'scope':'implementation and constructed properties, not native localization gain'}
(out/'TEST_RECEIPT.json').write_text(json.dumps(receipt,indent=2))
print((out/'pytest.log').read_text());sys.exit(result.returncode)
