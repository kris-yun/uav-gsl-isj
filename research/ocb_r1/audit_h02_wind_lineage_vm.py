#!/usr/bin/env python3
"""Read-only byte inventory of the two House02 wind trees."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

A = Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House02/wind_simulations')
B = Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House02/House02/wind_simulations')
OUT = Path('/home/zyc/h02_wind_lineage_r1_audit')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write(name, header, rows):
    with (OUT / name).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        writer.writerow(header)
        writer.writerows(rows)


def inventory(root):
    assert root.is_dir() and not root.is_symlink()
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_dir():
            continue
        if not path.is_file() or path.is_symlink():
            raise RuntimeError('Unexpected nonregular wind asset: ' + str(path))
        stat = path.stat()
        result[str(path.relative_to(root))] = (
            stat.st_size,
            datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            digest(path),
        )
    return result


def conflict_diff(left, right):
    differing = 0
    first = []
    blocks = 0
    with left.open('rb') as fa, right.open('rb') as fb:
        offset = 0
        while True:
            a, b = fa.read(1024 * 1024), fb.read(1024 * 1024)
            if not a and not b:
                break
            if a != b:
                blocks += 1
                for i, (va, vb) in enumerate(zip(a, b)):
                    if va != vb:
                        differing += 1
                        if len(first) < 16:
                            first.append((offset + i, va, vb))
                differing += abs(len(a) - len(b))
            offset += max(len(a), len(b))
    size_a, size_b = left.stat().st_size, right.stat().st_size
    prefix = min(size_a, size_b) if not first else first[0][0]
    return dict(differing_bytes=differing, blocks_with_difference=blocks,
                common_prefix_bytes=prefix,
                a_is_exact_prefix_of_b=(not first and size_a < size_b),
                first_divergence_offset=prefix if size_a != size_b or first else None,
                first_overlapping_byte_differences=first)


def main():
    OUT.mkdir(exist_ok=True)
    a, b = inventory(A), inventory(B)
    fields = ('relative_path', 'size_bytes', 'mtime_utc', 'sha256')
    write('A_FILES.tsv', fields, ((k, *v) for k, v in a.items()))
    write('B_FILES.tsv', fields, ((k, *v) for k, v in b.items()))
    a_only, b_only = sorted(a.keys() - b.keys()), sorted(b.keys() - a.keys())
    same = sorted(k for k in a.keys() & b.keys() if a[k][2] == b[k][2])
    different = sorted(k for k in a.keys() & b.keys() if a[k][2] != b[k][2])
    write('A_ONLY.tsv', fields, ((k, *a[k]) for k in a_only))
    write('B_ONLY.tsv', fields, ((k, *b[k]) for k in b_only))
    write('COMMON_IDENTICAL.tsv', ('relative_path', 'size_a', 'size_b', 'sha256'),
          ((k, a[k][0], b[k][0], a[k][2]) for k in same))
    write('COMMON_DIFFERENT.tsv', ('relative_path', 'size_a', 'size_b', 'mtime_a_utc',
                                   'mtime_b_utc', 'sha256_a', 'sha256_b'),
          ((k, a[k][0], b[k][0], a[k][1], b[k][1], a[k][2], b[k][2]) for k in different))
    info = dict(A_realpath=str(A.resolve()), B_realpath=str(B.resolve()),
                A_file_count=len(a), B_file_count=len(b), A_total_bytes=sum(v[0] for v in a.values()),
                B_total_bytes=sum(v[0] for v in b.values()), A_only=len(a_only), B_only=len(b_only),
                common_identical=len(same), common_different=len(different),
                different_paths=different, conflict_diffs={k: conflict_diff(A / k, B / k) for k in different})
    (OUT / 'A_B_SUMMARY.json').write_text(json.dumps(info, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(info, ensure_ascii=False))


if __name__ == '__main__':
    main()
