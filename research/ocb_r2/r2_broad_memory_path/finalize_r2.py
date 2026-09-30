#!/usr/bin/env python3
"""Independently verify R2 exported arithmetic and two deterministic passes."""
import csv
import hashlib
import itertools
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'evidence/ocb_r2/r2_broad_memory_path'
FILES = ('R2_INPUT_PARITY.json', 'R2_MZ_TARGETS.tsv', 'R2_PATH_CANDIDATE_TERMS.tsv',
         'R2_PATH_TARGETS.tsv', 'R2_GROUPS.tsv', 'R2_CONTEXTS.tsv',
         'R2_OMISSION_ROBUSTNESS.tsv', 'R2_COMPLEMENTARITY.json',
         'R2_GATE_RESULTS.json', 'R2_QTIME_PRESERVATION_AUDIT.json')


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
    terms = rows(BASE/'R2_PATH_CANDIDATE_TERMS.tsv')
    targets = rows(BASE/'R2_PATH_TARGETS.tsv')
    mz = rows(BASE/'R2_MZ_TARGETS.tsv')
    groups = rows(BASE/'R2_GROUPS.tsv')
    contexts = rows(BASE/'R2_CONTEXTS.tsv')
    assert len(terms) == 960 and len(targets) == 256 and len(mz) == 64
    assert len(groups) == 16 and len(contexts) == 8
    by_term = {}
    for r in terms:
        close(float(r['ES_Q_median'])-float(r['ES_RAW']), r['E_s_L'])
        key = (r['run_id'], r['candidate_source'], int(r['omitted_replicate']))
        by_term.setdefault(key, {})[int(r['lag'])] = float(r['E_s_L'])
    assert len(by_term) == 320 and all(set(v) == {1, 2, 3} for v in by_term.values())
    for r in targets:
        truth = by_term[(r['run_id'], r['truth_source'], int(r['target_replicate']))]
        alt = by_term[(r['run_id'], r['alternative_source'], int(r['alternative_omitted_replicate']))]
        et, ea = statistics.mean(truth.values()), statistics.mean(alt.values())
        close(et, r['E_BM_truth'])
        close(ea, r['E_BM_alt'])
        close(et-ea, r['Delta_BM'])
    r1_lags = rows(ROOT/'evidence/ocb_r2/cross_time_anatomy_r1/R1_LAG_TARGETS.tsv')
    r1_by_run = {}
    for r in r1_lags:
        if int(r['lag']) <= 3:
            r1_by_run.setdefault(r['run_id'], []).append(float(r['I_LAG']))
    assert len(r1_by_run) == 64 and all(len(v) == 3 for v in r1_by_run.values())
    primary = [r for r in targets if int(r['primary_omission']) == 1]
    differences = [float(r['Delta_BM'])-statistics.mean(r1_by_run[r['run_id']]) for r in primary]
    formula_audit = dict(candidate_formula='mean_L(median_Q_truth_L - raw_truth_L - median_Q_alt_L + raw_alt_L)',
                         r1_formula='mean_L(raw_alt_L - raw_truth_L - median_b(Q_alt_L_b - Q_truth_L_b))',
                         primary_targets=64,
                         max_abs_candidate_minus_r1_pairwise_median=max(abs(v) for v in differences),
                         mean_candidate_minus_r1_pairwise_median=statistics.mean(differences),
                         exact_equal_targets=sum(abs(v) < 1e-12 for v in differences))
    (BASE/'R2_FORMULA_AUDIT.json').write_text(json.dumps(formula_audit, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    for r in mz:
        close(float(r['M_truth_H3'])-float(r['M_truth_H1']), r['D_MZ'])
        close(float(r['M_truth_H5'])-float(r['M_truth_H1']), r['D_H5_H1'])
    gate = json.loads((BASE/'R2_GATE_RESULTS.json').read_text())
    for name, field in (('gate_a', 'mean_D_MZ'), ('gate_b', 'mean_Delta_BM')):
        s = gate[name]
        for house in ('House01', 'House02'):
            close(statistics.median(float(g[field]) for g in groups if g['house'] == house),
                  s['house_medians'][house])
        cmeans = [statistics.mean(float(g[field]) for g in groups if g['context'] == c['context'])
                  for c in contexts]
        close(statistics.mean(cmeans), s['context_mean'])
        observed = statistics.mean(cmeans)
        flips = [statistics.mean(sign[i]*cmeans[i] for i in range(8))
                 for sign in itertools.product((-1, 1), repeat=8)]
        p = sum(v >= observed-1e-15 for v in flips)/256
        close(p, s['exact_signflip'])
    assert gate['decision'] == 'OCB_R2_R2_MZ_PATH_FACTOR_DISCOVERY_ADVANCE'
    assert gate['gate_a_pass'] and gate['gate_b_pass']
    audit = dict(byte_identical=True, scoring_passes=2, files_sha256=hashes,
                 candidate_term_arithmetic_checked=len(targets),
                 gate_a_target_arithmetic_checked=len(mz),
                 exact_context_signflips_independently_checked=2,
                 house_medians_independently_checked=4,
                 candidate_vs_r1_formula_difference_audited=True,
                 decision_verified=gate['decision'])
    (BASE/'R2_DETERMINISTIC_REPEAT.json').write_text(json.dumps(audit, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print('R2_DETERMINISTIC_AND_ARITHMETIC_AUDIT_PASS')


if __name__ == '__main__':
    main()
