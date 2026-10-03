"""Execute pinned publisher preprocessing with explicitly recorded portability patches."""
from pathlib import Path
import os, json, subprocess, hashlib, sys
import matplotlib
matplotlib.use('Agg')
ROOT=Path(r'C:\work\SVALBARD_BOREHOLE_REAL_DATA_20261003')
sys.path.insert(0,str(ROOT/'dependencies'))
RAW=ROOT/'raw/active'
OUT=ROOT/'processed'
OUT.mkdir(exist_ok=True)
os.chdir(OUT)
changes=[]
for source in sorted((RAW/'nature_run/preprocess_drone_data').glob('0*.py')):
    code=source.read_text()
    code=code.replace('"./../drone_data/remote_control/"', repr(str(RAW/'drone_data/remote_control')))
    code=code.replace('"./../drone_data/methane_sensor/"', repr(str(RAW/'drone_data/methane_sensor')))
    code=code.replace('"./../drone_data/sonic_anemometer/"', repr(str(RAW/'drone_data/sonic_anemometer')))
    if source.name.startswith('03'):
        code=code.replace('if filename.endswith(suffix):', 'if filename.endswith(suffix) and filename != "readme.txt":')
        changes.append('03: exclude non-measurement readme.txt from instrument parser')
    if source.name.startswith('01'):
        code=code.replace('for folder in os.listdir(directory):', 'for folder in os.listdir(directory):\n    if not os.path.isdir(os.path.join(directory, folder)): continue')
        code=code.replace("df[col].str.replace(',', '.')", "df[col].map(lambda v: str(v).replace(',', '.') if pd.notna(v) else np.nan)")
        changes.append('01: skip root readme.txt; numeric conversion tolerates pandas integer-inferred zero columns')
    (OUT/('executed_'+source.name)).write_text(code)
    print('Executing', source.name, flush=True)
    exec(compile(code,str(source),'exec'), {'__name__':'__main__'})
(OUT/'portability_patches.json').write_text(json.dumps(changes,indent=2))
