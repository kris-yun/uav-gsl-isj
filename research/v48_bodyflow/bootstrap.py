#!/usr/bin/env python3
"""Build the exact tested V48 core from the frozen V46 tree without editing it.

The complete downloadable V48 package additionally contains 13 proof/test entries
and raw-data audit scripts. This repository patch is the executable method delta;
it does not claim to contain those full local receipts or the original dataset.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess
HERE=Path(__file__).resolve().parent
OLD='7250101427e41778c04b6ba91d2877b21c2f26b35dbea6ed12387ff6922faf11'
NEW='d01c7a2cff8de389581f26fc5d9e045c1e573f3c7627002101af59f41407bb2a'
PATCH='77d08076aa25c12fd8e890fc6f551eae31dc5da83659bd389a82ba1fc46c15b1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--base',type=Path,default=HERE.parent/'v46_bodyflow');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
base=a.base.resolve();out=a.output.resolve()
if out.exists():raise SystemExit('Output already exists; refusing to overwrite')
if not (base/'v46_flowolf/core.py').is_file() or sha(base/'v46_flowolf/core.py')!=OLD:raise SystemExit('Wrong frozen V46 base')
if sha(HERE/'core_v46_to_v48.patch')!=PATCH:raise SystemExit('Patch hash mismatch')
if shutil.which('patch') is None:raise SystemExit('Install the standard patch utility')
shutil.copytree(base,out,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git'))
subprocess.run(['patch','--batch','--forward','-p1','-i',str(HERE/'core_v46_to_v48.patch')],cwd=out,check=True)
if sha(out/'v46_flowolf/core.py')!=NEW:raise SystemExit('Patched core differs from tested V48 core')
(out/'v46_flowolf').rename(out/'v47_flowolf')
for f in out.rglob('*.py'):
    f.write_text(f.read_text().replace('v46_flowolf','v47_flowolf'))
shutil.copy2(HERE/'native_adapter_v48.py',out/'native_adapter_v48.py')
(out/'requirements.txt').write_text('numpy==2.3.5\nscipy==1.17.0\npandas==2.2.3\n')
receipt={'scope':'Exact V48 method-core delta only; no new native performance','base_core':OLD,'new_core':sha(out/'v47_flowolf/core.py'),'native_B0_repaired':False,'full_proof_bundle':'Use the separately delivered V48_Code_and_Contract.zip for 13 certificates and raw audits'}
(out/'V48_BOOTSTRAP_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
