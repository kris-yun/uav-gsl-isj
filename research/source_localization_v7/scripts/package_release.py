#!/usr/bin/env python3
"""Deterministic research bundle selection; never includes private raw OCB arrays."""
from pathlib import Path
import argparse, hashlib, json, zipfile

ROOT=Path(__file__).resolve().parents[1]


def selected_files():
    directories=['src','tests','configs','scripts','evidence']
    roots=['README.md','RUNBOOK_zh.md','pyproject.toml','requirements-tested.txt','DATA_AND_CODE_NOTICE.md']
    files=[ROOT/x for x in roots if (ROOT/x).is_file()]
    for directory in directories:
        files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file())
    files.extend(p for p in (ROOT/'docs').glob('*') if p.is_file())
    for directory in ['docs/METHOD_FRAMEWORK_PREVIEWS','docs/source',
                      'results/control_matrix_v7_frozen','results/ocb_static_v1',
                      'results/final_tests','results/final_review','results/bridge_demo','results/bridge_final']:
        files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file())
    excluded={'__pycache__','.pytest_cache','node_modules','build','dist'}
    return sorted({p for p in files if not excluded.intersection(p.relative_to(ROOT).parts)
                  and not any(x.endswith('.egg-info') for x in p.parts)
                  and p.suffix not in {'.pyc','.pyo','.base64'}})


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    files=selected_files();manifest=[]
    for path in files:
        data=path.read_bytes();manifest.append({'path':str(path.relative_to(ROOT)),
            'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    checksum=ROOT/'SHA256SUMS.txt'
    checksum.write_text(''.join(f'{x["sha256"]}  {x["path"]}\n' for x in manifest))
    package_manifest=ROOT/'PACKAGE_MANIFEST.json'
    package_manifest.write_text(json.dumps({'format':'gsl-v7-delivery-1','files':manifest,
      'raw_native_ocb_arrays_included':False,'controlled_synthetic_raw_ledger_included':True,
      'exclusions':['private physical arrays','sealed observations','build/lib','node_modules','old prototype results']},indent=2))
    files.extend([checksum,package_manifest])
    if (ROOT/'DELIVERY_RECEIPT.json').exists():files.append(ROOT/'DELIVERY_RECEIPT.json')
    output=Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in sorted(set(files)):
            info=zipfile.ZipInfo('source_localization_v7/'+str(path.relative_to(ROOT)),date_time=(2026,10,23,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,path.read_bytes())
    with zipfile.ZipFile(output) as z:
        bad=z.testzip()
        if bad:raise ValueError('corrupt archive member: '+bad)
    print(json.dumps({'path':str(output.resolve()),'bytes':output.stat().st_size,
       'files':len(set(files)),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
       'zip_integrity':'PASS'}))


if __name__=='__main__':main()
