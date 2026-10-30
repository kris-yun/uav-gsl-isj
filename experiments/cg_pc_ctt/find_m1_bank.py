#!/usr/bin/env python3
"""Forensic locator for the missing CG-PC-CTT M1 transport bank.

This script does not declare a file valid. It inventories likely artifacts so a
human/Codex can establish provenance before conversion.
"""
from __future__ import annotations
import argparse, hashlib, json, os
from pathlib import Path

NAME_TOKENS = (
    'house03', 'h03', 'ctt', 'm1', 'transport', '16480', 'trace', 'bank',
    'arrival', 'hazard', 'member', 'source_update', 'source-update'
)
TEXT_EXT = {'.md', '.txt', '.json', '.yaml', '.yml', '.csv', '.log'}
DATA_EXT = {'.npz', '.npy', '.csv', '.json', '.pkl', '.pickle', '.parquet', '.zip'}


def sha256(path: Path, max_bytes=None):
    h = hashlib.sha256(); read = 0
    with path.open('rb') as f:
        while True:
            b = f.read(1024 * 1024)
            if not b: break
            h.update(b); read += len(b)
            if max_bytes is not None and read >= max_bytes: break
    return h.hexdigest()


def score_name(path: Path):
    s = str(path).lower()
    return sum(int(t in s) for t in NAME_TOKENS)


def text_hits(path: Path):
    if path.suffix.lower() not in TEXT_EXT or path.stat().st_size > 5_000_000:
        return []
    try:
        txt = path.read_text(errors='ignore').lower()
    except Exception:
        return []
    needles = ['206', '8 transport', '8 member', '16480', 'house03', 'm1_go', 'arrival hazard']
    return [n for n in needles if n in txt]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('roots', nargs='+')
    p.add_argument('--out', required=True)
    p.add_argument('--max-files', type=int, default=200000)
    a = p.parse_args()

    findings = []; visited = 0
    for root_s in a.roots:
        root = Path(root_s).expanduser()
        if not root.exists():
            findings.append({'root': str(root), 'error': 'MISSING_ROOT'})
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # Avoid obvious build/cache trees unless explicitly passed as root.
            dirnames[:] = [d for d in dirnames if d not in {'.git','build','install','log','__pycache__','.cache'}]
            for name in filenames:
                visited += 1
                if visited > a.max_files:
                    break
                path = Path(dirpath) / name
                try:
                    st = path.stat()
                except OSError:
                    continue
                ns = score_name(path)
                th = text_hits(path)
                if ns >= 2 or th or (path.suffix.lower() in DATA_EXT and ns >= 1):
                    findings.append({
                        'path': str(path.resolve()),
                        'size_bytes': st.st_size,
                        'name_score': ns,
                        'text_hits': th,
                        'suffix': path.suffix.lower(),
                    })
            if visited > a.max_files:
                break

    findings = sorted(findings, key=lambda r: (-r.get('name_score',0), -len(r.get('text_hits',[])), r.get('path','')))
    report = {
        'status': 'FORENSIC_ONLY_NOT_QUALIFIED',
        'visited_files': visited,
        'candidate_count': len(findings),
        'candidates': findings[:500],
        'required_next_step': 'Establish provenance and member semantics; then convert/qualify phi[N,S,M,D].',
    }
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps({k:v for k,v in report.items() if k!='candidates'}, indent=2, ensure_ascii=False))
    print(f'full_report={out}')


if __name__ == '__main__':
    main()
