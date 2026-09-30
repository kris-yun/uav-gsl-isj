#!/usr/bin/env python3
"""Verify R2A repeat and arithmetic from exported anchor/target/context tables."""
import csv
import hashlib
import itertools
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'evidence/ocb_r2/r2a_matched_memory'
FILES = ('R2A_INPUT_PARITY.json', 'R2A_TARGETS.tsv', 'R2A_GROUPS.tsv',
         'R2A_CONTEXTS.tsv', 'R2A_ANCHOR_EFFECTS.tsv', 'R2A_ANCHOR_SUMMARY.tsv',
         'R2A_GATE_RESULTS.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def close(a, b):
    assert abs(float(a)-float(b)) < 1e-12, (a, b)


def main():
    hashes = {}
    for name in FILES:
        p1, p2 = BASE/'pass1'/name, BASE/'pass2'/name
        assert p1.is_file() and p2.is_file()
        hashes[name] = sha(p1)
        assert sha(p2) == hashes[name], name
        (BASE/name).write_bytes(p1.read_bytes())
    anchors = rows(BASE/'R2A_ANCHOR_EFFECTS.tsv')
    targets = rows(BASE/'R2A_TARGETS.tsv')
    groups = rows(BASE/'R2A_GROUPS.tsv')
    contexts = rows(BASE/'R2A_CONTEXTS.tsv')
    assert len(anchors) == 448 and len(targets) == 64 and len(groups) == 16 and len(contexts) == 8
    assert all(int(r['future_slot']) == int(r['anchor_t'])+1 for r in anchors)
    for r in targets:
        sub = [a for a in anchors if a['run_id'] == r['run_id']]
        assert sorted(int(a['anchor_t']) for a in sub) == list(range(2, 9))
        for h in (1, 2, 3):
            close(statistics.mean(float(a[f'M_H{h}']) for a in sub), r[f'M_H{h}_COMMON'])
        close(float(r['M_H3_COMMON'])-float(r['M_H1_COMMON']), r['D_MZ_COMMON'])
    for g in groups:
        sub = [r for r in targets if r['context'] == g['context'] and r['truth_source'] == g['truth_source']]
        assert len(sub) == 4
        close(statistics.mean(float(r['D_MZ_COMMON']) for r in sub), g['mean_D_MZ_COMMON'])
    for c in contexts:
        sub = [g for g in groups if g['context'] == c['context']]
        assert len(sub) == 2
        close(statistics.mean(float(g['mean_D_MZ_COMMON']) for g in sub), c['mean_D_MZ_COMMON'])
    gate = json.loads((BASE/'R2A_GATE_RESULTS.json').read_text())
    vals = [float(c['mean_D_MZ_COMMON']) for c in contexts]
    observed = statistics.mean(vals)
    flips = [statistics.mean(sign[i]*vals[i] for i in range(8))
             for sign in itertools.product((-1, 1), repeat=8)]
    close(sum(v >= observed-1e-15 for v in flips)/256, gate['stats']['exact_signflip'])
    for house in ('House01', 'House02'):
        close(statistics.median(float(g['mean_D_MZ_COMMON']) for g in groups if g['house'] == house),
              gate['stats']['house_medians'][house])
    assert gate['decision'] == 'OCB_R2_R2A_MZ_MATCHED_WINDOW_HOLD' and not gate['gate_pass']
    audit = dict(byte_identical=True, scoring_passes=2, files_sha256=hashes,
                 anchor_to_target_checks=64, target_to_group_checks=16,
                 group_to_context_checks=8, exact_signflip_independently_checked=True,
                 decision_verified=gate['decision'])
    (BASE/'R2A_DETERMINISTIC_REPEAT.json').write_text(json.dumps(audit, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    print('R2A_DETERMINISTIC_AND_ARITHMETIC_AUDIT_PASS')


if __name__ == '__main__':
    main()
