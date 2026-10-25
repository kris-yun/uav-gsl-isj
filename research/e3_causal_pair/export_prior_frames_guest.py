"""Copy only already queried old E3 states for portable readout verification.

Read-only source; no propagation, source movement, or regenerated frames.
"""
from pathlib import Path
import csv
import hashlib
import json
import shutil

ROOT = Path('/mnt/hgfs/workspace/METHOD_COMPARISON_O24_1M2_20261024')
OUT = ROOT / 'outputs/E3_CAUSAL_PAIR_20261025'
SOURCE = Path('/home/zyc/pmfs_e3_native_validation_20261009/one_realization_E3')


def main():
    with (OUT / 'schedule/ORIGINAL_NATIVE_QUERY_INPUT.csv').open() as stream:
        frames = sorted({int(row['frame']) for row in csv.DictReader(stream)})
    destination = OUT / 'original_E3_decomposition/saved_world'
    files = [SOURCE / f'iteration_{frame}' for frame in frames]
    files += sorted(path for path in (SOURCE / 'wind').rglob('*') if path.is_file())
    manifest = []
    for original in files:
        relative = original.relative_to(SOURCE)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        expected = hashlib.sha256(original.read_bytes()).hexdigest()
        if not target.exists():
            shutil.copy2(original, target)
        assert hashlib.sha256(target.read_bytes()).hexdigest() == expected
        manifest.append(dict(path=relative.as_posix(), bytes=target.stat().st_size,
                             sha256=expected, original_path=str(original)))
    (OUT / 'original_E3_decomposition/ORIGINAL_FRAME_COPY_MANIFEST.json').write_text(
        json.dumps(dict(new_physical_runs=0, frame_count=len(frames), files=manifest),
                   indent=2) + '\n')
    size = sum(path.stat().st_size for path in OUT.rglob('*') if path.is_file())
    assert size < 128 * 1024 * 1024, size
    print(json.dumps(dict(status='RESULT_RECEIVED_EXISTING_FRAME_COPY',
                          frames=len(frames), output_bytes=size)))


if __name__ == '__main__':
    main()
