#!/usr/bin/env python3
import csv, hashlib, json, statistics
from pathlib import Path

first=Path('/home/zyc/persistent_source_pmfs_r1_20260926')
repeat=Path('/home/zyc/persistent_source_pmfs_r1_repeat_20260926')
names=('candidate_summary.csv','scores_long.csv','persistent_source_samples.csv','source_blind_audit.txt')
hashes={}
for name in names:
    a=(first/name).read_bytes(); b=(repeat/name).read_bytes()
    assert a==b, 'EXECUTION_HOLD_NONDETERMINISTIC: '+name
    hashes[name]=hashlib.sha256(a).hexdigest()
with (first/'scores_long.csv').open(newline='') as f:
    rows=list(csv.DictReader(f))
assert len(rows)==6960
assert sum(x['mode']=='resampled' for x in rows)==696
assert sum(x['mode']=='fixed_center' for x in rows)==696
assert sum(x['mode']=='persistent' for x in rows)==5568
r=json.loads((first/'truth_evaluation.json').read_text())
repeat_record={'deterministic_repeat_status':'PASS','all_four_files_byte_identical':True,
               'source_blind_score_row_count':6960,'sha256':hashes}
(first/'deterministic_repeat.json').write_text(json.dumps(repeat_record,indent=2)+'\n')
lines=['# Persistent-source PMFS R1 development decision','',
       'Decision: `'+r['decision']+'`.','',
       'Source-blind scores were frozen and committed before the historical truth JSON was loaded.',
       'Four source-blind output files are byte-identical across the deterministic repeat.',
       'No scientific formula or supplied scorer/evaluator code was modified.','',
       '| Arm | Truth rank / 87 | Truth score | Top-1 center error (m) |',
       '| --- | ---: | ---: | ---: |']
for arm,label in (('resampled','R'),('fixed_center','C'),('persistent_marginal','P')):
    lines.append(f"| {label} | {r['ranks'][arm]} | {r['truth_scores'][arm]:.17g} | {r['top1'][arm]['center_error_m']:.17g} |")
lines += ['',f"R-minus-P truth rank improvement: {r['persistent_minus_resampled_truth_rank_improvement']}.",
          f"Spearman R-vs-P: {r['spearman_resampled_vs_persistent']:.17g}.",
          f"Median / maximum absolute candidate-rank displacement: {r['candidate_rank_abs_displacement_median']} / {r['candidate_rank_abs_displacement_max']}.",
          '', '| Leaf area (cells) | Candidate count | Median P-R score | Median R-P rank |',
          '| --- | ---: | ---: | ---: |']
for area, group in sorted(r['area_groups'].items(),key=lambda x:int(x[0])):
    lines.append(f"| {area} | {len(group)} | {statistics.median(g['delta_score'] for g in group):.17g} | {statistics.median(g['delta_rank'] for g in group)} |")
lines += ['', '## Five 1x1 diagnostic leaves', '', '| Candidate | P-R score | R-P rank |', '| --- | ---: | ---: |']
for g in r['one_by_one']:
    lines.append(f"| {g['id']} | {g['delta_score']:.17g} | {g['delta_rank']} |")
lines += ['', 'All raw area-group and per-candidate metrics are preserved in truth_evaluation.json.',
          'Development-only result; no main-innovation or closed-loop promotion.',
          'The frozen NULL/ADVERSE result is retained without rescue. No further experiment is started.','']
(first/'DECISION.md').write_text('\n'.join(lines))
print('DETERMINISTIC_REPEAT_PASS', r['decision'])
