from pathlib import Path
import argparse,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args()
    dest=Path(args.out)
    if dest.exists():raise RuntimeError('refuse to overwrite prior installation evidence')
    paths=sorted(p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='INSTALL_FILE_HASHES.json')
    manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    m=ROOT/'evidence/INSTALL_FILE_HASHES.json';m.write_text(json.dumps(manifest,indent=2)+'\n')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(paths+[m]):z.write(p,p.relative_to(ROOT).as_posix())
    print(json.dumps({'path':str(dest),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'manifest_files':len(manifest),'status':json.loads((ROOT/'STATUS.json').read_text())['status']},indent=2))
if __name__=='__main__':main()
