"""Join SHA-verified outer ZIP byte parts; no experiment or native process."""
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('--output',type=Path);args=p.parse_args();m=json.loads(args.manifest.read_text());root=args.manifest.resolve().parent;out=args.output or root/m['archive_name'];assert not out.exists()
total=hashlib.sha256()
with out.open('xb') as writer:
    for q in m['parts']:
        name=root/q['name'];h=hashlib.sha256();size=0
        with name.open('rb') as f:
            while block:=f.read(1024*1024):h.update(block);total.update(block);writer.write(block);size+=len(block)
        assert size==q['bytes'] and h.hexdigest()==q['sha256'],q['name']
assert out.stat().st_size==m['archive_bytes'] and total.hexdigest()==m['archive_sha256'];print(json.dumps({'archive':str(out),'SHA256':total.hexdigest(),'status':'REASSEMBLED_VERIFIED'},indent=2))
