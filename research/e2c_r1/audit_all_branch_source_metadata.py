#!/usr/bin/env python3
"""Metadata-only audit of historical Git branch panels absent from the union."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ID = re.compile(r'^pmfs_\d+_\d+$')
BRANCH_HOUSE = {
    'research/stochastic-benchmark-refoundation-20260924': 'House02',
    'research/causal-emergent-source-scale-v0': 'House02',
    'research/causal-biorthogonal-green-v1': 'House02',
    'research/path-action-source-inference-v0': 'House02',
    'research/realization-invariant-source-signature-v0': 'House02',
    'research/lsc-crosswind-d0-v0': 'House02',
}


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)


def visit_json(value, house: str | None, found: set[tuple[str, str]]) -> None:
    if isinstance(value, dict):
        house = value.get('house', house)
        for field in ('truth_source_id', 'true_source_id', 'target_source_id', 'source_id'):
            sid = value.get(field)
            if house in ('House01', 'House02', 'House03') and isinstance(sid, str) and ID.fullmatch(sid):
                found.add((house, sid))
        for child in value.values():
            visit_json(child, house, found)
    elif isinstance(value, list):
        for child in value:
            visit_json(child, house, found)


def main() -> None:
    union_path = ROOT / 'evidence/e2c_r1/PRIOR_SOURCE_EXPOSURE_UNION.tsv'
    with union_path.open(encoding='utf-8', newline='') as stream:
        union = {(r['house'], r['source_id']) for r in csv.DictReader(stream, delimiter='\t')}
    refs = [line.split(' ', 1) for line in git(
        'for-each-ref', '--format=%(refname:short) %(objectname)', 'refs/heads').decode().splitlines()]
    branches = [name for name, _ in refs]
    blob_origins: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for branch in branches:
        for line in git('ls-tree', '-r', branch).decode('utf-8', errors='replace').splitlines():
            if '\t' not in line:
                continue
            meta, path = line.split('\t', 1)
            blob = meta.split()[-1]
            low = path.lower()
            name = Path(path).name.lower()
            if not low.endswith(('.tsv', '.csv', '.json')):
                continue
            if not any(token in name for token in ('panel', 'manifest', 'freeze', 'truth', 'target', 'source')):
                continue
            if any(token in low for token in ('candidate', 'support', 'bank', 'prediction', 'posterior',
                                              'score', 'rank', 'result', 'metrics', 'evaluation',
                                              'all_candidate', 'e2c_r1')):
                continue
            blob_origins[blob].append((branch, path))
    discoveries: dict[tuple[str, str], set[str]] = defaultdict(set)
    blobs_read = 0
    batch = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT,
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for blob, origins in blob_origins.items():
        batch.stdin.write((blob + '\n').encode())
        batch.stdin.flush()
        header = batch.stdout.readline().decode().strip().split()
        if len(header) != 3 or header[1] != 'blob':
            raise RuntimeError(f'bad Git blob header: {header}')
        size = int(header[2])
        data = batch.stdout.read(size)
        batch.stdout.read(1)  # delimiter newline
        if size > 1_000_000:
            continue
        blobs_read += 1
        for branch, path in origins:
            house_hint = BRANCH_HOUSE.get(branch)
            if not house_hint:
                match = re.search(r'House0[123]', path)
                house_hint = match.group(0) if match else None
            found: set[tuple[str, str]] = set()
            if path.endswith(('.tsv', '.csv')):
                try:
                    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig')),
                                            delimiter='\t' if path.endswith('.tsv') else ',')
                    for row in reader:
                        sid = next((row.get(field) for field in
                                    ('truth_source_id', 'true_source_id', 'target_source_id', 'source_id')
                                    if row.get(field)), None)
                        house = row.get('house') or house_hint
                        if sid and ID.fullmatch(sid) and house in ('House01', 'House02', 'House03'):
                            found.add((house, sid))
                except (UnicodeError, csv.Error):
                    pass
            else:
                try:
                    visit_json(json.loads(data), house_hint, found)
                except (UnicodeError, json.JSONDecodeError):
                    pass
            for pair in found - union:
                discoveries[pair].add(f'{branch}:{path}')
    batch.stdin.close()
    batch.wait()
    ref_bytes = ''.join(f'{name}\t{head}\n' for name, head in refs).encode('utf-8')
    out = ROOT / 'evidence/e2c_r1'
    (out / 'PRIOR_SOURCE_EXPOSURE_BRANCH_REFS.tsv').write_bytes(
        b'branch\thead\n' + ref_bytes)
    summary = dict(branches=len(branches), branch_refs_sha256=hashlib.sha256(
                       (out / 'PRIOR_SOURCE_EXPOSURE_BRANCH_REFS.tsv').read_bytes()).hexdigest(),
                   unique_metadata_blobs=len(blob_origins),
                   blobs_read=blobs_read, missing_pairs=len(discoveries),
                   missing=[dict(house=h, source_id=s, origins=sorted(origins)[:5])
                            for (h, s), origins in sorted(discoveries.items())])
    (out / 'PRIOR_SOURCE_EXPOSURE_BRANCH_AUDIT.json').write_bytes(
        (json.dumps(summary, indent=2, sort_keys=True) + '\n').encode('utf-8'))
    print(json.dumps(summary, sort_keys=True))


if __name__ == '__main__':
    main()
