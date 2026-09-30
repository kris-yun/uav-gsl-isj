"""Report the frozen R2C failure and package the exact, independently checked inputs."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[3]
R=ROOT/'research/ocb_r2/r2c_signature_path'
E=ROOT/'evidence/ocb_r2/r2c_signature_path'


def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))


def report():
    a=json.loads((E/'R2C_RESULT.json').read_text());q=json.loads((E/'R2C_Q_CONVERGENCE.json').read_text())
    v=json.loads((E/'R2C_INDEPENDENT_AUDIT.json').read_text())
    assert a['decision']=='OCB_R2_R2C_SIGNATURE_PATH_NO_GO'
    lines=['# R2C signature-path discovery decision','',f"Decision: **{a['decision']}**",'',
        'The frozen RBF signature-kernel dependence residual did not reproduce or amplify the R2 source signal. '
        'All results are discovery-only and use the same 64 binary tensors. No generator, PMFS forward, continuous-channel scorer, '
        'neural model, confirmation, House03, R3, planner or closed loop was run.','',
        '| Scope | Frozen R2 Energy factor | R2C signature factor |','|---|---:|---:|',
        f"| All | 53/64 | {a['SIG_correct']}/64 |",
        f"| House01 | 26/32 | {a['houses']['House01']['SIG_correct']}/32 |",
        f"| House02 | 27/32 | {a['houses']['House02']['SIG_correct']}/32 |",'',
        f"Paired **{a['rescues']} rescues / {a['harms']} harms**; one-sided discordant binomial p = `{a['discordant_exact_binomial_p']}`.",
        f"Positive source-context group means: **{a['summary']['positive_groups']}/16**; positive contexts: **{a['summary']['positive_contexts']}/8**. "
        f"Exact context sign-flip p = `{a['summary']['exact_signflip']}`. Both House medians and all LOCO medians are positive, "
        'but these do not rescue the failed target, group and omission criteria.','',
        '## Context and source-group results','','| Context | House | Wind | Gas | ES / 8 | SIG / 8 | Mean Delta_SIG |',
        '|---|---|---|---:|---:|---:|---:|']
    for t in rows(E/'R2C_CONTEXTS.tsv'):
        lines.append(f"| {t['context']} | {t['house']} | {t['wind']} | {t['gas']} | {t['ES_correct']} | {t['SIG_correct']} | {float(t['mean_Delta_SIG']):.9f} |")
    lines+=['','| Context | Source | ES / 4 | SIG / 4 | Mean Delta_SIG |','|---|---|---:|---:|---:|']
    for t in rows(E/'R2C_GROUPS.tsv'):
        lines.append(f"| {t['context']} | {t['truth_source']} | {t['ES_correct']} | {t['SIG_correct']} | {float(t['mean_Delta_SIG']):.9f} |")
    lines+=['','## All frozen amplification conditions','','| Condition | Passed |','|---|---|']
    for name,passed in a['conditions'].items():lines.append(f"| {name} | {passed} |")
    lines+=['','## Q numerical convergence','',
        f"B=2048 -> 4096 sign agreement: **{q['sign_agreement']}/64**, meeting >=63. "
        f"Maximum absolute Delta change: **{q['max_absolute_delta_change']:.10f}**, exceeding the frozen "
        f"10%-of-median threshold **{q['allowed_maximum_delta_change']:.10f}**. Median absolute primary Delta: `{q['median_absolute_primary_delta']}`. "
        '**The convergence gate fails.** The 4096 result is not substituted, and no larger B or new seed is used to rescue it.','',
        '## Alternative-reference omission robustness','','| Omit | SIG / 64 | H01 median | H02 median | Pooled median |',
        '|---:|---:|---:|---:|---:|']
    for t in rows(E/'R2C_OMISSION.tsv'):
        lines.append(f"| {t['alternative_omission']} | {t['SIG_correct']} | {float(t['House01_group_median']):.9f} | {float(t['House02_group_median']):.9f} | {float(t['pooled_group_median']):.9f} |")
    lines+=['','## Truncated signature anatomy','','| Level | Scope | Strict positive / targets | Mean Delta |',
        '|---|---|---:|---:|']
    for t in rows(E/'R2C_ANATOMY_SUMMARY.tsv'):
        lines.append(f"| {t['level']} | {t['house']} | {t['positive']}/{t['targets']} | {float(t['mean_delta']):.9g} |")
    lines+=['',
        'These are explicit linear-coordinate Chen signatures, not truncations of the primary RBF feature-space signature. '
        'The <=2 and <=3 summaries do not support promotion. Level1 depends only on the endpoint; Q preserves that law. '
        'Its nonzero residual is exactly the finite-K difference between the RAW U self term and the empirical-product Q self expectation: '
        '`D_level1 = sum_i ||endpoint_i - mean_endpoint||^2 / [K(K-1)]`. '
        f"This identity was independently verified for all candidate/omission anatomy rows, maximum error `{v['level1_finite_K_self_term_identity_max_error']}`. "
        f"{v['level1_primary_zero_within_frozen_tolerance']}/64 primary deltas are numerical ties within 1e-10; exported strict signs are retained, "
        'and rounding-scale signs are not treated as information. Thus the level1 count cannot establish temporal coupling.', '',
        '## Implementation, repeat and interpretation','',
        'Scorer freeze commit: **be1b6930** (pushed before R2C scoring). Protocol source: **7967491d57af26875ce07ed6aac093c28879410c**. '
        'Public sigkernel reference commit: **40a583155ea8d2194af0e90dddab37e2659cfcfd**. '
        'RBF follows public exp(-squared_distance/sigma), sigma=1; default corrected PDE, dyadic order1. '
        'Synthetic public-library parity, symmetry, PSD and exact-Q Chen enumeration passed before scoring. '
        'An independent unmodified public solver then checked 512 original-path kernel pairs, all 1024 exported RAW candidate rows, '
        f"and 8192 fixed Q kernel pairs; maximum RAW discrepancy `{v['max_RAW_error']}`, Q discrepancy `{v['Q_2048_and_4096_one_fixed_candidate_max_error']}`. "
        'Two complete 2048/4096 scoring and aggregation passes are byte-identical.', '',
        'The public Torch parity backend emits a pre-existing NumPy ABI bridge warning. It uses list-to-Tensor and Tensor-to-list exclusively; '
        'all public comparisons completed successfully. The production scorer uses NumPy/Numba, no global package replacement or ROS changes.', '',
        'This NO-GO is for the specified binary RBF signature residual and its promotion gate. '
        'It does not prove every rough-path model fails, that the R0/R1/R2 mechanism is absent, or that pairwise models are universally inadequate. '
        'The failed numerical-convergence condition further limits broad scientific interpretation. '
        'A fair proper kernel score is not a source likelihood or calibrated posterior; nothing is inserted into PMFS. '
        '**STOP. No automatic continuous-axis experiment or network follows.**','']
    (R/'R2C_DECISION_REPORT.md').write_bytes('\n'.join(lines).encode())


def package():
    files=list(E.rglob('*.json'))+list(E.rglob('*.tsv'))+[p for p in R.rglob('*') if p.is_file() and p.suffix in ('.py','.md','.pyx')]+[R/'upstream_reference/LICENSE']
    files += [ROOT/'research/ocb_r2/R2C_SIGNATURE_PATH_PROTOCOL_20260930.md',ROOT/'research/ocb_r2/SC_RPSI_MAIN_ALGORITHM_CANDIDATE_20260930.md',
        ROOT/'research/ocb_r2/r2b_dependence_score/run_r2b.py',ROOT/'research/ocb_r2/r2b_dependence_score/R2B_PROTOCOL_FROZEN.md',
        ROOT/'research/ocb_r2/R2B_DEPENDENCE_SENSITIVE_SCORE_PROTOCOL_20260930.md',ROOT/'research/ocb_r2/mechanism_census_r0/run_census.py',
        ROOT/'research/ocb_r2/mechanism_census_r0/R0_PROTOCOL_FROZEN.md',ROOT/'research/ocb_r2/OCB_R2_SOURCE_INFORMATION_MECHANISM_CENSUS_R0.md',
        ROOT/'evidence/ocb_r2/r2_broad_memory_path/R2_PATH_TARGETS.tsv',ROOT/'evidence/ocb_r2/r2_broad_memory_path/R2_DETERMINISTIC_REPEAT.json',
        ROOT/'evidence/ocb_r2/mechanism_census_r0/R0_INPUT_HASHES.json']
    manifest=json.loads((ROOT/'evidence/ocb_r2/mechanism_census_r0/R0_INPUT_HASHES.json').read_text())
    files += [ROOT/n for n in manifest['input_file_sha256']]
    files += list((ROOT/'evidence/ocb_r2/mechanism_census_r0/inputs').glob('*.pooled.npy'))
    files += list((ROOT/'evidence/ocb_r2/mechanism_census_r0/inputs').glob('*.json'))+list((ROOT/'evidence/ocb_r2/mechanism_census_r0/inputs').glob('*.tsv'))
    for t in rows(E/'R2C_INPUTS_INDEX.tsv'):
        folder=ROOT/('evidence/ocb_r2/s2x/runs' if 's2x' in t['run_id'] else 'evidence/ocb_r2/s2_runs')
        files += [folder/(t['run_id']+s) for s in ('.RUN_MANIFEST.json','.QC.json','.RECORD_TIMELINE.tsv')]
    destination=Path('D:/ZYC/A-gas/_staging/OCB_R2_R2C_SIGNATURE_PATH_REVIEW_20260930.zip')
    destination.parent.mkdir(exist_ok=True)
    sums=[]
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(set(files)):
            data=p.read_bytes();name=p.relative_to(ROOT).as_posix()
            info=zipfile.ZipInfo(name,(2026,9,30,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
            sums.append(hashlib.sha256(data).hexdigest()+'  '+name)
        git=dict(branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
                 final_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),freeze_commit='be1b6930')
        data=(json.dumps(git,sort_keys=True,indent=2)+'\n').encode()
        z.writestr('PACKAGE_GIT.json',data);sums.append(hashlib.sha256(data).hexdigest()+'  PACKAGE_GIT.json')
        z.writestr('SHA256SUMS',('\n'.join(sums)+'\n').encode())
    with zipfile.ZipFile(destination) as z:
        for line in z.read('SHA256SUMS').decode().splitlines():
            digest,name=line.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==digest
    print(json.dumps(dict(path=str(destination),bytes=destination.stat().st_size,
        SHA256=hashlib.sha256(destination.read_bytes()).hexdigest(),files=len(sums)),indent=2))


if __name__=='__main__':
    import sys
    report() if len(sys.argv)==1 else package()
