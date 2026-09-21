#!/usr/bin/env python3
"""Verify only the files declared in SHA256SUMS; this does not validate science."""
from pathlib import Path
import hashlib
import sys
root = Path(__file__).resolve().parent
failures=[]; n=0
for line in (root/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    expected, name = line.split('  ',1)
    path=root/name; n+=1
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        failures.append(name)
if failures:
    print('FAILED: '+', '.join(failures)); sys.exit(1)
print(f'OK: {n} declared files match SHA-256. Runtime/scientific approval is not implied.')
