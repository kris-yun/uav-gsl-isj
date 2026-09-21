"""Package immutable response artifacts and verifiable SHA256 inventory."""
import hashlib,io,json,pathlib,sys,tarfile
repo=pathlib.Path(__file__).resolve().parents[2]
responses=pathlib.Path(sys.argv[1]).resolve();dest=pathlib.Path(sys.argv[2]).resolve()
assert not dest.exists(),'refuse overwriting an evidence package'
files={}
for prefix,folder in [('responses',responses),('implementation',pathlib.Path(__file__).parent),('evidence',repo/'evidence/active_deconfounding_v1')]:
    for p in sorted(folder.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.tar.gz') and p.name!='PACKAGE_MANIFEST.json':
            files[prefix+'/'+p.relative_to(folder).as_posix()]=p
inventory={name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in files.items()}
manifest=json.dumps(inventory,indent=2).encode()
with tarfile.open(dest,'w:gz') as t:
    for name,p in files.items():t.add(p,arcname=name,recursive=False)
    info=tarfile.TarInfo('SHA256SUMS.json');info.size=len(manifest);t.addfile(info,io.BytesIO(manifest))
with tarfile.open(dest) as t:
    actual=json.load(t.extractfile('SHA256SUMS.json'))
    assert all(hashlib.sha256(t.extractfile(name).read()).hexdigest()==h for name,h in actual.items())
summary={'file':dest.name,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
         'declared_files':len(files),'verified_files':len(files),'verdict':'NO_GO_WITHIN_FROZEN_OFFLINE_SCREEN'}
dest.with_name('PACKAGE_MANIFEST.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
