#!/usr/bin/env python3
"""Freeze prior *truth/source* exposure IDs from metadata, excluding candidate banks.

The extraction list is deliberately explicit. A PMFS candidate support is not a
scientific truth panel, even if every possible source ID occurs in that file.
No concentration, score, rank or model outcome is opened here.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import tarfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGING = Path('D:/ZYC/A-gas/_staging')
OUT = ROOT / 'evidence/e2c_r1'
ID = re.compile(r'^pmfs_\d+_\d+$')
PATH_ID = re.compile(r'(House0[123]).*?(pmfs_\d+_\d+)')
exposure: dict[tuple[str, str], set[str]] = defaultdict(set)
provenance: list[dict[str, str]] = []


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add(house: str, source_id: str, origin: str, source_sha: str, kind: str) -> None:
    if house not in ('House01', 'House02', 'House03') or not ID.fullmatch(source_id):
        raise RuntimeError(f'invalid exposure record: {house} {source_id} {origin}')
    key = (house, source_id)
    if origin in exposure[key]:
        return
    exposure[key].add(origin)
    provenance.append(dict(house=house, source_id=source_id, evidence_kind=kind,
                           origin=origin, origin_sha256=source_sha))


def rows_from_bytes(data: bytes, suffix: str) -> list[dict[str, str]]:
    delim = '\t' if suffix.endswith('.tsv') else ','
    return list(csv.DictReader(io.StringIO(data.decode('utf-8-sig')), delimiter=delim))


def table(data: bytes, origin: str, *, house: str | None = None,
          kind: str, source_key: str = 'source_id') -> None:
    rows = rows_from_bytes(data, origin)
    if not rows or source_key not in rows[0]:
        raise RuntimeError(f'missing {source_key} in {origin}')
    source_sha = digest(data)
    for row in rows:
        h = house or row.get('house')
        add(h, row[source_key], origin, source_sha, kind)


def repo_table(rel: str, *, house: str | None = None, kind: str,
               source_key: str = 'source_id') -> None:
    path = ROOT / rel
    table(path.read_bytes(), rel.replace('\\', '/'), house=house,
          kind=kind, source_key=source_key)


def archive_member(archive_name: str, member_suffix: str) -> tuple[bytes, str]:
    path = STAGING / archive_name
    with tarfile.open(path, 'r:gz') as archive:
        hits = [x for x in archive.getmembers() if x.isfile() and x.name.endswith(member_suffix)]
        if len(hits) != 1:
            raise RuntimeError(f'archive member ambiguity: {archive_name} {member_suffix}: {len(hits)}')
        data = archive.extractfile(hits[0]).read()
        return data, archive_name + '!' + hits[0].name


def archive_table(archive_name: str, member_suffix: str, *, house: str | None = None,
                  kind: str) -> None:
    data, origin = archive_member(archive_name, member_suffix)
    table(data, origin, house=house, kind=kind)


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    # Previously executed source panels, fresh target manifests and held source
    # panels. Candidate support banks and template banks are never inputs.
    repo_table('evidence/aod_house03_f0_prereg_20260927/inputs/e1/E1_HOUSE_SOURCE_PANELS.tsv',
               kind='E1_E2_SOURCE_PANEL')
    repo_table('research/aod_house03_f1_full624_20260927/protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv',
               house='House03', kind='AOD_F1_TRUTH_PANEL')
    repo_table('research/marked_encounter_pmfs_d0/protocol/JTD_E2_FRESH_TARGET_MANIFEST.tsv',
               kind='JTD_E2_FRESH_TARGET')
    for env, house in ((0, 'House01'), (1, 'House02'), (2, 'House02')):
        repo_table(f'evidence/marked_encounter_pmfs_d0/inputs/env_{env}/sources.csv',
                   house=house, kind='MARKED_ENCOUNTER_SOURCE_PANEL')
    archive_table('R0_STOCHASTIC_BENCHMARK_REVIEW_20260924.tar.gz',
                  '/repo/R0_SOURCE_PANEL_18.tsv', house='House02', kind='R0_SOURCE_PANEL')
    archive_table('CESS_D1R_REFERENCE_REVIEW_20260925.tar.gz',
                  '/repo/CESS_D1R_PANEL_168.tsv', house='House02', kind='CESS_D1R_REFERENCE_PANEL')
    archive_table('E2_CROSS_ENVIRONMENT_REVIEW_20260925.tar.gz',
                  '/repo/evidence/environment_level_benchmark_v0/e1/E1_HOUSE_SOURCE_PANELS.tsv',
                  kind='E1_E2_SOURCE_PANEL_ARCHIVE')
    # Single-source fresh targets whose metadata use a specific source ID.
    data, origin = archive_member('BIGREEN_GATE1A_REVIEW_20260924.tar.gz',
                                  '/frozen_inputs/gate1a_contract.json')
    add('House02', json.loads(data)['truth_source_id'], origin, digest(data), 'GATE1A_TRUTH')
    data, origin = archive_member('MZ_D3_S1_W2_REVIEW_20260924.tar.gz',
                                  '/targets/S1_W2_A/manifest.tsv')
    entries = dict(csv.reader(io.StringIO(data.decode('utf-8')), delimiter='\t'))
    add(entries['house'], entries['source_id'], origin, digest(data), 'MZ_D3_FRESH_TRUTH')
    data, origin = archive_member('PASI_D0_S3_W2_REVIEW_20260924.tar.gz',
                                  '/repo/PATH_ACTION_SOURCE_INFERENCE_FREEZE_20260924.md')
    ids = set(re.findall(r'pmfs_\d+_\d+', data.decode('utf-8')))
    if ids != {'pmfs_3_12'}:
        raise RuntimeError(f'PASI frozen S3 ID changed: {ids}')
    add('House02', 'pmfs_3_12', origin, digest(data), 'PASI_FRESH_TRUTH')
    # BRG collection and closed-loop evaluation receipts encode the physical
    # truth source in their filenames, independently of model outputs.
    for folder in ('receipts', 'native_collection_receipts',
                   'pilot_eval_collection_receipts', 'navfix_eval_collection_receipts'):
        directory = ROOT / 'research/brg_deployment_matched_v1/recovery' / folder
        for path in sorted(directory.glob('*.json')):
            match = PATH_ID.search(path.name)
            if match:
                add(match.group(1), match.group(2), path.relative_to(ROOT).as_posix(),
                    digest(path.read_bytes()), 'BRG_PHYSICAL_TRUTH_CASE')
    # These cross-House cases are explicit truth bindings, not support axes.
    cross = ROOT / 'research/aod_conditional_filter_v0/CROSSHOUSE_3CASE_FREEZE.json'
    data = cross.read_bytes()
    for case in json.loads(data)['cases']:
        add(case['house'], case['source_id'], cross.relative_to(ROOT).as_posix(),
            digest(data), 'AOD_FILTER_CROSSHOUSE_TRUTH')
    # LSC source IDs occur in raw-generation paths; inspect names only.
    lsc = STAGING / 'LSC_CROSSWIND_D0_REVIEW_20260925.tar.gz'
    with tarfile.open(lsc, 'r:gz') as archive:
        names = sorted({x.name for x in archive.getmembers() if x.name.endswith('/manifest.tsv')})
    for source_id in sorted(set(re.findall(r'pmfs_\d+_\d+', '\n'.join(names)))):
        add('House02', source_id, lsc.name + '!manifests/*/' + source_id,
            digest('\n'.join(names).encode()), 'LSC_CROSSWIND_SOURCE_PANEL')
    union = [dict(house=h, source_id=s, exposure_origin_count=len(origins),
                  first_origin=sorted(origins)[0])
             for (h, s), origins in sorted(exposure.items())]
    if not union:
        raise RuntimeError('empty prior-source exposure union')
    OUT.mkdir(parents=True, exist_ok=True)
    union_path = OUT / 'PRIOR_SOURCE_EXPOSURE_UNION.tsv'
    trace_path = OUT / 'PRIOR_SOURCE_EXPOSURE_PROVENANCE.tsv'
    write_tsv(union_path, union)
    write_tsv(trace_path, sorted(provenance, key=lambda r: (r['house'], r['source_id'], r['origin'])))
    report = dict(decision='PRIOR_SOURCE_EXPOSURE_UNION_FROZEN',
                  union_sha256=digest(union_path.read_bytes()),
                  provenance_sha256=digest(trace_path.read_bytes()),
                  exposure_ids_by_house={h: sum(r['house'] == h for r in union)
                                         for h in ('House01', 'House02', 'House03')},
                  provenance_rows=len(provenance),
                  selection_performed=False, concentration_or_outcome_values_read=False,
                  candidate_support_banks_excluded=True)
    (OUT / 'PRIOR_SOURCE_EXPOSURE_AUDIT.json').write_bytes(
        (json.dumps(report, indent=2, sort_keys=True) + '\n').encode('utf-8'))
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
