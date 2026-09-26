#!/usr/bin/env python3
import hashlib, json
from pathlib import Path

base=Path('/home/zyc/pmfs_evidence_pseudoreplication_20260926')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=('candidate_scores.csv','event_support_audit.json','native_parity.json','SCORES_SHA256.txt')
for name in names:
    assert (base/'result'/name).read_bytes()==(base/'deterministic_repeat'/name).read_bytes(), name
for folder in ('result','deterministic_repeat'):
    for line in (base/folder/'SCORES_SHA256.txt').read_text().splitlines():
        digest,name=line.split('  ',1)
        p=base/'code'/name if name.endswith('.py') else base/folder/name
        assert sha(p)==digest,name
for line in (base/'inputs/INPUT_SHA256SUMS.txt').read_text().splitlines():
    digest,name=line.split('  ',1)
    assert sha(base/'inputs'/name)==digest,name
record={'status':'PASS','all_four_source_blind_outputs_byte_identical':True,
        'sha256':{name:sha(base/'result'/name) for name in names}}
(base/'result/deterministic_repeat.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
r=json.loads((base/'result/truth_evaluation.json').read_text())
audit=json.loads((base/'result/event_support_audit.json').read_text())
parity=json.loads((base/'result/native_parity.json').read_text())
lines=['# PMFS evidence pseudoreplication R1 decision','',
       'Decision: `'+r['decision']+'`.','',
       'Freeze commit (pushed before the truth evaluator): `957781a646b748bcaec99c37d1759aa3218fdb48`.','',
       'The supplied scorer and evaluator are unchanged. The same 87 historical Native C-arm maps were rescored.',
       'No forward simulation, GADEN, new plume, training, parameter tuning, additional House or closed loop was run.',
       'Git storage attributes were corrected before truth evaluation to preserve exact CSV bytes; no scoring implementation patch was needed.','',
       '| Arm | Truth rank / 87 | Truth score | Top1 center error (m) | Spearman vs M |',
       '| --- | ---: | ---: | ---: | ---: |']
for name in ('M','S','Elog','Ebrier'):
    a=r['arms'][name]
    rho='1' if name=='M' else f"{a['spearman_vs_M']:.17g}"
    lines.append(f"| {name} | {a['truth_rank']} | {a['truth_score']:.17g} | {a['top1_center_error_m']:.17g} | {rho} |")
lines+=['',f"Native parity max absolute error: {parity['max_abs_native_score_diff']:.17g} (tolerance {parity['tolerance']}).",
        'Deterministic repeat: PASS for all four source-blind files.',
        f"Raw events / hits / misses / unique robot sites: {audit['raw_event_count']} / {audit['hit_count']} / {audit['miss_count']} / {audit['unique_robot_site_count']}.",
        f"Free cells / confidence >0 / >0.01 / >0.1: {audit['free_cell_count']} / {audit['confidence_gt_0']} / {audit['confidence_gt_0p01']} / {audit['confidence_gt_0p1']}.",
        f"Elog clipping evaluations: {audit['event_probability_clip_count']} (frozen epsilon {audit['event_probability_clip_epsilon']}).",'',
        '| Arm | Truth rank improvement vs M | Median / max absolute rank displacement | Top1 candidate |',
        '| --- | ---: | ---: | --- |']
for name in ('S','Elog','Ebrier'):
    a=r['arms'][name]
    lines.append(f"| {name} | {r['truth_rank_improvement_vs_M'][name]} | {a['rank_abs_displacement_median']} / {a['rank_abs_displacement_max']} | {a['top1_candidate']} |")
lines+=['',f"Elog / Ebrier truth-rank direction agreement: {r['event_scores_direction_agree']}.",
        'All top-10 candidate lists and exact raw metrics are retained in truth_evaluation.json.',
        'Development-only NULL/ADVERSE is retained. Execution stops here; no rescue or next mechanism experiment is started.','']
(base/'result/DECISION.md').write_text('\n'.join(lines))
print('EVIDENCE_FINALIZED',r['decision'])
