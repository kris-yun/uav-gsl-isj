#!/usr/bin/env python3
"""Write the stopped R2B report and a compact independently recomputable ZIP."""
import csv
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / 'evidence/ocb_r2/r2b_dependence_score'
R = ROOT / 'research/ocb_r2/r2b_dependence_score'


def rows(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def main():
    result=json.loads((E/'R2B_RESULT.json').read_text())
    repeat=json.loads((E/'R2B_REPEAT.json').read_text())
    audit=json.loads((E/'R2B_INDEPENDENT_ARITHMETIC.json').read_text())
    assert repeat['byte_identical'] and audit['strict_tie_rule_verified']
    report=[ '# OCB-R2 R2B decision report', '', f"Decision: **{result['decision']}**", '',
        'The frozen exact-Q lag1–3 binary Variogram dependence factor does not amplify the prior R2 factor. '
        'No new simulation, continuous scoring, learned SC-MPDR model, confirmation, House03, R3 or closed loop was run.', '',
        '| Scope | Frozen R2 Energy factor | R2B Variogram factor |', '|---|---:|---:|',
        f"| All targets | 53/64 (82.8125%) | {result['VS_correct']}/64 (54.6875%) |",
        '| House01 | 26/32 | 19/32 |', '| House02 | 27/32 | 16/32 |', '',
        f"Rescues: **{result['rescues']}**; harms: **{result['harms']}**. Exact one-sided discordant-target binomial p: `{result['discordant_exact_binomial_p']}`. "
        'The protocol treats target pairing as an operational score comparison; physical source/context grouping remains the mechanism stability unit.', '',
        f"Positive group means: **{result['summary']['positive_groups']}/16**; positive context means: **{result['summary']['positive_contexts']}/8**. "
        f"Exact 8-context sign-flip p: `{result['summary']['exact_signflip']}`. House01 group median: `{result['summary']['house_medians']['House01']}`; "
        f"House02: `{result['summary']['house_medians']['House02']}`. Seven of eight leave-one-context-out medians are negative.", '',
        '## Eight contexts', '', '| Context | House | Wind | Gas | ES correct / 8 | VS correct / 8 | Mean Delta_VS |',
        '|---|---|---|---:|---:|---:|---:|']
    for r in rows(E/'R2B_CONTEXTS.tsv'):
        report.append(f"| {r['context']} | {r['house']} | {r['wind']} | {r['gas']} | {r['ES_correct']} | {r['VS_correct']} | {float(r['mean_Delta_VS']):.8f} |")
    report += ['', '## Sixteen source-context groups', '', '| Context | Source | ES correct / 4 | VS correct / 4 | Mean Delta_VS |',
               '|---|---|---:|---:|---:|']
    for r in rows(E/'R2B_GROUPS.tsv'):
        report.append(f"| {r['context']} | {r['truth_source']} | {r['ES_correct']} | {r['VS_correct']} | {float(r['mean_Delta_VS']):.8f} |")
    report += ['', '## Omission and arithmetic verification', '',
        'The four synchronized alternative-reference omissions produce 35/64, 36/64, 31/64 and 36/64. '
        'Their House02 and pooled group medians are all negative. No diagnostic lag or stratum is allowed to rescue this result.', '',
        'Two full scoring/aggregation passes are byte-identical. An independent integer-arithmetic implementation checked all 512 candidate scores '
        'under the 256 target/alternative-omission combinations, all 16 group means and both exact tests. '
        f"Maximum Delta discrepancy: `{audit['max_absolute_delta_error']}`; **zero sign or tie mismatches**. "
        'The exact empirical product is also checked against all K² cross-realization pairs in the scorer.', '',
        '## Interpretation and stop', '',
        'This NO-GO applies to the preregistered Variogram factor and the Energy-insensitivity amplification hypothesis. '
        'It does not replace the frozen R0/R1/R2 results or establish that all temporal dependence estimators fail. '
        'SC-MPDR remains an untrained algorithm candidate. Any continuous-channel or learned ratio test requires its own later authorization and freeze.', '',
        'Protocol source commit: `8281f5d4dccd485c411c2529d430fa51119d2df7`. Scorer freeze commit: `0384fff2`. '
        'All ten amplification conditions fail except deterministic repeat. STOP after evidence packaging.', '']
    # Nine scientific conditions failed; the tenth is the successful repeat.
    assert sum(result['conditions'].values())==1
    report[-2]='Protocol source commit: `8281f5d4dccd485c411c2529d430fa51119d2df7`. Scorer freeze commit: `0384fff2`. Nine scientific amplification conditions fail; deterministic repeat passes. STOP after evidence packaging.'
    (R/'R2B_DECISION_REPORT.md').write_bytes('\n'.join(report).encode())
    files=list(E.rglob('*.json'))+list(E.rglob('*.tsv'))+list(R.glob('*.py'))+list(R.glob('*.md'))
    files += [ROOT/'research/ocb_r2/R2B_DEPENDENCE_SENSITIVE_SCORE_PROTOCOL_20260930.md',
              ROOT/'research/ocb_r2/SC_MPDR_MAIN_INNOVATION_CANDIDATE_20260930.md',
              ROOT/'research/ocb_r2/mechanism_census_r0/run_census.py',
              ROOT/'research/ocb_r2/mechanism_census_r0/R0_PROTOCOL_FROZEN.md',
              ROOT/'research/ocb_r2/OCB_R2_SOURCE_INFORMATION_MECHANISM_CENSUS_R0.md',
              ROOT/'evidence/ocb_r2/mechanism_census_r0/R0_INPUT_HASHES.json',
              ROOT/'evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv',
              ROOT/'evidence/ocb_r2/s2x/OCB_R2_S2X_RUNLIST_32.tsv',
              ROOT/'evidence/ocb_r2/r2_broad_memory_path/R2_PATH_TARGETS.tsv',
              ROOT/'evidence/ocb_r2/r2_broad_memory_path/R2_DETERMINISTIC_REPEAT.json']
    inputs=ROOT/'evidence/ocb_r2/mechanism_census_r0/inputs'
    files += list(inputs.glob('*.pooled.npy'))+list(inputs.glob('*.json'))+list(inputs.glob('*.tsv'))
    for row in rows(E/'R2B_INPUTS_INDEX.tsv'):
        folder=ROOT/('evidence/ocb_r2/s2x/runs' if 's2x' in row['run_id'] else 'evidence/ocb_r2/s2_runs')
        files += [folder/(row['run_id']+suffix) for suffix in ('.RUN_MANIFEST.json','.QC.json','.RECORD_TIMELINE.tsv')]
    files=sorted(set(files))
    dest=ROOT/'_staging/OCB_R2_R2B_DEPENDENCE_SCORE_REVIEW_20260930.zip'
    dest.parent.mkdir(exist_ok=True)
    sums=[]
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:
            data=p.read_bytes();name=p.relative_to(ROOT).as_posix()
            sums.append(hashlib.sha256(data).hexdigest()+'  '+name)
            zi=zipfile.ZipInfo(name,(2026,9,30,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(zi,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
        zi=zipfile.ZipInfo('SHA256SUMS',(2026,9,30,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(zi,('\n'.join(sums)+'\n').encode(),compress_type=zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(dest) as z:
        for line in z.read('SHA256SUMS').decode().splitlines():
            digest,name=line.split('  ',1)
            assert hashlib.sha256(z.read(name)).hexdigest()==digest
    print(str(dest));print('bytes='+str(dest.stat().st_size));print('sha256='+hashlib.sha256(dest.read_bytes()).hexdigest())


if __name__=='__main__':
    main()
