#!/usr/bin/env python3
"""Preserve a packaging-only attempt with an empty self-referential sidecar."""
import hashlib
import json
import zipfile
from pathlib import Path

source = Path('/home/zyc/AOD_HOUSE03_F1_FULL624_REVIEW_20260927.zip')
target = Path('/home/zyc/AOD_HOUSE03_F1_FULL624_REVIEW_20260927_archive_attempt_1.zip')
assert source.resolve().parent == target.resolve().parent == Path('/home/zyc').resolve()
assert source.is_file() and not target.exists()
with zipfile.ZipFile(source) as archive:
    assert archive.read('REVIEW_PACKAGE_METADATA.json') == b''
record = dict(reason='Exclude empty self-referential stdout sidecar from review payload',
              preserved_archive=str(target), bytes=source.stat().st_size,
              sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              scope='Packaging only; no scientific execution or target read')
source.rename(target)
Path('/home/zyc/aod_house03_f1_full624_20260927/ARCHIVE_REPAIR.json').write_text(
    json.dumps(record, indent=2) + '\n')
