#!/usr/bin/env python3
"""Read-only ELF inventory for historical-simulator recovery."""
import csv
import hashlib
import os
import subprocess
from pathlib import Path

OUT = Path('/home/zyc/ocb_r1_assets/EXECUTABLE_CANDIDATES.tsv')
SEARCH = Path('/home/zyc')


def run(*args):
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    return result.stdout.strip()


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    paths = [Path(line) for line in run('find', str(SEARCH), '-xdev', '-type', 'f',
                                       '-name', 'filament_simulator', '-print').splitlines()]
    rows = []
    for path in sorted(paths):
        raw = path.read_bytes()[:4]
        if raw != b'\x7fELF':
            continue
        realpath = path.resolve()
        needed = [line.strip().split('[', 1)[1].split(']', 1)[0]
                  for line in run('readelf', '-d', str(path)).splitlines()
                  if '(NEEDED)' in line and '[' in line]
        buildids = [line.strip().split('Build ID:', 1)[1].strip()
                    for line in run('readelf', '-n', str(path)).splitlines()
                    if 'Build ID:' in line]
        source_root = 'NOT_LOCATED'
        for parent in (path.parent, *path.parents):
            candidate = parent / 'src/GADEN'
            if candidate.exists():
                source_root = str(candidate)
                break
        current_source = (Path(source_root) / 'gaden_common/third_party/gaden_core/src/RunningSimulation.cpp'
                          if source_root != 'NOT_LOCATED' else None)
        if current_source and current_source.exists():
            content = current_source.read_text(encoding='utf-8', errors='replace')
            semantics = 'MISMATCH' if 'currentTime > lastSaveTime + parameters.saveDeltaTime' in content else 'UNKNOWN'
        else:
            semantics = 'UNKNOWN'
        if 'librclcpp.so' in needed and semantics == 'UNKNOWN':
            note = 'ROS2 ELF; historical ROS1 source correspondence not established'
        else:
            note = 'Current strict-interval float-clock source' if semantics == 'MISMATCH' else 'Source unavailable'
        rows.append(dict(path=str(path), realpath=str(realpath), size_bytes=path.stat().st_size,
                         mtime_ns=path.stat().st_mtime_ns, sha256=sha(path),
                         elf_info=run('file', '-b', str(path)).replace('\t', ' '),
                         build_id=','.join(buildids), linked_libraries=','.join(needed),
                         source_tree=source_root,
                         source_git_head=(run('git', '-C', source_root, 'rev-parse', 'HEAD')
                                          if source_root != 'NOT_LOCATED' else 'NOT_LOCATED'),
                         historical_semantics=semantics, note=note))
    if not rows:
        raise RuntimeError('No ELF filament_simulator candidates found')
    with OUT.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t',
                                lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    print(f'{len(rows)} ELF candidates; '
          f'{sum(r["historical_semantics"] == "MISMATCH" for r in rows)} mismatches; '
          f'{sum(r["historical_semantics"] == "UNKNOWN" for r in rows)} unknown')


if __name__ == '__main__':
    main()
