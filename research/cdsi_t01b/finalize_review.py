"""Verify repeat, write the signed interpretation, package compact evidence."""
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'evidence/cdsi_t01b'
RESEARCH=ROOT/'research/cdsi_t01b'
INPUT=ROOT/'evidence/ocb_r2/mechanism_census_r0/inputs'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,text):
    path.write_text(text,encoding='utf-8',newline='\n')


def rows(path):
    return list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8')),delimiter='\t'))


def finalize():
    a,b=EV/'pass1',EV/'pass2'
    names=sorted(p.name for p in a.iterdir() if p.is_file())
    assert names==sorted(p.name for p in b.iterdir() if p.is_file())
    checks=[]
    for name in names:
        assert (a/name).read_bytes()==(b/name).read_bytes(),name
        checks.append(dict(file=name,bytes=(a/name).stat().st_size,sha256=digest(a/name),byte_identical=True))
    repeat=dict(pass_=True,compared_files=len(checks),checks=checks)
    write(EV/'DETERMINISTIC_REPEAT.json',json.dumps(repeat,indent=2,sort_keys=True)+'\n')
    result=json.loads((a/'CDSI_T01B_RESULT.json').read_text(encoding='utf-8'))
    aggregate=json.loads((a/'AGGREGATE_PERMUTATION.json').read_text(encoding='utf-8'))
    ctx=rows(a/'CONTEXT_ENERGY_RESULTS.tsv')
    effects=rows(a/'DYNAMIC_INFORMATION_EFFECTS.tsv')
    houses=rows(a/'HOUSE_SUMMARY.tsv')
    report=['# CDSI-T0.1B independent-realization information audit','',
        'Date: 2026-10-01','',
        'Branch: `research/cdsi-t01b-independent-information-audit-20261001`','',
        'Pre-target protocol/script/metadata freeze: `52721852`.','',
        f"## Decision: `{result['decision']}`",'',
        'Independent-sample contract: **8/8 PASS**, 64 distinct discovery runs/seeds. '
        'The prior `CDSI_T01_MATCHED_INTERVENTION_FAIL` remains unchanged.','',
        '## Eight-context results','',
        '| Context | House | E FULL | E STATIC | E C2 | p FULL | Z FULL | Z STATIC | Z C2 | Delta static | Delta pairing |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for e in effects:
        arm={r['arm']:r for r in ctx if r['context']==e['context']}
        f,s,q=[arm[k] for k in ('FULL_DYNAMIC_300D','STATIC_COLLAPSED_30D','C2_PAIRING_DESTROYED')]
        vals=[float(r['energy']) for r in (f,s,q)]+[float(f['exact_p'])]+[float(e[k]) for k in ('z_full','z_static','z_c2','delta_static','delta_pairing')]
        report.append('| '+e['context']+' | '+e['house']+' | '+' | '.join(f'{v:.8f}' for v in vals)+' |')
    report.extend(['','## Frozen gates','', '```json',json.dumps(result['gates'],indent=2,sort_keys=True),'```','',
        '## House summaries','', '| House | median Z FULL | median Delta static | median Delta pairing | positive static | positive pairing |',
        '|---|---:|---:|---:|---:|---:|'])
    for h in houses:
        report.append(f"| {h['house']} | {float(h['median_z_full']):.8f} | {float(h['median_delta_static']):.8f} | {float(h['median_delta_pairing']):.8f} | {h['positive_delta_static']}/4 | {h['positive_delta_pairing']}/4 |")
    report.extend(['','## Exact versus Monte Carlo null','',
        'Every context exhaustively evaluates 70 source-label assignments, including the observed assignment. '
        'FULL, STATIC and C2 each use their own assignment null. C2 is rebuilt under every assignment; '
        '1000 source-local time-block shuffles are numerical integration, not independent scientific replicates.','',
        f"The aggregate tests mean FULL standardized effect {aggregate['observed']:.9f}.",
        f"It samples {aggregate['draws']:,} stratified assignments from 70^8={aggregate['exact_joint_assignments']:,}.",
        f"Exceedances: {aggregate['exceedances']}; plus-one p={aggregate['p_plus_one']:.9g};",
        f"95% Monte Carlo binomial interval={aggregate['monte_carlo_binomial_95_interval']}.",
        'It is **Monte Carlo**, not exhaustive aggregate enumeration.','',
        'The context sign tests are exact. G2/G3 use the explicitly listed median/6-of-8 criteria; '
        'their sign-test p-values are reported descriptively because the request specifies no extra cutoff.','',
        '## Preservation, arithmetic and determinism','',
        'C2 passed full 30D snapshot-multiset and all-300-marginal preservation for every assignment/draw/source. '
        'Synthetic C2 K=3 output is bitwise equal to the actual R0 routine. The K=4 extension changes only '
        'the present sample count; it retains R0 block-shuffle semantics. Optimized distances were checked '
        'against direct transformed-path distances. Known-value and zero-signal Energy checks passed.','',
        f"Two complete calculations matched byte-for-byte for {len(checks)} result files, including all null arrays.",
        'C2 finite Monte Carlo values are symmetrized over A/B-complement assignments as frozen before analysis.','',
        '## Interpretation and limits','',
        'This task tests different configured **xyz** source distributions under the same non-source context. '
        'H01 source z is 0.4 versus -0.3 m; H02 source z is 0.2 versus -0.1 m. '
        'Neither pure xy nor continuous two-dimensional source identifiability is established.','',
        'The Energy primary is the signed V-statistic. It is upward-biased with 4-vs-4 samples; '
        'raw Energy >0 alone is not a positive finding. The context permutation tests and standardized '
        'contrasts determine the signed gates. A comparison of standardized distances is this protocol\'s '
        'operational dynamic criterion, not a conditional-information, PID/PIRD synergy, Fisher information '
        'or deployable source likelihood estimate.','',
        'Observed unstandardized FULL Energy is higher than C2 in all eight contexts, but FULL Z is '
        'lower in all eight because their permutation references differ. G3 is defined using Z, '
        'so the raw difference cannot rescue it. Report both to avoid interpreting this gate as '
        'a direct proof that cross-time coupling contains no information.','',
        'These are already-used discovery tensors. This is a new pre-analysis implementation freeze for '
        'this statistic, not untouched external confirmation. Four realizations/source/context and two '
        'configured sources limit power and scope. A gate failing to establish dynamic advantage does not '
        'prove temporal dependence absent under all scores or acquisition policies.','',
        'No optional secondary scorer was run. No source/seed/probe/time/threshold was changed. '
        'No GADEN, PMFS, network, 3D change, R3A, confirmation/H03 or closed loop was executed.','',
        '**COMPLETED AND STOPPED.**',''])
    write(RESEARCH/'CDSI_T01B_REPORT.md','\n'.join(report))
    g=result['gates']
    theory=f'''# Theory interpretation

Signed decision: **{result['decision']}**.

G1={g['G1_FULL_SOURCE_DISTRIBUTION']['pass']}; G2={g['G2_DYNAMIC_ADVANTAGE']['pass']}; G3={g['G3_PAIRING_ADVANTAGE']['pass']}.

The independent-seed design samples each configured source distribution using
the same frozen random-generation law. It does not require common random
numbers. The previous paired-intervention protocol remains failed; it is a
different estimand and historical decision.

FULL versus STATIC compares complete binary time-space vectors with their time
means. FULL versus C2 compares intact paths with snapshot-marginal-preserving
time-block shuffles. Z values are relative to each representation's own exact
70-assignment source-label null. They are not estimates of mutual information
or a calibrated source posterior. Dynamic PASS/HOLD/STOP is limited to this
signed operational criterion.

The source changes include z. Do not claim 2D_SOURCE_IDENTIFIABLE, THEORY_PASS,
positive-definite Fisher information, PID/PIRD synergy, or an algorithmic
improvement over Native PMFS. Historical R0/R1/R2 findings are not overwritten
by these different statistics.

All 64 inputs are discovery, with only four independent physical realizations
per source/context. Surrogate paths and permutations do not enlarge that
physical sample size. An unestablished dynamic increment is not a proof that
all dynamic mechanisms are absent. No new route, data generation, fixed-z
experiment or model construction is authorized by completion of this task.

STOP for human review.
'''
    write(RESEARCH/'THEORY_INTERPRETATION.md',theory)
    print(json.dumps(dict(decision=result['decision'],repeat_pass=True,compared_files=len(checks)),sort_keys=True))


def package():
    files=[p for folder in (RESEARCH,EV) for p in folder.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    for rel in ('research/cdsi_t01/CDSI_T01_AUDIT_REPORT.md','research/cdsi_t01/THEORY_INTERPRETATION.md',
        'research/ocb_r2/OCB_R2_S2X_MATCHED_SOURCE_CROSSOVER_32_PLAN.md',
        'research/ocb_r2/OCB_R2_GENERATOR_CONTRACT.md','research/ocb_r2/RNG_THREAD_DETERMINISM_AUDIT.md',
        'research/ocb_r2/mechanism_census_r0/run_census.py',
        'research/ocb_r2/mechanism_census_r0/R0_PROTOCOL_FROZEN.md',
        'evidence/ocb_r2/mechanism_census_r0/R0_INPUT_HASHES.json'):
        files.append(ROOT/rel)
    files+=list(INPUT.glob('*.pooled.npy'))
    files+=list((EV.parent/'ocb_r2/s2_runs').glob('*.RUN_MANIFEST.json'))
    files+=list((EV.parent/'ocb_r2/s2x/runs').glob('*.RUN_MANIFEST.json'))
    files=sorted(set(files))
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    inventory=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for p in files]
    result=json.loads((EV/'pass1/CDSI_T01B_RESULT.json').read_text(encoding='utf-8'))
    provenance=dict(branch=branch,commit=commit,pre_target_freeze='52721852',decision=result['decision'],files=inventory)
    zip_path=Path('C:/Users/50176/Downloads/CDSI_T01B_INDEPENDENT_INFORMATION_REVIEW_20261001.zip')
    assert not zip_path.exists(),'Refusing overwrite'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:
            z.write(p,p.relative_to(ROOT).as_posix())
        z.writestr('PACKAGE_PROVENANCE.json',json.dumps(provenance,indent=2,sort_keys=True)+'\n')
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        for entry in inventory:
            assert hashlib.sha256(z.read(entry['path'])).hexdigest()==entry['sha256']
    meta=dict(path=str(zip_path),bytes=zip_path.stat().st_size,sha256=digest(zip_path),commit=commit,branch=branch,decision=result['decision'])
    write(zip_path.with_suffix('.json'),json.dumps(meta,indent=2,sort_keys=True)+'\n')
    print(json.dumps(meta,sort_keys=True))


if __name__=='__main__':
    import sys
    package() if '--package' in sys.argv else finalize()
