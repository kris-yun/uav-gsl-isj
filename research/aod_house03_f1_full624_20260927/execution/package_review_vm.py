#!/usr/bin/env python3
"""Review archive; an infrastructure HOLD never opens raw target gas products."""
import hashlib, json, zipfile
from pathlib import Path
R=Path('/home/zyc/aod_house03_f1_full624_20260927')

def main():
    state=json.loads((R/'FINAL_EXECUTION_STATE.json').read_text())
    assert state['decision'] in ['AOD_F1_HOLD_FULL624_BUDGET','AOD_F1_HOLD_TIMEBASE',
        'AOD_F1_HOLD_ASSET_OR_PARITY','AOD_F1_FULL624_NOT_CONFIRMED',
        'AOD_F1_FULL624_CONFIRMED_STRESS_NONINFERIOR',
        'AOD_F1_FULL624_CONFIRMED_STRESS_UNCERTAIN','AOD_F1_FULL624_CONFIRMED_TRADEOFF']
    out=Path('/home/zyc/AOD_HOUSE03_F1_FULL624_REVIEW_20260927.zip')
    files={}
    for folder in ['protocol','execution','amplitude_implementation','f0','open_regression',
                   'inputs','templates','timebase_logger','timebase_logger_compile_attempt_1',
                   'review_metadata','evaluation','provenance']:
        p=R/folder
        if p.exists():
            for f in p.rglob('*'):
                if f.is_file() and '__pycache__' not in f.parts:
                    files[str(f.relative_to(R))]=f
    for f in R.iterdir():
        # stdout redirection creates the sidecar before packaging begins.
        # Its final bytes describe this ZIP and therefore cannot be its input.
        if f.is_file() and f.name != 'REVIEW_PACKAGE_METADATA.json' and f.suffix in ['.json','.log','.md']:
            files[f.name]=f
    signed=R/'AOD_HOUSE03_F1_FULL624_SIGNED_20260927.zip'
    assert hashlib.sha256(signed.read_bytes()).hexdigest()=='1318dd08c0754800b6fcea33100443ed6ebe77b72adb75fcb622b7cbaaa75502'
    files['original_inputs/'+signed.name]=signed
    # Concentration files are added only after the signed timebase audit passed
    # and the target extraction/scoring stages were authorized by that marker.
    if not state['decision'].startswith('AOD_F1_HOLD_'):
        assert json.loads((R/'TIMEBASE_AUDIT.json').read_text())['passed']
        for f in (R/'target_data').rglob('*'):
            if f.is_file():files['target_data/'+str(f.relative_to(R/'target_data'))]=f
    inventory=[]
    with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,f in sorted(files.items()):
            data=f.read_bytes()
            info=zipfile.ZipInfo(name,date_time=(2026,9,27,0,0,0))
            info.compress_type=zipfile.ZIP_STORED if name.endswith('.zip') else zipfile.ZIP_DEFLATED
            z.writestr(info,data)
            inventory.append(hashlib.sha256(data).hexdigest()+'  '+name+'\n')
        z.writestr('SHA256SUMS',''.join(inventory))
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        for line in z.read('SHA256SUMS').decode().splitlines():
            h,name=line.split('  ',1)
            assert hashlib.sha256(z.read(name)).hexdigest()==h,name
    print(json.dumps(dict(path=str(out),bytes=out.stat().st_size,
        sha256=hashlib.sha256(out.read_bytes()).hexdigest(),inventory_entries=len(inventory)),indent=2))

if __name__=='__main__':main()
