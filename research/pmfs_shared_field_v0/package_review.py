import argparse,hashlib,json,subprocess,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.root=a.root.resolve()
if a.out.exists():raise FileExistsError('refuse to overwrite a review ZIP')
files=[a.root/'.gitattributes']
for folder in ('research/pmfs_shared_field_v0','evidence/pmfs_shared_field_v0'):
    files.extend(f for f in (a.root/folder).rglob('*') if f.is_file() and '__pycache__' not in f.parts)
for layout in ('P_G1A','P_E2'):
    files.append(a.root/f'evidence/source_probe_crossed_audit_v0/SPX_G0_CENTRAL_{layout}_10x30.npy')
sha=lambda b:hashlib.sha256(b).hexdigest()
items={f.relative_to(a.root).as_posix():f.read_bytes() for f in sorted(files)}
e=a.root/'evidence/pmfs_shared_field_v0';d=json.loads((e/'DEVELOPMENT_RESULT.json').read_text())
provenance={'branch':subprocess.check_output(['git','branch','--show-current'],cwd=a.root,text=True).strip(),
    'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.root,text=True).strip(),
    'decision':d['DEVELOPMENT_DECISION'],'pre_run_commit':'02ed0b43','new_plumes':0,'sealed_data_read':False}
items['PROVENANCE.json']=(json.dumps(provenance,indent=2)+'\n').encode()
items['SHA256SUMS']=''.join(f'{sha(b)}  {n}\n' for n,b in sorted(items.items())).encode()
with zipfile.ZipFile(a.out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for n,b in sorted(items.items()):z.writestr(n,b)
with zipfile.ZipFile(a.out) as z:
    assert z.testzip() is None
    entries=z.read('SHA256SUMS').decode().splitlines()
    for line in entries:
        h,n=line.split('  ',1);assert sha(z.read(n))==h,n
result={**provenance,'path':str(a.out.resolve()),'bytes':a.out.stat().st_size,'sha256':sha(a.out.read_bytes()),'verified_files':len(entries)}
a.out.with_suffix('.metadata.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(result,indent=2))
