"""Read-only portable data revalidation; no ROS, VM, raw banks, or training."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    root = args.root.resolve()
    assets = root / 'evidence/cstar_controlled_assets_20260907_r2'
    count = 0
    for line in (assets / 'BUNDLE_SHA256SUMS').read_text().splitlines():
        expected, name = line.split('  ', 1)
        path = (root / name).resolve()
        assert root in path.parents and path.is_file(), ('BUNDLE_PATH', name)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, ('BUNDLE_HASH', name)
        count += 1
    proc = subprocess.run([sys.executable, '-B', str(root / 'tools/cstar_audit_controlled_data.py'),
                           '--assets', str(assets), '--read-only'], capture_output=True, text=True)
    if proc.returncode:
        print(proc.stdout)
        print(proc.stderr)
        raise SystemExit(proc.returncode)
    print(f'CSTAR_CONTROLLED_BUNDLE_REVERIFY=PASS; files={count}; three frozen folds; independent sensor/branch audit; eight destructive controls')
    print('Scope: controlled data integrity/qualification, NOT M1/M2 utility, not virgin heldout confirmation.')


if __name__ == '__main__':
    main()
