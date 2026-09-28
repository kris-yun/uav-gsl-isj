"""Build a compact BRG V1 pause review and separate full GADEN data ZIP."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from collect_native_host import ROOT, NATIVE_ARCHIVE, VGR_ARCHIVE, sha
from collect_coverage_host import ARCHIVE as COVERAGE_ARCHIVE

WORKTREE = ROOT.parents[2]
HOST = Path(r'C:\Users\50176\Desktop\vm数据')
ASSETS = HOST / 'BRG_V1_PAUSE_REVIEW_ASSETS_20260928'
EPISODES = HOST / 'BRG_V1_EPISODES_20260928'
INVALID = HOST / 'BRG_V1_INVALID_COVERAGE_PILOT_20260928'
COMPACT = HOST / 'BRG_V1_PAUSED_REVIEW_20260928.zip'
FULL = HOST / 'BRG_V1_CONTINUOUS_72_FULL_20260928.zip'
CONTINUOUS_RECEIPTS = ROOT / 'receipts'
NATIVE_RECEIPTS = ROOT / 'native_collection_receipts'
COVERAGE_RECEIPTS = ROOT / 'coverage_collection_receipts'
FIXED_DATE = (2026, 9, 28, 0, 0, 0)


def add_bytes(bundle: zipfile.ZipFile, name: str, data: bytes,
              digest: dict[str, str]) -> None:
    info = zipfile.ZipInfo(name, FIXED_DATE)
    info.compress_type = zipfile.ZIP_STORED
    bundle.writestr(info, data)
    digest[name] = hashlib.sha256(data).hexdigest()


def add_file(bundle: zipfile.ZipFile, name: str, file: Path,
             digest: dict[str, str], expected: str | None = None) -> None:
    if not file.is_file() or name in digest:
        raise RuntimeError(f'missing/duplicate pause review member {name}')
    actual = sha(file)
    if expected is not None and actual != expected:
        raise RuntimeError(f'archive drift before pause packaging {file}')
    bundle.write(file, name, compress_type=zipfile.ZIP_STORED)
    digest[name] = actual


def sums_text(digest: dict[str, str]) -> bytes:
    return ''.join(f'{value}  {name}\n' for name, value in sorted(digest.items())).encode()


def receipts(folder: Path, count: int) -> list[dict]:
    rows = [json.loads(p.read_text()) for p in sorted(folder.glob('*.json'))]
    if len(rows) != count:
        raise RuntimeError(f'expected {count} receipts in {folder}, found {len(rows)}')
    return rows


def continuous_inventory() -> tuple[list[tuple[Path, dict]], bytes]:
    rows = receipts(CONTINUOUS_RECEIPTS, 72)
    result = []
    lines = ['ordinal\tcase_id\tarchive_file\tbytes\tsha256\n']
    for row in rows:
        case_id = row['run_id']
        path = NATIVE_ARCHIVE / f'{case_id}.tar.zst'
        actual = sha(path)
        if actual != row['archive_sha256'] or path.stat().st_size != row['archive_bytes']:
            raise RuntimeError(f'continuous GADEN archive drift: {case_id}')
        result.append((path, row))
        lines.append(f'{row["ordinal"]}\t{case_id}\t{path.name}\t'
                     f'{path.stat().st_size}\t{actual}\n')
    return result, ''.join(lines).encode()


def repo_files() -> list[Path]:
    result = subprocess.run(['git', 'ls-files', '-z', 'research/brg_deployment_matched_v1'],
                            cwd=WORKTREE, check=True, capture_output=True)
    return [WORKTREE / Path(raw.decode('utf-8')) for raw in result.stdout.split(b'\0') if raw]


def main() -> None:
    if COMPACT.exists() or FULL.exists():
        raise RuntimeError('refuse to overwrite an existing pause review ZIP')
    if subprocess.run(['git', 'status', '--porcelain'], cwd=WORKTREE,
                      capture_output=True, text=True, check=True).stdout.strip():
        raise RuntimeError('commit pause evidence before packaging')
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=WORKTREE,
                          capture_output=True, text=True, check=True).stdout.strip()
    continuous, inventory = continuous_inventory()
    native = receipts(NATIVE_RECEIPTS, 48)
    coverage = receipts(COVERAGE_RECEIPTS, 4)
    episodes = json.loads((EPISODES / 'OPEN_EPISODE_INVENTORY.json').read_text())
    if (episodes['count'] != 52 or episodes['train'] != 41 or
            episodes['dev'] != 11 or len(episodes['episodes']) != 52):
        raise RuntimeError('pause episode manifest count changed')
    pause_hash = sha(ROOT / 'V1_PAUSE_EPISODE_INVENTORY.json')
    if sha(EPISODES / 'OPEN_EPISODE_INVENTORY.json') != pause_hash:
        raise RuntimeError('host episode inventory drift since pause freeze')
    readme = (f'BRG V1 PAUSED REVIEW — 2026-09-28\n'
              f'Git branch: codex/brg-v1-continuous-recovery-20260928\n'
              f'Git HEAD: {head}\n'
              '72/72 continuous OPEN GADEN archives; 48/48 Native VGR paths; '
              '4/48 V3 coverage paths. No model training or four-arm evaluation.\n'
              'The compact ZIP contains all currently collected VGR raw logs, '
              'features, frozen banks/contracts/code, and an inventory of the '
              '72 native GADEN archives. The separate full ZIP contains all 72 '
              'unchanged native archives. See repo/research/brg_deployment_matched_v1/'
              'recovery/BRG_V1_PAUSE_HANDOFF_20260928.md.\n').encode('utf-8')
    with zipfile.ZipFile(COMPACT, 'w', allowZip64=True) as bundle:
        hashes: dict[str, str] = {}
        add_bytes(bundle, 'README_PAUSE.txt', readme, hashes)
        add_bytes(bundle, 'GADEN_72_ASSET_INVENTORY.tsv', inventory, hashes)
        for file in repo_files():
            add_file(bundle, 'repo/' + file.relative_to(WORKTREE).as_posix(), file, hashes)
        for row in native:
            path = VGR_ARCHIVE / f'native_{row["ordinal"]:03d}_{row["case_id"]}.tar.zst'
            add_file(bundle, 'vgr_native_48/' + path.name, path, hashes,
                     row['archive_sha256'])
        for row in coverage:
            path = COVERAGE_ARCHIVE / f'coverage_{row["ordinal"]:03d}_{row["case_id"]}.tar.zst'
            add_file(bundle, 'vgr_coverage_v3_4/' + path.name, path, hashes,
                     row['archive_sha256'])
        bad = INVALID / 'INVALID_COVERAGE_OPEN_LOOP_PILOT_013.tar.zst'
        add_file(bundle, 'invalid_v2_pilot/' + bad.name, bad, hashes,
                 'fd86348bbf9c9f7965ed3b0b8cb4e2f82704ed3a303411b2c632a319a0b1c911')
        for row in episodes['episodes']:
            for key in ('episode_path', 'metadata_path'):
                path = Path(row[key])
                add_file(bundle, 'episodes_52/' + path.name, path, hashes)
        for folder in ('banks', 'vm_patches', 'vgr_source'):
            for path in sorted((ASSETS / folder).glob('*')):
                if path.is_file():
                    add_file(bundle, f'{folder}/{path.name}', path, hashes)
        for path in sorted((HOST / 'BRG_V1_COVERAGE_ROUTES_20260928').glob('*')):
            if path.is_file():
                add_file(bundle, f'coverage_routes/{path.name}', path, hashes)
        add_bytes(bundle, 'SHA256SUMS', sums_text(hashes), {})
    with zipfile.ZipFile(COMPACT) as bundle:
        if bundle.testzip() is not None:
            raise RuntimeError('compact review ZIP CRC failure')
    with zipfile.ZipFile(FULL, 'w', allowZip64=True) as bundle:
        hashes = {}
        add_bytes(bundle, 'README_FULL.txt',
                  b'72 unchanged OPEN continuous native GADEN archives; see compact review ZIP for contracts and analysis.\n',
                  hashes)
        add_bytes(bundle, 'GADEN_72_ASSET_INVENTORY.tsv', inventory, hashes)
        for path, row in continuous:
            add_file(bundle, 'gaden_native_72/' + path.name, path, hashes,
                     row['archive_sha256'])
        add_bytes(bundle, 'SHA256SUMS', sums_text(hashes), {})
    with zipfile.ZipFile(FULL) as bundle:
        if bundle.testzip() is not None:
            raise RuntimeError('full data ZIP CRC failure')
    print(json.dumps({'status': 'BRG_V1_PAUSE_REVIEW_PACKAGED', 'git_head': head,
                      'compact': {'path': str(COMPACT), 'bytes': COMPACT.stat().st_size,
                                  'sha256': sha(COMPACT)},
                      'full_native': {'path': str(FULL), 'bytes': FULL.stat().st_size,
                                      'sha256': sha(FULL)}}))


if __name__ == '__main__':
    main()
