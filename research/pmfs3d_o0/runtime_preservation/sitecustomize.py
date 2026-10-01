"""Storage-only guard for the frozen O0 runner; no simulation/scoring changes."""
import hashlib
import json
import os
from pathlib import Path
import shutil

_original_rmtree = shutil.rmtree

def _retain_new_raw(path, *args, **kwargs):
    root = Path(os.environ['O0_PRESERVE_WORK_ROOT']).resolve()
    target = Path(path).resolve()
    if target.parent.parent == root / 'projected2d_runs' and target.name == 'realization':
        retained = target.with_name('raw_retained')
        if retained.exists():
            raise RuntimeError('Refusing to overwrite retained raw data')
        rows = []
        for file in sorted(target.rglob('*')):
            if file.is_file():
                rows.append({'path': str(file.relative_to(target)), 'bytes': file.stat().st_size,
                             'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
        target.rename(retained)
        record = {'action': 'retain_by_rename_instead_of_delete',
                  'source': str(target), 'retained': str(retained), 'files': rows,
                  'total_bytes': sum(r['bytes'] for r in rows)}
        (target.parent / 'RAW_PRESERVATION.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
        return
    return _original_rmtree(path, *args, **kwargs)

if os.environ.get('O0_PRESERVE_WORK_ROOT'):
    shutil.rmtree = _retain_new_raw
