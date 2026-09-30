#!/usr/bin/env python3
"""Verify independent R1 repeats and export context-level audit tables."""
import csv
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'evidence/ocb_r2/cross_time_anatomy_r1'
P1, P2 = BASE / 'pass1', BASE / 'pass2'
FILES = ('R1_AGGREGATES.json', 'R1_BLOCK_GROUPS.tsv', 'R1_BLOCK_TARGETS.tsv',
         'R1_INPUT_PARITY.json', 'R1_LAG_GROUPS.tsv', 'R1_LAG_TARGETS.tsv',
         'R1_PRESERVATION_AUDIT.json', 'R1_REFERENCE_OMISSION.tsv')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def write_tsv(path, records):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=records[0], delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)


def main():
    hashes = {}
    for name in FILES:
        assert (P1/name).is_file() and (P2/name).is_file()
        hashes[name] = digest(P1/name)
        assert hashes[name] == digest(P2/name), name
        (BASE/name).write_bytes((P1/name).read_bytes())
    lag = rows(BASE/'R1_LAG_GROUPS.tsv')
    block = rows(BASE/'R1_BLOCK_GROUPS.tsv')
    assert len(lag) == 144 and len(block) == 16
    context_rows = []
    for context in sorted({r['context'] for r in block}):
        for lag_index in range(1, 10):
            subset = [r for r in lag if r['context'] == context and int(r['lag']) == lag_index]
            values = [float(r['mean_I_LAG']) for r in subset]
            assert len(values) == 2
            context_rows.append(dict(context=context, house=subset[0]['house'],
                                     kind='LAG', lag=lag_index, n_source_groups=2,
                                     mean_effect=statistics.mean(values), median_effect=statistics.median(values),
                                     positive_groups=sum(v > 0 for v in values)))
        subset = [r for r in block if r['context'] == context]
        for kind, column in (('BLOCK_B2_MINUS_B1', 'mean_G_B2'),
                             ('BLOCK_B5_MINUS_B1', 'mean_G_B5'),
                             ('BLOCK_B10_MINUS_B1', 'mean_G_B10')):
            values = [float(r[column])-float(r['mean_G_B1']) for r in subset]
            context_rows.append(dict(context=context, house=subset[0]['house'],
                                     kind=kind, lag='', n_source_groups=2,
                                     mean_effect=statistics.mean(values), median_effect=statistics.median(values),
                                     positive_groups=sum(v > 0 for v in values)))
    write_tsv(BASE/'R1_CONTEXTS.tsv', context_rows)
    repeat = dict(byte_identical=True, scoring_passes=2, files_sha256=hashes,
                  canonical_context_rows=len(context_rows),
                  canonical_context_sha256=digest(BASE/'R1_CONTEXTS.tsv'))
    (BASE/'R1_DETERMINISTIC_REPEAT.json').write_text(json.dumps(repeat, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    print('R1_DETERMINISTIC_REPEAT_PASS', len(context_rows))


if __name__ == '__main__':
    main()
