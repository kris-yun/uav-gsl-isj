"""Create an additive portable screen bundle; never rewrite old data evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT/'evidence/cstar_controlled_screen_20260907'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,required=True)
    args = ap.parse_args()
    assert not args.out.exists()
    files = set()
    # Reuse all the prior portable bundle's files, without changing their bytes.
    index = ROOT/'evidence/cstar_controlled_assets_20260907_r2/BUNDLE_SHA256SUMS'
    for line in index.read_text().splitlines():
        digest,name = line.split('  ',1)
        p = ROOT/name
        assert hashlib.sha256(p.read_bytes()).hexdigest() == digest, name
        files.add(p)
    files.add(index)
    files.update(p for p in EVID.rglob('*') if p.is_file() and p.name != 'SCREEN_SHA256SUMS')
    for name in ['controlled_screen.py','verify_controlled_screen.py','CSTAR_CONTROLLED_SCREEN_CONFIG_20260907.json']:
        files.add(ROOT/'experiments/ctpi_cstar'/name)
    files.add(ROOT/'docs/CSTAR_BOUNDED_CAUSAL_SCREEN_20260907.md')
    files.add(Path(__file__).resolve())
    sha_index = EVID/'SCREEN_SHA256SUMS'
    sha_index.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n'
                                for p in sorted(files)),encoding='utf-8')
    files.add(sha_index)
    with tarfile.open(args.out,'x:gz') as archive:
        for p in sorted(files): archive.add(p,arcname=p.relative_to(ROOT).as_posix(),recursive=False)
    print(json.dumps({'files_hashed':len(files)-1,'archive':str(args.out),
                      'sha256':hashlib.sha256(args.out.read_bytes()).hexdigest()},indent=2))


if __name__ == '__main__': main()
